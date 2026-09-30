import json
from pathlib import Path

import pytest

from football_intelligence.data.adapters.skillcorner import SkillCornerAdapter
from football_intelligence.data.adapters.statsbomb import StatsBombAdapter
from football_intelligence.data.schema import TABLES, frame_from_records


@pytest.fixture
def root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def fixtures(root):
    return {
        p: json.loads((root / f"data/fixtures/{p}.json").read_text())
        for p in ["statsbomb", "skillcorner"]
    }


@pytest.fixture
def tables(fixtures):
    combined = {t: [] for t in TABLES}
    for adapter in [StatsBombAdapter(), SkillCornerAdapter()]:
        result = adapter.normalise(fixtures[adapter.provider], "test-only-provenance")
        for t, rows in result.items():
            combined[t].extend(rows)
    return {t: frame_from_records(TABLES[t], rows) for t, rows in combined.items()}
