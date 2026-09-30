import json

from football_intelligence.data.adapters.base import Rows
from football_intelligence.data.coordinates import STATSBOMB, to_canonical
from football_intelligence.data.positions import position_group

PERIOD_START = {1: 0, 2: 45 * 60, 3: 90 * 60, 4: 105 * 60, 5: 120 * 60}


def seconds(value: str) -> float:
    parts = [float(v) for v in value.split(":")]
    return sum(v * 60**i for i, v in enumerate(reversed(parts)))


def elapsed_lineup(value: str, period: int, ends: dict[int, float]) -> float:
    return sum(ends[p] for p in ends if p < period) + seconds(value) - PERIOD_START[period]


class StatsBombAdapter:
    provider = "statsbomb"

    def normalise(self, raw: dict, provenance_id: str) -> dict[str, list[dict]]:
        match = raw["match"]
        events = raw["events"]
        if not events or not raw["lineups"]:
            raise ValueError("StatsBomb event and lineup arrays must be non-empty")
        if len({e["id"] for e in events}) != len(events):
            raise ValueError("Duplicate StatsBomb event IDs")
        r = Rows(self.provider, provenance_id, match["match_date"])
        c = raw["competition"]
        comp = r.add(
            "competitions",
            c["competition_id"],
            name=c["competition_name"],
            country=c["country_name"],
            gender=c["competition_gender"],
        )
        year = int(c["season_name"].split("/")[0])
        season = r.add(
            "seasons",
            f"{c['competition_id']}:{c['season_id']}",
            competition_id=comp,
            name=c["season_name"],
            start_year=year,
            end_year=int(c["season_name"].split("/")[-1]),
        )
        teams = {}
        for side in ["home", "away"]:
            team = match[f"{side}_team"]
            teams[side] = r.add(
                "teams",
                team[f"{side}_team_id"],
                name=team[f"{side}_team_name"],
                country=team.get("country", {}).get("name"),
            )
        mid = r.add(
            "matches",
            match["match_id"],
            competition_id=comp,
            season_id=season,
            home_team_id=teams["home"],
            away_team_id=teams["away"],
            home_score=match["home_score"],
            away_score=match["away_score"],
            coverage="full_match_events_including_extra_time_and_shootout",
        )
        ends: dict[int, float] = {}
        for e in events:
            if e["period"] < 5:
                ends[e["period"]] = max(ends.get(e["period"], 0), seconds(e["timestamp"]))
        duration = sum(ends.values())
        for team in raw["lineups"]:
            for p in team["lineup"]:
                pid = r.add(
                    "players",
                    p["player_id"],
                    name=p["player_name"],
                    nationality=p.get("country", {}).get("name"),
                )
                intervals = p.get("positions", [])
                minutes = 0.0
                previous_end = -1.0
                valid_minutes = True
                for pos in intervals:
                    start = elapsed_lineup(pos["from"], pos["from_period"], ends)
                    end = (
                        elapsed_lineup(pos["to"], pos["to_period"], ends)
                        if pos.get("to") and pos.get("to_period")
                        else duration
                    )
                    if (
                        start < previous_end - 0.02
                        or end < start
                        or start < 0
                        or end > duration + 0.02
                    ):
                        valid_minutes = False
                    previous_end = end
                    minutes += max(0, end - start) / 60
                first = intervals[0] if intervals else {}
                r.add(
                    "lineups",
                    f"{match['match_id']}:{p['player_id']}",
                    match_id=mid,
                    player_id=pid,
                    team_id=r.id("teams", team["team_id"]),
                    starter=first.get("start_reason") == "Starting XI",
                    position=position_group(first.get("position")),
                    provider_positions_json=json.dumps(intervals, sort_keys=True),
                    minutes=round(minutes, 6) if valid_minutes else None,
                    minutes_method="lineup_intervals_actual_period_lengths"
                    if valid_minutes
                    else "unavailable_inconsistent_lineup_intervals",
                    substitution_in=first.get("from")
                    if first.get("start_reason", "").startswith("Substitution")
                    else None,
                    substitution_out=intervals[-1].get("to")
                    if intervals and intervals[-1].get("end_reason", "").startswith("Substitution")
                    else None,
                )
        for e in events:
            kind = e["type"]["name"]
            details = e.get(kind.lower().replace(" ", "_"), {})
            loc = e.get("location")
            end = details.get("end_location")
            x, y = (
                to_canonical(loc[0], loc[1], STATSBOMB, allow_outside=True) if loc else (None, None)
            )
            ex, ey = (
                to_canonical(end[0], end[1], STATSBOMB, allow_outside=True) if end else (None, None)
            )
            outcome = details.get("outcome", {}).get("name")
            if kind == "Pass" and outcome is None:
                outcome = "Complete"
            r.add(
                "events",
                e["id"],
                match_id=mid,
                index=e["index"],
                period=e["period"],
                timestamp_seconds=seconds(e["timestamp"]),
                team_id=r.id("teams", e["team"]["id"]),
                player_id=r.id("players", e["player"]["id"]) if e.get("player") else None,
                event_type=kind,
                subtype=details.get("type", {}).get("name"),
                outcome=outcome,
                x=x,
                y=y,
                end_x=ex,
                end_y=ey,
                raw_x=loc[0] if loc else None,
                raw_y=loc[1] if loc else None,
                possession=e.get("possession"),
                body_part=details.get("body_part", {}).get("name"),
                xg=details.get("statsbomb_xg"),
                attributes_json=json.dumps(e, sort_keys=True),
            )
        return r.result()
