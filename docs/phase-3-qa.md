# Phase 3 verification and release record

## Local verification

Phase 1/2 baseline was checked before edits: 76 Python tests, four frontend unit tests and ten Playwright tests passed. Final Phase 3 local checks pass:

- **93 Python tests**, including two-chain synthetic known-effect recovery/partial pooling, exposure uncertainty, provider identity/adjacency, cache tampering, source-context time cutoff, training-only baseline fitting, frozen selection and publication/API guards.
- **Four frontend unit tests** and **14 Playwright tests** across the original and new workflows.
- Ruff lint/format, mypy (35 source files), generated contracts, frontend lint/types and production static export.
- EN/NL translation selection, supported target changes, role/season rejection, visible predictive ranges/evidence, research comparison, error/retry, empty search, methodology links, keyboard operation and 390px mobile overflow checks.
- Axe WCAG A/AA scans passed in both languages and mobile; browser tests detected no unexpected console errors or HTTP failures. The deliberate failed-fetch test verifies retry separately.
- Desktop (1440px) and mobile (390px) screenshots were inspected. Observations and expectations remain distinct; ranges are prominent, context/selection limitations visible, and no recommendation score is shown. Local screenshots remain ignored in `artifacts/local-qa/`.

The new tests initially caught a select-label lookup issue and a test that chose the intentionally unsupported Aston Villa historical target. Explicit accessible labels and a supported-target test fixture resolved these. No scientific result or unsupported-state rule was loosened to make a test pass. The existing Starlette/httpx deprecation warning is non-failing; the locked stack works, with no unrequested dependency migration.

## Scientific and clean-build checks

The experiment and priors were committed before real-outcome fitting. Selection was frozen at `a330893` before the held-out evaluation recorded at `a624590`. The selected defaults are ridge for shots/passes and unchanged source for carries/pressures; no Bayesian model met every selection rule. Full results, including negative findings, are in [evaluation](league-translation-evaluation.md).

`uv run python scripts/phase3_reproduce.py` moved the entire processed Phase 3 directory aside, regenerated both provider audit marts and all WSL features/environments from verified raw caches with `httpx.Client.send` disabled, then compared outputs. **11 processed files matched byte-for-byte**, including both observation/context Parquet files. Source manifests match immutable source hashes; the implementation fingerprint can change when source code is reformatted. An initial verification attempt incorrectly compared missing separately generated audit outputs and an older code fingerprint; the corrected script explicitly regenerates audits and distinguishes source bytes from code provenance.

All **663 public JSON files matched byte-for-byte**, with **zero source requests**. Four fresh four-chain primary fits passed diagnostics and reproduced every held-out expected rate exactly on the locked local CPU stack (maximum difference 0.0; documented acceptance tolerance 0.03 per90). Cross-platform draws need not be bit-identical. [Machine-readable reproduction](../artifacts/phase3/reproducibility.json).

All final primary/sensitivity sampling diagnostics pass; zero primary divergences, max R-hat 1.0055, minimum key bulk ESS 943. Prior predictive gates pass after logged pre-fit alternatives. Overall PPCs pass, but seven small role/team variance/tail flags and held-out shot/pass undercoverage remain. There was no test-based retuning.

## Publication and payload

Strict Pydantic allowlists reject raw payload fields and nonfinite values. Every player file validates, ordered ranges are checked, unsupported scenarios have no estimates, context dates precede source cutoffs and method selections match the committed validation artifact. Per-file hashes appear in the publication manifest. Raw events, lineups, Parquet and full posterior draws are excluded from Git/static publication.

Four primary posterior files: 24,075,533 bytes, local only. Public Phase 3 JSON: 14,264,797 bytes across 663 files. Largest player summary: about 121 KB. The initial page fetches **one** player file, not all players or posterior arrays.

Measured static English HTML: 166,942 bytes (52,663 gzip); Dutch HTML: 166,039 bytes (52,627 gzip). Eight declared bootstrap script references total 655,121 bytes (201,324 gzip), including the legacy polyfill; modern browsers may skip that polyfill. Default player detail: 118,916 bytes (7,198 gzip); standalone index: 92,404 bytes (25,665 gzip). CDN compression, prefetch and HTTP overhead affect actual transfer. [Payload measurements](../artifacts/phase3/payload.json). No images or model samples are loaded for the interval charts.

## GitHub and deployment

[PR #3](https://github.com/frenk4business/football-recruitment-intelligence/pull/3), `phase/03-league-translation` → `main`, merged after green CI. The release evidence is recorded below. `main` already contained Phases 1 and 2 at `3d8f9a4`.

The existing Render static service is `srv-dauh12hsrm7s73c7uiu0`, Starter build plan, in workspace `tea-d7ln8pbbc2fs73bkqpdg`. No additional paid infrastructure was introduced beyond the existing subscription. The installed connector has no branch-update tool, so the Dashboard change was requested from the user. YAML targets `main`, but the actual service branch is checked separately below.

Live English route: https://football-recruitment-intelligence.onrender.com/translation/; Dutch: https://football-recruitment-intelligence.onrender.com/nl/translation/. No second site was created and no paid backend/worker/database was added.

## Verified GitHub release — 2026-09-30

PR #3 merged successfully with its scientific checkpoint history preserved. Release main commit: `7e2927a72544eb18f55aa269d42bde1cee27da4b`; reviewed head: `52911e1137503f9e113c45a08346cd7b5004a375`. Both [PR CI run 36745380996](https://github.com/frenk4business/football-recruitment-intelligence/actions/runs/36745380996) and [post-merge main CI run 36745723441](https://github.com/frenk4business/football-recruitment-intelligence/actions/runs/36745723441) passed Python and web jobs. Local main was fast-forwarded to the release and was clean before adding this release record.

The earlier 16:39 UTC check found 404s because Render still tracked the Phase 2 branch. A Dashboard change then deployed the reviewed Phase 3 implementation: `dep-daujo8hsrm7s73chap0g`, commit `52911e1137503f9e113c45a08346cd7b5004a375`, live at 16:44 UTC. At 16:50 UTC the homepage and both translation routes returned HTTP 200 and matched the tested local visible text. Model metadata and player index match the local export byte-for-byte. Full HTML differs in build-specific Next.js IDs/chunk references, so raw HTML byte equality is not an appropriate cross-build check. [Recorded production checks](../artifacts/phase3/deployment_check.json).

All **14 Playwright tests passed against the live Render URL** in 8.7 seconds, covering English/Dutch routes, supported and unsupported translation scenarios, Player DNA/explorer regressions, error/retry, keyboard, mobile overflow and Axe accessibility. Main documentation commit `3ddbb38c09b24e24c41a1ff1d222e9348f065299` also passed [CI run 36746052777](https://github.com/frenk4business/football-recruitment-intelligence/actions/runs/36746052777).

Research, implementation, local/live QA and GitHub merge are complete. **Production branch alignment remains pending:** despite the requested `main`, the Render API currently reports `phase/03-league-translation`. The user has been asked to select and save `main`. The connector cannot edit this setting. Verify the resulting main deployment before treating the release configuration as complete; no new application tests are required merely for documentation-only differences.
