# ADR 006 — evidence supports WSL season-context translation only

Status: accepted after evidence commit `af0f612`, before model fitting.

**NO-GO for broad cross-league translation. CONDITIONAL for a narrow WSL season-context study.** This is not a validated cross-league transfer model.

The StatsBomb catalogue audit covers 80 competition-seasons and 3,961 match lineups. Its 142 male / 23 female ordered domestic cross-league roster candidates fail the registered pair-coverage rules even before reconciled-minute filtering: only two male pairs reach 15 candidates; no pair reaches 50; the female maximum is ten candidates/nine players. Selected-club samples dominate much of the historical catalogue. Wyscout has 61 cross-league roster candidates across 19 pairs, no pair above eight, only one domestic season, and a different event ontology. No providers, genders or international/club observations are pooled to enlarge these counts.

The reconciled WSL audit contains 457 matches, 660 players, 1,225 dated player/team/season stints and 565 adjacent candidates. At 450/600/900/1,200 minutes on both sides, 191/162/117/51 episodes remain before the final role/context/split restrictions. Records across absent 2021/22 and 2022/23 seasons are rejected; 2023/24 remains available for observed profiles, not for inventing adjacent transfers. Thirteen WSL identities are conservatively quarantined for metadata inconsistencies.

Choose 600 minutes as a coverage/evidence compromise, not an optimum. Primary study: 2018/19→2019/20 development, 2019/20→2020/21 untouched destination-season test. Allow same or explicitly adjacent roles; reject major/unknown role changes and goalkeepers. Target role is a **specified scenario input**; in evaluation it is supplied retrospectively from the destination role. Therefore this is a conditional profile translation study, not a forecast of future role or minutes. Same-role sensitivity removes that assumption as far as possible.

Require both teams' context to be observable in at least three matches during the preceding 365 days **on or before the source environment ends**. No destination events enter source features or team-context predictors. Unknown/promoted team contexts are rejected rather than filled with future observations. This yields 53 training, 12 player-disjoint validation and 76 later-season test episodes; there is one episode per player within each period. Ten development and only four test episodes change team. Same-team season changes dominate, so broad team-transfer performance cannot be claimed.

Fit a modest negative-binomial model for four action counts, with exposure and strongly regularized role/team partial pooling. Do not estimate league effects (one competition) or player random intercepts (one training episode per player). A simple baseline can be selected for public use if Bayes does not earn its complexity on validation. Holdout outcomes do not determine publication-method selection. The next experiment-plan commit freezes the implementation and evaluation rules.

Keep the static architecture: offline inference, compact typed summaries, existing Next.js/Render service. No added backend, worker, database or paid resource is needed for the finite supported scenarios. Existing paid Render workspace/build resources remain in use; do not present this as an entirely free hosting account.
