# Player DNA — player-dna-v1

Player DNA is a compact representation of observed playing behaviour within the selected season and evidence threshold. It is not genetics, innate ability, potential, personality, player quality or transfer value.

The evidence layer is match-partitioned canonical Parquet. `player_feature_observation.parquet` retains match/date/team/competition/season/player IDs, reliable minutes, exclusion reasons, role time, event-derived counts and opportunity denominators. `player_profiles.json` aggregates this evidence; neither table replaces the Phase 1 descriptive marts. The same provider player ID can appear at multiple teams; team memberships are retained. No cross-season or cross-provider identity linking is claimed.

Eligibility requires the selected reliable minutes, all 18 core features, at least 60% known role minutes, a leading role share ≥40%, an outfield role and at least 12 eligible profiles in that role. Primary role uses accumulated minutes, never the number of matches. Secondary role, shares and a multi-role indicator (<70% in the primary role) remain visible. Only reliable observations enter profiles; one bad appearance does not invalidate the other measured appearances.

For each role/threshold/season, compute `z_j=(x_j-mean_j)/population_sd_j`. Constant dimensions contribute nothing; redistribute weights equally across the remaining families and equally across active dimensions within each family. The distance is:

`d(A,B) = sqrt(mean_family(mean_active_feature((z_A-z_B)^2)))`.

This is an equal-family Euclidean metric, with symmetry and zero distance for identical vectors. Ties sort by canonical player ID. No self-neighbour is returned. Distances have no probability interpretation and are not globally comparable between different role scalers. Percentiles use the same role/threshold/season: `100*(count_below + 0.5*count_equal)/cohort_size`.

A feature contributes its weighted squared standardized difference. Family contributions sum those values and divide by total squared distance. They therefore describe **squared distance**, not ability or importance to football. “Most similar” selects the three smallest absolute standardized differences among active dimensions; “largest differences” selects the three largest. Direction states which player has the higher measured value, without calling it better. No generated narrative or manual reranking is used.

The precomputed public index includes all roster profiles, with reasons at every threshold. Only eligible profiles have neighbours/percentiles. Each selected player's detail loads lazily; top 10 only, plus deterministic explanations and coarse 12×8 bins. The full N×N matrix and raw canonical/provider events never enter Git or the browser. The API and TypeScript consume generated Pydantic schemas.

`artifacts/phase2/model_manifest.json` records feature/vector versions, source revision, thresholds, seed, fitted scalers, family weights, method and public file hashes. Build timestamps are informational; scientific output and hashes reproduce. `make phase2-build` orchestrates retrieval → canonical validation → features/eligibility → all evaluations → publication → generated reports. `make cohort`, `make features`, `make similarity-evaluate`, `make similarity` also run individually. Research outputs require full configured evidence; CI never downloads a season.

See [evaluation](player-similarity-evaluation.md), [registry](player-features.md), [cohort](phase-2-cohort.md) and [selection decision](adr/005-player-similarity-method.md). Source terms permit this non-commercial research analysis with attribution; they do not grant raw-data redistribution or commercial scouting rights.
