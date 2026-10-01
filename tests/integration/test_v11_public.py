"""Committed derived-only evidence; ordinary CI never downloads expanded events."""

import gzip
import json
from pathlib import Path

from football_intelligence.profiles import contracts
from football_intelligence.profiles.cache import checksum
from football_intelligence.profiles.features import COMMON_IDS
from football_intelligence.profiles.publish import profile_path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "artifacts/v11/public"


def test_every_v11_public_artifact_is_allowlisted_valid_and_bounded():
    inventory = json.loads((ROOT / "config/v11-public-artifacts.json").read_text())["files"]
    assert len(inventory) > 3000
    assert {str(p.relative_to(ROOT)) for p in PUBLIC.rglob("*.json")} == {
        r["source"] for r in inventory
    }
    for row in inventory:
        path = ROOT / row["source"]
        assert checksum(path) == row["sha256"] and path.stat().st_size == row["bytes"]
        getattr(contracts, row["schema"]).model_validate_json(path.read_bytes())
        if "/profiles/" in row["path"]:
            assert row["bytes"] < 50_000
    assert len(gzip.compress((PUBLIC / "index.json").read_bytes(), mtime=0)) < 1_000_000


def test_full_index_capabilities_neighbours_and_counts():
    index = contracts.ProfileIndex.model_validate_json((PUBLIC / "index.json").read_bytes())
    assert len(index.profiles) == index.counts.profiles
    assert index.counts.native_profiles == index.counts.profiles
    assert sum(p.capabilities.common for p in index.profiles) == index.counts.common_profiles
    assert sum(p.capabilities.translation for p in index.profiles) == 0
    by_id = {p.id: p for p in index.profiles}
    for p in index.profiles:
        assert p.minutes >= 450
        assert set(p.teams) <= set(index.teams)
        detail = contracts.ProfileDetail.model_validate_json(
            (PUBLIC / profile_path(p.id)).read_bytes()
        )
        assert detail.identity == p
        if detail.common:
            assert set(detail.common.model_dump()) == set(COMMON_IDS)
        for neighbor in detail.neighbours:
            other = by_id[neighbor.id]
            assert (other.provider, other.scope, other.role_family) == (
                p.provider,
                p.scope,
                p.role_family,
            )
            assert other.capabilities.common and other.id != p.id
        assert not p.capabilities.validated_dna or (
            p.scope == "statsbomb-37-281" and detail.dna_player_id
        )


def test_source_and_definition_provenance():
    manifest = json.loads((PUBLIC / "build-manifest.json").read_text())
    assert manifest["source_manifest_sha256"] == checksum(ROOT / "config/v11-sources.json")
    assert manifest["feature_manifest_sha256"] == checksum(PUBLIC / "registry.json")
    assert manifest["evaluation_sha256"] == checksum(ROOT / "artifacts/v11/evaluation.json")
    files = {r["path"] for r in json.loads((ROOT / "config/v11-sources.json").read_text())["files"]}
    for p in PUBLIC.glob("profiles/*/*.json"):
        detail = json.loads(p.read_text())
        assert all(f.split("#")[0] in files for f in detail["provenance"]["source_files"])
        assert detail["provenance"]["code_commit"] == manifest["code_commit"]
