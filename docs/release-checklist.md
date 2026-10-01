# Release checklist

- [ ] Production audit and preimplementation release gate committed; all required findings closed.
- [ ] Canonical VERSION updated deliberately; npm mirror/lock matches; seven scientific versions and frozen results unchanged or separately versioned with approval.
- [ ] Locked setup, Python 3.12/3.13 quality/tests, frontend quality/unit/parity, schema/OpenAPI and public hash validation pass.
- [ ] Chromium/Firefox/WebKit, accessibility/keyboard/magnification/reduced motion/recovery/old URLs pass.
- [ ] Performance budgets and full output/publication bounds pass; no eager optional payloads.
- [ ] npm/Python audits and current/history secret review pass; source rights/attribution confirmed.
- [ ] Fresh checkout without research caches builds and validates; artifact hashes match; variability documented.
- [ ] README/changelog/release notes/operations/rollback/evidence updated; known negative findings preserved.
- [ ] PR checks green; merge to main; verify main CI; wait for Render checked-main live deploy.
- [ ] Live route/control/assets/header/console matrix and exact main==Render==manifest SHA verified.
- [ ] Create annotated v1.0.0 tag at that SHA only now; publish GitHub Release with manifest and final QA evidence.
- [ ] Confirm tag workflow validates only, exact tag/main/live identity and release links. Do not move tag or commit more changes to conceal a failed gate.

Use [release gate](release-gate-v1.md) for exact thresholds and [QA](v1-release-qa.md) for the completed evidence. This reusable checklist is intentionally unchecked; the release-specific report records execution.
