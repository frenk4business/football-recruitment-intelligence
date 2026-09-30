# Phase 5 hand-off — Production Hardening & Portfolio Integration

Phase 4 implements transparent, observed recruitment scenarios. Phase 5 has **not** started. Begin from current `main` after reviewing [Phase 4 QA](phase-4-qa.md), [model card](model-card-phase4.md), [complete evaluation](recruitment-fit-evaluation.md) and [deployment](deployment.md). Resolve the current deployed commit through Render and `git rev-parse origin/main`; do not assume a past phase SHA is still production.

## Preserve the evidence boundaries

- `player-dna-v1` / `features-v1` and Phase 2 artifacts remain unchanged: WSL 2023/24, 138 eligible ≥900-minute profiles, six roles, eighteen style features.
- `translation-model-v1` remains the historical WSL 2019/20 → 2020/21 study. Broad cross-league translation and transfer-success claims are NO-GO. Simple source/ridge defaults and calibration warnings remain; good Bayesian diagnostics did not establish better prediction.
- `recruitment-fit-v1` uses explicit weighted directional RMS percentile mismatch. `requirements-v1` separates assumptions from `club-context-v1` observations. Evidence is never blended into fit; no hidden club criteria, LLM ranking, age/fee/contract/nationality fields or current transfer advice.
- The selected rule was frozen before final queries. Final peer MRR .258 is effectively the same as existing DNA .259; final roster weighted MRR .232 trails DNA .332. Context findings are mixed. Every comparator and subgroup remains published.
- Weight Jaccard .950 and profile Jaccard .723 describe separate perturbations; neither is success confidence. Fourteen small pools force top-ten inclusion. Full-profile Pareto frontiers are often too large to discriminate.

## Product and contracts

English `/recruitment/`, Dutch `/nl/recruitment/`; methodology anchors `/methodology/#recruitment` and `/nl/methodology/#recruitment`. Find Candidates starts custom/neutral. Replace a Player creates exact observed targets, then supports adjusted requirements. Club Context reports fourteen team rates and club-stint roster distributions, with explicit adoption controls. The product provides top-ten ordering, up to three comparisons, per-feature/family explanations, evidence, exclusion reasons, Pareto flags, two robustness views and validated URL share/reset.

Python modules live in `src/football_intelligence/recruitment/`; shared specification in `config/recruitment-scoring.json`; browser scoring in `apps/web/src/lib/recruitment.ts`. `scripts/generate_contracts.py` generates TypeScript contracts, scoring metadata, schemas and OpenAPI. Twenty strict public aggregate artifacts are copied into the static build. No production API is required.

`make setup`, `make test`, `make build` and `make smoke` use committed aggregates and lockfiles. `make phase4-build` materializes the checksum-pinned 132-match cohort if absent, then rebuilds context/index/100 bootstrap samples and republishes frozen research results. First research run requires network/source cache and disk; subsequent runs reuse it. `make recruitment-evaluate` needs those canonical profiles/team observations and recomputes all registered query/robustness results without rewriting the selection. It is deliberately outside ordinary CI. `uv run python scripts/recruitment_reports.py` regenerates the report/figures. `fri recruitment audit` additionally requires the historical Phase 3 cache; it is not needed for a product build.

## Priorities to propose in Phase 5

1. Operational release controls: verify the actual commit-based Render auto-deploy setting, applied security headers, rollback procedure, dependency-update policy, CI permissions, build/bandwidth budgets and monitoring. The Blueprint is not automatically the configuration of this independently created site.
2. Measured product hardening: performance under lower-end mobile devices, keyboard/screen-reader review beyond automated axe, error recovery, stable scenario migrations, repeatable release checks and additional browser engines. Current browser automation uses Chromium; do not claim Safari/Firefox validation.
3. Publication/contract discipline: keep source caches private, validate every public export, keep deterministic parity fixtures and document breaking changes before introducing them. Profile bootstrap currently conditions on observed eligibility/targets and ignores shared match dependence; extending it changes the estimand and needs a new experiment.
4. Bilingual portfolio narrative: communicate progression from data engineering to representation learning, hierarchical inference and human decision support. Show negative results, sample-size limits and actual live evidence. The separate `Frenkkester.com` portfolio repository/service has not been modified; any integration is new Phase 5 work.
5. Future data research is a separate decision: expert relevance labels, prospective seasons, actual availability and broader longitudinal coverage would be needed to assess recruitment utility. Do not tune against the now-open final queries or silently redefine existing feature/version semantics.

## Delivery and resources

Continue using `frenk4business/football-recruitment-intelligence`, feature branches and reviewed PRs merged to `main` after checks. Preserve the chronological research commits. Existing Render static service `srv-dauh12hsrm7s73c7uiu0`, Starter build plan, current main branch. No backend, database, worker, persistent disk, subscription or paid resource was added for Phase 4. Existing build/bandwidth billing still applies. [Release checks](phase-4-qa.md) contain the actual counts and limitations.
