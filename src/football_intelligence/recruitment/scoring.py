"""Canonical deterministic requirement mismatch, with no evidence weighting."""

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import cast

from football_intelligence.dna.registry import FAMILIES
from football_intelligence.recruitment.contracts import (
    Family,
    RecruitmentExclusion,
    RecruitmentRank,
    RecruitmentResult,
    RecruitmentScenario,
)


def specification(root: Path | None = None) -> dict:
    root = root or Path(__file__).resolve().parents[3]
    return json.loads((root / "config/recruitment-scoring.json").read_text())


def mismatch(value: float, target: float, preference: str, spec: dict) -> float:
    loss = spec["loss"][preference]
    delta = value - target
    if loss == "ignore":
        return 0.0
    if loss == "shortfall":
        return max(0.0, -delta)
    if loss == "excess":
        return max(0.0, delta)
    return abs(delta)


def active_requirements(scenario: RecruitmentScenario) -> list:
    return sorted(
        [r for r in scenario.requirements if r.preference != "neutral"], key=lambda r: r.feature_id
    )


def effective_weights(
    requirements: list,
    scenario: RecruitmentScenario,
    method: str,
    factors: dict[str, float] | None = None,
) -> dict[str, float]:
    weights = {
        r.feature_id: r.weight
        * scenario.family_weights.get(cast(Family, FAMILIES[r.feature_id]), 1)
        * (factors or {}).get(r.feature_id, 1)
        for r in requirements
    }
    if method == "family_rms":
        totals: dict[str, float] = defaultdict(float)
        for r in requirements:
            totals[FAMILIES[r.feature_id]] += weights[r.feature_id]
        weights = {
            r.feature_id: weights[r.feature_id]
            / totals[FAMILIES[r.feature_id]]
            * scenario.family_weights.get(cast(Family, FAMILIES[r.feature_id]), 1)
            for r in requirements
        }
    return weights


def distance(
    values: dict[str, float],
    requirements: list,
    scenario: RecruitmentScenario,
    method: str = "weighted_rms",
    factors: dict[str, float] | None = None,
    spec: dict | None = None,
) -> tuple[float, list[dict]]:
    spec = spec or specification()
    weights = effective_weights(requirements, scenario, method, factors)
    contributions = []
    for r in requirements:
        value = values[r.feature_id]
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError("Candidate percentile outside published contract")
        loss = mismatch(value, r.value, r.preference, spec)
        contributions.append(
            dict(
                feature_id=r.feature_id,
                family=FAMILIES[r.feature_id],
                candidate=value,
                target=r.value,
                mismatch=loss,
                effective_weight=weights[r.feature_id],
                squared_contribution=weights[r.feature_id] * loss ** spec["power"],
                source=r.source,
            )
        )
    total = sum(c["squared_contribution"] for c in contributions)
    for c in contributions:
        c["share"] = c["squared_contribution"] / total if total else 0.0
    result = (total / sum(weights.values())) ** (1 / spec["power"]) if weights else 0.0
    return result, contributions


def order_key(
    values: dict[str, float],
    requirements: list,
    scenario: RecruitmentScenario,
    method: str,
    factors: dict[str, float] | None = None,
    spec: dict | None = None,
) -> tuple:
    spec = spec or specification()
    d, _ = distance(values, requirements, scenario, method, factors, spec)
    scale = 10 ** spec["ranking_round_decimals"]
    d = math.floor(d * scale + 0.5) / scale
    if method not in ("satisfaction", "hybrid"):
        return (d,)
    unmet = [
        r
        for r in requirements
        if mismatch(values[r.feature_id], r.value, r.preference, spec)
        > (spec["satisfaction_exact_tolerance"] if r.preference == "exact" else spec["epsilon"])
    ]
    if method == "hybrid":
        return (len(unmet), d)
    w = effective_weights(requirements, scenario, "weighted_rms", factors)
    return (sum(w[r.feature_id] for r in unmet) / sum(w.values()) if w else 0.0,)


def filter_candidates(
    players: list[dict], scenario: RecruitmentScenario
) -> tuple[list[dict], list[dict]]:
    eligible = []
    excluded = []
    active = active_requirements(scenario)
    spec = specification()
    for p in sorted(players, key=lambda p: p["player_id"]):
        reasons = list(p["exclusions"]) if not p["eligible"] else []
        if p["role"] != scenario.target_role:
            reasons.append("wrong_role")
        if p["minutes"] < scenario.hard_constraints.minimum_minutes:
            reasons.append("below_minutes")
        if scenario.hard_constraints.minimum_neighbor_stability > 0 and (
            p["neighbor_stability"] is None
            or p["neighbor_stability"] < scenario.hard_constraints.minimum_neighbor_stability
        ):
            reasons.append("below_evidence_threshold")
        if scenario.hard_constraints.exclude_same_club and scenario.club_id in p["team_ids"]:
            reasons.append("same_club_excluded")
        if (
            scenario.hard_constraints.candidate_team_id
            and scenario.hard_constraints.candidate_team_id not in p["team_ids"]
        ):
            reasons.append("candidate_team_filter")
        if p["player_id"] == scenario.replacement_player_id:
            reasons.append("replacement_reference")
        for r in active:
            if r.feature_id not in p["percentiles"]:
                reasons.append("missing_required_feature")
            elif (
                r.hard_constraint
                and mismatch(p["percentiles"][r.feature_id], r.value, r.preference, spec)
                > spec["epsilon"]
            ):
                reasons.append("hard_feature_constraint:" + r.feature_id)
        if reasons:
            excluded.append(dict(player_id=p["player_id"], reasons=sorted(set(reasons))))
        else:
            eligible.append(p)
    return eligible, excluded


def pareto_frontier(losses: dict[str, list[float]], epsilon: float = 1e-9) -> set[str]:
    return {
        pid
        for pid, values in losses.items()
        if not any(
            other != pid
            and all(x <= y + epsilon for x, y in zip(candidate, values, strict=True))
            and any(x < y - epsilon for x, y in zip(candidate, values, strict=True))
            for other, candidate in losses.items()
        )
    }


def rank_candidates(
    players: list[dict], scenario: RecruitmentScenario, method: str = "weighted_rms"
) -> dict:
    eligible, excluded = filter_candidates(players, scenario)
    requirements = active_requirements(scenario)
    if not requirements or not eligible:
        return RecruitmentResult(
            status="no_requirements" if not requirements else "no_candidates",
            eligible_count=len(eligible),
            active_requirements=len(requirements),
            frontier_count=0,
            rankings=[],
            exclusions=[RecruitmentExclusion.model_validate(e) for e in excluded],
        ).model_dump()
    spec = specification()
    losses = {
        p["player_id"]: [
            mismatch(p["percentiles"][r.feature_id], r.value, r.preference, spec)
            for r in requirements
        ]
        for p in eligible
    }
    frontier = pareto_frontier(losses, spec["epsilon"])
    ordered = sorted(
        eligible,
        key=lambda p: (
            *order_key(p["percentiles"], requirements, scenario, method, spec=spec),
            p["player_id"],
        ),
    )
    rankings = []
    for rank, p in enumerate(ordered, 1):
        value, contributions = distance(p["percentiles"], requirements, scenario, method, spec=spec)
        families: dict[str, float] = defaultdict(float)
        for c in contributions:
            families[c["family"]] += c["share"]
        rankings.append(
            dict(
                player_id=p["player_id"],
                rank=rank,
                distance=value,
                contributions=contributions,
                family_contributions=dict(sorted(families.items())),
                strong_matches=[
                    c["feature_id"]
                    for c in sorted(contributions, key=lambda c: (c["mismatch"], c["feature_id"]))[
                        :3
                    ]
                ],
                main_mismatches=[
                    c["feature_id"]
                    for c in sorted(
                        contributions, key=lambda c: (-c["squared_contribution"], c["feature_id"])
                    )
                    if c["mismatch"] > spec["epsilon"]
                ][:3],
                frontier=p["player_id"] in frontier,
            )
        )
    return RecruitmentResult(
        status="ok",
        eligible_count=len(eligible),
        active_requirements=len(requirements),
        frontier_count=len(frontier),
        rankings=[RecruitmentRank.model_validate(r) for r in rankings],
        exclusions=[RecruitmentExclusion.model_validate(e) for e in excluded],
    ).model_dump()


def validate_scenario(index: dict, scenario: RecruitmentScenario) -> None:
    club_ids = {c["club_id"] for c in index["clubs"]}
    if scenario.club_id not in club_ids or (
        scenario.hard_constraints.candidate_team_id
        and scenario.hard_constraints.candidate_team_id not in club_ids
    ):
        raise ValueError("Unknown club")
    if scenario.replacement_player_id:
        p = next(
            (p for p in index["players"] if p["player_id"] == scenario.replacement_player_id), None
        )
        if (
            p is None
            or not p["eligible"]
            or scenario.club_id not in p["team_ids"]
            or p["role"] != scenario.target_role
        ):
            raise ValueError(
                "Replacement player must have an eligible profile at the selected club/role"
            )
