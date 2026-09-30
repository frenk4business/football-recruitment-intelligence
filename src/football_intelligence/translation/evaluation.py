"""Validation selection is frozen before the later-season test is evaluated."""

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from football_intelligence.dna.cohort import write
from football_intelligence.translation.baselines import METHODS, Baseline, rate
from football_intelligence.translation.dataset import dataset, source_bootstrap
from football_intelligence.translation.materialize import settings
from football_intelligence.translation.models import fit, log_predictive_density, predict


def metrics(actual: np.ndarray, point: np.ndarray, draws: np.ndarray) -> dict:
    if len(actual) == 0 or not np.isfinite(draws).all() or not np.isfinite(point).all():
        raise ValueError("Evaluation requires finite nonempty predictions")
    result: dict = dict(
        n=len(actual),
        mae=float(np.mean(np.abs(actual - point))),
        rmse=float(np.sqrt(np.mean((actual - point) ** 2))),
        intervals={},
    )
    for coverage in [0.5, 0.8, 0.95]:
        alpha = 1 - coverage
        lo, hi = np.quantile(draws, [alpha / 2, 1 - alpha / 2], axis=0)
        score = (
            (hi - lo)
            + 2 / alpha * np.maximum(lo - actual, 0)
            + 2 / alpha * np.maximum(actual - hi, 0)
        )
        result["intervals"][str(int(coverage * 100))] = dict(
            coverage=float(np.mean((actual >= lo) & (actual <= hi))),
            mean_width=float(np.mean(hi - lo)),
            interval_score=float(np.mean(score)),
        )
    return result


def baseline_results(train: list[dict], evaluation: list[dict], target: str) -> tuple[dict, dict]:
    actual = np.array([rate(r, "destination", target) for r in evaluation])
    models = {m: Baseline(m, target).fit_residuals(train) for m in METHODS}
    return (
        {
            m: metrics(actual, model.predict(evaluation), model.predictive(evaluation))
            for m, model in models.items()
        },
        models,
    )


def choose(results: dict, diagnostics: dict) -> tuple[str, list[str]]:
    best = min(METHODS, key=lambda m: (results[m]["mae"], METHODS.index(m)))
    bayes = results["hierarchical_nb"]
    reasons = []
    if not diagnostics["passed"]:
        reasons.append("diagnostic_gate")
    if bayes["mae"] > 1.10 * results[best]["mae"]:
        reasons.append("validation_point_error")
    if not 0.65 <= bayes["intervals"]["80"]["coverage"] <= 0.95:
        reasons.append("validation_coverage")
    if (
        bayes["intervals"]["80"]["mean_width"]
        > 1.5 * results[best]["intervals"]["80"]["mean_width"]
    ):
        reasons.append("validation_width")
    return (best if reasons else "hierarchical_nb", reasons)


def validation(root: Path) -> dict:
    cfg = settings(root)
    rows, split = dataset(root)
    train = [r for r in rows if r["split"] == "train"]
    val = [r for r in rows if r["split"] == "validation"]
    report: dict = dict(
        stage="validation_before_test",
        split=split,
        experiment_commit="bbed4d24566f0c3a12c5b1538f493ec39f268497",
        targets={},
    )
    for target in cfg["targets"]:
        results, _ = baseline_results(train, val, target)
        trace, manifest = fit(root, train, target, cfg, "validation")
        pred = predict(trace, manifest["design"], val, seed=cfg["seed"] + 17)
        actual = np.array([rate(r, "destination", target) for r in val])
        results["hierarchical_nb"] = metrics(actual, pred["mean"], pred["predictive"])
        selected, reasons = choose(results, manifest["diagnostics"])
        report["targets"][target] = dict(
            results=results, selected_method=selected, selection_reasons=reasons, fit=manifest
        )
        write(root / "artifacts/phase3/validation.json", report)
        print(
            "Validation",
            target,
            selected,
            {m: round(v["mae"], 4) for m, v in results.items()},
            flush=True,
        )
    return report


def posterior_predictive_check(trace, rows: list[dict], target: str) -> dict:
    counts = trace.posterior_predictive["count"].values.reshape((-1, len(rows)))
    observed = np.array([r["destination"]["counts"][target] for r in rows])
    exposure = np.array([r["destination_minutes"] / 90 for r in rows])

    def group(indexes):
        obs = observed[indexes] / exposure[indexes]
        draws = counts[:, indexes] / exposure[indexes]
        result = {}
        for name, fn in [
            ("mean", lambda x, axis: np.mean(x, axis=axis)),
            ("variance", lambda x, axis: np.var(x, axis=axis)),
            ("zero_fraction", lambda x, axis: np.mean(x == 0, axis=axis)),
            ("p90", lambda x, axis: np.quantile(x, 0.9, axis=axis)),
        ]:
            actual = float(fn(obs, None))
            bounds = np.quantile(fn(draws, 1), [0.05, 0.5, 0.95]).tolist()
            result[name] = dict(
                observed=actual,
                replicated_p05=bounds[0],
                replicated_p50=bounds[1],
                replicated_p95=bounds[2],
                inside90=bounds[0] <= actual <= bounds[2],
            )
        return dict(n=len(indexes), statistics=result)

    return dict(
        overall=group(list(range(len(rows)))),
        by_role={
            role: group([i for i, r in enumerate(rows) if r["destination_role"] == role])
            for role in sorted({r["destination_role"] for r in rows})
        },
        by_team={
            team: group([i for i, r in enumerate(rows) if r["destination"]["team"] == team])
            for team in sorted({r["destination"]["team"] for r in rows})
        },
    )


def require_committed_selection(root: Path) -> dict:
    relative = "artifacts/phase3/validation.json"
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative], cwd=root, check=True, capture_output=True
    )
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--", relative], cwd=root, check=True)
    value = json.loads((root / relative).read_text())
    if set(value["targets"]) != set(settings(root)["targets"]):
        raise ValueError("Incomplete validation selection")
    return value


def evaluate(root: Path, sensitivities: bool = True) -> dict:
    cfg = settings(root)
    selection = require_committed_selection(root)
    rows, split = dataset(root)
    train = [r for r in rows if r["split"] != "test"]
    test = [r for r in rows if r["split"] == "test"]
    report: dict = dict(
        model_version=cfg["version"],
        scope=cfg["scope"],
        split=split,
        targets={},
        sensitivities={},
        selection_hash=hashlib.sha256(json.dumps(selection, sort_keys=True).encode()).hexdigest(),
        shared_historical_players=len(
            {r["player_id"] for r in train} & {r["player_id"] for r in test}
        ),
        competition_pair_sensitivity="Not identifiable: removing WSL→WSL leaves zero episodes.",
    )
    prediction_rows = []
    for target in cfg["targets"]:
        results, baselines = baseline_results(train, test, target)
        trace, manifest = fit(root, train, target, cfg, "development")
        if not manifest["diagnostics"]["passed"]:
            raise ValueError(f"Full development diagnostic gate failed: {target}")
        pred = predict(trace, manifest["design"], test, seed=cfg["seed"] + 23)
        actual = np.array([rate(r, "destination", target) for r in test])
        results["hierarchical_nb"] = metrics(actual, pred["mean"], pred["predictive"])
        results["hierarchical_nb"]["log_predictive_density"] = log_predictive_density(
            pred, np.array([r["destination"]["counts"][target] for r in test])
        )
        selected = selection["targets"][target]["selected_method"]
        draws = {
            "hierarchical_nb": pred["predictive"],
            **{m: b.predictive(test) for m, b in baselines.items()},
        }
        points = {
            "hierarchical_nb": pred["mean"],
            **{m: b.predict(test) for m, b in baselines.items()},
        }
        intervals = {
            m: np.quantile(v, [0.025, 0.1, 0.5, 0.9, 0.975], axis=0) for m, v in draws.items()
        }
        source_values = np.array([rate(r, "source", target) for r in test])
        q10, q90 = np.quantile(source_values, [0.1, 0.9])
        groups = {
            "same_team": [i for i, r in enumerate(test) if not r["actual_team_change"]],
            "changed_team": [i for i, r in enumerate(test) if r["actual_team_change"]],
            "previously_unseen_players": [
                i
                for i, r in enumerate(test)
                if r["player_id"] not in {q["player_id"] for q in train}
            ],
            "source_bottom_decile": np.flatnonzero(source_values <= q10).tolist(),
            "source_top_decile": np.flatnonzero(source_values >= q90).tolist(),
        }
        subgroup = {
            g: {m: metrics(actual[idx], points[m][idx], draws[m][:, idx]) for m in draws}
            for g, idx in groups.items()
            if idx
        }
        report["targets"][target] = dict(
            selected_method=selected,
            results=results,
            fit=manifest,
            ppc=posterior_predictive_check(trace, train, target),
            subgroups=subgroup,
            baseline_metadata={m: b.metadata() for m, b in baselines.items()},
        )
        for i, r in enumerate(test):
            prediction_rows.append(
                dict(
                    transition_id=r["transition_id"],
                    player_id=r["player_id"],
                    name=r["source"]["name"],
                    target=target,
                    source_environment_id=r["source_environment_id"],
                    destination_environment_id=r["destination_environment_id"],
                    source_team=r["source"]["team"],
                    destination_team=r["destination"]["team"],
                    source_role=r["source_role"],
                    destination_role=r["destination_role"],
                    source_minutes=r["source_minutes"],
                    destination_minutes=r["destination_minutes"],
                    actual_team_change=r["actual_team_change"],
                    source_observed=float(source_values[i]),
                    destination_observed=float(actual[i]),
                    selected_method=selected,
                    predictions={
                        m: dict(
                            mean=float(points[m][i]),
                            p025=float(intervals[m][0, i]),
                            p10=float(intervals[m][1, i]),
                            median=float(intervals[m][2, i]),
                            p90=float(intervals[m][3, i]),
                            p975=float(intervals[m][4, i]),
                        )
                        for m in draws
                    },
                )
            )
        write(root / "artifacts/phase3/translation_evaluation.json", report)
        write(root / "artifacts/phase3/heldout_predictions.json", prediction_rows)
        print("Held out", target, {m: round(v["mae"], 4) for m, v in results.items()}, flush=True)
        if sensitivities:
            boots = {
                r["source_environment_id"]: source_bootstrap(
                    root, r["source"], target, cfg["bootstrap_samples"]
                )
                for r in test
            }
            propagated = predict(
                trace, manifest["design"], test, seed=cfg["seed"] + 29, source_rates=boots
            )
            report["sensitivities"].setdefault("source_bootstrap", {})[target] = dict(
                metrics=metrics(actual, propagated["mean"], propagated["predictive"]),
                mean_source_standard_error=float(np.mean([v.std(ddof=1) for v in boots.values()])),
            )
    if sensitivities:
        for label, threshold, policy in [
            ("minutes_900", 900, "same_or_adjacent"),
            ("same_role", 600, "same"),
            ("alternative_prior", 600, "same_or_adjacent"),
            ("without_team", 600, "same_or_adjacent"),
        ]:
            variant = copy.deepcopy(cfg)
            if label == "alternative_prior":
                variant["priors"]["role_scale"] *= cfg["alternative_prior"][
                    "group_scale_multiplier"
                ]
                variant["priors"]["team_scale"] *= cfg["alternative_prior"][
                    "group_scale_multiplier"
                ]
                variant["priors"]["source_sd"] = cfg["alternative_prior"]["source_sd"]
                variant["priors_version"] = "context-priors-v1-wide"
            variant_rows, variant_split = dataset(root, threshold, policy)
            development = [r for r in variant_rows if r["split"] != "test"]
            heldout = [r for r in variant_rows if r["split"] == "test"]
            report["sensitivities"][label] = dict(split=variant_split, targets={})
            for target in cfg["targets"]:
                trace, manifest = fit(
                    root, development, target, variant, label, no_team=label == "without_team"
                )
                prediction = predict(trace, manifest["design"], heldout, seed=cfg["seed"] + 31)
                values = np.array([rate(r, "destination", target) for r in heldout])
                report["sensitivities"][label]["targets"][target] = dict(
                    metrics=metrics(values, prediction["mean"], prediction["predictive"]),
                    fit=manifest,
                )
                print("Sensitivity", label, target, manifest["diagnostics"]["passed"], flush=True)
                write(root / "artifacts/phase3/translation_evaluation.json", report)
    write(root / "artifacts/phase3/translation_evaluation.json", report)
    return report
