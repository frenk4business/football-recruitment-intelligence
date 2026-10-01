# Explicit research workflow

These commands may download provider data, materialize local research tables or fit models. They are separate from `make setup/test/release-build/release-validate` and are not required to run the product. Review the registered plans, source licenses and frozen scientific lock before using them. Do not overwrite released scientific results simply to refresh a dependency or fix a UI issue.

```sh
make data-bootstrap       # pinned small Phase 1 event/tracking sample
make phase2-build         # WSL 2023/24 observed features/similarity
make translation-audit    # catalogue and separate Wyscout metadata audit
make phase3-build         # explicit historical WSL research pipeline
uv run python scripts/phase3_reproduce.py
make phase4-build         # club context, candidate index and bootstrap aggregates
make recruitment-evaluate # compare all registered Phase 4 results
make contracts            # regenerate only after an authorized contract change
```

First research ingestion requires network access and storage; later runs reuse checksum-verified caches. Canonical data and full posterior samples stay ignored/local. Ordinary CI uses synthetic fixtures and committed aggregates, including small model smoke tests; it does not refit the full historical study or ingest the 132-match season.
