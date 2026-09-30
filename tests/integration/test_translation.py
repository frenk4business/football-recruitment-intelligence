"""Real aggregate contracts and immutable temporal evaluation; no football downloads."""

import hashlib
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from football_intelligence.api import create_app
from football_intelligence.translation.contracts import TranslationIndex, TranslationPlayerDetail


def test_publication_allowlist_ranges_and_temporal_context(root):
    directory = root / "artifacts/phase3/public"
    index = TranslationIndex.model_validate_json((directory / "index.json").read_text())
    manifest = json.loads((directory.parent / "publication_manifest.json").read_text())
    forbidden = {
        "events",
        "lineups",
        "posterior",
        "posterior_predictive",
        "match_ids",
        "raw_payload",
        "provider_payload",
    }

    def audit(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for v in value.values():
                audit(v)
        elif isinstance(value, list):
            for v in value:
                audit(v)

    supported = rejected = 0
    for player in index.players:
        path = directory / "players" / f"{player.player_id}.json"
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == manifest["sha256"][str(path.relative_to(directory))]
        )
        detail = TranslationPlayerDetail.model_validate_json(path.read_text())
        audit(detail.model_dump())
        envs = {e.environment_id: e for e in detail.environments}
        for p in detail.predictions:
            source = envs[p.source_environment_id]
            assert p.model_version == index.version
            if p.status != "supported":
                rejected += 1
                assert p.exclusions and not p.estimates and not p.research_estimates
                continue
            supported += 1
            assert (
                source.supported and source.season == "2019/2020" and source.reliable_minutes >= 600
            )
            assert p.evidence.context_latest_date <= source.end_date
            assert p.evidence.source_context_matches >= 3 and p.evidence.target_context_matches >= 3
            assert p.evidence.role_episodes >= 5
            assert len(p.estimates) == len(p.research_estimates) == 4
            for estimate in [*p.estimates, *p.research_estimates]:
                assert 0 <= estimate.p025 <= estimate.p10 <= estimate.p90 <= estimate.p975
    assert supported == manifest["scenario_statuses"]["supported"] and rejected > 0
    assert manifest["largest_player_bytes"] < 150_000


def test_frozen_validation_selection_and_no_target_period_overlap(root):
    base = root / "artifacts/phase3"
    validation = json.loads((base / "validation.json").read_text())
    test = json.loads((base / "translation_evaluation.json").read_text())
    split = test["split"]
    assert (
        test["selection_hash"]
        == hashlib.sha256(json.dumps(validation, sort_keys=True).encode()).hexdigest()
    )
    assert split["destination_date_range"]["train"][1] < split["destination_date_range"]["test"][0]
    assert not set(split["episode_ids"]["test"]) & set(
        split["episode_ids"]["train"] + split["episode_ids"]["validation"]
    )
    for target, result in test["targets"].items():
        assert result["selected_method"] == validation["targets"][target]["selected_method"]
        assert result["fit"]["episodes"] == 65
        assert result["fit"]["diagnostics"]["passed"]
        assert result["fit"]["destination_dates"][1] < split["destination_date_range"]["test"][0]


def test_translation_api_lookup_and_unsupported_states(root):
    client = TestClient(create_app(root / "artifacts"))
    index = client.get("/api/v1/translation/environments").json()
    player = next(p for p in index["players"] if p["supported_sources"])
    detail = client.get(f"/api/v1/translation/players/{player['player_id']}").json()
    for status in ["supported", "out_of_scope", "insufficient_evidence"]:
        prediction = next(p for p in detail["predictions"] if p["status"] == status)
        response = client.get(
            "/api/v1/translation/predict",
            params=dict(
                player_id=player["player_id"],
                source_environment=prediction["source_environment_id"],
                target_environment=prediction["target_environment_id"],
                target_role=prediction["target_role"],
            ),
        )
        assert response.status_code == 200 and response.json() == prediction
    assert client.get("/api/v1/translation/models").json()["provider"] == "statsbomb"
    assert client.get("/api/v1/translation/evaluation").json()["test"] == 76
    assert client.get("/api/v1/translation/players/not-an-id").status_code == 422
    assert (
        client.get("/api/v1/translation/players/00000000-0000-0000-0000-000000000000").status_code
        == 404
    )
    prediction["status"] = "out_of_scope"
    prediction["estimates"] = next(
        p["estimates"] for p in detail["predictions"] if p["status"] == "supported"
    )
    with pytest.raises(ValidationError, match="Unsupported translation"):
        from football_intelligence.translation.contracts import TranslationPrediction

        TranslationPrediction(**prediction)


def test_public_contract_rejects_raw_payload_and_nonfinite_values(root):
    base = root / "artifacts/phase3/public"
    detail = json.loads(next((base / "players").glob("*.json")).read_text())
    with pytest.raises(ValidationError):
        TranslationPlayerDetail(**dict(detail, events=[]))
    detail["environments"][0]["reliable_minutes"] = float("nan")
    with pytest.raises(ValidationError):
        TranslationPlayerDetail(**detail)
