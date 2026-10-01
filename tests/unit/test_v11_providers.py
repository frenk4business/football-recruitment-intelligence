"""Synthetic provider fixtures; no licensed raw observations or network in CI."""

import copy
import io

import pytest

from football_intelligence.data.adapters import wyscout as ws
from football_intelligence.profiles import statsbomb as sb
from football_intelligence.profiles.features import counts, native_values, values
from football_intelligence.profiles.ingest import decode_name, iter_json_array


def match():
    return {
        "wyId": 99,
        "status": "Played",
        "duration": "Regular",
        "dateutc": "2017-08-12 15:00:00",
        "teamsData": {
            str(t): {
                "hasFormation": 1,
                "formation": {
                    "lineup": [
                        {"playerId": p, "redCards": "0"} for p in range(t * 100, t * 100 + 11)
                    ],
                    "bench": [{"playerId": t * 100 + 11}],
                    "substitutions": [],
                },
            }
            for t in (1, 2)
        },
    }


def event(**changes):
    raw = {
        "id": 123,
        "matchId": 99,
        "teamId": 1,
        "playerId": 100,
        "matchPeriod": "1H",
        "eventSec": 60,
        "eventId": 8,
        "eventName": "Pass",
        "subEventId": 85,
        "subEventName": "Simple pass",
        "tags": [{"id": 1801}],
        "positions": [{"x": 40, "y": 50}, {"x": 90, "y": 50}],
    }
    return raw | changes


def parse(raw):
    return ws.parse_event(raw, match(), set(range(100, 112)) | set(range(200, 212)), {1, 2})


def clocks():
    return [parse(event(eventSec=2700, matchPeriod=p)) for p in ("1H", "2H")]


@pytest.mark.parametrize(
    "percent,expected",
    [
        ((0, 0), (0, 0)),
        ((100, 100), (105, 68)),
        ((50, 50), (52.5, 34)),
        ((100, 50), (105, 34)),
        ((0, 100), (0, 68)),
        ((88.5 / 1.05, 13.84 / 0.68), (88.5, 13.84)),
    ],
)
def test_geometry_same_origin_direction_and_box(percent, expected):
    x, y = percent
    assert ws.coordinates({"x": x, "y": y}) == pytest.approx(expected)
    assert sb.coordinates([x * 1.2, y * 0.8]) == pytest.approx(expected)
    for period in ("1H", "2H"):
        parsed = parse(event(matchPeriod=period, positions=[{"x": x, "y": y}]))
        assert (parsed["x"], parsed["y"]) == pytest.approx(expected)


@pytest.mark.parametrize(
    "point", [{"x": -1, "y": 0}, {"x": 101, "y": 0}, {"x": float("nan"), "y": 50}, {}]
)
def test_invalid_geometry_unavailable(point):
    assert ws.coordinates(point) == (None, None)


def test_native_fields_identity_tags_and_references():
    parsed = parse(event(tags=[{"id": 1801}, {"id": 302}]))
    assert parsed["event_id"] == "123" and parsed["provider_event_id"] == 8
    assert parsed["provider_subtype_id"] == "85" and parsed["tags"] == [302, 1801]
    assert parsed["provider"] == "wyscout" and parsed["player_known"]
    assert not parse(event(playerId=999))["player_known"]
    for field, value in [
        ("teamId", 5),
        ("matchId", 88),
        ("matchPeriod", "invalid"),
        ("eventSec", -1),
    ]:
        with pytest.raises(ValueError):
            parse(event(**{field: value}))
    assert ws.match_date(match()) == "2017-08-12"
    assert decode_name(r"N\u00e9stor") == "Néstor"


def test_equivalent_actions_all_seven_features_and_restarts():
    sb_events, ws_events = [], []
    for a, b, complete in [
        ((40, 50), (90, 50), True),
        ((80, 80), (95, 60), True),
        ((20, 5), (70, 5), False),
        ((0, 0), (15, 10), True),
    ]:
        sb_events.append(
            {
                "type": {"name": "Pass"},
                "location": [a[0] * 1.2, a[1] * 0.8],
                "pass": {
                    "end_location": [b[0] * 1.2, b[1] * 0.8],
                    "type": {"name": "Free Kick"},
                    **({} if complete else {"outcome": {"name": "Incomplete"}}),
                },
            }
        )
        ws_events.append(
            parse(
                event(
                    eventId=3,
                    subEventId=31,
                    positions=[
                        dict(zip(("x", "y"), a, strict=True)),
                        dict(zip(("x", "y"), b, strict=True)),
                    ],
                    tags=[{"id": 1801 if complete else 1802}],
                )
            )
        )
    for sb_type, subtype in [("Open Play", 100), ("Free Kick", 33), ("Penalty", 35)]:
        sb_events.append({"type": {"name": "Shot"}, "shot": {"type": {"name": sb_type}}})
        ws_events.append(parse(event(eventId=10 if subtype == 100 else 3, subEventId=subtype)))
    sb_counts = counts([a for e in sb_events if (a := sb.common_action(e))])
    ws_counts = counts([a for e in ws_events if (a := ws.common_action(e))])
    assert sb_counts == ws_counts
    result = values(sb_counts, 90)
    assert list(result.values()) == [2, 4, 0.75, 2, 2, 1, 2]


def test_zero_and_unavailable_are_different():
    empty = values(counts([]), 90)
    assert empty["non_penalty_shots_per90"] == 0
    assert empty["pass_completion_all"] is None
    for action in [
        sb.common_action({"type": {"name": "Pass"}}),
        ws.common_action(parse(event(tags=[]))),
    ]:
        incomplete = values(counts([action]), 90)
        assert incomplete["passes_all_per90"] == 1
        assert incomplete["pass_completion_all"] is None
        assert incomplete["progressive_passes_all_per90"] is None
    assert sb.native_counts([], set())["pressures"] is None
    assert "pressures_per90" not in native_values("wyscout", ws.native_counts([]), 90)
    assert values(counts([]), 0)["non_penalty_shots_per90"] is None


def test_minutes_starters_substitutes_and_unused_bench():
    m = match()
    m["teamsData"]["1"]["formation"]["substitutions"] = [
        {"playerIn": 111, "playerOut": 101, "minute": 60}
    ]
    rows = ws.minutes(m, clocks(), set(range(100, 112)) | set(range(200, 212)))
    assert rows[100]["minutes"] == 90
    assert rows[101]["minutes"] == 60 and rows[111]["minutes"] == 30
    assert rows[211]["minutes"] == 0 and not rows[211]["participated"]


def test_minutes_conflicts_red_cards_and_missing_half():
    m = match()
    events = clocks() + [
        parse(event(playerId=101, matchPeriod="2H", eventSec=900, tags=[{"id": 1701}]))
    ]
    rows = ws.minutes(m, events, set(range(100, 112)) | set(range(200, 212)))
    assert rows[101]["minutes"] == 60
    m["teamsData"]["1"]["formation"]["lineup"][1]["redCards"] = "1"
    assert ws.minutes(m, clocks(), set(range(100, 112)))[101]["minutes"] is None
    conflict = ws.minutes(match(), clocks() + [parse(event(playerId=111))], set(range(100, 112)))
    assert (
        conflict[111]["minutes"] is None
        and "action_outside_participation" in conflict[111]["reasons"]
    )
    assert ws.minutes(match(), clocks()[:1], set()) == {}
    extra = copy.deepcopy(match())
    extra["duration"] = "ExtraTime"
    assert ws.minutes(extra, clocks(), set()) == {}


@pytest.mark.parametrize(
    "code,expected",
    [
        ("GKP", ("GK", "GK")),
        ("DEF", (None, "DEF")),
        ("MID", (None, "MID")),
        ("FWD", (None, "FWD")),
        ("unknown", (None, None)),
    ],
)
def test_roles_keep_provider_ambiguity(code, expected):
    assert ws.role({"role": {"code3": code}}) == expected


def test_streaming_source_validation():
    assert list(iter_json_array(io.BytesIO(b'[{"id":1},{"id":2}]'))) == [{"id": 1}, {"id": 2}]
    for broken in [b"{}", b'[{"id":1}', b"[] {}", b"[1]"]:
        with pytest.raises(ValueError):
            list(iter_json_array(io.BytesIO(broken)))
