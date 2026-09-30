import json
from uuid import uuid4

from fastapi.testclient import TestClient

from football_intelligence.api import create_app
from football_intelligence.contracts import Coverage, Explorer


def test_api_health_and_pagination(root):
    client = TestClient(create_app(root / "artifacts"))
    assert client.get("/health").json()["data_ready"]
    Coverage.model_validate(client.get("/api/v1/coverage").json())
    rows = client.get("/api/v1/matches?provider=statsbomb&limit=1").json()
    assert len(rows) == 1
    payload = client.get("/api/v1/explorer/" + rows[0]["id"]).json()
    Explorer.model_validate(payload)
    assert (
        client.get("/api/v1/players", params={"match_id": rows[0]["id"], "limit": 2}).json()
        == payload["players"][:2]
    )
    for route in ["/api/v1/sources", "/api/v1/competitions", "/api/v1/metrics", "/openapi.json"]:
        assert client.get(route).status_code == 200


def test_api_invalid_inputs(root):
    c = TestClient(create_app(root / "artifacts"))
    for url in [
        "/api/v1/matches?provider=unknown",
        "/api/v1/matches?limit=100000",
        "/api/v1/matches?offset=-1",
        "/api/v1/players?match_id=../../etc/passwd",
        "/api/v1/explorer/not-a-uuid",
    ]:
        assert c.get(url).status_code == 422
    assert c.get("/api/v1/explorer/" + str(uuid4())).status_code == 404
    assert c.get("/api/v1/sql").status_code == 404


def test_no_artifacts_is_explicit(tmp_path):
    c = TestClient(create_app(tmp_path))
    assert not c.get("/health").json()["data_ready"]
    assert c.get("/api/v1/coverage").status_code == 503


def test_cors_is_restricted(root):
    c = TestClient(create_app(root / "artifacts"))
    assert (
        "access-control-allow-origin"
        not in c.get("/health", headers={"Origin": "https://untrusted.example"}).headers
    )
    assert (
        c.get("/health", headers={"Origin": "http://localhost:3000"}).headers[
            "access-control-allow-origin"
        ]
        == "http://localhost:3000"
    )


def test_public_exports_have_no_raw_statsbomb_events_or_test_fixtures(root):
    matches = json.loads((root / "artifacts/matches.json").read_text())
    for m in matches:
        text = (root / f"artifacts/explorer/{m['id']}.json").read_text()
        assert "TEST FIXTURE" not in text
        payload = json.loads(text)
        assert payload["event_counts"] == sorted(
            payload["event_counts"], key=lambda r: (-r["count"], r["event_type"])
        )
        assert "events" not in payload
        assert "attributes_json" not in text
        assert "provider_id" not in text
        if m["provider"] == "statsbomb":
            assert not payload["tracking_snapshots"]
            assert (
                sum(b["count"] for b in payload["spatial_bins"]) == payload["spatial_sample_size"]
            )
