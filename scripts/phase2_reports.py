"""Generate inspectable research reports from the frozen registry and measured results."""

import json
from pathlib import Path

from football_intelligence.dna.cohort import local_cohort, write
from football_intelligence.dna.registry import CORE, REGISTRY
from football_intelligence.dna.similarity import Representation, matrix, select

root = Path.cwd()
report = json.loads((root / "artifacts/phase2/similarity_evaluation.json").read_text())
eligibility = json.loads((root / "artifacts/phase2/cohort_eligibility.json").read_text())


def save(name, text):
    (root / "docs" / name).write_text(text + "\n")


features = """# Player feature registry — features-v1

The executable registry is `src/football_intelligence/dna/registry.py`. Player DNA contains 18 core style features in five families. Nine output/context measures are display/research only. All rates aggregate counts and reliable elapsed minutes first; they never average match rates. A conflicting player-match contributes neither actions nor denominator. Zero means observed absence; null means unavailable evidence or an undefined denominator. All 18 core values must exist for eligibility.

Coordinates are actor-relative 105 × 68 reference metres, attacking right. The goal centre is (105,34). Progression is this project's explicit research definition, not a claim to reproduce a vendor metric: `d_start - d_end >= max(10, 0.25*d_start)`. For example (20,34)→(50,34) qualifies; (50,34)→(55,34) and backward (60,34)→(20,34) do not. An explicitly reversed coordinate system is rotated before applying this formula. The penalty box is x≥88.5 and 13.84≤y≤54.16. Off-pitch endpoints are retained; box entries must end in the valid box. Long passes use ≥30 m reference displacement, not the provider's yard length.

Shot assists and xA require reciprocal pass.assisted_shot_id / shot.key_pass_id, same team, same match, later shot and periods 1–4. Penalty shots and shootouts are excluded; set-piece assists remain included. Missing links or xG make the affected value null. Own goals never become shot goals. The shot-assist measure is therefore a count of linked non-penalty shot opportunities, not all assists awarded by another provider.

Possession opportunities are distinct (match,period,possession,owner) sequences with at least one recorded event while the player is on the pitch. They measure sequences, not duration or true possession percentage. Team passing share uses open-play team attempts during the player's participation. Context alternatives remain outside the selected distance; three replacements were evaluated without a consistent benefit. Field tilt, possession-duration adjustment and aerial-duel reconstruction are deferred because further definition validation would be needed. No missing feature is imputed.

| ID | English | Nederlands | Family | Core | Unit | Formula |
|---|---|---|---|---|---|---|
"""
for f in REGISTRY:
    features += f"| `{f.id}` | {f.label_en} | {f.label_nl} | {f.family} | {f.core} | {f.unit} | {f.formula} |\n"
features += """
## Source/conversion assessment

[StatsBomb's official source repository](https://github.com/statsbomb/open-data) defines event fields. [socceraction SPADL documentation](https://socceraction.readthedocs.io/en/latest/documentation/spadl/spadl.html) describes an on-ball action schema with 105×68 coordinates and original-event links, but also inserts synthetic dribbles and omits pressure events. Canonical events can map ID, period, seconds, actor, team, coordinates, type, outcome and body part into SPADL; its home-team direction convention requires explicit rotation. Replacing this canonical layer would lose required pressure/context evidence. Decision: retain the existing model; no runtime socceraction dependency or purported independent action-count benchmark in this release. Its converter is a future validation experiment, not an authority that overrides discrepancies. xT and VAEP are not computed.

Dutch definitions and methodological explanations are authored manually in the application. They are not machine-translated at runtime.
"""
save("player-features.md", features)

text = """# Player similarity evaluation — evaluation-v1

Generated from `artifacts/phase2/similarity_evaluation.json`; includes every configured method and threshold, not only favourable results. The experiment plan was registered in `docs/phase-2-experiment-plan.md` before evaluation.

Cohort: 132 WSL 2023/24 matches, 12 teams, 336 roster players, 495,189 events. One provider/revision. Eligible populations exclude uncertain roles, missing core values, GK and role groups below 12 members. AM is not merged with W; DM and CM remain separate. Default: 900 reliable minutes, 138 eligible profiles, 18 features, five equal families, role-specific standard scaling and Euclidean distance.

Temporal views use the common median match-date cutoff. Queries/candidates are the same paired eligible players with at least half the threshold in each window and an unchanged primary role. Candidate sets are role-isolated; evaluation allows at least three paired profiles in a supported production role. Scalers and PCA fit only the earlier window. Source match sets are disjoint and recorded in the machine report. This is within-season consistency, not held-out transfer or scouting validation. Method selection used this experiment; there is no untouched test season.

100 bootstraps resample whole player-match observations with replacement, independently per player, rebuild all vectors and refit transformations. Eligibility and roles are frozen. Shared match/team dependence is not preserved by this bootstrap. Seed 20260930. The public inclusion rate is how often a neighbour occurs in the top 10; it is not a calibrated confidence probability.

## All method comparisons

| Minutes | Method | Eligible | Queries | R@1 | R@5 | R@10 | MRR | Bootstrap Jaccard | Overlap with robust baseline |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
"""
for threshold in ["450", "600", "900", "1200"]:
    values = report["thresholds"][threshold]
    for method, result in values["methods"].items():
        r = result["retrieval"]
        text += f"| {threshold} | {method} | {values['eligible']} | {r['queries']} | {r['recall1']:.3f} | {r['recall5']:.3f} | {r['recall10']:.3f} | {r['mrr']:.3f} | {result['bootstrap_jaccard']:.3f} | {result['baseline_neighbor_overlap']:.3f} |\n"
text += "\n## Selected method sensitivity and random reference\n\n| Minutes | Role sizes | Random R@5 | Random R@10 | Minutes–Jaccard Spearman |\n|---:|---|---:|---:|---:|\n"
for t in ["450", "600", "900", "1200"]:
    v = report["thresholds"][t]
    r = v["methods"]["standard_scaling"]["retrieval"]
    text += f"| {t} | {v['roles']} | {r['random_expectation']['recall5']:.3f} | {r['random_expectation']['recall10']:.3f} | {v['minutes_jaccard_spearman']:.3f} |\n"
base = report["thresholds"]["900"]
text += "\n## Default role-level results\n\n| Role | Paired candidates | R@1 | R@5 | R@10 | MRR | Bootstrap Jaccard (full eligible group) |\n|---|---:|---:|---:|---:|---:|---:|\n"
for role, r in base["methods"]["standard_scaling"]["retrieval"]["roles"].items():
    text += f"| {role} | {r['candidates']} | {r['recall1']:.3f} | {r['recall5']:.3f} | {r['recall10']:.3f} | {r['mrr']:.3f} | {base['methods']['standard_scaling']['jaccard_by_role'][role]:.3f} |\n"
text += """
## Hypotheses and selection

- H1 was not supported: global robust scaling outperformed role-specific robust scaling on retrieval and stability. Candidates remained role-isolated, so this is a scaling effect. The product keeps role-relative standard scaling for interpretation; it does not claim this restriction maximises retrieval.
- H2 is not established as a causal or strong within-cohort effect. Higher thresholds raise aggregate stability, but also remove players and shrink candidate groups. Within-threshold rank correlations are near zero or negative. CM has only 12 profiles at 900 minutes and ST only 12 at 1,200, making top-10 overlap intrinsically high.
- H3 was not consistently supported: equal family weighting does not beat naive feature weighting on every measure. We retain equal family weights as an explicit interpretability policy, preventing feature-count dominance, not as an empirical performance win.
- H4 is only partially supported: PCA broadly preserves neighbours and most variance, but neither improves retrieval consistently nor improves bootstrap stability. Retain full-feature distance. The separate two-dimensional PCA map is exploratory and is not used for ranking.
- Standard scaling improved retrieval and bootstrap stability over the robust full-feature baseline at all four thresholds. Winsorised robust scaling improved retrieval, but did not improve stability consistently and changes extreme observations. No profiles are removed or clipped in the selected model.
- Ablation: removing passing or defending noticeably weakens same-player retrieval. Other changes can help some metrics; no family is selected/dropped to make named player pairs look plausible.
- Possession adjustment replaces pressure/interception per-90 with per-100 opponent sequences and progressive passes with per-100 own sequences. It has no consistent stability advantage. Keep these measures separate and label them as sequence-based context.

900 is a practical coverage/evidence compromise, not a statistically optimal threshold: 138 profiles across six roles, versus 93 across five at 1,200. Lower thresholds stay available with numeric evidence and stability. No quality, tactical-fit, future-potential or transfer claims follow from these results.

## PCA audit

PCA uses full deterministic SVD on family-weighted standardized features, retaining at least 90% variance. No whitening. Each comparison-role model has separate loadings, mean and explained-variance ratios in the machine report. The UI map separately fits two components to role-standardized vectors and explicitly disclaims cross-role distance meaning.

| Role | Retained components | Explained variance | Largest absolute PC1 loadings |
|---|---:|---:|---|
"""
for p in base["pca"]:
    pc = p["pca"]
    load = sorted(zip(p["features"], pc["components"][0], strict=True), key=lambda x: -abs(x[1]))[
        :4
    ]
    text += f"| {p['role']} | {pc['n_components']} | {sum(pc['explained_variance_ratio']):.3f} | {', '.join(f'{k}: {v:.3f}' for k, v in load)} |\n"
text += """
## Outlier and publication policy

Robust scaling uses median/IQR; zero-IQR features fall back to population standard deviation, and constant dimensions are omitted. Standard scaling uses mean/population SD. The research winsorisation control clips at the training cohort's 1st/99th percentiles; it is not public production preprocessing. Full fitted scaler metadata and the named player/feature values affected by research clipping are recorded in `artifacts/phase2/outlier_audit.json`. All players, including unusual profiles, remain unless excluded by the documented evidence policy.

No UMAP, xT, VAEP or learned contrastive representation was trained. CPU PCA is the only latent representation experiment. A second independent season and team/context changes are needed before representation learning or league translation could be evaluated responsibly.
"""
save("player-similarity-evaluation.md", text)

# Named, derived audit of research clipping; no production value is clipped.

profiles = json.loads((local_cohort(root) / "player_profiles.json").read_text())
affected = []
for threshold in (450, 600, 900, 1200):
    selected = select(profiles, threshold)
    for role in sorted({p["primary_role"] for p in selected}):
        group = [p for p in selected if p["primary_role"] == role]
        x = matrix(group)
        model = Representation(scaling="winsor").fit(x)
        for i, p in enumerate(group):
            for j, feature in enumerate(CORE):
                if x[i, j] < model.lower[j] or x[i, j] > model.upper[j]:
                    affected.append(
                        dict(
                            threshold=threshold,
                            role=role,
                            player_id=p["player_id"],
                            name=p["name"],
                            feature=feature,
                            observed=float(x[i, j]),
                            research_clipped=float(
                                min(max(x[i, j], model.lower[j]), model.upper[j])
                            ),
                        )
                    )
write(
    root / "artifacts/phase2/outlier_audit.json",
    dict(
        policy="Research 1st/99th percentile winsorisation control only. Production does not clip or exclude outliers.",
        affected=affected,
    ),
)

# Independent DuckDB queries over canonical Parquet for team-context inspection.
import duckdb  # noqa: E402
import polars as pl  # noqa: E402

con = duckdb.connect()
con.read_parquet(str(local_cohort(root) / "matches/*/events.parquet")).create_view("events")
team_rows = (
    con.sql("""SELECT team_id, count(*) AS event_volume,
count(*) FILTER (WHERE event_type='Pass') AS pass_volume,
count(*) FILTER (WHERE event_type='Pass' AND x>=70) AS final_third_pass_starts,
count(DISTINCT (match_id,period,possession)) FILTER (
WHERE json_extract_string(attributes_json,'$.possession_team.id')=json_extract_string(attributes_json,'$.team.id')) AS own_sequences_in_actor_events
FROM events WHERE period<5 GROUP BY team_id ORDER BY team_id""")
    .pl()
    .to_dicts()
)
team_names = {
    r["id"]: r["name"] for r in pl.read_parquet(local_cohort(root) / "teams.parquet").to_dicts()
}
for row in team_rows:
    row["team"] = team_names[row["team_id"]]
write(
    root / "artifacts/phase2/team_context_audit.json",
    dict(
        note="Exploratory team volumes. Own sequences counted in actor events are not possession duration. Final-third pass starts are a field-tilt candidate, not a validated possession measure; not in production distance.",
        teams=team_rows,
    ),
)
obs = pl.read_parquet(local_cohort(root) / "player_feature_observation.parquet")
quality = (
    obs.filter(~pl.col("minutes_reliable"))
    .select(
        "player_id",
        "team_id",
        "match_id",
        "observed_on",
        "minutes_quality",
        "minutes_quality_reason",
    )
    .sort("match_id", "player_id")
    .to_dicts()
)
write(
    root / "artifacts/phase2/minutes_audit.json",
    dict(
        excluded_player_matches=quality,
        policy="Both numerator and minutes excluded for these conflicting observations. IDs are canonical; no provider lineup intervals or event feeds are published.",
    ),
)
actorless = (
    con.sql(
        "SELECT event_type,count(*) AS count FROM events WHERE player_id IS NULL GROUP BY event_type ORDER BY event_type"
    )
    .pl()
    .to_dicts()
)
team_coverage = (
    con.sql(
        "SELECT team_id,count(DISTINCT match_id) AS matches FROM events GROUP BY team_id ORDER BY team_id"
    )
    .pl()
    .to_dicts()
)
write(
    root / "artifacts/phase2/data_quality_audit.json",
    dict(
        actorless_events=actorless,
        team_match_coverage=team_coverage,
        unknown_or_uncertain_role_profiles=sum(p["primary_role"] is None for p in profiles),
        conflicting_player_matches=len(quality),
        missing_lineup_player_ids=int(obs["player_id"].null_count()),
    ),
)
