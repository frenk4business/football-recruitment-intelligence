# Production deployment

Product: https://football-recruitment-intelligence.onrender.com/ (English and `/nl/`). Source: `frenk4business/football-recruitment-intelligence`; production branch `main`. Existing Render service `srv-dauh12hsrm7s73c7uiu0`, workspace `tea-d7ln8pbbc2fs73bkqpdg`, Static Site / Starter build plan. No second service or additional paid infrastructure.

Build: `cd apps/web && npm ci && npm run build`; publish `apps/web/out`; NODE_VERSION=24.19.0; NEXT_TELEMETRY_DISABLED=1; PR previews off. Actual environment values and zero redirect/rewrite rules were checked through the authorized API. Unknown routes return a genuine 404; there is no SPA catch-all.

On 2026-10-01 the actual service was changed from commit-triggered deploys to `checksPass`; branch remains main. Ten security/cache/indexing header rules were applied from the prepared configuration and verified on real HTML, hashed JS and stable JSON. `render.yaml` is a reviewable equivalent, not proof of synchronization for this independently created service. Its schema validates against Render's official published schema. See [security](security-v1.md) and [cache policy](caching.md).

Main is protected: PRs, up-to-date required `Release gate`, resolved review conversations, no force pushes/deletions, including administrator enforcement. A zero required-approval count accommodates the sole maintainer; this is not a claim of independent human review. CI tokens have contents:read. Dependabot security updates and vulnerability alerts are enabled; secret scanning and push protection remain enabled.

The [v1 release record](releases/v1.0.0.md), GitHub release assets and live `/release-manifest.json` identify the exact final main/deployed/tagged SHA. The preceding known-good deployment is `dep-daul9fo473hc739ojjlg` at `29beb4d4462dda37b6ec0abca82ac904cef9620d`; [rollback](rollback.md) describes recovery. Tagging is the final step after production verification, not a deployment trigger.

Fresh build prerequisites and commands are in [README](../README.md). Static product builds require dependency installation but no football-source network, secret or research cache. Full research refresh/fitting remains explicit offline work. Billing remains subject to the existing workspace/build/bandwidth plan; no exact invoice amount or remaining quota is claimed from connector metadata.
