"""Dated, source-scoped metadata; fixtures never become performance features."""

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from football_intelligence.expansion.sources import Sources
from football_intelligence.profiles.cache import write_json
from football_intelligence.profiles.ingest import decode_name

COUNTRIES = {
    "bosnia-n-herzegovina": "Bosnia and Herzegovina",
    "latvija": "Latvia",
    "macedonia": "North Macedonia",
    "england": "England",
    "scotland": "Scotland",
    "wales": "Wales",
    "northern-ireland": "Northern Ireland",
    "czech-republic": "Czech Republic",
    "bosnia-herzegovina": "Bosnia and Herzegovina",
    "turkey": "Turkey",
    "germany": "Germany",
    "deutschland": "Germany",
}
JSON_COUNTRIES = {
    "at": "Austria",
    "be": "Belgium",
    "ch": "Switzerland",
    "cz": "Czech Republic",
    "de": "Germany",
    "dk": "Denmark",
    "en": "England",
    "es": "Spain",
    "fi": "Finland",
    "fr": "France",
    "gr": "Greece",
    "hu": "Hungary",
    "ie": "Ireland",
    "it": "Italy",
    "nl": "Netherlands",
    "no": "Norway",
    "pl": "Poland",
    "pt": "Portugal",
    "ro": "Romania",
    "ru": "Russia",
    "sco": "Scotland",
    "se": "Sweden",
    "tr": "Turkey",
    "ua": "Ukraine",
    "uefa": "Europe",
}


def normalize(value: str) -> str:
    return " ".join(
        re.sub(
            r"[^\w\s]",
            " ",
            "".join(
                c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)
            ).casefold(),
        ).split()
    )


def identifier(kind: str, *parts: str) -> str:
    return "openfootball-" + kind + "-" + hashlib.sha256("\0".join(parts).encode()).hexdigest()[:20]


def country(folder: str) -> str:
    return COUNTRIES.get(folder, folder.replace("-", " ").title())


def parse_clubs(text: str, nation: str, source: str) -> tuple[list[dict], list[dict]]:
    records, rejected = [], []
    current: dict | None = None
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("=", "--")):
            continue
        if line.startswith("|"):
            if current is not None:
                current["aliases"].extend(x.strip() for x in line.split("|") if x.strip())
            else:
                rejected.append({"line": line_number, "reason": "alias_without_club", "text": raw})
            continue
        name = re.sub(r"^ii\)\s*", "", line.split(",", 1)[0].strip())
        if not name or name.startswith(("@", "[")):
            rejected.append({"line": line_number, "reason": "unrecognized_club_row", "text": raw})
            continue
        stadium = re.search(r"@\s*([^,]+)", line)
        current = {
            "id": identifier("club", nation, normalize(name)),
            "name": name,
            "country": nation,
            "aliases": [],
            "stadium": stadium[1].strip() if stadium else None,
            "source": source,
            "source_line": line_number,
        }
        records.append(current)
    return records, rejected


def parse_players(text: str, nation: str, source: str) -> tuple[list[dict], list[dict]]:
    records, rejected = [], []
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("=", "|", "--")):
            continue
        fields = [v.strip() for v in line.split(",", 3)]
        if len(fields) != 4 or not all(
            p in {"G", "GK", "D", "DF", "M", "MF", "F", "FW"} for p in fields[1].split("|")
        ):
            rejected.append({"line": line_number, "reason": "unsupported_player_row", "text": raw})
            continue
        birth = re.search(r"b\.\s*(\d{1,2}\s+\w+\s+\d{4})", fields[3])
        dob = None
        if birth:
            try:
                dob = (
                    datetime.strptime(birth[1].replace("Sept", "Sep"), "%d %b %Y")
                    .date()
                    .isoformat()
                )
            except ValueError:
                pass
        height = re.fullmatch(r"(\d\.\d{2})\s*m", fields[2])
        records.append(
            {
                "id": identifier(
                    "player", nation, normalize(fields[0]), dob or f"{source}:{line_number}"
                ),
                "name": fields[0],
                "country": nation,
                "dob": dob,
                "height_m": float(height[1]) if height else None,
                "position": fields[1],
                "source": source,
                "source_line": line_number,
                "capabilities": {
                    "searchable": True,
                    "metadata_only": True,
                    "provider_profile": False,
                    "similarity": False,
                    "recruitment": False,
                    "common_profile": False,
                    "translation": False,
                    "physical": False,
                },
            }
        )
    return records, rejected


def parse_fixtures(text: str) -> tuple[list[dict], list[dict]]:
    """Conservative Football.TXT fixtures; dates retained verbatim, never guessed."""
    rows, rejected = [], []
    date, round_ = None, None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", "=")):
            continue
        if line.startswith(("▪", "»")) or line.startswith(("Matchday", "Round")):
            round_ = line.lstrip("▪» ")
            continue
        if re.match(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b", line) or re.match(r"^\[.*\]$", line):
            date = line
            continue
        middle_score = re.fullmatch(
            r"(?:(\d{1,2}:\d{2})\s+)?(.+?)\s{2,}(\d+)-(\d+)(?:\s+\([^)]*\))?\s{2,}(.+)", line
        )
        if middle_score and not re.search(r"\s+v\s+", line):
            time, home, a, b, away = middle_score.groups()
            rows.append(
                {
                    "home": home.strip(),
                    "away": away.strip(),
                    "date_text": date,
                    "time": time,
                    "round": round_,
                    "score": [int(a), int(b)],
                    "score_note": None,
                    "source_line": n,
                }
            )
        elif re.search(r"\s+v\s+", line):
            home, remainder = re.split(r"\s+v\s+", line, maxsplit=1)
            time = re.match(r"^(\d{1,2}:\d{2})\s+", home)
            home = home[time.end() :] if time else home
            score = re.search(r"\s+(\d+)\s*[-:]\s*(\d+)(?=\s|$)", remainder)
            away = remainder[: score.start()].strip() if score else remainder.strip()
            status = re.search(
                r"\s*\[(?:postponed|cancelled|awarded|abandoned|suspended)[^]]*\]\s*$", away, re.I
            )
            if status:
                away = away[: status.start()].strip()
            # Status-only suffix is not part of a team's identity.
            away = re.split(r"\s{2,}(?:postp|canc|awd|abd|susp|ppd)", away, flags=re.I)[0].strip()
            if not home or not away or "#" in away:
                rejected.append({"line": n, "reason": "ambiguous_fixture", "text": raw})
                continue
            rows.append(
                {
                    "home": home.strip(),
                    "away": away,
                    "date_text": date,
                    "time": time[1] if time else None,
                    "round": round_,
                    "score": [int(score[1]), int(score[2])] if score else None,
                    "score_note": remainder[score.end() :].strip()
                    if score
                    else status[0].strip()
                    if status
                    else None,
                    "source_line": n,
                }
            )
        elif re.search(r"\d+[-:]\d+", line):
            rejected.append({"line": n, "reason": "unsupported_fixture_syntax", "text": raw})
    return rows, rejected


def score_value(value):
    score = value.get("ft") if isinstance(value, dict) else value
    if score is None:
        return None
    if (
        not isinstance(score, list)
        or len(score) != 2
        or any(type(v) is not int or v < 0 for v in score)
    ):
        raise ValueError("Unsupported fixture score")
    return score


def build(root: Path):
    sources = Sources(root)
    output = root / "data/processed/v12/metadata"
    output.mkdir(parents=True, exist_ok=True)
    clubs: dict[str, dict] = {}
    players: dict[str, dict] = {}
    issues: list[dict] = []

    def files(key, pattern):
        base = sources.cache.root / key / sources.audit["repositories"][key]["revision"]
        paths = sorted(p for p in base.glob(pattern) if not p.name.endswith(".sha.json"))
        if not paths:
            raise ValueError(f"Missing pinned metadata source: {key}")
        from football_intelligence.profiles.cache import checksum

        for path in paths:
            lock = sources.expected.get(path.relative_to(sources.cache.root).as_posix())
            if not lock or checksum(path) != lock["sha256"]:
                raise ValueError(f"Unverified metadata input: {path}")
        return base, paths

    def url(key, relative):
        repo = sources.audit["repositories"][key]
        return f"https://github.com/{repo['repository']}/blob/{repo['revision']}/{relative}"

    base, paths = files("openfootball-clubs", "europe/**/*.clubs.txt")
    for path in paths:
        relative = path.relative_to(base).as_posix()
        rows, errors = parse_clubs(
            path.read_text(), country(Path(relative).parts[1]), url("openfootball-clubs", relative)
        )
        issues.extend({"file": relative, **e} for e in errors)
        for row in rows:
            if row["id"] in clubs:
                clubs[row["id"]]["aliases"] += [row["name"], *row["aliases"]]
            else:
                clubs[row["id"]] = row
    aliases: dict[tuple[str, str], set[str]] = defaultdict(set)
    for c in clubs.values():
        c["aliases"] = sorted(set(c["aliases"]))
        for name in [c["name"], *c["aliases"]]:
            aliases[(c["country"], normalize(name))].add(c["id"])
    collisions = [
        {"country": key[0], "alias": key[1], "clubs": sorted(ids)}
        for key, ids in sorted(aliases.items())
        if len(ids) > 1
    ]

    def resolve(nation, name, source):
        ids = aliases.get((nation, normalize(name)), set())
        if len(ids) == 1:
            return next(iter(ids))
        cid = identifier("fixture-club", nation, normalize(name))
        if cid not in clubs:
            clubs[cid] = {
                "id": cid,
                "name": name,
                "country": nation,
                "aliases": [],
                "stadium": None,
                "source": source,
                "source_line": None,
                "resolution": "ambiguous_alias_retained_separately"
                if ids
                else "fixture_source_identity",
            }
        return cid

    base, paths = files("openfootball-players", "europe/**/*.players.txt")
    for path in paths:
        relative = path.relative_to(base).as_posix()
        rows, errors = parse_players(
            path.read_text(),
            country(Path(relative).parts[1]),
            url("openfootball-players", relative),
        )
        issues.extend({"file": relative, **e} for e in errors)
        for row in rows:
            if row["id"] in players and any(
                row[k] != players[row["id"]][k] for k in ["dob", "height_m", "position"]
            ):
                issues.append(
                    {"file": relative, "reason": "conflicting_duplicate_player", "id": row["id"]}
                )
                players[row["id"]]["conflicting_source_rows"] = True
            else:
                players[row["id"]] = row
    scopes = []
    seen_fixture_sources = set()
    for key, pattern in [("openfootball-europe", "**/*.txt"), ("openfootball-json", "*/*.json")]:
        base, paths = files(key, pattern)
        for path in paths:
            relative = path.relative_to(base).as_posix()
            if key == "openfootball-europe":
                if len(Path(relative).parts) != 2 or not re.match(r"\d{4}", path.name):
                    continue
                nation = country(Path(relative).parts[0])
                season = path.stem.split("_")[0]
                code = path.stem.split("_", 1)[-1]
                text = path.read_text()
                name = next(
                    (line.lstrip("= ") for line in text.splitlines() if line.startswith("= ")),
                    path.stem,
                )
                rows, errors = parse_fixtures(text)
                issues.extend({"file": relative, **e} for e in errors)
            else:
                json_nation = JSON_COUNTRIES.get(path.name.split(".")[0])
                if json_nation is None:
                    continue
                nation = json_nation
                season, code = Path(relative).parts[0], path.stem
                value = json.loads(path.read_text())
                name = value.get("name", path.stem)
                raw = value.get(
                    "matches", [m for r in value.get("rounds", []) for m in r.get("matches", [])]
                )
                rows = [
                    {
                        "home": m["team1"],
                        "away": m["team2"],
                        "date_text": m.get("date"),
                        "time": m.get("time"),
                        "round": m.get("round"),
                        "score": score_value(m.get("score")),
                        "source_line": i + 1,
                        "score_note": m.get("status"),
                        "stage": m.get("stage"),
                    }
                    for i, m in enumerate(raw)
                ]
            source = url(key, relative)
            sid = identifier("scope", key, relative)
            fixtures = []
            for row in rows:
                if not isinstance(row["home"], str) or not isinstance(row["away"], str):
                    issues.append({"file": relative, "reason": "non_string_club_name"})
                    continue
                home, away = (
                    resolve(nation, row["home"], source),
                    resolve(nation, row["away"], source),
                )
                # Deduplicate only exact source scope/date/teams. Cross-repository observations retain their sources.
                identity = (sid, row["date_text"], home, away, row["round"])
                if identity in seen_fixture_sources:
                    issues.append(
                        {"file": relative, "reason": "duplicate_fixture", "identity": identity}
                    )
                    continue
                seen_fixture_sources.add(identity)
                fixtures.append({**row, "home": home, "away": away})
            if not fixtures:
                continue
            ids = sorted({tid for f in fixtures for tid in [f["home"], f["away"]]})
            scopes.append(
                {
                    "id": sid,
                    "name": name,
                    "country": nation,
                    "season": season,
                    "competition_code": code,
                    "clubs": ids,
                    "fixtures": len(fixtures),
                    "results": sum(f["score"] is not None for f in fixtures),
                    "source": source,
                    "provider": key,
                    "metadata_updated": sources.audit["repositories"][key]["committed_at"],
                    "capabilities": {
                        "metadata": True,
                        "team_context": False,
                        "recruitment": False,
                        "candidate_cohort": False,
                        "translation": False,
                        "tracking": False,
                    },
                }
            )
            write_json(
                output / "fixtures" / f"{sid}.json",
                {"scope": sid, "source": source, "fixtures": fixtures},
                compact=True,
            )
    for c in clubs.values():
        c["seasons"] = [s["id"] for s in scopes if c["id"] in s["clubs"]]
        source_key = next(
            k
            for k in ["openfootball-clubs", "openfootball-europe", "openfootball-json"]
            if sources.audit["repositories"][k]["repository"] + "/blob/" in c["source"]
        )
        c["metadata_updated"] = sources.audit["repositories"][source_key]["committed_at"]
        c["capabilities"] = {
            "metadata": True,
            "team_context": False,
            "recruitment": False,
            "candidate_cohort": False,
            "translation": False,
            "tracking": False,
        }
    # External metadata candidates remain separate, including verified matches.
    by_name: dict[str, list] = defaultdict(list)
    for p in players.values():
        by_name[normalize(p["name"])].append(p)
    wyscout = json.loads((root / "data/raw/v11/sources/wyscout/players.json").read_text())
    candidates = []
    for p in wyscout:
        name = decode_name(
            " ".join(p.get(k, "") for k in ["firstName", "middleName", "lastName"]).strip()
        )
        options = by_name.get(normalize(name), [])
        strong = [
            q
            for q in options
            if q["dob"]
            and q["dob"] == p.get("birthDate")
            and q["country"] == p.get("passportArea", {}).get("name")
            and not q.get("conflicting_source_rows")
        ]
        status = (
            "verified"
            if len(strong) == len(options) == 1
            else "ambiguous"
            if len(options) > 1
            else "likely"
            if options
            else "none"
        )
        candidates.append(
            {
                "provider_identity": f"wyscout:{p['wyId']}",
                "name": name,
                "status": status,
                "external_metadata_candidate": [q["id"] for q in options],
                "accepted_metadata_id": strong[0]["id"] if status == "verified" else None,
                "method": "unique_normalized_full_name_exact_DOB_exact_passport_country"
                if status == "verified"
                else "no_automatic_enrichment",
                "scientific_identity_merge": False,
            }
        )
    write_json(
        output / "clubs.json",
        sorted(clubs.values(), key=lambda c: (c["country"], c["name"], c["id"])),
        compact=True,
    )
    write_json(
        output / "players.json",
        sorted(players.values(), key=lambda p: (p["name"], p["id"])),
        compact=True,
    )
    write_json(output / "competitions.json", scopes, compact=True)
    write_json(output / "identity-candidates.json", candidates, compact=True)
    write_json(
        root / "artifacts/v12/metadata-quality.json",
        {
            "clubs": len(clubs),
            "player_metadata_records": len(players),
            "competition_seasons": len(scopes),
            "fixture_observations": sum(s["fixtures"] for s in scopes),
            "countries": sorted({s["country"] for s in scopes}),
            "identity_statuses": dict(Counter(c["status"] for c in candidates)),
            "alias_collisions": collisions,
            "issues": issues,
            "count_policy": "Source-scoped observations; do not claim deduplicated real-world fixtures or people. Metadata is not performance.",
        },
    )
    print(
        f"OpenFootball: {len(clubs)} club records, {len(players)} player metadata records, {len(scopes)} source competition-seasons; {len(issues)} retained parser/duplicate diagnostics",
        flush=True,
    )
    return clubs, players, scopes


def skillcorner(root: Path):
    sources = Sources(root)
    repo = sources.audit["repositories"]["skillcorner"]
    base = sources.cache.root / "skillcorner" / repo["revision"]
    people: dict[str, dict] = {}
    counts = {}
    from football_intelligence.profiles.cache import checksum

    paths = sorted((base / "data/aggregates").glob("*.csv"))
    if len(paths) != 3:
        raise ValueError("Expected all three pinned SkillCorner aggregate files")
    for path in paths:
        lock = sources.expected.get(path.relative_to(sources.cache.root).as_posix())
        if not lock or checksum(path) != lock["sha256"]:
            raise ValueError(f"Unverified SkillCorner input: {path}")
        kind = next(k for k in ["physical", "obr", "passing"] if k in path.name)
        rows = list(csv.DictReader(path.open()))
        counts[kind] = len(rows)
        for row in rows:
            key = (row["player_id"], row["season_id"])
            pid = f"skillcorner-{key[0]}-{key[1]}"
            person = people.setdefault(
                pid,
                {
                    "id": pid,
                    "provider": "skillcorner",
                    "provider_player_id": key[0],
                    "name": row["player_name"],
                    "season": row["season_name"],
                    "competition": row["competition_name"],
                    "country": "Australia",
                    "teams": {},
                    "records": [],
                    "capabilities": {
                        "searchable": True,
                        "metadata_only": False,
                        "provider_profile": False,
                        "similarity": False,
                        "recruitment": False,
                        "common_profile": False,
                        "translation": False,
                        "physical": True,
                    },
                    "scope_note": "Specialist A-League research; source aggregates cover performances above 60 minutes, not complete European event coverage.",
                    "source": f"https://github.com/{repo['repository']}/tree/{repo['revision']}/data/aggregates",
                },
            )
            person["teams"][row["team_id"]] = row["team_name"]
            metrics = {
                k: v
                for k, v in row.items()
                if k
                not in {
                    "player_name",
                    "player_short_name",
                    "player_id",
                    "player_birthdate",
                    "competition_name",
                    "competition_id",
                    "season_name",
                    "season_id",
                    "team_name",
                }
            }
            person["records"].append({"kind": kind, "source_file": path.name, "values": metrics})
    write_json(
        root / "data/processed/v12/metadata/physical.json",
        sorted(people.values(), key=lambda p: p["name"]),
        compact=True,
    )
    write_json(
        root / "artifacts/v12/skillcorner-quality.json",
        {
            "provider_identities": len({p["provider_player_id"] for p in people.values()}),
            "player_seasons": len(people),
            "source_rows": counts,
            "league": "Australian A-League",
            "season": "2024/2025",
            "not_european_recruitment": True,
            "units": "Retain original field names and records: average-match physical minutes are NOT summed as season minutes; OBR p30tip is per 30 possession minutes.",
        },
    )
    print(f"SkillCorner specialist profiles: {len(people)}; source rows {counts}", flush=True)
