# Deployment and costs

The deployed public service is one **Render Static Site** at https://football-recruitment-intelligence.onrender.com/, connected to `frenk4business/football-recruitment-intelligence`, branch `phase/02-player-dna`. The review branch remains separate from `main`; it is not automatically merged.

- Build: `cd apps/web && npm ci && npm run build`
- Publish: `apps/web/out`
- Runtime: static HTML/CSS/JS, Node 24.19.0 for builds
- Secrets: none
- Environment: `NODE_VERSION=24.19.0`, `NEXT_TELEMETRY_DISABLED=1`
- Data: committed validated aggregate artifacts; deployment never downloads source tracking files
- Routing: generated directory indexes, English `/`, Dutch `/nl/`; no SPA catch-all
- Indexing: noindex research preview
- Regions: static delivery is global CDN, so Frankfurt is not a selectable service region
- Backend: FastAPI local only; no hosted database, disk, worker or paid compute

`render.yaml` records the reproducible target configuration, including security headers and deploy-after-checks intent. Direct MCP creation supports only a subset of that configuration; actual applied settings are recorded in [Phase 1 QA](phase-1-qa.md). A YAML file does not prove its headers or auto-deploy policy are applied to an independently created service.

The project's fixed recurring infrastructure charge is **€0/month**. Render static sites share workspace bandwidth and build-minute allowances. Excess use can be billed depending on the existing workspace plan/settings; this task does not change billing limits or upgrade the workspace. Avoid enabling paid service plans and review the existing workspace spend cap before treating any free hosted preview as an unlimited zero-cost guarantee. Existing unrelated Render services are outside this project's cost claim.

Official references: [free services](https://render.com/docs/free), [static sites](https://render.com/docs/static-sites), [Blueprint specification](https://render.com/docs/blueprint-spec). GitHub Actions uses small offline fixtures plus committed analysis JSON. No large data ingestion runs per commit.

## Phase 2 release

The existing Render static service `srv-dauh12hsrm7s73c7uiu0` now tracks `phase/02-player-dna` (verified through the Render integration). The service's actual trigger remains commit-based; the optional Blueprint `checksPass`/headers are still declarative rather than claimed as applied. Build/publish paths and Node version are unchanged. No additional service, paid instance, database or disk was provisioned. Fixed project infrastructure remains €0/month within the existing workspace allowances; existing overage billing settings were not changed.

Routes: https://football-recruitment-intelligence.onrender.com/player-dna/ and https://football-recruitment-intelligence.onrender.com/nl/player-dna/. Local FastAPI remains optional and is not hosted. Research source downloads and model evaluation never run in the Render build. A branch switch was required because the installed Render connector can inspect/deploy services but cannot modify their configured Git branch. The user changed this existing setting in the Dashboard; no new deployment credential was requested.
