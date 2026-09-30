import json
from copy import deepcopy

import httpx
import pytest
import yaml

from football_intelligence.dna.cohort import retrieve


def test_cohort_cache_pin_and_corruption(tmp_path, fixtures, monkeypatch):
    (tmp_path / "config").mkdir()
    cfg = dict(
        cohorts={"test": dict(repository="test/repo", revision="a" * 40, competition=1, season=1)}
    )
    (tmp_path / "config/cohorts.yaml").write_text(yaml.safe_dump(cfg))
    raw = deepcopy(fixtures["statsbomb"])
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if str(request.url).endswith("competitions.json"):
            value = [raw["competition"]]
        elif "/matches/" in str(request.url):
            value = [raw["match"]]
        elif "/events/" in str(request.url):
            value = raw["events"]
        else:
            value = raw["lineups"]
        return httpx.Response(200, json=value)

    client_class = httpx.Client
    monkeypatch.setattr(
        "football_intelligence.dna.cohort.httpx.Client",
        lambda **kwargs: client_class(transport=httpx.MockTransport(handler)),
    )
    first = retrieve(tmp_path, "test")
    assert len(calls) == 4 and first["complete"]
    # Cache-only retrieval must not open a network response even with a closed client.
    second = retrieve(tmp_path, "test")
    assert first == second and len(calls) == 4
    directory = tmp_path / "data/raw/cohorts/test" / ("a" * 40)
    (directory / "data/events/1.json").write_text("tampered")
    with pytest.raises(ValueError, match="checksum"):
        retrieve(tmp_path, "test")
    assert json.loads((tmp_path / "config/test.sources.json").read_text()) == first
