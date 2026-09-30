# ADR 001 — DuckDB + Parquet

Accepted, 2026-09-30.

**Context:** analytical scans and reproducible research are the core workload; no transactional users or concurrent writes are needed.

**Decision:** canonical tables are local Parquet, queried through DuckDB. There is no hosted relational database.

**Consequences:** portable files, SQL, compression and pushdown without server administration, credentials or recurring database charges. Larger-than-memory analytical workflows are possible. This sample uses compact files rather than premature partitioning. Concurrent writes, application transactions and distributed serving are not provided. A later database or warehouse migration can preserve the canonical/API contracts.
