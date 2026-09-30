# Phase 3 validation decision — frozen before test evaluation

The registered models were fitted to 53 training episodes and assessed on 12 validation players. No 2020/21 destination outcome has been evaluated at this decision boundary.

| Target | Unchanged MAE | Role mean MAE | Ridge MAE | Bayes MAE | Bayes 80% coverage | Selected public default |
|---|---:|---:|---:|---:|---:|---|
| Non-penalty shots | 0.485 | 0.506 | 0.438 | 0.404 | 58.3% | Ridge |
| Progressive passes | 1.094 | 1.307 | 0.570 | 0.757 | 91.7% | Ridge |
| Progressive carries | 0.326 | 0.687 | 0.402 | 0.388 | 91.7% | Unchanged source |
| Pressures | 1.738 | 3.752 | 2.544 | 1.996 | 100.0% | Unchanged source |

All four Bayesian fits pass diagnostics: zero divergences, maximum R-hat below 1.006 and minimum key bulk ESS above 994. Convergence does not establish predictive usefulness. Shots fail the registered coverage rule; progressive passes/carries fail the relative point-error rule; pressures fail point-error and coverage rules. No Bayesian target is selected as the public default. Baseline prediction ranges remain empirical, not posterior credible intervals.

These choices are frozen now. Refit all models on the 65 development observations, then evaluate every baseline and Bayes on the 76 later-season cases and run the registered sensitivity checks. Report the results regardless of which method wins on that test. The public default will not be changed in response to the test results. Bayesian posterior summaries, partial-pooling evidence and diagnostics remain research outputs; the product must identify any optional Bayesian comparison as such.

Machine record: `artifacts/phase3/validation.json`. The small validation sample makes the selection uncertain; it is an operational rule for this release, not evidence that the selected methods are universally best.
