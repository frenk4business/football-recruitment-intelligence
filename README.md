# Football Recruitment Intelligence

Open football data → observed Player DNA → historical performance translation, with visible uncertainty. Independent non-commercial research by Frenk Kester.

[Live translation](https://football-recruitment-intelligence.onrender.com/translation/) · [Nederlands](README.nl.md) · [Player DNA](https://football-recruitment-intelligence.onrender.com/player-dna/) · [Research evaluation](docs/league-translation-evaluation.md) · [Model card](docs/model-card-phase3.md)

Phase 3 is merged into `main` with green CI. **Production activation is pending:** the existing Render service still needs its Branch setting changed from `phase/02-player-dna` to `main`. The translation links above are not yet live; [release verification](docs/phase-3-qa.md) records the current 404 checks.

## Phase 3: what the evidence supports

The full official StatsBomb catalogue was audited: **80 competition-seasons, 3,961 match lineups and 11,794 provider identities**. A separate Wyscout audit did not solve the shortage of longitudinal transfer evidence. Broad cross-league translation is **NO-GO**. The implemented fallback is a **conditional historical FA Women’s Super League season/team-context study**, not a universal translator or a transfer-success score.

Four WSL seasons provide 457 matches, 660 roster players and 1,225 environment stints. Reliable minutes, provider identity, adjacent observation windows and role/context coverage yield **53 train / 12 validation / 76 later-season test episodes**, with 600 reliable minutes on both sides. Only **four test episodes change team**. The source is 2019/20 and the target scenario is 2020/21; this is not a current-season forecast.

Three baselines are compared with four hierarchical Bayesian negative-binomial count models. Role and team effects are partially pooled; minutes enter as exposure. Inputs use source activity and team information available before the destination observation. No league coefficient is estimated from a single league. Priors and the experiment were committed before fitting, and method choices were committed before inspecting the later test.

| Target | Validation-selected default | Test MAE /90 | 80% range coverage | Mean width /90 |
|---|---|---:|---:|---:|
| Non-penalty shots | Ridge regression | 0.397 | 73.7% | 0.969 |
| Progressive passes | Ridge regression | 0.920 | 71.1% | 1.889 |
| Progressive carries | Unchanged source | 0.500 | 80.3% | 1.552 |
| Pressures | Unchanged source | 2.894 | 76.3% | 8.214 |

**No Bayesian model qualified as the public default under every validation rule.** It remains a documented research comparison. All primary fits have zero divergences and maximum R-hat 1.0055; good sampling did not guarantee better prediction. Shot/pass ranges understate uncertainty. Context effects are weakly identified and do not justify ranking clubs or leagues.

The bilingual workflow shows source and target environment, role assumption, observed versus expected action rates, an 80% predictive range, numeric evidence and pooling warnings. Unsupported periods, roles, low minutes, missing context and source extrapolation get explicit states without estimates. Observed Player DNA remains separate: WSL 2023/24, 132 matches, 336 roster players, 138 comparable profiles at 900 minutes and 18 style features.

## Run and reproduce

Requirements: Python 3.12–3.13, [uv](https://docs.astral.sh/uv/), Node **24.19.0**, npm and Make. Use the committed lockfiles.

```sh
git clone https://github.com/frenk4business/football-recruitment-intelligence.git
cd football-recruitment-intelligence
make setup
make test
make build
cd apps/web && npx playwright install chromium && cd ../..
make smoke
make dev
```

The static build uses committed, validated research aggregates and needs no source downloads, secrets or model server. English `/translation/`; Dutch `/nl/translation/`. `make api` starts optional local FastAPI with interactive `/docs`.

```sh
make data-bootstrap       # small Phase 1 event/tracking sample
make phase2-build         # pinned WSL 2023/24 features/similarity
make translation-audit    # full catalogue + separate Wyscout metadata audit
make phase3-build         # WSL data, fixed-selection evaluation, public summaries and reports
uv run python scripts/phase3_reproduce.py  # offline reconstruction + four fresh fits
make contracts            # Pydantic → TypeScript / JSON Schema / OpenAPI
```

The first research build downloads bounded, checksum-locked sources; repeated builds reuse them. Full research sampling is offline from the product, not part of Render builds or CI. `make translation-validate` is the explicit historical model-selection stage; the committed v1 selection must remain unchanged before test evaluation. [Architecture](docs/architecture.md) · [API](docs/api.md) · [provenance](docs/data-provenance.md).

## Research, rights and limits

[Evidence audit](docs/phase-3-transfer-evidence.md) · [scope decision](docs/adr/006-phase3-evidence-scope.md) · [registered experiment](docs/phase-3-experiment-plan.md) · [prior predictive checks](docs/phase-3-prior-predictive.md) · [every baseline and sensitivity](docs/league-translation-evaluation.md) · [Player DNA evaluation](docs/player-similarity-evaluation.md).

Selection on destination minutes omits many non-playing outcomes. Historical fixture coverage is incomplete, target roles are supplied assumptions, and team/ability/opportunity are confounded. There is no causal league-strength claim, market value model or club recommendation. Baseline ranges describe earlier ≥600-minute season windows; only the optional Bayesian research range simulates a specific 900-minute observation.

Raw StatsBomb event/lineup feeds, canonical Parquet and full posterior draws remain local. Only permitted derived research aggregates are published; source attribution and the StatsBomb logo remain visible. Wyscout metadata is separately attributed under CC BY 4.0. The one-minute SkillCorner sample remains a data-engineering demonstration, not a physical performance model. [Data rights and attribution](ATTRIBUTION.md).

## Delivery and next phase

One existing Render Static Site serves committed aggregates. **No additional paid infrastructure was introduced beyond the existing Render workspace/Starter subscription.** No backend, worker, database or disk was added. Production is intended to track `main`; actual deployment verification is recorded in [deployment](docs/deployment.md) and [Phase 3 QA](docs/phase-3-qa.md). Completed phase PRs merge after checks; phase branches are not permanent review boundaries.

1. Data Foundation — complete.
2. Player DNA & Similarity — complete.
3. League Translation & Bayesian Performance Transfer — complete/current, with the narrower WSL scope above.
4. Recruitment Intelligence & Club Fit — planned.
5. Production Hardening & Portfolio Integration — planned.

Phase 3 adds hierarchical inference, prior/PPC checks, probabilistic calibration, temporal holdout discipline, negative-result reporting and static delivery of predictive uncertainty. [Phase 4 hand-off](docs/phase-4-handoff.md) · [Portfolio learning](docs/portfolio-context.md).

Code © 2026 Frenk Kester, MIT. Data and logos retain their own rights.
