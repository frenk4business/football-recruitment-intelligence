"""Richer native features from verified cached events; does not rewrite v1.1."""

import json
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from football_intelligence.expansion.features import KEYS, VERSION, count_events, registry, values
from football_intelligence.profiles.cache import checksum, write_json


def aggregate(rows: list[dict]) -> dict:
    counts = {key: sum(r["counts"][key] for r in rows) for key in KEYS}
    missing = {key for r in rows for key in r["missing"]}
    reasons = {reason for r in rows for reason in r["reasons"]}
    reliable = all(r["reliable"] and r["minutes"] is not None for r in rows)
    minutes = sum(r["minutes"] or 0 for r in rows)
    team_minutes: Counter = Counter()
    for r in rows:
        team_minutes[str(r["team_id"])] += r["minutes"] or 0
    return {
        "minutes": round(minutes, 6),
        "minutes_reliable": reliable,
        "minutes_method": "nominal_regulation_roster_substitution_card",
        "quality_reason": sorted(reasons),
        "matches": len(rows),
        "features": values(counts, missing, minutes) if reliable else dict.fromkeys(KEYS),
        "missing_features": sorted(missing),
        "team_minutes": dict(team_minutes),
        "observation_start": min(r["date"] for r in rows),
        "observation_end": max(r["date"] for r in rows),
    }


def build(root: Path):
    plan = root / "docs/v1.2-wyscout-recruitment-plan.md"
    if not plan.exists():
        raise ValueError("Evaluation plan must be registered before feature extraction")
    destination = root / "data/processed/v12/wyscout"
    destination.mkdir(parents=True, exist_ok=True)
    reports, profiles, splits = [], [], []
    for folder in sorted(
        (root / "data/processed/v11/full/provider=wyscout").glob("competition=*/season=*")
    ):
        manifest = json.loads((folder / "manifest.json").read_text())
        for name, digest in manifest["files"].items():
            if checksum(folder / name) != digest:
                raise ValueError(f"Unverified cached partition: {folder}/{name}")
        quality = json.loads((folder / "quality.json").read_text())
        scope = quality["scope"]
        observations = pq.read_table(folder / "observations.parquet").to_pylist()
        lookup = {(r["match_id"], r["player_id"]): r for r in observations}
        rows: list[dict] = []
        events_count = 0
        current_mid = None
        events: list[dict] = []

        def process(group, lookup=lookup, rows=rows):
            actors: dict[int, list] = defaultdict(list)
            for event in group:
                if event["player_id"] > 0:
                    actors[event["player_id"]].append(event)
            mid = group[0]["match_id"]
            for (match_id, pid), row in lookup.items():
                if match_id != mid:
                    continue
                counts, missing = count_events(actors.get(pid, []))
                rows.append(
                    {
                        **{
                            k: row[k]
                            for k in [
                                "player_id",
                                "name",
                                "match_id",
                                "date",
                                "team_id",
                                "minutes",
                                "reliable",
                                "reasons",
                                "role_family",
                            ]
                        },
                        "counts": counts,
                        "missing": missing,
                    }
                )

        for batch in pq.ParquetFile(folder / "events.parquet").iter_batches(batch_size=16384):
            for event in batch.to_pylist():
                mid = event["match_id"]
                if events and mid != current_mid:
                    process(events)
                    events = []
                current_mid = mid
                events.append(event)
                events_count += 1
        if events:
            process(events)
        if len(rows) != len(observations):
            raise ValueError("Not every participation row received explicit feature counts")
        players: dict[int, list] = defaultdict(list)
        for row in rows:
            players[row["player_id"]].append(row)
        for pid, entries in sorted(players.items()):
            entries.sort(key=lambda r: (r["date"], r["match_id"]))
            identity = {
                "id": f"{scope}-{pid}",
                "provider": "wyscout",
                "scope": scope,
                "provider_player_id": str(pid),
                "name": entries[0]["name"],
                "role": entries[0]["role_family"],
                "competition_id": str(quality["competition_id"]),
                "season_id": str(quality["season_id"]),
                "competition": quality["competition"],
                "season": quality["season"],
                "feature_registry_version": VERSION,
            }
            profiles.append({**identity, **aggregate(entries)})
            if len(entries) >= 2:
                splits.append(
                    {**identity, "halves": [aggregate(entries[::2]), aggregate(entries[1::2])]}
                )
        pq.write_table(
            pa.Table.from_pylist(rows), destination / f"{scope}.parquet", compression="zstd"
        )
        reports.append(
            {
                **quality,
                "processed_events": events_count,
                "match_rows": len(rows),
                "profiles": len(players),
                "source_partition_hashes": manifest["files"],
            }
        )
        print(
            f"Wyscout richer extraction {scope}: {len(players)} profiles, {events_count} events",
            flush=True,
        )
    write_json(destination / "profiles.json", profiles, compact=True)
    write_json(destination / "splits.json", splits, compact=True)
    write_json(root / "artifacts/v12/wyscout-ingestion.json", reports)
    write_json(root / "artifacts/v12/wyscout-feature-registry.json", registry())
    return profiles, splits
