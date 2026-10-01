"""Measure pinned source coverage and local partition sizes; no raw records published."""

import json
import zipfile
from collections import Counter
from pathlib import Path

from football_intelligence.profiles.ingest import iter_json_array

root = Path.cwd()
destination = root / "data/processed/v11/full"
rows = json.loads((destination / "aggregates.json").read_text())
result = {
    "raw_participating_player_seasons": len(rows),
    "provider_participating_identities": {
        p: len({r["player_id"] for r in rows if r["provider"] == p})
        for p in ["statsbomb", "wyscout"]
    },
    "raw_profile_exclusion_reasons": dict(Counter(k for r in rows for k in r["exclusion_reasons"])),
    "source_bytes": {},
    "processed_bytes": {},
}
for provider in ["statsbomb", "wyscout"]:
    result["source_bytes"][provider] = sum(
        p.stat().st_size
        for p in (root / "data/raw/v11/sources" / provider).rglob("*")
        if p.is_file() and not p.name.endswith(".sha.json")
    )
    result["processed_bytes"][provider] = sum(
        p.stat().st_size for p in (destination / f"provider={provider}").rglob("*.parquet")
    )
base = root / "data/raw/v11/sources/wyscout"
result["wyscout_all_metadata_players"] = len(json.loads((base / "players.json").read_text()))
with zipfile.ZipFile(base / "matches.zip") as z:
    result["wyscout_all_competition_matches"] = {
        p: len(json.loads(z.read(p))) for p in z.namelist() if p.endswith(".json")
    }
with zipfile.ZipFile(base / "events.zip") as z:
    result["wyscout_additional_international_events"] = {
        p: sum(1 for _ in iter_json_array(z.open(p)))
        for p in z.namelist()
        if "European" in p or "World" in p
    }
result["canonical_parquet_files"] = len(
    list(destination.glob("provider=*/competition=*/season=*/events.parquet"))
)
result["observations_parquet_files"] = len(
    list(destination.glob("provider=*/competition=*/season=*/observations.parquet"))
)
(root / "artifacts/v11/storage-audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
