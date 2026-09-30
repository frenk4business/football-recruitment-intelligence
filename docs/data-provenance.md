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
