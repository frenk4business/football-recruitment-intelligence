import hashlib
import json
from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from football_intelligence.api import create_app
from football_intelligence.recruitment.contracts import (
    ClubContext,
    RecruitmentBootstrap,
    RecruitmentEvaluation,
    RecruitmentIndex,
)


def assert_reference(actual, expected):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key, value in expected.items():
            assert_reference(actual[key], value)
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected, strict=True):
            assert_reference(a, b)
    elif isinstance(expected, float):
        assert actual == pytest.approx(expected, abs=1e-7)
    else:
        assert actual == expected


def test_recruitment_api_reference_and_validation(root):
    client = TestClient(create_app(root / "artifacts"))
    base = "/api/v1/recruitment"
    index = client.get(base).json()
    RecruitmentIndex.model_validate(index)
    assert len(client.get(base + "/clubs").json()) == 12
    assert len(client.get(base + "/requirements").json()) == 18
    assert all(p["role"] == "CB" for p in client.get(base + "/candidates?role=CB").json())
    assert client.get(base + "/candidates?role=GK").status_code == 422
    assert client.get(base + "/clubs/" + str(uuid4())).status_code == 404
    assert client.get(base + "/clubs/invalid").status_code == 422
    ClubContext.model_validate(client.get(base + "/clubs/" + index["clubs"][0]["club_id"]).json())
    RecruitmentEvaluation.model_validate(client.get(base + "/evaluation").json())
    cases = json.loads((root / "artifacts/phase4/reference_cases.json").read_text())["cases"]
    for case in cases:
        response = client.post(base + "/scenario", json=case["scenario"])
        assert response.status_code == 200
        assert_reference(response.json(), case["result"])
    scenario = cases[0]["scenario"]
    for patch in [
        {"club_id": "unknown"},
        {"mode": "replace"},
        {"season": "2024/2025"},
        {"translation_mode": "predicted"},
        {"price": 1},
    ]:
        assert client.post(base + "/scenario", json={**scenario, **patch}).status_code == 422
    invalid = deepcopy(scenario)
    invalid["requirements"][0]["feature_id"] = "market_value"
    assert client.post(base + "/scenario", json=invalid).status_code == 422
    assert TestClient(create_app(root / "missing")).get(base).status_code == 503


def test_public_allowlists_manifest_and_cohort_consistency(root):
    base = root / "artifacts/phase4"
    manifest = json.loads((base / "recruitment_manifest.json").read_text())
    public = base / "public"
    assert len(manifest["public_sha256"]) == 20
    assert set(manifest["public_sha256"]) == {
        str(p.relative_to(public)) for p in public.rglob("*.json")
    }
    for name, digest in manifest["public_sha256"].items():
        path = public / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        text = path.read_text()
        assert all(
            f'"{key}"' not in text
            for key in [
                "events",
                "attributes_json",
                "provider_id",
                "lineups",
                "tracking_snapshots",
                "market_value",
                "birth_date",
            ]
        )
        model = (
            RecruitmentIndex
            if name == "index.json"
            else RecruitmentEvaluation
            if name == "evaluation.json"
            else ClubContext
            if name.startswith("clubs/")
            else RecruitmentBootstrap
        )
        model.model_validate_json(text)
        with pytest.raises(ValidationError):
            model.model_validate({**json.loads(text), "raw_payload": {}})
    index = json.loads((public / "index.json").read_text())
    assert len(index["players"]) == 336 and sum(p["eligible"] for p in index["players"]) == 138
    for role in index["roles"]:
        boot = json.loads((public / "bootstrap" / (role.replace("/", "-") + ".json")).read_text())
        assert set(boot["player_ids"]) == {
            p["player_id"] for p in index["players"] if p["eligible"] and p["role"] == role
        }
        assert boot["samples"] == 100
    for club in index["clubs"]:
        context = json.loads((public / "clubs" / (club["club_id"] + ".json")).read_text())
        assert context["season"] == index["season"] and context["matches"] == 22
        assert all(f["available_matches"] == 22 for f in context["features"])


def test_frozen_selection_precedes_final_queries_and_retains_negative_evidence(root):
    base = root / "artifacts/phase4"
    decision = json.loads((base / "method_selection.json").read_text())
    assert (
        decision["development_sha256"]
        == hashlib.sha256((base / "development_evaluation.json").read_bytes()).hexdigest()
    )
    assert (
        decision["experiment_sha256"]
        == hashlib.sha256((root / "docs/phase-4-experiment-plan.md").read_bytes()).hexdigest()
    )
    final = json.loads((base / "final_evaluation.json").read_text())
    split = final["split"]
    assert not set(split["development_clubs"]) & set(split["final_clubs"])
    assert len(split["development_clubs"]) == 8 and len(split["final_clubs"]) == 4
    assert final["temporal"]["metrics"]["weighted_rms"]["queries"] == 31
    assert final["roster"]["metrics"]["weighted_rms"]["queries"] == 27
    # Every registered comparator remains published even when its final result is poorer.
    assert {
        "weighted_rms",
        "family_rms",
        "satisfaction",
        "hybrid",
        "dna_nearest_neighbor",
    } <= final["temporal"]["metrics"].keys()
