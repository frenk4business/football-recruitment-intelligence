# Public contracts

Run `make api`; visit `http://127.0.0.1:8000/docs`. `artifacts/openapi.json` is the committed contract. Source models live in `contracts.py`; run `make contracts` to regenerate the TypeScript types and schema snapshots.

| GET endpoint | Response |
|---|---|
| `/health` | Process status, data-ready boolean, version |
| `/api/v1/coverage` | Coverage and quality overview |
| `/api/v1/sources` | Attribution, licence links, revisions and limitations |
| `/api/v1/metrics` | Bilingual metric definitions, availability, formulas and epistemic type |
| `/api/v1/competitions` | Sample competition/season summaries |
| `/api/v1/matches?provider=statsbomb&limit=50&offset=0` | Filtered/paginated sample matches |
| `/api/v1/explorer/{match_id}` | One match's public aggregate payload |
| `/api/v1/players?match_id={uuid}&limit=25&offset=0` | Paginated roster/derived player summaries |

`provider` is an enum, match identifiers are UUIDs and allowlisted against the match catalogue, limits are 1–100 and offsets cannot be negative. Missing data artifacts return 503, invalid inputs 422, unknown matches 404. `/health` remains a process-liveness check and separately reports data readiness. No user SQL or filesystem path enters a query. Default CORS is `http://localhost:3000`, configurable via `FRI_CORS_ORIGINS`; no production wildcard is set.

The public static preview reads `/data/data_coverage.json`, `/data/sources.json`, `/data/matches.json`, `/data/metrics.json` and `/data/explorer/{uuid}.json`. These are the exact response models, generated at data-build time. There is no public live API in Phase 1. Raw event and tracking storage paths are not API inputs.

Contract version is 1.0.0. Breaking changes require incrementing the schema version and regenerating all artifacts and types together. Stale TypeScript generation fails CI. Field nullability expresses unavailable evidence, not zero.

## Phase 2 contracts

- `GET /api/v1/player-dna`: cohort/search index including all roster players and threshold exclusion reasons.
- `GET /api/v1/player-dna/{player_id}?threshold=900`: derived profile and evidence; threshold is one of 450, 600, 900, 1200.
- `GET /api/v1/player-dna/{player_id}/similar?threshold=900&limit=10`: at most 20 requested, currently up to 10 precomputed neighbours; excluded profiles return an empty list.
- `GET /api/v1/similarity/evaluation`: public method/threshold retrieval and stability summary.
- `GET /api/v1/features`: bilingual versioned registry.

Invalid UUIDs/thresholds/limits return 422, unknown valid player UUIDs return 404, unavailable artifacts return 503. No arbitrary path or SQL endpoint. Static equivalents live at `/data/phase2/index.json`, `/<threshold>/<UUID>.json`, `/evaluation.json`, `/features.json` and `/map-<threshold>.json`. The FastAPI process remains local.
# Phase 3 translation contracts

The optional local FastAPI exposes:

- `GET /api/v1/translation/models`: versions, scope, provider revision, periods and selected methods.
- `GET /api/v1/translation/environments`: bounded player/target/role index and metric labels.
- `GET /api/v1/translation/players/{player_id}`: observed environments and precomputed conditional scenarios.
- `GET /api/v1/translation/predict?player_id=…&source_environment=…&target_environment=…&target_role=…`: one exact precomputed scenario, including unsupported states. Invalid UUIDs return 422; unaudited players 404; unavailable combinations 422.
- `GET /api/v1/translation/evaluation`: all four methods’ held-out error and interval calibration.

The deployed static equivalents are `/data/phase3/models.json`, `index.json`, `players/{player_id}.json` and `evaluation.json`. There is no hosted FastAPI service and no request-time inference. Pydantic publication models forbid extra/raw fields and nonfinite values; generated TypeScript, JSON Schema and OpenAPI remain the contract source. Predictions distinguish selected `estimates` from `research_estimates`, observed source from expected target, and `empirical_predictive` from `posterior_predictive` intervals. Unsupported states contain no estimates. Evidence exposes numerical episode counts, pooling, pre-change context dates and unseen-team status. `used_as_development_outcome` identifies a source observation also used as an earlier fitted outcome.
