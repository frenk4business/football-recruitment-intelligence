from copy import deepcopy

import pytest

from football_intelligence.translation.evidence import (
    adjacent_transitions,
    identity_status,
    role_change,
)


def env(label, start, end, team="a", season="2019", player="p", provider="statsbomb"):
    return dict(
        environment_id=label,
        provider=provider,
        player_id=player,
        team_id=team,
        competition_id="c",
        competition="WSL",
        season_id=season,
        season=season,
        season_start_year=int(season),
        start_date=start,
        end_date=end,
        country="England",
        gender="female",
        identity_confidence="provider_id_consistent_metadata",
        role="CM",
    )


def test_identity_compares_metadata_inside_provider_namespace():
    a = dict(provider="statsbomb", provider_player_id=7, name="José  Smith", nationality="England")
    assert identity_status([a, {**a, "name": "Jose Smith"}]) == (
        "provider_id_consistent_metadata",
        [],
    )
    assert identity_status([a, {**a, "name": "Another Player"}])[1] == ["conflicting_names"]
    assert identity_status([a, {**a, "provider": "wyscout"}])[1] == ["provider_identity_mismatch"]
    assert identity_status([a, {**a, "nationality": "Spain"}])[1] == ["conflicting_nationality"]


def test_only_adjacent_observed_environments_are_paired():
    a = env("a", "2019-01-01", "2019-04-01")
    b = env("b", "2019-08-01", "2019-12-01", team="b")
    c = env("c", "2020-08-01", "2020-12-01", team="c", season="2020")
    rows = adjacent_transitions([c, a, b])
    assert [(r["source_environment_id"], r["destination_environment_id"]) for r in rows] == [
        ("a", "b"),
        ("b", "c"),
    ]
    assert rows[0]["transition_type"] == "same_league_team_change"
    assert rows[1]["transition_type"] == "team_and_season_change"


def test_season_change_is_not_a_team_transfer():
    rows = adjacent_transitions(
        [env("a", "2019-01-01", "2019-04-01"), env("b", "2020-01-01", "2020-04-01", season="2020")]
    )
    assert rows[0]["transition_type"] == "season_change_same_team"
    assert not rows[0]["actual_team_change"]


def test_overlap_gap_and_identity_rejections_are_explicit():
    a = env("a", "2019-01-01", "2019-08-01")
    b = env("b", "2019-07-01", "2019-12-01", team="b")
    assert "overlapping_observations" in adjacent_transitions([a, b])[0]["exclusion_reasons"]
    c = env("c", "2023-01-01", "2023-05-01", season="2023")
    c["identity_confidence"] = "quarantined"
    assert set(adjacent_transitions([a, c])[0]["exclusion_reasons"]) == {
        "observation_gap_over_450_days",
        "unobserved_intervening_season",
        "rejected_identity",
    }


def test_provider_isolation_and_duplicate_environment_rejection():
    a = env("a", "2019-01-01", "2019-04-01")
    b = env("b", "2020-01-01", "2020-04-01", season="2020", provider="wyscout")
    assert adjacent_transitions([a, b]) == []
    with pytest.raises(ValueError, match="Duplicate environment"):
        adjacent_transitions([a, deepcopy(a)])


def test_cross_league_and_role_change_labels():
    a = env("a", "2019-01-01", "2019-04-01")
    b = env("b", "2020-01-01", "2020-04-01", season="2020", team="b")
    b.update(competition_id="d", competition="Frauen Bundesliga", country="Germany", role="DM")
    t = adjacent_transitions([a, b])[0]
    assert t["transition_type"] == "cross_league_change" and t["cross_country_change"]
    assert t["role_change"] == "adjacent"
    assert role_change("CB", "ST") == "major"
    assert role_change(None, "ST") == "unknown"
