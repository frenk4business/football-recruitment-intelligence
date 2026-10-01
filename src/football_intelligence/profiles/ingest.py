"""Incremental provider/competition/season Parquet ingestion, including explicit DQ."""

import hashlib
import io
import itertools
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from football_intelligence.data.adapters import wyscout
from football_intelligence.profiles import statsbomb
from football_intelligence.profiles.cache import checksum, write_json
from football_intelligence.profiles.features import COUNT_KEYS, NATIVE_COUNTS, counts, family
from football_intelligence.profiles.sources import Sources

EVENT_SCHEMA = pa.schema(
    [
        ("provider", pa.string()),
        ("event_id", pa.string()),
        ("match_id", pa.int64()),
        ("player_id", pa.int64()),
        ("team_id", pa.int64()),
        ("period", pa.int32()),
        ("clock_seconds", pa.float64()),
        ("provider_event_id", pa.int32()),
        ("provider_event_type", pa.string()),
        ("provider_subtype_id", pa.string()),
        ("provider_subtype", pa.string()),
        ("tags", pa.list_(pa.int32())),
        ("original_positions", pa.string()),
        ("x", pa.float64()),
        ("y", pa.float64()),
        ("end_x", pa.float64()),
        ("end_y", pa.float64()),
        ("attributes_json", pa.string()),
    ]
)
OBS_SCHEMA = pa.schema(
    [
        ("provider", pa.string()),
        ("scope", pa.string()),
        ("player_id", pa.int64()),
        ("name", pa.string()),
        ("match_id", pa.int64()),
        ("date", pa.string()),
        ("team_id", pa.int64()),
        ("minutes", pa.float64()),
        ("elapsed_minutes", pa.float64()),
        ("reliable", pa.bool_()),
        ("reasons", pa.list_(pa.string())),
        ("role", pa.string()),
        ("role_family", pa.string()),
        ("role_minutes_json", pa.string()),
        ("minute_method", pa.string()),
        ("source_files", pa.list_(pa.string())),
    ]
    + [("c_" + k, pa.float64()) for k in COUNT_KEYS]
    + [("n_" + k, pa.float64()) for k in NATIVE_COUNTS]
)


def iter_json_array(stream):
    """Stream a JSON array without materialising a 190 MB source or its Python objects."""
    decoder = json.JSONDecoder()
    text = io.TextIOWrapper(stream, encoding="utf-8")
    buffer, pos, started, ended = "", 0, False, False
    separator, after_comma = False, False
    while True:
        chunk = text.read(65536)
        buffer = buffer[pos:] + chunk
        pos = 0
        while pos < len(buffer):
            if buffer[pos].isspace():
                pos += 1
                continue
            if not started:
                if buffer[pos] != "[":
                    raise ValueError("Expected a JSON event array")
                started = True
                pos += 1
                continue
            if separator and buffer[pos] == ",":
                separator, after_comma = False, True
                pos += 1
                continue
            if buffer[pos] == "]":
                if after_comma:
                    raise ValueError("Trailing source comma")
                ended = True
                pos += 1
                if buffer[pos:].strip() or text.read().strip():
                    raise ValueError("Trailing JSON source content")
                return
            if separator or buffer[pos] == ",":
                raise ValueError("Invalid source record separator")
            try:
                value, end = decoder.raw_decode(buffer, pos)
            except json.JSONDecodeError:
                if not chunk or len(buffer) - pos > 2_000_000:
                    raise ValueError("Malformed or oversized event record") from None
                break
            if not isinstance(value, dict):
                raise ValueError("Expected event object")
            yield value
            separator, after_comma = True, False
            pos = end
        if not chunk:
            if not ended:
                raise ValueError("Truncated source array")
            return


def code_hash(root: Path) -> str:
    paths = [
        root / "src/football_intelligence/profiles" / name
        for name in ("ingest.py", "statsbomb.py", "features.py")
    ]
    paths += [
        root / "src/football_intelligence/data/adapters/wyscout.py",
        root / "config/v11-expansion.json",
    ]
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def decode_name(value: str) -> str:
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m[1], 16)), value)


def observation(provider, scope, pid, name, mid, date, row, common, native, files):
    return dict(
        provider=provider,
        scope=scope,
        player_id=pid,
        name=decode_name(name),
        match_id=mid,
        date=date,
        team_id=row["team_id"],
        minutes=row["minutes"],
        elapsed_minutes=row.get("elapsed_minutes"),
        reliable=row["reliable"],
        reasons=row["reasons"],
        role=row.get("role"),
        role_family=row.get("role_family"),
        role_minutes_json=json.dumps(row.get("role_minutes", {}), sort_keys=True),
        minute_method=row["minute_method"],
        source_files=files,
        **{"c_" + k: v for k, v in common.items()},
        **{"n_" + k: v for k, v in native.items()},
    )


def processing_key(root: Path, provider: str, revision: str, mids: list[int]):
    return hashlib.sha256(
        json.dumps(
            [code_hash(root), checksum(root / "config/v11-sources.json"), provider, revision, mids]
        ).encode()
    ).hexdigest()


def valid_partition(folder: Path, key: str) -> bool:
    marker = folder / "manifest.json"
    if not marker.exists():
        return False
    manifest = json.loads(marker.read_text())
    return manifest["processing_key"] == key and all(
        (folder / p).exists() and checksum(folder / p) == h for p, h in manifest["files"].items()
    )


def save_partition(folder: Path, key: str, observations: list[dict], report: dict):
    pq.write_table(
        pa.Table.from_pylist(observations, schema=OBS_SCHEMA),
        folder / "observations.parquet",
        compression="zstd",
    )
    write_json(folder / "quality.json", report)
    write_json(
        folder / "manifest.json",
        dict(
            processing_key=key,
            files={
                p: checksum(folder / p)
                for p in ("events.parquet", "observations.parquet", "quality.json")
            },
        ),
    )


def sb_season(sources: Sources, c: dict, destination: Path, max_matches: int | None):
    cid, sid = c["competition_id"], c["season_id"]
    scope = f"statsbomb-{cid}-{sid}"
    folder = destination / f"provider=statsbomb/competition={cid}/season={sid}"
    folder.mkdir(parents=True, exist_ok=True)
    matches = json.loads(sources.sb(f"data/matches/{cid}/{sid}.json").read_text())
    matches.sort(key=lambda m: (m["match_date"], m["match_id"]))
    selected = matches[:max_matches]
    key = processing_key(
        sources.root, "statsbomb", sources.revision, [m["match_id"] for m in selected]
    )
    if valid_partition(folder, key):
        return json.loads((folder / "quality.json").read_text())
    observations: list[dict] = []
    quality: Counter[str] = Counter()
    event_types: Counter[str] = Counter()
    teams: dict[int, str] = {}
    with pq.ParquetWriter(folder / "events.parquet", EVENT_SCHEMA, compression="zstd") as writer:
        for n, match in enumerate(selected, 1):
            mid = match["match_id"]
            files = [
                f"statsbomb/{sources.revision}/data/{kind}/{mid}.json"
                for kind in ("events", "lineups")
            ]
            raw = {
                kind: json.loads(sources.sb(f"data/{kind}/{mid}.json").read_text())
                for kind in ("events", "lineups")
            }
            parsed = statsbomb.canonical(raw["events"], mid)
            writer.write_table(pa.Table.from_pylist(parsed, schema=EVENT_SCHEMA))
            quality["events"] += len(parsed)
            event_types.update(e["type"]["name"] for e in raw["events"])
            people = {p["player_id"]: p for t in raw["lineups"] for p in t["lineup"]}
            teams.update({t["team_id"]: t["team_name"] for t in raw["lineups"]})
            by_actor: dict[int, list] = defaultdict(list)
            for event in raw["events"]:
                if event.get("player") and event["period"] < 3:
                    by_actor[event["player"]["id"]].append(event)
            participation = statsbomb.minutes(raw)
            if not participation:
                quality["unreconciled_matches"] += 1
                participation = {
                    pid: dict(
                        minutes=None,
                        team_id=t["team_id"],
                        reliable=False,
                        reasons=["unreconciled_match"],
                        minute_method="unavailable",
                        participated=True,
                    )
                    for t in raw["lineups"]
                    for pid in [p["player_id"] for p in t["lineup"]]
                    if pid in by_actor
                }
            for pid, row in participation.items():
                if not row["participated"]:
                    continue
                quality["participating_rows"] += 1
                quality["reliable_rows"] += row["reliable"]
                quality.update(row["reasons"])
                row["role_family"] = family(row.get("role"))
                common = counts(
                    [
                        a
                        for event in by_actor[pid]
                        if (a := statsbomb.common_action(event)) is not None
                    ]
                )
                native = statsbomb.native_counts(
                    by_actor[pid], {e["type"]["name"] for e in raw["events"]}
                )
                name = people.get(pid, {}).get("player_name", f"Unknown provider ID {pid}")
                observations.append(
                    observation(
                        "statsbomb",
                        scope,
                        pid,
                        name,
                        mid,
                        match["match_date"],
                        row,
                        common,
                        native,
                        files,
                    )
                )
            if n % 100 == 0:
                print(f"Ingest {scope}: {n}/{len(selected)} matches", flush=True)
    report = dict(
        provider="statsbomb",
        scope=scope,
        competition_id=cid,
        season_id=sid,
        competition=c["competition_name"],
        season=c["season_name"],
        gender=c["competition_gender"],
        source_revision=sources.revision,
        matches=len(selected),
        catalogue_matches=len(matches),
        first_date=selected[0]["match_date"],
        last_date=selected[-1]["match_date"],
        teams={str(k): v for k, v in teams.items()},
        quality=dict(quality),
        event_types=dict(event_types),
        raw_player_ids=len({o["player_id"] for o in observations}),
        coverage="partial_131_of_132"
        if (cid, sid) == (37, 90)
        else "catalogue_round_robin_complete",
        position_policy="audited_tactical_roles",
    )
    save_partition(folder, key, observations, report)
    return report


def ws_season(sources: Sources, member: str, destination: Path, max_matches: int | None):
    source_dir = sources.cache.root / "wyscout"
    people = {p["wyId"]: p for p in json.loads((source_dir / "players.json").read_text())}
    teams = {p["wyId"]: p for p in json.loads((source_dir / "teams.json").read_text())}
    comps = {p["wyId"]: p for p in json.loads((source_dir / "competitions.json").read_text())}
    with zipfile.ZipFile(source_dir / "matches.zip") as archive:
        matches = json.loads(archive.read(f"matches_{member}.json"))
    matches.sort(key=lambda m: (m["dateutc"], m["wyId"]))
    cid, sid = matches[0]["competitionId"], matches[0]["seasonId"]
    scope = f"wyscout-{cid}-{sid}"
    selected = {m["wyId"]: m for m in matches[:max_matches]}
    key = processing_key(
        sources.root, "wyscout", checksum(source_dir / "events.zip"), list(selected)
    )
    folder = destination / f"provider=wyscout/competition={cid}/season={sid}"
    folder.mkdir(parents=True, exist_ok=True)
    if valid_partition(folder, key):
        return json.loads((folder / "quality.json").read_text())
    observations: list[dict] = []
    quality: Counter[str] = Counter()
    event_types: Counter[str] = Counter()
    seen_matches: set[int] = set()
    seen_events: set[str] = set()
    people_ids, team_ids = set(people), set(teams)
    with (
        zipfile.ZipFile(source_dir / "events.zip") as archive,
        pq.ParquetWriter(folder / "events.parquet", EVENT_SCHEMA, compression="zstd") as writer,
    ):
        for mid, stream in itertools.groupby(
            iter_json_array(archive.open(f"events_{member}.json")), key=lambda e: int(e["matchId"])
        ):
            if mid not in selected:
                continue
            if mid in seen_matches:
                raise ValueError(
                    "Non-contiguous Wyscout match group; do not silently split observations"
                )
            seen_matches.add(mid)
            match = selected[mid]
            parsed = [wyscout.parse_event(raw, match, people_ids, team_ids) for raw in stream]
            for event in parsed:
                if event["event_id"] in seen_events:
                    raise ValueError("Duplicate Wyscout event ID")
                seen_events.add(event["event_id"])
            writer.write_table(pa.Table.from_pylist(parsed, schema=EVENT_SCHEMA))
            quality["events"] += len(parsed)
            quality["unknown_actor_events"] += sum(not e["player_known"] for e in parsed)
            quality["anonymous_actor_events"] += sum(e["player_id"] == 0 for e in parsed)
            quality["unknown_positive_actor_events"] += sum(
                e["player_id"] > 0 and not e["player_known"] for e in parsed
            )
            event_types.update(e["provider_event_type"] for e in parsed)
            by_actor: dict[int, list] = defaultdict(list)
            for event in parsed:
                by_actor[event["player_id"]].append(event)
            participation = wyscout.minutes(match, parsed, people_ids)
            if not participation:
                quality["unreconciled_matches"] += 1
                participation = {
                    pid: dict(
                        minutes=None,
                        team_id=events[0]["team_id"],
                        reliable=False,
                        reasons=["unreconciled_match"],
                        minute_method="unavailable",
                        participated=True,
                    )
                    for pid, events in by_actor.items()
                    if pid > 0
                }
            for pid, row in participation.items():
                if not row["participated"]:
                    continue
                quality["participating_rows"] += 1
                quality["reliable_rows"] += row["reliable"]
                quality.update(row["reasons"])
                player = people.get(pid, {})
                row["role"], row["role_family"] = wyscout.role(player)
                common = counts(
                    [
                        a
                        for event in by_actor[pid]
                        if (a := wyscout.common_action(event)) is not None
                    ]
                )
                native = wyscout.native_counts(by_actor[pid])
                name = (
                    " ".join(
                        v
                        for v in [
                            player.get("firstName"),
                            player.get("middleName"),
                            player.get("lastName"),
                        ]
                        if v
                    )
                    or f"Unknown provider ID {pid}"
                )
                observations.append(
                    observation(
                        "wyscout",
                        scope,
                        pid,
                        name,
                        mid,
                        wyscout.match_date(match),
                        row,
                        common,
                        native,
                        [
                            f"wyscout/events.zip#events_{member}.json",
                            f"wyscout/matches.zip#matches_{member}.json",
                            "wyscout/players.json",
                            "wyscout/teams.json",
                        ],
                    )
                )
            if len(seen_matches) % 100 == 0:
                print(f"Ingest {scope}: {len(seen_matches)}/{len(selected)} matches", flush=True)
            if max_matches is not None and len(seen_matches) == len(selected):
                break
    if seen_matches != set(selected):
        raise ValueError("Missing Wyscout event matches")
    report = dict(
        provider="wyscout",
        scope=scope,
        competition_id=cid,
        season_id=sid,
        competition=comps[cid]["name"],
        season="2017/2018",
        gender="male",
        source_revision="figshare-4415000-v5-events-v1",
        matches=len(selected),
        catalogue_matches=len(matches),
        first_date=wyscout.match_date(matches[0]),
        last_date=wyscout.match_date(list(selected.values())[-1]),
        teams={
            str(tid): teams[tid]["name"]
            for m in selected.values()
            for tid in map(int, m["teamsData"])
        },
        quality=dict(quality),
        event_types=dict(event_types),
        raw_player_ids=len({o["player_id"] for o in observations}),
        coverage="domestic_round_robin_complete",
        position_policy="provider_broad_role_only",
    )
    save_partition(folder, key, observations, report)
    return report


def ingest(root: Path, max_matches: int | None = None):
    if max_matches is not None and max_matches < 1:
        raise ValueError("max_matches must be positive")
    sources = Sources(root)
    sources.download(max_matches)
    destination = (
        root / "data/processed/v11" / (f"development-{max_matches}" if max_matches else "full")
    )
    reports = [sb_season(sources, c, destination, max_matches) for c in sources.seasons()]
    reports += [
        ws_season(sources, c, destination, max_matches) for c in sources.config["wyscout_members"]
    ]
    write_json(destination / "coverage.json", reports)
    # Local analytical catalogue; parameterised paths, no raw data copied to the public site.
    con = duckdb.connect(str(destination / "profiles.duckdb"))
    con.read_parquet(
        str(destination / "provider=*/competition=*/season=*/observations.parquet"),
        hive_partitioning=False,
    ).create_view("provider_match_observations", replace=True)
    con.close()
    return destination
