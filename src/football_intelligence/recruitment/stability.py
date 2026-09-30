"""Assumption sensitivity and player-match bootstrap sensitivity stay separate."""

import json
from pathlib import Path

import numpy as np
import polars as pl

from football_intelligence.dna.cohort import local_cohort
from football_intelligence.dna.evaluation import bootstrap_matrices
from football_intelligence.dna.publish import write
from football_intelligence.dna.registry import CORE
from football_intelligence.dna.similarity import matrix, select
from football_intelligence.recruitment.contracts import RecruitmentBootstrap, RecruitmentScenario
from football_intelligence.recruitment.scoring import (
    active_requirements,
    filter_candidates,
    order_key,
    specification,
)


def weight_draws(feature_ids: list[str], spec: dict):
    state = spec["seed"]
    rng = spec["lcg"]
    low, high = spec["weight_range"]
    for _ in range(spec["weight_samples"]):
        result = {}
        for f in sorted(feature_ids):
            state = (rng["multiplier"] * state + rng["increment"]) % rng["modulus"]
            result[f] = low + (high - low) * state / rng["modulus"]
        yield result


def rank_summary(reference: list[str], draws: list[list[str]], top_k: int = 10) -> dict:
    if not reference:
        return dict(samples=0, mean_jaccard=None, players={})
    k = min(top_k, len(reference))
    top = set(reference[:k])
    ranks: dict[str, list[int]] = {pid: [] for pid in reference}
    overlaps = []
    for draw in draws:
        selected = set(draw[:k])
        overlaps.append(len(top & selected) / len(top | selected))
        for rank, pid in enumerate(draw, 1):
            ranks[pid].append(rank)
    return dict(
        samples=len(draws),
        mean_jaccard=float(np.mean(overlaps)),
        players={
            pid: dict(
                top_k_inclusion=float(np.mean(np.array(values) <= k)),
                rank_p10=float(np.quantile(values, 0.1)),
                rank_p90=float(np.quantile(values, 0.9)),
            )
            for pid, values in ranks.items()
        },
    )


def scenario_stability(
    players: list[dict],
    scenario: RecruitmentScenario,
    method: str = "weighted_rms",
    bootstrap: dict | None = None,
) -> dict:
    eligible, _ = filter_candidates(players, scenario)
    requirements = active_requirements(scenario)
    spec = specification()
    if not requirements or not eligible:
        return dict(weight=rank_summary([], []), profile=None)

    def order(values, factors=None):
        return sorted(
            values,
            key=lambda pid: (
                *order_key(values[pid], requirements, scenario, method, factors, spec),
                pid,
            ),
        )

    values = {p["player_id"]: p["percentiles"] for p in eligible}
    reference = order(values)
    result = dict(
        weight=rank_summary(
            reference,
            [order(values, f) for f in weight_draws([r.feature_id for r in requirements], spec)],
        ),
        profile=None,
    )
    if bootstrap is not None:
        if bootstrap["role"] != scenario.target_role or not set(values) <= set(
            bootstrap["player_ids"]
        ):
            raise ValueError("Bootstrap role/candidate mismatch")
        positions = {pid: i for i, pid in enumerate(bootstrap["player_ids"])}
        draws = []
        for sample in bootstrap["values"]:
            sample_values = {
                pid: {
                    f: sample[positions[pid]][j] / bootstrap["scale"]
                    for j, f in enumerate(bootstrap["feature_ids"])
                }
                for pid in values
            }
            draws.append(order(sample_values))
        result["profile"] = rank_summary(reference, draws)
    return result


def build_bootstraps(root: Path) -> dict:
    local = local_cohort(root)
    profiles = select(json.loads((local / "player_profiles.json").read_text()), 900)
    observations = pl.read_parquet(local / "player_feature_observation.parquet").to_dicts()
    original = matrix(profiles)
    spec = specification(root)
    by_role = {
        role: [i for i, p in enumerate(profiles) if p["primary_role"] == role]
        for role in sorted({p["primary_role"] for p in profiles})
    }
    values: dict[str, list] = {role: [] for role in by_role}
    for sample, _ in bootstrap_matrices(
        observations, profiles, spec["profile_samples"], spec["seed"]
    ):
        for role, indexes in by_role.items():
            reference = original[indexes]
            current = sample[indexes]
            percentiles = (
                100
                * (
                    (reference[None, :, :] < current[:, None, :]).sum(axis=1)
                    + 0.5 * (reference[None, :, :] == current[:, None, :]).sum(axis=1)
                )
                / len(indexes)
            )
            values[role].append(
                np.floor(percentiles * spec["profile_percentile_scale"] + 0.5).astype(int).tolist()
            )
    result = {}
    for role, indexes in by_role.items():
        result[role] = RecruitmentBootstrap(
            role=role,
            seed=spec["seed"],
            samples=spec["profile_samples"],
            scale=spec["profile_percentile_scale"],
            feature_ids=CORE,
            player_ids=[profiles[i]["player_id"] for i in indexes],
            values=values[role],
        ).model_dump()
        write(
            root / "artifacts/phase4/bootstrap" / (role.replace("/", "-") + ".json"), result[role]
        )
    return result
