"""Registered league/role retrieval and capability gate, with analytic chance baselines."""

import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

from football_intelligence.expansion.features import FAMILIES, FEATURE_FAMILIES, KEYS
from football_intelligence.profiles.cache import checksum, write_json


def eligible(profile: dict, threshold: float) -> bool:
    return (
        profile["minutes_reliable"]
        and profile["minutes"] >= threshold
        and all(
            profile["features"][k] is not None and np.isfinite(profile["features"][k]) for k in KEYS
        )
    )


def scales(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sd = a.std(axis=0)
    family_counts = Counter(FEATURE_FAMILIES)
    weights = np.array([1 / len(FAMILIES) / family_counts[f] for f in FEATURE_FAMILIES])
    weights[sd <= 1e-10] = 0
    return np.where(sd > 1e-10, sd, 1), weights


def tie_metrics(distances: np.ndarray) -> dict:
    """Average all positions within the true counterpart's tie block."""
    rr, r5, r10 = [], [], []
    for i, row in enumerate(distances):
        tied = np.isclose(row, row[i], atol=1e-10, rtol=0)
        earlier = int(((row < row[i]) & ~tied).sum())
        count = int(tied.sum())
        rr.append(float(np.mean(1 / np.arange(earlier + 1, earlier + count + 1))))
        r5.append(min(max(5 - earlier, 0), count) / count)
        r10.append(min(max(10 - earlier, 0), count) / count)
    return {"rr": rr, "recall5": r5, "recall10": r10}


def evaluate_role(pairs: list[dict], plan: dict, seed: int) -> dict:
    n = len(pairs)
    base = {"paired_players": n, "passed": False, "reasons": []}
    if n < 2:
        return {**base, "reasons": ["insufficient_pairs"], "metrics": None, "random": None}
    a, b = [
        np.array([[p["halves"][h]["features"][k] for k in KEYS] for p in pairs]) for h in [0, 1]
    ]
    sd, weights = scales(a)
    distances = cdist(a / sd * np.sqrt(weights), b / sd * np.sqrt(weights))
    q = tie_metrics(distances)
    random = {
        "recall_at_5": min(5, n) / n,
        "recall_at_10": min(10, n) / n,
        "mrr": float(np.mean(1 / np.arange(1, n + 1))),
    }
    rng = np.random.default_rng(seed)
    rr = np.asarray(q["rr"])
    boot = rr[rng.integers(0, n, size=(plan["bootstrap_repeats"], n))].mean(axis=1)
    correlations = {}
    for i, key in enumerate(KEYS):
        correlations[key] = (
            float(spearmanr(a[:, i], b[:, i]).statistic)
            if a[:, i].std() > 1e-10 and b[:, i].std() > 1e-10
            else None
        )
    valid = [c for c in correlations.values() if c is not None and np.isfinite(c)]
    median = float(np.median(valid)) if valid else None
    top = np.argsort(distances, axis=1, kind="stable")[:, : min(10, n)]
    sensitivity = []
    for family in FAMILIES:
        for factor in [0.5, 2.0]:
            changed = weights * np.array([factor if f == family else 1 for f in FEATURE_FAMILIES])
            perturbed = cdist(a / sd * np.sqrt(changed), b / sd * np.sqrt(changed))
            other = np.argsort(perturbed, axis=1, kind="stable")[:, : min(10, n)]
            overlap = float(
                np.mean([len(set(x) & set(y)) / len(x) for x, y in zip(top, other, strict=True)])
            )
            sensitivity.append(
                {"family": family, "factor": factor, "top10_overlap": round(overlap, 6)}
            )
    metrics = {
        "recall_at_5": float(np.mean(q["recall5"])),
        "recall_at_10": float(np.mean(q["recall10"])),
        "mrr": float(rr.mean()),
        "mrr_95_interval": np.quantile(boot, [0.025, 0.975]).tolist(),
        "median_feature_spearman": median,
        "nonconstant_features": len(valid),
    }
    reasons = []
    if n < plan["minimum_role_pairs"]:
        reasons.append("fewer_than_registered_role_pairs")
    if median is None or median < plan["minimum_median_feature_spearman"]:
        reasons.append("profile_stability_below_registered_floor")
    if metrics["recall_at_5"] < plan["minimum_recall5_over_random"] * random["recall_at_5"]:
        reasons.append("recall5_below_registered_random_multiple")
    if metrics["mrr"] < plan["minimum_mrr_over_random"] * random["mrr"]:
        reasons.append("mrr_below_registered_random_multiple")
    return {
        **base,
        "metrics": metrics,
        "random": random,
        "feature_stability": correlations,
        "weight_sensitivity": sensitivity,
        "passed": not reasons,
        "reasons": reasons,
    }


def build(root: Path):
    plan = json.loads((root / "config/v12-expansion.json").read_text())
    folder = root / "data/processed/v12/wyscout"
    profiles = json.loads((folder / "profiles.json").read_text())
    splits = json.loads((folder / "splits.json").read_text())
    split_map = {p["id"]: p for p in splits}
    scopes = json.loads((root / "artifacts/v12/wyscout-ingestion.json").read_text())
    results, capabilities = [], []
    for scope_index, scope in enumerate(scopes):
        coverage_ok = (
            scope["coverage"] == "domestic_round_robin_complete"
            and scope["matches"] == scope["catalogue_matches"]
            and scope["matches"] == len(scope["teams"]) * (len(scope["teams"]) - 1)
        )
        if not coverage_ok:
            raise ValueError(f"Wyscout season coverage gate failed: {scope['scope']}")
        full = [p for p in profiles if p["scope"] == scope["scope"]]
        grid = []
        for threshold in plan["candidate_thresholds"]:
            roles = {}
            for role_index, role in enumerate(["DEF", "MID", "FWD"]):
                candidates = [p for p in full if p["role"] == role and eligible(p, threshold)]
                pairs = [
                    split_map[p["id"]]
                    for p in candidates
                    if p["id"] in split_map
                    and all(eligible(h, threshold / 2) for h in split_map[p["id"]]["halves"])
                ]
                report = evaluate_role(pairs, plan, plan["seed"] + scope_index * 100 + role_index)
                roles[role] = {"eligible_profiles": len(candidates), **report}
            grid.append({"minutes_threshold": threshold, "roles": roles})
        selected = next(
            (
                row
                for row in grid
                if sum(r["passed"] for r in row["roles"].values())
                >= plan["minimum_enabled_outfield_roles"]
            ),
            None,
        )
        enabled_roles = (
            [r for r, evidence in selected["roles"].items() if evidence["passed"]]
            if selected
            else []
        )
        threshold = selected["minutes_threshold"] if selected else None
        eligible_profiles = (
            [p for p in full if p["role"] in enabled_roles and eligible(p, threshold)]
            if threshold
            else []
        )
        # Count actual source club-seasons; club-role medians need at least two eligible members.
        club_roles = {
            tid: {
                role: sum(
                    p["role"] == role and p["team_minutes"].get(tid, 0) >= 90
                    for p in eligible_profiles
                )
                for role in enabled_roles
            }
            for tid in scope["teams"]
        }
        target_clubs = [
            tid
            for tid, roles in club_roles.items()
            if any(n >= plan["minimum_roster_players"] for n in roles.values())
        ]
        result = {
            "scope": scope["scope"],
            "competition": scope["competition"],
            "season": scope["season"],
            "feature_registry": "wyscout-recruitment-features-v1",
            "threshold_grid": grid,
            "selected_threshold": threshold,
            "enabled_roles": enabled_roles,
        }
        results.append(result)
        capabilities.append(
            {
                "provider": "wyscout",
                "scope": scope["scope"],
                "league": scope["competition"],
                "competition_id": str(scope["competition_id"]),
                "season_id": str(scope["season_id"]),
                "season": scope["season"],
                "matches": scope["matches"],
                "events": scope["processed_events"],
                "coverage_status": "complete",
                "club_seasons": len(scope["teams"]),
                "profiles": len(full),
                "eligible_profiles": len(eligible_profiles),
                "roles": enabled_roles,
                "minutes_threshold": threshold,
                "evaluation": result,
                "recruitment_enabled": bool(selected and target_clubs),
                "enabled_clubs": target_clubs,
                "club_role_counts": club_roles,
                "reason": "registered_league_role_gates_passed"
                if selected
                else "registered_gates_not_met",
                "translation_enabled": False,
            }
        )
        print(
            f"{scope['competition']}: threshold={threshold}; roles={enabled_roles}; {len(target_clubs)}/{len(club_roles)} target clubs; {len(eligible_profiles)} eligible profiles",
            flush=True,
        )
    write_json(
        root / "artifacts/v12/wyscout-evaluation.json",
        {
            "version": "recruitment-fit-wyscout-v1",
            "plan_sha256": checksum(root / "config/v12-expansion.json"),
            "registry_sha256": checksum(root / "artifacts/v12/wyscout-feature-registry.json"),
            "split_policy": "alternating chronological appearances; scale on A only; no mixed leagues",
            "results": results,
        },
    )
    # Publish explicit disabled decisions for the entire fresh StatsBomb catalogue.
    audit = json.loads((root / "artifacts/v12/source-audit.json").read_text())
    old = json.loads((root / "artifacts/v11/public/index.json").read_text())
    added = json.loads((root / "artifacts/v12/statsbomb-ingestion.json").read_text())
    profile_counts = {s["id"]: s["profiles"] for s in old["scopes"]}
    profile_counts.update({s["scope"]: s["searchable_profiles"] for s in added["scopes"]})
    legacy = json.loads((root / "artifacts/phase4/public/index.json").read_text())
    for scope in audit["statsbomb_catalogue"]:
        sid = f"statsbomb-{scope['competition_id']}-{scope['season_id']}"
        enabled = sid == "statsbomb-37-281"
        capabilities.append(
            {
                "provider": "statsbomb",
                "scope": sid,
                "league": scope["competition_name"],
                "season": scope["season_name"],
                "competition_id": str(scope["competition_id"]),
                "season_id": str(scope["season_id"]),
                "matches": scope["catalogue_matches"],
                "coverage_status": scope["coverage_status"],
                "profiles": profile_counts.get(sid, 0),
                "eligible_profiles": sum(p["eligible"] for p in legacy["players"])
                if enabled
                else 0,
                "roles": legacy["roles"] if enabled else [],
                "evaluation": {
                    "version": "recruitment-fit-v1",
                    "path": "artifacts/phase4/evaluation.json",
                }
                if enabled
                else None,
                "recruitment_enabled": enabled,
                "enabled_clubs": [p["club_id"] for p in legacy["clubs"]] if enabled else [],
                "reason": "existing_frozen_WSL_validation"
                if enabled
                else "No registered native recruitment evaluation; search/common description only where supported",
                "translation_enabled": False,
            }
        )
    write_json(
        root / "artifacts/v12/recruitment_capability.json",
        {"version": "v12-capabilities-v1", "competitions": capabilities},
    )
    return capabilities
