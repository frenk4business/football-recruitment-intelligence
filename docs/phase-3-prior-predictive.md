# Phase 3 prior predictive checks

Registered before real-outcome fitting. 1,500 prior draws per specification; fixed seed 20260930. Both latent-rate and future-observation tails are checked against football plausibility ceilings. These are broad regularization checks, not hard outcome limits. Main priors passed. Two wider-prior candidates failed the 1% carry-tail gate and were narrowed before fitting; all rejected runs remain in the audit JSON and original experiment amendment.

| Check | Latent p01 / median / p99 | Future p01 / median / p99 | Ceiling | Latent above | Future above | Passed |
|---|---|---|---:|---:|---:|---|
| alternative:pressures | 1.08 / 12.22 / 110.58 | 0.00 / 10.59 / 131.82 | 150 | 0.485% | 0.753% | True |
| alternative:progressive_carries | 0.10 / 3.17 / 53.29 | 0.00 / 2.69 / 58.83 | 50 | 1.132% | 1.346% | False |
| alternative:progressive_passes | 0.24 / 3.01 / 35.29 | 0.00 / 2.60 / 40.44 | 50 | 0.467% | 0.658% | True |
| alternative:shots | 0.03 / 1.59 / 32.16 | 0.00 / 1.34 / 35.51 | 50 | 0.419% | 0.553% | True |
| final_alternative:pressures | 1.42 / 12.23 / 84.63 | 0.00 / 10.65 / 103.09 | 150 | 0.159% | 0.406% | True |
| final_alternative:progressive_carries | 0.13 / 3.20 / 40.08 | 0.00 / 2.72 / 45.83 | 50 | 0.633% | 0.854% | True |
| final_alternative:progressive_passes | 0.31 / 3.01 / 27.21 | 0.00 / 2.61 / 32.62 | 50 | 0.207% | 0.366% | True |
| final_alternative:shots | 0.05 / 1.60 / 23.85 | 0.00 / 1.35 / 27.93 | 50 | 0.182% | 0.307% | True |
| primary:pressures | 1.58 / 12.25 / 76.16 | 0.00 / 10.71 / 96.07 | 150 | 0.087% | 0.324% | True |
| primary:progressive_carries | 0.15 / 3.21 / 35.66 | 0.00 / 2.73 / 42.80 | 50 | 0.440% | 0.726% | True |
| primary:progressive_passes | 0.34 / 3.01 / 24.49 | 0.00 / 2.61 / 30.46 | 50 | 0.134% | 0.316% | True |
| primary:shots | 0.05 / 1.61 / 21.10 | 0.00 / 1.35 / 24.62 | 50 | 0.107% | 0.202% | True |
| revised_alternative:pressures | 1.31 / 12.23 / 91.07 | 0.00 / 10.69 / 111.77 | 150 | 0.252% | 0.505% | True |
| revised_alternative:progressive_carries | 0.12 / 3.20 / 44.19 | 0.00 / 2.73 / 50.45 | 50 | 0.794% | 1.022% | False |
| revised_alternative:progressive_passes | 0.28 / 3.01 / 29.51 | 0.00 / 2.60 / 35.34 | 50 | 0.280% | 0.469% | True |
| revised_alternative:shots | 0.04 / 1.60 / 26.71 | 0.00 / 1.35 / 30.52 | 50 | 0.262% | 0.377% | True |

Each final fit also runs its own prior check with its development covariates and exposures; these results are retained in the fit manifests. A failed prior gate stops fitting. The final alternative uses role/team scale multiplier 1.15 and source elasticity SD 0.40. No prior was selected by held-out accuracy.

Priors and likelihood: [registered experiment](phase-3-experiment-plan.md). Full outputs: `artifacts/phase3/prior_predictive.json`. The negative-binomial dispersion prior creates much wider predictive tails than coefficient uncertainty alone; both are explicitly checked.
