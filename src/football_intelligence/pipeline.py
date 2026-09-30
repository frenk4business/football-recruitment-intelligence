import json
import shutil
from pathlib import Path

import polars as pl

from football_intelligence.data.adapters.base import Adapter
from football_intelligence.data.adapters.skillcorner import SkillCornerAdapter
from football_intelligence.data.adapters.statsbomb import StatsBombAdapter
from football_intelligence.data.fetch import digest, load_raw
from football_intelligence.data.marts import build_marts
from football_intelligence.data.schema import TABLES, frame_from_records
from football_intelligence.data.validation import validate
from football_intelligence.export import export


def build(root: Path) -> dict:
    combined: dict[str, list[dict]] = {t: [] for t in TABLES}
    manifests = []
    adapters: list[Adapter] = [StatsBombAdapter(), SkillCornerAdapter()]
    for adapter in adapters:
        raw, manifest = load_raw(root, adapter.provider)
        provenance_id = digest(
            json.dumps(
                [(f["url"], f["sha256"]) for f in manifest["files"]], sort_keys=True
            ).encode()
        )
        manifest["provenance_id"] = provenance_id
        manifests.append(manifest)
        for table, rows in adapter.normalise(raw, provenance_id).items():
            combined[table].extend(rows)
    tables = {
        t: frame_from_records(TABLES[t], rows).sort(
            "canonical_id" if t == "provider_entity_map" else "id"
        )
        for t, rows in combined.items()
    }
    report = validate(tables)
    staging = root / "data/interim/build"
    staging.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.write_parquet(staging / f"{name}.parquet", compression="zstd", statistics=True)
    marts = build_marts(staging)
    for name, df in marts.items():
        df.write_parquet(staging / f"{name}.parquet", compression="zstd", statistics=True)
    processed = root / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    for p in staging.glob("*.parquet"):
        shutil.copy2(p, processed / p.name)
    return export(root, tables, marts, report, manifests)


def validate_stored(root: Path) -> dict:
    return validate({t: pl.read_parquet(root / "data/processed" / f"{t}.parquet") for t in TABLES})
