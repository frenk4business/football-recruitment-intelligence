# Provenance and reproducibility

`config/sample.json` freezes the source repositories, full commit IDs, selected match paths, tracking window and input SHA-256 checksums. The initial verified retrieval occurred on 30 September 2026. Re-running from the same bytes produces identical canonical/Parquet outputs; build time is intentionally variable.

For each file, `data/raw/<provider>/manifest.json` records URL, revision, retrieval UTC timestamp, hash, byte size and selection. Cache corruption fails before parsing. Downloads write temporary files then replace the cache file; partial HTTP/parse failures cannot become valid cache entries. No access token is required for source data.

SkillCorner's LFS object is streamed from GitHub's media endpoint. The downloader reads only the prefix necessary to capture frames **4040 ≤ frame < 4640** (600 frames at 10 Hz), with a 100 MB read ceiling. The stored source slice is 1,140,043 bytes. Its checksum applies to the selected JSONL slice, not the entire upstream LFS object. Transformation retains every tenth frame: 60 frames, timestamps 0–59 seconds. Metadata is full-match metadata and is labelled separately.

The StatsBomb sample has four input files: catalogue, competition-season matches, match lineups and events. Only the configured match is normalized. Catalogues facilitate discovery but their rows are not counted as ingested analytical coverage.

`artifacts/manifest.json` records pipeline/schema versions, source provenance, table counts, deterministic Parquet hashes and lineage stages. `artifacts/validation.json` records anomalies and null counts. `artifacts/data_coverage.json` derives counts and dates from canonical tables. No row totals are invented in frontend components.

Raw data, intermediate files, Parquet, virtual environments and local QA screenshots are excluded from Git. Committed public artifacts contain research aggregates and the permitted small SkillCorner sample. Test fixtures are synthetic and explicitly labelled. The public exporter never uses them.

A source-data update is a reviewable change: inspect the new licence and format, change the revision/selection, retrieve and verify hashes, rebuild, inspect anomalies, update contracts if needed, run tests, then commit only publication-safe artifacts. Do not silently refresh upstream `master` during CI or deployment.

## Phase 2 frozen season

The official repository head was reverified on 30 September 2026 at the same commit as Phase 1. WSL competition 37 / season 281 has 132 matches and 12 teams; IDs belong in `config/cohorts.yaml`, not analytical logic. 266 exact files are locked in `config/wsl_2023_24.sources.json`. The license PDF was downloaded again and was byte-identical to the audited Phase 1 copy. Bounded concurrency is three, retries cover transient HTTP/network failures, and each cache hit verifies SHA-256 without network retrieval. All raw data remains ignored.

`artifacts/phase2/cohort_eligibility.json` reports actual coverage, feature missingness, role populations and per-player exclusion reasons at four thresholds. `model_manifest.json` records the source/feature/representation versions, fitted scalers and publication hashes. Public payloads are derived research profiles and coarse bins, with no source event IDs/timestamps/payloads. The registered hypotheses predate similarity evaluation. Seed and fitted transformations are preserved; generation times intentionally vary.
# Phase 3 provenance extension

The official catalogue audit uses StatsBomb revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`; its licence was redownloaded and compared with the earlier pinned agreement. `config/phase3.sources.json` records 4,518 input URLs, byte lengths and SHA-256 checksums. The Wyscout audit uses separately pinned Figshare file IDs; current discovery metadata is archival evidence, while the reproducible audit replays immutable metadata-file downloads. It never harmonizes providers by name or mixes event definitions.

An environment preserves provider/player identity, competition, team, season, dates, observed role shares, reliable exposure, counts and feature revision. Adjacent episodes retain inclusion/exclusion reasons, role changes and recorded team changes. Observation dates are not contract dates. Missing 2021/22–2022/23 WSL data prevents direct bridging. Identity conflicts are conservatively quarantined. [Detailed audit](phase-3-transfer-evidence.md).

Offline fits retain code/data/config hashes, package versions, seed, priors, source revision, feature/DNA/model versions and diagnostics. The validation-selection hash binds evaluation and publication. The frozen test was never fitted into the v1 model. Full posterior draws and source event/lineup payloads are local/ignored. Public outputs use strict derived-only schemas and per-file hashes. [Model card](model-card-phase3.md) · [rebuild and QA](phase-3-qa.md).
