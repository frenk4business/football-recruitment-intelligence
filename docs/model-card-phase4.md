# Model card — Recruitment Fit v1

This is a deterministic decision-support rule, not a trained transfer-success model. Owner: Frenk Kester. Version: `recruitment-fit-v1`; requirements `requirements-v1`; context `club-context-v1`. [Evaluation](recruitment-fit-evaluation.md) and [registered experiment](phase-4-experiment-plan.md) define its empirical scope.

## Intended use and users

Analysts can express an observed playing-style requirement, inspect within-role candidates, compare up to three profiles, and examine weight/profile sensitivity. The interface supports Find Candidates, Replace a Player and Club Context in English and Dutch. A ranking orders evidence under selected criteria and leaves the football decision to a person.

Not intended for recruitment recommendations, predicting transfer success, judging overall player quality, current player availability, league strength, 2024/25 forecasts, betting, market values, medical assessment or employment decisions without independent evidence. No actual transfer opportunity set or success label exists. There is no LLM or external model API in ranking, explanations or scenario construction.

## Data and observation windows

StatsBomb Open Data, revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`. FA Women's Super League 2023/24: 132 matches, twelve clubs, 336 roster identities. The existing `player-dna-v1` / `features-v1` rules yield 138 complete ≥900-minute profiles: CB 36, CM 12, DM 22, FB/WB 29, ST 15, W 24. Users can tighten the minute boundary; lowering it is unsupported. AM has insufficient comparison evidence, GK is out of scope. Candidate percentiles remain against the original role cohort when filters change.

Five eligible candidates have multiple observed clubs and use labelled whole-season DNA. Club-role reference medians use player events from that club stint only, requiring 900 reliable stint minutes; low-minute/unknown profiles remain in roster exposure summaries with reasons. Team context counts events once per team and divides by actual period-end match duration, including goalkeeper actions. Fourteen team rates and within-season percentiles describe the observation window, not a permanent club identity. Missing fields remain unavailable, distinct from measured zero.

## Requirements and scoring

Each requirement records ID, known feature, type (style preference / target profile / club context), source (user-defined / adopted observed club context / replacement player / derived roster reference), preference, target percentile, importance and optional hard threshold. The eighteen existing core style features span shooting, creation, passing, carrying and defensive activity. Role-specific visibility is a UI convenience; it does not imply an expert-validated role template.

Custom requirements start neutral. Replacement targets use the selected eligible player's exact percentiles; adjustments become visible user assumptions. An adopted roster median is an exact target; adopting a team percentile creates a player-role minimum. The latter mapping is an explicit analyst assumption and is not empirically calibrated. The reference player is always excluded.

Hard filters run first: valid provider/cohort/role, existing DNA eligibility, minimum reliable minutes, optional candidate team, optional same-club exclusion, optional minimum neighbour stability and hard feature minima/maxima. Every excluded identity retains all relevant reasons. No age filter is provided because birth dates are missing for all 336 players. No nationality, fee, salary, contract or market-value fields are introduced.

For feature j, let d_j be absolute deviation for exact, positive shortfall for minimum, positive excess for maximum, and absent for neutral. Effective weight w_j = feature importance × family importance; both are explicit integers 1/2/3 and default to one. Fit distance is `sqrt(sum(w_j*d_j²)/sum(w_j))`, in percentile points, **lower = closer**. It is not a probability or a 0–100 suitability rating. Evidence never contributes to this distance. Equal explicit features have equal weight; families containing more active features can contribute more, which is visible and adjustable.

The strongest-match and largest-mismatch explanations come from actual criteria and squared contributions, with sources and targets visible. Family contribution totals sum feature shares. UUID order resolves ties after distance rounding to nine decimals. The Pareto frontier uses each active mismatch independently: no other candidate is no worse on all and strictly better on one. Ties remain non-dominated. A large frontier is weak information, not many optimal players.

## Development, evaluation and negative results

The chronological audit/registration/selection commits are documented in the evaluation. Eight development query clubs and four final query clubs share some candidates; the season was previously studied in Phase 2. Weighted RMS was selected before final queries using continuous semantics, transparency, development MRR above chance and weight Jaccard ≥.65. The family-balanced comparator also passed; no tiny difference was treated as proof of superiority.

Final later-half peer retrieval: 31 queries, Recall@5 .452, Recall@10 .806, MRR .258; random .316/.632/.210; existing DNA .419/.806/.259. Final roster holdout: 27 queries, weighted MRR .232 versus DNA .332 and chance .160. Context improves some roster metrics, but worsens final common-query peer MRR .223 → .210. Threshold/hybrid comparisons and poor subgroup results are retained. These retrospective, representation-derived labels do not demonstrate expert scouting validity or transfer success. Historical success evaluation is NO-GO.

Across 205 scenarios, 100 ±20% weight changes give mean top-10 Jaccard .950; 100 player-match bootstraps give .723. Excluding pools of ten or fewer gives .946/.703. Fourteen small CM scenarios force top-ten inclusion. Custom frontier median is 2.5; eighteen-feature replacement frontier median is 22, illustrating weak discrimination in many dimensions.

## Uncertainty and failure modes

Weight sensitivity and profile sampling are separate, never a combined confidence score. Bootstrap whole player-match rows preserve joint feature counts and minutes. Players are sampled independently; role reference ECDF, targets, eligibility and hard constraints are held fixed. Shared team/match dependence, target uncertainty, role uncertainty, tactical change and uncertainty about meeting hard constraints are not modelled. Published draws are rounded to 0.1 percentile points. Rank intervals and top-ten inclusion are sensitivity descriptions, not calibrated confidence or success probability.

Percentiles hide absolute-rate gaps and depend on a small role cohort. Observed actions reflect team tactics and opportunity as well as player behaviour. Roster conformity need not be complementary fit. Query and candidate overlap, conditioning on later-half exposure, missing low-minute outcomes, weak final subgroup sizes, and prior examination of the season limit generalisation. Whole-season summaries cannot serve as decision-date features.

## Translation boundary

No Phase 3 prediction enters observed 2023/24 recruitment scoring. The product states that no validated translation model supports this environment. A separate link opens the historical 2019/20 → 2020/21 WSL study, retaining its unchanged source/ridge defaults, calibration undercoverage and cross-league NO-GO. No universal league coefficient or 2024/25 expected profile is created.

## Implementation, publication and governance

Python is canonical. A single declarative scoring specification generates browser metadata; ten Python reference scenarios verify TypeScript ranking, exclusions, contributions, Pareto and separate robustness at 1e-7 tolerance. Strict Pydantic allowlists validate twenty public derived JSON artifacts. Initial loading fetches the 206,564-byte index and one club detail; role bootstrap samples load only when robustness is opened. No raw event/lineup/provider payload is published. StatsBomb attribution/logo remain visible.

Scenarios live in versioned, validated URL state and can be copied/reset; no account or hosted database is needed. FastAPI is optional/local. The existing Render static site serves precomputed aggregates; no hosted inference or added service is required. Manifests record schema/feature/method versions, source and code hashes, plan/selection hashes, seeds and payload hashes. `make phase4-build` and `make recruitment-evaluate` reproduce artifacts and evidence without reselecting the method. Semantics changes require a new version and preregistration. [QA](phase-4-qa.md) records actual checks; [Phase 5 hand-off](phase-5-handoff.md) records remaining work.
