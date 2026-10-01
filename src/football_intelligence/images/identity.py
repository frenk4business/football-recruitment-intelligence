"""Provider-scoped identity evidence and deterministic conservative resolution."""

import hashlib
import json
import re
import unicodedata
from pathlib import Path


def normalize(value: str) -> str:
    return " ".join(
        re.sub(
            r"[^\w ]",
            " ",
            "".join(
                c
                for c in unicodedata.normalize("NFKD", value.casefold())
                if not unicodedata.combining(c)
            ),
        ).split()
    )


def identities(root: Path) -> list[dict]:
    index = json.loads((root / "artifacts/v11/public/index.json").read_text())
    scopes = {s["id"]: s for s in index["scopes"]}
    result: dict[str, dict] = {}
    for profile in index["profiles"]:
        provider, _, _, pid = profile["id"].split("-")
        key = f"{provider}:{pid}"
        record = result.setdefault(
            key,
            {
                "id": key,
                "provider": provider,
                "provider_player_id": pid,
                "names": [],
                "profiles": [],
                "teams": [],
                "contexts": [],
                "dob": None,
                "nationalities": [],
                "source_files": [],
            },
        )
        record["names"] = sorted(set(record["names"] + [profile["name"]]))
        record["profiles"].append(profile["id"])
        record["teams"] = sorted(
            set(record["teams"] + [index["teams"][t] for t in profile["teams"]])
        )
        s = scopes[profile["scope"]]
        record["contexts"].append({k: s[k] for k in ("id", "competition", "season", "gender")})
    lock = {
        f["path"]: f["sha256"]
        for f in json.loads((root / "config/v11-sources.json").read_text())["files"]
    }
    source_root = root / "data/raw/v11/sources"

    def read_source(relative):
        path = source_root / relative
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != lock[relative]:
            raise ValueError(f"Player source differs from pinned provider metadata: {relative}")
        return json.loads(raw), {"path": relative, "sha256": lock[relative]}

    wy_path = "wyscout/players.json"
    if (source_root / wy_path).exists():
        values, source = read_source(wy_path)
        for p in values:
            key = f"wyscout:{p['wyId']}"
            if key in result:
                row = result[key]
                row["dob"] = p.get("birthDate") or None
                row["nationalities"] = (
                    [p["passportArea"]["name"]] if p.get("passportArea", {}).get("name") else []
                )
                row["source_files"].append(source)
    for path in sorted(source_root.glob("statsbomb/*/data/lineups/*.json")):
        if path.name.endswith(".sha.json"):
            continue
        values, source = read_source(str(path.relative_to(source_root)))
        for team in values:
            for player in team["lineup"]:
                sb_row = result.get(f"statsbomb:{player['player_id']}")
                if sb_row is None:
                    continue
                for name in [player.get("player_name"), player.get("player_nickname")]:
                    if name and name not in sb_row["names"]:
                        sb_row["names"].append(name)
                country = player.get("country", {}).get("name")
                if country and country not in sb_row["nationalities"]:
                    sb_row["nationalities"].append(country)
                # One pinned observed lineup suffices to trace metadata, without copying raw records.
                if not sb_row["source_files"]:
                    sb_row["source_files"].append(source)
    frequencies: dict[tuple[str, str], int] = {}
    for row in result.values():
        if not row["source_files"]:
            raise ValueError(f"Pinned raw player metadata is required for enrichment: {row['id']}")
        name_key = (row["provider"], normalize(row["names"][0]))
        frequencies[name_key] = frequencies.get(name_key, 0) + 1
    for row in result.values():
        row["common_name_review"] = (
            frequencies[(row["provider"], normalize(row["names"][0]))] > 1
            or len(normalize(row["names"][0]).split()) < 2
        )
    return [result[k] for k in sorted(result)]


def values(entity: dict, prop: str):
    return [
        s["mainsnak"]["datavalue"]["value"]
        for s in entity.get("claims", {}).get(prop, [])
        if s.get("rank") != "deprecated"
        and s.get("mainsnak", {}).get("snaktype") == "value"
        and "datavalue" in s["mainsnak"]
    ]


def labels(entity: dict) -> set[str]:
    return {normalize(v["value"]) for v in entity.get("labels", {}).values()} | {
        normalize(a["value"]) for aliases in entity.get("aliases", {}).values() for a in aliases
    }


def evaluate(
    person: dict, candidates: list[dict], related: dict, override: dict | None = None
) -> dict:
    override = override or {}
    if override.get("status") == "excluded":
        return {
            "status": "excluded",
            "method": "manual_exclusion",
            "reason": override["reason"],
            "candidates": [],
        }
    rows = []
    for entity in candidates:
        names = labels(entity)
        name_match = bool(names & {normalize(n) for n in person["names"]})
        display_name = entity.get("labels", {}).get("en", {}).get("value", "")
        display_tokens = set(normalize(display_name).split())
        label_compatible = len(display_tokens) >= 2 and any(
            display_tokens <= set(normalize(n).split()) for n in person["names"]
        )
        dobs = [
            v["time"][1:11]
            for v in values(entity, "P569")
            if isinstance(v, dict)
            and v.get("precision", 0) >= 11
            and v.get("calendarmodel", "").endswith("Q1985727")
        ]
        dob_match = bool(person["dob"] and person["dob"] in dobs)
        dob_conflict = bool(person["dob"] and any(d != person["dob"] for d in dobs))
        footballer = any(
            v.get("id") == "Q937857" for v in values(entity, "P106") if isinstance(v, dict)
        )
        countries = {v["id"] for v in values(entity, "P27") if isinstance(v, dict)}
        country_names = set().union(*(labels(related.get(q, {})) for q in countries))
        supplied_countries = {normalize(n) for n in person["nationalities"]}
        # Source football nationality and Wikidata citizenship are different concepts.
        nationality_match = bool(country_names & supplied_countries)
        # Source football-country labels can name a UK constituent nation while
        # Wikidata records UK citizenship. This is compatible, not a contradiction.
        uk_compatible = "Q145" in countries and bool(
            supplied_countries & {"england", "scotland", "wales", "northern ireland"}
        )
        nationality_match = nationality_match or uk_compatible
        nationality_conflict = bool(
            person["provider"] == "wyscout"
            and country_names
            and supplied_countries
            and not nationality_match
        )
        clubs = {v["id"] for v in values(entity, "P54") if isinstance(v, dict)}
        club_names = set().union(*(labels(related.get(q, {})) for q in clubs))
        club_match = bool(club_names & {normalize(n) for n in person["teams"]})
        genders = {v["id"] for v in values(entity, "P21") if isinstance(v, dict)}
        source_genders = {c["gender"] for c in person["contexts"]}
        gender_conflict = ("male" in source_genders and "Q6581072" in genders) or (
            "female" in source_genders and "Q6581097" in genders
        )
        conflict = dob_conflict or nationality_conflict or gender_conflict
        signals = {
            "name_or_alias": name_match,
            "label_name_compatible": label_compatible,
            "dob_match": dob_match,
            "dob_conflict": dob_conflict,
            "footballer": footballer,
            "nationality_match": nationality_match,
            "uk_constituent_country_compatible": uk_compatible,
            "nationality_conflict": nationality_conflict,
            "historical_club_match": club_match,
            "gender_conflict": gender_conflict,
        }
        rows.append(
            {
                "qid": entity["id"],
                "names": [entity.get("labels", {}).get("en", {}).get("value", entity["id"])],
                "matched_names_or_aliases": sorted(names & {normalize(n) for n in person["names"]}),
                "dob": dobs,
                "country_qids": sorted(countries),
                "country_names": sorted(
                    {
                        related.get(q, {}).get("labels", {}).get("en", {}).get("value", q)
                        for q in countries
                    }
                ),
                "club_qids": sorted(clubs),
                "club_names": sorted(
                    {
                        related.get(q, {}).get("labels", {}).get("en", {}).get("value", q)
                        for q in clubs
                    }
                ),
                "images": values(entity, "P18"),
                "signals": signals,
                "credible": name_match and footballer,
                "automatic": name_match
                and label_compatible
                and dob_match
                and footballer
                and nationality_match
                and not conflict,
                "conflict": conflict,
            }
        )
    if override.get("status") == "verified":
        row = next((r for r in rows if r["qid"] == override.get("wikidata_id")), None)
        if (
            not row
            or not override.get("reason")
            or not override.get("reviewer")
            or len(override.get("evidence_urls", [])) < 2
        ):
            raise ValueError(
                "Verified override requires fetched QID, reviewer, reason and two independent evidence URLs"
            )
        return {
            "status": "verified",
            "method": "manual_metadata_review",
            "reason": override["reason"],
            "qid": row["qid"],
            "candidates": rows,
            "override": override,
        }
    credible = [r for r in rows if r["credible"]]
    if len(credible) > 1 or any(r["conflict"] for r in credible):
        return {
            "status": "ambiguous",
            "method": "deterministic_v1",
            "reason": "multiple_candidates_or_conflicting_evidence",
            "candidates": rows,
        }
    if (
        len(rows) == 1
        and len(credible) == 1
        and credible[0]["automatic"]
        and not person.get("common_name_review")
    ):
        return {
            "status": "verified",
            "method": "name_dob_occupation_citizenship",
            "reason": "independent_identity_evidence",
            "qid": credible[0]["qid"],
            "candidates": rows,
        }
    if credible:
        return {
            "status": "likely",
            "method": "deterministic_v1",
            "reason": "manual_review_required_no_dob_multiple_candidates_divergent_alias_or_insufficient_context",
            "candidates": rows,
        }
    return {
        "status": "none",
        "method": "deterministic_v1",
        "reason": "no_supported_candidate",
        "candidates": rows,
    }
