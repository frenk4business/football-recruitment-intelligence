# Deployment and costs

One existing Render **Static Site** serves https://football-recruitment-intelligence.onrender.com/ from `frenk4business/football-recruitment-intelligence`.

- Service: `srv-dauh12hsrm7s73c7uiu0`, workspace `tea-d7ln8pbbc2fs73bkqpdg`.
- Actual build plan: **Starter**, within the user's existing paid workspace/resource context.
- Build: `cd apps/web && npm ci && npm run build`; publish: `apps/web/out`; Node 24.19.0.
- Secrets: none. Source downloads, Bayesian fitting and evaluation never run in the deployment build.
- Runtime: static HTML/CSS/JS plus validated derived JSON. FastAPI remains optional/local.
- No additional backend, worker, database, disk or production site was introduced.
- **No additional paid infrastructure was introduced beyond the existing Render subscription.** Shared build/bandwidth usage remains subject to existing billing settings; this is not a claim that the account costs €0/month.

Production tracks `main`, confirmed through the Render API after the user saved the Dashboard setting. Deploy `dep-daujukm7bikc73f1lscg` made main commit `9a92fcb2183b36f07c4aab178367bd1666b40ccf` live at 2026-09-30 16:57 UTC. Both translation routes and all 14 live browser tests pass; content/data checks were repeated against the main deployment. The installed integration cannot modify the Git branch, so the setting was changed in the Dashboard. Actual deployment evidence is in [Phase 3 QA](phase-3-qa.md).

The actual auto-deploy trigger observed at Phase 3 start is commit-based. The Blueprint's `checksPass` and security headers remain a target configuration, not a claim that they are applied to this independently created service. Completed PRs merge only after GitHub checks pass. Verify the deployed commit and both language routes after merge. No SPA catch-all is needed: Next exports directory indexes. Static delivery uses the global CDN, so no compute region is selected.

Phase 3 routes: `/translation/`, `/nl/translation/`, `/methodology/#translation`, `/nl/methodology/#translation`. Player DNA and explorer routes remain. Historical source observations and unsupported states are precomputed; no arbitrary public model parameters or inference endpoint are exposed.

Official references: [Render static sites](https://render.com/docs/static-sites), [Blueprint specification](https://render.com/docs/blueprint-spec). Source/data rights are independent of hosting costs and code licensing: [attribution](../ATTRIBUTION.md).
