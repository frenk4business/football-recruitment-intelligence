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
