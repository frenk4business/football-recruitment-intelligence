# ADR 005 — role-specific standard scaling and family-balanced Euclidean distance

Status: accepted for player-dna-v1, after the registered Phase 2 comparisons. Source data and experiments are frozen before publication.

We need an interpretable behavioural comparison, not a goal ranking. Use 18 style features, original separate outfield roles, 900 reliable elapsed minutes by default, ≥12 members per role, role-specific mean/population-SD scaling and equal weighting of five families. No clipping or outcome metric in the default vector. Distances and contributions remain explicit; no arbitrary 0–100 score.

Standard scaling improved temporal retrieval and bootstrap stability over the proposed median/IQR baseline across 450/600/900/1,200 minutes. At 900, selected Recall@1/5/10 is .472/.843/.944, MRR .636 and bootstrap Jaccard .669 (89 paired temporal queries; 138 production profiles). PCA (.612 MRR; .642 Jaccard for robust PCA) did not consistently improve the robust full-feature representation; cosine had weaker R@1/MRR and stability. Keep PCA as a separately labelled exploratory map and research comparator.

The negative controls matter: global robust scaling and naive feature weighting beat role-specific robust family weighting on several measures. We do not claim role-aware scaling or equal weights are empirically optimal. The former preserves role-relative interpretation required by the product; the latter prevents an arbitrary number of features from deciding family importance. No family is dropped because of one favourable ablation. Winsorisation improved retrieval but not stability consistently and would alter unusual profiles. Possession sequence adjustments did not improve stability consistently.

900 balances coverage and evidence, without an optimality claim. At 1,200 only 93 profiles across five roles remain, and small groups inflate neighbour overlap. The within-threshold minutes–stability association is weak. Publish numeric evidence and stability at all four thresholds, and reject subthreshold profiles explicitly.

No learned model, xT or VAEP dependency. Preserve the raw descriptive marts, source namespaces and local-first architecture. Revisit the method on an independent season and with team changes; this evaluation was also used for selection and is not an untouched test set.
