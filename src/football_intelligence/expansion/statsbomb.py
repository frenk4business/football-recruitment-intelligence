"""Additional separately scoped StatsBomb profiles using frozen, conservative parsers."""

import json
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from football_intelligence.expansion.sources import Sources
from football_intelligence.profiles import statsbomb
from football_intelligence.profiles.aggregate import aggregate_rows
from football_intelligence.profiles.cache import checksum, write_json
from football_intelligence.profiles.features import counts, family
from football_intelligence.profiles.ingest import OBS_SCHEMA, observation


def build(root: Path):
    sources = Sources(root)
    destination = root / "data/processed/v12/statsbomb"
    destination.mkdir(parents=True, exist_ok=True)
    profiles, reports = [], []
    for c in sources.seasons():
        cid, sid = c["competition_id"], c["season_id"]
        scope = f"statsbomb-{cid}-{sid}"
        rows = []
        totals: Counter = Counter()
        teams = {}
        matches = json.loads(sources.sb(f"data/matches/{cid}/{sid}.json").read_text())
        for match in sorted(matches, key=lambda m: (m["match_date"], m["match_id"])):
            mid = match["match_id"]
            raw = {
                kind: json.loads(sources.sb(f"data/{kind}/{mid}.json").read_text())
                for kind in ["lineups", "events"]
            }
            people = {p["player_id"]: p for t in raw["lineups"] for p in t["lineup"]}
            teams.update({str(t["team_id"]): t["team_name"] for t in raw["lineups"]})
            actors: dict[int, list] = defaultdict(list)
            for e in raw["events"]:
                if e.get("player") and e["period"] < 3:
                    actors[e["player"]["id"]].append(e)
            totals["events"] += len(raw["events"])
            participation = statsbomb.minutes(raw)
            if not participation:
                totals["unreconciled_matches"] += 1
                participation = {
                    p["player_id"]: {
                        "minutes": None,
                        "team_id": team["team_id"],
                        "reliable": False,
                        "reasons": ["unreconciled_match_or_unsupported_extra_time"],
                        "minute_method": "unavailable",
                        "participated": True,
                    }
                    for team in raw["lineups"]
                    for p in team["lineup"]
                    if p["player_id"] in actors
                }
            for pid, row in participation.items():
                if not row["participated"]:
                    continue
                totals["participating_rows"] += 1
                totals["reliable_rows"] += row["reliable"]
                totals.update(row["reasons"])
                row["role_family"] = family(row.get("role"))
                common = counts(
                    [a for e in actors[pid] if (a := statsbomb.common_action(e)) is not None]
                )
                native = statsbomb.native_counts(
                    actors[pid], {e["type"]["name"] for e in raw["events"]}
                )
                files = [
                    f"statsbomb/{sources.revision}/data/{kind}/{mid}.json"
                    for kind in ["lineups", "events"]
                ]
                rows.append(
                    observation(
                        "statsbomb",
                        scope,
                        pid,
                        people.get(pid, {}).get("player_name", f"Provider ID {pid}"),
                        mid,
                        match["match_date"],
                        row,
                        common,
                        native,
                        files,
                    )
                )
        groups: dict[int, list] = defaultdict(list)
        for row in rows:
            groups[row["player_id"]].append(row)
        aggregated = [aggregate_rows(group) for _, group in sorted(groups.items())]
        profiles.extend(aggregated)
        pq.write_table(
            pa.Table.from_pylist(rows, schema=OBS_SCHEMA),
            destination / f"{scope}.parquet",
            compression="zstd",
        )
        reports.append(
            {
                **c,
                "scope": scope,
                "provider": "statsbomb",
                "teams_by_id": teams,
                "quality": dict(totals),
                "profiles_before_quality_filter": len(aggregated),
                "searchable_profiles": sum(
                    p["reliable"] and p["minutes"] >= 450 for p in aggregated
                ),
                "exclusions": dict(Counter(r for p in aggregated for r in p["exclusion_reasons"])),
                "recruitment_enabled": False,
                "recruitment_reason": "No registered provider-native recruitment evaluation for this additional scope",
                "scope_label": "European competition matches only"
                if cid in {16, 35}
                else "Cup/international matches only"
                if cid in {43, 55, 87, 223, 1267, 1470}
                else "Domestic league observations",
                "source_revision": sources.revision,
            }
        )
        print(
            f"StatsBomb {scope}: {len(matches)} matches; {reports[-1]['searchable_profiles']} searchable profiles; {c['coverage_status']}",
            flush=True,
        )
    write_json(destination / "profiles.json", profiles, compact=True)
    write_json(
        root / "artifacts/v12/statsbomb-ingestion.json",
        {
            "source_manifest_sha256": checksum(root / "config/v12-sources.json"),
            "scopes": reports,
            "profile_version": "statsbomb-expanded-profile-v1",
            "note": "New source scopes; existing v1.1 artifacts unchanged. No new similarity/recruitment/translation validation is implied.",
        },
    )
    return profiles, reports
