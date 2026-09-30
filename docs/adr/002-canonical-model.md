# ADR 002 — Canonical model with provider namespaces

Accepted, 2026-09-30.

**Context:** event feeds and tracking frames differ in timing, dimensions, identifiers, granularity and confidence. A common column name does not establish comparability.

**Decision:** explicit Pydantic row contracts, deterministic UUID5 IDs, source-aware coordinates and a provider entity map. Keep complete provider event attributes and original lineup roles in local JSON columns. Unknown identity matches remain separate.

**Consequences:** typed SQL over shared concepts, with provider provenance intact. Some columns remain nullable and event/tracking availability differs. No fuzzy name joins, universal event ontology or inferred league equivalence is introduced. Schema changes require a version and regenerated contracts.
