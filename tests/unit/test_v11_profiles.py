"""Aggregation, split, ranking and publication invariants on synthetic observations."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from football_intelligence.profiles.aggregate import aggregate_rows, split_profiles
from football_intelligence.profiles.contracts import CommonMetrics
from football_intelligence.profiles.evaluate import fit_scalers, neighbours, select_threshold
from football_intelligence.profiles.features import COMMON_IDS, COUNT_KEYS, NATIVE_COUNTS
from football_intelligence.profiles.ingest import valid_partition
from football_intelligence.profiles.publish import profile_path


def observation(mid=1, pid=10, team=1):
    return dict(
        provider="wyscout",
        scope="wyscout-1-2",
        player_id=pid,
        name="Same Name",
        match_id=mid,
        team_id=team,
        date=f"2017-08-{mid:02}",
        minutes=90.0,
        reliable=True,
        reasons=[],
        role_family="MID",
        source_files=["fixture.json"],
        minute_method="synthetic",
        **{"c_" + key: 0.0 for key in COUNT_KEYS},
        **{"n_" + key: 0.0 for key in NATIVE_COUNTS},
    )


def profile(pid, provider="wyscout", role="MID"):
    return dict(
        id=f"{provider}-1-2-{pid}",
        player_id=pid,
        provider=provider,
        scope=f"{provider}-1-2",
        role_family=role,
        common_ready=True,
        common=dict(zip(COMMON_IDS, [float(pid), float(pid * 20), float(pid * 3)], strict=True)),
    )


def test_multiteam_identity_and_unresolved_season_conflict():
    rows = [observation(1), observation(2, team=2)]
    result = aggregate_rows(rows)
    assert result["teams"] == [1, 2] and result["minutes"] == 180
    assert result["common_ready"]
    rows[1].update(minutes=None, reliable=False, reasons=["conflicting_substitution"])
    result = aggregate_rows(rows)
    assert not result["reliable"] and not result["common_ready"]
    assert "unresolved_participation_conflict" in result["exclusion_reasons"]
    with pytest.raises(ValueError):
        aggregate_rows([observation(), observation()])
    with pytest.raises(ValueError):
        aggregate_rows([observation(), observation(2, pid=11)])


def test_unknown_outcomes_do_not_become_zero_but_attempt_metrics_remain_observed():
    row = observation()
    row.update(c_passes=10.0, c_completed=8.0, c_outcome_missing=1.0)
    result = aggregate_rows([row])
    assert result["common_ready"] and set(result["common"]) == set(COMMON_IDS)
    assert "pass_completion_all" not in result["common"]
    row["c_geometry_missing"] = 1.0
    result = aggregate_rows([row])
    assert not result["common_ready"] and result["common"]["long_passes_all_per90"] is None


def test_temporal_split_is_by_match_not_player_appearances():
    rows = [observation(i) for i in range(1, 7)] + [observation(1, 11), observation(6, 11)]
    split, cutoff = split_profiles(Path("unused"), rows)
    assert cutoff["wyscout-1-2"]["last_first_match"] == ("2017-08-03", 3)
    assert [r["minutes"] for r in split if r["player_id"] == 11] == [90, 90]


def test_shared_scaling_determinism_and_hard_provider_role_boundaries():
    query = profile(1)
    candidates = [profile(2), profile(3), profile(1, "statsbomb"), profile(4, role="DEF")]
    scale = fit_scalers([query, *candidates])
    before = neighbours(query, candidates, scale)
    assert [p["id"] for p in before] == ["wyscout-1-2-2", "wyscout-1-2-3"]
    altered = copy.deepcopy(candidates)
    for p in altered:
        p["native"] = {"pressures_per90": 1e10}
    assert neighbours(query, list(reversed(altered)), scale) == before
    assert np.allclose(
        scale["shared"]["shared"]["mean"],
        np.array([list(p["common"].values()) for p in [query, *candidates]]).mean(axis=0),
    )


def test_development_only_threshold_selection():
    results = []
    for threshold, mrr in [(450, 0.18), (600, 0.19), (900, 0.20)]:
        results.append(
            dict(
                threshold=threshold,
                cohorts=[
                    dict(scope=f"{p}-1-2", n=30, metrics={"mrr": mrr})
                    for p in ("statsbomb", "wyscout")
                ]
                + [
                    dict(
                        scope="statsbomb-9-9", n=2000, metrics={"mrr": 1 if threshold == 900 else 0}
                    )
                ],
            )
        )
    threshold, scores = select_threshold(results, {"statsbomb-1-2", "wyscout-1-2"})
    assert threshold == 450
    assert scores[900] == 0.20
    with pytest.raises(ValueError):
        select_threshold(results, {"statsbomb-9-9"})


def test_common_contract_rejects_native_and_nonfinite_fields():
    good = dict(zip(COMMON_IDS, [0.0, 10.0, 1.0], strict=True))
    assert CommonMetrics.model_validate(good).non_penalty_shots_per90 == 0
    for wrong in [
        good | {"pressures_per90": 2},
        good | {COMMON_IDS[0]: float("nan")},
        good | {COMMON_IDS[1]: -1},
    ]:
        with pytest.raises(ValidationError):
            CommonMetrics.model_validate(wrong)


def test_partition_tampering_and_shard_path(tmp_path):
    (tmp_path / "manifest.json").write_text(
        json.dumps(dict(processing_key="a", files={"rows.parquet": "wrong"}))
    )
    assert not valid_partition(tmp_path, "a")
    assert not valid_partition(tmp_path, "b")
    assert profile_path("statsbomb-37-281-7") == "profiles/07/statsbomb-37-281-7.json"
