"""Prediction-time covariates and frozen temporal/player-separated splits."""

import hashlib
import json
import math
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from football_intelligence.dna.cohort import write
from football_intelligence.dna.registry import VERSION


def historical_context(rows: list[dict], team_id: str, cutoff: str, days: int = 365) -> dict | None:
    first = str(date.fromisoformat(cutoff) - timedelta(days=days))
    past = [
        r
        for r in rows
        if r["team_id"] == team_id
        and first <= r["observed_on"] <= cutoff
        and r["duration_minutes"] is not None
    ]
    if len(past) < 3:
        return None
    minutes = sum(r["duration_minutes"] for r in past)
    own, opp = sum(r["possessions"] for r in past), sum(r["opponent_possessions"] for r in past)
    return dict(
        passes_per90=90 * sum(r["passes"] for r in past) / minutes,
        shots_per90=90 * sum(r["shots"] for r in past) / minutes,
        possession_sequence_share=own / (own + opp) if own + opp else None,
        matches=len(past),
        first_date=min(r["observed_on"] for r in past),
        last_date=max(r["observed_on"] for r in past),
    )


def validation_player(player_id: str) -> bool:
    return (
        int(hashlib.sha256(("phase3-seed20260930:" + player_id).encode()).hexdigest(), 16) % 5 == 0
    )


def dataset(
    root: Path, threshold: int = 600, role_policy: str = "same_or_adjacent"
) -> tuple[list[dict], dict]:
    local = root / "data/processed/phase3"
    environments = {
        e["environment_id"]: e for e in json.loads((local / "player_environment.json").read_text())
    }
    transitions = json.loads((local / "transition_episode.json").read_text())
    context = pl.read_parquet(local / "team_match_context.parquet").to_dicts()
    result = []
    rejections: Counter = Counter()
    for t in transitions:
        reasons = list(t["eligibility"][str(threshold)])
        if t["role_change"] not in (["same"] if role_policy == "same" else ["same", "adjacent"]):
            reasons.append("unsupported_role_change")
        a, b = (
            environments[t["source_environment_id"]],
            environments[t["destination_environment_id"]],
        )
        season_pair = (a["season"], b["season"])
        if season_pair not in [("2018/2019", "2019/2020"), ("2019/2020", "2020/2021")]:
            reasons.append("outside_adjacent_season_study")
        if reasons:
            rejections.update(reasons)
            continue
        source_context = historical_context(context, a["team_id"], a["end_date"])
        target_context = historical_context(context, b["team_id"], a["end_date"])
        if source_context is None or target_context is None:
            rejections["missing_prechange_team_context"] += 1
            continue
        if a["feature_version"] != VERSION or b["feature_version"] != VERSION:
            raise ValueError("Feature version mismatch")
        if a["end_date"] >= b["start_date"]:
            raise ValueError("Temporal leakage")
        split = (
            "test"
            if b["season"] == "2020/2021"
            else "validation"
            if validation_player(a["player_id"])
            else "train"
        )
        result.append(
            dict(
                **t,
                split=split,
                source=a,
                destination=b,
                source_context=source_context,
                target_context=target_context,
                context_log_ratio=math.log(
                    target_context["passes_per90"] / source_context["passes_per90"]
                ),
                context_share_change=target_context["possession_sequence_share"]
                - source_context["possession_sequence_share"],
            )
        )
    result.sort(key=lambda r: r["transition_id"])
    if len({r["transition_id"] for r in result}) != len(result):
        raise ValueError("Duplicate episode")
    if {r["player_id"] for r in result if r["split"] == "train"} & {
        r["player_id"] for r in result if r["split"] == "validation"
    }:
        raise ValueError("Player leakage across validation split")
    fit = [r for r in result if r["split"] != "test"]
    test = [r for r in result if r["split"] == "test"]
    if (
        fit
        and test
        and max(r["destination"]["end_date"] for r in fit)
        >= min(r["destination"]["start_date"] for r in test)
    ):
        raise ValueError("Destination-period leakage")
    report = dict(
        threshold=threshold,
        role_policy=role_policy,
        counts=dict(Counter(r["split"] for r in result)),
        unique_players={
            s: len({r["player_id"] for r in result if r["split"] == s})
            for s in ["train", "validation", "test"]
        },
        roles={
            s: dict(Counter(r["destination_role"] for r in result if r["split"] == s))
            for s in ["train", "validation", "test"]
        },
        teams={
            s: dict(Counter(r["destination"]["team"] for r in result if r["split"] == s))
            for s in ["train", "validation", "test"]
        },
        team_changes={
            s: sum(r["actual_team_change"] for r in result if r["split"] == s)
            for s in ["train", "validation", "test"]
        },
        rejections=dict(rejections),
        source_date_range=[
            min(r["source"]["start_date"] for r in result),
            max(r["source"]["end_date"] for r in result),
        ],
        destination_date_range={
            s: [
                min(r["destination"]["start_date"] for r in result if r["split"] == s),
                max(r["destination"]["end_date"] for r in result if r["split"] == s),
            ]
            for s in ["train", "validation", "test"]
        },
        episode_ids={
            s: [r["transition_id"] for r in result if r["split"] == s]
            for s in ["train", "validation", "test"]
        },
    )
    return result, report


def source_bootstrap(root: Path, environment: dict, target: str, samples: int = 200) -> np.ndarray:
    rows = pl.read_parquet(
        root / "data/processed/phase3/player_feature_observation.parquet"
    ).filter(
        (pl.col("player_id") == environment["player_id"])
        & (pl.col("team_id") == environment["team_id"])
        & (pl.col("observed_on") >= environment["start_date"])
        & (pl.col("observed_on") <= environment["end_date"])
        & pl.col("minutes_reliable")
        & (pl.col("minutes") > 0)
    )
    if rows.is_empty() or rows[target].null_count():
        raise ValueError("Missing source bootstrap evidence")
    rng = np.random.default_rng(
        int(hashlib.sha256((environment["environment_id"] + target).encode()).hexdigest()[:8], 16)
    )
    idx = rng.integers(0, rows.height, (samples, rows.height))
    return (
        rows[target].to_numpy()[idx].sum(axis=1) * 90 / rows["minutes"].to_numpy()[idx].sum(axis=1)
    )


def prepare(root: Path) -> dict:
    rows, report = dataset(root)
    write(root / "data/processed/phase3/model_dataset.json", rows)
    write(root / "artifacts/phase3/dataset_split.json", report)
    return report
