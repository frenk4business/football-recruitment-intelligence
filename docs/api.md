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
