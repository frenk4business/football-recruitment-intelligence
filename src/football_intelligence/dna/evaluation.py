"""Temporal retrieval, match bootstrap, threshold sensitivity and ablation."""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from football_intelligence.dna.cohort import COHORT, local_cohort, settings, write
from football_intelligence.dna.features import aggregate, eligibility
from football_intelligence.dna.registry import CORE, FAMILIES
from football_intelligence.dna.similarity import Representation, matrix, select, topk

METHODS: dict[str, dict] = {
    "euclidean": dict(method="euclidean"),
    "cosine": dict(method="cosine"),
    "pca": dict(method="pca"),
    "global_scaling": dict(method="euclidean"),
    "naive_features": dict(method="euclidean", balanced=False),
    "standard_scaling": dict(method="euclidean", scaling="standard"),
    "winsor_scaling": dict(method="euclidean", scaling="winsor"),
    "possession_context": dict(method="euclidean"),
    **{
        "without_" + family: dict(
            method="euclidean", features=[f for f in CORE if FAMILIES[f] != family]
        )
        for family in sorted(set(FAMILIES.values()))
    },
}


def retrieval_metrics(ranks: list[int]) -> dict:
    return dict(
        queries=len(ranks),
        recall1=float(np.mean(np.array(ranks) <= 1)) if ranks else None,
        recall5=float(np.mean(np.array(ranks) <= 5)) if ranks else None,
        recall10=float(np.mean(np.array(ranks) <= 10)) if ranks else None,
        mrr=float(np.mean(1 / np.array(ranks))) if ranks else None,
    )


def jaccard(a, b) -> float:
    x, y = set(a), set(b)
    return len(x & y) / len(x | y) if x | y else 1.0


def temporal_views(observations: list[dict], threshold: int) -> tuple[list[dict], list[dict], dict]:
    dates = sorted(r["observed_on"] for r in {r["match_id"]: r for r in observations}.values())
    cutoff = dates[len(dates) // 2]
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in observations:
        groups[r["player_id"]].append(r)
    first = []
    second = []
    exclusions: dict[str, int] = defaultdict(int)
    for _pid, rows in sorted(groups.items()):
        a = [r for r in rows if r["observed_on"] < cutoff]
        b = [r for r in rows if r["observed_on"] >= cutoff]
        if not a or not b:
            exclusions["absent_window"] += 1
            continue
        pa, pb = aggregate(a), aggregate(b)
        if eligibility(pa, threshold / 2) or eligibility(pb, threshold / 2):
            exclusions["window_eligibility"] += 1
            continue
        if pa["primary_role"] != pb["primary_role"]:
            exclusions["role_change"] += 1
            continue
        first.append(pa)
        second.append(pb)
    return (
        first,
        second,
        dict(
            cutoff=cutoff,
            first_match_ids=sorted(
                {r["match_id"] for r in observations if r["observed_on"] < cutoff}
            ),
            second_match_ids=sorted(
                {r["match_id"] for r in observations if r["observed_on"] >= cutoff}
            ),
            exclusions=dict(exclusions),
            minimum_window_minutes=threshold / 2,
        ),
    )


def retrieval(observations: list[dict], threshold: int, method: str) -> dict:
    first, second, split = temporal_views(observations, threshold)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in observations:
        grouped[row["player_id"]].append(row)
    eligible_ids = {
        p["player_id"] for p in select([aggregate(v) for v in grouped.values()], threshold)
    }
    valid = [i for i, p in enumerate(first) if p["player_id"] in eligible_ids]
    split["exclusions"]["full_season_or_sparse_role"] = len(first) - len(valid)
    first, second = [first[i] for i in valid], [second[i] for i in valid]
    params = METHODS[method]
    features = params.get("features", CORE)
    context = method == "possession_context"
    all_first = matrix(first, features, context)
    ranks = []
    roles = {}
    random_ranks = []
    for role in sorted({p["primary_role"] for p in first}):
        indexes = [i for i, p in enumerate(first) if p["primary_role"] == role]
        if len(indexes) < 3:
            continue
        a = all_first[indexes]
        b = matrix([second[i] for i in indexes], features, context)
        model = Representation(**params).fit(all_first if method == "global_scaling" else a)
        distances = model.distances(a, b)
        ids = [first[i]["player_id"] for i in indexes]
        order = topk(distances, ids, k=len(ids), exclude_self=False)
        role_ranks = [row.index(i) + 1 for i, row in enumerate(order)]
        ranks.extend(role_ranks)
        random_ranks.extend([len(ids)] * len(ids))
        roles[role] = {**retrieval_metrics(role_ranks), "candidates": len(ids)}
    return {
        **retrieval_metrics(ranks),
        "roles": roles,
        "split": split,
        "random_expectation": dict(
            recall1=float(np.mean([1 / n for n in random_ranks])),
            recall5=float(np.mean([min(5, n) / n for n in random_ranks])),
            recall10=float(np.mean([min(10, n) / n for n in random_ranks])),
            mrr=float(np.mean([sum(1 / k for k in range(1, n + 1)) / n for n in random_ranks])),
        ),
    }


def bootstrap_matrices(observations: list[dict], profiles: list[dict], samples: int, seed: int):
    """Resample whole player-match count/denominator rows, never individual events."""
    rng = np.random.default_rng(seed)
    counts = [f.removesuffix("_per90") for f in CORE]
    groups = {
        p["player_id"]: [
            r
            for r in observations
            if r["player_id"] == p["player_id"]
            and r["minutes_reliable"]
            and r["minutes"]
            and r["minutes"] > 0
        ]
        for p in profiles
    }
    prepared = [
        np.array(
            [
                [r[k] for k in counts]
                + [r["minutes"], r["own_possessions"], r["opponent_possessions"]]
                for r in groups[p["player_id"]]
            ],
            dtype=float,
        )
        for p in profiles
    ]
    for _ in range(samples):
        x = []
        context = []
        for values in prepared:
            totals = values[rng.integers(0, len(values), len(values))].sum(axis=0)
            rates = 90 * totals[: len(CORE)] / totals[len(CORE)]
            ctx = rates.copy()
            for key, denom in [
                ("pressures_per90", -1),
                ("interceptions_per90", -1),
                ("progressive_passes_per90", -2),
            ]:
                ctx[CORE.index(key)] = 100 * totals[CORE.index(key)] / totals[denom]
            x.append(rates)
            context.append(ctx)
        yield np.array(x), np.array(context)


def rankings(profiles: list[dict], x: np.ndarray, method: str) -> tuple[dict, list[dict]]:
    params = METHODS[method]
    features = params.get("features", CORE)
    indexes = [CORE.index(f) for f in features]
    x = x[:, indexes]
    result = {}
    fitted = []
    for role in sorted({p["primary_role"] for p in profiles}):
        group = [i for i, p in enumerate(profiles) if p["primary_role"] == role]
        values = x[group]
        model = Representation(**params).fit(x if method == "global_scaling" else values)
        ids = [profiles[i]["player_id"] for i in group]
        orders = topk(model.distances(values, values), ids)
        for i, order in enumerate(orders):
            result[ids[i]] = [ids[j] for j in order]
        fitted.append(dict(role=role, **model.metadata()))
    return result, fitted


def evaluate(root: Path, name: str = COHORT) -> dict:
    directory = local_cohort(root, name)
    eligibility_report = json.loads((root / "artifacts/phase2/cohort_eligibility.json").read_text())
    if not eligibility_report["complete"]:
        raise ValueError("Public evaluation requires a complete cohort eligibility report")
    profiles = json.loads((directory / "player_profiles.json").read_text())
    observations = pl.read_parquet(directory / "player_feature_observation.parquet").to_dicts()
    cfg = settings(root)
    results = {}
    stability_export = {}
    for threshold in cfg["thresholds"]:
        selected = select(profiles, threshold, cfg["minimum_role_players"])
        baseline = {}
        fitted = {}
        for method in METHODS:
            baseline[method], fitted[method] = rankings(
                selected, matrix(selected, context=method == "possession_context"), method
            )
        overlaps: dict[str, dict[str, list[float]]] = {m: defaultdict(list) for m in METHODS}
        inclusions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for b, (x, context) in enumerate(
            bootstrap_matrices(observations, selected, cfg["bootstrap_samples"], cfg["seed"]), 1
        ):
            for method in METHODS:
                sampled, _ = rankings(
                    selected, context if method == "possession_context" else x, method
                )
                for pid, neighbors in sampled.items():
                    overlaps[method][pid].append(jaccard(baseline[method][pid], neighbors))
                    if method == "standard_scaling":
                        for neighbor in neighbors:
                            inclusions[pid][neighbor] += 1
            if b % 25 == 0:
                print(
                    f"Evaluation {threshold} minutes: bootstrap {b}/{cfg['bootstrap_samples']}",
                    flush=True,
                )
        methods = {}
        for method in METHODS:
            per_player = {pid: float(np.mean(v)) for pid, v in overlaps[method].items()}
            methods[method] = dict(
                retrieval=retrieval(observations, threshold, method),
                bootstrap_jaccard=float(np.mean(list(per_player.values()))),
                jaccard_by_role={
                    role: float(
                        np.mean(
                            [
                                per_player[p["player_id"]]
                                for p in selected
                                if p["primary_role"] == role
                            ]
                        )
                    )
                    for role in sorted({p["primary_role"] for p in selected})
                },
                baseline_neighbor_overlap=float(
                    np.mean(
                        [
                            jaccard(baseline["euclidean"][pid], n)
                            for pid, n in baseline[method].items()
                        ]
                    )
                ),
            )
        per_player = {pid: float(np.mean(v)) for pid, v in overlaps["standard_scaling"].items()}
        correlation = float(
            spearmanr(
                [p["minutes"] for p in selected], [per_player[p["player_id"]] for p in selected]
            ).statistic
        )
        results[str(threshold)] = dict(
            eligible=len(selected),
            excluded=len(profiles) - len(selected),
            roles=eligibility_report["thresholds"][str(threshold)]["roles"],
            methods=methods,
            minutes_jaccard_spearman=correlation,
            pca=fitted["pca"],
            scalers=fitted["standard_scaling"],
        )
        stability_export[str(threshold)] = {
            pid: dict(
                jaccard=per_player[pid],
                inclusion={n: count / cfg["bootstrap_samples"] for n, count in sorted(v.items())},
            )
            for pid, v in sorted(inclusions.items())
        }
    result = dict(
        version="evaluation-v1",
        seed=cfg["seed"],
        bootstrap_samples=cfg["bootstrap_samples"],
        cohort=name,
        thresholds=results,
    )
    write(root / "artifacts/phase2/similarity_evaluation.json", result)
    write(directory / "stability.json", stability_export)
    return result
