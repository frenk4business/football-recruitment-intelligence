# Phase 2 hand-off — Player DNA & Similarity

## Starting point

- Repository: https://github.com/frenk4business/football-recruitment-intelligence
- Phase 1 branch: `phase/01-data-foundation`; preserve the review boundary against `main`.
- Implementation scope: data foundation only. No embeddings, similarity scores, league models or recruitment predictions.
- Python 3.12 with uv; Next.js/React/TypeScript with Node 24.19.0; both dependency lockfiles are committed.

## Architecture and files

`src/football_intelligence/data/` owns adapters, Pydantic canonical rows, coordinate/position normalization, bounded retrieval, validation and DuckDB marts. `pipeline.py` builds local Parquet and `export.py` creates publication-safe artifacts. `contracts.py` supplies both API models and generated TypeScript types. `api.py` is the local FastAPI service; `apps/web` is the bilingual static product.

Local tables: competitions, seasons, teams, players, matches, lineups, events, tracking_frames, tracking_objects, provider_entity_map, player_match, player_season, team_season. Storage: ignored `data/processed/*.parquet`. Source revisions/checksums: `config/sample.json`. Source rights: `config/data_sources.yaml`, `ATTRIBUTION.md`, `docs/data-sources.md`.

Actual sample: StatsBomb Argentina–France World Cup final (4,407 events, 50 roster players) and SkillCorner Western United–Sydney FC (60 seconds / 60 retained frames / 1,380 object positions, 36 roster players). These are different matches with separate provider identities. No broad cohort exists yet.

## Commands

```sh
git switch phase/01-data-foundation
make setup
make test
make data-bootstrap
make data-validate
make dev                 # web :3000, English /, Dutch /nl/
make api                 # optional local API :8000, docs /docs
make build
cd apps/web && npx playwright install chromium && cd ../..
make smoke
make contracts           # after public schema edits
```

`make test` is offline once dependencies are installed; CI uses only tiny synthetic fixtures and committed real research aggregates. Data bootstrap retrieves only pinned sample inputs. To query Parquet, use `data.marts.connect(Path('data/processed'))` or DuckDB directly. No secrets or hosted database are needed.

## API and public product

See `docs/api.md` and `artifacts/openapi.json`: health, coverage, sources, metrics, competitions, matches, players and explorer payloads only. The public product uses the same contracts as static JSON under `/data/`. Model version 1.0.0. English `/` and Dutch `/nl/` have overview, explorer, coverage, methodology and roadmap. The API is local, intentionally not deployed.

Live preview: https://football-recruitment-intelligence.onrender.com/ (Dutch `/nl/`). Render static service: `srv-dauh12hsrm7s73c7uiu0`, auto-deploy on commits to `phase/01-data-foundation`. Phase 1 review: https://github.com/frenk4business/football-recruitment-intelligence/pull/1. Final verification evidence is in `docs/phase-1-qa.md`: 46 Python tests, 4 frontend unit tests, 5 browser tests and remote CI. `render.yaml` declares the intended static CDN configuration. Direct integration creation does not automatically apply every Blueprint setting. No paid compute, database or disk is part of this project.

## Known evidence limits and technical debt

1. The cohort is intentionally tiny. The current adapters select one configured match per provider. Expand discovery/selection and entity deduplication across matches before building season features.
2. Six StatsBomb lineup minute intervals are inconsistent; five SkillCorner full-match minute entries are absent. They remain null. Two source-order timestamp inversions remain flagged. Investigate source event/substitution reconciliation with tests before relying on minutes; do not impute full matches.
3. The existing static sample cannot evaluate a similarity method or league translation. Select adequate position-specific player minutes, multiple matches and temporal splits first.
4. The local staged build assumes one writer and does not provide a transaction spanning Parquet and JSON publication. Revisit atomic snapshot activation if automated refresh is added.
5. One benign upstream TestClient/httpx deprecation warning remains; tests pass. Migrate when the FastAPI/Starlette client transition settles, without adding a second HTTP library solely to hide a warning.

## Recommended first Phase 2 task

Create a **cohort and feature eligibility report before fitting anything**: choose an appropriately licensed multi-match event cohort; implement bounded configurable multi-match ingestion and provider-entity deduplication; audit role coverage, reliable minutes, missingness and dates; define position-aware features and excluded observations. Reconcile minutes or exclude unreliable entries explicitly. Begin with standardized descriptive features and an interpretable distance baseline only after that report is reviewable. Assess sensitivity to minutes thresholds and time windows, and keep keeper/outfield roles separate.

Do not mistake supplied StatsBomb xG for this project's model. Never fuzzy-merge source identities, rank the tracking sample, infer commercial reuse rights from download access, or publish raw StatsBomb records. Preserve source scope, temporal provenance and non-commercial attribution throughout Phase 2.

## Phase 2 implemented

This document above preserves the starting hand-off from Phase 1. The completed continuation is on `phase/02-player-dna`; see [cohort](phase-2-cohort.md), [feature registry](player-features.md), [evaluation](player-similarity-evaluation.md), [method ADR](adr/005-player-similarity-method.md) and [Phase 3 hand-off](phase-3-handoff.md). The initial small-sample and interval-minute limitations are addressed for the separate WSL analytical cohort, with explicit remaining exclusions. Keep the original Phase 1 PR review boundary.
