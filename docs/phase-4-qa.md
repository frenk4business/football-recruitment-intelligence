# Phase 4 QA and release evidence

Branch `phase/04-recruitment-intelligence`, based on main `6051ce04da532381766c69b83773fd1fe4b732b1`. Existing baseline: 93 Python tests, four frontend unit tests and fourteen browser tests passed before changes. Chronological audit, registration, implementation, method-selection and final-evaluation commits are linked in the [evaluation](recruitment-fit-evaluation.md). No Phase 5 work is included.

## Completed local verification — 30 September 2026

- **114 Python tests passed** (21 added). Club aggregation uses actual team minutes; season isolation, duplicate rejection, missing-versus-zero, club-stint role medians/ranges/concentration, requirement validation, exact/min/max/neutral losses, hard constraints, evidence independence, deterministic ties/frontiers, weight/profile robustness, API errors and strict public allowlists are exercised. One pre-existing Starlette/httpx deprecation warning remains.
- **17 frontend unit tests passed**. Ten full Python-reference scenarios cover six roles, replacement, adjusted replacement, hard constraints and neutral/empty state. Ordering, distances, exclusions, explanations, Pareto membership, both sensitivity summaries and URL reconstruction agree within 1e-7. Invalid/unsupported URLs and EN/NL copy keys are checked.
- **20 Chromium browser tests passed**, including all fourteen earlier product tests and six new recruitment tests. EN/NL find/replace/context, club/role changes, requirements, shortlist, comparison limit, evidence/translation boundary, filters, share/locale/reset, invalid/empty states, network failure/retry, lazy bootstrap loading, mobile, keyboard and axe WCAG A/AA checks passed. No unexpected console/page/HTTP errors in normal workflows.
- Ruff lint/format, mypy (46 source files), ESLint, TypeScript, generated-contract check, static Next build and `git diff --check` passed. No dependencies or workflow permissions changed. Next emits both recruitment routes.
- Scientific reproduction compared every development/final query and all 205 registered robustness scenarios at 1e-10 tolerance; all reproduced. Frozen registration, selection and evidence remained unchanged. Current code-commit metadata is the only ignored reproduction field.
- Phase 2/3 artifacts and source feature/translation modules are unchanged against base main. Twenty public Phase 4 JSON artifacts validate against strict schemas and their manifest hashes; **1,562,322 bytes** total. Initial recruitment data is two requests, **232,781 bytes** uncompressed for index + Chelsea detail. Bootstrap role payloads are 86,204–261,232 bytes and load only when sensitivity is opened. These are payload measurements, not mobile latency guarantees.

Local logs: `/private/tmp/fri-phase4-all-checks.log`, `/private/tmp/fri-phase4-parity.log`, `/private/tmp/fri-phase4-browser-all.log`, `/private/tmp/fri-phase4-reproduce.log`. Screenshot artifacts remain local under `artifacts/local-qa/`; research figures are committed under `docs/figures/phase4/`. Desktop and mobile visual inspection covered requirements, candidate comparisons and club context, retaining the existing ivory/forest editorial style; mobile checks use 390×844 and desktop 1440×1000.

## QA corrections

Reference fixture generation originally encoded a replacement ID with find-mode metadata; corrected to replacement mode and added coherence validation. Scientific results reproduced unchanged. API comparisons use the documented floating tolerance because compact public artifacts round at eight decimals. Scrollable robustness/methodology/roster regions and exclusion lists are keyboard-focusable; automated accessibility checks passed after this correction. Keyboard automation exercises mode buttons and candidate selection rather than platform-dependent native-select popup keystrokes. The shortlist shortcut keeps eighteen-feature replacement workflows navigable.

## Rebuild and release checkpoint

Clean clone of product commit `6c777fc` passed `make setup`, `make test` (114 Python +17 frontend tests) and `make build` with no source or processed data. Then only the 413 MB raw WSL source cache was copied in: `make phase4-build` verified 266 source files with **zero network requests**, rebuilt all 132 canonical matches and features, and reproduced all twenty public artifacts, the manifest and reference cases **byte-for-byte**. The clean clone had no tracked diff; Phase 2/3 artifacts stayed unchanged. Logs are `/private/tmp/fri-phase4-clean-{setup,test,build,research}.log`.

[PR #4](https://github.com/frenk4business/football-recruitment-intelligence/pull/4) contains the chronological research commits. The completed hosted release is verified below. Render service inspection confirms `main`, `autoDeployTrigger=commit`, static-site type and Starter build plan; no new resource is required.

## Practical limits

Automated browsers cover Chromium, not Safari/Firefox or a manual screen-reader audit. Axe passing is not proof of complete accessibility. Bootstrap uncertainty excludes target/eligibility/shared-match dependence; rankings are descriptive and no expert relevance or transfer-success labels exist. Age/availability/fees are missing. No hosted backend or arbitrary historical-to-current translation is offered. [Model card](model-card-phase4.md) and [Phase 5 hand-off](phase-5-handoff.md) preserve these limits.

## Verified GitHub and production release — 30 September 2026

[PR #4](https://github.com/frenk4business/football-recruitment-intelligence/pull/4) merged from `phase/04-recruitment-intelligence`, preserving all scientific checkpoint commits. Reviewed head `01178ba5eee66e8502d6485eece538b260d82818`; release main `91884ed2e75253f4376d21bf022af5c75d937c79`. Both [PR CI 36757979847](https://github.com/frenk4business/football-recruitment-intelligence/actions/runs/36757979847) and [main CI 36758389371](https://github.com/frenk4business/football-recruitment-intelligence/actions/runs/36758389371) passed Python and web jobs.

Render deploy `dep-daul7t49v7es73bbhdl0` made the exact release main commit live at **18:25:43 UTC**. Service branch is `main`; type Static Site; build plan Starter; trigger commit. The existing service/workspace remains unchanged and no backend, worker, database, disk or other paid resource was added.

Both [English recruitment](https://football-recruitment-intelligence.onrender.com/recruitment/) and [Dutch recruitment](https://football-recruitment-intelligence.onrender.com/nl/recruitment/) returned HTTP 200 with the correct headings. All **twenty** live aggregate JSON files matched the committed manifest's SHA-256 hashes, totalling 1,562,322 uncompressed bytes. All **20 browser tests passed against production in 8.3 seconds**, including the earlier DNA/translation/explorer workflows and new EN/NL recruitment interactions, mobile, keyboard, error recovery and accessibility. Log: `/private/tmp/fri-phase4-production-browser.log`. [Machine-readable release evidence](../artifacts/phase4/deployment_check.json).

The freshly reconstructed source-cache clone also passed `make recruitment-evaluate`: every development/final result and all 205 robustness cases reproduced within 1e-10, with frozen files unchanged (`/private/tmp/fri-phase4-clean-evaluation.log`). Later documentation-only commits record this verification; they do not change the tested product. Resolve current main/Render for the latest documentation commit rather than treating the functional release SHA as an immutable branch head. Phase 4 is complete; Phase 5 has not started.
