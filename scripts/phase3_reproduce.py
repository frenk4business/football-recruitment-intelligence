"""Explicit offline rebuild from raw caches and fresh primary posterior sampling."""

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np

from football_intelligence.dna.cohort import write
from football_intelligence.translation.dataset import dataset, prepare
from football_intelligence.translation.evidence import audit_catalogue_identities
from football_intelligence.translation.materialize import materialize, settings
from football_intelligence.translation.models import fit, predict
from football_intelligence.translation.publish import publish
from football_intelligence.translation.wyscout import audit_wyscout


def hashes(directory: Path, pattern="*.json"):
    return {
        str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(directory.glob(pattern))
    }


def reproduce(root: Path):
    from phase3_reports import evidence_report

    local = root / "data/processed/phase3"
    expected = hashes(local) | hashes(local, "*.parquet")
    expected.pop("source_manifest.json")
    previous_sources = json.loads((local / "source_manifest.json").read_text())
    public = root / "artifacts/phase3/public"
    before = hashes(public, "**/*.json")
    backup = Path(tempfile.mkdtemp(prefix="fri-phase3-rebuild-")) / "processed"
    shutil.move(str(local), backup)
    try:
        with patch(
            "httpx.Client.send",
            side_effect=AssertionError("Offline rebuild attempted a source request"),
        ):
            audit_catalogue_identities(root)
            audit_wyscout(root)
            materialize(root)
            prepare(root)
            evidence_report(root)
        actual = hashes(local) | hashes(local, "*.parquet")
        differences = [p for p in expected if actual.get(p) != expected[p]]
        if differences:
            raise AssertionError(f"Rebuilt data changed: {differences}")
        current_sources = json.loads((local / "source_manifest.json").read_text())
        assert previous_sources["revision"] == current_sources["revision"]
        assert [r["source_hashes"] for r in previous_sources["matches"]] == [
            r["source_hashes"] for r in current_sources["matches"]
        ]
    except BaseException:
        if local.exists():
            shutil.rmtree(local)
        shutil.move(str(backup), local)
        raise
    cfg = settings(root)
    rows, _ = dataset(root)
    train = [r for r in rows if r["split"] != "test"]
    test = [r for r in rows if r["split"] == "test"]
    frozen = json.loads((root / "artifacts/phase3/heldout_predictions.json").read_text())
    result = {}
    for target in cfg["targets"]:
        for suffix in [".nc", ".json"]:
            (root / f"artifacts/phase3/posterior/reproduction-{target}{suffix}").unlink(
                missing_ok=True
            )
        trace, manifest = fit(root, train, target, cfg, "reproduction")
        pred = predict(trace, manifest["design"], test, seed=cfg["seed"] + 23)
        original = {
            r["transition_id"]: r["predictions"]["hierarchical_nb"]["mean"]
            for r in frozen
            if r["target"] == target
        }
        delta = float(
            np.max(np.abs(pred["mean"] - np.array([original[r["transition_id"]] for r in test])))
        )
        if delta > 0.03 or not manifest["diagnostics"]["passed"]:
            raise AssertionError("Fresh posterior failed reproducibility tolerance/diagnostics")
        result[target] = dict(
            max_absolute_expected_rate_difference=delta,
            tolerance=0.03,
            diagnostics=manifest["diagnostics"],
            fit_hash=manifest["fit_hash"],
        )
    publish(root)
    after = hashes(public, "**/*.json")
    if before != after:
        raise AssertionError("Precomputed public artifacts changed in offline rebuild")
    report = dict(
        source_requests=0,
        removed_processed_cache=True,
        processed_files_compared=len(expected),
        public_files_compared=len(before),
        public_byte_identical=True,
        fresh_primary_fits=result,
    )
    write(root / "artifacts/phase3/reproducibility.json", report)
    shutil.rmtree(backup.parent)
    print(
        "Reproduced",
        len(expected),
        "processed files and",
        len(before),
        "public files; four fresh fits passed.",
    )


if __name__ == "__main__":
    reproduce(Path.cwd())
