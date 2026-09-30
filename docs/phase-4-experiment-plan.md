# Phase 4 registered recruitment experiment

Status: registered after evidence/schema checkpoint `b2a6d57`, before scoring implementation or Phase 4 evaluation. Prior model versions are immutable. Seed 20260930; `requirements-v1`, `club-context-v1`, `recruitment-fit-v1`.

## Estimand and limits

Fit means mismatch between a candidate's observed role-relative feature profile and explicitly selected analyst requirements. It is not quality, success probability, or a transfer recommendation. Evidence and predictive uncertainty are not fit dimensions. Historical transfer-success evaluation is NO-GO for the reasons in the evidence audit. No learning-to-rank labels exist.

Use the established WSL 2023/24 900-minute cohort (138 players, six supported roles). Player DNA percentiles retain their original role cohort even when a user filters candidates; filtering cannot change an individual's observed feature value. Minimum minutes can only tighten the 900-minute boundary. Reference players and hard-constraint failures are excluded before ranking, with reasons.

## Candidate methods, before results

1. **Weighted Euclidean/RMS percentile mismatch:** exact = absolute candidate minus target; minimum = max(target minus candidate, 0); maximum = max(candidate minus target, 0); neutral ignored. Distance is the square root of the weighted mean squared percentile-point mismatches. Effective weight is feature importance times family importance; both default to one. Equal explicit requirements therefore have equal default weight.
2. **Family-balanced RMS:** average weighted squared mismatches within each active family, then average across active families. This prevents feature-count dominance, at the cost of changing relative feature weights when features are added to a family.
3. **Requirement satisfaction:** weighted proportion outside their allowed direction/threshold; exact preferences use a registered ten-percentile-point tolerance. This loses mismatch magnitude and creates ties.
4. **Hybrid:** sort first by number of unmet selected requirements (using the same tolerance), then by weighted RMS distance. It preserves severity within the unmet-count tier but can change abruptly at thresholds.
5. Existing **Player DNA nearest neighbour**, role-specific standard scaling and family-balanced raw-rate Euclidean distance, is the representation baseline. Random ordering supplies analytic expectations.

Public preference is a transparent distance in percentile points (lower is closer), not an arbitrary 0–100 rating. Candidate order ties break by stable player ID. Explanations show actual per-feature/family weighted squared contributions and signed shortfalls. Neutral dimensions are absent from both distance and explanations. Fit and evidence never multiply or average together.

## Development and final query partition

Sort the twelve club IDs by SHA256(`phase4-seed20260930:` + club_id). The first eight are development query clubs; the remaining four are final query clubs. Persist their IDs before evaluating methods. Query players with multiple observed clubs are excluded to avoid ambiguous query assignment; they may remain labelled candidate composites in the public full-season tool. Candidate pools can be shared across query partitions; therefore final queries are not an independent population sample. The raw 2023/24 season was already studied in Phase 2. This is a newly registered Phase 4 query holdout, not an untouched football season.

Run development first and commit the public method decision before reading final-query metrics. No tuning against final metrics; report every registered comparator. Selection is primarily semantic: require continuous severity, directional preference correctness, neutrality, hard-constraint correctness, determinism and separation of evidence. Prefer weighted RMS if its development known-peer MRR exceeds the analytic random expectation and its mean top-10 weight-perturbation Jaccard is at least .65. If it fails, family-balanced RMS must pass the same gates. If neither passes, withhold a default public ordering pending a new documented experiment. Binary/hybrid comparators are reported but their discontinuities fail the desired continuous-severity criterion. Differences of .01 do not select a winner.

## A — temporal known-peer retrieval

Reuse the Phase 2 common median match-date split and paired profiles with at least 450 reliable minutes in each half and stable supported role. Freeze the same audited full-season eligibility boundary. The source query and candidates use earlier-half features; the query player is removed from its candidate universe. The evaluation label is the query's nearest *other* role peer in the later half using the Phase 2 representation fitted on earlier-half observations only. This is explicitly representation consistency, not an external scouting judgement.

For percentile methods, fit empirical percentile reference distributions on the earlier-half role group and transform earlier values; later outcomes do not fit scoring transforms. Exact requirements use the earlier query profile. Compare all four scoring designs and the Phase 2 baseline. Report Recall@1/5/10, MRR, candidate sizes, per-role results and each query's rank. Random expectation is min(k,N)/N for recall and harmonic(N)/N for reciprocal rank. Small groups are never omitted to improve metrics.

## B — leave-one-player-out roster alignment and context ablation

For each single-club eligible query whose club-role has at least three eligible single-club members, remove the query from all reference summaries. Candidates are all other same-role eligible players plus the held-out query, so retrieval of the query is possible. Remaining club members are excluded from candidates to avoid trivially retrieving target construction inputs. No held-out player's values enter the role target or percentile/scaling reference distribution.

Construct exact requirements for progressive passing, progressive carrying and pressures using remaining role-mates' median percentiles. Compare random order, Phase 2 raw-rate distance to the remaining roster median, and each registered requirement method. Also compare requirements only against (a) 75% requirement squared distance + 25% full role-median squared distance and (b) 50% requirements + 25% role median + 25% team-context squared distance.

The team-context ablation uses matching count definitions (exclude xG) and same-season team percentiles. Remove the held-out player's team event counts before recomputing the target team's context percentiles. Retain actual team minutes. This prevents direct held-out contribution leakage, but is only a descriptive leave-one-player-out team context—not a counterfactual team without that player. Team percentiles are not player-role percentiles; this ecological mismatch is an explicit limitation of the ablation.

Report held-out rank, normalized rank, Recall@5/10 and MRR, with candidate-specific random expectations. Full club context is not silently incorporated into public ranking: the user must explicitly adopt a contextual characteristic as a requirement. Even retrospective gains would not authorize hidden criteria or establish recruitment success.

## C — requirements reconstruction and replacement consistency

For each development/final query, create exact percentile requirements, remove the query and compare nearest peer sets with the unchanged Phase 2 neighbours. Report top-10 Jaccard as representation agreement, not correctness. Synthetic profiles separately verify that a target-identical candidate has zero distance, worse active mismatch increases distance, satisfying a minimum is not punished, and evidence changes do not change fit. Exercise minimum, maximum, exact, neutral and mixed requirements; validate exclusions and deterministic ties.

## D — two separate robustness analyses

Weight sensitivity: 100 deterministic perturbations independently multiply each active effective feature weight by a uniform factor in [0.8,1.2]. Use a shared 32-bit LCG specification for Python/browser parity; fixed seed and stable feature ordering. Keep targets and candidates fixed. Report per-candidate top-10 inclusion, 10th/90th rank range, and mean top-10 Jaccard against the unperturbed ordering. Hard constraints remain fixed.

Profile uncertainty: 100 whole player-match bootstraps, with replacement independently per candidate; preserve joint feature counts and minutes within each sampled player-match. Rebuild rates, transform against the fixed original role reference distribution, and quantize only published percentile samples to 0.1 point. Freeze eligibility, roles, targets and requirement weights. Rank bootstrap profiles with the selected method; report inclusion, rank range and Jaccard separately from weight sensitivity. Shared team/match dependence and target uncertainty are not modelled; this is sensitivity, not calibrated confidence.

Assess both full replacement profiles and three-feature custom research scenarios for each supported club-role group. Registered custom requirements: progressive passes minimum 75, progressive carries minimum 70, pressures minimum 75, equal weight. These are explicit research assumptions, not a football philosophy or the default UI. Higher moments/quantiles and per-role results accompany aggregate robustness. Record both small candidate pools (N≤10) and larger pools because small pools force top-10 inclusion to 100%.

## E — Pareto trade-offs

Use nonnegative mismatch on each active requirement as separate minimization criteria. Candidate A dominates B only when A is no worse on every criterion and strictly better on at least one. Equal candidates remain non-dominated. Excluded candidates and evidence metrics never enter the frontier. Report active criteria, eligible N, frontier N and frontier membership sensitivity to profile samples. Weight perturbations cannot change this unweighted frontier. Show frontier flags/counts alongside a bounded shortlist, not dozens of alleged optimal players.

## Publication and reproducibility gates

Python is canonical. One committed declarative scoring specification supplies preference loss, aggregation, ties, versions and deterministic perturbation settings to both implementations. Generated TypeScript metadata and Python-produced reference scenarios must verify browser ordering, distances, explanations, exclusions, Pareto membership and robustness within documented tolerance.

Publish only typed derived aggregates. Initial client data is a compact candidate index and registry; club details and role bootstrap summaries load on demand. Preserve Phase 2 and Phase 3 artifacts byte-for-byte. No raw event, lineup or provider payload is added to public assets. Full research runs outside ordinary CI; compact fixtures/contract checks run in CI. Record source hashes, code/plan/selection commits, seeds, payloads, clean rebuild results and all deviations.
