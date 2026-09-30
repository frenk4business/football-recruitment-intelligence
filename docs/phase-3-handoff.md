# Phase 3 hand-off — League Translation & Bayesian Performance Transfer

Repository: https://github.com/frenk4business/football-recruitment-intelligence. Phase 2 branch: `phase/02-player-dna`, based on the unmerged `phase/01-data-foundation` review boundary. Do not merge either PR automatically. Inspect current GitHub status before choosing the next base.

## Analytical evidence

Primary cohort: StatsBomb FA Women's Super League 2023/24, 132 matches, 12 teams, 336 roster players, 495,189 events. Pinned revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`. Source configuration and all 266 file hashes live in `config/cohorts.yaml` and `config/wsl_2023_24.sources.json`. Other WSL catalogue seasons: 2018/19 (4), 2019/20 (42), 2020/21 (90). They have not been ingested for Player DNA and do not form a continuous annual panel. The public source catalogue contains other competitions; run `uv run fri data discover statsbomb` and audit suitability/licensing before expansion. Provider IDs have only been checked within this selected season; no cross-season identity consistency assertion has been made.

The Phase 1 World Cup final and SkillCorner one-minute tracking sample still work in Data Explorer. They are not Player DNA inputs. There is no physical capacity model, cross-provider join, transfer dataset, valuation, club-fit ranking or league-strength estimate.

Canonical cohort partitions are ignored under `data/processed/cohorts/wsl_2023_24/matches/<source match ID>/`. Entities live at the cohort root. `player_feature_observation.parquet` retains competition, season, team, player, match, date, reliable minutes, quality reasons, role-minute shares and count/opportunity denominators. A player who changed teams retains all memberships. Public profiles aggregate across those memberships; team-specific observation rows remain available for future models.

## Features and representation

See `docs/player-features.md` and executable `dna/registry.py`: 18 behavioural features across shooting, creation, passing, carrying and defending. Open-play pass features exclude restarts. Progression reduces goal-centre distance by ≥max(10 reference metres,25%); no vendor-equivalence claim. xA requires reciprocal event links and provider shot xG. Nine output/context features remain outside the default vector. Zero and null are distinct.

`player-dna-v1`: at least 900 reliable minutes by default; controlled alternatives 450/600/1,200. Six separate roles at 900: CB 36, FB/WB 29, DM 22, CM 12, W 24, ST 15. No GK similarity or sparse AM similarity. At least 12 eligible members per role. Mean/population-SD scaling within role and threshold; no clipping. Five equal family weights, Euclidean distance over standardized features. Top 10 with deterministic tie-breaking, squared-distance contributions, role percentiles and 100-bootstrap inclusion/Jaccard stability.

Public contracts live in `dna/contracts.py`, generated TypeScript in `apps/web/src/lib/contracts.ts`, schemas/OpenAPI under `artifacts/`. `artifacts/phase2/public/` contains the small search index, lazy per-player/threshold details, map and evaluation summaries. Full evaluation/scalers/version/hashes are in `artifacts/phase2/similarity_evaluation.json` and `model_manifest.json`. Do not use browser artifacts as a substitute for match-level modelling evidence.

## Evaluation and cautions

Default: 89 paired queries, Recall@1 .472, @5 .843, @10 .944, MRR .636, bootstrap Jaccard .669. Random Recall@5 .337 and @10 .618 because candidate groups are small. Scalers fit first-window profiles only in temporal evaluation. Methods were selected using these experiments; there is no untouched test season.

Global robust scaling and naive weights beat some preferred design choices; hypotheses did not all succeed. Standard scaling improves the robust baseline. PCA does not consistently help; UMAP/xT/VAEP/contrastive learning are absent. Raising minutes shrinks cohorts and inflates top-10 overlap; within-threshold minutes–stability correlation is weak. Bootstrap samples players independently and do not preserve shared match/team dependence.

Minutes reconciliation: 5,067 agreeing, 25 reconciled, 10 conflicting player-match records (including unused-roster records in the first count). Conflicting records are excluded together with event counts. Role summaries remain a simplification. Team context is still a material confounder. Possession denominators count sequences, not time. Single-season within-competition consistency does not establish tactical meaning or transfer success.

## Run, validate and serve

`make setup && make test && make data-bootstrap && make data-validate && make phase2-build && make build`. Bootstrap is cached/checksummed; repeat research builds make zero source requests once cached. `uv run fri cohort build --max-matches 5` creates a separate development canonical snapshot. It must not replace the full-season public cohort. `make features`, `make similarity-evaluate`, `make similarity` separate costly stages. CI is offline and uses synthetic fixtures plus permitted derived artifacts, never a full download.

`make dev` serves the bilingual product; `make api` provides local FastAPI. Endpoints: `/api/v1/player-dna`, `/{player_id}?threshold=900`, `/{player_id}/similar?threshold=900&limit=10`, `/api/v1/similarity/evaluation`, `/api/v1/features`. IDs are allowlisted UUIDs and thresholds are controlled. Existing explorer endpoints remain. No public model API is required.

Render is static, no paid compute/database/disk. Existing service `srv-dauh12hsrm7s73c7uiu0`, tracking `phase/02-player-dna`; see `docs/deployment.md` and Phase 2 QA for the final deployment/branch state and verification links. Fixed project infrastructure is €0/month within workspace allowances; usage overages follow existing Render billing settings. Raw events, lineups and canonical Parquet must remain outside Git. StatsBomb requires attribution/logo for non-commercial analysis; code MIT does not change data rights.

Verified tests: 76 Python, four frontend unit and ten Playwright tests pass; the ten browser tests also pass against the live site. English: https://football-recruitment-intelligence.onrender.com/player-dna/. Dutch: https://football-recruitment-intelligence.onrender.com/nl/player-dna/. [PR #2](https://github.com/frenk4business/football-recruitment-intelligence/pull/2) records final review status and CI evidence. The clean rebuild reproduced all 1,351 public JSON files byte-for-byte and the feature-observation Parquet byte-for-byte, using 266 checksum-verified cached source files and no source requests.

## Recommended first Phase 3 task

Start with a **transfer-evidence feasibility and identity audit**, not Bayesian training. Determine which openly licensed competitions/seasons contain verified same-provider players before and after actual team/competition changes, enough reliable minutes in both environments, compatible event definitions and usable team-context denominators. Freeze an evaluation design with held-out destination periods/players before fitting hierarchical models. Audit identity stability explicitly rather than matching names. If there is insufficient cross-league evidence, state that limitation and design a narrower team-context or within-league transfer study. The next question is how much observed performance transfers when competition and team context change; Phase 2 does not answer it.
