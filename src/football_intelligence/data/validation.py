"""Fail on contract errors; report genuine missingness and off-pitch observations."""

import math

import polars as pl

from football_intelligence.data.schema import TABLES

FOREIGN_KEYS = {
    "seasons": {"competition_id": "competitions"},
    "matches": {
        "competition_id": "competitions",
        "season_id": "seasons",
        "home_team_id": "teams",
        "away_team_id": "teams",
    },
    "lineups": {"match_id": "matches", "team_id": "teams", "player_id": "players"},
    "events": {"match_id": "matches", "team_id": "teams", "player_id": "players"},
    "tracking_frames": {"match_id": "matches", "possession_team_id": "teams"},
    "tracking_objects": {
        "match_id": "matches",
        "frame_id": "tracking_frames",
        "player_id": "players",
        "team_id": "teams",
    },
}


def validate(tables: dict[str, pl.DataFrame]) -> dict:
    warnings = []
    for name, model in TABLES.items():
        df = tables[name]
        for row in df.to_dicts():
            model.model_validate(row)
        key = "canonical_id" if name == "provider_entity_map" else "id"
        if df[key].null_count() or df[key].n_unique() != df.height:
            raise ValueError(f"{name}: null or duplicate primary key")
        for column, target in FOREIGN_KEYS.get(name, {}).items():
            if set(df[column].drop_nulls()) - set(tables[target]["id"]):
                raise ValueError(f"{name}.{column}: unresolved reference")
    for m in tables["matches"].to_dicts():
        if m["home_team_id"] == m["away_team_id"]:
            raise ValueError("Match must have two distinct teams")
        allowed = {m["home_team_id"], m["away_team_id"]}
        for name in ["lineups", "events", "tracking_objects"]:
            rows = tables[name].filter(pl.col("match_id") == m["id"])
            if set(rows["team_id"].drop_nulls()) - allowed:
                raise ValueError(f"{name}: team is not in match")
        lineup = tables["lineups"].filter(pl.col("match_id") == m["id"])
        for team in allowed:
            count = lineup.filter((pl.col("team_id") == team) & pl.col("starter")).height
            if count != 11:
                warnings.append(
                    f"{m['provider']} {m['provider_id']}: {count} starters recorded for {team}"
                )
    for name in ["events", "tracking_objects"]:
        df = tables[name]
        for row in df.select("x", "y").to_dicts():
            if (row["x"] is None) != (row["y"] is None):
                raise ValueError("Partially missing coordinate pair")
            if row["x"] is not None:
                if not all(math.isfinite(v) for v in row.values()):
                    raise ValueError("Non-finite coordinates")
                if not (-10 <= row["x"] <= 115 and -10 <= row["y"] <= 78):
                    raise ValueError("Coordinates outside generous physical envelope")
        outside = df.filter(
            (pl.col("x") < 0) | (pl.col("x") > 105) | (pl.col("y") < 0) | (pl.col("y") > 68)
        ).height
        if outside:
            warnings.append(f"{name}: {outside} off-pitch observations retained, not clipped")
    unavailable = tables["lineups"].filter(pl.col("minutes").is_null()).height
    if unavailable:
        warnings.append(
            f"lineups: {unavailable} unavailable minutes; absent metadata or inconsistent intervals"
        )
    events = tables["events"]
    for rows in events.partition_by("match_id"):
        times = rows.sort("index").select("period", "timestamp_seconds").rows()
        if [p for p, _ in times] != sorted(p for p, _ in times):
            raise ValueError("Event periods are not chronologically ordered")
        inversions = sum(b < a for a, b in zip(times, times[1:], strict=False))
        if inversions:
            warnings.append(
                f"events: {inversions} provider-index timestamp inversions retained; sort by period/time for timelines"
            )
        shots = rows.filter((pl.col("event_type") == "Shot") & (pl.col("period") < 5)).height
        if shots > 150:
            warnings.append("More than 150 shots in a match; inspect source")
    return {
        "status": "passed",
        "warnings": warnings,
        "null_counts": {name: df.null_count().row(0, named=True) for name, df in tables.items()},
    }
