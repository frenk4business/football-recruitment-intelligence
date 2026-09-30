"""Registered development/final query evaluations; no transfer-success labels."""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import polars as pl

from football_intelligence.dna.cohort import local_cohort, write
from football_intelligence.dna.evaluation import jaccard, retrieval_metrics, temporal_views
from football_intelligence.dna.registry import CORE, SPECS
from football_intelligence.dna.similarity import Representation, matrix, select
from football_intelligence.recruitment.context import aggregate_team_context
from football_intelligence.recruitment.contracts import RecruitmentRequirement, RecruitmentScenario
from football_intelligence.recruitment.data import replacement_requirements
from football_intelligence.recruitment.scoring import (
    distance,
    order_key,
    rank_candidates,
    specification,
)
from football_intelligence.recruitment.stability import scenario_stability

METHODS = ["weighted_rms", "family_rms", "satisfaction", "hybrid"]


def percentile_matrix(reference: np.ndarray, values: np.ndarray) -> np.ndarray:
    return (
        100
        * (
            (reference[None, :, :] < values[:, None, :]).sum(axis=1)
            + 0.5 * (reference[None, :, :] == values[:, None, :]).sum(axis=1)
        )
        / len(reference)
    )


def exact_requirements(values: dict[str, float], source="replacement_player") -> list:
    return [
        RecruitmentRequirement.model_validate(
            dict(
                requirement_id=f,
                feature_id=f,
                preference="exact",
                value=v,
                source=source,
                type="target_profile",
            )
        )
        for f, v in sorted(values.items())
    ]


def scenario(
    club_id: str, role: str, requirements: list, replacement: str | None = None, exclude_club=False
) -> RecruitmentScenario:
    return RecruitmentScenario.model_validate(
        dict(
            club_id=club_id,
            target_role=role,
            mode="replace" if replacement else "find",
            created_from="replacement" if replacement else "custom",
            requirements=[r.model_dump() for r in requirements],
            replacement_player_id=replacement,
            hard_constraints=dict(exclude_same_club=exclude_club),
        )
    )


def metric_summary(rows: list[dict]) -> dict:
    ranks = [r["rank"] for r in rows]
    ns = [r["candidates"] for r in rows]
    return {
        **retrieval_metrics(ranks),
        "mean_rank_percentile": float(
            np.mean(
                [100 * (n - r) / (n - 1) if n > 1 else 100 for r, n in zip(ranks, ns, strict=True)]
            )
        )
        if rows
        else None,
        "candidate_sizes": dict(min=min(ns), max=max(ns), median=float(np.median(ns)))
        if ns
        else None,
        "random": {
            f"recall{k}": float(np.mean([min(k, n) / n for n in ns])) if ns else None
            for k in (1, 5, 10)
        }
        | {
            "mrr": float(np.mean([sum(1 / i for i in range(1, n + 1)) / n for n in ns]))
            if ns
            else None
        },
        "roles": {
            role: retrieval_metrics([r["rank"] for r in rows if r["role"] == role])
            for role in sorted({r["role"] for r in rows})
        },
    }


def aggregate_metrics(rows: list[dict]) -> dict:
    return {
        method: metric_summary([r for r in rows if r["method"] == method])
        for method in sorted({r["method"] for r in rows})
    }


def query_club(player: dict, club_ids: list[str]) -> str | None:
    return (
        player["team_ids"][0]
        if len(player["team_ids"]) == 1 and player["team_ids"][0] in club_ids
        else None
    )


def context_without_player(
    team_rows: list[dict], observations: list[dict], pid: str, tid: str, cutoff: str | None = None
) -> dict[str, float]:
    counts = [k for k, *_ in SPECS] + ["npxg", "xa", "goals", "completed_passes"]
    own = {r["match_id"]: r for r in observations if r["player_id"] == pid and r["team_id"] == tid}
    adjusted = []
    for row in team_rows:
        if cutoff is not None and row["observed_on"] >= cutoff:
            continue
        r = dict(row)
        if r["team_id"] == tid and r["match_id"] in own:
            player = own[r["match_id"]]
            for key in counts:
                if r[key] is not None and player[key] is not None:
                    r[key] = max(0, r[key] - player[key])
                elif player[key] is None:
                    r[key] = None
        adjusted.append(r)
    context = next((c for c in aggregate_team_context(adjusted) if c["club_id"] == tid), None)
    if context is None:
        return {}
    return {
        f["feature_id"]: f["percentile"]
        for f in context["features"]
        if f["feature_id"] in CORE and f["percentile"] is not None
    }


def temporal_retrieval(
    profiles: list[dict], observations: list[dict], club_ids: list[str], team_rows: list[dict]
) -> dict:
    first, second, split = temporal_views(observations, 900)
    full = {p["player_id"]: p for p in select(profiles, 900)}
    valid = [i for i, p in enumerate(first) if p["player_id"] in full]
    first, second = [first[i] for i in valid], [second[i] for i in valid]
    rows = []
    ablations = []
    spec = specification()
    for role in sorted({p["primary_role"] for p in first}):
        indexes = [i for i, p in enumerate(first) if p["primary_role"] == role]
        if len(indexes) < 3:
            continue
        a, b = matrix([first[i] for i in indexes]), matrix([second[i] for i in indexes])
        model = Representation(scaling="standard").fit(a)
        dna = model.distances(a, a)
        labels = model.distances(b, b)
        pcts = percentile_matrix(a, a)
        values = [dict(zip(CORE, row, strict=True)) for row in pcts]
        ids = [first[i]["player_id"] for i in indexes]
        for i, pid in enumerate(ids):
            club = query_club(full[pid], club_ids)
            if not club:
                continue
            others = [j for j in range(len(ids)) if j != i]
            gold = min(others, key=lambda j: (labels[i, j], ids[j]))
            req = exact_requirements(values[i])
            sc = scenario(club, role, req, pid)
            for method in ["dna_nearest_neighbor", *METHODS]:
                order = (
                    sorted(others, key=lambda j: (dna[i, j], ids[j]))
                    if method == "dna_nearest_neighbor"
                    else sorted(
                        others,
                        key=lambda j: (*order_key(values[j], req, sc, method, spec=spec), ids[j]),
                    )
                )
                rows.append(
                    dict(
                        player_id=pid,
                        club_id=club,
                        role=role,
                        method=method,
                        candidates=len(others),
                        rank=order.index(gold) + 1,
                        gold_peer_id=ids[gold],
                    )
                )
            mates = [j for j in others if full[ids[j]]["team_ids"] == [club]]
            if len(mates) >= 2:
                role_target = dict(zip(CORE, np.median(pcts[mates], axis=0), strict=True))
                role_req = exact_requirements(role_target, "derived_roster_gap")
                context = context_without_player(
                    team_rows, observations, pid, club, split["cutoff"]
                )
                if not context:
                    continue
                context_req = exact_requirements(context, "observed_club_context")
                scores = {
                    j: (
                        distance(values[j], req, sc, spec=spec)[0] ** 2,
                        distance(values[j], role_req, sc, spec=spec)[0] ** 2,
                        distance(values[j], context_req, sc, spec=spec)[0] ** 2,
                    )
                    for j in others
                }
                for name, weights in [
                    ("requirements_only", (1, 0, 0)),
                    ("plus_role_median", (0.75, 0.25, 0)),
                    ("plus_full_context", (0.5, 0.25, 0.25)),
                ]:
                    order = sorted(
                        others,
                        key=lambda j: (
                            sum(x * w for x, w in zip(scores[j], weights, strict=True)),
                            ids[j],
                        ),
                    )
                    ablations.append(
                        dict(
                            player_id=pid,
                            club_id=club,
                            role=role,
                            method=name,
                            candidates=len(others),
                            rank=order.index(gold) + 1,
                        )
                    )
    return dict(
        split=split,
        metrics=aggregate_metrics(rows),
        queries=rows,
        context_ablation=dict(metrics=aggregate_metrics(ablations), queries=ablations),
    )


def roster_holdout(
    profiles: list[dict], observations: list[dict], club_ids: list[str], team_rows: list[dict]
) -> dict:
    selected = select(profiles, 900)
    rows = []
    spec = specification()
    for query in selected:
        club = query_club(query, club_ids)
        if not club:
            continue
        role = query["primary_role"]
        group = [p for p in selected if p["primary_role"] == role]
        mates = [
            p for p in group if p["team_ids"] == [club] and p["player_id"] != query["player_id"]
        ]
        if len(mates) < 2:
            continue
        ids = [p["player_id"] for p in group]
        held = ids.index(query["player_id"])
        raw = matrix(group)
        reference = np.delete(raw, held, axis=0)
        transformed = percentile_matrix(reference, raw)
        values = [dict(zip(CORE, row, strict=True)) for row in transformed]
        mate_indexes = [ids.index(p["player_id"]) for p in mates]
        target = dict(zip(CORE, np.median(transformed[mate_indexes], axis=0), strict=True))
        chosen = {
            f: target[f]
            for f in ("progressive_passes_per90", "progressive_carries_per90", "pressures_per90")
        }
        req = exact_requirements(chosen, "derived_roster_gap")
        role_req = exact_requirements(target, "derived_roster_gap")
        sc = scenario(club, role, req)
        context = context_without_player(team_rows, observations, query["player_id"], club)
        context_req = exact_requirements(context, "observed_club_context")
        model = Representation(scaling="standard").fit(reference)
        dna = model.distances(np.median(raw[mate_indexes], axis=0)[None, :], raw)[0]
        candidates = [j for j in range(len(ids)) if j not in mate_indexes]
        scores = {
            j: (
                distance(values[j], req, sc, spec=spec)[0] ** 2,
                distance(values[j], role_req, sc, spec=spec)[0] ** 2,
                distance(values[j], context_req, sc, spec=spec)[0] ** 2,
            )
            for j in candidates
        }
        for method in ["dna_nearest_neighbor", *METHODS, "plus_role_median", "plus_full_context"]:
            if method == "dna_nearest_neighbor":
                order = sorted(candidates, key=lambda j: (dna[j], ids[j]))
            elif method in ("plus_role_median", "plus_full_context"):
                weights = (0.75, 0.25, 0) if method == "plus_role_median" else (0.5, 0.25, 0.25)
                order = sorted(
                    candidates,
                    key=lambda j: (
                        sum(x * w for x, w in zip(scores[j], weights, strict=True)),
                        ids[j],
                    ),
                )
            else:
                order = sorted(
                    candidates,
                    key=lambda j: (*order_key(values[j], req, sc, method, spec=spec), ids[j]),
                )
            rows.append(
                dict(
                    player_id=query["player_id"],
                    club_id=club,
                    role=role,
                    method=method,
                    candidates=len(candidates),
                    rank=order.index(held) + 1,
                    reference_players=len(mates),
                    target_requirement=chosen,
                )
            )
    return dict(metrics=aggregate_metrics(rows), queries=rows)


def reconstruction(index: dict, club_ids: list[str]) -> dict:
    rows = []
    spec = specification()
    for query in index["players"]:
        club = query_club(query, club_ids)
        if not query["eligible"] or not club:
            continue
        req = replacement_requirements(query)
        sc = scenario(club, query["role"], req, query["player_id"])
        others = [
            p
            for p in index["players"]
            if p["eligible"] and p["role"] == query["role"] and p["player_id"] != query["player_id"]
        ]
        # Existing Phase 2 neighbours supply a descriptive representation reference.
        for method in METHODS:
            baseline = rank_candidates(index["players"], sc, method)
            stability = scenario_stability(index["players"], sc, method)
            rows.append(
                dict(
                    player_id=query["player_id"],
                    club_id=club,
                    role=query["role"],
                    method=method,
                    candidates=len(others),
                    neighbor_ids=[r["player_id"] for r in baseline["rankings"][: spec["top_k"]]],
                    weight_jaccard=stability["weight"]["mean_jaccard"],
                )
            )
    return dict(queries=rows)


def evaluate(root: Path, stage: str, *, persist: bool = True) -> dict:
    if stage not in ("development", "final"):
        raise ValueError("Evaluation stage must be development or final")
    plan = root / "docs/phase-4-experiment-plan.md"
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(plan.relative_to(root))],
        cwd=root,
        check=True,
        capture_output=True,
    )
    committed_plan = subprocess.check_output(
        ["git", "show", "HEAD:docs/phase-4-experiment-plan.md"], cwd=root
    )
    if plan.read_bytes() != committed_plan:
        raise ValueError("Experiment plan must be committed before evaluation")
    if stage == "final":
        selection = root / "artifacts/phase4/method_selection.json"
        committed = subprocess.check_output(
            ["git", "show", "HEAD:artifacts/phase4/method_selection.json"], cwd=root
        )
        if selection.read_bytes() != committed:
            raise ValueError("Final evaluation requires an unchanged committed method selection")
        decision = json.loads(committed)
        if hashlib.sha256(plan.read_bytes()).hexdigest() != decision["experiment_sha256"]:
            raise ValueError("Experiment plan changed after method selection")
        if (
            hashlib.sha256(
                (root / "artifacts/phase4/development_evaluation.json").read_bytes()
            ).hexdigest()
            != decision["development_sha256"]
        ):
            raise ValueError("Development evidence changed after method selection")
    local = local_cohort(root)
    profiles = json.loads((local / "player_profiles.json").read_text())
    observations = pl.read_parquet(local / "player_feature_observation.parquet").to_dicts()
    team_rows = pl.read_parquet(
        root / "data/processed/phase4/team_feature_observation.parquet"
    ).to_dicts()
    index = json.loads((root / "artifacts/phase4/candidate_index.json").read_text())
    split = json.loads((root / "artifacts/phase4/evaluation_split.json").read_text())
    clubs = split[stage + "_clubs"]
    print(f"Phase 4 {stage}: temporal known-peer retrieval", flush=True)
    temporal = temporal_retrieval(profiles, observations, clubs, team_rows)
    print(f"Phase 4 {stage}: roster holdout", flush=True)
    roster = roster_holdout(profiles, observations, clubs, team_rows)
    print(f"Phase 4 {stage}: replacement/weight sensitivity", flush=True)
    reconstruct = reconstruction(index, clubs)
    for row in reconstruct["queries"]:
        dna = json.loads(
            (root / "artifacts/phase2/public/900" / (row["player_id"] + ".json")).read_text()
        )
        row["dna_neighbor_jaccard"] = jaccard(
            row["neighbor_ids"], [p["player_id"] for p in dna["neighbors"]]
        )
    reconstruct["metrics"] = {
        method: dict(
            queries=sum(r["method"] == method for r in reconstruct["queries"]),
            mean_weight_jaccard=float(
                np.mean(
                    [r["weight_jaccard"] for r in reconstruct["queries"] if r["method"] == method]
                )
            ),
            mean_dna_neighbor_jaccard=float(
                np.mean(
                    [
                        r["dna_neighbor_jaccard"]
                        for r in reconstruct["queries"]
                        if r["method"] == method
                    ]
                )
            ),
        )
        for method in METHODS
    }
    result = dict(
        stage=stage,
        version="recruitment-fit-evaluation-v1",
        seed=specification()["seed"],
        code_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        experiment_sha256=hashlib.sha256(plan.read_bytes()).hexdigest(),
        split=split,
        temporal=temporal,
        roster=roster,
        reconstruction=reconstruct,
    )
    if persist:
        write(root / f"artifacts/phase4/{stage}_evaluation.json", result)
    return result


def select_method(root: Path) -> dict:
    development = json.loads((root / "artifacts/phase4/development_evaluation.json").read_text())
    checks = []
    for method in ("weighted_rms", "family_rms"):
        temporal = development["temporal"]["metrics"][method]
        stability = development["reconstruction"]["metrics"][method]
        checks.append(
            dict(
                method=method,
                mrr=temporal["mrr"],
                random_mrr=temporal["random"]["mrr"],
                weight_jaccard=stability["mean_weight_jaccard"],
                eligible=temporal["mrr"] > temporal["random"]["mrr"]
                and stability["mean_weight_jaccard"] >= 0.65,
            )
        )
    selected = next((r["method"] for r in checks if r["eligible"]), None)
    if selected is None:
        raise ValueError("No registered public method passed the development gate")
    result = dict(
        version="recruitment-fit-v1",
        selected_method=selected,
        checks=checks,
        context_in_ranking="Only explicit user-adopted requirements; no hidden context blend",
        selection_policy="Continuous severity + correct constraints + transparency, then development retrieval above random and weight Jaccard >=0.65; prefer equal explicit feature weights",
        development_sha256=hashlib.sha256(
            (root / "artifacts/phase4/development_evaluation.json").read_bytes()
        ).hexdigest(),
        experiment_sha256=development["experiment_sha256"],
        code_commit=development["code_commit"],
        final_queries_opened=False,
    )
    write(root / "artifacts/phase4/method_selection.json", result)
    return result
