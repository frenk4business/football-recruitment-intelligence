"""Wyscout-native recruitment registry and conservative event-to-count mapping."""

import math
from collections import Counter

VERSION = "wyscout-recruitment-features-v1"
# Every row is audited against the pinned Figshare event and tag dictionaries.
ROWS = [
    (
        "non_penalty_shots",
        "Non-penalty shots",
        "Schoten zonder penalty",
        "shooting",
        "event 10 or 3/33; exclude 3/35",
        [],
    ),
    (
        "box_shots",
        "Shots inside the box",
        "Schoten uit strafschopgebied",
        "shooting",
        "non-penalty shot; start inside penalty area",
        [],
    ),
    (
        "on_target_shots",
        "On-target tagged shots",
        "Schoten met doelvlak-tag",
        "shooting",
        "non-penalty shot; tag 1201–1209 or 101, excluding 2101",
        [101, *range(1201, 1210), 2101],
    ),
    (
        "passes",
        "Open-play pass attempts",
        "Passpogingen uit open spel",
        "passing",
        "event 8; all subtypes; no restart event 3",
        [],
    ),
    (
        "completed_passes",
        "Completed open-play passes",
        "Geslaagde passes uit open spel",
        "passing",
        "event 8; tag 1801 and not 1802",
        [1801, 1802],
    ),
    (
        "pass_completion",
        "Open-play pass completion",
        "Passnauwkeurigheid open spel",
        "passing",
        "completed_passes / passes × 100",
        [1801, 1802],
    ),
    (
        "forward_passes",
        "Forward pass attempts",
        "Voorwaartse passpogingen",
        "passing",
        "event 8; end_x > x in attacking coordinates",
        [],
    ),
    (
        "progressive_passes",
        "Completed progressive passes",
        "Geslaagde progressieve passes",
        "passing",
        "event 8, completed; goal-distance reduction ≥30/15/10 m for own/crossing/opposition half",
        [1801, 1802],
    ),
    (
        "final_third_entries",
        "Completed final-third entries",
        "Geslaagde passes naar laatste derde",
        "passing",
        "event 8, completed; x < 70 and end_x >= 70",
        [1801, 1802],
    ),
    (
        "box_entries",
        "Completed penalty-area entries",
        "Geslaagde passes naar strafschopgebied",
        "passing",
        "event 8, completed; outside-to-inside penalty area",
        [1801, 1802],
    ),
    (
        "long_passes",
        "Long pass attempts",
        "Lange passpogingen",
        "passing",
        "event 8; endpoint Euclidean distance >= 30 m",
        [],
    ),
    ("crosses", "Cross attempts", "Voorzetpogingen", "creation", "event 8/subtype 80", []),
    (
        "completed_crosses",
        "Completed crosses",
        "Geslaagde voorzetten",
        "creation",
        "event 8/subtype 80; tag 1801 and not 1802",
        [1801, 1802],
    ),
    (
        "key_passes",
        "Key-pass tagged passes",
        "Passes met sleutelpass-tag",
        "creation",
        "event 8; tag 302",
        [302],
    ),
    (
        "attacking_duels",
        "Ground attacking duels",
        "Aanvallende grondduels",
        "attacking",
        "event 1/subtype 11",
        [],
    ),
    (
        "won_attacking_duels",
        "Won ground attacking duels",
        "Gewonnen aanvallende grondduels",
        "attacking",
        "event 1/subtype 11; sole outcome tag 703",
        [701, 702, 703],
    ),
    (
        "defensive_duels",
        "Ground defending duels",
        "Verdedigende grondduels",
        "defending",
        "event 1/subtype 12",
        [],
    ),
    (
        "won_defensive_duels",
        "Won ground defending duels",
        "Gewonnen verdedigende grondduels",
        "defending",
        "event 1/subtype 12; sole outcome tag 703",
        [701, 702, 703],
    ),
    ("aerial_duels", "Aerial duels", "Luchtduels", "defending", "event 1/subtype 10", []),
    (
        "won_aerial_duels",
        "Won aerial duels",
        "Gewonnen luchtduels",
        "defending",
        "event 1/subtype 10; sole outcome tag 703",
        [701, 702, 703],
    ),
    (
        "interceptions",
        "Interception-tagged actions",
        "Acties met onderschepping-tag",
        "defending",
        "actor event with tag 1401",
        [1401],
    ),
    (
        "sliding_tackles",
        "Sliding-tackle-tagged actions",
        "Acties met sliding-tag",
        "defending",
        "actor event with tag 1601",
        [1601],
    ),
    ("clearances", "Clearances", "Weggewerkte ballen", "defending", "event 7/subtype 71", []),
    (
        "accelerations",
        "Acceleration events",
        "Versnellingsacties",
        "attacking",
        "event 7/subtype 70; not tracking speed",
        [],
    ),
]
KEYS = [r[0] for r in ROWS]
FAMILIES = sorted({r[3] for r in ROWS})
FEATURE_FAMILIES = [r[3] for r in ROWS]


def registry() -> dict:
    return {
        "version": VERSION,
        "provider": "wyscout",
        "pitch_metres": [105, 68],
        "role_policy": "GKP→GK, DEF→DEF, MID→MID, FWD→FWD; no finer inference",
        "features": [
            {
                "id": key,
                "label_en": en,
                "label_nl": nl,
                "family": family,
                "formula": "completed_passes / passes * 100"
                if key == "pass_completion"
                else "count * 90 / reliable nominal regulation minutes",
                "event_mapping": mapping,
                "tags_required": tags,
                "unit": "%" if key == "pass_completion" else "per90",
                "null_semantics": "Unavailable when an applicable event lacks required geometry/outcome, minutes are unreliable, or a ratio has zero denominator. Zero means a valid observed zero count.",
                "role_suitability": ["DEF", "MID", "FWD"],
                "research_note": "Provider-native historical event involvement, not ability, transfer success or a StatsBomb-equivalent measure. See registered v1.2 plan.",
            }
            for key, en, nl, family, mapping, tags in ROWS
        ],
    }


def box(x, y) -> bool:
    return 88.5 <= x <= 105 and 13.84 <= y <= 54.16


def point(*coordinates) -> bool:
    return all(isinstance(x, (int, float)) and math.isfinite(x) for x in coordinates)


def progressive(x, y, ex, ey) -> bool:
    reduction = math.hypot(105 - x, 34 - y) - math.hypot(105 - ex, 34 - ey)
    if x < 52.5 and ex < 52.5:
        return reduction >= 30
    if x < 52.5 <= ex:
        return reduction >= 15
    if x >= 52.5 and ex >= 52.5:
        return reduction >= 10
    return False


def count_events(events: list[dict]) -> tuple[dict, list[str]]:
    counts: Counter = Counter(dict.fromkeys(KEYS, 0))
    missing: set[str] = set()
    for e in events:
        kind, sub = e["provider_event_id"], int(e["provider_subtype_id"] or -1)
        tags = set(e["tags"])
        x, y, ex, ey = (e.get(k) for k in ["x", "y", "end_x", "end_y"])
        if kind == 10 or (kind == 3 and sub == 33):
            counts["non_penalty_shots"] += 1
            if point(x, y):
                counts["box_shots"] += box(x, y)
            else:
                missing.add("box_shots")
            counts["on_target_shots"] += bool(tags & {101, *range(1201, 1210)}) and 2101 not in tags
        if kind == 8:
            counts["passes"] += 1
            counts["crosses"] += sub == 80
            counts["key_passes"] += 302 in tags
            known = len(tags & {1801, 1802}) == 1
            completed = 1801 in tags and 1802 not in tags
            if not known:
                missing.update(
                    [
                        "completed_passes",
                        "pass_completion",
                        "progressive_passes",
                        "final_third_entries",
                        "box_entries",
                    ]
                )
                if sub == 80:
                    missing.add("completed_crosses")
            counts["completed_passes"] += completed
            counts["completed_crosses"] += sub == 80 and completed
            if point(x, y, ex, ey):
                assert x is not None and y is not None and ex is not None and ey is not None
                counts["forward_passes"] += ex > x
                counts["long_passes"] += math.hypot(ex - x, ey - y) >= 30
                counts["progressive_passes"] += completed and progressive(x, y, ex, ey)
                counts["final_third_entries"] += completed and x < 70 <= ex
                counts["box_entries"] += completed and not box(x, y) and box(ex, ey)
            else:
                missing.update(
                    [
                        "forward_passes",
                        "long_passes",
                        "progressive_passes",
                        "final_third_entries",
                        "box_entries",
                    ]
                )
        if kind == 1 and sub in {10, 11, 12}:
            feature = {10: "aerial_duels", 11: "attacking_duels", 12: "defensive_duels"}[sub]
            counts[feature] += 1
            if len(tags & {701, 702, 703}) != 1:
                missing.add("won_" + feature)
            counts["won_" + feature] += 703 in tags and not tags & {701, 702}
        counts["interceptions"] += 1401 in tags
        counts["sliding_tackles"] += 1601 in tags
        counts["clearances"] += kind == 7 and sub == 71
        counts["accelerations"] += kind == 7 and sub == 70
    return dict(counts), sorted(missing)


def values(counts: dict, missing: set[str], minutes: float) -> dict:
    result: dict[str, float | None] = {}
    for key in KEYS:
        if key in missing or minutes <= 0:
            result[key] = None
        elif key == "pass_completion":
            result[key] = (
                round(100 * counts["completed_passes"] / counts["passes"], 6)
                if counts["passes"]
                else None
            )
        else:
            result[key] = round(counts[key] * 90 / minutes, 6)
    return result
