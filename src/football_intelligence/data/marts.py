"""Small local analytical layer. SQL is fixed, with no user query interface."""

from pathlib import Path

import duckdb
import polars as pl


def connect(directory: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    for name in [
        "competitions",
        "seasons",
        "teams",
        "players",
        "matches",
        "lineups",
        "events",
        "tracking_frames",
        "tracking_objects",
    ]:
        # File paths are trusted local configuration, never HTTP parameters.
        con.read_parquet(str(directory / f"{name}.parquet")).create_view(name)
    return con


def build_marts(directory: Path) -> dict[str, pl.DataFrame]:
    with connect(directory) as con:
        player_match = con.sql("""
            WITH counts AS (
              SELECT match_id, player_id,
                count(*) FILTER (WHERE event_type='Shot') AS shots,
                count(*) FILTER (WHERE event_type='Pass') AS passes,
                count(*) FILTER (WHERE event_type='Pass' AND outcome='Complete') AS completed_passes,
                count(*) FILTER (WHERE event_type='Shot' AND outcome='Goal') AS goals,
                sum(xg) AS xg,
                count(*) FILTER (WHERE event_type='Shot' AND xg IS NULL) AS missing_shot_xg
              FROM events WHERE period < 5 GROUP BY match_id, player_id
            )
            SELECT l.id, l.provider, l.match_id, l.player_id, p.name AS player_name,
              l.team_id, t.name AS team_name, m.season_id, m.competition_id, m.observed_on,
              l.starter, l.position, l.minutes, l.minutes_method,
              CASE WHEN l.provider='statsbomb' THEN coalesce(c.shots,0) END AS shots,
              CASE WHEN l.provider='statsbomb' THEN coalesce(c.passes,0) END AS passes,
              CASE WHEN l.provider='statsbomb' THEN coalesce(c.completed_passes,0) END AS completed_passes,
              CASE WHEN l.provider='statsbomb' THEN coalesce(c.goals,0) END AS goals,
              CASE WHEN l.provider='statsbomb' AND coalesce(c.missing_shot_xg,0)=0 THEN coalesce(c.xg,0) END AS xg,
              CASE WHEN l.provider='statsbomb' AND l.minutes>=30 THEN coalesce(c.shots,0)/l.minutes*90 END AS shots_per90,
              CASE WHEN c.passes>0 THEN c.completed_passes::DOUBLE/c.passes END AS pass_completion
            FROM lineups l JOIN players p ON p.id=l.player_id JOIN teams t ON t.id=l.team_id
            JOIN matches m ON m.id=l.match_id
            LEFT JOIN counts c ON c.match_id=l.match_id AND c.player_id=l.player_id
            ORDER BY l.provider, l.match_id, p.name
        """).pl()
        con.register("player_match", player_match.to_arrow())
        player_season = con.sql("""
            SELECT provider, season_id, competition_id, player_id, player_name,
              count(*) AS roster_matches, count(*) FILTER (WHERE minutes>0) AS appearances,
              sum(minutes) AS minutes, sum(starter::INTEGER) AS starts,
              sum(shots) AS shots, sum(passes) AS passes, sum(goals) AS goals,
              CASE WHEN count(xg)=count(*) THEN sum(xg) END AS xg,
              CASE WHEN sum(minutes)>=30 THEN sum(shots)/sum(minutes)*90 END AS shots_per90
            FROM player_match GROUP BY ALL ORDER BY provider, player_name
        """).pl()
        team_season = con.sql("""
            SELECT provider, season_id, competition_id, team_id, team_name,
              count(DISTINCT match_id) AS matches, sum(shots) AS shots,
              sum(passes) AS passes, sum(goals) AS player_goals_excluding_own_goals
            FROM player_match GROUP BY ALL ORDER BY provider, team_name
        """).pl()
    return {
        "player_match": player_match,
        "player_season": player_season,
        "team_season": team_season,
    }
