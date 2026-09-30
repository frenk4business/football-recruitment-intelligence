# Provenance and reproducibility

`config/sample.json` freezes the source repositories, full commit IDs, selected match paths, tracking window and input SHA-256 checksums. The initial verified retrieval occurred on 30 September 2026. Re-running from the same bytes produces identical canonical/Parquet outputs; build time is intentionally variable.

For each file, `data/raw/<provider>/manifest.json` records URL, revision, retrieval UTC timestamp, hash, byte size and selection. Cache corruption fails before parsing. Downloads write temporary files then replace the cache file; partial HTTP/parse failures cannot become valid cache entries. No access token is required for source data.

SkillCorner's LFS object is streamed from GitHub's media endpoint. The downloader reads only the prefix necessary to capture frames **4040 ≤ frame < 4640** (600 frames at 10 Hz), with a 100 MB read ceiling. The stored source slice is 1,140,043 bytes. Its checksum applies to the selected JSONL slice, not the entire upstream LFS object. Transformation retains every tenth frame: 60 frames, timestamps 0–59 seconds. Metadata is full-match metadata and is labelled separately.

The StatsBomb sample has four input files: catalogue, competition-season matches, match lineups and events. Only the configured match is normalized. Catalogues facilitate discovery but their rows are not counted as ingested analytical coverage.

`artifacts/manifest.json` records pipeline/schema versions, source provenance, table counts, deterministic Parquet hashes and lineage stages. `artifacts/validation.json` records anomalies and null counts. `artifacts/data_coverage.json` derives counts and dates from canonical tables. No row totals are invented in frontend components.

Raw data, intermediate files, Parquet, virtual environments and local QA screenshots are excluded from Git. Committed public artifacts contain research aggregates and the permitted small SkillCorner sample. Test fixtures are synthetic and explicitly labelled. The public exporter never uses them.

A source-data update is a reviewable change: inspect the new licence and format, change the revision/selection, retrieve and verify hashes, rebuild, inspect anomalies, update contracts if needed, run tests, then commit only publication-safe artifacts. Do not silently refresh upstream `master` during CI or deployment.
