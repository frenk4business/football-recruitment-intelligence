"""Publish derived research aggregates, never StatsBomb source event records."""

import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from football_intelligence.contracts import (
    METRICS,
    CompetitionSummary,
    Coverage,
    CoverageRow,
    EventCount,
    Explorer,
    MatchSummary,
    PlayerSummary,
    Source,
    SpatialBin,
    TrackingPoint,
    TrackingSnapshot,
)
from football_intelligence.data.fetch import digest, read_config
from football_intelligence.data.schema import SCHEMA_VERSION


def sources(root: Path) -> list[Source]:
    cfg = read_config(root)
    return [
        Source(
            id="statsbomb",
            name="StatsBomb Open Data",
            url="https://github.com/hudl/open-data",
            license="StatsBomb Public Data User Agreement",
            license_url="https://github.com/hudl/open-data/blob/master/LICENSE.pdf",
            attribution="Data: StatsBomb. Independent, non-commercial research; no endorsement.",
            limitation_en="One 2022 World Cup match. Event data only; no continuous tracking. Public output contains derived analysis.",
            limitation_nl="Eén WK-wedstrijd uit 2022. Alleen events; geen doorlopende tracking. Publieke uitvoer bevat afgeleide analyses.",
            revision=cfg["statsbomb"]["revision"],
        ),
        Source(
            id="skillcorner",
            name="SkillCorner Open Data",
            url="https://github.com/SkillCorner/opendata",
            license="MIT",
            license_url="https://github.com/SkillCorner/opendata/blob/master/LICENSE",
            attribution="Copyright (c) 2020 Skillcorner. Source: SkillCorner / PySport.",
            limitation_en="60 seconds of broadcast tracking at 1 Hz. Includes extrapolated positions. Full-match minutes come from separate metadata.",
            limitation_nl="60 seconden broadcasttracking op 1 Hz, inclusief geëxtrapoleerde posities. Wedstrijdminuten komen uit aparte metadata.",
            revision=cfg["skillcorner"]["revision"],
        ),
    ]


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def export(
    root: Path,
    tables: dict[str, pl.DataFrame],
    marts: dict[str, pl.DataFrame],
    validation: dict,
    manifests: list[dict],
) -> dict:
    out = root / "artifacts"
    source_models = sources(root)
    coverage_rows = []
    for source in source_models:
        provider = source.id
        sub = {name: df.filter(pl.col("provider") == provider) for name, df in tables.items()}
        dates = sub["matches"]["observed_on"].sort()
        events_available = provider == "statsbomb"
        tracking_available = provider == "skillcorner"
        coverage_rows.append(
            CoverageRow(
                provider=provider,
                **{
                    k: sub[k].height
                    for k in ["competitions", "seasons", "matches", "teams", "players"]
                },
                events=sub["events"].height if events_available else None,
                tracking_frames=sub["tracking_frames"].height if tracking_available else None,
                tracking_objects=sub["tracking_objects"].height if tracking_available else None,
                date_start=str(dates[0]),
                date_end=str(dates[-1]),
                missing_player_events=sub["events"]["player_id"].null_count()
                if events_available
                else None,
                undetected_objects=sub["tracking_objects"].filter(~pl.col("is_detected")).height
                if tracking_available
                else None,
                available_metrics=[m.id for m in METRICS if provider in m.providers],
            )
        )
    coverage = Coverage(
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        providers=coverage_rows,
        validation_status=validation["status"],
        warnings=validation["warnings"],
    )
    names = {
        row["id"]: row["name"]
        for name in ["competitions", "seasons", "teams", "players"]
        for row in tables[name].to_dicts()
    }
    matches = []
    competitions = []
    for row in tables["matches"].sort("provider").to_dicts():
        match = MatchSummary(
            id=row["id"],
            provider=row["provider"],
            competition=names[row["competition_id"]],
            season=names[row["season_id"]],
            date=str(row["observed_on"]),
            home=names[row["home_team_id"]],
            away=names[row["away_team_id"]],
            score=f"{row['home_score']}–{row['away_score']}",
            coverage=row["coverage"],
        )
        matches.append(match)
        competitions.append(
            CompetitionSummary(
                id=row["competition_id"],
                provider=row["provider"],
                name=match.competition,
                season=match.season,
            )
        )
        players = [
            PlayerSummary(
                id=p["player_id"],
                match_id=p["match_id"],
                provider=p["provider"],
                name=p["player_name"],
                team=p["team_name"],
                position=p["position"],
                minutes=p["minutes"],
                minutes_method=p["minutes_method"],
                shots=p["shots"],
                passes=p["passes"],
                xg=p["xg"],
                shots_per90=p["shots_per90"],
                pass_completion=p["pass_completion"],
            )
            for p in marts["player_match"].filter(pl.col("match_id") == row["id"]).to_dicts()
        ]
        ev = tables["events"].filter((pl.col("match_id") == row["id"]) & (pl.col("period") < 5))
        counts = [
            EventCount(event_type=e["event_type"], count=e["len"])
            for e in ev.group_by("event_type").len().sort("len", descending=True).to_dicts()
        ]
        # 12 x 8 broad bins aggregate all in-pitch actions; cannot reconstruct event feeds.
        located = ev.filter(pl.col("x").is_between(0, 105) & pl.col("y").is_between(0, 68))
        bins_df = (
            located.with_columns(
                (pl.col("x") / 8.75).floor().clip(0, 11).alias("bx"),
                (pl.col("y") / 8.5).floor().clip(0, 7).alias("by"),
            )
            .group_by("bx", "by")
            .len()
            .sort("bx", "by")
        )
        bins = [
            SpatialBin(x=(b["bx"] + 0.5) * 8.75, y=(b["by"] + 0.5) * 8.5, count=b["len"])
            for b in bins_df.to_dicts()
        ]
        snapshots = []
        for frame in (
            tables["tracking_frames"]
            .filter(pl.col("match_id") == row["id"])
            .sort("frame")
            .to_dicts()
        ):
            points = [
                TrackingPoint(
                    x=o["x"],
                    y=o["y"],
                    name=names.get(o["player_id"], "Ball"),
                    team=names.get(o["team_id"]),
                    object_type=o["object_type"],
                    is_detected=o["is_detected"],
                )
                for o in tables["tracking_objects"]
                .filter(pl.col("frame_id") == frame["id"])
                .to_dicts()
            ]
            snapshots.append(
                TrackingSnapshot(
                    frame=frame["frame"],
                    period=frame["period"],
                    timestamp_seconds=frame["timestamp_seconds"],
                    points=points,
                )
            )
        explorer = Explorer(
            schema_version=SCHEMA_VERSION,
            match=match,
            players=players,
            event_counts=counts,
            spatial_bins=bins,
            spatial_sample_size=located.height,
            tracking_snapshots=snapshots,
        )
        write_json(out / "explorer" / f"{match.id}.json", explorer.model_dump())
    write_json(out / "data_coverage.json", coverage.model_dump())
    write_json(out / "sources.json", [s.model_dump() for s in source_models])
    write_json(out / "matches.json", [m.model_dump() for m in matches])
    write_json(out / "competitions.json", [c.model_dump() for c in competitions])
    write_json(out / "metrics.json", [m.model_dump() for m in METRICS])
    write_json(out / "validation.json", validation)
    manifest = dict(
        schema_version=SCHEMA_VERSION,
        pipeline_version="0.1.0",
        generated_at=coverage.generated_at,
        sources=manifests,
        row_counts={
            **{k: v.height for k, v in tables.items()},
            **{k: v.height for k, v in marts.items()},
        },
        parquet_sha256={
            p.name: digest(p.read_bytes())
            for p in sorted((root / "data/processed").glob("*.parquet"))
        },
        lineage={
            "canonical": "source revisions + input checksums → typed canonical tables → Parquet",
            "mart": "lineups + events + matches + players + teams → player_match → player_season / team_season",
            "public": "canonical + marts → Pydantic contracts → aggregate JSON → API / static site",
        },
    )
    write_json(out / "manifest.json", manifest)
    return manifest
