# Player similarity evaluation — evaluation-v1

Generated from `artifacts/phase2/similarity_evaluation.json`; includes every configured method and threshold, not only favourable results. The experiment plan was registered in `docs/phase-2-experiment-plan.md` before evaluation.

Cohort: 132 WSL 2023/24 matches, 12 teams, 336 roster players, 495,189 events. One provider/revision. Eligible populations exclude uncertain roles, missing core values, GK and role groups below 12 members. AM is not merged with W; DM and CM remain separate. Default: 900 reliable minutes, 138 eligible profiles, 18 features, five equal families, role-specific standard scaling and Euclidean distance.

Temporal views use the common median match-date cutoff. Queries/candidates are the same paired eligible players with at least half the threshold in each window and an unchanged primary role. Candidate sets are role-isolated; evaluation allows at least three paired profiles in a supported production role. Scalers and PCA fit only the earlier window. Source match sets are disjoint and recorded in the machine report. This is within-season consistency, not held-out transfer or scouting validation. Method selection used this experiment; there is no untouched test season.

100 bootstraps resample whole player-match observations with replacement, independently per player, rebuild all vectors and refit transformations. Eligibility and roles are frozen. Shared match/team dependence is not preserved by this bootstrap. Seed 20260930. The public inclusion rate is how often a neighbour occurs in the top 10; it is not a calibrated confidence probability.

## All method comparisons

| Minutes | Method | Eligible | Queries | R@1 | R@5 | R@10 | MRR | Bootstrap Jaccard | Overlap with robust baseline |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 450 | cosine | 186 | 119 | 0.328 | 0.748 | 0.950 | 0.519 | 0.530 | 0.478 |
| 450 | euclidean | 186 | 119 | 0.361 | 0.756 | 0.916 | 0.548 | 0.566 | 1.000 |
| 450 | global_scaling | 186 | 119 | 0.429 | 0.798 | 0.950 | 0.588 | 0.597 | 0.651 |
| 450 | naive_features | 186 | 119 | 0.387 | 0.765 | 0.924 | 0.555 | 0.569 | 0.829 |
| 450 | pca | 186 | 119 | 0.353 | 0.731 | 0.924 | 0.514 | 0.553 | 0.875 |
| 450 | possession_context | 186 | 119 | 0.361 | 0.756 | 0.899 | 0.545 | 0.566 | 0.945 |
| 450 | standard_scaling | 186 | 119 | 0.429 | 0.798 | 0.916 | 0.594 | 0.586 | 0.802 |
| 450 | winsor_scaling | 186 | 119 | 0.395 | 0.824 | 0.958 | 0.579 | 0.567 | 0.980 |
| 450 | without_carrying | 186 | 119 | 0.319 | 0.723 | 0.891 | 0.498 | 0.547 | 0.782 |
| 450 | without_creation | 186 | 119 | 0.353 | 0.773 | 0.916 | 0.525 | 0.570 | 0.721 |
| 450 | without_defending | 186 | 119 | 0.319 | 0.697 | 0.882 | 0.499 | 0.571 | 0.723 |
| 450 | without_passing | 186 | 119 | 0.336 | 0.706 | 0.857 | 0.501 | 0.552 | 0.751 |
| 450 | without_shooting | 186 | 119 | 0.361 | 0.782 | 0.916 | 0.546 | 0.569 | 0.702 |
| 600 | cosine | 168 | 109 | 0.330 | 0.771 | 0.972 | 0.523 | 0.559 | 0.509 |
| 600 | euclidean | 168 | 109 | 0.431 | 0.798 | 0.927 | 0.590 | 0.605 | 1.000 |
| 600 | global_scaling | 168 | 109 | 0.468 | 0.835 | 0.954 | 0.623 | 0.629 | 0.660 |
| 600 | naive_features | 168 | 109 | 0.404 | 0.807 | 0.954 | 0.578 | 0.607 | 0.835 |
| 600 | pca | 168 | 109 | 0.358 | 0.771 | 0.917 | 0.538 | 0.598 | 0.885 |
| 600 | possession_context | 168 | 109 | 0.413 | 0.807 | 0.917 | 0.581 | 0.604 | 0.945 |
| 600 | standard_scaling | 168 | 109 | 0.459 | 0.817 | 0.936 | 0.618 | 0.620 | 0.782 |
| 600 | winsor_scaling | 168 | 109 | 0.459 | 0.853 | 0.963 | 0.622 | 0.605 | 0.975 |
| 600 | without_carrying | 168 | 109 | 0.413 | 0.743 | 0.908 | 0.558 | 0.580 | 0.804 |
| 600 | without_creation | 168 | 109 | 0.394 | 0.789 | 0.927 | 0.563 | 0.605 | 0.742 |
| 600 | without_defending | 168 | 109 | 0.349 | 0.743 | 0.890 | 0.531 | 0.610 | 0.741 |
| 600 | without_passing | 168 | 109 | 0.358 | 0.743 | 0.881 | 0.524 | 0.595 | 0.787 |
| 600 | without_shooting | 168 | 109 | 0.394 | 0.835 | 0.936 | 0.567 | 0.614 | 0.706 |
| 900 | cosine | 138 | 89 | 0.393 | 0.798 | 0.978 | 0.575 | 0.613 | 0.554 |
| 900 | euclidean | 138 | 89 | 0.438 | 0.820 | 0.921 | 0.614 | 0.653 | 1.000 |
| 900 | global_scaling | 138 | 89 | 0.494 | 0.865 | 0.966 | 0.659 | 0.682 | 0.715 |
| 900 | naive_features | 138 | 89 | 0.472 | 0.854 | 0.944 | 0.634 | 0.656 | 0.862 |
| 900 | pca | 138 | 89 | 0.449 | 0.831 | 0.921 | 0.612 | 0.642 | 0.907 |
| 900 | possession_context | 138 | 89 | 0.461 | 0.820 | 0.921 | 0.624 | 0.652 | 0.951 |
| 900 | standard_scaling | 138 | 89 | 0.472 | 0.843 | 0.944 | 0.636 | 0.669 | 0.824 |
| 900 | winsor_scaling | 138 | 89 | 0.494 | 0.854 | 0.955 | 0.659 | 0.652 | 0.967 |
| 900 | without_carrying | 138 | 89 | 0.449 | 0.820 | 0.944 | 0.617 | 0.635 | 0.809 |
| 900 | without_creation | 138 | 89 | 0.427 | 0.831 | 0.955 | 0.605 | 0.654 | 0.743 |
| 900 | without_defending | 138 | 89 | 0.393 | 0.775 | 0.910 | 0.550 | 0.656 | 0.769 |
| 900 | without_passing | 138 | 89 | 0.382 | 0.753 | 0.899 | 0.552 | 0.641 | 0.802 |
| 900 | without_shooting | 138 | 89 | 0.449 | 0.831 | 0.933 | 0.608 | 0.665 | 0.783 |
| 1200 | cosine | 93 | 63 | 0.460 | 0.937 | 1.000 | 0.639 | 0.676 | 0.608 |
| 1200 | euclidean | 93 | 63 | 0.524 | 0.905 | 0.984 | 0.680 | 0.732 | 1.000 |
| 1200 | global_scaling | 93 | 63 | 0.603 | 0.921 | 1.000 | 0.742 | 0.760 | 0.782 |
| 1200 | naive_features | 93 | 63 | 0.556 | 0.873 | 1.000 | 0.698 | 0.734 | 0.895 |
| 1200 | pca | 93 | 63 | 0.476 | 0.889 | 1.000 | 0.645 | 0.728 | 0.944 |
| 1200 | possession_context | 93 | 63 | 0.540 | 0.905 | 0.984 | 0.686 | 0.729 | 0.963 |
| 1200 | standard_scaling | 93 | 63 | 0.540 | 0.905 | 0.968 | 0.690 | 0.748 | 0.855 |
| 1200 | winsor_scaling | 93 | 63 | 0.571 | 0.937 | 1.000 | 0.724 | 0.730 | 0.975 |
| 1200 | without_carrying | 93 | 63 | 0.556 | 0.905 | 0.984 | 0.691 | 0.719 | 0.877 |
| 1200 | without_creation | 93 | 63 | 0.444 | 0.857 | 0.984 | 0.632 | 0.729 | 0.813 |
| 1200 | without_defending | 93 | 63 | 0.444 | 0.794 | 0.968 | 0.601 | 0.734 | 0.823 |
| 1200 | without_passing | 93 | 63 | 0.460 | 0.873 | 0.984 | 0.630 | 0.724 | 0.870 |
| 1200 | without_shooting | 93 | 63 | 0.492 | 0.857 | 0.984 | 0.651 | 0.746 | 0.826 |

## Selected method sensitivity and random reference

| Minutes | Role sizes | Random R@5 | Random R@10 | Minutes–Jaccard Spearman |
|---:|---|---:|---:|---:|
| 450 | {'CB': 44, 'CM': 16, 'DM': 30, 'FB/WB': 37, 'ST': 24, 'W': 35} | 0.252 | 0.487 | -0.009 |
| 600 | {'CB': 38, 'CM': 15, 'DM': 29, 'FB/WB': 33, 'ST': 21, 'W': 32} | 0.275 | 0.523 | -0.045 |
| 900 | {'CB': 36, 'CM': 12, 'DM': 22, 'FB/WB': 29, 'ST': 15, 'W': 24} | 0.337 | 0.618 | 0.039 |
| 1200 | {'CB': 28, 'DM': 15, 'FB/WB': 20, 'ST': 12, 'W': 18} | 0.397 | 0.762 | -0.024 |

## Default role-level results

| Role | Paired candidates | R@1 | R@5 | R@10 | MRR | Bootstrap Jaccard (full eligible group) |
|---|---:|---:|---:|---:|---:|---:|
| CB | 26 | 0.231 | 0.769 | 0.846 | 0.474 | 0.540 |
| CM | 5 | 0.600 | 1.000 | 1.000 | 0.717 | 0.926 |
| DM | 14 | 0.643 | 0.929 | 1.000 | 0.763 | 0.738 |
| FB/WB | 19 | 0.474 | 0.842 | 0.947 | 0.625 | 0.579 |
| ST | 11 | 0.455 | 0.818 | 1.000 | 0.624 | 0.838 |
| W | 14 | 0.714 | 0.857 | 1.000 | 0.808 | 0.675 |

## Hypotheses and selection

- H1 was not supported: global robust scaling outperformed role-specific robust scaling on retrieval and stability. Candidates remained role-isolated, so this is a scaling effect. The product keeps role-relative standard scaling for interpretation; it does not claim this restriction maximises retrieval.
- H2 is not established as a causal or strong within-cohort effect. Higher thresholds raise aggregate stability, but also remove players and shrink candidate groups. Within-threshold rank correlations are near zero or negative. CM has only 12 profiles at 900 minutes and ST only 12 at 1,200, making top-10 overlap intrinsically high.
- H3 was not consistently supported: equal family weighting does not beat naive feature weighting on every measure. We retain equal family weights as an explicit interpretability policy, preventing feature-count dominance, not as an empirical performance win.
- H4 is only partially supported: PCA broadly preserves neighbours and most variance, but neither improves retrieval consistently nor improves bootstrap stability. Retain full-feature distance. The separate two-dimensional PCA map is exploratory and is not used for ranking.
- Standard scaling improved retrieval and bootstrap stability over the robust full-feature baseline at all four thresholds. Winsorised robust scaling improved retrieval, but did not improve stability consistently and changes extreme observations. No profiles are removed or clipped in the selected model.
- Ablation: removing passing or defending noticeably weakens same-player retrieval. Other changes can help some metrics; no family is selected/dropped to make named player pairs look plausible.
- Possession adjustment replaces pressure/interception per-90 with per-100 opponent sequences and progressive passes with per-100 own sequences. It has no consistent stability advantage. Keep these measures separate and label them as sequence-based context.

900 is a practical coverage/evidence compromise, not a statistically optimal threshold: 138 profiles across six roles, versus 93 across five at 1,200. Lower thresholds stay available with numeric evidence and stability. No quality, tactical-fit, future-potential or transfer claims follow from these results.

## PCA audit

PCA uses full deterministic SVD on family-weighted standardized features, retaining at least 90% variance. No whitening. Each comparison-role model has separate loadings, mean and explained-variance ratios in the machine report. The UI map separately fits two components to role-standardized vectors and explicitly disclaims cross-role distance meaning.

| Role | Retained components | Explained variance | Largest absolute PC1 loadings |
|---|---:|---:|---|
| CB | 7 | 0.917 | crosses_per90: 0.596, shot_assists_per90: 0.446, box_carries_per90: 0.340, box_passes_per90: 0.286 |
| CM | 5 | 0.919 | carry_distance_per90: 0.483, progressive_carries_per90: 0.475, carries_per90: 0.328, recoveries_per90: 0.298 |
| DM | 5 | 0.902 | box_carries_per90: 0.770, shots_per90: 0.369, box_shots_per90: 0.259, box_passes_per90: 0.235 |
| FB/WB | 7 | 0.902 | box_passes_per90: 0.532, shot_assists_per90: 0.432, progressive_passes_per90: 0.360, final_third_passes_per90: 0.355 |
| ST | 5 | 0.917 | progressive_carries_per90: 0.556, carry_distance_per90: 0.465, carries_per90: 0.346, crosses_per90: 0.325 |
| W | 6 | 0.914 | crosses_per90: 0.460, shot_assists_per90: 0.440, box_passes_per90: 0.394, progressive_passes_per90: 0.309 |

## Outlier and publication policy

Robust scaling uses median/IQR; zero-IQR features fall back to population standard deviation, and constant dimensions are omitted. Standard scaling uses mean/population SD. The research winsorisation control clips at the training cohort's 1st/99th percentiles; it is not public production preprocessing. Full fitted scaler metadata and the named player/feature values affected by research clipping are recorded in `artifacts/phase2/outlier_audit.json`. All players, including unusual profiles, remain unless excluded by the documented evidence policy.

No UMAP, xT, VAEP or learned contrastive representation was trained. CPU PCA is the only latent representation experiment. A second independent season and team/context changes are needed before representation learning or league translation could be evaluated responsibly.

