"""Explicit common concepts, independent of both providers' native ontologies."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    kind: str
    complete: bool | None = None
    x: float | None = None
    y: float | None = None
    end_x: float | None = None
    end_y: float | None = None


CANDIDATES = [
    ("non_penalty_shots_per90", "Non-penalty shots", "Schoten zonder strafschoppen", "shots"),
    (
        "passes_all_per90",
        "Pass attempts, including restarts",
        "Passpogingen, inclusief spelhervattingen",
        "passes",
    ),
    (
        "pass_completion_all",
        "Pass completion, including restarts",
        "Passnauwkeurigheid, inclusief spelhervattingen",
        "completion",
    ),
    ("long_passes_all_per90", "Long pass attempts (≥30 m)", "Lange passpogingen (≥30 m)", "long"),
    (
        "progressive_passes_all_per90",
        "Completed progressive passes",
        "Geslaagde progressieve passes",
        "progressive",
    ),
    (
        "final_third_entries_all_per90",
        "Completed passes entering the final third",
        "Geslaagde passes het laatste derde in",
        "final_third",
    ),
    (
        "box_entries_all_per90",
        "Completed passes entering the penalty area",
        "Geslaagde passes het strafschopgebied in",
        "box",
    ),
]
# Availability screen: an unknown outcome must not become a completed/failed pass.
# Outcome-dependent candidates remain native diagnostics and are not harmonised v1 features.
COMMON = [row for row in CANDIDATES if row[3] in {"shots", "passes", "long"}]
COMMON_IDS = [row[0] for row in COMMON]
COUNT_KEYS = [
    "shots",
    "passes",
    "completed",
    "outcome_missing",
    "geometry_missing",
    "long",
    "progressive",
    "final_third",
    "box",
]
SB_NATIVE = [
    ("open_play_passes_per90", "Open-play passes", "Open-spelpasses", "open_passes"),
    (
        "open_play_completion",
        "Open-play pass completion",
        "Nauwkeurigheid van open-spelpasses",
        "open_completion",
    ),
    (
        "crosses_per90",
        "Cross attempts (provider flag)",
        "Voorzetpogingen (providerlabel)",
        "crosses",
    ),
    ("pressures_per90", "Pressure events", "Drukzetacties", "pressures"),
    ("carries_per90", "Carry events", "Carry-acties", "carries"),
    ("dribbles_per90", "Dribble events", "Dribbelacties", "dribbles"),
    ("tackles_per90", "Tackle duels", "Tackle-duels", "tackles"),
    ("interceptions_per90", "Interception events", "Onderscheppingsacties", "interceptions"),
    ("recoveries_per90", "Ball recovery events", "Balheroveringsacties", "recoveries"),
    ("non_penalty_xg_per90", "Provider non-penalty xG", "Provider-xG zonder strafschoppen", "npxg"),
]
WS_NATIVE = [
    ("pass_events_per90", "Pass events (type 8)", "Passacties (type 8)", "open_passes"),
    (
        "pass_event_completion",
        "Type-8 pass completion",
        "Nauwkeurigheid van type-8-passes",
        "open_completion",
    ),
    ("crosses_per90", "Cross subevents (80)", "Voorzetacties (80)", "crosses"),
    ("key_passes_per90", "Key-pass tags", "Sleutelpaslabels", "key_passes"),
    ("duels_per90", "Duel events", "Duelacties", "duels"),
    (
        "attacking_duels_per90",
        "Ground attacking duels",
        "Aanvallende grondduels",
        "attacking_duels",
    ),
    ("sliding_tackles_per90", "Sliding-tackle tags", "Sliding-tacklelabels", "sliding_tackles"),
    ("interceptions_per90", "Interception tags", "Onderscheppingslabels", "interceptions"),
    ("accelerations_per90", "Acceleration subevents", "Versnellingsacties", "accelerations"),
    ("clearances_per90", "Clearance subevents", "Wegwerkacties", "clearances"),
]
SET_PIECES = {"Corner", "Free Kick", "Throw-in", "Kick Off", "Goal Kick"}
NATIVE_COUNTS = sorted({r[3] for r in SB_NATIVE + WS_NATIVE} - {"open_completion"}) + [
    "open_completed",
    "open_outcome_missing",
]


def inside_box(x: float, y: float) -> bool:
    return 88.5 <= x <= 105 and 13.84 <= y <= 54.16


def progressive(x: float, y: float, ex: float, ey: float) -> bool:
    start = math.hypot(105 - x, 34 - y)
    return start - math.hypot(105 - ex, 34 - ey) >= max(10, start * 0.25)


def counts(actions: list[Action]) -> dict[str, float]:
    result = dict.fromkeys(COUNT_KEYS, 0.0)
    for a in actions:
        if a.kind == "shot":
            result["shots"] += 1
        elif a.kind == "pass":
            result["passes"] += 1
            result["completed"] += float(a.complete is True)
            result["outcome_missing"] += float(a.complete is None)
            values = (a.x, a.y, a.end_x, a.end_y)
            if any(v is None for v in values):
                result["geometry_missing"] += 1
                continue
            x, y, ex, ey = (float(v) for v in values if v is not None)
            result["long"] += float(math.hypot(ex - x, ey - y) >= 30)
            if a.complete:
                result["progressive"] += float(progressive(x, y, ex, ey))
                result["final_third"] += float(x < 70 <= ex)
                result["box"] += float(not inside_box(x, y) and inside_box(ex, ey))
    return result


def values(count: dict[str, float], minutes: float) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for key, _, _, numerator in CANDIDATES:
        if minutes <= 0:
            value = None
        elif numerator == "completion":
            value = (
                count["completed"] / count["passes"]
                if count["passes"] and not count["outcome_missing"]
                else None
            )
        elif (
            numerator in {"long", "progressive", "final_third", "box"} and count["geometry_missing"]
        ):
            value = None
        elif numerator in {"progressive", "final_third", "box"} and count["outcome_missing"]:
            value = None
        else:
            value = count[numerator] * 90 / minutes
        result[key] = round(value, 6) if value is not None else None
    return result


def native_values(
    provider: str, count: dict[str, float | None], minutes: float
) -> dict[str, float | None]:
    result = {}
    for key, _, _, numerator in SB_NATIVE if provider == "statsbomb" else WS_NATIVE:
        attempts, completed = count["open_passes"], count["open_completed"]
        total = count.get(numerator)
        if minutes <= 0:
            value = None
        elif numerator == "open_completion":
            value = (
                completed / attempts
                if attempts and completed is not None and count["open_outcome_missing"] == 0
                else None
            )
        else:
            value = total * 90 / minutes if total is not None else None
        result[key] = round(value, 6) if value is not None else None
    return result


def family(role: str | None) -> str | None:
    return {
        "CB": "DEF",
        "FB/WB": "DEF",
        "DM": "MID",
        "CM": "MID",
        "AM": "MID",
        "W": "FWD",
        "ST": "FWD",
        "GK": "GK",
        "DEF": "DEF",
        "MID": "MID",
        "FWD": "FWD",
    }.get(role or "")
