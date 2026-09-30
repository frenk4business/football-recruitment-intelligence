import json

import numpy as np
import pytest

from football_intelligence.dna.evaluation import (
    bootstrap_matrices,
    jaccard,
    retrieval_metrics,
    temporal_views,
)
from football_intelligence.dna.registry import CORE, SPECS


def observations():
    rows = []
    for p in range(3):
        for i, date in enumerate(["2024-01-01", "2024-01-02", "2024-02-01", "2024-02-02"]):
            rows.append(
                dict(
                    player_id=str(p),
                    match_id=str(i),
                    observed_on=date,
                    minutes=90,
                    minutes_reliable=True,
                    team_id="a",
                    role_minutes_json=json.dumps({"CM": 90}),
                    bins_json="[]",
                    **{k: float(p + 1) for k, *_ in SPECS},
                    goals=0,
                    npxg=1,
                    xa=1,
                    completed_passes=1,
                    own_possessions=40,
                    opponent_possessions=50,
                    team_passes=500,
                )
            )
    return rows


def test_retrieval_metrics_and_jaccard_are_not_accuracy_claims():
    m = retrieval_metrics([1, 2, 6, 11])
    assert m["recall1"] == 0.25 and m["recall5"] == 0.5 and m["recall10"] == 0.75
    assert m["mrr"] == pytest.approx((1 + 0.5 + 1 / 6 + 1 / 11) / 4)
    assert jaccard([1, 2], [2, 3]) == pytest.approx(1 / 3)
    assert retrieval_metrics([])["mrr"] is None


def test_temporal_split_is_disjoint_and_window_minimum_applies():
    first, second, split = temporal_views(observations(), 300)
    assert len(first) == len(second) == 3
    assert not set(split["first_match_ids"]) & set(split["second_match_ids"])
    assert split["minimum_window_minutes"] == 150
    assert not temporal_views(observations(), 450)[0]


def test_bootstrap_seed_and_player_evidence():
    rows = observations()
    profiles = [{"player_id": str(i)} for i in range(3)]
    a = list(bootstrap_matrices(rows, profiles, 5, 42))
    b = list(bootstrap_matrices(rows, profiles, 5, 42))
    assert all(
        np.array_equal(x, y)
        for pair, other in zip(a, b, strict=True)
        for x, y in zip(pair, other, strict=True)
    )
    for x, _ in a:
        assert np.all(x[0] == 1) and np.all(x[2] == 3)
        assert x.shape == (3, len(CORE))
