"""CI validates committed derived data offline; never fetch full event feeds."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from football_intelligence.expansion import contracts
from football_intelligence.expansion.features import KEYS

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


def test_v12_derived_allowlist_schemas_hashes_and_safe_paths():
    inventory = read("config/v12-public-artifacts.json")["files"]
    assert {r["source"] for r in inventory} == {
        str(p.relative_to(ROOT)) for p in (ROOT / "artifacts/v12/public").rglob("*.json")
    }
    for row in inventory:
        assert row["path"].startswith("data/v12/") and ".." not in row["path"]
        data = (ROOT / row["source"]).read_bytes()
        assert (
            len(data) == row["bytes"] <= 3_000_000
            and hashlib.sha256(data).hexdigest() == row["sha256"]
        )
        getattr(contracts, row["schema"]).model_validate_json(data)
    subprocess.run(
        [sys.executable, "scripts/generate_expansion_contracts.py", "--check"], cwd=ROOT, check=True
    )


def test_capabilities_counts_gates_and_scope_isolation():
    index = read("artifacts/v12/public/index.json")
    assert index["counts"]["profiles"] == len(index["profiles"])
    assert index["counts"]["provider_identities"] == len(
        {(p["provider"], p["id"].split("-")[-1]) for p in index["profiles"]}
    )
    old = read("artifacts/v11/public/index.json")
    assert {p["id"] for p in old["profiles"]} <= {p["id"] for p in index["profiles"]}
    capabilities = read("artifacts/v12/recruitment_capability.json")["competitions"]
    registry = read("artifacts/v12/public/recruitment/index.json")
    assert (
        len(registry["leagues"]) == 5
        and sum(league["clubs"] for league in registry["leagues"]) == 98
    )
    assert len(capabilities) == 85
    for cap in capabilities:
        if cap["provider"] != "wyscout":
            continue
        league = read(f"artifacts/v12/public/recruitment/{cap['scope']}.json")
        assert (
            cap["recruitment_enabled"]
            and not cap["translation_enabled"]
            and cap["coverage_status"] == "complete"
        )
        evidence = next(
            r
            for r in cap["evaluation"]["threshold_grid"]
            if r["minutes_threshold"] == cap["minutes_threshold"]
        )
        assert all(evidence["roles"][role]["passed"] for role in league["roles"])
        assert all(
            p["scope"] == league["scope"]
            and set(p["features"]) == set(KEYS)
            and p["role"] in league["roles"]
            for p in league["players"]
        )
        assert all(len(r["players"]) >= 2 for club in league["clubs"] for r in club["roles"])
    new = [p for p in index["profiles"] if "/v12/profiles/" in p["detail_path"]]
    assert len(new) == 665 and not any(
        p["capabilities_v12"]["recruitment"]
        or p["capabilities_v12"]["translation"]
        or p["capabilities_v12"]["similarity"]
        for p in new
    )
    metadata = read("artifacts/v12/public/metadata/index.json")
    assert all(not s["capabilities"]["recruitment"] for s in metadata["competitions"])
    assert index["counts"]["metadata_clubs"] == sum(
        not c["performance_scopes"] for c in metadata["clubs"]
    )


def test_new_sources_are_pinned_official_and_inventory_is_complete():
    lock = read("config/v12-sources.json")
    assert (
        lock["audit_sha256"]
        == hashlib.sha256((ROOT / "artifacts/v12/source-audit.json").read_bytes()).hexdigest()
    )
    assert len({r["path"] for r in lock["files"]}) == len(lock["files"])
    for r in lock["files"]:
        assert r["url"].startswith("https://raw.githubusercontent.com/")
        assert r["path"].split("/")[1] in r["url"] and len(r["sha256"]) == 64
    plan = read("artifacts/v12/wyscout-evaluation.json")
    assert (
        plan["plan_sha256"]
        == hashlib.sha256((ROOT / "config/v12-expansion.json").read_bytes()).hexdigest()
    )
