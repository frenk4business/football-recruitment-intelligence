"""Generate the evidence report from measured provider and environment audits."""

import json
from pathlib import Path

from football_intelligence.dna.cohort import write


def evidence_report(root: Path):
    public = root / "artifacts/phase3"
    catalogue = json.loads((public / "source_catalogue.json").read_text())
    identity = json.loads((public / "identity_audit.json").read_text())
    wyscout = json.loads((public / "wyscout_audit.json").read_text())
    evidence = json.loads((public / "transfer_evidence.json").read_text())
    local = root / "data/processed/phase3"
    environments = json.loads((local / "player_environment.json").read_text())
    transitions = json.loads((local / "transition_episode.json").read_text())
    valid = [t for t in transitions if t["structurally_eligible"]]
    evidence.update(
        scope_decision="NO-GO for broad cross-league translation; assess narrower WSL season/team context",
        selected_competitions=sorted({e["competition"] for e in environments}),
        selected_seasons=sorted({e["season"] for e in environments}),
        teams=len({e["team_id"] for e in environments}),
        structurally_eligible_candidates=len(valid),
        structural_destination_zero_minutes=sum(t["destination_minutes"] == 0 for t in valid),
        structural_destination_under_450=sum(t["destination_minutes"] < 450 for t in valid),
        selected_matrix=[
            dict(
                source_season=a,
                destination_season=b,
                candidates=sum(
                    t["source_season"] == a and t["destination_season"] == b for t in transitions
                ),
                eligible={
                    str(th): sum(
                        t["source_season"] == a
                        and t["destination_season"] == b
                        and not t["eligibility"][str(th)]
                        for t in transitions
                    )
                    for th in [450, 600, 900, 1200]
                },
            )
            for a, b in sorted({(t["source_season"], t["destination_season"]) for t in transitions})
        ],
        catalogue_cross_league_candidates={
            g: sum(p["episodes"] for p in identity["cross_league_matrix"] if p["gender"] == g)
            for g in ["male", "female"]
        },
        catalogue_matrix=identity["cross_league_matrix"],
    )
    write(public / "transfer_evidence.json", evidence)
    lines = [
        "# Phase 3 transfer evidence feasibility audit",
        "",
        "Measured before model fitting. Protocol: [registered audit rules](phase-3-audit-protocol.md). Raw sources and per-match/identity records remain local; committed files are derived audit aggregates.",
        "",
        "## Official-source discovery",
        "",
        f"[StatsBomb official repository](https://github.com/statsbomb/open-data) was freshly verified at `{catalogue['revision']}`: {len(catalogue['competition_seasons'])} competition-seasons and {catalogue['matches']:,} distinct match lineups audited. The licence PDF was retrieved again at this revision; source attribution/logo and non-commercial aggregate-publication restrictions remain applicable. See `config/phase3.sources.json` for URLs, byte counts and checksums.",
        "",
        "Coverage is observed catalogue coverage, not an assumption of full seasons. Bundesliga 2015/16 and 2023/24 each have 34 matches, while most La Liga seasons contain a selected-club sample. Broad women’s 2023/24 coverage does not by itself create longitudinal transfer evidence. International tournaments and club cups are classified separately and excluded from the domestic-transition screen.",
        "",
        "| Competition | Season | Matches | Teams | Observed dates |",
        "|---|---|---:|---:|---|",
    ]
    for c in catalogue["competition_seasons"]:
        lines.append(
            f"| {c['competition_name']} | {c['season_name']} | {c['matches']} | {c['teams']} | {c['first_date']}–{c['last_date']} |"
        )
    lines += [
        "",
        "## Identity audit",
        "",
        f"{identity['unique_players']:,} provider IDs; {identity['repeated_ids']:,} occur in multiple rosters; {identity['cross_season_ids']:,} across seasons, {identity['cross_team_ids']:,} across teams and {identity['cross_competition_ids']:,} across competitions. {identity['identity_status']['quarantined']} IDs have metadata inconsistencies and are quarantined, rather than automatically joined by names. Legitimate name/nationality changes can cause conservative exclusions; an anomaly does not prove a different person. Birth-date coverage is not established for StatsBomb, so age is not used.",
        "",
        "Local `catalogue_identities.json` retains names, metadata comparisons and reasons. `catalogue_environments.json` retains provider ID, competition, season, team, observation dates and appearances. Catalogue reliable minutes are explicitly null until event reconciliation. Source IDs are isolated by provider; normalized names only check metadata attached to an identical provider ID.",
        "",
        "## Cross-league screen",
        "",
        "The following are ordered, provider-ID-consistent **roster-context candidates**, not reconciled-minute eligible transfers. A one-player entry records an audit count only; no effect is estimated. Returning to a team creates a separate stint. Adjacent observed environments only; overlap, identity conflicts, gaps over 450 days and missing intervening seasons reject training candidates. Observation boundaries are not contract dates.",
        "",
        "| Gender | Source | Destination | Candidates | Unique players | ≥5 appearances on both sides |",
        "|---|---|---|---:|---:|---:|",
    ]
    for p in identity["cross_league_matrix"]:
        lines.append(
            f"| {p['gender']} | {p['source']} | {p['destination']} | {p['episodes']} | {p['players']} | {p['at_least_five_appearances_both']} |"
        )
    lines += [
        "",
        "The male screen has only two pairs with at least 15 candidates before any minute filtering; no pair reaches 50. The female maximum is ten candidates (nine players). Thus the registered broad/pair feasibility rules already fail before minute reconciliation. Five appearances is descriptive and is not a reliable-minute threshold. Further event ingestion cannot turn these screened sets into a sufficient independent evaluation panel.",
        "",
        "## Wyscout/Figshare — separate audit",
        "",
        f"The [official Figshare collection](https://figshare.com/collections/Soccer_match_event_dataset/4415000) and [original data descriptor](https://doi.org/10.1038/s41597-019-0247-7) were rechecked. The current metadata has {wyscout['players_metadata']:,} player rows, {wyscout['domestic_roster_players']:,} observed domestic roster identities, 1,826 domestic matches in five leagues in 2017/18, and separate Euro 2016 / World Cup 2018 metadata. Exact downloaded item/file versions are preserved locally and checksummed. The item licence is CC BY 4.0. Fifteen roster IDs lack matching player metadata and are rejected.",
        "",
        f"There are {wyscout['cross_league_candidates']} ordered cross-league candidates across {len(wyscout['matrix'])} directional pairs, with no pair above eight. There is no later domestic season for an untouched temporal test. Minutes were not event-reconciled and event features were not ingested: different pressure/carry/xG semantics cannot be assumed equivalent to StatsBomb. Wyscout remains a separate potential replication source, not a way to inflate the StatsBomb sample.",
        "",
        "Other open sources were not ingested: the existing SkillCorner sample and seven-match IDSSE release cannot supply a substantial repeated-season event panel; results-only and anonymized samples do not resolve the missing transfer evidence. No Transfermarkt, market values or name-based cross-provider linking is used.",
        "",
        "## Reconciled WSL environment dataset",
        "",
        f"Four available WSL seasons (2018/19, 2019/20, 2020/21, 2023/24): {evidence['matches']} matches, {evidence['teams']} distinct teams, {evidence['players']} players and {evidence['environments']} player/team/season stints. Observations span {evidence['dates'][0]} to {evidence['dates'][1]}. The first two historical full-calendar candidates are not assumed complete: published match counts are 107, 87, 131 and 132 respectively. No records exist here for 2021/22 or 2022/23.",
        "",
        f"{evidence['repeated_players']} players have candidate repeated environments. {evidence['candidates']} adjacent candidates become {len(valid)} structurally eligible observations; {evidence['actual_team_changes']} of these change recorded team. There are zero cross-league episodes in this selected dataset. Names/nationalities conflict for {evidence['identity_status']['quarantined']} of the 660 selected identities, which remain quarantined. Event participation reconciliation yields {evidence['minutes_quality']['reliable']:,} agreeing, {evidence['minutes_quality']['reconciled']} reconciled and {evidence['minutes_quality']['conflicting']} conflicting player-match records (including unused roster members). Conflicting counts and minutes are excluded together.",
        "",
        "| Minutes on both sides | Eligible episodes | Players | Destination seasons | Role coverage |",
        "|---:|---:|---:|---|---|",
    ]
    for th in ["450", "600", "900", "1200"]:
        r = evidence["thresholds"][th]
        lines.append(
            f"| {th} | {r['eligible']} | {r['players']} | {r['destination_seasons']} | {r['roles']} |"
        )
    lines += [
        "",
        "| Source season | Destination season | Candidates | ≥600/600 | ≥900/900 |",
        "|---|---|---:|---:|---:|",
    ]
    for p in evidence["selected_matrix"]:
        lines.append(
            f"| {p['source_season']} | {p['destination_season']} | {p['candidates']} | {p['eligible']['600']} | {p['eligible']['900']} |"
        )
    lines += [
        "",
        "## Missingness, selection and scope",
        "",
        f"Among structurally accepted candidates, {evidence['structural_destination_zero_minutes']} destinations have zero reliable minutes and {evidence['structural_destination_under_450']} have fewer than 450. Across all candidates, including gap rejections, these counts are {evidence['destination_zero_minutes']} and {evidence['destination_under_450']}. This is a roster-observed outcome cohort: players never appearing in destination rosters are unobserved, not successful or failed transfers.",
        "",
        f"All 18 core features are available in {evidence['feature_coverage']['shots_per90']} environments. The 162 others have no positive reliable exposure and keep null rates. No core performance values are imputed. Rejection reasons can overlap: at 600 minutes, `{evidence['thresholds']['600']['rejected_reasons']}`. Unknown/intervening seasons cannot be bridged to manufacture direct transfers.",
        "",
        "**NO-GO for broad cross-league or single-pair translation.** The evidence supports assessing a narrower WSL season/team-context model, with later destination-season holdout and explicit separation of team changes from same-team season changes. Most eligible observations are same-team season transitions; the model must not be marketed as a validated transfer-success or league-strength model. The final scope and model plan are separate committed decisions.",
        "",
        "Machine-readable evidence: `artifacts/phase3/transfer_evidence.json`, `identity_audit.json`, `wyscout_audit.json`, `source_catalogue.json`. Local marts: `player_environment.json`, `transition_episode.json`, `player_feature_observation.parquet` and `team_match_context.parquet`. Counts/opportunities, role shares, dates, provider revision and feature version remain available for modelling.",
        "",
    ]
    (root / "docs/phase-3-transfer-evidence.md").write_text("\n".join(lines))
    lock = []
    for provider in ["statsbomb", "wyscout"]:
        base = root / "data/raw/phase3" / provider
        for p in sorted(base.rglob("*.sha.json")):
            r = json.loads(p.read_text())
            lock.append(
                dict(
                    provider=provider, path=str(p.relative_to(base)).removesuffix(".sha.json"), **r
                )
            )
    write(root / "config/phase3.sources.json", dict(revision=catalogue["revision"], files=lock))
    return dict(files=len(lock), scope=evidence["scope_decision"])


if __name__ == "__main__":
    print(evidence_report(Path.cwd()))
