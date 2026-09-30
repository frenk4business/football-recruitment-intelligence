"""Team-event context and within-club stint profiles; never mean player DNA."""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

from football_intelligence.dna.cohort import local_cohort, partitions, write
from football_intelligence.dna.features import aggregate, eligibility, match_observations
from football_intelligence.dna.registry import CORE
from football_intelligence.dna.similarity import percentile, select
from football_intelligence.recruitment.contracts import ClubContext
from football_intelligence.recruitment.registry import CONTEXT_FEATURES


def team_observations(events: list[dict], match: dict) -> list[dict]:
    """One artificial counting actor per team reuses the unchanged event definitions.

    Every event is attributed to its team exactly once, including goalkeeper events.
    There is no player-rate averaging and no reliability-driven player selection.
    Synthetic participation spans actual match duration, solely for denominators.
    """
    ends: dict[int, float] = {}
    for e in events:
        if e["event_type"] == "Half End" and e["period"] < 5:
            ends[e["period"]] = max(ends.get(e["period"], 0), e["timestamp_seconds"])
    if set(ends) not in ({1, 2}, {1, 2, 3, 4}):
        raise ValueError("Cannot build team context without complete match duration")
    duration = sum(ends.values())
    if duration <= 0:
        raise ValueError("Team duration must be positive")
    teams = [match["home_team_id"], match["away_team_id"]]
    team_actors = [dict(e, player_id=e["team_id"]) for e in events]
    windows = [
        dict(
            player_id=tid,
            team_id=tid,
            match_id=match["id"],
            minutes=duration / 60,
            minutes_reliable=True,
            minutes_quality="team_match_duration",
            minutes_quality_reason="Actual elapsed period endpoints; not summed player minutes",
            role_minutes_json="{}",
            participation_json=json.dumps([[0, duration]]),
        )
        for tid in teams
    ]
    return match_observations(team_actors, windows, match)


def aggregate_team_context(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[row["competition_id"], row["season_id"], row["team_id"]].append(row)
    result = []
    for (competition, season, tid), matches in sorted(groups.items()):
        if len({r["match_id"] for r in matches}) != len(matches):
            raise ValueError("Duplicate team-match observation")
        profile = aggregate(matches)
        features = []
        for f in CONTEXT_FEATURES:
            count = f.removesuffix("_per90")
            features.append(
                dict(
                    feature_id=f,
                    value=profile["values"][f],
                    percentile=None,
                    available_matches=sum(r[count] is not None for r in matches),
                )
            )
        result.append(
            dict(
                club_id=tid,
                competition_id=competition,
                season_id=season,
                observation_start=min(r["observed_on"] for r in matches),
                observation_end=max(r["observed_on"] for r in matches),
                matches=len(matches),
                team_minutes=profile["minutes"],
                features=features,
            )
        )
    for club in result:
        cohort = [
            c
            for c in result
            if (c["competition_id"], c["season_id"]) == (club["competition_id"], club["season_id"])
        ]
        for feature in club["features"]:
            values = [
                f["value"]
                for c in cohort
                for f in c["features"]
                if f["feature_id"] == feature["feature_id"] and f["value"] is not None
            ]
            if feature["value"] is not None:
                feature["percentile"] = percentile(np.array(values), feature["value"])
    return result


def roster_context(observations: list[dict], profiles: list[dict], names: dict[str, str]) -> dict:
    # A club's roster reference only uses that player's events at this club.
    groups = defaultdict(list)
    for r in observations:
        groups[r["team_id"], r["player_id"]].append(r)
    selected = select(profiles, 900)
    references = {
        role: {
            f: np.array([p["values"][f] for p in selected if p["primary_role"] == role])
            for f in CORE
        }
        for role in sorted({p["primary_role"] for p in selected})
    }
    rosters = defaultdict(list)
    for (tid, pid), rows in sorted(groups.items()):
        p = aggregate(rows)
        reasons = eligibility(p, 900)
        if p["primary_role"] not in references:
            reasons.append("unsupported_role")
        values = (
            {f: percentile(references[p["primary_role"]][f], p["values"][f]) for f in CORE}
            if not reasons
            else {}
        )
        rosters[tid].append(
            dict(
                player_id=pid,
                name=names[pid],
                minutes=p["minutes"],
                role=p["primary_role"],
                profile_eligible=not reasons,
                percentiles=values,
                exclusions=sorted(set(reasons)),
            )
        )
    result = {}
    for tid, players in sorted(rosters.items()):
        roles = []
        for role in sorted({p["role"] or "unknown" for p in players}):
            group = [p for p in players if (p["role"] or "unknown") == role]
            eligible = [p for p in group if p["profile_eligible"]]
            minutes = sum(p["minutes"] for p in group)
            item = dict(
                role=role,
                players=group,
                reliable_minutes=minutes,
                roster_depth=sum(p["minutes"] > 0 for p in group),
                profile_depth=len(eligible),
                top_player_minutes_share=max(p["minutes"] for p in group) / minutes
                if minutes
                else None,
                minutes_hhi=sum((p["minutes"] / minutes) ** 2 for p in group) if minutes else None,
            )
            for name, q in [
                ("median", 0.5),
                ("p25", 0.25),
                ("p75", 0.75),
                ("minimum", 0),
                ("maximum", 1),
            ]:
                item[name] = (
                    {
                        f: float(np.quantile([p["percentiles"][f] for p in eligible], q))
                        for f in CORE
                    }
                    if eligible
                    else {}
                )
            roles.append(item)
        result[tid] = roles
    return result


def build_context(root: Path) -> list[dict]:
    local = local_cohort(root)
    cohort = json.loads((local / "cohort.json").read_text())
    if not cohort["complete"]:
        raise ValueError("Club context requires the complete audited cohort")
    matches = {m["id"]: m for m in pl.read_parquet(local / "matches.parquet").to_dicts()}
    teams = {t["id"]: t["name"] for t in pl.read_parquet(local / "teams.parquet").to_dicts()}
    profiles = json.loads((local / "player_profiles.json").read_text())
    rows = []
    for i, (_, events, lineups) in enumerate(partitions(root), 1):
        rows.extend(team_observations(events.to_dicts(), matches[lineups["match_id"][0]]))
        if i % 30 == 0 or i == len(matches):
            print(f"Club context: {i}/{len(matches)}", flush=True)
    destination = root / "data/processed/phase4"
    destination.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(
        destination / "team_feature_observation.parquet", compression="zstd"
    )
    rosters = roster_context(
        pl.read_parquet(local / "player_feature_observation.parquet").to_dicts(),
        profiles,
        {p["player_id"]: p["name"] for p in profiles},
    )
    clubs = []
    for c in aggregate_team_context(rows):
        c.pop("competition_id")
        c.pop("season_id")
        clubs.append(
            ClubContext(
                **c,
                name=teams[c["club_id"]],
                competition=cohort["competition"],
                season=cohort["season"],
                source_revision=cohort["source_revision"],
                roles=rosters[c["club_id"]],
            ).model_dump()
        )
    write(root / "artifacts/phase4/club_context.json", clubs)
    return clubs
