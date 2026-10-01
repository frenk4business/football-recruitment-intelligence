# Performance v1

Budgets were fixed in [release gate](release-gate-v1.md) before implementation. [Baseline](releases/evidence/performance-baseline.json) and [local hardened measurement](releases/evidence/performance-local.json) retain raw observations. Exact final production measurements are attached to the GitHub v1.0.0 release as `production-performance.json`, alongside the final commit/deploy evidence. The local report identifies committed candidate a8f05d6; it is a premerge measurement, not the tagged release identity.

Profile: Apple Silicon macOS 26.6.2, Playwright Chromium, 375×812 CSS viewport, device scale 1, cold browser cache, 4× CPU throttle, 150ms emulated latency, 1.6Mbps down / 750Kbps up, five seconds observed after load. Hardened measurements use three runs per route; baseline used one exploratory run. Local gzip static server reproduces the cache/security rules; the final report uses the actual Render CDN. These are controlled lab measurements, not real-device or field Core Web Vitals claims. Long-task blocking sums duration above 50ms within the observation window; it is a synthetic TBT proxy, not a Lighthouse score or field INP.

| Route | Local median LCP (ms) | Max CLS | Median blocking (ms) | Initial JS gzip (bytes) | Initial fetched JSON decoded (bytes) | Max transfer (bytes) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| / | 516 | 0.0000 | 21.0 | 179131 | 0 | 311294 |
| /player-dna/ | 532 | 0.0000 | 14.0 | 179131 | 73485 | 382873 |
| /translation/ | 520 | 0.0000 | 13.0 | 179131 | 206037 | 406617 |
| /recruitment/ | 496 | 0.0000 | 19.0 | 179131 | 234534 | 351716 |
| /methodology/ | 544 | 0.0000 | 18.0 | 179131 | 0 | 239442 |

Recruitment requirement input-to-visible-ranking median: 32.2ms under the same CPU profile (budget <200ms). All local measured route budgets pass. Baseline recruitment CLS was 0.2254; reserving initial workspace removes that measured shift. Home document overflow was repaired; navigation and wide evidence tables remain contained scroll regions.

Initial JS is measured by downloaded script bodies recompressed with Node gzip, not by summing every chunk in the full export. Stable client code is shared across routes; it is already below the 250KB cap, so no speculative dependency or chart-framework rewrite was warranted. Navigation prefetch is disabled to avoid loading all research routes in the background. No remote fonts or heavy charting package is included. Ajv runs only at build time and is absent from browser bundles.

JSON counts include the small, lazy integrity index and selected data files. Server-rendered initial indexes are reflected in HTML/overall transfer rather than miscounted as JSON fetches. PCA, additional player profiles and role bootstrap sensitivity remain lazy; browser tests assert the optional bootstrap is absent before expansion. Largest public JSON is 328,088 bytes; complete public JSON is 36,277,787 bytes spread across 2,041 files, and is never fetched as a whole. Clean static export at the reproducibility checkpoint is 43,306,915 bytes, below 50MB.

Run `node scripts/serve.mjs` from apps/web, then `node scripts/performance.mjs` in another shell. For production set PREVIEW_URL and PERFORMANCE_REPORT; the command writes raw/summary JSON and fails its fixed budgets. Run performance measurements without competing heavy tests for final evidence. Network variability and host CPU remain limitations; no fabricated Lighthouse score or universal performance guarantee is reported.
