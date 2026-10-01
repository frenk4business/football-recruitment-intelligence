"""Generate human-readable v1.1 evidence from the measured, versioned outputs."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def generate():
    index = load("artifacts/v11/public/index.json")
    evaluation = load("artifacts/v11/evaluation.json")
    reports = load("data/processed/v11/full/coverage.json")
    coverage = load("artifacts/v11/public/coverage.json")
    storage = load("artifacts/v11/storage-audit.json")
    counts = index["counts"]
    audit = ROOT / "docs/v1.1-data-expansion-audit.md"
    initial = audit.read_text().split("## Final measured build")[0].rstrip()
    lines = [
        initial,
        "",
        "## Final measured build",
        "",
        f"The pinned domestic build ingests **{counts['matches']:,} matches and {counts['events']:,} events**, yielding **{counts['profiles']:,} searchable player-season profiles**, **{counts['provider_identities']:,} distinct provider identities** and **{counts['common_profiles']:,} common profiles**. Counts are not unique cross-provider people. There are {counts['competitions']} distinct named/gender competitions, {counts['provider_competitions']} provider-competition entities, {counts['competition_seasons']} provider competition-seasons and {counts['seasons']} season labels.",
        "",
        "| Provider | Competition | Season | Matches | Events | Participating IDs | Searchable | Common | Similarity | Reliable match rows |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for c in reports:
        s = next(s for s in index["scopes"] if s["id"] == c["scope"])
        q = c["quality"]
        lines.append(
            f"| {c['provider']} | {c['competition']} | {c['season']} | {c['matches']} | {q['events']:,} | {c['raw_player_ids']} | {s['profiles']} | {s['common_profiles']} | {s['similarity_profiles']} | {q['reliable_rows']:,}/{q['participating_rows']:,} |"
        )
    lines += [
        "",
        "StatsBomb: 1,535 matches, 5,361,046 events, 2,358 participating provider identities, 1,178 searchable profiles / 1,118 searchable identities. Wyscout: 1,826 matches, 3,071,395 events, 2,571 participating provider identities, 1,896 searchable profiles / 1,887 searchable identities. The 2020/21 WSL catalogue has **131/132** scheduled fixtures and remains labelled partial. Listed full seasons still have explicitly reported event/minute anomalies; full schedule coverage does not imply all player profiles qualify.",
        "",
        "### Published dataset totals versus this build",
        "",
        f"The complete Figshare match archive contains **1,941** matches, verified from all seven members. Its event archive contains **3,251,294** records: the five domestic selections plus {sum(storage['wyscout_additional_international_events'].values()):,} international events counted separately. The pinned players article v3 file contains **{storage['wyscout_all_metadata_players']:,} metadata identities**. The literature/reported 4,299 count is **not the count of this downloaded metadata file**; this project neither fabricates the difference nor uses it as database coverage. No unknown positive player IDs occur in the selected Wyscout events; 226,038 events have actor ID zero (stoppages/unattributed actions), kept canonical but not invented as players.",
        "",
        "### Minute and role exclusions",
        "",
        "Unreliable participation in any included appearance excludes that entire player-season, even if its remaining appearances exceed the minute threshold. Reliable minutes alone do not override missing roles/geometry. The build does not relax this policy to increase player count. Reasons overlap:",
        "",
        "| Exclusion reason | Player-seasons |",
        "| --- | ---: |",
    ]
    lines += [f"| `{key}` | {n} |" for key, n in sorted(coverage["excluded_profiles"].items())]
    lines += [
        "",
        "Source metadata additionally audits all 80 StatsBomb catalogue competition-seasons: match/team/player counts, dates, event-file presence, position/interval coverage and source revision are in `artifacts/v11/catalogue-audit.json`. Unselected seasons are **not** asserted to have reconciled event minutes. Selected per-season quality reports are committed in `artifacts/v11/ingestion-quality.json`.",
        "",
        "### Storage and publication",
        "",
        "All source files are pinned in `config/v11-sources.json` with SHA256, bytes, official URL and upstream MD5 where provided. Raw files remain ignored, outside Git and Render. There are 11 substantial event Parquet partitions and 11 observation partitions, split by provider/competition/season, plus season-profile Parquet. DuckDB exposes observations, provider player-seasons/features, common features and eligibility views. Full events are streamed/per-match decoded; the 190 MB Wyscout league JSON is never loaded as one Python object.",
        "",
        f"The local source cache occupies {storage['source_bytes']['statsbomb']:,} StatsBomb bytes (including catalogue lineups) and {storage['source_bytes']['wyscout']:,} Wyscout bytes. Initial event/observation Parquet totals were {sum(storage['processed_bytes'].values()):,} bytes; all current partition measurements are in `storage-audit.json`. Incremental manifests verify code/source keys and output hashes before reuse. A failed/incomplete partition is never reused.",
        "",
    ]
    audit.write_text("\n".join(lines))
    lines = [
        "# Common profile evaluation — v1.1",
        "",
        "Reproduce with `make v11-data-build`. The source/semantic audit preceded expanded event ingestion. The [experiment plan](v1.1-experiment-plan.md) records both pre-evaluation amendments; the machine-readable results are in [`evaluation.json`](../artifacts/v11/evaluation.json). Frozen Phase 1–4 research is separate.",
        "",
        "## Feature decisions and missingness",
        "",
        "`common-profile-v1` contains exactly **non-penalty shots per90, all pass attempts per90 including restarts, and long pass attempts ≥30 m per90**. A nominal 90-minute denominator and a shared 105×68 m geometry are explicit. Common comparisons display unscaled rates; similarity uses shared development z-scaling. Goalkeepers are excluded from the common representation.",
        "",
        "Seven candidates passed the initial conceptual mapping, but four completion-dependent candidates failed the full-season availability screen: legitimate StatsBomb Unknown outcomes leave only 30 EPL development profiles at 450 minutes. No successful threshold/classifier result preceded their removal. Completion, progressive passes, final-third entries and box entries remain tested candidate formulas, not deployed common dimensions. Neither unknown outcomes nor missing geometry are imputed. See the [semantic matrix](provider-feature-semantics.md) and [`candidate-availability.json`](../artifacts/v11/candidate-availability.json). Three dimensions offer much less style detail than validated WSL Player DNA.",
        "",
        "## Threshold selection and temporal retrieval",
        "",
        "Within each provider/competition-season, split matches chronologically at the median match. Full profiles must be reliable, and each half needs at least half the total-minute threshold. Only same-identity pairs with the same broad role enter each retrieval cohort (minimum 20). This is a survivor/stable-role sample, not all searchable players. First-half development profiles from StatsBomb EPL 2015/16 and Wyscout EPL 2017/18 alone fit all scalers. Other leagues are method-transfer checks, not prospective external validation.",
        "",
        "| Minutes | Development macro-provider MRR | Common profiles |",
        "| ---: | ---: | ---: |",
    ]
    for t in (450, 600, 900):
        lines.append(
            f"| {t} | {evaluation['development_scores'][str(t)]:.6f} | {coverage['threshold_counts'][str(t)]} |"
        )
    lines += [
        "",
        f"The registered smallest-threshold-at-90%-of-best rule selects **{evaluation['selected_threshold']} minutes**. This decision is close to its boundary: 450-minute development MRR is 0.298713 versus a 90%-of-best cutoff of 0.298563. The higher-threshold sensitivity is retained; 450 is an evidence/coverage trade-off, not proof that 450-minute profiles are as stable as 900-minute profiles.",
        "",
        "| Scaling | Minutes | Provider | Queries | MRR | 95% query-bootstrap interval |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]
    for r in evaluation["temporal"]:
        for provider, v in r["providers"].items():
            lines.append(
                f"| {r['scaling']} | {r['threshold']} | {provider} | {v['n']} | {v['mrr']:.4f} | {v['mrr_ci'][0]:.4f}–{v['mrr_ci'][1]:.4f} |"
            )
    selected = next(
        r for r in evaluation["temporal"] if r["threshold"] == 450 and r["scaling"] == "shared"
    )
    lines += [
        "",
        "### Selected common-similarity-v1, per cohort",
        "",
        "| Cohort / role | n | Recall@1 | Recall@5 | Recall@10 | MRR | Random expected MRR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in selected["cohorts"]:
        m = row["metrics"]
        lines.append(
            f"| {row['scope']} / {row['role']} | {row['n']} | "
            + (
                " | ".join(
                    f"{m[k]:.3f}"
                    for k in ["recall_at_1", "recall_at_5", "recall_at_10", "mrr", "random_mrr"]
                )
                if m
                else "— | — | — | — | —"
            )
            + " |"
        )
    boot = evaluation["match_bootstrap"]
    lines += [
        "",
        f"Match bootstrap resamples observed appearances independently for **both query and candidate profiles**, with a fixed development scaler, 40 replicates and up to 12 queries per cohort. Mean top-ten Jaccard ranges from **{min(r['mean_top10_jaccard'] for r in boot):.3f} to {max(r['mean_top10_jaccard'] for r in boot):.3f}**. It conditions on the observed schedule and reliable included profiles; it does not model opponent dependence, future availability or source annotation uncertainty. Full cohort intervals and candidate/query counts are in the JSON report. Each Jaccard interval is the empirical replicate/query spread, not a confidence interval for the mean.",
        "",
        "## Held-out provider classification",
        "",
        "A fixed balanced logistic regression (C=1), with a training-only standard scaler, predicts provider from the common vector. A 30% held-out split groups provider player IDs, preventing the same identity in multiple seasons from crossing train/test. Primary analysis matches provider counts within broad role and the three shared league names; seasons remain different. No hyperparameter optimisation.",
        "",
        "| Analysis | Train / held-out profiles | AUC (95% identity-bootstrap CI) | Balanced accuracy (95% CI) |",
        "| --- | ---: | --- | --- |",
    ]
    for label, r in evaluation["provider_classification"].items():
        lines.append(
            f"| {label}: {r['sample']} | {r['train_profiles']} / {r['heldout_profiles']} | {r['auc']:.3f} ({r['auc_ci'][0]:.3f}–{r['auc_ci'][1]:.3f}) | {r['balanced_accuracy']:.3f} ({r['balanced_accuracy_ci'][0]:.3f}–{r['balanced_accuracy_ci'][1]:.3f}) |"
        )
    lines += [
        "",
        "**Provider measurement remains detectable despite semantic harmonisation.** The point estimates do not trigger the predeclared >0.75 veto, but the AUC intervals overlap 0.75. Passing a veto is not positive validation. Public cross-provider nearest-neighbour ranking is therefore **withheld**: three dimensions, no cross-provider identity ground truth and confounded league/time/gender cannot establish player-style equivalence. Manual descriptive comparison remains available using only common v1; within-provider rankings enforce competition-season and broad role. No domain adaptation is deployed.",
        "",
        "## Provider distributions and neighbourhood composition",
        "",
        "Every accepted feature is audited by broad role, both across all included data and within the three shared league names. The full report contains n, mean, median, population SD, 5/25/75/95% quantiles, KS statistic and raw-unit Wasserstein distance. League/year differences are confounded with provider; these are not paired annotation error estimates.",
        "",
        "| League | Role | Feature | SB mean / median / SD | Wyscout mean / median / SD | KS | Wasserstein |",
        "| --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for r in evaluation["distributions"]:
        a, b = r["providers"]["statsbomb"], r["providers"]["wyscout"]
        lines.append(
            f"| {r['league']} | {r['role']} | {r['feature']} | {a['mean']:.3f} / {a['median']:.3f} / {a['sd']:.3f} | {b['mean']:.3f} / {b['median']:.3f} / {b['sd']:.3f} | {r['ks_statistic']:.3f} | {r['wasserstein']:.3f} |"
        )
    lines += [
        "",
        "| Scaling | Role | Provider | Same-provider top-ten share | Same-provider candidate share |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for r in evaluation["neighbour_provider_balance"]:
        lines.append(
            f"| {r['scaling']} | {r['role']} | {r['provider']} | {r['same_provider_top10_share']:.3f} | {r['same_provider_available_share']:.3f} |"
        )
    lines += [
        "",
        "Raw, shared, provider-global and provider/role scaling are all reported. Provider-specific scalers change neighbour composition and may conceal real measurement differences; they are sensitivity experiments, never evidence that the providers became equivalent. Shared scaling is the explicitly versioned published within-cohort method. Neighbour ties resolve by profile ID.",
        "",
        "![Provider PCA, descriptive only](../artifacts/v11/provider-pca.png)",
        "",
        "PCA is descriptive on all eligible profiles after development-fitted shared scaling. Its axes are not used for similarity or tuned for separation; loadings and explained variance are in `artifacts/v11/pca.json`.",
        "",
        "## Unchanged research and limits",
        "",
        "Searchable, common-comparable, similarity-capable and historical-translation eligibility are different flags. Expanded StatsBomb raw profiles are `statsbomb-profile-v2`, not a revalidation of WSL `player-dna-v1`. Wyscout `wyscout-profile-v1` has broad metadata roles; no CB/DM positions are invented. Exact StatsBomb IDs link only the original WSL 2023/24 DNA capability. No selected scope is the original Phase-3 2019/20 source cohort, so expanded translation flags are false. No expanded profile enters Phase-4 recruitment.",
        "",
        "Source event coverage can be incomplete despite a complete schedule; 809 player-seasons have unresolved participation conflicts and are excluded as a whole. Keeper and geometric-availability exclusions further narrow common coverage. No cross-provider identity resolution, causal provider-effect estimate, commercial-feed coverage, longitudinal transfer utility, live data refresh or expanded recruitment validation is claimed.",
        "",
    ]
    (ROOT / "docs/common-profile-evaluation.md").write_text("\n".join(lines))
    (ROOT / "artifacts/v11/ingestion-quality.json").write_text(
        json.dumps(reports, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    generate()
