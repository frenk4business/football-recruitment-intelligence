"""Publish finite, historical scenarios; no raw events or posterior draws leave research storage."""

import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import polars as pl

from football_intelligence.data.schema import canonical_id
from football_intelligence.dna.cohort import write
from football_intelligence.translation.baselines import Baseline, rate
from football_intelligence.translation.contracts import (
    TranslationEnvironment,
    TranslationEstimate,
    TranslationEvaluation,
    TranslationEvaluationRow,
    TranslationEvidence,
    TranslationIndex,
    TranslationMetric,
    TranslationModels,
    TranslationPlayer,
    TranslationPlayerDetail,
    TranslationPrediction,
    TranslationTarget,
)
from football_intelligence.translation.dataset import dataset, historical_context
from football_intelligence.translation.evaluation import require_committed_selection
from football_intelligence.translation.evidence import role_change
from football_intelligence.translation.materialize import settings
from football_intelligence.translation.models import fit, predict

LABELS = {
    "shots": ("Shots", "Schoten"),
    "progressive_passes": ("Progressive passes", "Progressieve passes"),
    "progressive_carries": ("Progressive carries", "Progressieve dribbels"),
    "pressures": ("Pressures", "Drukacties"),
}


def source_exclusions(e: dict, bounds: dict) -> list[str]:
    reasons = []
    if e["season"] != "2019/2020":
        reasons.append("outside_source_season")
    if e["identity_confidence"] != "provider_id_consistent_metadata":
        reasons.append("identity_quarantined")
    if e["reliable_minutes"] < 600:
        reasons.append("below_600_reliable_minutes")
    if e["role"] not in {"AM", "CB", "CM", "DM", "FB/WB", "ST", "W"}:
        reasons.append("unsupported_source_role")
    for target, (low, high) in bounds.items():
        count = e["counts"].get(target)
        if count is None or e["reliable_minutes"] <= 0:
            reasons.append("missing_source_features")
            break
        if not low <= 90 * count / e["reliable_minutes"] <= high:
            reasons.append("source_outside_development_range")
            break
    return sorted(set(reasons))


def estimate(target: str, method: str, observed: float, point: float, draws, latent=None):
    q = np.quantile(draws, [0.025, 0.1, 0.9, 0.975])
    return TranslationEstimate(
        metric=target,
        method=method,
        observed_source=round(observed, 5),
        expected_target=round(float(point), 5),
        p025=round(float(q[0]), 5),
        p10=round(float(q[1]), 5),
        p90=round(float(q[2]), 5),
        p975=round(float(q[3]), 5),
        interval_kind="posterior_predictive" if latent is not None else "empirical_predictive",
        expected_rate_p10=None if latent is None else round(float(np.quantile(latent, 0.1)), 5),
        expected_rate_p90=None if latent is None else round(float(np.quantile(latent, 0.9)), 5),
    )


def compact(path: Path, model):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json() + "\n")


def publish(root: Path) -> dict:
    cfg = settings(root)
    selection = require_committed_selection(root)
    evaluation = json.loads((root / "artifacts/phase3/translation_evaluation.json").read_text())
    if (
        evaluation["selection_hash"]
        != hashlib.sha256(json.dumps(selection, sort_keys=True).encode()).hexdigest()
    ):
        raise ValueError("Evaluation and committed method selection differ")
    rows, split = dataset(root)
    development = [r for r in rows if r["split"] != "test"]
    roles = sorted({r["destination_role"] for r in development})
    role_counts = Counter(r["destination_role"] for r in development)
    bounds = {
        t: (
            min(rate(r, "source", t) for r in development),
            max(rate(r, "source", t) for r in development),
        )
        for t in cfg["targets"]
    }
    traces, manifests, baselines = {}, {}, {}
    for target in cfg["targets"]:
        traces[target], manifests[target] = fit(root, development, target, cfg, "development")
        if not manifests[target]["diagnostics"]["passed"]:
            raise ValueError("Cannot publish a failed model fit")
        if manifests[target]["fit_hash"] != evaluation["targets"][target]["fit"]["fit_hash"]:
            raise ValueError("Evaluation and publication models differ")
        method = selection["targets"][target]["selected_method"]
        baselines[target] = (
            None
            if method == "hierarchical_nb"
            else Baseline(method, target).fit_residuals(development)
        )
    local = root / "data/processed/phase3"
    environments = json.loads((local / "player_environment.json").read_text())
    contexts = pl.read_parquet(local / "team_match_context.parquet").to_dicts()
    teams = {e["team_id"]: e["team"] for e in environments if e["season"] == "2020/2021"}
    targets = [
        dict(
            environment_id=canonical_id("statsbomb", "translation-target", f"{tid}:2020/2021"),
            team_id=tid,
            team=name,
            competition="FA Women's Super League",
            season="2020/2021",
        )
        for tid, name in sorted(teams.items(), key=lambda item: item[1])
    ]
    by_player = defaultdict(list)
    for e in environments:
        by_player[e["player_id"]].append(e)
    staging = root / "artifacts/phase3/public.tmp"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    players = []
    statuses: Counter = Counter()
    source_reasons: Counter = Counter()
    for pid, envs in sorted(by_player.items()):
        public_envs = []
        scenarios: list[tuple[int, dict]] = []
        predictions: list[dict] = []
        for e in sorted(envs, key=lambda e: (e["season"], e["team"])):
            reasons = source_exclusions(e, bounds)
            source_reasons.update(reasons)
            public_envs.append(
                TranslationEnvironment(
                    **{
                        k: e[k]
                        for k in [
                            "environment_id",
                            "team_id",
                            "team",
                            "competition",
                            "season",
                            "start_date",
                            "end_date",
                            "role",
                            "role_shares",
                            "reliable_minutes",
                            "appearances",
                        ]
                    },
                    supported=not reasons,
                    exclusions=reasons,
                    used_as_development_outcome=e["environment_id"]
                    in {r["destination_environment_id"] for r in development},
                )
            )
            if reasons:
                continue
            sc = historical_context(contexts, e["team_id"], e["end_date"])
            for target in targets:
                tc = historical_context(contexts, target["team_id"], e["end_date"])
                for role in roles:
                    change = role_change(e["role"], role)
                    direct = [
                        r
                        for r in development
                        if r["source"]["team_id"] == e["team_id"]
                        and r["destination"]["team_id"] == target["team_id"]
                        and r["destination_role"] == role
                    ]
                    team_role = [
                        r
                        for r in development
                        if r["destination"]["team_id"] == target["team_id"]
                        and r["destination_role"] == role
                    ]
                    excludes = []
                    if change not in ("same", "adjacent"):
                        excludes.append("unsupported_role_change")
                    if role_counts[role] < 5:
                        excludes.append("fewer_than_5_role_episodes")
                    if sc is None or tc is None:
                        excludes.append("missing_prechange_team_context")
                    evidence = TranslationEvidence(
                        direct_episodes=len(direct),
                        direct_players=len({r["player_id"] for r in direct}),
                        target_team_role_episodes=len(team_role),
                        role_episodes=role_counts[role],
                        development_episodes=len(development),
                        development_seasons=["2018/2019 → 2019/2020"],
                        relies_on_pooling=len(direct) < 5,
                        unseen_target_team=target["team_id"]
                        not in manifests[cfg["targets"][0]]["design"]["teams"],
                        source_context_matches=sc["matches"] if sc else 0,
                        target_context_matches=tc["matches"] if tc else 0,
                        context_latest_date=max(sc["last_date"], tc["last_date"])
                        if sc and tc
                        else None,
                    )
                    prediction = dict(
                        model_version=cfg["version"],
                        source_environment_id=e["environment_id"],
                        target_environment_id=target["environment_id"],
                        target_role=role,
                        status="out_of_scope"
                        if change not in ("same", "adjacent")
                        else "insufficient_evidence"
                        if excludes
                        else "supported",
                        exclusions=excludes,
                        prediction_minutes=cfg["public_exposure_minutes"],
                        estimates=[],
                        research_estimates=[],
                        evidence=evidence,
                    )
                    if not excludes:
                        assert sc is not None and tc is not None
                        scenarios.append(
                            (
                                len(predictions),
                                dict(
                                    player_id=pid,
                                    source_environment_id=e["environment_id"],
                                    source=e,
                                    source_minutes=e["reliable_minutes"],
                                    source_role=e["role"],
                                    destination_role=role,
                                    destination={"team_id": target["team_id"]},
                                    destination_minutes=cfg["public_exposure_minutes"],
                                    source_context=sc,
                                    target_context=tc,
                                    role_change=change,
                                    context_log_ratio=math.log(
                                        tc["passes_per90"] / sc["passes_per90"]
                                    ),
                                ),
                            )
                        )
                    predictions.append(prediction)
        if scenarios:
            scenario_rows = [r for _, r in scenarios]
            for target in cfg["targets"]:
                pred = predict(
                    traces[target],
                    manifests[target]["design"],
                    scenario_rows,
                    seed=cfg["seed"]
                    + int(hashlib.sha256((pid + target).encode()).hexdigest()[:8], 16),
                    exposure_minutes=cfg["public_exposure_minutes"],
                )
                baseline = baselines[target]
                points = baseline.predict(scenario_rows) if baseline else pred["mean"]
                draws = baseline.predictive(scenario_rows) if baseline else pred["predictive"]
                for j, (i, r) in enumerate(scenarios):
                    observed = rate(r, "source", target)
                    predictions[i]["estimates"].append(
                        estimate(
                            target,
                            selection["targets"][target]["selected_method"],
                            observed,
                            points[j],
                            draws[:, j],
                            None if baseline else pred["latent"][:, j],
                        )
                    )
                    predictions[i]["research_estimates"].append(
                        estimate(
                            target,
                            "hierarchical_nb",
                            observed,
                            pred["mean"][j],
                            pred["predictive"][:, j],
                            pred["latent"][:, j],
                        )
                    )
        player = dict(
            player_id=pid,
            name=envs[-1]["name"],
            teams=sorted({e["team"] for e in envs}),
            supported_sources=sum(e.supported for e in public_envs),
        )
        players.append(player)
        statuses.update(p["status"] for p in predictions)
        detail = TranslationPlayerDetail(
            player=TranslationPlayer(**player),
            model_version=cfg["version"],
            environments=public_envs,
            predictions=[TranslationPrediction(**p) for p in predictions],
        )
        compact(staging / "players" / f"{pid}.json", detail)
    index = TranslationIndex(
        version=cfg["version"],
        translated_profile_version="translated-profile-v1",
        feature_version=cfg["feature_version"],
        observed_dna_version=cfg["player_dna_version"],
        scope=cfg["scope"],
        source_season="2019/2020",
        target_season="2020/2021",
        minimum_minutes=600,
        prediction_minutes=cfg["public_exposure_minutes"],
        development_episodes=len(development),
        test_episodes=split["counts"]["test"],
        test_team_changes=split["team_changes"]["test"],
        players=[TranslationPlayer(**p) for p in sorted(players, key=lambda p: p["name"])],
        targets=[TranslationTarget(**t) for t in targets],
        roles=roles,
        metrics=[
            TranslationMetric(
                id=t,
                label_en=LABELS[t][0],
                label_nl=LABELS[t][1],
                selected_method=selection["targets"][t]["selected_method"],
            )
            for t in cfg["targets"]
        ],
    )
    compact(staging / "index.json", index)
    compact(
        staging / "evaluation.json",
        TranslationEvaluation(
            model_version=cfg["version"],
            train=split["counts"]["train"],
            validation=split["counts"]["validation"],
            test=split["counts"]["test"],
            test_period=split["destination_date_range"]["test"],
            test_team_changes=split["team_changes"]["test"],
            max_rhat=max(
                t["fit"]["diagnostics"]["max_rhat"] for t in evaluation["targets"].values()
            ),
            divergences=sum(
                t["fit"]["diagnostics"]["divergences"] for t in evaluation["targets"].values()
            ),
            rows=[
                TranslationEvaluationRow(
                    metric=t,
                    method=m,
                    n=v["n"],
                    mae=v["mae"],
                    rmse=v["rmse"],
                    coverage50=v["intervals"]["50"]["coverage"],
                    coverage80=v["intervals"]["80"]["coverage"],
                    coverage95=v["intervals"]["95"]["coverage"],
                    width80=v["intervals"]["80"]["mean_width"],
                    selected=m == item["selected_method"],
                )
                for t, item in evaluation["targets"].items()
                for m, v in item["results"].items()
            ],
        ),
    )
    compact(
        staging / "models.json",
        TranslationModels(
            version=cfg["version"],
            scope=cfg["scope"],
            provider="statsbomb",
            source_revision=cfg["revision"],
            feature_version=cfg["feature_version"],
            observed_dna_version=cfg["player_dna_version"],
            supported_competitions=["FA Women's Super League"],
            development_period=split["destination_date_range"]["train"],
            heldout_period=split["destination_date_range"]["test"],
            likelihood="Negative Binomial counts with minutes exposure; validated baselines are public defaults",
            primary_priors_version=cfg["priors_version"],
            selected_methods={t: v["selected_method"] for t, v in selection["targets"].items()},
            model_code_commit=next(iter(manifests.values()))["git_commit"],
        ),
    )
    destination = root / "artifacts/phase3/public"
    if destination.exists():
        shutil.rmtree(destination)
    staging.rename(destination)
    manifest = dict(
        model_version=cfg["version"],
        translated_profile_version="translated-profile-v1",
        source_feature_bounds=bounds,
        public_role_minimum=5,
        source_exclusions=dict(source_reasons),
        scenario_statuses=dict(statuses),
        players=len(players),
        players_with_supported_sources=sum(p["supported_sources"] > 0 for p in players),
        public_bytes=sum(p.stat().st_size for p in destination.rglob("*.json")),
        largest_player_bytes=max(
            p.stat().st_size for p in (destination / "players").glob("*.json")
        ),
        fitted_posterior_bytes=sum(m["posterior_bytes"] for m in manifests.values()),
        sha256={
            str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(destination.rglob("*.json"))
        },
    )
    write(root / "artifacts/phase3/publication_manifest.json", manifest)
    return manifest
