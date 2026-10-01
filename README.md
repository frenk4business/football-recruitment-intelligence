# Football Recruitment Intelligence

[![Checks](https://github.com/frenk4business/football-recruitment-intelligence/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/frenk4business/football-recruitment-intelligence/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/frenk4business/football-recruitment-intelligence)](https://github.com/frenk4business/football-recruitment-intelligence/releases)

A bilingual, non-commercial football research product: open-data provenance, observed Player DNA, historical translation evidence, and explicit recruitment requirements. Rankings describe observed similarity under chosen criteria; they are not transfer recommendations or success predictions.

**[Open the product](https://football-recruitment-intelligence.onrender.com/)** · [Nederlands](https://football-recruitment-intelligence.onrender.com/nl/) · [v1.1 data audit](docs/v1.1-data-expansion-audit.md) · [v1 release record](docs/releases/v1.0.0.md) · [Documentation](docs/README.md)

## What it does

- Search **3,074 observed player-season profiles** (3,005 provider identities) across seven competitions, with native StatsBomb/Pappalardo-Wyscout definitions, 2,840 conservative common profiles and lazy detail comparison in English/Dutch. [Player database](https://football-recruitment-intelligence.onrender.com/players/) · [evaluation and limits](docs/common-profile-evaluation.md).

- Explore an attributed event/tracking sample and inspect coverage.
- Compare eighteen observed Player DNA features across six roles in WSL 2023/24: 138 eligible profiles at the default ≥900-minute threshold.
- Inspect a narrower historical WSL translation study, its simple baselines, uncertainty and unsupported cases.
- Set explicit recruitment requirements, compare replacements and club context, inspect top-ten mismatch explanations and separate weight/profile sensitivity. Share bounded versioned scenarios in the URL.

**The negative findings remain visible.** Broad cross-league translation is NO-GO. No Bayesian model qualified as the default across validation gates; simple source/ridge defaults remain and intervals under-cover. Final recruitment peer MRR (.258) is essentially the existing DNA result (.259); final roster MRR (.232) trails DNA (.332). Context results are mixed and small pools inflate stability. This is an evidence-organizing research tool, not validated transfer utility. [Model cards and full results](docs/README.md#research-evidence).

## Quick start

Install Node **24.19.0** (`.node-version`), Python **3.12 or 3.13**, and uv **0.12.21**. Dependency installation needs network access; product tests/builds need no football-source download, secret, database or local research cache.

```sh
git clone https://github.com/frenk4business/football-recruitment-intelligence.git
cd football-recruitment-intelligence
make setup
make test
make release-build
make release-validate
cd apps/web && npx playwright install chromium firefox webkit && cd ../..
make smoke
make dev
```

Expanded data reproduction uses `make v11-data-build`; `uv run fri data expand --max-matches 5` writes isolated development output. [v1.1 engineering and publication](docs/v1.1-engineering.md).

`make build` remains the static product build. `make api` runs the optional local FastAPI interface on 127.0.0.1; it is not hosted in production. Explicit research ingestion/reproduction commands are documented in the [research workflow](docs/research-workflow.md), separate from routine release CI.

## Release and operation

One existing Render Static Site serves 18 EN/NL routes from protected `main`, after checks pass. The release validates all 5,119 public JSON artifacts and 2,146 frozen research files; browser fetches verify release hashes and recover safely from stale/corrupt data. `/release-manifest.json` records the exact deployed commit, deterministic commit timestamp, source revisions and artifact/build hashes. Scientific versions remain independent of the canonical application `VERSION`.

[Release gate](docs/release-gate-v1.md) · [QA evidence](docs/v1-release-qa.md) · [Performance](docs/performance-v1.md) · [Accessibility](docs/accessibility-v1.md) · [Security](docs/security-v1.md) · [Operations](docs/operations.md) · [Rollback](docs/rollback.md) · [Contributing](CONTRIBUTING.md).

No additional paid infrastructure was introduced beyond the existing Render workspace/Starter resources. Actual build/bandwidth billing still applies. No backend, database, worker, disk, analytics service or visitor account system is added. The separate Frenkkester.com repository is outside this release.

Code © 2026 Frenk Kester, MIT. Provider data and logos retain separate rights. StatsBomb raw feeds, canonical research caches and full posterior draws are not published. Non-commercial restrictions and attribution remain: [data rights and attribution](ATTRIBUTION.md).
