"""Real derived artifacts validate the publication/API boundary; no source download."""

import json

import pytest
from fastapi.testclient import TestClient

from football_intelligence.api import create_app
from football_intelligence.dna.contracts import DNAIndex, DNAProfile
from football_intelligence.dna.registry import CORE


def test_public_profiles_have_threshold_role_isolation_and_explanations(root):
    directory = root / "artifacts/phase2/public"
    index = DNAIndex.model_validate_json((directory / "index.json").read_text())
    for threshold in index.thresholds:
        eligible = []
        for player in index.players:
            p = DNAProfile.model_validate_json(
                (directory / str(threshold) / f"{player.player_id}.json").read_text()
            )
            assert p.version == "player-dna-v1"
            assert p.eligible == (not p.exclusions)
            if not p.eligible:
                assert not p.neighbors and p.scaled_vector is None
                continue
            eligible.append(p)
            assert p.player.minutes >= threshold and p.player.primary_role != "GK"
            assert p.comparison_size >= 12 and len(p.scaled_vector) == len(CORE)
            assert all(f.value is not None for f in p.features if f.id in CORE)
            assert p.neighbors == sorted(p.neighbors, key=lambda n: (n.distance, n.player_id))
            for n in p.neighbors:
                assert n.player_id != p.player.player_id and n.role == p.player.primary_role
                assert n.minutes >= threshold
                assert sum(f.squared_contribution for f in n.contributions) == pytest.approx(
                    n.distance**2, abs=1e-6
                )
                assert sum(n.family_contributions.values()) == pytest.approx(1, abs=1e-6)
        report = json.loads((root / "artifacts/phase2/cohort_eligibility.json").read_text())
        assert len(eligible) == report["thresholds"][str(threshold)]["eligible"]


def test_dna_api_validates_ids_thresholds_and_pagination(root):
    client = TestClient(create_app(root / "artifacts"))
    response = client.get("/api/v1/player-dna")
    assert response.status_code == 200
    index = response.json()
    pid = next(p["player_id"] for p in index["players"] if not p["eligibility"]["900"])
    assert client.get(f"/api/v1/player-dna/{pid}").json()["eligible"]
    assert len(client.get(f"/api/v1/player-dna/{pid}/similar?limit=3").json()) == 3
    assert client.get(f"/api/v1/player-dna/{pid}?threshold=901").status_code == 422
    assert client.get(f"/api/v1/player-dna/{pid}/similar?limit=100").status_code == 422
    assert client.get("/api/v1/player-dna/not-a-uuid").status_code == 422
    assert client.get("/api/v1/player-dna/00000000-0000-0000-0000-000000000000").status_code == 404
    assert client.get("/api/v1/similarity/evaluation").status_code == 200
    assert client.get("/api/v1/features").status_code == 200


def test_missing_artifacts_return_unavailable(tmp_path):
    assert TestClient(create_app(tmp_path)).get("/api/v1/player-dna").status_code == 503


def test_public_artifacts_never_contain_raw_event_fields(root):
    forbidden = {
        "attributes_json",
        "provider_positions_json",
        "participation_json",
        "related_events",
        "freeze_frame",
        "shot",
        "pass",
        "raw_x",
        "raw_y",
        "timestamp_seconds",
        "event_type",
    }

    def inspect(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for v in value.values():
                inspect(v)
        elif isinstance(value, list):
            for v in value:
                inspect(v)

    for path in (root / "artifacts/phase2/public").rglob("*.json"):
        inspect(json.loads(path.read_text()))
    assert (root / "artifacts/phase2/public/index.json").stat().st_size < 300_000
    assert (
        max(p.stat().st_size for p in (root / "artifacts/phase2/public").glob("*/*.json")) < 100_000
    )
