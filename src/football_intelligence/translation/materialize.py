"""Reuse canonical events and Phase 2 count definitions for dated environments."""

import hashlib
import json
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl
import yaml

from football_intelligence.data.adapters.statsbomb import StatsBombAdapter
from football_intelligence.data.schema import canonical_id
from football_intelligence.dna.cohort import write
from football_intelligence.dna.features import SET_PIECES, aggregate, match_observations
from football_intelligence.dna.registry import CORE, VERSION
from football_intelligence.translation.evidence import adjacent_transitions, identity_status
from football_intelligence.translation.sources import SourceCache


def settings(root: Path) -> dict:
    return yaml.safe_load((root / "config/translation.yaml").read_text())


def team_context(events: list[dict], match: dict) -> list[dict]:
    ends: dict[int, float] = {}
    sequences: dict[str, set] = defaultdict(set)
    for e in events:
        if e["period"] > 4:
            continue
        if e["event_type"] == "Half End":
            ends[e["period"]] = max(ends.get(e["period"], 0), e["timestamp_seconds"])
        owner = json.loads(e["attributes_json"]).get("possession_team", {}).get("id")
        if owner is not None and e["possession"] is not None:
            sequences[canonical_id("statsbomb", "teams", owner)].add((e["period"], e["possession"]))
    duration = sum(ends.values()) / 60 if set(ends) in ({1, 2}, {1, 2, 3, 4}) else None
    rows = []
    for tid in (match["home_team_id"], match["away_team_id"]):
        own = [e for e in events if e["team_id"] == tid and e["period"] < 5]
        rows.append(
            dict(
                team_id=tid,
                match_id=match["id"],
                observed_on=str(match["observed_on"]),
                competition_id=match["competition_id"],
                season_id=match["season_id"],
                duration_minutes=duration,
                passes=sum(
                    e["event_type"] == "Pass" and e["subtype"] not in SET_PIECES for e in own
                ),
                shots=sum(e["event_type"] == "Shot" and e["subtype"] != "Penalty" for e in own),
                possessions=len(sequences[tid]),
                opponent_possessions=sum(len(v) for k, v in sequences.items() if k != tid),
            )
        )
    return rows


def materialize(root: Path) -> dict:
    cfg = settings(root)
    revision = cfg["revision"]
    directory = root / "data/raw/phase3/statsbomb" / revision
    cache = SourceCache(directory)
    base = f"https://raw.githubusercontent.com/statsbomb/open-data/{revision}/"
    catalogue = cache.json("data/competitions.json", base + "data/competitions.json")
    local = root / "data/processed/phase3"
    observations = []
    context_rows = []
    identity_records: dict[str, list[dict]] = defaultdict(list)
    metadata = {}
    source_records = []
    code_hash = hashlib.sha256(
        b"".join(
            (root / f"src/football_intelligence/{p}").read_bytes()
            for p in [
                "translation/materialize.py",
                "data/adapters/statsbomb.py",
                "data/minutes.py",
                "dna/features.py",
                "dna/registry.py",
            ]
        )
    ).hexdigest()
    for cid, sid in cfg["audit_seasons"]:
        c = next(c for c in catalogue if (c["competition_id"], c["season_id"]) == (cid, sid))
        path = f"data/matches/{cid}/{sid}.json"
        matches = cache.json(path, base + path)

        def fetch(mid):
            for kind in ("events", "lineups"):
                relative = f"data/{kind}/{mid}.json"
                # Reuse the Phase 2 frozen source bytes when available; validate their lock.
                old = root / "data/raw/cohorts/wsl_2023_24" / revision / relative
                destination = directory / relative
                if old.exists() and not destination.exists():
                    lock = json.loads((root / "config/wsl_2023_24.sources.json").read_text())
                    record = next(r for r in lock["files"] if r["path"] == relative)
                    payload = old.read_bytes()
                    if hashlib.sha256(payload).hexdigest() != record["sha256"]:
                        raise ValueError("Phase 2 cache checksum mismatch")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(payload)
                    write(
                        destination.with_suffix(".json.sha.json"),
                        dict(url=base + relative, sha256=record["sha256"], bytes=len(payload)),
                    )
                cache.get(relative, base + relative)
            return mid

        with ThreadPoolExecutor(max_workers=3) as pool:
            for i, _ in enumerate(pool.map(fetch, [m["match_id"] for m in matches]), 1):
                if i % 30 == 0 or i == len(matches):
                    print(f"Transfer source {cid}/{sid}: {i}/{len(matches)}", flush=True)
        for i, m in enumerate(sorted(matches, key=lambda m: (m["match_date"], m["match_id"]))):
            mid = m["match_id"]
            raw_lineups = cache.json(f"data/lineups/{mid}.json", base + f"data/lineups/{mid}.json")
            for team in raw_lineups:
                for p in team["lineup"]:
                    pid = canonical_id("statsbomb", "players", p["player_id"])
                    identity_records[pid].append(
                        dict(
                            provider="statsbomb",
                            provider_player_id=p["player_id"],
                            name=p["player_name"],
                            nationality=p.get("country", {}).get("name"),
                            gender=c["competition_gender"],
                        )
                    )
                    metadata[
                        pid,
                        canonical_id("statsbomb", "teams", team["team_id"]),
                        canonical_id("statsbomb", "seasons", f"{cid}:{sid}"),
                    ] = dict(
                        name=p["player_name"],
                        provider_player_id=p["player_id"],
                        team=team["team_name"],
                        competition=c["competition_name"],
                        season=c["season_name"],
                        season_start_year=int(c["season_name"].split("/")[0]),
                        country=c["country_name"],
                        gender=c["competition_gender"],
                    )
            hashes = [
                json.loads((directory / f"data/{k}/{mid}.json.sha.json").read_text())["sha256"]
                for k in ("events", "lineups")
            ]
            fingerprint = hashlib.sha256(
                (code_hash + "".join(hashes) + json.dumps(m, sort_keys=True)).encode()
            ).hexdigest()
            target = local / "matches" / f"{mid}.json"
            saved = json.loads(target.read_text()) if target.exists() else None
            if saved and saved["fingerprint"] == fingerprint:
                rows = saved["observations"]
                context = saved["team_context"]
            else:
                raw = dict(
                    competition=c,
                    match=m,
                    lineups=raw_lineups,
                    events=cache.json(f"data/events/{mid}.json", base + f"data/events/{mid}.json"),
                )
                canonical = StatsBombAdapter().normalise(raw, fingerprint)
                rows = match_observations(
                    canonical["events"], canonical["lineups"], canonical["matches"][0]
                )
                context = team_context(canonical["events"], canonical["matches"][0])
                write(
                    target, dict(fingerprint=fingerprint, observations=rows, team_context=context)
                )
            observations.extend(rows)
            context_rows.extend(context)
            source_records.append(
                dict(
                    match_id=mid,
                    competition_id=cid,
                    season_id=sid,
                    source_hashes=hashes,
                    observation_hash=fingerprint,
                )
            )
            if (i + 1) % 30 == 0 or i + 1 == len(matches):
                print(f"Transfer counts {cid}/{sid}: {i + 1}/{len(matches)}", flush=True)
    # Exact provider identity plus consistent metadata; no name-based joins.
    identities = {
        pid: dict(
            zip(("status", "reasons"), identity_status(rows), strict=True),
            names=sorted({r["name"] for r in rows}),
            provider_player_id=rows[0]["provider_player_id"],
        )
        for pid, rows in identity_records.items()
    }
    local.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(observations, infer_schema_length=None).write_parquet(
        local / "player_feature_observation.parquet", compression="zstd"
    )
    pl.DataFrame(context_rows, infer_schema_length=None).write_parquet(
        local / "team_match_context.parquet", compression="zstd"
    )
    write(local / "identity_records.json", identities)
    write(
        local / "metadata.json",
        [{"player_id": k[0], "team_id": k[1], "season_id": k[2], **v} for k, v in metadata.items()],
    )
    write(
        local / "source_manifest.json",
        dict(
            revision=revision,
            feature_version=VERSION,
            model_code_hash=code_hash,
            matches=source_records,
        ),
    )
    return build_environments(root)


def build_environments(root: Path) -> dict:
    cfg = settings(root)
    local = root / "data/processed/phase3"
    observations = pl.read_parquet(local / "player_feature_observation.parquet").to_dicts()
    identities = json.loads((local / "identity_records.json").read_text())
    meta = {
        (m["player_id"], m["team_id"], m["season_id"]): m
        for m in json.loads((local / "metadata.json").read_text())
    }
    # Stints follow changes in recorded team, including a return to an earlier team.
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in observations:
        groups[row["player_id"], row["competition_id"], row["season_id"]].append(row)
    environments = []
    for _, rows in sorted(groups.items()):
        stints: list[list[dict]] = []
        for r in sorted(rows, key=lambda r: (r["observed_on"], r["match_id"], r["team_id"])):
            if not stints or stints[-1][-1]["team_id"] != r["team_id"]:
                stints.append([])
            stints[-1].append(r)
        for rows in stints:
            p = aggregate(rows)
            first = rows[0]
            metadata = meta[first["player_id"], first["team_id"], first["season_id"]]
            start, end = min(r["observed_on"] for r in rows), max(r["observed_on"] for r in rows)
            eid = canonical_id(
                "translation",
                "environments",
                ":".join(
                    [
                        first["player_id"],
                        first["competition_id"],
                        first["season_id"],
                        first["team_id"],
                        start,
                        end,
                    ]
                ),
            )
            valid = [
                r
                for r in rows
                if r["minutes_reliable"] and r["minutes"] is not None and r["minutes"] > 0
            ]
            keys = [
                "shots",
                "progressive_passes",
                "carries",
                "progressive_carries",
                "pressures",
                "npxg",
                "xa",
                "own_possessions",
                "opponent_possessions",
                "team_passes",
            ]
            counts = {
                k: sum(r[k] for r in valid)
                if valid and all(r[k] is not None for r in valid)
                else None
                for k in keys
            }
            environments.append(
                dict(
                    environment_id=eid,
                    provider="statsbomb",
                    player_id=first["player_id"],
                    team_id=first["team_id"],
                    competition_id=first["competition_id"],
                    season_id=first["season_id"],
                    **{
                        k: v
                        for k, v in metadata.items()
                        if k not in ("player_id", "team_id", "season_id")
                    },
                    start_date=start,
                    end_date=end,
                    match_dates=sorted({r["observed_on"] for r in rows}),
                    match_ids=[r["match_id"] for r in rows],
                    environment_class="domestic",
                    identity_confidence=identities[first["player_id"]]["status"],
                    reliable_minutes=p["minutes"],
                    appearances=p["appearances"],
                    roster_appearances=len(rows),
                    unreliable_appearances=p["unreliable_appearances"],
                    role=p["primary_role"],
                    role_shares=p["role_shares"],
                    feature_version=VERSION,
                    source_revision=cfg["revision"],
                    counts=counts,
                    values=p["values"],
                )
            )
    transitions = adjacent_transitions(environments, cfg["max_gap_days"])
    lookup = {e["environment_id"]: e for e in environments}
    for t in transitions:
        a, b = lookup[t["source_environment_id"]], lookup[t["destination_environment_id"]]
        t["source_minutes"], t["destination_minutes"] = a["reliable_minutes"], b["reliable_minutes"]
        t["source_role"], t["destination_role"] = a["role"], b["role"]
        t["eligibility"] = {}
        for threshold in cfg["audit_thresholds"]:
            reasons = list(t["exclusion_reasons"])
            if min(a["reliable_minutes"], b["reliable_minutes"]) < threshold:
                reasons.append("below_minutes")
            if not a["role"] or not b["role"]:
                reasons.append("missing_role")
            if "GK" in (a["role"], b["role"]):
                reasons.append("goalkeeper_excluded")
            if any(e["values"][f] is None for e in (a, b) for f in CORE):
                reasons.append("missing_core_features")
            t["eligibility"][str(threshold)] = reasons
    write(local / "player_environment.json", environments)
    write(local / "transition_episode.json", transitions)
    report = dict(
        provider="statsbomb",
        revision=cfg["revision"],
        matches=len({r["match_id"] for r in observations}),
        players=len(identities),
        identity_status=dict(Counter(v["status"] for v in identities.values())),
        identity_anomalies={k: v for k, v in identities.items() if v["reasons"]},
        environments=len(environments),
        candidates=len(transitions),
        transition_types=dict(Counter(t["transition_type"] for t in transitions)),
        repeated_players=len({t["player_id"] for t in transitions}),
        actual_team_changes=sum(
            t["actual_team_change"] and t["structurally_eligible"] for t in transitions
        ),
        cross_league_changes=sum(
            t["transition_type"] == "cross_league_change" and t["structurally_eligible"]
            for t in transitions
        ),
        minutes_quality=dict(Counter(r["minutes_quality"] for r in observations)),
        destination_zero_minutes=sum(t["destination_minutes"] == 0 for t in transitions),
        destination_under_450=sum(t["destination_minutes"] < 450 for t in transitions),
        thresholds={
            str(th): dict(
                eligible=sum(not t["eligibility"][str(th)] for t in transitions),
                players=len({t["player_id"] for t in transitions if not t["eligibility"][str(th)]}),
                roles=dict(
                    Counter(
                        t["destination_role"] for t in transitions if not t["eligibility"][str(th)]
                    )
                ),
                destination_seasons=dict(
                    Counter(
                        t["destination_season"]
                        for t in transitions
                        if not t["eligibility"][str(th)]
                    )
                ),
                transition_types=dict(
                    Counter(
                        t["transition_type"] for t in transitions if not t["eligibility"][str(th)]
                    )
                ),
                rejected_reasons=dict(
                    Counter(r for t in transitions for r in t["eligibility"][str(th)])
                ),
            )
            for th in cfg["audit_thresholds"]
        },
        feature_coverage={f: sum(e["values"][f] is not None for e in environments) for f in CORE},
        dates=[
            min(r["observed_on"] for r in observations),
            max(r["observed_on"] for r in observations),
        ],
    )
    write(root / "artifacts/phase3/transfer_evidence.json", report)
    return report
