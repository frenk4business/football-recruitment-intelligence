# Operating v1

Owner: repository maintainer Frenk Kester. Product: [live site](https://football-recruitment-intelligence.onrender.com/). Source: `frenk4business/football-recruitment-intelligence`. Production is one existing Render Static Site (`srv-dauh12hsrm7s73c7uiu0`) in workspace `tea-d7ln8pbbc2fs73bkqpdg`, built from main using the existing Starter build plan. No infrastructure or subscription expansion is needed.

The build installs locked npm packages, validates committed research aggregates, exports Next.js HTML/JS/CSS and generates an integrity inventory. Scientific processing remains local/offline. Python/FastAPI is an optional local research interface bound to 127.0.0.1; there is no public `/api`, model inference service, authentication system or writable production data store.

Release sequence: follow [checklist](release-checklist.md), inspect all CI jobs and baseline locks, merge PR, wait for checked-main Render deploy, compare exact SHA, run production smoke and performance/headers/hash checks, then tag and publish. The tag workflow only validates; it never creates another deploy path. Do not publish a tag while mandatory gates/settings are pending.

For incidents, record impact and evidence without secrets, reproduce with the static export, identify the smallest reversible fix, and stop release tagging until checks pass. For a broken public page or mismatched scientific artifact, use [rollback](rollback.md) promptly. A missing source feed does not prevent the existing static product from operating; research refreshes are separate authorized work. Never “fix” a released result by editing a JSON score.

Recurring duties and privacy are in [monitoring](monitoring.md); dependencies in [dependency policy](dependency-policy.md); browser cache behavior in [caching](caching.md). Render builds and GitHub tests consume existing included quotas. Monitor their actual billing dashboards; exact subscription charges/limits are not available through this session's tools. Do not describe the project as cost-free merely because no extra service was created.
