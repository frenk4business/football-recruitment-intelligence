"""Expanded StatsBomb observations; frozen Player DNA extraction is left untouched."""

import json
import math

from football_intelligence.data.minutes import clock_seconds, reconcile
from football_intelligence.dna.features import role_summary
from football_intelligence.profiles.features import NATIVE_COUNTS, SET_PIECES, Action


def coordinates(location) -> tuple[float | None, float | None]:
    if not isinstance(location, list) or len(location) < 2:
        return None, None
    x, y = location[:2]
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y)) or not (
        0 <= x <= 120 and 0 <= y <= 80
    ):
        return None, None
    return round(x * 105 / 120, 6), round(y * 68 / 80, 6)


def common_action(raw: dict) -> Action | None:
    kind = raw["type"]["name"]
    if kind == "Shot" and raw.get("shot", {}).get("type", {}).get("name") != "Penalty":
        return Action("shot")
    if kind == "Pass":
        p = raw.get("pass", {})
        outcome = p.get("outcome", {}).get("name", "Complete")
        complete = (
            True
            if outcome == "Complete"
            else False
            if outcome in {"Incomplete", "Out", "Pass Offside", "Injury Clearance", "Unknown"}
            else None
        )
        # Unknown is genuinely unavailable; it must not enter a completion denominator as a failure.
        if outcome == "Unknown" or "pass" not in raw:
            complete = None
        x, y = coordinates(raw.get("location"))
        ex, ey = coordinates(p.get("end_location"))
        return Action("pass", complete, x, y, ex, ey)
    return None


def native_counts(events: list[dict], match_types: set[str]) -> dict:
    result: dict[str, float | None] = dict.fromkeys(NATIVE_COUNTS, 0.0)

    def add(key: str, value: float):
        previous = result[key]
        if previous is not None:
            result[key] = previous + value

    for key, kind in [
        ("pressures", "Pressure"),
        ("carries", "Carry"),
        ("recoveries", "Ball Recovery"),
    ]:
        if kind not in match_types:
            result[key] = None
    for e in events:
        kind = e["type"]["name"]
        if kind == "Pass":
            details = e.get("pass", {})
            if details.get("type", {}).get("name") not in SET_PIECES:
                add("open_passes", 1)
                outcome = common_action(e)
                add("open_completed", float(outcome is not None and outcome.complete is True))
                add("open_outcome_missing", float(outcome is None or outcome.complete is None))
            add("crosses", float(details.get("cross", False)))
        if kind == "Shot" and e.get("shot", {}).get("type", {}).get("name") != "Penalty":
            xg = e.get("shot", {}).get("statsbomb_xg")
            if xg is None:
                result["npxg"] = None
            elif result["npxg"] is not None:
                add("npxg", float(xg))
        for key, expected in [
            ("pressures", "Pressure"),
            ("carries", "Carry"),
            ("dribbles", "Dribble"),
            ("interceptions", "Interception"),
            ("recoveries", "Ball Recovery"),
        ]:
            if kind == expected and result[key] is not None:
                add(key, 1)
        add(
            "tackles",
            float(kind == "Duel" and e.get("duel", {}).get("type", {}).get("name") == "Tackle"),
        )
    return result


def minutes(raw: dict) -> dict[int, dict]:
    if {e["period"] for e in raw["events"] if e["type"]["name"] == "Half End"} != {1, 2}:
        return {}
    ends: dict[int, float] = {}
    for e in raw["events"]:
        if e["type"]["name"] == "Half End":
            ends[e["period"]] = max(ends.get(e["period"], 0), clock_seconds(e["timestamp"]))
    if any(t < 2700 or t > 3900 for t in ends.values()):
        return {}
    reconciled = reconcile(raw)
    result = {}
    teams = {p["player_id"]: t["team_id"] for t in raw["lineups"] for p in t["lineup"]}
    actor_ids = {e.get("player", {}).get("id") for e in raw["events"]}
    for pid, row in reconciled.items():
        segments = json.loads(row["participation_json"])
        nominal = 0.0
        for a, b in segments:
            for start in (0, ends[1]):
                nominal += max(0, min(b, start + 2700) - max(a, start)) / 60
        roles = json.loads(row["role_minutes_json"])
        summary = role_summary(roles, row["minutes"] or 0)
        result[pid] = dict(
            minutes=round(nominal, 6) if row["minutes_reliable"] else None,
            team_id=teams[pid],
            reliable=row["minutes_reliable"],
            reasons=[] if row["minutes_reliable"] else row["minutes_quality_reason"].split(";"),
            role=summary["primary_role"],
            role_minutes=roles,
            minute_method="nominal_regulation_from_reconciled_event_intervals",
            precision="event_clock_seconds_clipped_to_regulation_halves",
            participated=bool(segments) or pid in actor_ids,
            elapsed_minutes=row["minutes"],
        )
    return result


def canonical(raw: list[dict], mid: int) -> list[dict]:
    result = []
    seen = set()
    for e in raw:
        if e["id"] in seen:
            raise ValueError("Duplicate StatsBomb event ID")
        seen.add(e["id"])
        x, y = coordinates(e.get("location"))
        kind = e["type"]["name"]
        attr = e.get(kind.lower().replace(" ", "_"), {})
        ex, ey = coordinates(attr.get("end_location"))
        result.append(
            dict(
                provider="statsbomb",
                event_id=e["id"],
                match_id=mid,
                player_id=e.get("player", {}).get("id"),
                team_id=e.get("team", {}).get("id"),
                period=e["period"],
                clock_seconds=clock_seconds(e["timestamp"]),
                provider_event_id=e["type"]["id"],
                provider_event_type=kind,
                provider_subtype=attr.get("type", {}).get("name"),
                original_positions=json.dumps([e.get("location"), attr.get("end_location")]),
                x=x,
                y=y,
                end_x=ex,
                end_y=ey,
                attributes_json=json.dumps(attr, separators=(",", ":")),
            )
        )
    return result
