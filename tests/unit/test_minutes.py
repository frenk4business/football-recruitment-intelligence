"""Synthetic participation timelines, including stoppage time and temporary exits."""

from copy import deepcopy

import pytest

from football_intelligence.data.minutes import reconcile


def timeline():
    roster = [{"player_id": p, "positions": []} for p in range(1, 13)]

    def event(i, kind, period=1, timestamp="00:00:00.000", **fields):
        return dict(
            id=str(i),
            index=i,
            type={"name": kind},
            period=period,
            timestamp=timestamp,
            team={"id": 1},
            **fields,
        )

    xi = [{"player": {"id": p}, "position": {"name": "Center Midfield"}} for p in range(1, 12)]
    events = [
        event(1, "Starting XI", tactics={"lineup": xi}),
        event(2, "Half End", timestamp="00:47:00.000"),
        event(
            3,
            "Substitution",
            2,
            "00:15:00.000",
            player={"id": 1},
            substitution={"replacement": {"id": 12}},
        ),
        event(4, "Half End", 2, "00:49:00.000"),
    ]
    return dict(lineups=[dict(team_id=1, lineup=roster)], events=events)


def test_substitution_uses_actual_period_lengths():
    r = reconcile(timeline())
    assert r[1]["minutes"] == 62
    assert r[12]["minutes"] == 34
    assert r[2]["minutes"] == 96
    assert r[1]["minutes_reliable"]


def test_temporary_exit_and_card():
    raw = timeline()
    base = raw["events"][0]
    for i, kind, t in [(5, "Player Off", "00:05:00.000"), (6, "Player On", "00:07:00.000")]:
        raw["events"].append(
            {**base, "index": i, "type": {"name": kind}, "timestamp": t, "player": {"id": 2}}
        )
    r = reconcile(raw)
    assert r[2]["minutes"] == 94
    raw["events"].append(
        {
            **base,
            "index": 7,
            "type": {"name": "Bad Behaviour"},
            "timestamp": "00:30:00.000",
            "player": {"id": 3},
            "bad_behaviour": {"card": {"name": "Red Card"}},
        }
    )
    assert reconcile(raw)[3]["minutes"] == 30


def test_conflicting_substitution_not_silently_repaired():
    raw = timeline()
    raw["events"][2]["substitution"]["replacement"]["id"] = 2
    assert not reconcile(raw)[2]["minutes_reliable"]
    assert reconcile(raw)[2]["minutes"] is None


def test_no_complete_periods_no_reliable_reconstruction():
    raw = timeline()
    raw["events"] = raw["events"][:-1]
    assert reconcile(raw) == {}


def test_extra_time_and_tactical_role_minutes():
    raw = timeline()
    e = deepcopy(raw["events"][-1])
    e.update(period=3, timestamp="00:16:00.000", index=5)
    raw["events"].append(e)
    e = deepcopy(e)
    e.update(period=4, timestamp="00:17:00.000", index=6)
    raw["events"].append(e)
    assert reconcile(raw)[2]["minutes"] == 129
    assert reconcile(raw)[12]["minutes"] == pytest.approx(67)
