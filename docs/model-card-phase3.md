# Model card — historical WSL context translation v1

## Intended use and actual scope

Independent, non-commercial research by Frenk Kester. `translation-model-v1`, `translated-profile-v1`, `features-v1`, observed `player-dna-v1`. This is a **conditional historical WSL season/team-context study**, not a general league translator, player-quality score, transfer-success predictor or club recommendation. Broad cross-league translation is **NO-GO**; this narrower study is **CONDITIONAL**.

The official StatsBomb catalogue was freshly audited at revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`: 80 competition-seasons, 3,961 match lineups, 11,794 distinct provider IDs. Cross-league roster candidates were too sparse and temporally unsuitable under the registered rules. Wyscout/Figshare was audited separately; no cross-provider names or IDs were joined and no Wyscout event features were mixed into these models. [Evidence](phase-3-transfer-evidence.md) · [scope decision](adr/006-phase3-evidence-scope.md).

The selected event dataset comprises 457 published WSL matches across 2018/19, 2019/20, 2020/21 and 2023/24, 660 roster identities and 1,225 environment stints. An environment identifies provider, player, competition, season, team, observation window, role shares and reliable exposure. It is not a verified employment contract. Missing 2021/22–2022/23 seasons are never bridged into direct transfers.

## Selection and validation

Adjacent, nonoverlapping environments only; no identity anomalies, unknown intervening seasons or gaps exceeding 450 days. Require 600 reliable minutes on both sides, same/adjacent outfield roles and three prior team-context matches on both sides. The initial minute-eligible set has 162 episodes; the registered temporal/role/context study has 141: 53 train, 12 validation and 76 later test. The 65 development outcomes end on 2020-02-23; test outcomes start on 2020-09-05. Validation is player-disjoint. Earlier history may recur in the later test, but no player intercept or later outcome is fitted.

The provider catalogue, identity and minute audit were committed before choosing scope. The experiment was committed at `bbed4d2`, model code at `dbd62b4`, validation decision at `a330893`, and held-out results at `a624590`. Final priors were amended only through pre-fit plausibility checks. There was no test-driven model selection. [Registered experiment](phase-3-experiment-plan.md) · [validation decision](phase-3-validation-decision.md).

## Targets, baselines and model

Four targets retain integer action counts and minutes: non-penalty shots, completed progressive open-play passes, progressive carries and StatsBomb pressures. All per90 values are ratios of summed counts/exposure. Existing `features-v1` definitions are reused; xG/xA and other continuous quantities are not incorrectly fitted as counts. Goalkeepers are excluded. Event definitions and role assignment remain observational simplifications.

Three baselines: unchanged source rate; exposure-weighted destination-role mean; ridge regression with alpha 10 and training-only standardization/role indicators. Ridge includes source rate, source exposure, source/destination roles, role change and historically available team pass-volume context. Predictions are clipped at zero. Baseline prediction ranges are centred empirical errors from five deterministic player-separated development folds, with a nonnegative boundary.

Separate hierarchical models use:

`Y ~ NegativeBinomial(mu = destination_minutes / 90 × exp(eta), alpha = dispersion)`

`eta = intercept + source elasticity × centred log source rate + source-minutes coefficient + role-change coefficient + historical pass-volume context coefficient + destination-role effect + destination-team effect`.

The finite source transform is `(count + 0.5)/(minutes/90 + 0.5)`. Role and team effects are non-centred, zero-mean, partially pooled groups. Only one development episode per player is present, so a player random intercept is not justified. Only one league is present, so league/pair effects are not identifiable and are omitted. No competition rankings are produced.

Team context uses only observations in the 365 days ending at the source environment’s last observed date. Team pass volume is normalized by actual match duration, not summed player minutes. Opponent/own possession sequences are descriptive; they are not time in possession. Destination role is an explicit assumption, supplied retrospectively in evaluation; the model does not predict role or playing time.

## Priors and inference

Log intercept Normal(log(reference rate), 0.5), with reference rates 1.5/3/3/12. Source elasticity Normal(1, 0.35); context Normal(0, 0.35); log source-minutes coefficient Normal(0, 0.15); role-change coefficient Normal(0, 0.2). Role SD HalfNormal(0.35), team SD HalfNormal(0.25), standardized group effects Normal(0,1), dispersion Exponential(0.1). The mild alternative uses scale multiplier 1.15 and source SD 0.40.

PyMC 5.28.5 / ArviZ 0.23.4, locked dependencies, four CPU NUTS chains per target, 1,000 tune plus 1,000 retained draws, target acceptance .95, seed 20260930. Prior predictive sampling uses 1,500 draws; both latent and future-observation tails must pass. Two initial alternative-prior settings failed the carry-tail gate and are retained in the audit. [Prior predictive report](phase-3-prior-predictive.md).

Development fits have zero divergences, maximum R-hat 1.0055, minimum key bulk ESS 943 and minimum tail ESS 1,409. All registered sensitivity fits also pass their sampling diagnostics. Overall posterior predictive means/variances/zeros/tails are plausible, with seven local role/team statistic flags. These checks do not negate later-season undercoverage. [Full diagnostics and effects](league-translation-evaluation.md).

## Results and production decision

| Target | Public method | Test MAE | Bayesian MAE | Public 80% cover / width | Bayesian 80% cover / width |
|---|---|---:|---:|---|---|
| Shots | Ridge | 0.397 | 0.404 | 73.7% / 0.969 | 71.1% / 1.131 |
| Progressive passes | Ridge | 0.920 | 0.950 | 71.1% / 1.889 | 64.5% / 1.761 |
| Progressive carries | Unchanged source | 0.500 | 0.550 | 80.3% / 1.552 | 92.1% / 2.034 |
| Pressures | Unchanged source | 2.894 | 3.354 | 76.3% / 8.214 | 80.3% / 10.549 |

All errors/widths are per90, N=76. None of the Bayesian targets passed every precommitted validation eligibility rule. The advanced model is available only as a research comparison. The test did not override this decision. Unchanged-source defaults do not respond to target-team changes; the UI states this explicitly. Baselines are selected reference estimates, not proof that context never matters.

Nominal 80% ranges under-cover shots and progressive passes. The model card and public UI disclose this. There is no calibrated guarantee for a specific player. All four context-effect 95% intervals include no association. With only four test team changes, counterfactual club scenarios are much less validated than same-club season continuity. [Every baseline, interval score, log density, subgroup and sensitivity result](league-translation-evaluation.md).

## Public contract and exclusions

Only 2019/20 source profiles can drive 2020/21 WSL team scenarios. The 660-player catalogue retains other observed seasons with explicit exclusion reasons. 120 players have source-eligible observations; 3,608 supported source/team/role scenarios are generated. Numeric display also requires at least five development episodes in the target role, complete source counts, source rates within development min/max, supported role change and available prior team context. AM remains visible as an insufficient-evidence role. New teams receive a team population prior only if historical context exists; this is marked explicitly.

The five-role-episode and source-range display guards were finalized after evaluating the registered test. They are conservative publication rules, not tuned accuracy filters; the reported test remains all 76 rows. Direct evidence means earlier matching source-team/target-team/target-role episodes, not an observed effect of the hypothetical move. Fewer than five direct episodes triggers a pooling warning. The workflow shows direct N, target-team/role N, target-role N, development N and the context cutoff date.

Each estimate exposes observed source, expected target, predictive p10/p90 and p025/p975, method and interval kind. Bayesian research summaries additionally retain expected-rate p10/p90; these coefficient/latent uncertainties are not substituted for prediction ranges. Bayesian public scenarios simulate a 900-minute future observation. Empirical baseline ranges reflect earlier ≥600-minute windows and are exposure-invariant, so they cannot be claimed as precisely calibrated 900-minute forecasts.

Source-rate sampling uncertainty is examined by 200 whole-match bootstrap resamples. It widens the research ranges but does not solve pass undercoverage. Primary outputs condition on measured source features and are not a full errors-in-variables posterior. Source observations used as earlier development outcomes are flagged; target-season outcomes are never fitted into v1. Observed Player DNA is unchanged.

## Limitations and failure modes

- Published historical fixtures are incomplete/selected. WSL match counts are 107, 87, 131 and 132; one calendar is not necessarily a complete season.
- Only 65 development episodes, 12 validation players, one league, a single later test season and four test team changes. No independent provider replication.
- Conditioning on destination minutes selects players who continued appearing. Among 385 structurally accepted candidates, 33 have zero reliable destination minutes and 116 have fewer than 450; players absent from all destination rosters are unobserved. No success/failure label is inferred.
- Supplied target role and historical team context are imperfect proxies. Opportunity, tactics, ability, injury and selection are confounded. No age adjustment is attempted without reliable birth dates.
- Source uncertainty, shared match dependence, missing-not-at-random selection and season shocks are only partially handled. NB dispersion captures residual variation, not every omitted mechanism.
- Conservative ID metadata quarantines can reject legitimate name/nationality changes. They are not evidence that two people were joined.
- No extrapolation to other leagues, current seasons, arbitrary new roles, tracking physiology, market values or club recommendations.

## Reproduction, rights and operations

`make setup && make translation-audit && make phase3-build`. A fresh install downloads bounded, checksummed inputs; subsequent builds use cache. The committed selection is immutable for v1; `make translation-validate` is an explicit research stage, not part of normal rebuild/deployment. Use `uv run python scripts/phase3_reproduce.py` for a network-disabled reconstruction and fresh primary fits. CI runs synthetic Bayesian recovery/pooling tests and aggregate-contract/browser checks; it does not ingest the catalogue or fit the full research models.

Research posteriors are local and ignored; four development fits occupy about 24 MB. Public summaries total about 14.3 MB across lazy per-player artifacts; the largest player file is about 121 KB. Nothing runs MCMC in a browser or request handler. The public site is static; FastAPI is an optional local view of the same contracts. Source/event/lineup payloads and full posterior draws are excluded by strict publication schemas.

StatsBomb terms, name/logo attribution and non-commercial research boundaries remain in force; code MIT does not replace data rights. [Attribution](../ATTRIBUTION.md). No additional paid Render infrastructure was introduced beyond the existing workspace/Starter subscription. See [deployment](deployment.md) and [Phase 4 hand-off](phase-4-handoff.md).
