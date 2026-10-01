"""Strict derived-only publication, lean discovery index and lazy profile shards."""

import gzip
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from football_intelligence.data.schema import canonical_id
from football_intelligence.profiles import contracts
from football_intelligence.profiles.cache import checksum, write_json
from football_intelligence.profiles.evaluate import neighbours
from football_intelligence.profiles.features import COMMON, SB_NATIVE, WS_NATIVE

COMPETITIONS = {
    "statsbomb-2-27": "premier-league",
    "wyscout-364-181150": "premier-league",
    "statsbomb-11-27": "la-liga",
    "wyscout-795-181144": "la-liga",
    "statsbomb-12-27": "serie-a",
    "wyscout-524-181248": "serie-a",
    "statsbomb-37-90": "wsl",
    "statsbomb-37-281": "wsl",
    "statsbomb-135-281": "frauen-bundesliga",
    "wyscout-412-181189": "ligue-1",
    "wyscout-426-181137": "bundesliga",
}
VERSION = {"statsbomb": "statsbomb-profile-v2", "wyscout": "wyscout-profile-v1"}
COMMON_DEFINITIONS = {
    "non_penalty_shots_per90": (
        "Shot attempts excluding penalties, including direct free-kick shots; count × 90 / reliable nominal regulation minutes.",
        "Schotpogingen zonder strafschoppen, inclusief directe vrije trappen; aantal × 90 / betrouwbare nominale reguliere minuten.",
        "Shot, shot.type != Penalty",
        "eventId 10 or eventId 3/subEventId 33; exclude subtype 35",
    ),
    "passes_all_per90": (
        "All pass attempts, including restarts and unsuccessful passes; count × 90 / reliable nominal regulation minutes.",
        "Alle passpogingen, inclusief spelhervattingen en mislukte passes; aantal × 90 / betrouwbare nominale reguliere minuten.",
        "All Pass events",
        "eventId 8 or eventId 3/subEventId 30,31,32,34,36",
    ),
    "long_passes_all_per90": (
        "All pass attempts with endpoint distance ≥30 m on a 105 × 68 m pitch; count × 90 / reliable nominal regulation minutes. Any unavailable endpoint withholds the season rate.",
        "Alle passpogingen met een afstand tussen begin- en eindpunt ≥30 m op een veld van 105 × 68 m; aantal × 90 / betrouwbare nominale reguliere minuten. Een ontbrekend punt maakt de seizoenswaarde niet beschikbaar.",
        "All Pass events, Euclidean distance after 120×80 → 105×68",
        "All common pass attempts, Euclidean distance after percentage → 105×68",
    ),
}


def pipeline_hash(root: Path):
    paths = sorted((root / "src/football_intelligence/profiles").glob("*.py")) + [
        root / "src/football_intelligence/data/adapters/wyscout.py",
        root / "config/v11-expansion.json",
    ]
    digest = hashlib.sha256()
    for p in paths:
        digest.update(str(p.relative_to(root)).encode())
        digest.update(p.read_bytes())
    return digest.hexdigest()


def registry(root: Path, threshold: int):
    features = []
    for key, en, nl, _ in COMMON:
        definition_en, definition_nl, sb, ws = COMMON_DEFINITIONS[key]
        features.append(
            dict(
                id=key,
                en=en,
                nl=nl,
                unit="per90",
                definition_en=definition_en,
                definition_nl=definition_nl,
                statsbomb_mapping=sb,
                wyscout_mapping=ws,
            )
        )
    native = {}
    for provider, rows in (("statsbomb", SB_NATIVE), ("wyscout", WS_NATIVE)):
        native[provider] = [
            dict(
                id=key,
                en=en,
                nl=nl,
                unit="fraction" if numerator == "open_completion" else "per90",
                definition_en=f"{en}. Provider-native definition; "
                + (
                    "completed attempts / attempts with fully known outcomes."
                    if numerator == "open_completion"
                    else "count × 90 / reliable nominal regulation minutes."
                )
                + " Not a harmonised cross-provider metric.",
                definition_nl=f"{nl}. Providerspecifieke definitie; "
                + (
                    "geslaagde pogingen / pogingen met volledig bekende uitkomsten."
                    if numerator == "open_completion"
                    else "aantal × 90 / betrouwbare nominale reguliere minuten."
                )
                + " Geen geharmoniseerd kenmerk voor vergelijking tussen providers.",
                statsbomb_mapping=en if provider == "statsbomb" else "not_applicable",
                wyscout_mapping=en if provider == "wyscout" else "not_applicable",
            )
            for key, en, nl, numerator in rows
        ]
    definitions = dict(
        features=features,
        **native,
        coordinate_convention="105x68_m_upper_left_origin_attack_positive_x_every_period_no_period_flip",
        denominator="nominal_regulation_minutes_45_plus_45_numerator_includes_stoppage_events",
        excluded_concepts=[
            "pass_completion",
            "completed_progressive_passes",
            "completed_final_third_entries",
            "completed_box_entries",
            "pressures",
            "carries",
            "crosses",
            "tackles",
            "interceptions",
            "duels",
            "provider_xg",
            "provider_xa",
            "possessions",
        ],
        scaler_policy="common_similarity_shared_zscore_first_half_development_only; no scaling for descriptive raw comparison",
        evidence_threshold=threshold,
    )
    sources = json.loads((root / "config/v11-sources.json").read_text())
    return dict(
        version="common-profile-v1",
        **definitions,
        validation_date="2026-10-01",
        source_versions={
            "statsbomb": sources["statsbomb_revision"],
            "wyscout": "figshare_collection_4415000_v5_events_article_7770599_v1",
        },
        definitions_sha256=hashlib.sha256(
            json.dumps(definitions, sort_keys=True).encode()
        ).hexdigest(),
    )


def profile_path(profile_id: str):
    return f"profiles/{profile_id.split('-')[-1][-2:].zfill(2)}/{profile_id}.json"


def publish(root: Path):
    destination = root / "data/processed/v11/full"
    raw = json.loads((destination / "aggregates.json").read_text())
    season_reports = json.loads((destination / "coverage.json").read_text())
    evaluation = json.loads((root / "artifacts/v11/evaluation.json").read_text())
    config = json.loads((root / "config/v11-expansion.json").read_text())
    if any(c["matches"] != c["catalogue_matches"] for c in season_reports) or len(
        season_reports
    ) != len(config["statsbomb_seasons"]) + len(config["wyscout_members"]):
        raise ValueError("Partial datasets cannot overwrite production")
    threshold = evaluation["selected_threshold"]
    selected = next(
        r
        for r in evaluation["temporal"]
        if r["threshold"] == threshold and r["scaling"] == "shared"
    )
    validated = {(r["scope"], r["role"]) for r in selected["cohorts"] if r["status"] == "evaluated"}
    profiles = sorted(
        [p for p in raw if p["reliable"] and p["minutes"] >= 450],
        key=lambda p: (p["name"].casefold(), p["id"]),
    )
    common_profiles = [p for p in profiles if p["common_ready"] and p["minutes"] >= threshold]
    original_dna = {
        p["player_id"]
        for p in json.loads((root / "artifacts/phase2/public/index.json").read_text())["players"]
        if not p["eligibility"]["900"]
    }
    index_rows = []
    for p in profiles:
        is_common = p["common_ready"] and p["minutes"] >= threshold
        dna = (
            p["scope"] == "statsbomb-37-281"
            and str(canonical_id("statsbomb", "players", p["player_id"])) in original_dna
        )
        index_rows.append(
            dict(
                id=p["id"],
                name=p["name"],
                provider=p["provider"],
                scope=p["scope"],
                teams=[f"{p['provider']}:{t}" for t in p["teams"]],
                role=p["role"],
                role_family=p["role_family"],
                minutes=p["minutes"],
                capabilities=dict(
                    common=is_common,
                    similarity=is_common and (p["scope"], p["role_family"]) in validated,
                    translation=False,
                    validated_dna=dna,
                ),
            )
        )
    # None of these scopes is the original 2019/20 Phase-3 SOURCE season.
    # Matching a player name/ID in the target season must not imply translation eligibility.
    scopes = []
    teams = {}
    for c in sorted(season_reports, key=lambda c: c["scope"]):
        rows = [p for p in index_rows if p["scope"] == c["scope"]]
        scopes.append(
            dict(
                id=c["scope"],
                provider=c["provider"],
                competition=c["competition"],
                competition_key=COMPETITIONS[c["scope"]],
                season=c["season"],
                gender=c["gender"],
                matches=c["matches"],
                profiles=len(rows),
                common_profiles=sum(p["capabilities"]["common"] for p in rows),
                similarity_profiles=sum(p["capabilities"]["similarity"] for p in rows),
                coverage=c["coverage"],
                first_date=c["first_date"],
                last_date=c["last_date"],
            )
        )
        teams.update({f"{c['provider']}:{tid}": name for tid, name in c["teams"].items()})
    # Competition identifiers stay provider scoped. Count provider competitions explicitly.
    counts = dict(
        providers=2,
        competitions=len(set(COMPETITIONS.values())),
        provider_competitions=len({(c["provider"], c["competition_id"]) for c in season_reports}),
        competition_seasons=len(scopes),
        seasons=len({c["season"] for c in scopes}),
        matches=sum(c["matches"] for c in scopes),
        events=sum(c["quality"]["events"] for c in season_reports),
        profiles=len(profiles),
        provider_identities=len({(p["provider"], p["player_id"]) for p in profiles}),
        native_profiles=len(profiles),
        common_profiles=len(common_profiles),
        similarity_profiles=sum(p["capabilities"]["similarity"] for p in index_rows),
        translation_profiles=0,
        validated_dna_profiles=sum(p["capabilities"]["validated_dna"] for p in index_rows),
    )
    index = dict(
        version="player-database-v1",
        common_version="common-profile-v1",
        common_threshold=threshold,
        search_threshold=450,
        counts=counts,
        scopes=scopes,
        teams=teams,
        profiles=index_rows,
    )
    output = root / "artifacts/v11/public"
    if output.exists():
        shutil.rmtree(output)
    inventory = []

    def emit(path, value, model):
        value = model.model_validate(value).model_dump(mode="json")
        target = output / path
        write_json(target, value, compact=True)
        size = target.stat().st_size
        if path.startswith("profiles/") and size >= 50_000:
            raise ValueError("Profile budget exceeded")
        inventory.append(
            dict(
                path="data/v11/" + path,
                source=str(target.relative_to(root)),
                bytes=size,
                sha256=checksum(target),
                schema=model.__name__,
                array=False,
            )
        )
        return checksum(target)

    emit("index.json", index, contracts.ProfileIndex)
    feature_hash = emit("registry.json", registry(root, threshold), contracts.ProfileRegistry)
    source_hash = checksum(root / "config/v11-sources.json")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    code_hash = pipeline_hash(root)
    revision_map = {c["scope"]: c["source_revision"] for c in season_reports}
    for p, entry in zip(profiles, index_rows, strict=True):
        reasons = (
            []
            if entry["capabilities"]["common"]
            else (["goalkeeper_excluded"] if p["role_family"] == "GK" else [])
            + (["below_common_minutes"] if p["minutes"] < threshold else [])
            + ["unavailable:" + k for k in p["common_unavailable"]]
        )
        emit(
            profile_path(p["id"]),
            dict(
                version=VERSION[p["provider"]],
                identity=entry,
                provider_player_id=p["player_id"],
                provider_role=("GKP" if p["role_family"] == "GK" else p["role_family"])
                if p["provider"] == "wyscout"
                else p["role"] or p["role_family"],
                appearances=p["appearances"],
                first_date=p["first_date"],
                last_date=p["last_date"],
                minute_methods=p["minute_methods"],
                native=p["native"],
                common=p["common"] if entry["capabilities"]["common"] else None,
                common_unavailable_reasons=reasons,
                similarity_version="common-similarity-v1",
                similarity_scope="same_provider_competition_season_role",
                similarity_scaling="shared_first_half_development_zscore",
                neighbours=neighbours(p, common_profiles, evaluation["scalers"])
                if entry["capabilities"]["similarity"]
                else [],
                dna_player_id=str(canonical_id("statsbomb", "players", p["player_id"]))
                if entry["capabilities"]["validated_dna"]
                else None,
                provenance=dict(
                    source_revision=revision_map[p["scope"]],
                    source_files=p["source_files"],
                    source_manifest_sha256=source_hash,
                    feature_manifest_sha256=feature_hash,
                    build_manifest="/data/v11/build-manifest.json",
                    code_commit=commit,
                    pipeline_sha256=code_hash,
                ),
            ),
            contracts.ProfileDetail,
        )
    coverage = dict(
        version="player-database-v1",
        counts=counts,
        scopes=scopes,
        common_threshold=threshold,
        common_features=evaluation["features"],
        provider_bias={
            k: evaluation["provider_classification"]["primary"][k]
            for k in ("auc", "balanced_accuracy", "heldout_profiles")
        },
        cross_provider_ranking_enabled=evaluation["cross_provider_ranking_enabled"],
        temporal_mrr={provider: v["mrr"] for provider, v in selected["providers"].items()},
        excluded_profiles=dict(Counter(reason for p in raw for reason in p["exclusion_reasons"])),
        threshold_counts={
            str(t): sum(p["common_ready"] and p["minutes"] >= t for p in raw)
            for t in (450, 600, 900)
        },
    )
    emit("coverage.json", coverage, contracts.ProfileCoverage)
    index_bytes = (output / "index.json").read_bytes()
    compressed = len(gzip.compress(index_bytes, mtime=0))
    if compressed >= 1_000_000:
        raise ValueError("Compressed search index budget exceeded")
    manifest = dict(
        version="player-database-v1",
        code_commit=commit,
        pipeline_sha256=code_hash,
        source_manifest_sha256=source_hash,
        feature_manifest_sha256=feature_hash,
        evaluation_sha256=checksum(root / "artifacts/v11/evaluation.json"),
        public_files=len(inventory),
        public_bytes=sum(p["bytes"] for p in inventory),
        index_bytes=len(index_bytes),
        index_gzip_bytes=compressed,
        largest_profile_bytes=max(p["bytes"] for p in inventory if "/profiles/" in p["path"]),
        counts=counts,
        partial=False,
    )
    emit("build-manifest.json", manifest, contracts.ProfileBuildManifest)
    write_json(
        root / "config/v11-public-artifacts.json",
        dict(version="v11-public-artifacts-v1", files=sorted(inventory, key=lambda f: f["path"])),
    )
    print(json.dumps(manifest, indent=2), flush=True)
    return manifest
