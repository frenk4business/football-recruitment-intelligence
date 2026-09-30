import json

from football_intelligence.data.adapters.base import Rows
from football_intelligence.data.adapters.statsbomb import PERIOD_START, seconds
from football_intelligence.data.coordinates import CoordinateSystem, in_pitch, to_canonical
from football_intelligence.data.positions import position_group


class SkillCornerAdapter:
    provider = "skillcorner"

    def normalise(self, raw: dict, provenance_id: str) -> dict[str, list[dict]]:
        m = raw["match"]
        r = Rows(self.provider, provenance_id, m["date_time"][:10])
        c = m["competition_edition"]["competition"]
        s = m["competition_edition"]["season"]
        cid = r.add("competitions", c["id"], name=c["name"], country=c["area"], gender=c["gender"])
        sid = r.add(
            "seasons",
            f"{c['id']}:{s['id']}",
            competition_id=cid,
            name=s["name"],
            start_year=s["start_year"],
            end_year=s["end_year"],
        )
        teams = {
            side: r.add("teams", m[f"{side}_team"]["id"], name=m[f"{side}_team"]["name"])
            for side in ["home", "away"]
        }
        mid = r.add(
            "matches",
            m["id"],
            competition_id=cid,
            season_id=sid,
            home_team_id=teams["home"],
            away_team_id=teams["away"],
            home_score=m["home_team_score"],
            away_score=m["away_team_score"],
            pitch_length=m["pitch_length"],
            pitch_width=m["pitch_width"],
            coverage="60_second_tracking_sample_1hz_full_match_roster_metadata",
        )
        player_teams = {}
        for p in m["players"]:
            pid = r.add(
                "players",
                p["id"],
                name=f"{p['first_name'].strip()} {p['last_name'].strip()}",
                birth_date=p.get("birthday"),
            )
            tid = r.id("teams", p["team_id"])
            player_teams[p["id"]] = tid
            minutes = ((p.get("playing_time") or {}).get("total") or {}).get("minutes_played")
            pos = p.get("player_role") or {}
            r.add(
                "lineups",
                f"{m['id']}:{p['id']}",
                match_id=mid,
                team_id=tid,
                player_id=pid,
                starter=p.get("start_time") == "00:00:00",
                position=position_group(pos.get("name")),
                provider_positions_json=json.dumps(pos, sort_keys=True),
                minutes=minutes,
                minutes_method="provider_full_match_metadata",
                substitution_in=p.get("start_time"),
                substitution_out=p.get("end_time"),
            )
        system = CoordinateSystem(m["pitch_length"], m["pitch_width"], centered=True)
        seen = set()
        for frame in raw["tracking"]:
            if frame["frame"] in seen:
                raise ValueError("Duplicate tracking frame")
            seen.add(frame["frame"])
            period = frame["period"]
            group = (frame.get("possession") or {}).get("group")
            fid = r.add(
                "tracking_frames",
                f"{m['id']}:{frame['frame']}",
                match_id=mid,
                frame=frame["frame"],
                period=period,
                timestamp_seconds=seconds(frame["timestamp"]) - PERIOD_START[period],
                provider_timestamp=frame["timestamp"],
                possession_team_id=teams.get(group) if group is not None else None,
                home_attacking_direction=m.get("home_team_side", [None, None])[period - 1],
            )
            objects = [("player", obj) for obj in frame["player_data"]]
            objects.append(("ball", frame["ball_data"]))
            for kind, obj in objects:
                if obj.get("x") is None or obj.get("y") is None:
                    continue
                player = obj.get("player_id")
                x, y = to_canonical(obj["x"], obj["y"], system, allow_outside=True)
                r.add(
                    "tracking_objects",
                    f"{m['id']}:{frame['frame']}:{kind}:{player}",
                    frame_id=fid,
                    match_id=mid,
                    object_type=kind,
                    player_id=r.id("players", player) if player is not None else None,
                    team_id=player_teams.get(player),
                    x=x,
                    y=y,
                    z=obj.get("z"),
                    raw_x=obj["x"],
                    raw_y=obj["y"],
                    is_detected=obj.get("is_detected"),
                    in_pitch=in_pitch(x, y),
                )
        if not seen:
            raise ValueError("No usable tracking frames")
        return r.result()
