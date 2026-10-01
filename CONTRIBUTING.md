# Contributing

Use a focused branch and pull request against main. Start with the production quick start in README; `make test`, `make release-build`, `make release-validate` and the three-browser smoke suite are required for product changes. Node/uv/Python and dependency policy are documented under docs. Keep English and Dutch copy/controls equivalent, including errors and evidence limitations.

Do not add new data, model features, transfer advice or scoring semantics as a routine UI fix. Research changes require a separate versioned experiment plan before touching inspected final evaluation data. Never regenerate a frozen result to make a test green. Do not edit scientific/public lock manifests unless an explicitly reviewed, versioned research change authorizes it.

Describe the user-visible problem, final behavior and relevant test evidence in the PR. Avoid secrets, provider raw feeds, local caches, posterior draws, sourcemaps and personal file paths in public output. Retain source attribution and code/data license boundaries. Dependency updates require full gates and review; no automatic merges. Security/incident handling is in docs/security-v1.md and docs/operations.md. Be respectful, specific and evidence-led in issues and reviews.
