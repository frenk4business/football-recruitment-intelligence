# Player feature registry — features-v1

The executable registry is `src/football_intelligence/dna/registry.py`. Player DNA contains 18 core style features in five families. Nine output/context measures are display/research only. All rates aggregate counts and reliable elapsed minutes first; they never average match rates. A conflicting player-match contributes neither actions nor denominator. Zero means observed absence; null means unavailable evidence or an undefined denominator. All 18 core values must exist for eligibility.

Coordinates are actor-relative 105 × 68 reference metres, attacking right. The goal centre is (105,34). Progression is this project's explicit research definition, not a claim to reproduce a vendor metric: `d_start - d_end >= max(10, 0.25*d_start)`. For example (20,34)→(50,34) qualifies; (50,34)→(55,34) and backward (60,34)→(20,34) do not. An explicitly reversed coordinate system is rotated before applying this formula. The penalty box is x≥88.5 and 13.84≤y≤54.16. Off-pitch endpoints are retained; box entries must end in the valid box. Long passes use ≥30 m reference displacement, not the provider's yard length.

Shot assists and xA require reciprocal pass.assisted_shot_id / shot.key_pass_id, same team, same match, later shot and periods 1–4. Penalty shots and shootouts are excluded; set-piece assists remain included. Missing links or xG make the affected value null. Own goals never become shot goals. The shot-assist measure is therefore a count of linked non-penalty shot opportunities, not all assists awarded by another provider.

Possession opportunities are distinct (match,period,possession,owner) sequences with at least one recorded event while the player is on the pitch. They measure sequences, not duration or true possession percentage. Team passing share uses open-play team attempts during the player's participation. Context alternatives remain outside the selected distance; three replacements were evaluated without a consistent benefit. Field tilt, possession-duration adjustment and aerial-duel reconstruction are deferred because further definition validation would be needed. No missing feature is imputed.

| ID | English | Nederlands | Family | Core | Unit | Formula |
|---|---|---|---|---|---|---|
| `shots_per90` | Non-penalty shots | Schoten zonder penalty's | shooting | True | per90 | 90 * sum(Shot, excluding Penalty and period 5) / sum(reliable elapsed minutes) |
| `box_shots_per90` | Shots from the box | Schoten uit het strafschopgebied | shooting | True | per90 | 90 * sum(Non-penalty Shot starting in x>=88.5, 13.84<=y<=54.16) / sum(reliable elapsed minutes) |
| `shot_assists_per90` | Shot assists | Schotassists | creation | True | per90 | 90 * sum(Pass with explicit assisted_shot_id and reciprocal shot.key_pass_id; non-penalty Shot) / sum(reliable elapsed minutes) |
| `box_passes_per90` | Passes into the box | Passes naar het strafschopgebied | creation | True | per90 | 90 * sum(Completed open-play Pass from outside to inside penalty area) / sum(reliable elapsed minutes) |
| `crosses_per90` | Completed crosses | Aangekomen voorzetten | creation | True | per90 | 90 * sum(Completed open-play Pass with pass.cross=true) / sum(reliable elapsed minutes) |
| `passes_per90` | Passing volume | Passvolume | passing | True | per90 | 90 * sum(All attempted open-play Pass events; exclude Corner, Free Kick, Throw-in, Kick Off, Goal Kick) / sum(reliable elapsed minutes) |
| `progressive_passes_per90` | Progressive passes | Progressieve passes | passing | True | per90 | 90 * sum(Completed open-play Pass reducing distance to goal (105,34) by >=max(10m,25% of starting distance)) / sum(reliable elapsed minutes) |
| `final_third_passes_per90` | Final-third entries by pass | Passes naar het laatste derde | passing | True | per90 | 90 * sum(Completed open-play Pass from x<70 to end_x>=70) / sum(reliable elapsed minutes) |
| `long_passes_per90` | Long passes | Lange passes | passing | True | per90 | 90 * sum(Open-play Pass with canonical Euclidean start-to-end distance >=30m; attempts) / sum(reliable elapsed minutes) |
| `carries_per90` | Carrying volume | Baldribbelvolume | carrying | True | per90 | 90 * sum(Provider Carry event count; no synthetic carries) / sum(reliable elapsed minutes) |
| `progressive_carries_per90` | Progressive carries | Progressieve baldribbels | carrying | True | per90 | 90 * sum(Carry reducing distance to goal (105,34) by >=max(10m,25% of starting distance)) / sum(reliable elapsed minutes) |
| `carry_distance_per90` | Carry distance | Baldribbelafstand | carrying | True | m / 90 | 90 * sum(Sum of Euclidean Carry displacement in reference metres; not physical tracking distance) / sum(reliable elapsed minutes) |
| `box_carries_per90` | Carries into the box | Baldribbels naar het strafschopgebied | carrying | True | per90 | 90 * sum(Carry from outside to inside penalty area) / sum(reliable elapsed minutes) |
| `pressures_per90` | Pressures | Drukacties | defending | True | per90 | 90 * sum(Provider Pressure event count; no inferred off-ball pressure) / sum(reliable elapsed minutes) |
| `counterpressures_per90` | Counterpressures | Tegendrukacties | defending | True | per90 | 90 * sum(Pressure with counterpress=true) / sum(reliable elapsed minutes) |
| `tackles_per90` | Tackles | Tackles | defending | True | per90 | 90 * sum(Duel with type Tackle; all outcomes) / sum(reliable elapsed minutes) |
| `interceptions_per90` | Interceptions | Onderscheppingen | defending | True | per90 | 90 * sum(Interception event count; all outcomes) / sum(reliable elapsed minutes) |
| `recoveries_per90` | Ball recoveries | Balheroveringen | defending | True | per90 | 90 * sum(Ball Recovery event count; all outcomes) / sum(reliable elapsed minutes) |
| `goals` | Non-penalty goals | Doelpunten zonder penalty's | output | False | count | Non-penalty Shot with outcome Goal; own goals excluded |
| `npxg_per90` | Non-penalty xG | xG zonder penalty's | output | False | per90 | 90 * sum(provider xG of non-penalty shots) / reliable minutes |
| `xg_per_shot` | xG per shot | xG per schot | output | False | xG / shot | Non-penalty xG / non-penalty shots; no shots -> null |
| `xa_per90` | Linked expected assists | Gekoppelde verwachte assists | output | False | per90 | 90 * sum(non-penalty shot xG linked reciprocally to assist pass) / reliable minutes; includes set pieces |
| `pass_completion` | Open-play pass completion | Passnauwkeurigheid in open spel | output | False | fraction | Completed open-play passes / attempted open-play passes; no passes -> null |
| `pressures_per100_opponent` | Pressures per 100 opponent possessions | Drukacties per 100 balbezitreeksen tegenstander | context | False | per100 | 100 * Pressure / distinct opponent (match, period, possession) sequences with an event during participation |
| `interceptions_per100_opponent` | Interceptions per 100 opponent possessions | Onderscheppingen per 100 balbezitreeksen tegenstander | context | False | per100 | 100 * Interception / distinct opponent possession sequences during participation |
| `progressive_passes_per100_team` | Progressive passes per 100 team possessions | Progressieve passes per 100 eigen balbezitreeksen | context | False | per100 | 100 * progressive Pass / distinct own-team possession sequences during participation |
| `team_pass_share` | Share of team passes while playing | Aandeel teampasses tijdens speeltijd | context | False | fraction | Player open-play attempts / team open-play attempts during player participation |

## Source/conversion assessment

[StatsBomb's official source repository](https://github.com/statsbomb/open-data) defines event fields. [socceraction SPADL documentation](https://socceraction.readthedocs.io/en/latest/documentation/spadl/spadl.html) describes an on-ball action schema with 105×68 coordinates and original-event links, but also inserts synthetic dribbles and omits pressure events. Canonical events can map ID, period, seconds, actor, team, coordinates, type, outcome and body part into SPADL; its home-team direction convention requires explicit rotation. Replacing this canonical layer would lose required pressure/context evidence. Decision: retain the existing model; no runtime socceraction dependency or purported independent action-count benchmark in this release. Its converter is a future validation experiment, not an authority that overrides discrepancies. xT and VAEP are not computed.

Dutch definitions and methodological explanations are authored manually in the application. They are not machine-translated at runtime.

