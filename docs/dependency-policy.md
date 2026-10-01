# Dependency and toolchain policy

Node production/CI baseline is `.node-version` (24.19.0); package engines accept 24.19.x only. No claim is made for other Node majors. Python supports 3.12 and 3.13 (`>=3.12,<3.14`); CI runs the complete Python suite on both. uv is pinned to 0.12.21 in CI. npm installs use `npm ci`; Python uses `uv sync --frozen`. Lockfiles are required.

Dependabot checks npm, uv and GitHub Actions weekly with bounded PR counts. No automatic merge or deploy of an unreviewed update. Review release notes, direct/transitive changes, license/security effects, contract/artifact locks, both Python minors and all browsers. A scientific dependency update does not authorize re-fitting or changing frozen results. Pin major Actions versions and review their updates; ordinary workflows have contents:read and cannot approve PRs.

CI audits the npm lock and all exported locked Python dependencies with pip-audit 2.10.1. A high/critical advisory blocks release. Review every lower-severity finding; record applicability, mitigation, owner and review date for any exception. There are no accepted advisory exceptions at this release checkpoint. The temporary build-only Ajv 8.17.1 advisory encountered during development was resolved by pinning 8.20.0; no unsafe `$data` schema option is enabled.

Run `make security-audit`. Advisory databases require network access: a database outage is a failed/unverified audit, not a clean result. Audits detect known published issues, not all malicious packages or supply-chain compromises. Public dependency manifests contain no credentials. Do not store Render/GitHub tokens in workflows, variables, artifacts or issue reports.
