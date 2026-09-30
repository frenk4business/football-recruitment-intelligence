# Phase 2 experiment plan — registered before evaluation

Registered on 2026-09-30, before feature extraction or similarity results. Phase 1 audit passed all required commands (46 Python and 4 web unit tests). PR #1 remains open; this branch starts at 15b8415.

Primary cohort: complete StatsBomb WSL 2023/24 at the verified source revision in `config/cohorts.yaml`. One competition and season; no identity linking by name. SkillCorner remains explorer-only. Primary candidate threshold: 900 reliable minutes; compare 450, 600 and 1,200. Goalkeepers are excluded from outfield similarity. Keep the eight canonical roles; require at least 12 eligible profiles per comparison role (top 10 must have alternatives). Do not merge sparse roles simply to enable results. At least 60% known role minutes and a primary role share of 40% are required; display multi-role shares.

H1: role-specific median/IQR scaling improves temporal retrieval and bootstrap top-10 Jaccard compared with global scaling, while keeping candidates role-isolated in both.
H2: more minutes are associated with greater bootstrap top-10 Jaccard. Report both threshold aggregates and per-player correlation; cohort composition is a confounder.
H3: equal feature-family weighting improves retrieval/stability compared with feature-level Euclidean distance.
H4: PCA retaining 90% variance preserves useful neighbours and retrieval relative to full features. Report loadings, dimensions, explained variance and top-10 overlap.

Use a single common calendar split at the season's match-date median. Fit evaluation scalers/PCA on first-window profiles only; compare first-window queries to second-window candidate profiles in the same role, with at least half the threshold in each window. Exclude role changes from paired retrieval and report their number. No shared match events. This is repeated-observation consistency, not transfer accuracy. Report query counts, candidate counts, Recall@1/5/10, MRR and random-candidate expectations; small role groups can inflate Recall@10.

Bootstrap 100 times with a fixed seed: resample each eligible player's reliable match observations with replacement, preserving match-level counts and denominators; rebuild all candidate/query features, refit role scalers and recompute rankings. Freeze eligibility and role to the baseline to isolate sampling noise. Compare against baseline top min(10,n-1). Inclusion rate is sampling stability, not a similarity probability. Small cohorts may make top-10 stability trivial; show cohort size and k.

Compare family-balanced Euclidean, family-balanced cosine and PCA distance. Run leave-one-family-out ablation, global-scaling and naive Euclidean controls. Investigate possession opportunity rates and team-relative passing separately; keep the directly interpretable per-90 baseline unless adjustments have clear evidence. Record failures and weak findings. Do not tune towards recognisable names.

Selection considers temporal retrieval, neighbour stability, interpretability and simplicity together. Choose and document a default only after evaluation. No neural, xT or VAEP dependency is required.
