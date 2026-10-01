# Provider feature semantics — common-profile-v1

Official sources: StatsBomb's [event specifications](https://github.com/hudl/open-data/tree/master/doc), Figshare's [events documentation](https://figshare.com/articles/dataset/Events/7770599), [event dictionary](https://figshare.com/articles/dataset/Mapping_of_event_identifiers_to_event_names/11743836) and [tag dictionary](https://figshare.com/articles/dataset/Mapping_of_tag_identifiers_to_tag_names/11743818). The exact downloaded CSVs and provider revisions are hash-pinned in `config/v11-sources.json`. These mappings are separate from the native canonical event tables.

| Concept | StatsBomb definition | Wyscout definition | Harmonised? | Notes |
| --- | --- | --- | --- | --- |
| Non-penalty shots | `Shot`, excluding shot type Penalty | Event 10 Shot plus event 3/subevent 33 Free kick shot; exclude 3/35 Penalty | Yes | Includes direct free-kick shots; does not use provider xG or count penalty shootouts |
| All pass attempts | All `Pass` events, including restarts | Event 8 Pass plus 3/{30,31,32,34,36}: corners, free-kick passes/crosses, goal kicks and throw-ins | Yes, conservative operational mapping | Includes head/hand passes. Collection policies for directed recoveries may differ; provider-bias evaluation is essential |
| All-pass completion | Absent pass outcome means complete; known failed outcomes mean failed; Unknown remains unavailable | Exactly one of tags 1801 accurate / 1802 inaccurate | No, availability screen | Neither or both Wyscout tags makes completion unavailable; no attempt denominator yields null, not zero |
| Geometric long passes | All-pass endpoint Euclidean distance ≥30 m on canonical pitch | Same geometry, same all-pass set | Yes | Attempts, not just completions; restart involvement remains part of the measured quantity |
| Progressive passes | Completed all-pass actions reducing distance to (105,34) by ≥max(10 m, 25% of starting distance) | Same geometry and completion rule | No, availability screen | No provider “progressive” tag; includes restarts |
| Final-third pass entries | Completed all-pass actions from x<70 to x≥70 | Same geometry and completion rule | No, availability screen | Counts crossings, not passes already inside the final third |
| Penalty-area pass entries | Completed all-pass actions from outside to inside x≥88.5, 13.84≤y≤54.16 | Same geometry and completion rule | No, availability screen | Same nominal 105×68 pitch; not an estimate of every real stadium's dimensions |
| Open-play passes | Pass type excludes Corner/Free Kick/Throw-in/Kick Off/Goal Kick | Event 8 excludes listed restart event types but includes kickoff passes | No | Kickoff lacks an equivalent explicit Wyscout subtype. Native registries retain distinct definitions |
| Crosses | Pass cross flag | Pass subevent 80 (and separate restart crossing subtypes) | Native only | Provider annotation/ontology differs; not admitted solely by similar wording |
| Key passes / shot assists | Explicit assisted-shot links/shot-assist flag | Tag 302 | Native only | Tag is not assumed to equal a reciprocal shot linkage |
| Dribbles/carries | Separate Dribble and Carry events | Ground attacking duels, take-on tags and acceleration subevents | No | A duel participant or acceleration is not a StatsBomb carry trajectory |
| Tackles | Tackle subtype of Duel | Sliding-tackle tag 1601 / ground defending duels | Native only | A sliding tackle is a subset, not an all-tackle equivalent |
| Interceptions | Interception event and sometimes pass type | Tag 1401 on other native event types | Native only | Different event vs qualifier counting units |
| Recoveries | Ball Recovery event | No directly equivalent standalone event | No | Do not derive from vague loose-ball-duel labels |
| Duels | Provider-specific subset and event structure | Paired offensive/defensive/air/loose-ball duels | Native only | Paired-event counting and outcomes differ |
| Pressure/counterpressure | Explicit Pressure and counterpress flag | No equivalent event | No | Unavailable is not zero |
| xG/xA and possession-adjusted rates | Provider model/linkage and possession segmentation | No same model or identical possession definition | No | No provider-model output enters the common vector |

## Coordinates and denominators

Both sources describe actions in the attacking team's direction. StatsBomb (120×80) maps to (105×68) by x×105/120 and y×68/80; Wyscout percentages map by x×1.05 and y×0.68. Origin is the attacking side's upper-left touchline/corner, own goal (0,34), opponent goal (105,34). Both providers already encode attacking direction; applying home/away or second-half flips would be an error. Original coordinates remain in canonical storage. Invalid/missing pass endpoints withhold geometric rates for that player's aggregation; no zero imputation.

Every common per-90 numerator covers the included, reliable, regular-time matches including stoppage-time events. The denominator is nominal regulation participation: two 45-minute halves, with substitutions/cards reconciled and times clipped at regulation half/full-time. This is a standardised exposure convention, not exact elapsed playing time. Wyscout substitution annotation has minute precision; source/event disagreement greater than two nominal minutes is a participation conflict. Missing card timing, inconsistent rosters/substitutions and absent full-half evidence are withheld. Extra-time matches are outside this domestic release. A whole-season profile with unresolved participating-match conflict is withheld from searchable/common output rather than silently dropping inconvenient matches.

StatsBomb native v2 adopts the same explicit nominal denominator for this new discovery product; original elapsed-minute `features-v1` and Player DNA remain untouched. Wyscout broad DEF/MID/FWD metadata roles remain broad. Comparability/similarity uses these explicit families, not invented CB/DM labels.

## Pre-evaluation change from candidate plan

The official CSV audit found that Wyscout lacks a distinct kickoff pass label. Before computing expanded profiles or evaluation results, the proposed **open-play** common pass set was therefore replaced by an explicitly named **all-pass including restarts** set. Seven initial candidate features were `non_penalty_shots_per90`, `passes_all_per90`, `pass_completion_all`, `long_passes_all_per90`, `progressive_passes_all_per90`, `final_third_entries_all_per90`, `box_entries_all_per90`. This avoids silently calling the two native open-play pass definitions equal. Provider distributions and held-out classification still test whether the resulting operational harmonisation is adequate for cross-provider similarity.

## Final availability decision

The candidate matrix above records the semantic investigation; it does not imply final inclusion. The full source missingness screen is stored in `artifacts/v11/candidate-availability.json`. Legitimate StatsBomb `Unknown` pass outcomes withhold completion and completed-geometric rates. Requiring complete seven-feature seasons leaves insufficient StatsBomb development cohorts. Instead of imputing these outcomes, the final common registry contains **only non-penalty shots per90, all pass attempts per90 and long pass attempts ≥30 m per90**. Completion, progression, final-third entries and box entries are rejected from common v1 after availability validation. Their candidate definitions and equivalent-action tests remain reproducible, but no public common comparison or ranking uses them. This trades descriptive detail for honest common coverage, not weaker per-profile eligibility.
