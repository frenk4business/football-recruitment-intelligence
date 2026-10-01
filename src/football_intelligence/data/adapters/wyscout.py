"""Pappalardo/Wyscout adapter. Native event types/tags never become StatsBomb labels."""

import json
import math
from collections import defaultdict
from datetime import datetime

from football_intelligence.profiles.features import NATIVE_COUNTS, Action

PERIODS = {"1H": 1, "2H": 2, "E1": 3, "E2": 4, "P": 5}
PASS_RESTARTS = {30, 31, 32, 34, 36}


def coordinates(position: dict | None) -> tuple[float | None, float | None]:
    if not position:
        return None, None
    x, y = position.get("x"), position.get("y")
    if not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 100 for v in (x, y)):
        return None, None
    # Provider uses attacking-team coordinates every period; no home/away/period flip.
    assert x is not None and y is not None
    return round(x * 1.05, 6), round(y * 0.68, 6)


def parse_event(raw: dict, match: dict, people: set[int], teams: set[int]) -> dict:
    if int(raw["matchId"]) != int(match["wyId"]):
        raise ValueError("Wrong Wyscout match reference")
    team = int(raw["teamId"])
    if team not in teams or str(team) not in match["teamsData"]:
        raise ValueError("Unknown Wyscout team reference")
    pid = int(raw["playerId"])
    period = PERIODS.get(raw["matchPeriod"])
    sec = float(raw["eventSec"])
    if period is None or not math.isfinite(sec) or sec < 0 or sec > 4500:
        raise ValueError("Invalid Wyscout period/clock")
    positions = raw.get("positions", [])
    x, y = coordinates(positions[0] if positions else None)
    ex, ey = coordinates(positions[1] if len(positions) > 1 else None)
    tags = sorted({int(t["id"]) for t in raw.get("tags", [])})
    return dict(
        provider="wyscout",
        event_id=str(raw["id"]),
        match_id=int(raw["matchId"]),
        player_id=pid,
        player_known=pid in people,
        team_id=team,
        period=period,
        clock_seconds=sec,
        provider_event_id=int(raw["eventId"]),
        provider_event_type=str(raw["eventName"]),
        provider_subtype_id=str(raw.get("subEventId", "")),
        provider_subtype=str(raw.get("subEventName", "")),
        tags=tags,
        original_positions=json.dumps(positions, separators=(",", ":")),
        x=x,
        y=y,
        end_x=ex,
        end_y=ey,
    )


def common_action(event: dict) -> Action | None:
    kind = event["provider_event_id"]
    subtype = int(event["provider_subtype_id"] or -1)
    if kind == 10 or (kind == 3 and subtype == 33):
        return Action("shot")
    if kind == 8 or (kind == 3 and subtype in PASS_RESTARTS):
        tags = set(event["tags"])
        outcome = (
            True
            if 1801 in tags and 1802 not in tags
            else False
            if 1802 in tags and 1801 not in tags
            else None
        )
        return Action("pass", outcome, event["x"], event["y"], event["end_x"], event["end_y"])
    return None


def native_counts(events: list[dict]) -> dict:
    result = dict.fromkeys(NATIVE_COUNTS, 0.0)
    for event in events:
        kind = event["provider_event_id"]
        sub = int(event["provider_subtype_id"] or -1)
        tags = set(event["tags"])
        if kind == 8:
            result["open_passes"] += 1
            result["open_completed"] += float(1801 in tags and 1802 not in tags)
            result["open_outcome_missing"] += float((1801 in tags) == (1802 in tags))
        result["crosses"] += float(kind == 8 and sub == 80)
        result["key_passes"] += float(302 in tags)
        result["duels"] += float(kind == 1)
        result["attacking_duels"] += float(kind == 1 and sub == 11)
        result["sliding_tackles"] += float(1601 in tags)
        result["interceptions"] += float(1401 in tags)
        result["accelerations"] += float(kind == 7 and sub == 70)
        result["clearances"] += float(kind == 7 and sub == 71)
    return result


def role(player: dict) -> tuple[str | None, str | None]:
    code = player.get("role", {}).get("code3")
    return (
        ("GK", "GK") if code == "GKP" else (None, code if code in {"DEF", "MID", "FWD"} else None)
    )


def match_date(match: dict) -> str:
    return datetime.strptime(match["dateutc"], "%Y-%m-%d %H:%M:%S").date().isoformat()


def minutes(match: dict, events: list[dict], people: set[int]) -> dict[int, dict]:
    """Nominal regulation minutes from explicit rosters/substitutions; no event-count proxy."""
    if match["status"] != "Played" or match["duration"] != "Regular":
        return {}
    if {e["period"] for e in events} != {1, 2}:
        return {}
    if any(max(e["clock_seconds"] for e in events if e["period"] == p) < 2400 for p in (1, 2)):
        return {}
    actors: dict[int, list] = defaultdict(list)
    for event in events:
        actors[event["player_id"]].append(event)
    result = {}
    for key, team in match["teamsData"].items():
        tid = int(key)
        formation = team.get("formation", {})
        lineup, bench = formation.get("lineup", []), formation.get("bench", [])
        roster = {int(p["playerId"]): p for p in lineup + bench}
        starters = {int(p["playerId"]) for p in lineup}
        bad_team = (
            team.get("hasFormation") != 1
            or len(starters) != 11
            or len(roster) != len(lineup) + len(bench)
        )
        problems: dict[int, set[str]] = defaultdict(set)
        intervals = {pid: [0.0, 90.0] for pid in starters}
        active = set(starters)
        substitutions = formation.get("substitutions")
        if substitutions in (None, "null"):
            substitutions = []
        if not isinstance(substitutions, list):
            bad_team = True
            substitutions = []
        for sub in sorted(substitutions, key=lambda s: (float(s["minute"]), int(s["playerOut"]))):
            incoming, outgoing = int(sub["playerIn"]), int(sub["playerOut"])
            raw_minute = float(sub["minute"])
            at = min(90.0, max(0.0, raw_minute))
            if (
                raw_minute < 0
                or raw_minute > 110
                or outgoing not in active
                or incoming in intervals
                or incoming not in roster
            ):
                problems[incoming].add("conflicting_substitution")
                problems[outgoing].add("conflicting_substitution")
                continue
            intervals[outgoing][1] = at
            active.remove(outgoing)
            active.add(incoming)
            intervals[incoming] = [at, 90.0]
        for pid, player in roster.items():
            if pid not in people:
                problems[pid].add("unknown_player_reference")
            if bad_team:
                problems[pid].add("invalid_roster")
            actor = actors.get(pid, [])
            cards = [e for e in actor if set(e["tags"]) & {1701, 1703}]
            stated_red = str(player.get("redCards", "0")) not in {"0", "null", "None", ""}
            if stated_red and not cards and pid in intervals:
                problems[pid].add("red_card_without_time")
            if cards and pid in intervals:
                at = min((e["period"] - 1) * 45 + min(45, e["clock_seconds"] / 60) for e in cards)
                if at < intervals[pid][0]:
                    problems[pid].add("card_before_entry")
                intervals[pid][1] = min(intervals[pid][1], at)
            for e in actor:
                at = (e["period"] - 1) * 45 + min(45, e["clock_seconds"] / 60)
                # Roster minutes have one-minute precision; permit at most two minutes of annotation disagreement.
                if (
                    e["team_id"] != tid
                    or pid not in intervals
                    or not (intervals[pid][0] - 2 <= at <= intervals[pid][1] + 2)
                ):
                    problems[pid].add("action_outside_participation")
            start, end = intervals.get(pid, [0.0, 0.0])
            if end < start:
                problems[pid].add("negative_interval")
            result[pid] = dict(
                minutes=round(end - start, 6) if not problems[pid] else None,
                team_id=tid,
                reliable=not problems[pid],
                reasons=sorted(problems[pid]),
                starter=pid in starters,
                minute_method="nominal_regulation_roster_substitution_card",
                precision="substitutions_recorded_to_whole_minutes",
                participated=pid in intervals or bool(actor),
            )
    # An actor absent from both rosters invalidates that actor, not every known player.
    for pid, actor in actors.items():
        if pid > 0 and pid not in result:
            result[pid] = dict(
                minutes=None,
                team_id=actor[0]["team_id"],
                reliable=False,
                reasons=["actor_absent_from_roster"],
                starter=False,
                minute_method="unavailable",
                precision="unavailable",
                participated=True,
            )
    return result
