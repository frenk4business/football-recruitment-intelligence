"""Semantic and isolation regressions for additive native recruitment and metadata."""

import numpy as np
import pytest

from football_intelligence.expansion.evaluate import eligible, scales, tie_metrics
from football_intelligence.expansion.features import KEYS, count_events, progressive, values
from football_intelligence.expansion.metadata import (
    normalize,
    parse_clubs,
    parse_fixtures,
    parse_players,
    score_value,
)
from football_intelligence.expansion.publish import percentiles
from football_intelligence.expansion.wyscout import aggregate


def event(kind=8, sub=85, tags=(1801,), x=40.0, y=34.0, end_x=80.0, end_y=34.0):
    return dict(
        provider_event_id=kind,
        provider_subtype_id=sub,
        tags=list(tags),
        x=x,
        y=y,
        end_x=end_x,
        end_y=end_y,
    )


def test_native_pass_geometry_and_completion():
    counts, missing = count_events(
        [event(), event(tags=(1802,), end_x=90.0), event(x=80.0, end_x=90.0)]
    )
    assert not missing
    assert {
        k: counts[k]
        for k in [
            "passes",
            "completed_passes",
            "forward_passes",
            "long_passes",
            "progressive_passes",
            "final_third_entries",
            "box_entries",
        ]
    } == dict(
        passes=3,
        completed_passes=2,
        forward_passes=3,
        long_passes=2,
        progressive_passes=2,
        final_third_entries=1,
        box_entries=1,
    )
    rates = values(counts, set(missing), 180)
    assert rates["passes"] == 1.5
    assert rates["pass_completion"] == pytest.approx(66.666667)
    assert (
        progressive(5, 34, 40, 34) and progressive(40, 34, 60, 34) and progressive(75, 34, 90, 34)
    )
    assert not progressive(65, 34, 30, 34)


def test_shots_exclude_penalties_blocked_and_off_target():
    counts, missing = count_events(
        [
            event(10, 100, (1201,), 90),
            event(3, 33, (101,), 20),
            event(3, 35, (101,), 94),
            event(10, 100, (1201, 2101), 90),
            event(10, 100, (1210,), 90),
        ]
    )
    assert not missing
    assert (
        counts["non_penalty_shots"] == 4
        and counts["on_target_shots"] == 2
        and counts["box_shots"] == 3
    )


@pytest.mark.parametrize(
    ("sub", "key"), [(10, "aerial_duels"), (11, "attacking_duels"), (12, "defensive_duels")]
)
def test_duels_have_explicit_winning_tags(sub, key):
    counts, missing = count_events(
        [event(1, sub, (703,)), event(1, sub, (701,)), event(1, sub, (702,))]
    )
    assert counts[key] == 3 and counts["won_" + key] == 1 and not missing
    counts, missing = count_events([event(1, sub, ()), event(1, sub, (701, 703))])
    assert counts["won_" + key] == 0 and "won_" + key in missing


def test_native_tags_crosses_interventions_and_no_invented_concepts():
    counts, missing = count_events(
        [
            event(8, 80, (1801, 302)),
            event(8, 80, (1802,)),
            event(7, 71, (1401, 1601)),
            event(7, 70, ()),
        ]
    )
    assert not missing
    for key, n in dict(
        crosses=2,
        completed_crosses=1,
        key_passes=1,
        interceptions=1,
        sliding_tackles=1,
        clearances=1,
        accelerations=1,
    ).items():
        assert counts[key] == n
    assert len(KEYS) == 24 and not {"pressures", "dribbles", "recoveries", "headers"} & set(KEYS)


def test_missing_semantics_are_not_zero_and_unreliable_appearance_withholds_season():
    counts, missing = count_events([event(tags=(), end_x=None)])
    rate = values(counts, set(missing), 90)
    assert (
        rate["passes"] == 1 and rate["completed_passes"] is None and rate["forward_passes"] is None
    )
    assert values(dict.fromkeys(KEYS, 0), set(), 90)["pass_completion"] is None
    rows = [
        dict(
            counts=counts,
            missing=missing,
            reasons=["unresolved_substitution"],
            reliable=False,
            minutes=None,
            team_id=1,
            date="2017-01-01",
        )
    ]
    profile = aggregate(rows)
    assert not profile["minutes_reliable"] and all(v is None for v in profile["features"].values())
    assert not eligible(profile, 450)


def test_league_reference_is_local_and_ties_match_random_expectation():
    local = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
    # Another league cannot enter unless deliberately passed as the reference.
    np.testing.assert_allclose(percentiles(np.array([[2.0, 4.0]]), local), [[50, 50]])
    assert percentiles(np.array([[2.0, 4.0]]), np.array([[10.0, 20.0], [20.0, 40.0]]))[0, 0] == 0
    tied = tie_metrics(np.zeros((20, 20)))
    assert np.mean(tied["recall5"]) == 0.25
    assert np.mean(tied["rr"]) == pytest.approx(np.mean(1 / np.arange(1, 21)))
    sd, weights = scales(np.ones((20, 24)))
    assert np.all(sd == 1) and np.all(weights == 0)


def test_openfootball_aliases_positions_dates_and_results():
    clubs, errors = parse_clubs(
        "Arsenal FC, 1886, @ Emirates Stadium, London\n | Arsenal | FC Arsenal\n# ignored",
        "England",
        "https://example.org",
    )
    assert (
        not errors
        and clubs[0]["aliases"] == ["Arsenal", "FC Arsenal"]
        and clubs[0]["stadium"] == "Emirates Stadium"
    )
    assert normalize("Atlético Madrid") == normalize("Atletico Madrid")
    players, errors = parse_players(
        "A Person, D|M,1.82 m, b. 10 Nov 2002 @ City\nB Person, F,-, b. ??",
        "England",
        "https://example.org",
    )
    assert not errors and players[0]["dob"] == "2002-11-10" and players[1]["dob"] is None
    assert (
        players[0]["capabilities"]["metadata_only"]
        and not players[0]["capabilities"]["recruitment"]
    )
    rows, errors = parse_fixtures(
        "Fri Aug 7 2026\n17:00  Club A v Club B  2-1 (1-0)\n  19:00   Club C  3-1 (1-0)  Club D\nClub E v Club F [cancelled]\nClub G v Club H  3-0 [awarded]"
    )
    assert not errors and len(rows) == 4
    assert rows[0]["score"] == [2, 1] and rows[1]["away"] == "Club D" and rows[2]["score"] is None
    assert all(r["date_text"] == "Fri Aug 7 2026" for r in rows)
    assert score_value({"ft": [1, 0]}) == score_value([1, 0]) and score_value({}) is None
    with pytest.raises(ValueError):
        score_value([True, 0])
