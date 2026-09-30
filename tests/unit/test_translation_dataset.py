from copy import deepcopy

from football_intelligence.translation.dataset import historical_context, validation_player


def test_context_cannot_observe_destination_events():
    rows = [
        dict(
            team_id="a",
            observed_on=d,
            duration_minutes=90,
            passes=400,
            shots=10,
            possessions=50,
            opponent_possessions=50,
        )
        for d in ["2019-01-01", "2019-02-01", "2019-03-01"]
    ]
    expected = historical_context(rows, "a", "2019-03-01")
    future = {**rows[0], "observed_on": "2019-04-01", "passes": 100000}
    assert historical_context(rows + [future], "a", "2019-03-01") == expected
    assert expected["passes_per90"] == 400
    assert expected["last_date"] == "2019-03-01"
    assert historical_context(rows, "unknown", "2019-03-01") is None
    assert historical_context(rows, "a", "2021-03-01") is None


def test_validation_assignment_is_player_stable():
    assert validation_player("same-player") == validation_player(deepcopy("same-player"))
    assert {validation_player(str(i)) for i in range(100)} == {False, True}
