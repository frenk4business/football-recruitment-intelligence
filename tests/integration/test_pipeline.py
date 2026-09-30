import json
from copy import deepcopy

import polars as pl
import pytest

from football_intelligence.data.fetch import digest, load_raw
from football_intelligence.data.marts import build_marts, connect
from football_intelligence.data.validation import validate
from football_intelligence.pipeline import build


def test_parquet_duckdb_and_metric_availability(tmp_path, tables):
    assert validate(tables)["status"] == "passed"
    for name, df in tables.items():
        df.write_parquet(tmp_path / f"{name}.parquet")
    marts = build_marts(tmp_path)
    pm = marts["player_match"]
    shooter = pm.filter((pl.col("provider") == "statsbomb") & (pl.col("shots") > 0)).row(
        0, named=True
    )
    assert shooter["shots"] == 1  # shootout excluded
    assert shooter["goals"] == 1
    assert shooter["xg"] == pytest.approx(0.3)
    assert shooter["shots_per90"] == pytest.approx(1)
    assert shooter["pass_completion"] == 1
    assert pm.filter(pl.col("provider") == "skillcorner")["shots"].null_count() == 2
    with connect(tmp_path) as con:
        assert con.sql("SELECT count(*) FROM matches").fetchone()[0] == 2
    for name, df in tables.items():
        assert pl.read_parquet(tmp_path / f"{name}.parquet").equals(df)


def test_unresolved_reference_rejected(tables):
    bad = {**tables, "events": tables["events"].with_columns(pl.lit("missing").alias("match_id"))}
    with pytest.raises(ValueError, match="unresolved"):
        validate(bad)


def test_duplicate_primary_key_rejected(tables):
    bad = {**tables, "events": pl.concat([tables["events"], tables["events"].head(1)])}
    with pytest.raises(ValueError, match="duplicate"):
        validate(bad)


def test_outside_coordinate_envelope_rejected(tables):
    bad = {**tables, "events": tables["events"].with_columns(pl.lit(999.0).alias("x"))}
    with pytest.raises(ValueError, match="envelope"):
        validate(bad)


def test_timestamp_anomaly_is_reported(tables):
    df = tables["events"].with_columns(
        pl.when(pl.col("index") == 1)
        .then(0)
        .otherwise(pl.col("timestamp_seconds"))
        .alias("timestamp_seconds")
    )
    report = validate({**tables, "events": df})
    assert any("timestamp inversions" in s for s in report["warnings"])


def test_build_is_idempotent_offline(tmp_path, root, fixtures, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/sample.json").write_bytes((root / "config/sample.json").read_bytes())

    def fake_load(root, provider):
        return deepcopy(fixtures[provider]), {
            "provider": provider,
            "files": [{"url": "test-fixture-only", "sha256": "fixture-hash"}],
        }

    monkeypatch.setattr("football_intelligence.pipeline.load_raw", fake_load)
    first = build(tmp_path)
    first_public = {
        p.name: p.read_bytes() for p in (tmp_path / "artifacts/explorer").glob("*.json")
    }
    second = build(tmp_path)
    assert first_public == {
        p.name: p.read_bytes() for p in (tmp_path / "artifacts/explorer").glob("*.json")
    }
    assert first["row_counts"] == second["row_counts"]
    assert first["parquet_sha256"] == second["parquet_sha256"]
    assert len(list((tmp_path / "artifacts/explorer").glob("*.json"))) == 2
    assert first["lineage"]


def test_cache_tampering_fails_before_parsing(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/sample.json").write_text(json.dumps({"statsbomb": {"revision": "pinned"}}))
    raw = tmp_path / "data/raw/statsbomb"
    raw.mkdir(parents=True)
    (raw / "events.json").write_text("tampered")
    (raw / "manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {"key": "events", "sha256": digest(b"original"), "source_revision": "pinned"}
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="checksum"):
        load_raw(tmp_path, "statsbomb")
