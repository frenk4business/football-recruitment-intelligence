"""Render the committed experiment results; never fit or select a method."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/phase4"
NAMES = {
    "weighted_rms": "Weighted RMS (selected)",
    "family_rms": "Family-balanced RMS",
    "satisfaction": "Threshold satisfaction",
    "hybrid": "Threshold + distance",
    "dna_nearest_neighbor": "Existing Player DNA",
    "requirements_only": "Requirements only",
    "plus_role_median": "Requirements + role median",
    "plus_full_context": "Requirements + role + team",
}


def load(name):
    return json.loads((BASE / (name + ".json")).read_text())


def table(metrics):
    lines = [
        "| Method | N | R@1 | R@5 | R@10 | MRR | Mean rank percentile | Candidates min/median/max |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name, m in metrics.items():
        size = m["candidate_sizes"]
        lines.append(
            f"| {NAMES[name]} | {m['queries']} | {m['recall1']:.3f} | {m['recall5']:.3f} | {m['recall10']:.3f} | {m['mrr']:.3f} | {m['mean_rank_percentile']:.1f} | {size['min']}/{size['median']:g}/{size['max']} |"
        )
    m = next(iter(metrics.values()))
    r = m["random"]
    lines.append(
        f"| Random expectation | {m['queries']} | {r['recall1']:.3f} | {r['recall5']:.3f} | {r['recall10']:.3f} | {r['mrr']:.3f} | 50 | same pools |"
    )
    return "\n".join(lines)


def main():
    results = {stage: load(stage + "_evaluation") for stage in ("development", "final")}
    robust = load("robustness")
    index = load("candidate_index")
    clubs = {c["club_id"]: c["name"] for c in index["clubs"]}
    text = """# Recruitment fit evaluation — Phase 4

`recruitment-fit-v1` · `requirements-v1` · `club-context-v1` · WSL 2023/24.

Weighted directional RMS provides transparent ordering under an analyst's requirements. The small retrospective experiments show some retrieval signal above chance, with limited separation from existing Player DNA and mixed context gains. They do not establish transfer success or expert scouting validity.

## Chronology and estimands

Evidence/schema commit `b2a6d57` preceded the registered [experiment](phase-4-experiment-plan.md), commit `2aa494e`. Scoring implementation `9a96a5a` preceded development evaluation. The [method decision](adr/007-recruitment-fit-method.md), commit `190bdc0`, preceded final outcomes at `c9982e5`. The registration and development hashes remain unchanged. The frozen decision's `final_queries_opened: false` records its state **at selection**, not the current completion state.

Eight clubs supplied development queries; four final query clubs (West Ham, Manchester City, Leicester and Brighton) were withheld from selection. Candidate pools overlap. The season and Phase 2 representation had already been examined. This is a query holdout, not a wholly unseen season or population.

Known-peer retrieval uses the median match-date split, **27 January 2024**, at least 450 reliable minutes in each half and stable roles. Earlier-half transforms are fitted before scoring; the label is the later-half nearest *other* peer under the existing DNA representation fitted on earlier observations. There are 89 paired profiles; two multi-club queries are omitted, leaving 56 development and 31 final queries. This is representation consistency, not a football-success label.

Roster holdout removes each eligible single-club query from its club-role target, reference percentile/scaling fit and team counts. At least two eligible role-mates remain. Those role-mates are excluded as candidate alternatives; the held-out player stays in the candidate pool. Three exact requirements use remaining role medians (progressive passes, progressive carries, pressures). This measures descriptive roster alignment. It can reward conformity and cannot distinguish complementarity from redundancy.

All methods, roles and sparse cases remain in the results. Recall@k means whether the designated profile is within k places; MRR averages reciprocal rank. Rank percentile is 100 × (N−rank)/(N−1), where higher places the designated profile earlier. Chance uses each query's actual N: min(k,N)/N and harmonic(N)/N, not an arbitrary universal baseline.

## Scoring and selection

For a candidate percentile x and target t, mismatch is |x−t| for exact, max(t−x,0) for minimum, max(x−t,0) for maximum, and absent for neutral. Distance is sqrt(sum(w × mismatch²)/sum(w)); lower is closer. Feature importance × family importance sets w; each explicit feature defaults to 1. Family balance is a registered comparator, not a hidden default. Hard constraints and reference exclusion run before scoring. Minutes and neighbour stability are evidence/filter dimensions, never fit terms. Stable IDs break distance ties at nine decimal places.

Weighted RMS passed development MRR-above-chance and mean weight-Jaccard ≥.65 gates. Family balance also passed and had greater DNA-neighbour agreement. The registered preference for equal explicit feature weights selected RMS; tiny metric differences did not establish a superior model. Threshold satisfaction (ten-point exact tolerance) and hybrid ordering are retained as research baselines but their discontinuities fail the continuous-severity requirement. No parameters were tuned on final queries.

## Retrieval and context ablations

Context ablations are 75% requirement squared distance +25% full role median, or 50% requirements +25% role +25% team. Team context uses matching count features with the held-out player's target-team counts removed; actual team minutes remain. In temporal experiments all contextual data is from the earlier half. Comparing team percentiles with player-role percentiles remains an ecological assumption, not a validated translation rule. The product instead requires explicit adoption of a contextual characteristic.

"""
    for stage, result in results.items():
        text += f"### {stage.title()}: later-half peer retrieval\n\n{table(result['temporal']['metrics'])}\n\n"
        text += f"### {stage.title()}: roster holdout\n\n{table(result['roster']['metrics'])}\n\n"
        text += f"### {stage.title()}: temporal context, common supported queries only\n\n{table(result['temporal']['context_ablation']['metrics'])}\n\n"
    text += """Final weighted peer Recall@5 is 45.2% versus 31.6% random; MRR .258 is essentially the same as existing DNA .259. With only 31 queries, shared candidate pools and representation-derived labels, these differences are not proof of scouting value. Threshold satisfaction's final Recall@5 (.258) is below chance (.316), despite slightly higher MRR than chance.

Context has **mixed**, not uniformly negative, results. Final roster MRR improves from .232 to .271 with role median and .277 with team context, while existing DNA remains higher at .332. Final temporal context MRR falls .223 → .218 → .210, but Recall@10 increases .667 → .750. Development temporal context MRR had improved .412 → .464 → .513. These tiny, selected subgroups do not justify a general context claim.

![Held-out retrieval and chance](figures/phase4/retrieval.png)

### Final role-level results: selected method

| Task | Role | N | R@5 | R@10 | MRR |
|---|---|---:|---:|---:|---:|
"""
    for task in ("temporal", "roster"):
        for role, m in results["final"][task]["metrics"]["weighted_rms"]["roles"].items():
            text += f"| {task} | {role} | {m['queries']} | {m['recall5']:.3f} | {m['recall10']:.3f} | {m['mrr']:.3f} |\n"
    text += """
Final temporal CM has no eligible query; final roster ST has none. Missing rows are not zeros. Final CB roster Recall@5 is only .083 (12 queries); final FB/WB roster Recall@10 is zero (three queries). These failures remain visible. All methods' role metrics and every query's candidate size/rank are in the complete [development](../artifacts/phase4/development_evaluation.json) and [final](../artifacts/phase4/final_evaluation.json) artifacts.

## Replacement reconstruction and weights

Exact full-profile targets remove the reference player. Overlap with existing DNA neighbours measures representation agreement, not correctness. Final reconstruction has 46 single-club queries; development has 87.

| Stage | Method | N | Mean top-10 weight Jaccard | Mean DNA-neighbour Jaccard |
|---|---|---:|---:|---:|
"""
    for stage, result in results.items():
        for name, m in result["reconstruction"]["metrics"].items():
            text += f"| {stage} | {NAMES[name]} | {m['queries']} | {m['mean_weight_jaccard']:.3f} | {m['mean_dna_neighbor_jaccard']:.3f} |\n"
    text += """
## Separate robustness analyses

205 registered scenarios: 72 club-role three-feature custom profiles and 133 single-club full-profile replacements. Custom thresholds (75 progressive passes, 70 progressive carries, 75 pressures) are research assumptions and are not silently preselected in the UI.

Weight sensitivity uses 100 independent ±20% multipliers on active weights, shared seed 20260930 and a deterministic LCG. Profile sensitivity uses 100 whole-player-match bootstraps, preserving feature/minute dependence within a sampled row and recomputing rates. Percentiles use the fixed original role ECDF; published samples are quantized to 0.1 percentile point. Eligibility, targets, hard constraints and roles stay fixed. The two analyses are intentionally not averaged into a confidence score. Per-candidate inclusion and 10th–90th rank intervals are reported separately.

| Group | Scenarios | Pools ≤10 | Weight Jaccard mean | Profile Jaccard mean | Frontier median |
|---|---:|---:|---:|---:|---:|
"""
    groups = {
        "All": robust["summary"],
        "Pools >10": robust["larger_pools"],
        **robust["by_kind"],
        **robust["by_role"],
    }
    for group, m in groups.items():
        text += f"| {group} | {m['scenarios']} | {m['small_pools']} | {m['weight_mean_jaccard']:.3f} | {m['profile_mean_jaccard']:.3f} | {m['frontier_size_quantiles'][2]:g} |\n"
    text += (
        "\n| Analysis | Minimum | P10 | Median | P90 | Maximum |\n|---|---:|---:|---:|---:|---:|\n"
    )
    for name in ("weight", "profile"):
        text += (
            f"| {name} | "
            + " | ".join(f"{x:.3f}" for x in robust["summary"][name + "_jaccard_quantiles"])
            + " |\n"
        )
    text += """
Fourteen CM scenarios have at most ten candidates, forcing top-10 inclusion to 100%. Larger-pool results (.946 weights, .703 profiles) better expose sensitivity. Profile sampling affects the ordering substantially more than modest weight changes, especially CB and FB/WB. Hard constraints are held fixed during profile resampling: this is ranking sensitivity conditional on observed eligibility, not uncertainty about constraint compliance. Shared team/match dependence, target uncertainty, injuries, tactical change and external validity are absent. Bootstrap inclusion is not a success probability or calibrated confidence level.

![Separate ranking sensitivities by role](figures/phase4/robustness.png)

### Least stable custom scenarios under profile sampling

| Club | Role | Eligible | Weight Jaccard | Profile Jaccard | Frontier size |
|---|---|---:|---:|---:|---:|
"""
    for r in sorted(
        (r for r in robust["scenarios"] if r["kind"] == "custom"),
        key=lambda r: r["profile"]["mean_jaccard"],
    )[:5]:
        text += f"| {clubs[r['club_id']]} | {r['role']} | {r['eligible']} | {r['weight']['mean_jaccard']:.3f} | {r['profile']['mean_jaccard']:.3f} | {r['frontier_count']} |\n"
    text += """
## Pareto trade-offs

A candidate is dominated only when another eligible candidate is no worse on every active mismatch and strictly better on at least one. Ties remain on the frontier; evidence is not a criterion. Weight changes do not alter this unweighted frontier. The UI shows flags/counts beside a bounded top ten, with the actual per-feature differences available in comparison.

For three-criterion custom scenarios, the median frontier has **2.5 players**, range **1–7**. For eighteen-feature replacements the median is **22**, range **8–34**: high dimensionality makes non-dominance weak evidence of usefulness. The product warns when most candidates share the frontier. All 72 custom cases include per-candidate frontier membership over 100 profile samples in [robustness.json](../artifacts/phase4/robustness.json); replacement frontier bootstrap is deliberately withheld because near-universal membership is uninformative. No list is called an optimal-player set.

## Evidence limits and reproducibility

The [historical audit](phase-4-fit-evidence.md) found only twelve minute-eligible recorded team changes at 900 minutes, nine ending 2019/20 and three 2020/21. Real availability, recruitment opportunities and success labels are absent; destination observations were already studied. Transfer-success evaluation is **NO-GO**. Do not call these tests transfer accuracy, current recruitment advice, or 2024/25 predictions.

Observed 2023/24 rankings never use the historical Phase 3 predictions. The separate 2019/20 → 2020/21 study retains its simple defaults, undercoverage warnings and cross-league NO-GO. Player DNA features and representations remain unchanged. Five eligible multi-club players are labelled whole-season composites; club roster references instead use ≥900-minute club stints. Age, salary, contracts, nationality and market value are absent.

`make phase4-build` rebuilds club/index/bootstrap aggregates from the pinned canonical cohort and republishes strict allowlists using the frozen selection/results. A clean first run downloads the checksum-locked 132-match cohort; cached reruns need no network. `make recruitment-evaluate` recomputes all query and robustness results and compares at 1e-10 tolerance, ignoring only the current code-commit metadata; it never overwrites frozen evidence or reselects a method. `uv run python scripts/recruitment_reports.py` renders this report and figures from committed results.

Public aggregate numbers are rounded to eight decimals; bootstrap percentiles are quantized to tenths. Ten Python reference scenarios test browser ordering, contribution values, exclusions, Pareto membership, URL reconstruction and both robustness summaries at 1e-7 tolerance. During product QA the reference-scenario helper's mode metadata was corrected (replacement IDs require replacement mode); all scientific results reproduced unchanged. Additional season/duplicate guards do not alter valid outputs. [Model card](model-card-phase4.md) · [QA](phase-4-qa.md) · [Phase 5 hand-off](phase-5-handoff.md).
"""
    (ROOT / "docs/recruitment-fit-evaluation.md").write_text(text)
    destination = ROOT / "docs/figures/phase4"
    destination.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "#f6f7f3",
            "axes.facecolor": "#f6f7f3",
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), layout="constrained")
    for ax, task, title in zip(
        axes,
        ["temporal", "roster"],
        ["Later-half peer retrieval · 31 queries", "Roster holdout · 27 queries"],
        strict=True,
    ):
        metrics = results["final"][task]["metrics"]
        keys = ["weighted_rms", "family_rms", "hybrid", "satisfaction", "dna_nearest_neighbor"]
        ax.barh(
            [NAMES[k].replace(" (selected)", "") for k in keys][::-1],
            [metrics[k]["mrr"] for k in keys][::-1],
            color=["#788e81", "#788e81", "#788e81", "#788e81", "#17583f"],
        )
        ax.axvline(
            metrics[keys[0]]["random"]["mrr"],
            color="#ad592c",
            linestyle="--",
            label="Random expectation",
        )
        ax.set(xlabel="Mean reciprocal rank (higher retrieves earlier)", xlim=(0, 0.4), title=title)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Final query evidence · descriptive retrieval, not transfer success", fontsize=12)
    fig.savefig(destination / "retrieval.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4.8), layout="constrained")
    roles = list(robust["by_role"])
    x = np.arange(len(roles))
    for offset, field, label, color in [
        (-0.18, "weight", "±20% weights", "#17583f"),
        (0.18, "profile", "Player-match bootstrap", "#b47d50"),
    ]:
        ax.bar(
            x + offset,
            [robust["by_role"][r][field + "_mean_jaccard"] for r in roles],
            0.36,
            label=label,
            color=color,
        )
    ax.set(
        xticks=x,
        xticklabels=roles,
        ylim=(0, 1.05),
        ylabel="Mean top-10 Jaccard",
        title="205 scenarios · fixed targets / eligibility · 100 draws per analysis",
    )
    ax.legend(loc="lower left", frameon=False)
    fig.text(
        0.5,
        -0.01,
        "14 small CM pools force top-10 inclusion; sampling does not measure success probability.",
        ha="center",
        fontsize=9,
    )
    fig.savefig(destination / "robustness.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
