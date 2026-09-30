from copy import deepcopy

import pytest

from football_intelligence.recruitment.contracts import RecruitmentScenario
from football_intelligence.recruitment.scoring import (
    pareto_frontier,
    rank_candidates,
    specification,
)
from football_intelligence.recruitment.stability import (
    rank_summary,
    scenario_stability,
    weight_draws,
)

F = "progressive_passes_per90"
G = "pressures_per90"


def candidate(pid, passing, pressing=50, **changes):
    return dict(
        player_id=pid,
        role="CB",
        minutes=1000,
        team_ids=["away"],
        eligible=True,
        exclusions=[],
        neighbor_stability=0.6,
        percentiles={F: passing, G: pressing},
        **changes,
    )


def scenario(preference="exact", target=75, **changes):
    data = dict(
        club_id="home",
        target_role="CB",
        requirements=[dict(requirement_id=F, feature_id=F, preference=preference, value=target)],
    )
    return RecruitmentScenario.model_validate({**data, **changes})


@pytest.mark.parametrize(
    "preference,values,expected",
    [
        ("exact", [75, 65, 40], [0, 10, 35]),
        ("minimum", [90, 75, 60], [0, 0, 15]),
        ("maximum", [60, 75, 90], [0, 0, 15]),
    ],
)
def test_directional_preferences_preserve_distance_semantics(preference, values, expected):
    result = rank_candidates(
        [candidate(str(i), v) for i, v in enumerate(values)], scenario(preference)
    )
    by_id = {r["player_id"]: r for r in result["rankings"]}
    assert [by_id[str(i)]["distance"] for i in range(3)] == expected
    assert [r["player_id"] for r in result["rankings"]] == ["0", "1", "2"]


def test_neutral_and_evidence_do_not_change_fit():
    players = [candidate("a", 75, 0), candidate("b", 60, 100)]
    base = scenario()
    neutral = base.model_dump()
    neutral["requirements"].append(
        dict(requirement_id=G, feature_id=G, preference="neutral", value=99, weight=3)
    )
    assert rank_candidates(players, base) == rank_candidates(
        players, RecruitmentScenario.model_validate(neutral)
    )
    changed = deepcopy(players)
    changed[0]["minutes"] = 4000
    changed[0]["neighbor_stability"] = 0.99
    changed[1]["neighbor_stability"] = 0.01
    assert rank_candidates(players, base) == rank_candidates(changed, base)


def test_hard_constraints_precede_ranking_and_remain_traceable():
    players = [candidate("a", 75), candidate("b", 60), candidate("c", 90)]
    players[0]["team_ids"] = ["home"]
    players[2]["role"] = "ST"
    sc = scenario("minimum", 70)
    sc.requirements[0].hard_constraint = True
    result = rank_candidates(players, sc)
    assert result["status"] == "no_candidates" and not result["rankings"]
    assert {p["player_id"]: p["reasons"] for p in result["exclusions"]} == {
        "a": ["same_club_excluded"],
        "b": ["hard_feature_constraint:" + F],
        "c": ["wrong_role"],
    }


def test_explanations_and_explicit_weights():
    sc = scenario()
    sc.requirements.append(
        sc.requirements[0].model_copy(
            update=dict(requirement_id=G, feature_id=G, value=50, weight=3)
        )
    )
    result = rank_candidates([candidate("a", 65, 30)], sc)["rankings"][0]
    assert result["distance"] == pytest.approx((100 * 0.25 + 400 * 0.75) ** 0.5)
    assert sum(c["share"] for c in result["contributions"]) == pytest.approx(1)
    assert result["main_mismatches"][0] == G
    assert result["family_contributions"]["defending"] == pytest.approx(1200 / 1300)


def test_pareto_dominance_ties_and_exclusions():
    assert pareto_frontier({"a": [0, 2], "b": [2, 0], "c": [3, 3], "d": [0, 2]}) == {"a", "b", "d"}
    sc = scenario()
    assert rank_candidates([candidate("a", 75), candidate("b", 74)], sc)["frontier_count"] == 1
    assert rank_candidates([candidate("b", 75), candidate("a", 75)], sc)["frontier_count"] == 2
    assert [
        r["player_id"]
        for r in rank_candidates([candidate("b", 75), candidate("a", 75)], sc)["rankings"]
    ] == ["a", "b"]


def test_no_active_requirements_withholds_ordering():
    result = rank_candidates([candidate("a", 75)], scenario("neutral"))
    assert result["status"] == "no_requirements" and result["rankings"] == []


def test_weight_and_profile_sensitivity_are_deterministic_and_separate():
    players = [candidate("a", 75), candidate("b", 74)]
    sc = scenario()
    spec = specification()
    draws = list(weight_draws([F, G], spec))
    assert draws == list(weight_draws([G, F], spec))
    assert len(draws) == 100 and all(0.8 <= v <= 1.2 for d in draws for v in d.values())
    boot = dict(
        role="CB",
        player_ids=["a", "b"],
        feature_ids=[F, G],
        scale=10,
        values=[[[0, 500], [750, 500]], [[750, 500], [0, 500]]],
    )
    result = scenario_stability(players, sc, bootstrap=boot)
    assert result == scenario_stability(players, sc, bootstrap=boot)
    assert result["weight"]["players"]["a"]["rank_p90"] == 1
    assert result["profile"]["players"]["a"]["rank_p90"] == pytest.approx(1.9)
    assert (
        result["profile"]["players"]["a"]["top_k_inclusion"] == 1
    )  # N < k; never pretend this proves robustness.
    summary = rank_summary(["a", "b", "c"], [["c", "a", "b"], ["a", "b", "c"]], 1)
    assert summary["players"]["a"]["top_k_inclusion"] == 0.5
    assert summary["mean_jaccard"] == 0.5
