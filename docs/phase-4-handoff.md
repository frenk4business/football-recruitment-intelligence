# Phase 4 hand-off — Recruitment Intelligence & Club Fit

## Repository and release boundary

Repository: `frenk4business/football-recruitment-intelligence`. Phase 3 implementation branch: `phase/03-league-translation`; [PR #3](https://github.com/frenk4business/football-recruitment-intelligence/pull/3) targets `main`. The latest main at Phase 3 start was `3d8f9a4ad7f1eb585ea5256cbaeeb5a273c32519`, with Phases 1/2 already merged. The Phase 3 release commit and final CI/deployment evidence are recorded on PR #3 and in [Phase 3 QA](phase-3-qa.md). Before starting Phase 4, fetch and resolve current main with `git fetch origin && git rev-parse origin/main`; never branch from the old Phase 2 deployment branch. Completed phase PRs are authorized to merge after checks.

## What exists

- Phase 1: separate StatsBomb event and one-minute SkillCorner/PySport tracking demonstrations, canonical schemas, validation, Parquet/DuckDB, local FastAPI and a bilingual explorer. The tracking sample is not a physical-capacity model.
- Phase 2: observed `player-dna-v1`, registry `features-v1`; WSL 2023/24, 132 matches, 336 roster players, 138 comparable at 900 minutes, 18 style features, role-standardized/family-balanced Euclidean distance, top-10 explanations and bootstrap stability. [Phase 2 evaluation](player-similarity-evaluation.md).
- Phase 3: `translation-model-v1`, `translated-profile-v1`, same feature/DNA revisions, conditional historical WSL season/team context. Four Bayesian count models and three baselines, frozen method selection, later-season evaluation and static predictive summaries. Observed DNA is never overwritten with translated values.

## Providers, supported environments and evidence

StatsBomb revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`; exact inputs in `config/phase3.sources.json`. Full audit: 80 competition-seasons, 3,961 matches/lineups, 11,794 player IDs, 9,651 repeated roster IDs. Provider-ID metadata anomalies are quarantined; names never join IDs or providers. Wyscout/Figshare metadata has a separate CC BY 4.0 feasibility audit; it contributes no event features or training rows. No Transfermarkt or market values.

Only FA Women’s Super League supports this model. Selected historical coverage: 2018/19 (107 matches), 2019/20 (87), 2020/21 (131), 2023/24 (132). 660 identities, 1,225 player/team/season stints, 565 adjacent candidates, 385 structurally accepted and 162 eligible at 600/600 minutes before final temporal/role/context narrowing. There are zero cross-league model episodes. Broad/pair cross-league translation is NO-GO; within-WSL context is CONDITIONAL. [Full evidence and rejection matrices](phase-3-transfer-evidence.md).

Public sources must be 2019/20, at least 600 reliable minutes, complete/in-range source rates and consistent identity. Target scenarios are teams observed in WSL 2020/21, with prior team context available at the source cutoff and same/adjacent target role. The index includes all audited target teams so unsupported ones can explain their missing context; inclusion in the index is not permission to produce a number. AM has only two earlier role episodes and fails the five-episode public display guard. Major role changes, sparse context and extrapolation contain no estimates. 120 players have source-eligible observations and 3,608 supported scenario combinations. Hypothetical club choices are research scenarios, not recommendations.

## Targets and uncertainty

Non-penalty shots, completed progressive open-play passes, progressive carries and StatsBomb pressures, all counts normalized by reliable exposure. The selected default is ridge for shots/passes and unchanged source for carries/pressures. Changing target club therefore does not change the latter two default point estimates. No Bayesian target qualified under every validation rule; it is a labelled research comparison only.

The Bayesian likelihood is negative binomial with minutes offset, source rate/exposure, assumed target role, role-change indicator, prior team pass-volume ratio and partially pooled role/team effects. No player intercept or league effect. Priors, seeds, frozen splits and amendments: [registered experiment](phase-3-experiment-plan.md), [model card](model-card-phase3.md).

Contracts expose observed source, expected target, predictive p10/p90 and p025/p975, interval kind, source/target IDs, assumed role, model/profile versions, status/exclusion reasons and numerical evidence. Bayesian expected-rate p10/p90 is separate from future-observation intervals. Public Bayesian ranges simulate 900 minutes; baseline empirical ranges are exposure-invariant and reflect earlier ≥600-minute season windows. Never label the latter as Bayesian credible intervals or promise their nominal coverage. Source bootstrap uncertainty is a sensitivity analysis, not fully integrated errors-in-variables inference.

## Evaluation to carry forward

53 train, 12 player-disjoint validation; 65 refit development; 76 later test. Fitted outcomes end February 2020; test begins September 2020. Only four test team changes. Roles in research: AM, CB, CM, DM, FB/WB, ST, W. Source observations may overlap earlier development outcomes; they are flagged, and target outcomes remain held out. Method selection is immutable for v1.

| Target | Default MAE /90 | Bayesian MAE /90 | Default 80% cover / width |
|---|---:|---:|---|
| Shots | 0.397 | 0.404 | 73.7% / 0.969 |
| Progressive passes | 0.920 | 0.950 | 71.1% / 1.889 |
| Progressive carries | 0.500 | 0.550 | 80.3% / 1.552 |
| Pressures | 2.894 | 3.354 | 76.3% / 8.214 |

Zero primary divergences; max R-hat 1.0055; min key bulk ESS 943. Prior checks pass after documented pre-fit alternatives. Local PPC variance/tail failures remain. Wider priors and removing team terms change point estimates little. Source bootstrap widens intervals but does not resolve pass undercoverage. Removing the only league pair leaves no data. [All baselines, effects, calibration, subgroup and sensitivity results](league-translation-evaluation.md).

## Artifacts, APIs and build

- `data/processed/phase3/`: local feature-observation/context Parquet, environment and transition JSON marts, frozen dataset and source metadata.
- `artifacts/phase3/`: committed source/identity/eligibility audit, split, priors, validation, evaluation, held-out pairs, context effects, reproduction and publication manifests.
- `artifacts/phase3/posterior/`: local ignored NetCDF and fit manifests. Four development fits about 24 MB; do not publish draws.
- `artifacts/phase3/public/`: typed compact index, models/evaluation and lazy per-player profiles, about 14.3 MB total and about 121 KB maximum per player. Static product under `/data/phase3/`.
- Local endpoints: `/api/v1/translation/models`, `/environments`, `/players/{player_id}`, `/predict?player_id=…&source_environment=…&target_environment=…&target_role=…`, `/evaluation`. [API contract](api.md).
- `make setup`, `make test`, `make build`, `make smoke`; `make translation-audit`, `make phase3-build`; `uv run python scripts/phase3_reproduce.py` reconstructs locally with network disabled and runs fresh primary fits. Full research sampling is outside CI and production requests.

Python tests cover synthetic known-effect recovery, partial pooling, exposure, identity, adjacency, leakage guards, source checksums, frozen selection, contract/range validity, API validation and unsupported states. Frontend tests and Playwright check EN/NL, interactions, keyboard, mobile, errors, uncertainty and accessibility. Final actual counts and clean-build evidence: [Phase 3 QA](phase-3-qa.md).

## Render and rights

Use existing static service `srv-dauh12hsrm7s73c7uiu0` in `tea-d7ln8pbbc2fs73bkqpdg`, Starter build plan. Build `cd apps/web && npm ci && npm run build`, publish `apps/web/out`, Node 24.19.0. No additional paid infrastructure beyond the existing Render subscription. Target branch `main`; see [deployment](deployment.md) and QA for the actual branch/deploy verification. No database/worker/API hosting is necessary for precomputed scenarios. English `/translation/`, Dutch `/nl/translation/`.

StatsBomb raw events, lineup feeds and canonical raw Parquet stay local, with required source attribution/logo and non-commercial terms. Code MIT does not override source rights. Wyscout is separately attributed; never mix provider metrics merely because labels sound similar. [Attribution](../ATTRIBUTION.md).

## First Phase 4 task

Define and audit **one concrete club-context/recruitment requirement schema** against the available historical observations, before building a recommendation score. It should accept observed Player DNA, supported translation scenarios, uncertainty, numeric evidence and explicit constraints. Determine which club context can actually be observed at decision time, which requirements are user assumptions and which outcomes could evaluate fit on a new untouched period.

Do not treat Phase 3 team coefficients as causal club effects, fill unsupported leagues with pooled guesses, merge observed and estimated profiles, or calibrate on the already inspected 2020/21 test while still calling it untouched. Cross-league expansion needs new same-provider longitudinal evidence and a new registered experiment/version. Failed/non-playing moves, missing role/context, selection bias, weak effects and undercoverage are research priorities. Phase 4 must preserve those limits while answering its own club-fit question.
