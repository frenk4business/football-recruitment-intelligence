# Phase 3 transfer evidence feasibility audit

Measured before model fitting. Protocol: [registered audit rules](phase-3-audit-protocol.md). Raw sources and per-match/identity records remain local; committed files are derived audit aggregates.

## Official-source discovery

[StatsBomb official repository](https://github.com/statsbomb/open-data) was freshly verified at `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`: 80 competition-seasons and 3,961 distinct match lineups audited. The licence PDF was retrieved again at this revision; source attribution/logo and non-commercial aggregate-publication restrictions remain applicable. See `config/phase3.sources.json` for URLs, byte counts and checksums.

Coverage is observed catalogue coverage, not an assumption of full seasons. Bundesliga 2015/16 and 2023/24 each have 34 matches, while most La Liga seasons contain a selected-club sample. Broad women’s 2023/24 coverage does not by itself create longitudinal transfer evidence. International tournaments and club cups are classified separately and excluded from the domestic-transition screen.

| Competition | Season | Matches | Teams | Observed dates |
|---|---|---:|---:|---|
| 1. Bundesliga | 2023/2024 | 34 | 18 | 2023-08-19–2024-05-18 |
| 1. Bundesliga | 2015/2016 | 34 | 18 | 2015-08-15–2016-05-14 |
| African Cup of Nations | 2023 | 52 | 24 | 2024-01-13–2024-02-11 |
| Champions League | 2018/2019 | 1 | 2 | 2019-06-01–2019-06-01 |
| Champions League | 2017/2018 | 1 | 2 | 2018-05-26–2018-05-26 |
| Champions League | 2016/2017 | 1 | 2 | 2017-06-03–2017-06-03 |
| Champions League | 2015/2016 | 1 | 2 | 2016-05-28–2016-05-28 |
| Champions League | 2014/2015 | 1 | 2 | 2015-06-06–2015-06-06 |
| Champions League | 2013/2014 | 1 | 2 | 2014-05-24–2014-05-24 |
| Champions League | 2012/2013 | 1 | 2 | 2013-05-25–2013-05-25 |
| Champions League | 2011/2012 | 1 | 2 | 2012-05-19–2012-05-19 |
| Champions League | 2010/2011 | 1 | 2 | 2011-05-28–2011-05-28 |
| Champions League | 2009/2010 | 1 | 2 | 2010-05-22–2010-05-22 |
| Champions League | 2008/2009 | 1 | 2 | 2009-05-27–2009-05-27 |
| Champions League | 2006/2007 | 1 | 2 | 2007-05-23–2007-05-23 |
| Champions League | 2004/2005 | 1 | 2 | 2005-05-25–2005-05-25 |
| Champions League | 2003/2004 | 1 | 2 | 2004-05-26–2004-05-26 |
| Champions League | 1999/2000 | 1 | 2 | 1999-11-23–1999-11-23 |
| Champions League | 1972/1973 | 1 | 2 | 1973-05-30–1973-05-30 |
| Champions League | 1971/1972 | 1 | 2 | 1972-05-31–1972-05-31 |
| Champions League | 1970/1971 | 1 | 2 | 1971-06-02–1971-06-02 |
| Copa America | 2024 | 32 | 16 | 2024-06-21–2024-07-15 |
| Copa del Rey | 1983/1984 | 1 | 2 | 1984-05-05–1984-05-05 |
| Copa del Rey | 1982/1983 | 1 | 2 | 1983-06-04–1983-06-04 |
| Copa del Rey | 1977/1978 | 1 | 2 | 1978-04-19–1978-04-19 |
| FA Women's Super League | 2023/2024 | 132 | 12 | 2023-10-01–2024-05-18 |
| FA Women's Super League | 2020/2021 | 131 | 12 | 2020-09-05–2021-05-09 |
| FA Women's Super League | 2019/2020 | 87 | 12 | 2019-09-07–2020-02-23 |
| FA Women's Super League | 2018/2019 | 107 | 11 | 2018-09-09–2019-05-11 |
| FIFA U20 World Cup | 1979 | 1 | 2 | 1979-09-07–1979-09-07 |
| FIFA World Cup | 2022 | 64 | 32 | 2022-11-20–2022-12-18 |
| FIFA World Cup | 2018 | 64 | 32 | 2018-06-14–2018-07-15 |
| FIFA World Cup | 1990 | 1 | 2 | 1990-06-24–1990-06-24 |
| FIFA World Cup | 1986 | 3 | 4 | 1986-06-22–1986-06-29 |
| FIFA World Cup | 1974 | 6 | 6 | 1974-06-19–1974-07-07 |
| FIFA World Cup | 1970 | 6 | 7 | 1970-06-03–1970-06-21 |
| FIFA World Cup | 1962 | 1 | 2 | 1962-05-30–1962-05-30 |
| FIFA World Cup | 1958 | 2 | 3 | 1958-06-24–1958-06-29 |
| Frauen Bundesliga | 2023/2024 | 132 | 12 | 2023-09-15–2024-05-20 |
| Indian Super league | 2021/2022 | 115 | 11 | 2021-11-19–2022-03-20 |
| La Liga | 2020/2021 | 35 | 19 | 2020-09-27–2021-05-16 |
| La Liga | 2019/2020 | 33 | 20 | 2019-09-21–2020-07-19 |
| La Liga | 2018/2019 | 34 | 20 | 2018-08-18–2019-05-19 |
| La Liga | 2017/2018 | 36 | 20 | 2017-08-20–2018-05-20 |
| La Liga | 2016/2017 | 34 | 20 | 2016-08-20–2017-05-21 |
| La Liga | 2015/2016 | 380 | 20 | 2015-08-21–2016-05-15 |
| La Liga | 2014/2015 | 38 | 20 | 2014-08-24–2015-05-23 |
| La Liga | 2013/2014 | 31 | 20 | 2013-08-18–2014-05-17 |
| La Liga | 2012/2013 | 32 | 20 | 2012-08-19–2013-05-12 |
| La Liga | 2011/2012 | 37 | 20 | 2011-08-29–2012-05-12 |
| La Liga | 2010/2011 | 33 | 20 | 2010-08-29–2011-05-11 |
| La Liga | 2009/2010 | 35 | 20 | 2009-09-12–2010-05-16 |
| La Liga | 2008/2009 | 31 | 19 | 2008-08-31–2009-05-10 |
| La Liga | 2007/2008 | 27 | 20 | 2007-08-26–2008-05-17 |
| La Liga | 2006/2007 | 26 | 20 | 2006-08-28–2007-06-17 |
| La Liga | 2005/2006 | 17 | 17 | 2005-10-01–2006-02-25 |
| La Liga | 2004/2005 | 7 | 7 | 2004-10-16–2005-05-01 |
| La Liga | 1973/1974 | 1 | 2 | 1974-02-17–1974-02-17 |
| Liga F | 2023/2024 | 240 | 16 | 2023-09-15–2024-06-16 |
| Liga Profesional | 1997/1998 | 1 | 2 | 1997-10-25–1997-10-25 |
| Liga Profesional | 1981 | 1 | 2 | 1981-04-10–1981-04-10 |
| Ligue 1 | 2022/2023 | 32 | 20 | 2022-08-06–2023-06-03 |
| Ligue 1 | 2021/2022 | 26 | 18 | 2021-08-29–2022-05-21 |
| Ligue 1 | 2015/2016 | 377 | 20 | 2015-08-07–2016-05-14 |
| Major League Soccer | 2023 | 6 | 7 | 2023-08-27–2023-10-22 |
| North American League | 1977 | 1 | 2 | 1977-08-28–1977-08-28 |
| NWSL | 2023 | 137 | 12 | 2023-03-25–2023-11-12 |
| NWSL | 2018 | 36 | 9 | 2018-04-15–2018-08-12 |
| Premier League | 2015/2016 | 380 | 20 | 2015-08-08–2016-05-17 |
| Premier League | 2003/2004 | 38 | 20 | 2003-08-16–2004-05-15 |
| Serie A | 2015/2016 | 380 | 20 | 2015-08-22–2016-05-15 |
| Serie A | 1986/1987 | 1 | 2 | 1986-11-09–1986-11-09 |
| Serie A Women | 2023/2024 | 130 | 10 | 2023-09-16–2024-05-19 |
| UEFA Euro | 2024 | 51 | 24 | 2024-06-14–2024-07-14 |
| UEFA Euro | 2020 | 51 | 24 | 2021-06-11–2021-07-11 |
| UEFA Europa League | 1988/1989 | 3 | 4 | 1989-03-15–1989-05-03 |
| UEFA Women's Euro | 2025 | 31 | 16 | 2025-07-02–2025-07-27 |
| UEFA Women's Euro | 2022 | 31 | 16 | 2022-07-06–2022-07-31 |
| Women's World Cup | 2023 | 64 | 32 | 2023-07-20–2023-08-20 |
| Women's World Cup | 2019 | 52 | 24 | 2019-06-07–2019-07-07 |

## Identity audit

11,794 provider IDs; 9,651 occur in multiple rosters; 4,025 across seasons, 2,897 across teams and 2,376 across competitions. 75 IDs have metadata inconsistencies and are quarantined, rather than automatically joined by names. Legitimate name/nationality changes can cause conservative exclusions; an anomaly does not prove a different person. Birth-date coverage is not established for StatsBomb, so age is not used.

Local `catalogue_identities.json` retains names, metadata comparisons and reasons. `catalogue_environments.json` retains provider ID, competition, season, team, observation dates and appearances. Catalogue reliable minutes are explicitly null until event reconciliation. Source IDs are isolated by provider; normalized names only check metadata attached to an identical provider ID.

## Cross-league screen

The following are ordered, provider-ID-consistent **roster-context candidates**, not reconciled-minute eligible transfers. A one-player entry records an audit count only; no effect is estimated. Returning to a team creates a separate stint. Adjacent observed environments only; overlap, identity conflicts, gaps over 450 days and missing intervening seasons reject training candidates. Observation boundaries are not contract dates.

| Gender | Source | Destination | Candidates | Unique players | ≥5 appearances on both sides |
|---|---|---|---:|---:|---:|
| female | Frauen Bundesliga | Liga F | 1 | 1 | 1 |
| female | Frauen Bundesliga | Serie A Women | 1 | 1 | 1 |
| female | Liga F | FA Women's Super League | 1 | 1 | 1 |
| female | Liga F | Serie A Women | 1 | 1 | 1 |
| female | NWSL | FA Women's Super League | 10 | 9 | 5 |
| female | NWSL | Frauen Bundesliga | 2 | 2 | 2 |
| female | NWSL | Liga F | 2 | 2 | 0 |
| female | NWSL | Serie A Women | 2 | 2 | 1 |
| female | Serie A Women | FA Women's Super League | 1 | 1 | 1 |
| female | Serie A Women | Frauen Bundesliga | 1 | 1 | 0 |
| female | Serie A Women | Liga F | 1 | 1 | 1 |
| male | 1. Bundesliga | La Liga | 4 | 4 | 0 |
| male | 1. Bundesliga | Ligue 1 | 1 | 1 | 0 |
| male | 1. Bundesliga | Premier League | 2 | 2 | 0 |
| male | 1. Bundesliga | Serie A | 1 | 1 | 0 |
| male | La Liga | 1. Bundesliga | 4 | 4 | 0 |
| male | La Liga | Ligue 1 | 14 | 14 | 3 |
| male | La Liga | Premier League | 9 | 9 | 2 |
| male | La Liga | Serie A | 12 | 12 | 2 |
| male | Ligue 1 | 1. Bundesliga | 11 | 11 | 0 |
| male | Ligue 1 | La Liga | 12 | 12 | 3 |
| male | Ligue 1 | Major League Soccer | 3 | 3 | 1 |
| male | Ligue 1 | Premier League | 5 | 5 | 2 |
| male | Ligue 1 | Serie A | 4 | 4 | 2 |
| male | Premier League | 1. Bundesliga | 4 | 4 | 0 |
| male | Premier League | La Liga | 15 | 15 | 0 |
| male | Premier League | Ligue 1 | 4 | 4 | 2 |
| male | Premier League | Serie A | 4 | 4 | 1 |
| male | Serie A | 1. Bundesliga | 1 | 1 | 0 |
| male | Serie A | La Liga | 26 | 26 | 4 |
| male | Serie A | Ligue 1 | 2 | 2 | 1 |
| male | Serie A | Premier League | 4 | 4 | 2 |

The male screen has only two pairs with at least 15 candidates before any minute filtering; no pair reaches 50. The female maximum is ten candidates (nine players). Thus the registered broad/pair feasibility rules already fail before minute reconciliation. Five appearances is descriptive and is not a reliable-minute threshold. Further event ingestion cannot turn these screened sets into a sufficient independent evaluation panel.

## Wyscout/Figshare — separate audit

The [official Figshare collection](https://figshare.com/collections/Soccer_match_event_dataset/4415000) and [original data descriptor](https://doi.org/10.1038/s41597-019-0247-7) were rechecked. The current metadata has 3,603 player rows, 2,996 observed domestic roster identities, 1,826 domestic matches in five leagues in 2017/18, and separate Euro 2016 / World Cup 2018 metadata. Exact downloaded item/file versions are preserved locally and checksummed. The item licence is CC BY 4.0. Fifteen roster IDs lack matching player metadata and are rejected.

There are 61 ordered cross-league candidates across 19 directional pairs, with no pair above eight. There is no later domestic season for an untouched temporal test. Minutes were not event-reconciled and event features were not ingested: different pressure/carry/xG semantics cannot be assumed equivalent to StatsBomb. Wyscout remains a separate potential replication source, not a way to inflate the StatsBomb sample.

Other open sources were not ingested: the existing SkillCorner sample and seven-match IDSSE release cannot supply a substantial repeated-season event panel; results-only and anonymized samples do not resolve the missing transfer evidence. No Transfermarkt, market values or name-based cross-provider linking is used.

## Reconciled WSL environment dataset

Four available WSL seasons (2018/19, 2019/20, 2020/21, 2023/24): 457 matches, 15 distinct teams, 660 players and 1225 player/team/season stints. Observations span 2018-09-09 to 2024-05-18. The first two historical full-calendar candidates are not assumed complete: published match counts are 107, 87, 131 and 132 respectively. No records exist here for 2021/22 or 2022/23.

311 players have candidate repeated environments. 565 adjacent candidates become 385 structurally eligible observations; 87 of these change recorded team. There are zero cross-league episodes in this selected dataset. Names/nationalities conflict for 13 of the 660 selected identities, which remain quarantined. Event participation reconciliation yields 16,527 agreeing, 40 reconciled and 26 conflicting player-match records (including unused roster members). Conflicting counts and minutes are excluded together.

| Minutes on both sides | Eligible episodes | Players | Destination seasons | Role coverage |
|---:|---:|---:|---|---|
| 450 | 191 | 130 | {'2019/2020': 92, '2020/2021': 97, '2023/2024': 2} | {'AM': 5, 'CB': 38, 'CM': 20, 'DM': 28, 'FB/WB': 40, 'ST': 20, 'W': 40} |
| 600 | 162 | 112 | {'2019/2020': 80, '2020/2021': 81, '2023/2024': 1} | {'AM': 5, 'CB': 34, 'CM': 18, 'DM': 22, 'FB/WB': 31, 'ST': 16, 'W': 36} |
| 900 | 117 | 83 | {'2019/2020': 55, '2020/2021': 62} | {'AM': 4, 'CB': 28, 'CM': 14, 'DM': 18, 'FB/WB': 18, 'ST': 10, 'W': 25} |
| 1200 | 51 | 35 | {'2019/2020': 27, '2020/2021': 24} | {'AM': 3, 'CB': 17, 'CM': 7, 'DM': 7, 'FB/WB': 7, 'ST': 2, 'W': 8} |

| Source season | Destination season | Candidates | ≥600/600 | ≥900/900 |
|---|---|---:|---:|---:|
| 2018/2019 | 2018/2019 | 3 | 0 | 0 |
| 2018/2019 | 2019/2020 | 173 | 80 | 55 |
| 2018/2019 | 2020/2021 | 13 | 0 | 0 |
| 2018/2019 | 2023/2024 | 3 | 0 | 0 |
| 2019/2020 | 2019/2020 | 7 | 0 | 0 |
| 2019/2020 | 2020/2021 | 191 | 81 | 62 |
| 2019/2020 | 2023/2024 | 19 | 0 | 0 |
| 2020/2021 | 2020/2021 | 13 | 0 | 0 |
| 2020/2021 | 2023/2024 | 133 | 0 | 0 |
| 2023/2024 | 2023/2024 | 10 | 1 | 0 |

## Missingness, selection and scope

Among structurally accepted candidates, 33 destinations have zero reliable minutes and 116 have fewer than 450. Across all candidates, including gap rejections, these counts are 44 and 160. This is a roster-observed outcome cohort: players never appearing in destination rosters are unobserved, not successful or failed transfers.

All 18 core features are available in 1063 environments. The 162 others have no positive reliable exposure and keep null rates. No core performance values are imputed. Rejection reasons can overlap: at 600 minutes, `{'below_minutes': 298, 'goalkeeper_excluded': 50, 'missing_core_features': 70, 'missing_role': 95, 'observation_gap_over_450_days': 170, 'rejected_identity': 17, 'unobserved_intervening_season': 168}`. Unknown/intervening seasons cannot be bridged to manufacture direct transfers.

**NO-GO for broad cross-league or single-pair translation.** The evidence supports assessing a narrower WSL season/team-context model, with later destination-season holdout and explicit separation of team changes from same-team season changes. Most eligible observations are same-team season transitions; the model must not be marketed as a validated transfer-success or league-strength model. The final scope and model plan are separate committed decisions.

Machine-readable evidence: `artifacts/phase3/transfer_evidence.json`, `identity_audit.json`, `wyscout_audit.json`, `source_catalogue.json`. Local marts: `player_environment.json`, `transition_episode.json`, `player_feature_observation.parquet` and `team_match_context.parquet`. Counts/opportunities, role shares, dates, provider revision and feature version remain available for modelling.
