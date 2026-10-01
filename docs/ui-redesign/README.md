# UI/UX redesign review

Baseline: `5e400cb3a81880bb91b0d8957da519e355b557a5` (v1.1.0). This update changes presentation and navigation; the scientific release version remains 1.1.0.

## A–B. Problems and information architecture

The previous UI gave project phases, source registers, technical controls and research methods the same prominence as player search. The header now has Players, Recruitment and Research; the author and version move to the footer. All 18 prior routes remain functional. New English and Dutch research hubs bring the total to 20.

## C. Home

Player, club and competition search is the primary action. Search submits a same-origin GET with the existing query-string format. The displayed profile count comes from the generated coverage artifact. Three restrained task links replace the phase tracker, source table and pipeline; the latter remain under Research. Logos and favicon are unchanged.

## D–E. Players and profiles

A search-first workspace puts results beside the selected profile on desktop, without automatic selection. Filters collapse behind a native disclosure, with an active summary and reset. Search includes accent-insensitive names, clubs and competitions without changing the result order. Selection and comparison survive language changes and URL restoration.

Overview, Playing style, Similar players and Data quality are sections in one profile. The original 900-minute WSL profiles supply their existing percentiles, with eight visible core metrics and all remaining metrics/rates available on demand. Other profiles show observed rates, not invented percentiles. Same-provider native comparisons and the three-feature descriptive common comparison keep their existing restrictions. Exact neighbour distances and provenance are secondary. The legacy DNA tool remains available, now accepting an explicit player deep link.

## F. Recruitment

Club → position → requirements → shortlist. Four or five role-relevant features are visible by default, with active requirements retained and all 18 available under Advanced requirements. Exact, minimum, maximum, ignore, hard constraints, family and feature weights remain intact. Results update live; a prominent action jumps to the shortlist. Desktop puts requirements alongside results. Candidate names open and focus the existing detailed comparison, showing contributions and separate evidence. Replacement requirements start collapsed. Club context is a separate mode. Ranking, fit distance, frontier membership and robustness calculations are unchanged.

## G. Research

Research links to Methodology, Coverage, Historical translation, Explorer, Evaluation and the full DNA view. Methodology has anchored contents and an evaluation conclusion before the expandable full results. Translation retains observed source, target and expected ranges, with calibration, evidence and model details in disclosures. No definitions, evaluation values or scientific conclusions were rewritten.

## H–I. Visual and mobile

Semantic color tokens, warm neutral background, white work areas, stronger heading hierarchy and denser rows preserve the existing restraint. There is no new icon library, photography or dark mode. At 760px and below the header uses the supplied emblem and a native keyboard-operable menu that also works without JavaScript. Mobile player selection becomes a detail view with a return action. Candidate tables become stacked rows; research tables retain intentional scrolling.

## J. Accessibility and recovery

Native form, search, select, button and details controls; semantic tables and labelled regions; visible keyboard focus; profile/candidate focus and return-to-results focus; reduced-motion compatibility; preserved network/integrity retries. The CSP now permits only same-origin form submission (`form-action 'self'`) so the new search works without JavaScript; all other directives are unchanged. No-JavaScript search and bilingual mobile navigation tests guard these behaviors.

## K. Performance

Chromium on an Apple M5 Pro, localhost, no network or CPU throttling, fresh browser context per route. Both locales at 1440 and 375px. Decoded resource bytes are not compressed transfer sizes. LCP is the median of the four locale/width observations, sampled after the initial render; these small local timings are not field Core Web Vitals. Each interaction sample includes Playwright automation overhead.

| Route | Initial JS bytes before → after | Initial JSON bytes before → after | Local LCP median, ms before → after |
|---|---:|---:|---:|
| Home | 642,085 → 474,646 | 0 → 0 | 26 → 24 |
| Players | 642,085 → 541,601 | 859,981 → 859,981 | 46 → 46 |
| Recruitment | 642,085 → 562,825 | 234,534 → 234,534 | 20 → 22 |
| Translation | 642,085 → 533,506 | 206,037 → 206,037 | 26 → 64 |
| Methodology | 642,085 → 561,906 | 0 → 0 | 30 → 30 |

Route-specific loading reduces initial JS on every measured route. JSON payloads are identical. Local LCP is not uniformly lower; every measured LCP remains at or below 88ms. These samples do not support a claim of statistically significant timing improvement or regression.

Player search fill-to-render median: 22.3 → 14.0ms. Recruitment requirement-to-shortlist median: 29.1 → 21.6ms. The production export remains below 65MB; public JSON remains 47,430,174 bytes under its 55MB budget. No full profile is fetched on initial player search.

Reproduce review captures with `node apps/web/scripts/ui-review.mjs after` while the static preview runs on port 4173. Optional `PREVIEW_URL` targets another deployment. JSON observations are retained in this directory; screenshots are in `artifacts/local-qa/ui-redesign/`.

## L. Validation

- `make test`: Ruff/format, mypy, ESLint, TypeScript, generated-contract checks, 148 Python tests and 27 frontend unit tests.
- Production build: 20 static routes, 5,119 allowlisted public artifacts.
- Browser suite: 162 passing tests across Chromium, Firefox and WebKit. Includes EN/NL search → profile → similarity → comparison, recruitment → requirements → candidate details, mobile menu → research → methodology, language state, axe, errors, native form CSP, metadata and favicon.
- Visual inspection: homepage, players, profile, recruitment, translation, methodology and research in both locales at 375/1440px. Responsive regression also covers 320/480/481/760/761/768/1280px.

## M. Scientific integrity

28,063 baseline file hashes checked, zero changed: data/artifacts, Python model sources and supplied brand assets. The release validator separately verifies 2,146 frozen research files and all 5,119 public artifact hashes. No dataset, model, ranking, threshold, evaluation or logo generation was run. See `integrity.json`.

## N–O. Delivery

Branch: `feature/ui-ux-redesign`. [PR #15](https://github.com/frenk4business/football-recruitment-intelligence/pull/15). Separate commits cover navigation, home, players, profile integration, recruitment, research and final QA. Publication follows the protected main-branch release gate and the existing Render service (`srv-dauh12hsrm7s73c7uiu0`), with checks-pass auto-deploy. The delivery record is supplied with the final PR/merge and production verification evidence.

## P. Screenshots

`artifacts/local-qa/ui-redesign/{before,after}-{en,nl}-{1440,375}-{home,players,profile,recruitment,translation,methodology}.png`.

The Research hub is new, so only after screenshots exist for it. Screenshots are review artifacts, excluded from the production export. All captured views report no document-level horizontal overflow.
