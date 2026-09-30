"""Reproduce scientific tables and figures from the frozen Phase 3 experiment."""

import json
from pathlib import Path

import numpy as np

from football_intelligence.dna.cohort import write
from football_intelligence.translation.baselines import rate
from football_intelligence.translation.dataset import dataset
from football_intelligence.translation.materialize import settings
from football_intelligence.translation.models import fit, posterior_array


def reports(root: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = root / "artifacts/phase3"
    cfg = settings(root)
    evaluation = json.loads((directory / "translation_evaluation.json").read_text())
    heldout = json.loads((directory / "heldout_predictions.json").read_text())
    priors = json.loads((directory / "prior_predictive.json").read_text())
    rows, split = dataset(root)
    development = [r for r in rows if r["split"] != "test"]
    training = [r for r in rows if r["split"] == "train"]
    figures = root / "docs/figures/phase3"
    figures.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
        }
    )
    methods = ["unchanged_source", "role_mean", "ridge", "hierarchical_nb"]
    colors = ["#737773", "#a57745", "#275e4a", "#4b68a2"]
    effects, descriptive = {}, {}
    lines = [
        "# Held-out WSL context translation evaluation",
        "",
        "The later-season test was opened only after method selection was committed at `a330893`. The experiment was frozen at `bbed4d2`, after the separate evidence audit. All methods and sensitivity results are reported; the test did not change public method selection.",
        "",
        "## Data and interpretation",
        "",
        f"53 train / 12 player-disjoint validation / 76 later-season test episodes. Refit development N=65. {evaluation['shared_historical_players']} test players have earlier development history; no player intercept is fitted. Four test episodes change recorded club, so this is principally next-season context prediction rather than a transfer-effect test. Target roles are supplied scenario assumptions, and target minutes condition the evaluation rather than being predicted.",
        "",
        "600 reliable minutes required on both sides; seven outfield role groups in research. Train roles: `"
        + str(split["roles"]["train"])
        + "`; validation: `"
        + str(split["roles"]["validation"])
        + "`; test: `"
        + str(split["roles"]["test"])
        + "`. Test destination dates: 2020-09-05–2021-05-09; all fitted outcomes end by 2020-02-23.",
        "",
        "## Every method on the untouched season",
        "",
        "Errors and widths are actions per 90. Intervals are future-observation intervals. Empirical baseline ranges use centred five-fold player-separated residuals, clipped at zero; Bayesian intervals simulate counts at each actual held-out exposure. LP density is the Bayesian mean log probability of the observed count; it is not comparable to a rate-density score or available for the empirical baselines.",
        "",
        "| Target | Method | MAE | RMSE | 50% cover | 80% cover | 95% cover | 80% width | 80% interval score | Default |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for target in cfg["targets"]:
        item = evaluation["targets"][target]
        for method in methods:
            v = item["results"][method]
            lines.append(
                f"| {target} | {method} | {v['mae']:.3f} | {v['rmse']:.3f} | {v['intervals']['50']['coverage']:.1%} | {v['intervals']['80']['coverage']:.1%} | {v['intervals']['95']['coverage']:.1%} | {v['intervals']['80']['mean_width']:.3f} | {v['intervals']['80']['interval_score']:.3f} | {'yes' if method == item['selected_method'] else ''} |"
            )
    lines += [
        "",
        "![Predictive calibration](figures/phase3/calibration.png)",
        "",
        "The selected defaults underestimate uncertainty for shots and progressive passes. The Bayesian model does not consistently improve point error, and its progressive-pass intervals under-cover substantially. Carries are conservative. Coverage has sampling uncertainty: only 76 episodes, clustered by team and with some repeated historical players. No post-test calibration was fitted.",
        "",
        "![Held-out observations and residuals](figures/phase3/heldout.png)",
        "",
        "Every point above is a held-out episode using its validation-selected method. The committed `heldout_predictions.json` includes every observed value and each method’s predictive bounds. High-end source profiles and the four changing-team cases need particular caution.",
        "",
        "## Sampling and posterior predictive checks",
        "",
        "| Target | Divergences | Max R-hat | Min key bulk ESS | Min tail ESS | Mean count log predictive density |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for target, item in evaluation["targets"].items():
        d = item["fit"]["diagnostics"]
        lines.append(
            f"| {target} | {d['divergences']} | {d['max_rhat']:.5f} | {d['min_key_bulk_ess']:.0f} | {d['min_tail_ess']:.0f} | {item['results']['hierarchical_nb']['log_predictive_density']:.3f} |"
        )
    lines += [
        "",
        "All four overall development means, variances, zero fractions and 90th percentiles lie inside the model’s 90% posterior-predictive statistic intervals. This in-sample check does not establish out-of-sample calibration. Local failures remain:",
        "",
    ]
    for target, item in evaluation["targets"].items():
        misses = [
            f"{group}/{name}: {stat}"
            for group in ["by_role", "by_team"]
            for name, v in item["ppc"][group].items()
            for stat, check in v["statistics"].items()
            if not check["inside90"]
        ]
        lines.append(
            f"- {target}: {'; '.join(misses) if misses else 'no flagged role/team statistic'}."
        )
    lines += [
        "",
        "Small-group PPC flags are descriptive, without multiple-comparison correction. Dispersion allows overdispersion; there is no zero-inflation term because the exposure-filtered targets contain few zeros. Means alone would hide the listed variance/tail mismatches.",
        "",
        "## Context and partial pooling",
        "",
        "One competition makes league effects unidentifiable. The following ratios describe a **10% increase in historically observed target/source team pass volume**, conditional on source rate, role and source exposure. They are associations, not interventions or league-strength coefficients. All 95% intervals include one.",
        "",
        "| Target | Context rate ratio | 80% equal-tail interval | 95% equal-tail interval | Posterior mean role SD | Posterior mean team SD |",
        "|---|---:|---|---|---:|---:|",
    ]
    for target in cfg["targets"]:
        trace, manifest = fit(root, development, target, cfg, "development")
        beta = posterior_array(trace, "beta_context")
        ratio = np.exp(beta * np.log(1.1))
        q = np.quantile(ratio, [0.025, 0.1, 0.9, 0.975])
        role_effect = posterior_array(trace, "role_effect")
        latent = posterior_array(trace, "rate")
        pooled = []
        for j, role in enumerate(manifest["design"]["roles"]):
            idx = [i for i, r in enumerate(development) if r["destination_role"] == role]
            y = sum(development[i]["destination"]["counts"][target] for i in idx)
            without_role = latent[:, idx] / np.exp(role_effect[:, j, None])
            expected = np.sum(
                without_role.mean(axis=0)
                * np.array([development[i]["destination_minutes"] / 90 for i in idx])
            )
            pooled.append(
                dict(
                    role=role,
                    n=len(idx),
                    unpooled_conditional_log_residual=float(np.log((y + 0.5) / (expected + 0.5))),
                    posterior_log_effect_mean=float(role_effect[:, j].mean()),
                    posterior_log_effect_p10=float(np.quantile(role_effect[:, j], 0.1)),
                    posterior_log_effect_p90=float(np.quantile(role_effect[:, j], 0.9)),
                )
            )
        effects[target] = dict(
            context_for_10_percent_pass_ratio=dict(
                mean=float(ratio.mean()),
                p025=float(q[0]),
                p10=float(q[1]),
                p90=float(q[2]),
                p975=float(q[3]),
            ),
            role_pooling=pooled,
        )
        lines.append(
            f"| {target} | {ratio.mean():.3f} | {q[1]:.3f}–{q[2]:.3f} | {q[0]:.3f}–{q[3]:.3f} | {posterior_array(trace, 'role_sd').mean():.3f} | {posterior_array(trace, 'team_sd').mean():.3f} |"
        )
        delta = np.array(
            [rate(r, "destination", target) - rate(r, "source", target) for r in training]
        )
        descriptive[target] = dict(
            n=len(delta),
            mean=float(delta.mean()),
            median=float(np.median(delta)),
            sd=float(delta.std(ddof=1)),
            p10=float(np.quantile(delta, 0.1)),
            p90=float(np.quantile(delta, 0.9)),
        )
    write(directory / "context_effects.json", effects)
    write(directory / "training_descriptive_changes.json", descriptive)
    changes = {}
    fig, axes = plt.subplots(2, 4, figsize=(13, 6), layout="constrained")
    for j, target in enumerate(cfg["targets"]):
        roles = sorted({r["destination_role"] for r in training})
        changes[target] = []
        for i, role in enumerate(roles):
            for changed, color, offset in [(False, colors[2], -0.1), (True, colors[1], 0.1)]:
                group = [
                    r
                    for r in training
                    if r["destination_role"] == role and r["actual_team_change"] == changed
                ]
                if not group:
                    continue
                delta = [rate(r, "destination", target) - rate(r, "source", target) for r in group]
                ratio = [
                    rate(r, "destination", target) / rate(r, "source", target)
                    for r in group
                    if rate(r, "source", target) > 0
                ]
                changes[target].append(
                    dict(
                        role=role,
                        competition_pair="WSL → WSL",
                        transition_type="team_and_season_change"
                        if changed
                        else "season_change_same_team",
                        n=len(group),
                        delta=delta,
                        ratio=ratio,
                        undefined_zero_source_ratios=len(group) - len(ratio),
                    )
                )
                for ax, values in [(axes[0, j], delta), (axes[1, j], ratio)]:
                    ax.scatter(
                        np.full(len(values), i + offset),
                        values,
                        s=13,
                        color=color,
                        alpha=0.65,
                        marker="x" if changed else "o",
                    )
        axes[0, j].set(title=target.replace("_", " "), ylabel="Destination − source /90")
        axes[1, j].set(ylabel="Destination / source", xlabel="Assumed target role")
        for ax, reference in [(axes[0, j], 0), (axes[1, j], 1)]:
            ax.axhline(reference, color="#aaaaaa", linestyle="--")
            ax.set(xticks=range(len(roles)), xticklabels=roles)
            ax.tick_params(axis="x", labelsize=7)
    fig.suptitle(
        "Training observations only (n=53), WSL → WSL · green: same team; brown ×: team change",
        fontsize=10,
    )
    fig.savefig(figures / "training_changes.png", dpi=160)
    plt.close(fig)
    write(directory / "training_change_distributions.json", changes)
    lines += [
        "",
        "![Partial pooling](figures/phase3/pooling.png)",
        "",
        "Open crosses show role-wise log residual adjustments relative to posterior-mean fixed/team terms; bars show posterior role effects with equal-tail 80% intervals. This is an explanatory conditional residual comparison, not a separately fitted no-pooling model. AM has just two development episodes and is excluded from public numeric scenarios by the five-episode display rule. Group effects are weakly identified and correlated with context; do not rank clubs or roles from them. The synthetic test separately verifies low-N shrinkage.",
        "",
        "## Sensitivity results",
        "",
        "These were registered, then evaluated on their specified later subsets. They are not candidates for post-test selection. Different minutes/role filters change the evaluation population, so their errors are not paired improvement claims.",
        "",
        "| Variant | Target | Development / test N | MAE | 80% cover | 80% width | Diagnostic gate |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for variant, item in evaluation["sensitivities"].items():
        for target, v in item.get("targets", item).items():
            m = v["metrics"]
            n = v["fit"]["episodes"] if "fit" in v else 65
            lines.append(
                f"| {variant} | {target} | {n} / {m['n']} | {m['mae']:.3f} | {m['intervals']['80']['coverage']:.1%} | {m['intervals']['80']['mean_width']:.3f} | {v.get('fit', {}).get('diagnostics', {}).get('passed', 'same primary fit')} |"
            )
    lines += [
        "",
        "The modest wider prior barely changes point estimates. Removing team terms also changes little, consistent with limited information about context effects. A 900-minute filter and same-role policy do not solve progressive-pass undercoverage. Source bootstrap propagation widens ranges and raises progressive-pass 80% coverage from 64.5% to 71.1%, still short of nominal. Mean source bootstrap standard errors (per90): "
        + ", ".join(
            f"{t} {v['mean_source_standard_error']:.3f}"
            for t, v in evaluation["sensitivities"]["source_bootstrap"].items()
        )
        + ". Bootstrap resamples player matches independently and does not model shared match/team dependence or full errors-in-variables uncertainty.",
        "",
        "Dominant-pair sensitivity is not identifiable: removing the sole WSL→WSL pair leaves no data. No second competition was manufactured. Role/team effects do not separate tactical role, opportunity, season changes or unobserved ability causally.",
        "",
        "## Small held-out subgroups",
        "",
        "| Target | Subgroup | N | Selected MAE | Bayesian MAE | Bayesian 80% cover |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for target, item in evaluation["targets"].items():
        for group, g in item["subgroups"].items():
            b = g["hierarchical_nb"]
            lines.append(
                f"| {target} | {group} | {b['n']} | {g[item['selected_method']]['mae']:.3f} | {b['mae']:.3f} | {b['intervals']['80']['coverage']:.1%} |"
            )
    lines += [
        "",
        "## Post-fit descriptive and publication notes",
        "",
        "![Training-only changes](figures/phase3/training_changes.png)",
        "",
        "The requested separate distributions of difference and ratio were produced after fitting, from the 53 training rows only (`training_descriptive_changes.json` and `training_change_distributions.json`). Ratios omit and count zero-source denominators; no epsilon is used. The figure separates roles and same-team/team-change episodes within the sole WSL→WSL pair. It did not select priors, targets or hyperparameters. The pre-fit audit established counts/coverage/selection but did not include this separate descriptive table; this timing deviation is recorded rather than backdated.",
        "",
        "Public eligibility adds conservative source bounds (per-target training+validation min/max), a minimum of five role episodes, and the registered same/adjacent-role and pre-change-context requirements. These gates were implemented after test reporting for display safety; the held-out evaluation is reported on all 76 registered rows, not recomputed on a favourable displayed subset. They do not establish that arbitrary club scenarios are validated transfers.",
        "",
        "The initial experiment wording applied a 900-minute public exposure to all intervals. Implementation clarifies that only count-model predictive simulations are exposure-specific: empirical baseline residual intervals span the earlier ≥600-minute season windows and remain exposure-invariant. No test-based scaling was added. Both limitations are visible in the product.",
        "",
        "Full metadata, priors, seeds, package versions, code/data hashes and diagnostics: `artifacts/phase3/translation_evaluation.json`. NetCDF posteriors remain local under ignored `artifacts/phase3/posterior/`; public summaries contain no draws or raw provider feeds.",
        "",
    ]
    (root / "docs/league-translation-evaluation.md").write_text("\n".join(lines))
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.5), layout="constrained")
    for ax, target in zip(axes, cfg["targets"], strict=True):
        for method, color in zip(methods, colors, strict=True):
            v = evaluation["targets"][target]["results"][method]
            ax.plot(
                [0.5, 0.8, 0.95],
                [v["intervals"][q]["coverage"] for q in ["50", "80", "95"]],
                "o-",
                color=color,
                label=method,
            )
        ax.plot([0.45, 1], [0.45, 1], "--", color="#aaaaaa")
        ax.set(
            xlim=(0.45, 1),
            ylim=(0.25, 1),
            title=target.replace("_", " "),
            xlabel="Nominal coverage",
            ylabel="Observed coverage",
        )
    axes[-1].legend(fontsize=6, loc="lower right")
    fig.savefig(figures / "calibration.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(2, 4, figsize=(13, 6), layout="constrained")
    for j, target in enumerate(cfg["targets"]):
        values = [r for r in heldout if r["target"] == target]
        actual = np.array([r["destination_observed"] for r in values])
        pred = np.array([r["predictions"][r["selected_method"]]["mean"] for r in values])
        hi = max(actual.max(), pred.max()) * 1.05
        axes[0, j].scatter(pred, actual, s=12, color=colors[2], alpha=0.7)
        axes[0, j].plot([0, hi], [0, hi], "--", color="#aaaaaa")
        axes[0, j].set(
            title=target.replace("_", " "),
            xlabel="Expected /90",
            ylabel="Observed /90",
            xlim=(0, hi),
            ylim=(0, hi),
        )
        axes[1, j].hist(actual - pred, bins=12, color=colors[2], alpha=0.8)
        axes[1, j].axvline(0, color="#333333", linestyle="--")
        axes[1, j].set(xlabel="Observed − expected /90", ylabel="Episodes")
    fig.savefig(figures / "heldout.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 4, figsize=(13, 4), layout="constrained")
    for ax, target in zip(axes, cfg["targets"], strict=True):
        v = effects[target]["role_pooling"]
        y = np.arange(len(v))
        point = np.array([r["posterior_log_effect_mean"] for r in v])
        lo = np.array([r["posterior_log_effect_p10"] for r in v])
        hi = np.array([r["posterior_log_effect_p90"] for r in v])
        ax.errorbar(
            point,
            y,
            xerr=np.stack([point - lo, hi - point]),
            fmt="o",
            color=colors[2],
            label="Pooled 80% interval",
        )
        ax.scatter(
            [r["unpooled_conditional_log_residual"] for r in v],
            y,
            marker="x",
            color=colors[1],
            label="Conditional raw adjustment",
        )
        ax.axvline(0, color="#aaaaaa", linestyle="--")
        ax.set(
            yticks=y,
            yticklabels=[f"{r['role']} (n={r['n']})" for r in v],
            title=target.replace("_", " "),
            xlabel="Log role adjustment",
        )
    axes[-1].legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    fig.savefig(figures / "pooling.png", dpi=160)
    plt.close(fig)
    prior_lines = [
        "# Phase 3 prior predictive checks",
        "",
        "Registered before real-outcome fitting. 1,500 prior draws per specification; fixed seed 20260930. Both latent-rate and future-observation tails are checked against football plausibility ceilings. These are broad regularization checks, not hard outcome limits. Main priors passed. Two wider-prior candidates failed the 1% carry-tail gate and were narrowed before fitting; all rejected runs remain in the audit JSON and original experiment amendment.",
        "",
        "| Check | Latent p01 / median / p99 | Future p01 / median / p99 | Ceiling | Latent above | Future above | Passed |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for name, p in priors.items():
        q = p["rate_quantiles"]
        future = p["observation_prediction"]
        prior_lines.append(
            f"| {name} | {q['p01']:.2f} / {q['p50']:.2f} / {q['p99']:.2f} | {' / '.join(f'{v:.2f}' for v in future['rate_quantiles'])} | {p['ceiling']} | {p['fraction_above_ceiling']:.3%} | {future['fraction_above_ceiling']:.3%} | {p['passed']} |"
        )
    prior_lines += [
        "",
        "Each final fit also runs its own prior check with its development covariates and exposures; these results are retained in the fit manifests. A failed prior gate stops fitting. The final alternative uses role/team scale multiplier 1.15 and source elasticity SD 0.40. No prior was selected by held-out accuracy.",
        "",
        "Priors and likelihood: [registered experiment](phase-3-experiment-plan.md). Full outputs: `artifacts/phase3/prior_predictive.json`. The negative-binomial dispersion prior creates much wider predictive tails than coefficient uncertainty alone; both are explicitly checked.",
    ]
    (root / "docs/phase-3-prior-predictive.md").write_text("\n".join(prior_lines) + "\n")


if __name__ == "__main__":
    reports(Path.cwd())
