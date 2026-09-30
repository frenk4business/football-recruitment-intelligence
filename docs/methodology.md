# Phase 1 methods and limits

This phase asks whether heterogeneous open football data can be represented, validated and explored reproducibly. It does not evaluate recruitment performance.

## Coordinates and time

Reference pitch: 105 × 68 metres, origin bottom-left, x rightwards and y upwards. StatsBomb 120 × 80, top-left coordinates transform as `x * 105/120`, `(80-y) * 68/80`. Events remain actor-relative, attacking left to right; the two teams' event positions are not a synchronized physical snapshot.

SkillCorner centre-origin metres use the **actual 106 × 68 m** match pitch: `(x/106 + 0.5)*105`, `y+34`. Fixed-pitch direction is retained. The home direction is stored per period; period number alone does not authorize a rotation. Explicit `attack_left=True` rotates both axes when a caller has verified direction. The inverse transform is tested. Reference metres from a rescaled pitch are not original physical distances for speed estimation.

Off-pitch positions can be legitimate. They are retained and counted, never clipped silently. A generous physical envelope catches gross unit errors; nonfinite/partial coordinate pairs fail. Spatial analysis includes only in-pitch located actions, grouped into 12 × 8 bins. Missing locations are excluded and the plotted sample size is shown.

Canonical time is elapsed seconds within the stated period. SkillCorner nominal match-clock offsets (45/90/105 minutes for periods 2/3/4) are subtracted; its original timestamp is retained. The current first-period sample is 0–59 seconds. These sources are different matches and are never time-joined. A second-period fixture checks clock normalization and preserved fixed-pitch orientation.

## Descriptive metrics

- Shots/passes are counts of StatsBomb events in periods 1–4. Penalty shootout events remain in canonical storage but are excluded from player totals and spatial plots.
- Goals are Shot outcomes named Goal. Own-goal event types are not attributed as scorer goals. Match score comes from source match metadata.
- Penalties during normal/extra time are included; their subtype is retained for later sensitivity analysis.
- xG sums estimates supplied by StatsBomb. It is a provider model output, not observed truth or a model trained here. Missing shot xG makes the aggregate unavailable rather than being imputed as zero.
- Pass completion is completed passes / passes; zero attempts yields null. Absence of a StatsBomb pass outcome means complete by provider convention.
- Minutes sum nonoverlapping lineup position intervals using actual recorded period lengths, including stoppage/extra time. Overlap, backwards intervals or impossible endpoints produce null and a reason. Empty position lists indicate an unused StatsBomb substitute and produce zero. Six StatsBomb lineups in the sample fail the conservative interval rule.
- SkillCorner minutes are supplied full-match metadata, independent of the short tracking sample. Five roster entries have absent playing-time metadata and remain null.
- `shots_per90 = shots / minutes * 90`, only at ≥30 reliable minutes. Season per-90 is recomputed from totals, never averaged from match rates; if any minutes are unavailable, the season denominator is unavailable. This threshold is a display guard, not statistical certainty.
- Source unavailable metrics remain null. SkillCorner has no ingested event count, shots, passes or xG; these are never displayed as zero.

Duplicate IDs and broken references fail validation. Events without actors are retained (e.g. administrative events); the sample contains 29. Two provider-index timestamp inversions are retained and reported. A temporal view must sort by period/time while keeping provider index available. No timeline interpretation silently assumes strict source-index chronology.

Tracking is downsampled to 1 Hz for exploration only. 448 of 1,380 object observations are flagged not detected. No distance, speed, acceleration, pressure model or physical capacity claim is derived from this sample. Detection flags are not calibrated confidence scores.

Player-season and team-season tables describe **ingested observations**, not complete seasons. Teams, players and competitions remain namespaced per provider. Missing data, small samples, event-definition differences, selection bias and temporal coverage prevent cross-provider rankings or league-strength conclusions.

## Phase 2 — evaluated behavioural similarity

The earlier limitations above describe the Phase 1 sample. Phase 2 adds a separate complete WSL 2023/24 cohort, explicit event-based minutes reconciliation and versioned player features. The sample explorer remains separate. See [features](player-features.md), [similarity](player-similarity.md), [full evaluation](player-similarity-evaluation.md) and [cohort eligibility](phase-2-cohort.md). Public methodology is available in authored English and Dutch on `/methodology/#player-dna` and `/nl/methodology/#player-dna`.

Similarity measures observed style under role/season/evidence constraints. It does not estimate player quality, future ability, tactical fit or transfer success. The default is family-balanced Euclidean distance with role-specific standard scaling, selected after experiments. Failed hypotheses and candidate-size inflation are documented. The one-minute tracking sample remains unsuitable for physical profiling.

## Phase 3 — conditional historical WSL translation

The full evidence audit rejected broad cross-league modelling. A registered 53/12/76 temporal experiment compares three baselines with four hierarchical negative-binomial count models at 600 reliable minutes on both sides. Priors were checked before fitting; method selection was committed before test outcomes were inspected. No Bayesian target qualified for the default. Public expected values and 80% predictive ranges use ridge for shots/passes and unchanged source rates for carries/pressures; a clearly labelled research comparison retains Bayesian posterior predictive summaries.

Predictive ranges describe later observed performance, not coefficient uncertainty. Empirical ranges are not exposure-specific; Bayesian scenarios simulate 900 minutes. Source measurement uncertainty is explored by bootstrap sensitivity. Target roles are supplied assumptions; historical context never uses events after the source cutoff. There is one league and only four test team changes, so no causal league effect or recruitment advice follows. [Full model card](model-card-phase3.md) · [all results, effects, sensitivity and figures](league-translation-evaluation.md) · [prior checks](phase-3-prior-predictive.md). Authored public explanations: `/methodology/#translation` and `/nl/methodology/#translation`.

## Phase 4 — explicit observed recruitment fit

[Registered experiment](phase-4-experiment-plan.md) · [evidence audit](phase-4-fit-evidence.md) · [complete comparisons](recruitment-fit-evaluation.md) · [model card](model-card-phase4.md).

Observed profiles say what happened; requirements say what the analyst wants; club context describes the observed environment. Fit is weighted directional RMS percentile mismatch. Evidence (minutes and neighbour stability) remains separate, and historical translation is not available for the observed recruitment environment. Hard constraints remove candidates before ordering. Context only enters when explicitly adopted, with its assumption/source visible.

Known-peer retrieval, roster holdout, unchanged DNA/random baselines, context ablations, weight sensitivity and player-match bootstraps quantify representation consistency and robustness. They are not success labels. The final evidence is modest, includes poor subgroups, and gives mixed context gains. Pareto membership illustrates trade-offs but becomes weak information with eighteen dimensions. Changes to these semantics require a new version and registered evaluation; final queries are now open evidence and cannot serve as untouched validation again.
