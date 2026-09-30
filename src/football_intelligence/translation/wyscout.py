"""Separate Figshare metadata screen; never harmonizes provider event metrics."""

import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from football_intelligence.data.schema import canonical_id
from football_intelligence.dna.cohort import write
from football_intelligence.translation.evidence import adjacent_transitions
from football_intelligence.translation.sources import SourceCache


def audit_wyscout(root: Path) -> dict:
    cache = SourceCache(root / "data/raw/phase3/wyscout")
    lock = json.loads((root / "config/phase3.sources.json").read_text())
    for record in lock["files"]:
        if record["provider"] == "wyscout" and record["path"].startswith("files/"):
            cache.get(record["path"], record["url"])
    directory = root / "data/raw/phase3/wyscout/files"
    players = json.loads((directory / "players.json").read_text())
    if len({p["wyId"] for p in players}) != len(players):
        raise ValueError("Conflicting duplicate Wyscout identity rows")
    people = {p["wyId"]: p for p in players}
    teams = {t["wyId"]: t for t in json.loads((directory / "teams.json").read_text())}
    comps = {c["wyId"]: c for c in json.loads((directory / "competitions.json").read_text())}
    groups: dict[tuple, list[dict]] = defaultdict(list)
    seasons: dict[int, set] = defaultdict(set)
    match_counts: Counter = Counter()
    missing = set()
    with zipfile.ZipFile(directory / "matches.zip") as archive:
        for name in sorted(archive.namelist()):
            if not name.endswith(".json") or archive.getinfo(name).file_size > 30_000_000:
                raise ValueError("Unexpected metadata archive member")
            for m in json.loads(archive.read(name)):
                cid = m["competitionId"]
                seasons[cid].add(m["seasonId"])
                match_counts[cid] += 1
                if comps[cid]["format"] != "Domestic league":
                    continue
                for tid, t in m["teamsData"].items():
                    formation = t["formation"]
                    substitutes = formation.get("substitutions") or []
                    if not isinstance(substitutes, list):
                        substitutes = []
                    incoming = {s["playerIn"] for s in substitutes}
                    starters = {p["playerId"] for p in formation["lineup"]}
                    for p in formation["lineup"] + formation["bench"]:
                        pid = p["playerId"]
                        if pid not in people:
                            missing.add(pid)
                            continue
                        groups[pid, cid, m["seasonId"], int(tid)].append(
                            dict(date=m["dateutc"][:10], played=pid in starters or pid in incoming)
                        )
    environments = []
    for (pid, cid, sid, tid), rows in sorted(groups.items()):
        p, c = people[pid], comps[cid]
        environments.append(
            dict(
                provider="wyscout",
                player_id=canonical_id("wyscout", "players", pid),
                environment_id=canonical_id(
                    "translation", "screening_environments", f"wyscout:{pid}:{cid}:{sid}:{tid}"
                ),
                identity_confidence="provider_id_unique_metadata",
                name=p["firstName"] + " " + p["lastName"],
                competition_id=cid,
                competition=c["name"],
                season_id=sid,
                season="2017/2018",
                season_start_year=2017,
                team_id=tid,
                team=teams[tid]["name"],
                country=c["area"]["name"],
                gender="male",
                environment_class="domestic",
                start_date=min(r["date"] for r in rows),
                end_date=max(r["date"] for r in rows),
                appearances=sum(r["played"] for r in rows),
                roster_appearances=len(rows),
                reliable_minutes=None,
                minutes_status="not_reconciled_metadata_screen",
            )
        )
    transitions = adjacent_transitions(environments)
    cross = [
        t
        for t in transitions
        if t["structurally_eligible"] and t["transition_type"] == "cross_league_change"
    ]
    pair = Counter((t["source_competition"], t["destination_competition"]) for t in cross)
    report = dict(
        provider="wyscout",
        licence="CC BY 4.0",
        source="https://figshare.com/collections/Soccer_match_event_dataset/4415000",
        players_metadata=len(people),
        domestic_roster_players=len({e["player_id"] for e in environments}),
        competitions=[
            dict(id=cid, name=comps[cid]["name"], seasons=sorted(seasons[cid]), matches=n)
            for cid, n in sorted(match_counts.items())
        ],
        metadata_missing_player_ids=sorted(missing),
        environments=len(environments),
        candidate_transitions=len(transitions),
        structural_rejections=dict(Counter(r for t in transitions for r in t["exclusion_reasons"])),
        cross_league_candidates=len(cross),
        cross_league_players=len({t["player_id"] for t in cross}),
        matrix=[dict(source=a, destination=b, candidates=n) for (a, b), n in sorted(pair.items())],
        feature_compatibility="Separate event ontology; no StatsBomb pressure, carry or xG equivalence assumed. No events pooled or model fitted.",
        limitation="Only one domestic season. Counts are provider-ID-linked ordered roster-context candidates, not reconciled-minute eligible episodes or contractual transfer records. No later domestic season for independent temporal validation.",
    )
    write(root / "artifacts/phase3/wyscout_audit.json", report)
    write(root / "data/processed/phase3/wyscout_environments.json", environments)
    return report
