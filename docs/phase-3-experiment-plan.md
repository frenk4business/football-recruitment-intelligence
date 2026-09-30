# Phase 3 registered experiment — conditional WSL season context

Frozen after the evidence audit and before any Bayesian fit or inspection of held-out destination performance. Commit history is the registration record. Any later deviation must be labelled with its reason and whether test outcomes had been inspected.

## Question, population and split

Question: given a player's previous WSL season observation, a specified target role and historically available target-team context, how well can we estimate the next observed season's action rates and uncertainty?

StatsBomb only, revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`, `features-v1`. Require 600 reliable minutes on both sides; same or adjacent outfield roles; consistent provider identity; adjacent observed seasons; no overlap, intervening unknown seasons or gap above 450 days; at least three historical team matches on both sides. Keep major role changes, unsupported teams, zero/low-minute destinations and identity conflicts in the rejection/outcome audit.

Development: 2018/19 source → 2019/20 destination (destination dates 2019-09-07–2020-02-23). SHA-256(`phase3-seed20260930:` + canonical player ID) modulo 5 equal to zero assigns a player to validation: 53 train / 12 validation. All other development players train. Test: 2019/20 source → 2020/21 destination, 76 episodes, destination dates 2020-09-05–2021-05-09. Freeze IDs in `artifacts/phase3/dataset_split.json`.

Training and validation are player-disjoint. Players may recur across earlier development and later test periods, but no test destination row or target event enters a fitted effect, scaler or baseline residual before evaluation. Some test source observations overlap earlier training destinations; those are genuinely available historical information. There is no player-specific fitted effect. Report the distinct-player overlap and a test subgroup of previously unseen players.

The target role is given as a scenario assumption; retrospective evaluation supplies the actual observed destination role. The model does not predict that role, a contract move or destination playing time. Same-role-only sensitivity will quantify dependence on role-change assumptions. All primary targets and diagnostics below are fixed before looking at test outcomes.

## Targets and prediction-time context

Four counts: non-penalty shots, completed progressive open-play passes, progressive carries and provider pressures. Preserve underlying counts and exposure `reliable_minutes / 90`. These span distinct behaviours, have complete coverage in eligible environments, and admit a count likelihood. Do not model xG/xA with a Gaussian rate likelihood; continuous targets are deferred.

Predictors: source action rate, specified destination role, same/adjacent role-change indicator, historically observed destination/source team pass-volume log ratio, and log source minutes relative to 900. Source log rate uses `log((count + 0.5) / (minutes/90 + 0.5))`, a documented finite transform for zero counts, and is centred using training data only. The unchanged-source baseline uses the unmodified observed rate.

Team pass volume, shot volume and possession-sequence share are audited over the 365 days ending at the source environment end date. At least three observed matches per team are required. Only the pass-volume log ratio enters the primary model; the other two remain descriptive checks. No actual destination-season context is substituted. Sequences are not possession duration.

Compute 200 whole-match source bootstraps with deterministic environment/target seeds. Report source-rate standard errors and propagate bootstrap source uncertainty into predictive sensitivity. The primary likelihood conditions on the measured source covariate and includes source exposure as a predictor; this is not a complete errors-in-variables model.

## Baselines

0. Unchanged observed source rate.
1. Destination role mean estimated on training observations; unseen roles fall back to the training population mean.
2. Ridge regression (`alpha=10`) with source rate, source/destination role indicators, role-change indicator, historical source/destination team pass volumes, context log ratio and source minutes. Standardization/encoding fit only on training data; clip negative predicted rates to zero and report that boundary.

For interval comparisons, use a common empirical additive residual distribution obtained from five deterministic player-disjoint training folds, recentered to zero and clipped only at the nonnegative support boundary. These are **empirical predictive intervals**, not Bayesian credible intervals. Report point and probabilistic metrics for every baseline; empirical interval log density is not reported without a defensible density model.

## Bayesian specification and priors

Separate per-target negative-binomial likelihoods: `count ~ NB(mu = destination_exposure * exp(eta), alpha = dispersion)`. Log rate `eta` contains an intercept, centred source log rate, role-change indicator, context log ratio, log source minutes, a non-centred destination-role effect and a non-centred destination-team effect. Role/team effects borrow information through shared scales. There is no competition coefficient, competition-pair coefficient or player intercept. Team hierarchy acknowledges shared team dependence; it does not establish a causal team effect.

Primary priors on log-rate scale: intercept Normal(log(reference rate), 0.5), using fixed reference rates shots 1.5, progressive passes 3, progressive carries 3 and pressures 12. Source elasticity Normal(1, 0.35); context coefficient Normal(0, 0.35); source-minutes coefficient Normal(0, 0.15); role-change coefficient Normal(0, 0.2). Role SD HalfNormal(0.35), team SD HalfNormal(0.25), standardized group offsets Normal(0,1), NB dispersion Exponential(0.1). Centre group offsets for identifiability. No clipping of observations or posteriors.

Prior predictive simulation happens before each fit. Inspect finite, nonnegative rates; report 1st/50th/99th percentiles and the fraction above 50 shots, 50 progressive passes/carries or 150 pressures per 90. More than 1% above the relevant ceiling triggers prior revision **before fitting**, logged separately; these are plausibility checks rather than hard outcome limits.

PyMC CPU NUTS: four chains, 1,000 tuning and 1,000 retained draws each, target_accept .95, fixed seed 20260930. Save local posterior files and compact parameter summaries. Require zero divergences, maximum rank R-hat ≤1.01, bulk ESS ≥400 for key coefficients/scales, and no material tree-depth warnings. If diagnostics fail, increase tune/draws or target_accept according to a documented computational repair; do not select repairs by test accuracy.

## Selection and untouched evaluation

Fit candidates on training only and evaluate on the 12 validation players. For each target, Bayes is eligible as the public default only if diagnostics pass, MAE ≤1.10 times the best baseline MAE, 80% predictive coverage is between .65 and .95 inclusive, and mean 80% width is ≤1.5 times the best baseline width. Otherwise choose the baseline with lowest validation MAE (ties prefer unchanged source, then role mean, then ridge). With 12 validation cases this is a conservative operating rule, not proof of calibration.

Freeze method choices before test evaluation. Refit primary Bayes and all baselines on train+validation, preserving the same priors/specification; then evaluate all methods once on the untouched destination season. Publish weak/negative findings regardless of selection. Do not refit on test destinations for the v1 public model. Public historical scenarios use the development-only fit and explicitly disclose which observations were in-sample or held out.

For each target/model report N, MAE, RMSE, 50/80/95% predictive coverage and width, interval score, and Bayesian log predictive density using the count likelihood. Compare latent expected-rate credible intervals separately from future-observation prediction intervals. Use actual held-out exposure only to evaluate a conditional rate observation; no claim to forecast playing time. Public scenario intervals use a clearly stated 900-minute future observation window.

Posterior predictive checks: observed vs replicated training mean, variance, zeros and upper tail, by role/team where group size permits. Plot and publish every held-out observed/expected pair, calibration and residual distributions. Report source extreme-decile errors to examine regression to the mean. Small subgroup results remain descriptive.

## Registered sensitivity and partial pooling

Repeat the primary specification at 900/900 minutes; same-role-only; a prior with role/team SD scales multiplied by 1.5 and source coefficient SD 0.5; without the team-context coefficient and team random effect; and with bootstrap source uncertainty propagated through predictions. All use the same temporal policy and are reported as sensitivity, not post-test model selection. Four targets are evaluated consistently.

There is only one competition pair (WSL→WSL); removing it leaves no dataset. Report league-pair sensitivity as non-identifiable rather than inventing a second league. Compare actual team-change and same-team transitions, while emphasizing the four primary test team changes. Demonstrate pooling with synthetic low-N groups and report group posterior effects alongside unpooled residual estimates; do not rank teams by these coefficients.

## Engineering, publication and limits

Synthetic tests cover approximate known translation recovery, partial pooling and exposure uncertainty, plus fast model construction/CI smoke sampling. No full research MCMC or source downloads in CI. Cache fits by data/config/code hashes; store provider/feature/DNA/prior/model versions, code commit, dependency/backend versions, seed and sampler settings. A clean fit should reproduce substantively equivalent posterior summaries, not bit-identical chains.

Public: strict derived contracts, expected rate and 80% prediction range, numeric evidence, scope, model/version, source and target environment. Keep 95% summaries in research artifacts. No raw events, provider lineups, full posterior samples, arbitrary leagues, transfer-success score or club recommendation. Major role changes, unavailable historical context, out-of-range source evidence and unsupported periods get explicit states without fabricated numbers.

Principal limits: small development/validation cohorts; observational selection; destination-minute survivorship; incomplete published historical fixtures; an interrupted 2019/20 observation window; supplied target role; historical target context as a proxy; predominantly same-team seasons; no untouched independent provider or competition; no causal effects or general league ranking.
