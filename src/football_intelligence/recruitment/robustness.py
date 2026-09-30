"""All registered custom/replacement scenarios, including poor/sparse cases."""

import json
from pathlib import Path

import numpy as np

from football_intelligence.dna.cohort import write
from football_intelligence.recruitment.data import replacement_requirements, research_requirements
from football_intelligence.recruitment.evaluation import scenario
from football_intelligence.recruitment.scoring import (
    active_requirements,
    filter_candidates,
    mismatch,
    pareto_frontier,
    rank_candidates,
    specification,
)
from football_intelligence.recruitment.stability import scenario_stability


def analyze(root: Path, *, persist: bool = True) -> dict:
    index = json.loads((root / "artifacts/phase4/candidate_index.json").read_text())
    selected = json.loads((root / "artifacts/phase4/method_selection.json").read_text())[
        "selected_method"
    ]
    bootstraps = {
        role: json.loads(
            (root / "artifacts/phase4/bootstrap" / (role.replace("/", "-") + ".json")).read_text()
        )
        for role in index["roles"]
    }
    cases = []
    for club in index["clubs"]:
        for role in index["roles"]:
            cases.append(
                (
                    "custom",
                    scenario(club["club_id"], role, research_requirements(), exclude_club=True),
                )
            )
    for p in index["players"]:
        if p["eligible"] and len(p["team_ids"]) == 1:
            cases.append(
                (
                    "replacement",
                    scenario(
                        p["team_ids"][0],
                        p["role"],
                        replacement_requirements(p),
                        p["player_id"],
                        exclude_club=True,
                    ),
                )
            )
    rows = []
    spec = specification(root)
    for i, (kind, sc) in enumerate(cases, 1):
        ranking = rank_candidates(index["players"], sc, selected)
        bootstrap = bootstraps[sc.target_role]
        stability = scenario_stability(index["players"], sc, selected, bootstrap)
        eligible, _ = filter_candidates(index["players"], sc)
        req = active_requirements(sc)
        positions = {pid: j for j, pid in enumerate(bootstrap["player_ids"])}
        inclusion = {p["player_id"]: 0 for p in eligible}
        # Frontier sensitivity is most interpretable in the three-criterion custom cases.
        if kind == "custom":
            for sample in bootstrap["values"]:
                losses = {
                    p["player_id"]: [
                        mismatch(
                            sample[positions[p["player_id"]]][
                                bootstrap["feature_ids"].index(r.feature_id)
                            ]
                            / bootstrap["scale"],
                            r.value,
                            r.preference,
                            spec,
                        )
                        for r in req
                    ]
                    for p in eligible
                }
                for pid in pareto_frontier(losses):
                    inclusion[pid] += 1
        rows.append(
            dict(
                kind=kind,
                club_id=sc.club_id,
                role=sc.target_role,
                reference=sc.replacement_player_id,
                eligible=ranking["eligible_count"],
                frontier_count=ranking["frontier_count"],
                active_criteria=len(req),
                weight=stability["weight"],
                profile=stability["profile"],
                frontier_profile_inclusion={
                    pid: n / bootstrap["samples"] for pid, n in inclusion.items()
                }
                if kind == "custom"
                else None,
            )
        )
        if i % 25 == 0 or i == len(cases):
            print(f"Recruitment robustness: {i}/{len(cases)}", flush=True)

    def summary(group):
        return dict(
            scenarios=len(group),
            small_pools=sum(r["eligible"] <= 10 for r in group),
            weight_mean_jaccard=float(np.mean([r["weight"]["mean_jaccard"] for r in group])),
            profile_mean_jaccard=float(np.mean([r["profile"]["mean_jaccard"] for r in group])),
            weight_jaccard_quantiles=np.quantile(
                [r["weight"]["mean_jaccard"] for r in group], [0, 0.1, 0.5, 0.9, 1]
            ).tolist(),
            profile_jaccard_quantiles=np.quantile(
                [r["profile"]["mean_jaccard"] for r in group], [0, 0.1, 0.5, 0.9, 1]
            ).tolist(),
            frontier_size_quantiles=np.quantile(
                [r["frontier_count"] for r in group], [0, 0.1, 0.5, 0.9, 1]
            ).tolist(),
        )

    result = dict(
        version="recruitment-robustness-v1",
        seed=spec["seed"],
        samples=spec["profile_samples"],
        summary=summary(rows),
        by_kind={
            kind: summary([r for r in rows if r["kind"] == kind])
            for kind in ["custom", "replacement"]
        },
        by_role={role: summary([r for r in rows if r["role"] == role]) for role in index["roles"]},
        larger_pools=summary([r for r in rows if r["eligible"] > 10]),
        scenarios=rows,
    )
    if persist:
        write(root / "artifacts/phase4/robustness.json", result)
    return result
