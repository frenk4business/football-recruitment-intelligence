# Phase 1 verification — 30 September 2026

## Public project

- [English preview](https://football-recruitment-intelligence.onrender.com/)
- [Dutch preview](https://football-recruitment-intelligence.onrender.com/nl/)
- [Repository](https://github.com/frenk4business/football-recruitment-intelligence)
- [Phase 1 PR #1](https://github.com/frenk4business/football-recruitment-intelligence/pull/1), branch `phase/01-data-foundation`; not merged
- [CI runs](https://github.com/frenk4business/football-recruitment-intelligence/actions)
- Render service `srv-dauh12hsrm7s73c7uiu0`, workspace `tea-d7ln8pbbc2fs73bkqpdg`
- [Render dashboard](https://dashboard.render.com/static/srv-dauh12hsrm7s73c7uiu0)

The connected Render integration created a static site using `cd apps/web && npm ci && npm run build`, publish directory `apps/web/out`, Node 24.19.0. The applied automatic deployment trigger is **commit** on the Phase 1 branch. It is not Blueprint-managed: the stricter `checksPass` trigger and optional headers in `render.yaml` are reproducible target settings, not claimed as applied. The HTML/robots files independently mark this as a noindex preview. The API is local only. No database, paid compute, persistent disk or additional paid service was created. Static delivery uses the global CDN, not a selectable Frankfurt runtime.

## Verification evidence

| Check | Result |
|---|---|
| Fresh checkout `make setup` | Passed from committed lockfiles |
| Python Ruff lint/format, mypy | Passed |
| Python tests | 46 passed; source adapters, coordinates, schema, references, SQL, idempotency, API and export boundary |
| Frontend ESLint, TypeScript | Passed |
| Frontend unit tests | 4 passed |
| Next.js production static export | Passed; five sections in both languages |
| Chromium/Playwright | 5 tests passed locally and on the live preview |
| Accessibility | No axe WCAG 2.2 AA rule violations on ten pages; this is not full manual certification |
| Browser errors and assets | No unexpected console/page errors or HTTP asset failures in the ten-page live scan |
| Interactions | Source selection, search empty state, tracking slider, pagination controls, language switch, loading failure/retry state |
| Responsive layout | Actual desktop and 390 px mobile screenshots reviewed; no document-level overflow after navigation settles |
| Real source bootstrap from fresh checkout | Passed; both sources retrieved directly with pinned checksums |
| Reproducibility | Canonical Parquet checksums match across fresh downloads; public explorer JSON byte-identical on repeat builds |
| Render Blueprint | Validated against `https://render.com/schema/render.yaml.json` |
| GitHub Actions | Python and web jobs passed remotely; final branch runs remain linked above |
| Git audit | No raw provider files, local Parquet/DuckDB, .env, caches, credentials or unexpectedly large tracked files |

A first end-to-end run caught two test-selector issues; those were fixed. Live verification caught a navigation-timing race in the mobile assertion; the test now waits for translated content and settled width. Reproducibility checking caught unstable ordering of equal-count event categories; an explicit secondary sort and byte-level regression check now cover it.

One upstream FastAPI/Starlette TestClient deprecation warning advises a future httpx2 transition. It is a warning, not a failing check; see the hand-off for follow-up.

## Real data quality

| Provider | Matches | Roster players | Events | Frames | Objects |
|---|---:|---:|---:|---:|---:|
| StatsBomb | 1 | 50 | 4,407 | unavailable | unavailable |
| SkillCorner | 1 | 36 | unavailable | 60 | 1,380 |

StatsBomb: 29 events without player identifiers, two timestamp inversions in provider order and six inconsistent minute intervals retained as unavailable. SkillCorner: five absent full-match minute entries; 448 object observations marked not detected. No missing evidence is silently replaced with zero.

A measured warm offline build took about **0.50 seconds** on this development machine. The 13 Parquet files total **1,167,276 bytes**; both public explorer payloads total **359,762 bytes** uncompressed. This is a small-sample observation, not a full-dataset benchmark. The browser receives only the selected match artifact.

## Cost boundary

Fixed recurring infrastructure cost for the created project: **€0/month**. Static-site traffic and build minutes share the existing Render workspace allowance; overages may be billable under its current billing settings. No billing plan or spend limit was changed. Existing unrelated services are excluded from this project cost statement.
