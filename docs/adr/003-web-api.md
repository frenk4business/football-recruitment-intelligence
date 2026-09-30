# ADR 003 — Next.js product and FastAPI contracts

Accepted, 2026-09-30.

**Context:** Python suits the analytical pipeline while the bilingual product requires accessible, responsive pages. Always-on infrastructure adds no Phase 1 benefit.

**Decision:** Next.js/React/TypeScript static export, with FastAPI locally. Pydantic validates both API payloads and published JSON. TypeScript types are generated, not maintained independently. Render serves the static export from the Phase 1 branch.

**Consequences:** English and Dutch pages and the explorer work without backend cold starts. There is no server database or secret. Public artifacts refresh only after an explicit reviewed data build. Later live analytics can use the same contracts. The public site exposes no arbitrary query endpoint.
