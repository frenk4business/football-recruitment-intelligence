# Phase 4 evidence and requirements audit

Audit precedes candidate scoring and method selection. Base: main `6051ce04da532381766c69b83773fd1fe4b732b1`. Baseline verification passed: 93 Python tests, four frontend unit tests, 14 browser tests, lint/types/contracts. Source definitions and Player DNA/translation versions remain unchanged.

## Decision

**NO-GO for transfer-success evaluation. CONDITIONAL for observed profile retrieval, roster-profile alignment and ranking robustness.** The audit uses existing, checksum-pinned StatsBomb sources; no new provider, scraped ages, prices, contracts or outcome labels are introduced.

The WSL 2023/24 cohort contains 132 matches, 12 clubs and 336 roster identities. Exactly 138 pass the established 900-minute/complete-feature/supported-role rules: CB 36, CM 12, DM 22, FB/WB 29, ST 15 and W 24. Five eligible players appear at multiple clubs; candidate DNA remains their explicitly labelled whole-season composite. Club roster medians instead use each player's own club stint, requiring 900 reliable minutes within that stint. AM and GK are not eligible comparison roles. Birth dates are absent for all 336 players, so there is no age filter. Nationality is neither needed nor introduced as a recruitment constraint.

Existing historical evidence contains 182 adjacent candidates involving a recorded team change, including structurally rejected cases. Only 30/25/12/5 satisfy the 450/600/900/1,200-minute rules on both sides. At 900 minutes, nine end in 2019/20 and three in 2020/21; none supports an adjacent full-season 2023/24 backtest. Phase 3's narrower role/context study has ten development and four test team changes at 600 minutes. Those destination observations were already inspected in Phase 3.

For every candidate move, `artifacts/phase4/fit_evidence.json` records source/destination exposure, complete source-feature availability, subsequent observations, supplied destination role, source-end decision-date proxy, historically available target context, and exclusion reasons. For the 12 minute-eligible moves, the audit also reconstructs an observed same-role candidate set from source-season player-match counts strictly on/before the proxy. Sizes range from 5 to 26. These are observed players, not an actual recruitment opportunity set. Contract availability, unobserved alternatives, failed/unrecorded moves and a defensible success label are missing. A joiner's observed rank would not establish transfer success; no historical success backtest will be fabricated.

## Formal schema before scoring

`RecruitmentScenario` / `RecruitmentRequirement` define **requirements-v1**. Requirements have an ID, type, provenance source, known feature, exact/minimum/maximum/neutral preference, percentile value, integer importance 1–3 and optional hard-threshold flag. Sources are user-defined, observed-club-context, replacement-player or derived-roster-gap. An adopted context suggestion remains an analyst assumption. It never becomes a hidden football truth.

Hard constraints precede ranking: supported provider/cohort, selected role, complete eligible DNA, minimum reliable minutes, optional minimum existing neighbour stability, optional candidate team and same-club exclusion. Replacement reference players are excluded from their candidate alternatives. Hard feature minima/maxima are permitted; neutral and exact preferences cannot masquerade as hard pass/fail thresholds. Evidence thresholds filter eligibility and never multiply or add to football fit.

The scenario includes club, season, mode, replacement ID, requirements, family importance, comparison cohort and fit version. It is serialisable and restricted to observed WSL 2023/24. No cloud account or saved database is needed. Formal JSON Schemas are committed alongside the executable Pydantic contracts; unknown fields and nonfinite values fail validation.

## Club context definition

**club-context-v1** describes one provider, competition, season and observation window. It reports raw event rates, season-relative midrank percentiles, feature availability, actual team-match minutes/matches and source revision. It is not a permanent club identity or an estimate of managerial quality.

Team counts reuse the unchanged `features-v1` event predicates through a counting actor per team. Each team event enters once, including goalkeepers; the denominator is actual match duration from period endpoints. This deliberately differs from averaging player rates or summing eleven players' minutes. Missing relevant event fields make a season feature unavailable rather than zero. Percentiles compare only clubs in the same competition-season.

Fourteen contextual features cover passing/progression, long passes, progressive carries, final-third/box entries, shot assists, crosses, pressures/counterpressures, interceptions, shots and descriptive non-penalty xG. All fourteen are available for all 12 clubs, each with 22 matches. The feature registry is reused; recruitment relevance/default visibility extend it without altering `features-v1` or `player-dna-v1`. Context features are descriptive and are not automatically fit inputs.

Role roster views report reliable exposure, observed depth, complete-profile depth, top-player minutes share, minutes HHI, role-profile median, quartiles and range. Roles use the player's predominant role within the club stint. There are 24 club-role groups with at least three eligible club-stint profiles, versus 28 when whole-season multi-club profiles are counted at every team. The former is the correct public roster reference. A roster gap means the difference between an explicit selected requirement and these observed profiles, not an inferred need to sign anyone. Sparse/missing role profiles remain visible and do not receive invented medians.

## Temporal and evidential separation

Observed Fit uses 2023/24 DNA and same-season descriptive club/roster context. These full-season summaries support a retrospective scenario tool, not a decision-date forecast. Historical Translation remains the separate supported 2019/20 → 2020/21 Phase 3 workflow, preserving its simple defaults and undercoverage warnings. No 2024/25 predictions are generated from that historical model.

The next committed experiment will compare transparent scoring designs before selecting the public method. Its retrieval targets measure representation consistency, roster holdout measures descriptive compatibility, and perturbations measure assumption/data sensitivity. None is recruitment accuracy.
