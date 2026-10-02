"""Validated, partitioned derived publication; no raw events or identity merging."""

import gzip
import hashlib
import json
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np

from football_intelligence.expansion import contracts as c
from football_intelligence.expansion.evaluate import eligible, scales
from football_intelligence.expansion.features import KEYS
from football_intelligence.expansion.metadata import normalize
from football_intelligence.profiles.cache import checksum, write_json
from football_intelligence.profiles.ingest import decode_name
from football_intelligence.profiles.publish import COMPETITIONS, profile_path

WS_COUNTRY = {"364": "England", "412": "France", "426": "Germany", "524": "Italy", "795": "Spain"}
LEAGUES = {
    "364": "Premier League",
    "412": "Ligue 1",
    "426": "Bundesliga",
    "524": "Serie A",
    "795": "La Liga",
}


def percentiles(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Midrank empirical standing; descriptive within this exact league-role only."""
    return np.array(
        [
            100
            * ((reference < v).sum(axis=0) + 0.5 * (reference == v).sum(axis=0))
            / len(reference)
            for v in values
        ]
    )


def pipeline_hash(root: Path) -> str:
    paths = sorted((root / "src/football_intelligence/expansion").glob("*.py"))
    return hashlib.sha256(b"".join(p.name.encode() + p.read_bytes() for p in paths)).hexdigest()


def build(root: Path):
    def read(path):
        return json.loads((root / path).read_text())

    output = root / "artifacts/v12/public"
    stage = root / "data/processed/v12/public-stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    inventory = []

    def emit(path, value, model):
        validated = model.model_validate(value).model_dump(mode="json")
        target = stage / path
        write_json(target, validated, compact=True)
        if target.stat().st_size > 3_000_000:
            raise ValueError(f"Artifact too large: {path}")
        inventory.append(
            {
                "source": f"artifacts/v12/public/{path}",
                "path": f"data/v12/{path}",
                "sha256": checksum(target),
                "bytes": target.stat().st_size,
                "schema": model.__name__,
                "array": False,
            }
        )
        return checksum(target)

    old = read("artifacts/v11/public/index.json")
    old_scopes = {s["scope"]: s for s in read("data/processed/v11/full/coverage.json")}
    audit = read("artifacts/v12/source-audit.json")
    catalog = {
        f"statsbomb-{s['competition_id']}-{s['season_id']}": s for s in audit["statsbomb_catalogue"]
    }
    sb_report = read("artifacts/v12/statsbomb-ingestion.json")
    new_profiles = [
        p
        for p in read("data/processed/v12/statsbomb/profiles.json")
        if p["reliable"] and p["minutes"] >= 450
    ]
    native_profiles = read("data/processed/v12/wyscout/profiles.json")
    caps = read("artifacts/v12/recruitment_capability.json")["competitions"]
    caps = [s for s in caps if s["provider"] == "wyscout"]
    capmap = {s["scope"]: s for s in caps}
    native_by_id = {p["id"]: p for p in native_profiles}
    # Legacy WSL eligibility comes only from the existing published recruitment population.
    wsl = read("artifacts/phase4/public/index.json")
    from football_intelligence.data.schema import canonical_id

    wsl_ids = {p["player_id"] for p in wsl["players"] if p["eligible"]}
    entries = []
    for p in old["profiles"]:
        cap = capmap.get(p["scope"])
        native = native_by_id.get(p["id"])
        recruitment = bool(
            cap
            and native
            and native["role"] in cap["roles"]
            and eligible(native, cap["minutes_threshold"])
        )
        if p["scope"] == "statsbomb-37-281":
            recruitment = (
                str(canonical_id("statsbomb", "players", int(p["id"].split("-")[-1]))) in wsl_ids
            )
        entries.append(
            {
                **p,
                "name": decode_name(p["name"]),
                "detail_path": "/data/v11/" + profile_path(p["id"]),
                "capabilities_v12": c.CapabilitySet(
                    recruitment=recruitment,
                    similarity=p["capabilities"]["similarity"],
                    common_profile=p["capabilities"]["common"],
                    translation=p["capabilities"]["translation"],
                ).model_dump(),
            }
        )
    new_entries = {}
    for p in new_profiles:
        common = p["common_ready"] and p["minutes"] >= old["common_threshold"]
        entry = {
            "id": p["id"],
            "name": p["name"],
            "provider": "statsbomb",
            "scope": p["scope"],
            "teams": [f"statsbomb:{tid}" for tid in p["teams"]],
            "role": p["role"],
            "role_family": p["role_family"],
            "minutes": p["minutes"],
            "capabilities": {
                "common": common,
                "similarity": False,
                "translation": False,
                "validated_dna": False,
            },
            "capabilities_v12": c.CapabilitySet(common_profile=common).model_dump(),
            "detail_path": "/data/v12/" + profile_path(p["id"]),
        }
        entries.append(entry)
        new_entries[p["id"]] = entry
    if len({p["id"] for p in entries}) != len(entries):
        raise ValueError("Duplicate performance profile scope")
    teams = {k: decode_name(v) for k, v in old["teams"].items()}
    scopes = []
    for s in old["scopes"]:
        original = old_scopes[s["id"]]
        sb = catalog.get(s["id"])
        country = sb["country_name"] if sb else WS_COUNTRY[str(original["competition_id"])]
        scopes.append(
            {
                **s,
                "competition": LEAGUES.get(str(original["competition_id"]), s["competition"])
                if s["provider"] == "wyscout"
                else s["competition"],
                "coverage": sb["coverage_status"] if sb else "complete",
                "country": country,
                "scope_label": "Domestic league observations",
                "recruitment": s["id"] in capmap or s["id"] == "statsbomb-37-281",
                "clubs": [f"{s['provider']}:{tid}" for tid in original["teams"]],
            }
        )
    for s in sb_report["scopes"]:
        rows = [p for p in entries if p["scope"] == s["scope"]]
        scopes.append(
            {
                "id": s["scope"],
                "provider": "statsbomb",
                "competition": s["competition_name"],
                "competition_key": next(
                    (
                        key
                        for sid, key in COMPETITIONS.items()
                        if sid.startswith(f"statsbomb-{s['competition_id']}-")
                    ),
                    f"statsbomb-{s['competition_id']}",
                ),
                "season": s["season_name"],
                "gender": "male",
                "matches": s["catalogue_matches"],
                "profiles": len(rows),
                "common_profiles": sum(p["capabilities"]["common"] for p in rows),
                "similarity_profiles": 0,
                "coverage": s["coverage_status"],
                "first_date": s["first_date"],
                "last_date": s["last_date"],
                "country": s["country_name"],
                "scope_label": s["scope_label"],
                "recruitment": False,
                "clubs": [f"statsbomb:{tid}" for tid in s["teams_by_id"]],
            }
        )
        teams.update({f"statsbomb:{tid}": name for tid, name in s["teams_by_id"].items()})
    summaries = []
    for cap in caps:
        scope = cap["scope"]
        rows = [
            p
            for p in native_profiles
            if p["scope"] == scope
            and p["role"] in cap["roles"]
            and eligible(p, cap["minutes_threshold"])
        ]
        players, role_scales, role_weights, populations = [], {}, {}, {}
        for role in cap["roles"]:
            population = [p for p in rows if p["role"] == role]
            matrix = np.array([[p["features"][k] for k in KEYS] for p in population])
            populations[role] = matrix
            sd, weights = scales(matrix)
            role_scales[role] = dict(zip(KEYS, sd.tolist(), strict=True))
            role_weights[role] = dict(zip(KEYS, weights.tolist(), strict=True))
            for p, pct in zip(population, percentiles(matrix, matrix), strict=True):
                players.append(
                    {
                        "id": p["id"],
                        "name": decode_name(p["name"]),
                        "scope": scope,
                        "role": role,
                        "minutes": p["minutes"],
                        "teams": [f"wyscout:{tid}" for tid in p["team_minutes"]],
                        "features": p["features"],
                        "percentiles": dict(zip(KEYS, np.round(pct, 2).tolist(), strict=True)),
                    }
                )
        clubs = []
        for tid in cap["enabled_clubs"]:
            roles = []
            for role in cap["roles"]:
                roster = [
                    p for p in rows if p["role"] == role and p["team_minutes"].get(tid, 0) >= 90
                ]
                if len(roster) < 2:
                    continue
                matrix = np.array([[p["features"][k] for k in KEYS] for p in roster])
                median = np.median(matrix, axis=0)
                roles.append(
                    {
                        "role": role,
                        "players": [p["id"] for p in roster],
                        "minutes": sum(p["team_minutes"][tid] for p in roster),
                        "median": dict(zip(KEYS, median.tolist(), strict=True)),
                        "q25": dict(
                            zip(KEYS, np.quantile(matrix, 0.25, axis=0).tolist(), strict=True)
                        ),
                        "q75": dict(
                            zip(KEYS, np.quantile(matrix, 0.75, axis=0).tolist(), strict=True)
                        ),
                        "percentiles": dict(
                            zip(
                                KEYS,
                                percentiles(median[None, :], populations[role])[0].tolist(),
                                strict=True,
                            )
                        ),
                    }
                )
            roster = [p for p in rows if p["team_minutes"].get(tid, 0) >= 90]
            clubs.append(
                {
                    "id": f"wyscout:{tid}",
                    "name": teams[f"wyscout:{tid}"],
                    "roles": roles,
                    "roster_median": {
                        k: float(np.median([p["features"][k] for p in roster])) for k in KEYS
                    },
                    "capabilities": {
                        "metadata": True,
                        "team_context": True,
                        "recruitment": True,
                        "candidate_cohort": True,
                        "translation": False,
                        "tracking": False,
                    },
                }
            )
        league = {
            "version": "recruitment-fit-wyscout-v1",
            "context_version": "wyscout-club-context-v1",
            "feature_registry_version": "wyscout-recruitment-features-v1",
            "scope": scope,
            "competition": LEAGUES[cap["competition_id"]],
            "country": WS_COUNTRY[cap["competition_id"]],
            "competition_id": cap["competition_id"],
            "season_id": cap["season_id"],
            "season": cap["season"],
            "minutes_threshold": cap["minutes_threshold"],
            "roles": cap["roles"],
            "clubs": clubs,
            "players": players,
            "scales": role_scales,
            "weights": role_weights,
        }
        emit(f"recruitment/{scope}.json", league, c.NativeLeague)
        summaries.append(
            {
                k: league[k]
                for k in ["scope", "competition", "country", "season", "minutes_threshold"]
            }
            | {
                "clubs": len(clubs),
                "profiles": len(players),
                "path": f"/data/v12/recruitment/{scope}.json",
            }
        )
    registry = read("artifacts/v12/wyscout-feature-registry.json")
    features = [
        {
            **{k: v for k, v in f.items() if k not in ["label_en", "label_nl"]},
            "en": f["label_en"],
            "nl": f["label_nl"],
        }
        for f in registry["features"]
    ]
    emit(
        "recruitment/index.json",
        {
            "version": "recruitment-fit-wyscout-v1",
            "features": features,
            "leagues": summaries,
            "source": "https://figshare.com/collections/Soccer_match_event_dataset/4415000/5",
            "license": "CC BY 4.0 — Pappalardo et al. (2019), Wyscout",
            "evaluation_path": "https://github.com/frenk4business/football-recruitment-intelligence/blob/main/docs/v1.2-recruitment-expansion-evaluation.md",
        },
        c.NativeRegistry,
    )
    metadata = read("data/processed/v12/metadata/clubs.json")
    metadata_scopes = read("data/processed/v12/metadata/competitions.json")
    people = read("data/processed/v12/metadata/players.json")
    aliases = defaultdict(set)
    for club in metadata:
        for name in [club["name"], *club["aliases"]]:
            aliases[(club["country"], normalize(name))].add(club["id"])
    matches = defaultdict(set)
    mapping_report = []
    for scope in scopes:
        if scope["gender"] != "male" or scope["scope_label"] != "Domestic league observations":
            continue
        for tid in scope["clubs"]:
            options = aliases[(scope["country"], normalize(teams[tid]))]
            status = (
                "verified_exact_country_alias"
                if len(options) == 1
                else "ambiguous"
                if options
                else "unmatched"
            )
            mapping_report.append(
                {
                    "scope": scope["id"],
                    "provider_club": tid,
                    "candidates": sorted(options),
                    "status": status,
                }
            )
            if len(options) == 1:
                matches[next(iter(options))].add(scope["id"])
    for club in metadata:
        club["performance_scopes"] = sorted(matches[club["id"]])
        # Metadata entities do not themselves become recruitment scenarios; explicit scoped links do.
    write_json(root / "artifacts/v12/club-identity-audit.json", mapping_report)
    grouped = defaultdict(list)
    for person in people:
        grouped[person["country"]].append(person)
    player_paths = {}
    for country, population in sorted(grouped.items()):
        key = normalize(country).replace(" ", "-")
        path = f"metadata/players/{key}.json"
        emit(
            path,
            {
                "version": "player-metadata-v1",
                "country": country,
                "metadata_updated": audit["repositories"]["openfootball-players"]["committed_at"],
                "players": population,
            },
            c.MetadataPeople,
        )
        player_paths[country] = "/data/v12/" + path
    emit(
        "metadata/index.json",
        {
            "version": "club-metadata-v1",
            "clubs": [
                {
                    k: club[k]
                    for k in ["id", "name", "country", "aliases", "seasons", "performance_scopes"]
                }
                for club in metadata
            ],
            "competitions": metadata_scopes,
            "player_countries": {k: len(v) for k, v in grouped.items()},
            "player_paths": player_paths,
            "specialist_path": "/data/v12/physical/index.json",
            "license": "OpenFootball — CC0 / public domain",
        },
        c.MetadataDirectory,
    )
    for club in metadata:
        emit(f"metadata/clubs/{club['id'][-2:]}/{club['id']}.json", club, c.MetadataClub)
    for scope in metadata_scopes:
        data = read(f"data/processed/v12/metadata/fixtures/{scope['id']}.json")
        emit(
            f"metadata/fixtures/{scope['id']}.json",
            {
                "version": "fixture-metadata-v1",
                "scope": scope["id"],
                "source": data["source"],
                "columns": ["home", "away", "source_date", "round", "score", "status"],
                "rows": [
                    [
                        r["home"],
                        r["away"],
                        r["date_text"],
                        r["round"],
                        r["score"],
                        r.get("score_note"),
                    ]
                    for r in data["fixtures"]
                ],
            },
            c.MetadataFixtures,
        )
    physical = read("data/processed/v12/metadata/physical.json")
    for person in physical:
        emit(f"physical/{person['id']}.json", person, c.PhysicalPerson)
    emit(
        "physical/index.json",
        {
            "version": "physical-research-v1",
            "profiles": [
                {k: p[k] for k in ["id", "name", "season", "competition"]}
                | {"teams": list(p["teams"].values())}
                for p in physical
            ],
            "source": physical[0]["source"],
            "license": "SkillCorner — MIT; see /skillcorner-license.txt",
        },
        c.PhysicalIndex,
    )
    counts = {
        **old["counts"],
        "profiles": len(entries),
        "native_profiles": len(entries),
        "provider_identities": len({(p["provider"], p["id"].split("-")[-1]) for p in entries}),
        "common_profiles": sum(p["capabilities"]["common"] for p in entries),
        "recruitment_profiles": sum(p["capabilities_v12"]["recruitment"] for p in entries),
        "competition_seasons": len(scopes),
        "competitions": len({s["competition_key"] for s in scopes}),
        "provider_competitions": len({(s["provider"], s["id"].split("-")[1]) for s in scopes}),
        "seasons": len({s["season"] for s in scopes}),
        "countries": len({s["country"] for s in scopes}),
        "matches": old["counts"]["matches"]
        + sum(s["catalogue_matches"] for s in sb_report["scopes"]),
        "events": old["counts"]["events"]
        + sum(s["quality"]["events"] for s in sb_report["scopes"]),
        "club_seasons": sum(len(s["clubs"]) for s in scopes),
        "recruitment_clubs": sum(len(s["enabled_clubs"]) for s in caps) + len(wsl["clubs"]),
        "metadata_clubs": sum(not club["performance_scopes"] for club in metadata),
        "metadata_player_records": len(people),
        "metadata_competition_seasons": len(metadata_scopes),
        "specialist_profiles": len(physical),
    }
    index = {
        **old,
        "version": "player-database-v12",
        "counts": counts,
        "scopes": scopes,
        "teams": teams,
        "profiles": sorted(entries, key=lambda p: (p["name"].casefold(), p["id"])),
    }
    emit("index.json", index, c.ExpandedIndex)
    source_hash, code_hash = checksum(root / "config/v12-sources.json"), pipeline_hash(root)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for p in new_profiles:
        entry = new_entries[p["id"]]
        identity = {k: v for k, v in entry.items() if k not in ["capabilities_v12", "detail_path"]}
        emit(
            profile_path(p["id"]),
            {
                "version": "statsbomb-expanded-profile-v1",
                "identity": identity,
                "provider_player_id": p["player_id"],
                "provider_role": p["role"] or p["role_family"],
                "appearances": p["appearances"],
                "first_date": p["first_date"],
                "last_date": p["last_date"],
                "minute_methods": p["minute_methods"],
                "native": p["native"],
                "common": p["common"] if entry["capabilities"]["common"] else None,
                "common_unavailable_reasons": p["common_unavailable"],
                "similarity_version": "not_evaluated",
                "similarity_scope": "not_evaluated",
                "similarity_scaling": "not_evaluated",
                "neighbours": [],
                "provenance": {
                    "source_revision": audit["repositories"]["statsbomb"]["revision"],
                    "source_files": p["source_files"],
                    "source_manifest_sha256": source_hash,
                    "feature_manifest_sha256": checksum(
                        root / "artifacts/v11/public/registry.json"
                    ),
                    "build_manifest": "/data/v12/build-manifest.json",
                    "code_commit": commit,
                    "pipeline_sha256": code_hash,
                },
            },
            c.ExpandedDetail,
        )
    locked = read("config/v12-sources.json")["files"]
    manifest = {
        "version": "v12-build-v1",
        "code_commit": commit,
        "pipeline_sha256": code_hash,
        "source_manifest_sha256": source_hash,
        "evaluation_sha256": checksum(root / "artifacts/v12/wyscout-evaluation.json"),
        "counts": counts,
        "public_files": len(inventory),
        "public_bytes": sum(x["bytes"] for x in inventory),
        "index_gzip_bytes": len(gzip.compress((stage / "index.json").read_bytes(), mtime=0)),
        "source_bytes": sum(x["bytes"] for x in locked),
        "source_files": len(locked),
        "partial": False,
    }
    emit("build-manifest.json", manifest, c.ExpansionManifest)
    if output.exists():
        shutil.rmtree(output)
    shutil.move(stage, output)
    write_json(
        root / "config/v12-public-artifacts.json",
        {"version": "v12-public-artifacts-v1", "files": sorted(inventory, key=lambda f: f["path"])},
    )
    print(json.dumps(manifest, indent=2))
    return manifest
