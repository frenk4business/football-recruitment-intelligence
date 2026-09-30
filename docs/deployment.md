# Deployment and costs

One existing Render **Static Site** serves https://football-recruitment-intelligence.onrender.com/ from `frenk4business/football-recruitment-intelligence`.

- Service: `srv-dauh12hsrm7s73c7uiu0`, workspace `tea-d7ln8pbbc2fs73bkqpdg`.
- Actual build plan: **Starter**, within the user's existing paid workspace/resource context.
- Build: `cd apps/web && npm ci && npm run build`; publish: `apps/web/out`; Node 24.19.0.
- Secrets: none. Source downloads, Bayesian fitting and evaluation never run in the deployment build.
- Runtime: static HTML/CSS/JS plus validated derived JSON. FastAPI remains optional/local.
- No additional backend, worker, database, disk or production site was introduced.
- **No additional paid infrastructure was introduced beyond the existing Render subscription.** Shared build/bandwidth usage remains subject to existing billing settings; this is not a claim that the account costs €0/month.

Production's target branch is `main`; `render.yaml` now declares it. At the start of Phase 3, the actual service still tracked `phase/02-player-dna`. The installed Render integration can inspect/deploy the service but cannot modify its Git branch, and no Render API/CLI credential is available. A Dashboard branch change to `main` was requested from the user. Final observed branch/deploy state belongs in [Phase 3 QA](phase-3-qa.md); this document does not treat editing YAML as proof that the independent service configuration changed.

The actual auto-deploy trigger observed at Phase 3 start is commit-based. The Blueprint's `checksPass` and security headers remain a target configuration, not a claim that they are applied to this independently created service. Completed PRs merge only after GitHub checks pass. Verify the deployed commit and both language routes after merge. No SPA catch-all is needed: Next exports directory indexes. Static delivery uses the global CDN, so no compute region is selected.

Phase 3 routes: `/translation/`, `/nl/translation/`, `/methodology/#translation`, `/nl/methodology/#translation`. Player DNA and explorer routes remain. Historical source observations and unsupported states are precomputed; no arbitrary public model parameters or inference endpoint are exposed.

Official references: [Render static sites](https://render.com/docs/static-sites), [Blueprint specification](https://render.com/docs/blueprint-spec). Source/data rights are independent of hosting costs and code licensing: [attribution](../ATTRIBUTION.md).
