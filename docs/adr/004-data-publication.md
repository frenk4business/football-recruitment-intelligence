# ADR 004 — Publish permitted analysis, keep raw data local

Accepted, 2026-09-30.

**Context:** zero-cost access does not grant redistribution rights. StatsBomb's agreement restricts underlying-data sharing; SkillCorner retains an MIT notice.

**Decision:** never commit downloaded raw data or canonical Parquet. Commit only labelled synthetic test fixtures, source references/checksums, research aggregates and the permitted small tracking sample. StatsBomb event locations become coarse spatial bins rather than a public event feed. Keep required source names, logo and licence notices visible.

**Consequences:** source downloads remain reproducible, but consumers must obtain their own permitted raw inputs. The project code's MIT licence does not relicense data or trademarks. Reassess terms before any commercial use or new source export.
