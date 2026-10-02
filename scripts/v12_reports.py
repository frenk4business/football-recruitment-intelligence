"""Generate exact coverage/evaluation/source registries from audited artifacts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def write(path, text):
    (ROOT / path).write_text(text + "\n")


def main():
    index = read("artifacts/v12/public/index.json")
    manifest = read("artifacts/v12/public/build-manifest.json")
    capabilities = read("artifacts/v12/recruitment_capability.json")["competitions"]
    evaluation = read("artifacts/v12/wyscout-evaluation.json")
    audit = read("artifacts/v12/source-audit.json")
    metadata = read("artifacts/v12/metadata-quality.json")
    lines = [
        "# v1.2 recruitment expansion evaluation",
        "",
        "The evaluation plan and source audit were committed before extraction/evaluation in `ae3badb`. The fixed plan hash is `"
        + evaluation["plan_sha256"]
        + "`. No features, thresholds or gate floors were tuned after results. All five leagues passed at the preregistered lowest threshold of 450 minutes; DEF/MID/FWD passed independently. Goalkeepers remain searchable only. These tests measure repeated profile retrieval, not target-club fit or transfer success.",
        "",
        "Each player’s chronological appearances are assigned alternately to A/B, both with at least half the threshold. A-only scales and equal family/within-family weights determine Euclidean retrieval. Exact random baselines are min(k,n)/n and H_n/n. Ties average all admissible rank positions. MRR intervals bootstrap players 1,000 times. A/B are interleaved observations, not a forward temporal test. A-only evaluation scaling differs intentionally from production full-season league-role scaling. The latter is descriptive, not a held-out evaluation.",
        "",
        "## Selected league/role evidence",
        "",
        "| League | Role | Eligible | Paired | Recall@5 | Random R5 | Recall@10 | Random R10 | MRR | Random MRR | MRR 95% | Median feature Spearman |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    aggregate = []
    for cap in capabilities:
        if cap["provider"] != "wyscout":
            continue
        grid = cap["evaluation"]["threshold_grid"]
        selected = next(r for r in grid if r["minutes_threshold"] == cap["minutes_threshold"])
        totals = {key: 0.0 for key in ["recall_at_5", "recall_at_10", "mrr"]}
        n = 0
        random = {key: 0.0 for key in totals}
        for role, r in selected["roles"].items():
            m, b = r["metrics"], r["random"]
            count = r["paired_players"]
            n += count
            for key in totals:
                totals[key] += m[key] * count
                random[key] += b[key] * count
            lines.append(
                f"| {cap['league']} | {role} | {r['eligible_profiles']} | {count} | {m['recall_at_5']:.3f} | {b['recall_at_5']:.3f} | {m['recall_at_10']:.3f} | {b['recall_at_10']:.3f} | {m['mrr']:.3f} | {b['mrr']:.3f} | {m['mrr_95_interval'][0]:.3f}–{m['mrr_95_interval'][1]:.3f} | {m['median_feature_spearman']:.3f} |"
            )
        aggregate.append(
            {
                "scope": cap["scope"],
                "league": cap["league"],
                "eligible_profiles": cap["eligible_profiles"],
                "paired_profiles": n,
                "clubs": len(cap["enabled_clubs"]),
                "metrics": {k: v / n for k, v in totals.items()},
                "random": {k: v / n for k, v in random.items()},
            }
        )
    lines += [
        "",
        "## All preregistered thresholds and failed cohorts",
        "",
        "| Scope | Minutes | Role | Paired | Passed | Reasons | Minimum family-perturbation top-10 overlap |",
        "|---|---:|---|---:|---|---|---:|",
    ]
    for scope in evaluation["results"]:
        for row in scope["threshold_grid"]:
            for role, r in row["roles"].items():
                sensitivity = r.get("weight_sensitivity", [])
                lines.append(
                    f"| {scope['scope']} | {row['minutes_threshold']} | {role} | {r['paired_players']} | {r['passed']} | {', '.join(r['reasons']) or 'none'} | {min((x['top10_overlap'] for x in sensitivity), default=0):.3f} |"
                )
    lines += [
        "",
        "## Features and club context",
        "",
        "All 24 definitions, tags, null rules and role suitability are published in `artifacts/v12/wyscout-feature-registry.json`. They are provider-native. No headers, pressure, recoveries, inferred carries or dribble success are invented. Missing required geometry/outcomes yields unavailable features; valid observed absence yields zero. Pass accuracy is percent, all other values per nominal regulation 90 minutes. Any unreliable appearance withholds the entire season profile.",
        "",
        "Each of the 98 actual clubs has at least one role with two eligible roster members, each with ≥90 minutes at that club. Role medians, Q25/Q75, minutes and player IDs are exposed. These are full-season **roster-profile** summaries; transferred players can contribute profiles covering other teams. They are not team possession totals or isolated tactical effects. Broad DEF/MID/FWD positions are retained.",
        "",
        "Same-league comparison uses target league/season/role scales. Cross-league mode keeps raw observations, uses target-cohort scales and displays a warning; own-league percentiles are descriptive only. Equal percentiles in different leagues do not establish equal quality. No league strength, WSL translation, transfer availability or future fit is inferred. Custom criteria retain registered family/feature weights, multiplied by explicit user weights. A zero-weight constant feature cannot rank candidates.",
        "",
        "Additional StatsBomb scopes are searchable/common-descriptive where minutes and feature checks pass; none receives new native similarity or recruitment validation. Existing WSL recruitment and scientific artifacts remain untouched.",
    ]
    write("docs/v1.2-recruitment-expansion-evaluation.md", "\n".join(lines))
    write("artifacts/v12/league-summary.json", json.dumps(aggregate, indent=2))
    lines = [
        "# v1.2 platform coverage",
        "",
        json.dumps(index["counts"], indent=2),
        "",
        "Performance counts refer to provider-scoped player-season observations, never global unique people. Club-seasons include cup/international team scopes and are not all domestic seasons. Countries include scope areas such as International/Europe. `verified_persons` remains zero: metadata candidate verification does not merge scientific identities.",
        "",
        "| Provider | Competition | Season | Country | Clubs | Profiles | Matches | Coverage | Recruitment | Similarity profiles |",
        "|---|---|---|---|---:|---:|---:|---|---|---:|",
    ]
    for s in index["scopes"]:
        lines.append(
            f"| {s['provider']} | {s['competition']} | {s['season']} | {s['country']} | {len(s['clubs'])} | {s['profiles']} | {s['matches']} | {s['coverage']} | {s['recruitment']} | {s['similarity_profiles']} |"
        )
    lines += [
        "",
        "## Metadata and specialist sources",
        "",
        f"OpenFootball: {metadata['clubs']:,} source club entities, {index['counts']['metadata_clubs']:,} with no deterministic performance link; {metadata['player_metadata_records']:,} player metadata records; {metadata['competition_seasons']} source competition-season files; {metadata['fixture_observations']:,} fixture observations. Cross-repository fixtures and unresolved aliases remain separate, so these are not unique world clubs/matches/persons. {len(metadata['issues'])} exact duplicate fixture rows were withheld; all other source rows were parsed. Alias collisions remain separate and are audited. Identity candidate categories: `{metadata['identity_statuses']}`. Even verified name+DOB+country matches remain external candidates; no global person join or current-club substitution occurs.",
        "",
        "SkillCorner: 290 separate A-League 2024/25 specialist player-season records, 407 off-ball, 407 passing and 406 physical source rows. Team/position records are preserved, not silently averaged. Average physical match minutes are not season minutes; p30tip denominators differ from per90. No European recruitment breadth or extra main performance player count is claimed.",
        "",
        "The complete StatsBomb catalogue audit, including nonselected scopes, is `artifacts/v12/source-audit.json`. Domestic complete requires expected match count plus unique balanced home/away pairs; near_complete is ≥95% below complete, partial ≥25%, sample lower or unknown denominator. International/cup profiles retain scope labels; no domestic club context is generated from them.",
    ]
    write("docs/v1.2-platform-coverage.md", "\n".join(lines))
    # Explicit extensible discovery registry: unknown counts stay null; no automatic ingestion.
    specs = [
        (
            "statsbomb",
            "StatsBomb / Hudl",
            "https://github.com/hudl/open-data",
            "CORE",
            "event performance",
            "Custom non-commercial agreement",
            "non-commercial only",
            "derived analyses with attribution/logo; raw feeds withheld",
            True,
            False,
            True,
            False,
            True,
            True,
            True,
            "existing WSL only",
            False,
            "Historical named-player performance",
        ),
        (
            "wyscout",
            "Pappalardo / Wyscout",
            "https://figshare.com/collections/Soccer_match_event_dataset/4415000/5",
            "CORE",
            "event performance",
            "CC BY 4.0",
            "permitted with attribution",
            "permitted with attribution and change notice",
            True,
            False,
            True,
            True,
            True,
            True,
            True,
            "five evaluated leagues",
            False,
            "Historical Big Five native recruitment",
        ),
        *[
            (
                key,
                "OpenFootball",
                "https://github.com/openfootball/" + repo,
                "ENRICHMENT",
                kind,
                "CC0",
                "permitted",
                "permitted",
                False,
                False,
                False,
                key == "openfootball-players",
                key != "openfootball-players",
                key == "openfootball-players",
                False,
                "no",
                False,
                "Dated isolated metadata",
            )
            for key, repo, kind in [
                ("openfootball-europe", "europe", "match/club metadata"),
                ("openfootball-clubs", "clubs", "club metadata"),
                ("openfootball-players", "players", "player metadata"),
                ("openfootball-json", "football.json", "match/club metadata"),
            ]
        ],
        (
            "skillcorner",
            "SkillCorner",
            "https://github.com/SkillCorner/opendata",
            "ENRICHMENT",
            "tracking / physical",
            "MIT",
            "permitted under licence",
            "retain MIT notice",
            False,
            True,
            True,
            True,
            True,
            True,
            False,
            "no",
            False,
            "Australian physical/off-ball specialist research",
        ),
        (
            "idsse",
            "DFL / authors",
            "https://github.com/spoho-datascience/idsse-data",
            "RESEARCH",
            "event + tracking",
            "CC BY 4.0",
            "permitted with attribution",
            "DFL and paper attribution",
            True,
            True,
            True,
            None,
            True,
            True,
            False,
            "no: seven-match sample",
            False,
            "Spatial model/pipeline research",
        ),
        (
            "metrica",
            "Metrica Sports",
            "https://github.com/metrica-sports/sample-data",
            "RESEARCH",
            "event + tracking",
            "README acknowledgement; full grant not established",
            "not established",
            "not established",
            True,
            True,
            None,
            False,
            False,
            None,
            False,
            "no: anonymous sample",
            False,
            "Schema research only, no product republication",
        ),
        (
            "soccernet",
            "SoccerNet",
            "https://www.soccer-net.org/data",
            "RESEARCH",
            "video / sparse annotations",
            "Task-specific research terms; video NDA",
            "non-commercial",
            "videos prohibited; inspect annotation terms",
            False,
            None,
            None,
            False,
            True,
            None,
            False,
            "no",
            False,
            "Computer vision research, no season metrics",
        ),
        (
            "driblab",
            "Driblab",
            "https://github.com/driblab/open-data",
            "REJECT",
            "tracking",
            "No explicit reusable data grant established",
            "unknown",
            "unknown",
            None,
            True,
            None,
            None,
            True,
            None,
            False,
            "no",
            False,
            "Withhold pending licence/source audit",
        ),
        (
            "alfheim",
            "Simula",
            "https://datasets.simula.no/alfheim/",
            "RESEARCH",
            "tracking / video",
            "Non-commercial research; no performance profiles",
            "non-commercial",
            "restricted; no reidentification",
            False,
            True,
            None,
            False,
            False,
            None,
            False,
            "no: expressly unsuitable",
            False,
            "Anonymous spatial research only",
        ),
        (
            "soccertrack",
            "SoccerTrack authors",
            "https://huggingface.co/datasets/atomscott/soccertrack-v2",
            "RESEARCH",
            "video / tracking / events",
            "CC BY 4.0 stated; gated access",
            "subject to gated conditions",
            "subject to source conditions",
            True,
            True,
            None,
            False,
            False,
            None,
            False,
            "no: pseudonymous",
            False,
            "No gated acquisition for product",
        ),
        (
            "unverified-epl",
            "Third-party uploader",
            "https://huggingface.co/datasets/peggy44/PremierLeague25-26",
            "REJECT",
            "claimed SkillCorner tracking",
            "Uploader CC BY-NC not verified provider permission",
            "not established",
            "not established",
            None,
            True,
            None,
            None,
            None,
            None,
            False,
            "no",
            False,
            "Withhold pending provider authorization",
        ),
        (
            "eredivisie-mirror",
            "Third-party uploader",
            "https://github.com/TopMarx/eredivisie",
            "REJECT",
            "fantasy metadata",
            "MIT code; underlying data rights reserved",
            "not established",
            "not established",
            False,
            False,
            None,
            None,
            True,
            None,
            False,
            "no",
            False,
            "No ingestion of scraped proprietary data",
        ),
    ]
    records = []
    for (
        key,
        provider,
        url,
        classification,
        kind,
        license_,
        commercial,
        redistribution,
        event,
        tracking,
        lineups,
        dob,
        clubs,
        positions,
        performance,
        recruitment,
        translation,
        use,
    ) in specs:
        records.append(
            dict(
                id=key,
                provider=provider,
                official_url=url,
                classification=classification,
                dataset_type=kind,
                licence=license_,
                commercial_use=commercial,
                redistribution=redistribution,
                event_level=event,
                tracking=tracking,
                lineups=lineups,
                DOB=dob,
                club_metadata=clubs,
                positions=positions,
                performance_suitable=performance,
                recruitment_suitable=recruitment,
                translation_suitable=translation,
                recommended_use=use,
                source_stability="pinned Git revision"
                if key in audit["repositories"]
                else "versioned publication or restricted source; manual review",
                revision=audit["repositories"].get(key, {}).get("revision"),
                countries=[],
                competitions=[],
                seasons=[],
                matches=None,
                players=None,
                coverage="See cited source and source-audit catalogue; unknown counts are not zero",
            )
        )
    for r in records:
        if r["id"] == "statsbomb":
            r.update(
                countries=sorted({s["country_name"] for s in audit["statsbomb_catalogue"]}),
                competitions=sorted({s["competition_name"] for s in audit["statsbomb_catalogue"]}),
                seasons=sorted({s["season_name"] for s in audit["statsbomb_catalogue"]}),
                matches=sum(s["catalogue_matches"] for s in audit["statsbomb_catalogue"]),
                coverage="80 source catalogue scopes; actual player identities depend on minutes/profile gates",
            )
        elif r["id"] == "wyscout":
            r.update(
                countries=["England", "France", "Germany", "Italy", "Spain"],
                competitions=[x["league"] for x in aggregate],
                seasons=["2017/2018"],
                matches=1826,
                players=2571,
                coverage="Five complete domestic event seasons; player count is domestic source actors, not eligible profiles",
            )
        elif r["id"].startswith("openfootball"):
            r.update(
                countries=metadata["countries"],
                coverage="Metadata only; countries refer to combined selected European metadata snapshots; source-scoped counts in metadata-quality.json",
            )
            if r["id"] == "openfootball-players":
                r["players"] = metadata["player_metadata_records"]
        elif r["id"] == "skillcorner":
            r.update(
                countries=["Australia"],
                competitions=["A-League"],
                seasons=["2024/2025"],
                matches=10,
                players=290,
                coverage="290 aggregate identities; 10 tracking matches not ingested here",
            )
        elif r["id"] == "idsse":
            r.update(countries=["Germany"], seasons=["2022/2023"], matches=7)
        elif r["id"] == "metrica":
            r.update(matches=3)
    write(
        "config/v12-source-registry.json",
        json.dumps(
            {
                "version": "source-registry-v12",
                "audit_date": "2026-10-02",
                "new_source_policy": "Manual official URL, licence, schema, provenance and capability approval before adding to pinned ingestion config",
                "sources": records,
            },
            indent=2,
        ),
    )
    print(
        f"Reports: {len(index['scopes'])} performance scopes; {len(records)} source decisions; {manifest['public_bytes']:,} additive public bytes"
    )


if __name__ == "__main__":
    main()
