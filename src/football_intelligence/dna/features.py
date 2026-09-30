"""Canonical events -> match observations -> evidence-aware season profiles."""

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import polars as pl

from football_intelligence.data.schema import canonical_id
from football_intelligence.dna.cohort import COHORT, local_cohort, partitions, settings, write
from football_intelligence.dna.registry import CORE, REGISTRY, SPECS

SET_PIECES = {"Corner", "Free Kick", "Throw-in", "Kick Off", "Goal Kick"}


def per90(value: float | None, minutes: float | None) -> float | None:
    return (
        value * 90 / minutes if value is not None and minutes is not None and minutes > 0 else None
    )


def in_box(x: float, y: float) -> bool:
    return 88.5 <= x <= 105 and 13.84 <= y <= 54.16


def progressive(x: float, y: float, ex: float, ey: float, attack_left: bool = False) -> bool:
    if attack_left:
        x, y, ex, ey = 105 - x, 68 - y, 105 - ex, 68 - ey
    before = math.hypot(105 - x, 34 - y)
    return before - math.hypot(105 - ex, 34 - ey) >= max(10.0, 0.25 * before)


def role_summary(role_minutes: dict[str, float], minutes: float) -> dict:
    ordered = sorted(
        ((k, v) for k, v in role_minutes.items() if k != "unknown" and v > 0),
        key=lambda x: (-x[1], x[0]),
    )
    shares = {k: v / minutes for k, v in ordered} if minutes else {}
    primary = ordered[0][0] if ordered else None
    known = sum(shares.values())
    confident = bool(primary and known >= 0.6 and shares[primary] >= 0.4)
    return dict(
        primary_role=primary if confident else None,
        secondary_role=ordered[1][0] if len(ordered) > 1 else None,
        role_shares=shares,
        known_role_share=known,
        multi_role=bool(primary and shares[primary] < 0.7),
        role_entropy=-sum(v * math.log(v) for v in shares.values()),
    )


def match_observations(events: list[dict], lineups: list[dict], match: dict) -> list[dict]:
    event_by_id = {e["provider_id"]: e for e in events}
    attributes = {e["id"]: json.loads(e["attributes_json"]) for e in events}
    actor: dict[str, list[dict]] = defaultdict(list)
    ends: dict[int, float] = {}
    for e in events:
        if e["period"] < 5:
            if e["player_id"]:
                actor[e["player_id"]].append(e)
            if e["event_type"] == "Half End":
                ends[e["period"]] = max(ends.get(e["period"], 0), e["timestamp_seconds"])
    rows = []
    for lu in lineups:
        counts: dict[str, float | None] = dict.fromkeys(
            [k for k, *_ in SPECS] + ["goals", "npxg", "xa", "completed_passes"], 0.0
        )
        bins: Counter = Counter()

        def add(key: str, value: float = 1, target=counts):
            current = target[key]
            if current is not None:
                target[key] = current + value

        for e in actor[lu["player_id"]]:
            a = attributes[e["id"]]
            kind = e["event_type"]
            xy = (e["x"], e["y"], e["end_x"], e["end_y"])
            located = all(v is not None for v in xy)
            if (
                kind in ("Pass", "Carry", "Shot")
                and e["x"] is not None
                and e["y"] is not None
                and 0 <= e["x"] <= 105
                and 0 <= e["y"] <= 68
            ):
                bins[min(11, int(e["x"] / 105 * 12)), min(7, int(e["y"] / 68 * 8))] += 1
            if kind == "Shot" and e["subtype"] != "Penalty":
                add("shots")
                add("goals", float(e["outcome"] == "Goal"))
                if e["xg"] is None:
                    counts["npxg"] = None
                else:
                    add("npxg", e["xg"])
                if e["x"] is None or e["y"] is None:
                    counts["box_shots"] = None
                else:
                    add("box_shots", float(in_box(e["x"], e["y"])))
            if kind == "Pass":
                details = a.get("pass", {})
                link = details.get("assisted_shot_id")
                if link or details.get("shot_assist"):
                    shot = event_by_id.get(link)
                    valid = (
                        shot is not None
                        and shot["event_type"] == "Shot"
                        and shot["period"] < 5
                        and shot["team_id"] == e["team_id"]
                        and shot["index"] > e["index"]
                        and attributes[shot["id"]].get("shot", {}).get("key_pass_id")
                        == e["provider_id"]
                    )
                    if not valid:
                        counts["shot_assists"] = None
                        counts["xa"] = None
                    elif shot is not None and shot["subtype"] != "Penalty":
                        add("shot_assists")
                        if shot["xg"] is None:
                            counts["xa"] = None
                        else:
                            add("xa", shot["xg"])
                if e["subtype"] not in SET_PIECES:
                    add("passes")
                    complete = e["outcome"] == "Complete"
                    add("completed_passes", float(complete))
                    add("crosses", float(complete and details.get("cross", False)))
                    if located:
                        x, y, ex, ey = xy
                        add("long_passes", float(math.hypot(ex - x, ey - y) >= 30))
                        add("progressive_passes", float(complete and progressive(x, y, ex, ey)))
                        add("final_third_passes", float(complete and x < 70 <= ex))
                        add("box_passes", float(complete and not in_box(x, y) and in_box(ex, ey)))
                    else:
                        for key in [
                            "long_passes",
                            "progressive_passes",
                            "final_third_passes",
                            "box_passes",
                        ]:
                            counts[key] = None
            if kind == "Carry":
                add("carries")
                if located:
                    x, y, ex, ey = xy
                    add("progressive_carries", float(progressive(x, y, ex, ey)))
                    add("carry_distance", math.hypot(ex - x, ey - y))
                    add("box_carries", float(not in_box(x, y) and in_box(ex, ey)))
                else:
                    for key in ["progressive_carries", "carry_distance", "box_carries"]:
                        counts[key] = None
            if kind == "Pressure":
                add("pressures")
                add("counterpressures", float(a.get("counterpress", False)))
            if kind == "Duel" and e["subtype"] == "Tackle":
                add("tackles")
            if kind == "Interception":
                add("interceptions")
            if kind == "Ball Recovery":
                add("recoveries")
        own: set = set()
        opp: set = set()
        team_passes = 0
        intervals = json.loads(lu["participation_json"])
        context_valid = True
        for e in events:
            if e["period"] > 4:
                continue
            at = sum(v for k, v in ends.items() if k < e["period"]) + e["timestamp_seconds"]
            if not any(start <= at <= end for start, end in intervals):
                continue
            possession_team = attributes[e["id"]].get("possession_team", {}).get("id")
            if e["possession"] is None or possession_team is None:
                context_valid = False
                continue
            possession_key = (e["period"], e["possession"], possession_team)
            # Compare the source ID from event JSON with lineup's canonical team via event team map.
            own_team = canonical_id("statsbomb", "teams", possession_team) == lu["team_id"]
            (own if own_team else opp).add(possession_key)
            if (
                e["team_id"] == lu["team_id"]
                and e["event_type"] == "Pass"
                and e["subtype"] not in SET_PIECES
            ):
                team_passes += 1
        rows.append(
            dict(
                player_id=lu["player_id"],
                team_id=lu["team_id"],
                match_id=lu["match_id"],
                observed_on=str(match["observed_on"]),
                competition_id=match["competition_id"],
                season_id=match["season_id"],
                minutes=lu["minutes"],
                minutes_reliable=lu["minutes_reliable"],
                minutes_quality=lu["minutes_quality"],
                minutes_quality_reason=lu["minutes_quality_reason"],
                role_minutes_json=lu["role_minutes_json"],
                bins_json=json.dumps([[x, y, v] for (x, y), v in sorted(bins.items())]),
                own_possessions=len(own) if context_valid else None,
                opponent_possessions=len(opp) if context_valid else None,
                team_passes=team_passes,
                **counts,
            )
        )
    return rows


def aggregate(rows: list[dict]) -> dict:
    reliable = [
        r for r in rows if r["minutes_reliable"] and r["minutes"] is not None and r["minutes"] > 0
    ]
    minutes = sum(r["minutes"] for r in reliable)
    keys = [k for k, *_ in SPECS] + [
        "goals",
        "npxg",
        "xa",
        "completed_passes",
        "own_possessions",
        "opponent_possessions",
        "team_passes",
    ]
    totals = {
        k: sum(r[k] for r in reliable)
        if reliable and all(r[k] is not None for r in reliable)
        else None
        for k in keys
    }
    values = {k + "_per90": per90(totals[k], minutes) for k, *_ in SPECS}

    def ratio(n: str, d: str, scale=1):
        numerator, denominator = totals[n], totals[d]
        return (
            scale * numerator / denominator
            if numerator is not None and denominator is not None and denominator > 0
            else None
        )

    values.update(
        goals=totals["goals"],
        npxg_per90=per90(totals["npxg"], minutes),
        xa_per90=per90(totals["xa"], minutes),
        xg_per_shot=ratio("npxg", "shots"),
        pass_completion=ratio("completed_passes", "passes"),
        pressures_per100_opponent=ratio("pressures", "opponent_possessions", 100),
        interceptions_per100_opponent=ratio("interceptions", "opponent_possessions", 100),
        progressive_passes_per100_team=ratio("progressive_passes", "own_possessions", 100),
        team_pass_share=ratio("passes", "team_passes"),
    )
    role_minutes: Counter = Counter()
    bins: Counter = Counter()
    for r in reliable:
        role_minutes.update(json.loads(r["role_minutes_json"]))
        bins.update({(x, y): v for x, y, v in json.loads(r["bins_json"])})
    return dict(
        player_id=rows[0]["player_id"],
        minutes=minutes,
        appearances=len(reliable),
        unreliable_appearances=sum(not r["minutes_reliable"] for r in rows),
        team_ids=sorted({r["team_id"] for r in reliable} or {r["team_id"] for r in rows}),
        values=values,
        **role_summary(dict(role_minutes), minutes),
        bins=[[x, y, v] for (x, y), v in sorted(bins.items())],
    )


def eligibility(profile: dict, threshold: float) -> list[str]:
    reasons = []
    if profile["minutes"] < threshold:
        reasons.append("below_minutes")
    if not profile["primary_role"]:
        reasons.append("uncertain_role")
    if profile["primary_role"] == "GK":
        reasons.append("goalkeeper_excluded")
    if any(profile["values"][f] is None for f in CORE):
        reasons.append("missing_core_features")
    return reasons


def build_features(root: Path, name: str = COHORT) -> dict:
    directory = local_cohort(root, name)
    cohort = json.loads((directory / "cohort.json").read_text())
    matches = {r["id"]: r for r in pl.read_parquet(directory / "matches.parquet").to_dicts()}
    observations = []
    for i, (_, events, lineups) in enumerate(partitions(root, name), 1):
        observations.extend(
            match_observations(
                events.to_dicts(), lineups.to_dicts(), matches[lineups["match_id"][0]]
            )
        )
        if i % 20 == 0 or i == len(matches):
            print(f"Feature matches: {i}/{len(matches)}", flush=True)
    frame = pl.DataFrame(observations, infer_schema_length=None)
    frame.write_parquet(directory / "player_feature_observation.parquet", compression="zstd")
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in observations:
        groups[r["player_id"]].append(r)
    profiles = [aggregate(v) for _, v in sorted(groups.items())]
    players = {
        r["id"]: r["name"] for r in pl.read_parquet(directory / "players.parquet").to_dicts()
    }
    teams = {r["id"]: r["name"] for r in pl.read_parquet(directory / "teams.parquet").to_dicts()}
    for p in profiles:
        p.update(
            name=players[p["player_id"]],
            teams=[teams[t] for t in p["team_ids"]],
            cohort=name,
            competition=cohort["competition"],
            season=cohort["season"],
        )
    write(directory / "player_profiles.json", profiles)
    thresholds = {}
    minimum = settings(root)["minimum_role_players"]
    for threshold in settings(root)["thresholds"]:
        candidates = [p for p in profiles if not eligibility(p, threshold)]
        roles = Counter(p["primary_role"] for p in candidates)
        eligible = [p for p in candidates if roles[p["primary_role"]] >= minimum]
        exclusions = {
            p["player_id"]: eligibility(p, threshold)
            or (["sparse_role"] if roles[p["primary_role"]] < minimum else [])
            for p in profiles
        }
        thresholds[str(threshold)] = dict(
            eligible=len(eligible),
            roles=dict(sorted(Counter(p["primary_role"] for p in eligible).items())),
            before_role_size=dict(sorted(roles.items())),
            excluded=[dict(player_id=k, reasons=v) for k, v in exclusions.items() if v],
        )
    report = dict(
        cohort=name,
        competition=cohort["competition"],
        season=cohort["season"],
        complete=cohort["complete"],
        source_revision=cohort["source_revision"],
        matches=len(matches),
        teams=len(teams),
        roster_players=len(profiles),
        players_with_reliable_minutes=sum(p["minutes"] > 0 for p in profiles),
        minutes_quality=cohort["minutes_quality"],
        dates=[cohort["dates"][0], cohort["dates"][-1]],
        role_counts=dict(Counter(p["primary_role"] or "unknown" for p in profiles)),
        minutes_quantiles=dict(
            zip(
                ["min", "p25", "p50", "p75", "max"],
                np.quantile([p["minutes"] for p in profiles], [0, 0.25, 0.5, 0.75, 1]).tolist(),
                strict=True,
            )
        ),
        appearances_quantiles=dict(
            zip(
                ["min", "p25", "p50", "p75", "max"],
                np.quantile([p["appearances"] for p in profiles], [0, 0.25, 0.5, 0.75, 1]).tolist(),
                strict=True,
            )
        ),
        feature_availability={
            f.id: sum(p["values"][f.id] is not None for p in profiles) for f in REGISTRY
        },
        missing_player_ids=sum(r["player_id"] is None for r in observations),
        minimum_role_players=minimum,
        thresholds=thresholds,
    )
    write(root / "artifacts/phase2/cohort_eligibility.json", report)
    write(root / "artifacts/phase2/feature_registry.json", [f.model_dump() for f in REGISTRY])
    return report
