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


def test_roster_context_isolates_club_stints_and_rejects_mixed_seasons():
    import json

    from football_intelligence.dna.features import aggregate
    from football_intelligence.dna.registry import SPECS
    from football_intelligence.recruitment.context import roster_context

    counts = dict.fromkeys(
        [k for k, *_ in SPECS]
        + [
            "goals",
            "npxg",
            "xa",
            "completed_passes",
            "own_possessions",
            "opponent_possessions",
            "team_passes",
        ],
        0,
    )
    rows = [
        dict(
            counts,
            player_id=str(i),
            team_id="A",
            match_id="match",
            competition_id="c",
            season_id="s",
            minutes=1000,
            minutes_reliable=True,
            role_minutes_json=json.dumps({"CB": 1000}),
            bins_json="[]",
            shots=i,
        )
        for i in range(12)
    ]
    # A 500-minute move cannot create a 1,500-minute eligible club-B stint.
    rows.append(
        {
            **rows[0],
            "team_id": "B",
            "match_id": "move",
            "minutes": 500,
            "role_minutes_json": '{"CB":500}',
        }
    )
    profiles = [aggregate([r for r in rows if r["player_id"] == str(i)]) for i in range(12)]
    names = {str(i): str(i) for i in range(12)}
    context = roster_context(rows, profiles, names)
    assert context == roster_context(list(reversed(rows)), profiles, names)
    role = context["A"][0]
    assert role["roster_depth"] == role["profile_depth"] == 12
    assert role["minutes_hhi"] == pytest.approx(1 / 12)
    assert role["median"]["shots_per90"] == pytest.approx(50)
    assert (
        role["minimum"]["shots_per90"]
        < role["median"]["shots_per90"]
        < role["maximum"]["shots_per90"]
    )
    assert context["B"][0]["profile_depth"] == 0
    assert context["B"][0]["median"] == {}
    assert "below_minutes" in context["B"][0]["players"][0]["exclusions"]
    with pytest.raises(ValueError, match="competition-season"):
        roster_context(rows + [{**rows[0], "season_id": "future"}], profiles, names)
    with pytest.raises(ValueError, match="Duplicate"):
        roster_context(rows + [rows[0]], profiles, names)


def test_missing_team_feature_is_unavailable_not_zero(fixtures):
    canonical = StatsBombAdapter().normalise(fixtures["statsbomb"], "fixture")
    from football_intelligence.data.schema import Lineup, frame_from_records
    from football_intelligence.dna.features import match_observations

    lineups = frame_from_records(Lineup, canonical["lineups"]).to_dicts()
    rows = match_observations(canonical["events"], lineups, canonical["matches"][0])
    row = {**rows[0], "minutes": 90, "minutes_reliable": True, "shots": None}
    context = aggregate_team_context([row])
    shot = next(f for f in context[0]["features"] if f["feature_id"] == "shots_per90")
    assert shot == dict(feature_id="shots_per90", value=None, percentile=None, available_matches=0)
