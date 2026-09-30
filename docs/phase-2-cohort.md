# Player Feature Eligibility Report

Generated before similarity evaluation. StatsBomb FA Women's Super League 2023/2024. 132 matches, 12 teams, 336 roster players; 296 with positive reliable minutes. Coverage: 2023-10-01 to 2024-05-18.

| Minimum reliable minutes | Eligible | Role populations |
|---|---:|---|
| 1200 | 93 | {'CB': 28, 'DM': 15, 'FB/WB': 20, 'ST': 12, 'W': 18} |
| 450 | 186 | {'CB': 44, 'CM': 16, 'DM': 30, 'FB/WB': 37, 'ST': 24, 'W': 35} |
| 600 | 168 | {'CB': 38, 'CM': 15, 'DM': 29, 'FB/WB': 33, 'ST': 21, 'W': 32} |
| 900 | 138 | {'CB': 36, 'CM': 12, 'DM': 22, 'FB/WB': 29, 'ST': 15, 'W': 24} |

All 18 core measures are available for the 296 players with positive reliable minutes. Unused roster players have unavailable rates, not zero. Complete machine-readable exclusions, missingness, quantiles and quality counts: `artifacts/phase2/cohort_eligibility.json`.

Minutes include actual stoppage time. Of 5,102 roster-match records, 5,067 have agreeing lineup/event evidence, 25 are reconciled from the explicit participation timeline, and 10 conflicting records are excluded in full (counts and minutes). Unused substitutes are reliable zero minutes.

Six original roles have at least 12 eligible members at 900 minutes. Keep CM and DM separate. AM is too sparse (four candidates at 900); it is not merged into W. GK requires dedicated features and is excluded. The 12-player minimum makes top-10 stability optimistic for CM; the UI must display cohort size and numeric stability. Primary role requires at least 60% known role time and 40% in the leading role; mixed profiles remain labelled.

The recommended 900-minute threshold is a candidate, not a claim of optimality. Similarity evaluation follows this report.
