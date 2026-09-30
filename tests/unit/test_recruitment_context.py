from copy import deepcopy

import pytest
from pydantic import ValidationError

from football_intelligence.data.adapters.statsbomb import StatsBombAdapter
from football_intelligence.recruitment.context import aggregate_team_context, team_observations
from football_intelligence.recruitment.contracts import RecruitmentRequirement, RecruitmentScenario


def requirement(**changes):
    return RecruitmentRequirement.model_validate(
        dict(
            requirement_id="passing",
            feature_id="progressive_passes_per90",
            preference="minimum",
            value=75,
            **changes,
        )
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"feature_id": "price"},
        {"value": 101},
        {"value": float("nan")},
        {"weight": 0},
        {"preference": "exact", "hard_constraint": True},
    ],
)
def test_requirement_rejects_unsupported_values(changes):
    data = dict(
        requirement_id="passing",
        feature_id="progressive_passes_per90",
        preference="minimum",
        value=75,
    )
    with pytest.raises(ValidationError):
        RecruitmentRequirement.model_validate({**data, **changes})


def test_scenario_requires_coherent_versioned_assumptions():
    r = requirement()
    assert r.source == "user_defined" and r.weight == 1
    scenario = RecruitmentScenario(club_id="club", target_role="CB", requirements=[r])
    assert scenario.translation_mode == "observed_only"
    with pytest.raises(ValidationError):
        RecruitmentScenario(club_id="club", target_role="CB", requirements=[r, r])
    with pytest.raises(ValidationError):
        RecruitmentScenario(club_id="club", target_role="CB", mode="replace")


def test_team_counts_use_match_duration_and_isolate_seasons(fixtures):
    raw = deepcopy(fixtures["statsbomb"])
    canonical = StatsBombAdapter().normalise(raw, "fixture")
    events = [e for e in canonical["events"] if e["event_type"] != "Half End"]
    # Removing period endpoints must make duration unavailable.
    with pytest.raises(ValueError):
        team_observations(events, canonical["matches"][0])
    for period in (1, 2):
        events.append(
            {
                **events[0],
                "id": f"end{period}",
                "provider_id": f"end{period}",
                "event_type": "Half End",
                "period": period,
                "timestamp_seconds": 3000,
                "player_id": None,
            }
        )
    rows = team_observations(events, canonical["matches"][0])
    assert len(rows) == 2 and all(r["minutes"] == 100 for r in rows)
    assert sum(r["shots"] for r in rows) == 1  # shootout excluded
    first = aggregate_team_context(rows)
    more = [{**r, "season_id": "future", "shots": 1000} for r in rows]
    after = aggregate_team_context(rows + more)
    assert [c for c in after if c["season_id"] != "future"] == first
    for c in first:
        shot = next(f for f in c["features"] if f["feature_id"] == "shots_per90")
        assert shot["value"] in (0, 0.9)
        assert shot["percentile"] in (25, 75)
    with pytest.raises(ValueError):
        aggregate_team_context(rows + rows)
