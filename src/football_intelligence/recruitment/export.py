"""Strict aggregate publication and Python reference fixtures for the browser."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from football_intelligence.dna.cohort import build_cohort, local_cohort
from football_intelligence.dna.cohort import write as write_report
from football_intelligence.dna.features import build_features
from football_intelligence.dna.publish import write
from football_intelligence.recruitment.context import build_context
from football_intelligence.recruitment.contracts import (
    ClubContext,
    RecruitmentBootstrap,
    RecruitmentEvaluation,
    RecruitmentIndex,
    RecruitmentScenario,
)
from football_intelligence.recruitment.data import (
    build_index,
    replacement_requirements,
    research_requirements,
)
from football_intelligence.recruitment.evaluation import scenario
from football_intelligence.recruitment.scoring import rank_candidates, specification
from football_intelligence.recruitment.stability import build_bootstraps, scenario_stability


def publish(root: Path) -> dict:
    base = root / "artifacts/phase4"
    decision = json.loads((base / "method_selection.json").read_text())
    if (
        hashlib.sha256((base / "development_evaluation.json").read_bytes()).hexdigest()
        != decision["development_sha256"]
    ):
        raise ValueError("Development selection evidence has changed")
    if (
        hashlib.sha256((root / "docs/phase-4-experiment-plan.md").read_bytes()).hexdigest()
        != decision["experiment_sha256"]
    ):
        raise ValueError("Registered experiment has changed")
    index = RecruitmentIndex.model_validate(json.loads((base / "candidate_index.json").read_text()))
    if index.method != decision["selected_method"]:
        raise ValueError("Public method differs from frozen selection")
    stage = root / "data/interim/recruitment-public"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    write(stage / "index.json", index.model_dump())
    for c in json.loads((base / "club_context.json").read_text()):
        club = ClubContext.model_validate(c)
        if club.club_id not in {c.club_id for c in index.clubs}:
            raise ValueError("Unknown club publication")
        write(stage / "clubs" / (club.club_id + ".json"), club.model_dump())
    for role in index.roles:
        filename = role.replace("/", "-") + ".json"
        bootstrap = RecruitmentBootstrap.model_validate(
            json.loads((base / "bootstrap" / filename).read_text())
        )
        if not set(bootstrap.player_ids) <= {
            p.player_id for p in index.players if p.eligible and p.role == role
        }:
            raise ValueError("Bootstrap publication outside eligible cohort")
        write(stage / "bootstrap" / filename, bootstrap.model_dump())
    rows = []
    for phase in ["development", "final"]:
        result = json.loads((base / (phase + "_evaluation.json")).read_text())
        tasks = {task: result[task]["metrics"] for task in ["temporal", "roster"]}
        tasks["context_ablation"] = result["temporal"]["context_ablation"]["metrics"]
        for task, methods in tasks.items():
            for method, m in methods.items():
                rows.append(
                    dict(
                        stage=phase,
                        task=task,
                        method=method,
                        queries=m["queries"],
                        recall5=m["recall5"],
                        recall10=m["recall10"],
                        mrr=m["mrr"],
                        random_recall5=m["random"]["recall5"],
                        random_recall10=m["random"]["recall10"],
                        random_mrr=m["random"]["mrr"],
                    )
                )
    robustness = json.loads((base / "robustness.json").read_text())["summary"]
    evaluation = RecruitmentEvaluation.model_validate(
        dict(
            selected_method=decision["selected_method"],
            rows=rows,
            robustness_scenarios=robustness["scenarios"],
            weight_mean_jaccard=robustness["weight_mean_jaccard"],
            profile_mean_jaccard=robustness["profile_mean_jaccard"],
            frontier_median_size=robustness["frontier_size_quantiles"][2],
            small_pool_scenarios=robustness["small_pools"],
        )
    )
    write(stage / "evaluation.json", evaluation.model_dump())
    target = base / "public"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(stage, target)
    manifest = dict(
        version="recruitment-fit-v1",
        cohort=index.cohort,
        feature_registry=index.feature_version,
        dna_version=index.dna_version,
        requirement_schema=index.requirements_version,
        club_context_version=index.club_context_version,
        fit_algorithm=index.method,
        default_threshold=900,
        score_unit="Weighted RMS percentile-point mismatch; lower is closer; not a suitability probability",
        weights_policy="Equal explicitly selected feature weights by default; optional visible 1/2/3 feature and family importance",
        ranking_stability_settings=specification(root),
        selection=decision,
        generated_at=subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", "--", "artifacts/phase4/method_selection.json"],
            cwd=root,
            text=True,
        ).strip(),
        selection_commit=subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", "artifacts/phase4/method_selection.json"],
            cwd=root,
            text=True,
        ).strip(),
        code_sha256={
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / "src/football_intelligence/recruitment").glob("*.py"))
        },
        source_revision=json.loads((root / "artifacts/phase2/model_manifest.json").read_text())[
            "source_revision"
        ],
        public_sha256={
            str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(target.rglob("*.json"))
        },
        public_bytes=sum(p.stat().st_size for p in target.rglob("*.json")),
        eligible_players=sum(p.eligible for p in index.players),
        roster_players=len(index.players),
        clubs=len(index.clubs),
    )
    write_report(base / "recruitment_manifest.json", manifest)
    reference_fixtures(root)
    return manifest


def reference_fixtures(root: Path):
    base = root / "artifacts/phase4"
    index = json.loads((base / "candidate_index.json").read_text())
    club = next(c for c in index["clubs"] if c["name"] == "Chelsea FCW")
    cases = []
    for role in index["roles"]:
        req = research_requirements()
        sc = scenario(club["club_id"], role, req, exclude_club=True)
        cases.append((f"custom-{role}", sc))
    replacement = next(
        p
        for p in index["players"]
        if p["eligible"] and p["role"] == "FB/WB" and club["club_id"] in p["team_ids"]
    )
    cases.append(
        (
            "replacement",
            scenario(
                club["club_id"],
                "FB/WB",
                replacement_requirements(replacement),
                replacement["player_id"],
                True,
            ),
        )
    )
    adjusted = cases[-1][1].model_dump()
    adjusted["requirements"][0].update(
        preference="maximum", value=40, weight=3, source="user_defined"
    )
    adjusted["requirements"][1].update(preference="neutral")
    adjusted["family_weights"] = {"passing": 3, "carrying": 2}
    cases.append(("adjusted", RecruitmentScenario.model_validate(adjusted)))
    hard = cases[0][1].model_dump()
    hard["requirements"][0]["hard_constraint"] = True
    hard["hard_constraints"].update(minimum_minutes=1200, minimum_neighbor_stability=0.5)
    cases.append(("hard-constraints", RecruitmentScenario.model_validate(hard)))
    cases.append(("empty", scenario(club["club_id"], "CB", [])))
    output = []
    for name, sc in cases:
        boot = json.loads(
            (base / "bootstrap" / (sc.target_role.replace("/", "-") + ".json")).read_text()
        )
        output.append(
            dict(
                name=name,
                scenario=sc.model_dump(),
                result=rank_candidates(index["players"], sc, index["method"]),
                stability=scenario_stability(index["players"], sc, index["method"], boot),
            )
        )
    write(
        base / "reference_cases.json",
        dict(
            notice="Python reference fixtures; derived profiles only; not additional research outcomes",
            cases=output,
        ),
    )


def build(root: Path) -> dict:
    local = local_cohort(root)
    # A clean checkout can materialize the 132-match pinned cohort. Downloads are bounded
    # and checksum-verified by the existing cohort builder; subsequent runs use the cache.
    if not (local / "cohort.json").exists():
        build_cohort(root)
    if not (local / "player_profiles.json").exists():
        build_features(root)
    build_context(root)
    method = json.loads((root / "artifacts/phase4/method_selection.json").read_text())[
        "selected_method"
    ]
    build_index(root, method)
    build_bootstraps(root)
    # Published research results and method selection are immutable inputs to a product rebuild.
    return publish(root)
