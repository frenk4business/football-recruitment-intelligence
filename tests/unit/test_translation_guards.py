import json

import pytest

from football_intelligence.translation.evaluation import choose
from football_intelligence.translation.sources import SourceCache


def test_locked_cache_detects_tampering_even_if_local_sidecar_is_changed(tmp_path):
    import hashlib

    directory = tmp_path / "data/raw/phase3/wyscout"
    directory.mkdir(parents=True)
    (tmp_path / "config").mkdir()
    digest = hashlib.sha256(b"original").hexdigest()
    (tmp_path / "config/phase3.sources.json").write_text(
        json.dumps({"files": [{"provider": "wyscout", "path": "sample.json", "sha256": digest}]})
    )
    (directory / "sample.json").write_bytes(b"changed")
    (directory / "sample.json.sha.json").write_text(
        json.dumps(
            {"url": "https://example.test/sample", "sha256": hashlib.sha256(b"changed").hexdigest()}
        )
    )
    with pytest.raises(ValueError, match="Source cache mismatch"):
        SourceCache(directory).get("sample.json", "https://example.test/sample")


def test_model_selection_requires_both_point_and_predictive_quality():
    import copy

    good = {"mae": 1.0, "intervals": {"80": {"coverage": 0.8, "mean_width": 2.0}}}
    results = {
        m: copy.deepcopy(good)
        for m in ["unchanged_source", "role_mean", "ridge", "hierarchical_nb"]
    }
    assert choose(results, {"passed": True}) == ("hierarchical_nb", [])
    results["hierarchical_nb"]["intervals"]["80"]["coverage"] = 0.6
    assert choose(results, {"passed": True}) == ("unchanged_source", ["validation_coverage"])
    results["hierarchical_nb"] = copy.deepcopy(good)
    results["hierarchical_nb"]["mae"] = 1.11
    assert choose(results, {"passed": True}) == ("unchanged_source", ["validation_point_error"])
    results["hierarchical_nb"] = copy.deepcopy(good)
    assert choose(results, {"passed": False}) == ("unchanged_source", ["diagnostic_gate"])
