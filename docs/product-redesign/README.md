# Product workspace redesign

Baseline: `5c939eafa43cbf467edbc36f06909559dabe46aa` (scientific release 1.1.0).

## Audit and implementation plan

The existing Next.js static export has 20 EN/NL routes, a shared server shell and route-specific client tools. Compact SHA-verified public indices support local search; individual profiles and WSL percentiles load on selection. Recruitment uses the original validated WSL cohort and unchanged pure TypeScript scoring with Python parity. Existing provider restrictions, thresholds and legacy routes remain authoritative.

The current horizontal header, large home typography, hidden primary filters, two-profile comparison and visible hard-constraint controls obstruct the requested workstation flow. Preserve the native mobile menu, keyboard focus, no-JavaScript research navigation, artifact retries and query-string compatibility. There is no supplied mockup file in the latest attachment directory; the written brief is the available design reference.

1. Introduce a 212px dark sidebar, compact search bar and native mobile navigation; keep supplied branding intact.
2. Compact the home entry and show factual generated coverage.
3. Expose primary player filters; improve row scanning and grouped playing-style metrics.
4. Extend the existing comparison query contract to three players, retaining old links and scientific comparability.
5. Simplify recruitment controls with exact mappings to existing scenario preferences; retain every advanced control.
6. Lead Research with existing evaluation conclusions and links to full evidence.
7. Verify EN/NL desktop/tablet/mobile, keyboard, errors and all existing science/security regressions. Measure fresh-context resource transfer, decoded JS, local LCP/CLS and interactions before/after. Screenshots are local review evidence, not production assets.
8. Separate commits, protected PR, merge and checks-pass Render deployment; verify the actual production export and all routes.

No new datasets, runtime services, UI framework, fabricated metrics, imagery, accounts or persistence. No release tag.

## Implemented product behavior

### A–B. Initial UX and information architecture

The previous redesign had already reduced the top-level choices to Players, Recruitment and Research. This iteration retains that hierarchy but replaces the website header with an application shell. All 20 public language routes and legacy analytical tools remain available. No account, notification, report, settings or persistence UI was invented.

### C–D. Application shell and entry

The dark sidebar is 212px (200px on smaller desktops). The existing reversed artwork has a lossless 360px display copy, avoiding a 441KB social image download for a small mark. Original branding and favicon files are unchanged. Mobile uses the standalone emblem and native Menu disclosure; navigation and the same-origin search form work without JavaScript.

The top search bar is sticky on desktop. Its verified compact index and integrity code load only on focus; suggestions group actual players, clubs and competition names, including provider aliases. Native links support direct profiles and existing database filters. No full player detail loads for suggestions. The home entry now has a compact title, two task actions, a generated profile/competition-season summary and a restrained trust line.

### E. Discovery

Search precedes six primary filters. More filters contains profile availability; the active summary and reset remain visible. Rows prioritize name, team and role, followed by competition, season, minutes and provider. Name/minutes sorting only changes browsing order, never a scientific ranking. Pagination remains 50 profiles. Desktop has a selected-profile pane; narrower workspaces stack, and mobile selection opens a dedicated detail with focus restoration on return.

### F. Profile

The profile leads with identity and evidence, then sections for playing style, similar players and data/methodology. Validated WSL profiles show ten existing percentile values grouped into five meaningful families; observed rates and definitions stay in a disclosure. No percentile was computed for an unsupported profile. Common profiles retain exactly three harmonised features, and native metrics retain their provider-specific definitions. One concise notice explains why cross-provider rankings are unavailable.

### G. Comparison

Up to three profiles share a metric-by-player table. Existing `profile`/`compare` URLs remain valid; `compare2` adds a third, with validation and duplicate rejection. A bounded native picker and comparison search work on mobile as well as desktop. Minutes, team/season/provider context and explicit comparability notes accompany selections. Adding comparison collapses the single-player percentile panel so comparable observed rates come first. Native metric columns are shown only for the selected provider; unsupported common comparisons fail closed. No winner, fake match percentage or aggregate confidence is introduced. Selection, language changes and browser back/forward are covered by tests.

### H. Recruitment

The existing Club → Role → Requirements → Shortlist flow now shows Ignore / Similar to / At least as simple preferences. They map exactly to neutral / exact / minimum. Existing maximum scenarios remain visible; all four modes, weights, hard constraints, evidence filters and all 18 core features remain available to expert users. Neutral rows omit a disabled target input visually; advanced source/club references remain available. An explicit notice identifies scenarios containing advanced weights or hard constraints.

Switching presentation does not change the encoded scenario or rankings. Scenario changes now create browser history entries; back/forward decodes the same validated contract and clears stale candidate selections. The live-update explanation and Find candidates action remain explicit. Candidate selection focuses an explanation titled “Why this player appears here”; multiple candidates retain the existing comparison. Distance, evidence, frontier membership and ranking stability remain separate. Replace mode starts with its requirement adjustment collapsed. Existing unsupported-role URLs still fail closed.

### I. Research

Research opens with bounded conclusions supported by the existing evaluations: within-season similarity consistency; no evidence for broad cross-league translation; recruitment signal above chance without consistent improvement over Player DNA. Each conclusion links to its relevant full evaluation. Historical translation, explorer, coverage, sources and legacy DNA remain accessible. The historical WSL-only translation warning, observed/expected ranges, calibration findings and all detailed evaluations remain intact.

### J–K. Responsive design and accessibility

EN/NL screenshots cover home, discovery, selected profile, three-profile comparison, recruitment and research. Profile/comparison captures include 1440, 768 and 375px. Existing tests additionally check 320–1280px breakpoints, 200% zoom and reduced motion. The responsive review reduced mobile setup height, retained native controls and made the scrolling Dutch coverage table explicitly keyboard-focusable. Safari pointer blur no longer removes a result link before its click completes. Focus styles, skip navigation, profile/candidate focus, table semantics, retry/error announcements and no-JavaScript navigation remain tested. Loading reserves the first player-workspace viewport to avoid pushing the footer out of view when data arrives.

### L. Performance before/after

Fresh Chromium contexts on an Apple M5 Pro, localhost with the existing static server, no throttling, EN/NL at 1440/375px. Each cell is the median of four observations; sampling begins at navigation and ends 350ms after load. Resource `transferSize` includes navigation and fetched resources; JS bytes are decoded script bytes, not transfer bytes. CLS sums non-input layout shifts within this short observation window. Interaction timings include Playwright overhead. The final measurement ran without concurrent browser tests.

| Route | Decoded initial JS bytes | Initial transfer bytes | LCP ms | CLS |
|---|---:|---:|---:|---:|
| Home | 474,646 → 480,412 | 297,363 → 299,898 | 26 → 34 | 0.0000 → 0.0000 |
| players/ | 541,601 → 549,988 | 405,986 → 407,958 | 48 → 54 | 0.2131 → 0.0000 |
| recruitment/ | 562,825 → 569,479 | 365,477 → 367,764 | 22 → 26 | 0.0114 → 0.0127 |
| translation/ | 533,506 → 539,267 | 412,790 → 414,449 | 68 → 70 | 0.2352 → 0.0000 |
| methodology/ | 561,906 → 580,882 | 259,209 → 265,618 | 32 → 34 | 0.0000 → 0.0000 |
| research/ | 474,646 → 480,412 | 298,152 → 301,200 | 22 → 26 | 0.0000 → 0.0000 |

Player search: 15.0 → 15.1ms median. Player filter: 6.2 → 6.9ms median. Recruitment requirement to results: 20.0 → 21.2ms median.

Global search adds about 5.8KB of decoded initial home UI code; its artifact/integrity logic is deferred. Public JSON payloads and model work are unchanged. Reserving loading space reduces observed player and translation layout shifts to zero in these samples. LCP and interaction differences are small local observations, not evidence of a statistically significant change. Full observations are in `before.json` and `after.json`. Run `node apps/web/scripts/product-review.mjs after` against the static preview to reproduce captures. Profile/comparison baseline screenshots reuse prior delivery captures of the same baseline implementation. Review `artifacts/local-qa/product-redesign/gallery.html` for side-by-side screens.

### M. Scientific integrity

`integrity.json` records 28,064 unchanged baseline file hashes, including source data/artifacts, Python scientific sources, the pure TypeScript recruitment implementation and existing brand files. The release validator also checks all 2,146 frozen research files and 5,119 allowlisted public JSON artifacts (47,430,174 bytes). No model, feature, threshold, ranking semantics, evaluation result, provider boundary or dataset was regenerated. Scientific release version remains 1.1.0; no tag is created.

### N. Validation

- Ruff checks and formatting: 95 Python files; mypy: 57 source files.
- ESLint, TypeScript, Prettier and generated contract validation pass.
- 148 Python tests and 28 frontend unit tests pass.
- 180 browser tests pass across Chromium, Firefox and WebKit (60 per browser), including EN/NL, accessibility, native navigation, malformed artifact recovery, share URLs and all legacy routes.
- Static production build and publication validation: 20 routes; approximately 57.3MB export, below the 65MB limit. Public JSON remains below 55MB.

### O–P. Delivery

Branch: `feature/product-ui-redesign`. Separate commits cover shell/search, discovery/comparison, recruitment/research, browser fixes and final performance refinement. A protected PR targets main. The existing Render static service tracks main and deploys after checks pass; service configuration, security headers and billing are unchanged. The final delivery record contains PR, merge SHA, CI, deployment and production-verification results.

### Q. Remaining UX limitations

The referenced mockup image was not present in the attachment directory, so visual review follows the written brief and actual product capabilities. This is not a field usability study. Most expanded profiles have observed rates rather than validated WSL percentiles; manual comparison is constrained by available providers/features. Recruitment remains historical WSL research rather than a current transfer market. The mobile advanced editor is necessarily long, and three-way comparisons can require table scrolling on very narrow screens. Search results are capped for scanability, with full database search available. Existing analytical CSS is preserved under the new workspace layer; further consolidation is possible without changing this release. Performance samples are local observations, not field Core Web Vitals or proof of a statistically significant speed improvement.
