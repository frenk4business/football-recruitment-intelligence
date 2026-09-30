"""Bounded season retrieval and match-partitioned canonical storage (all local)."""

import json
import re
import shutil
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import polars as pl
import yaml

from football_intelligence.data.adapters.statsbomb import StatsBombAdapter
from football_intelligence.data.fetch import digest
from football_intelligence.data.schema import TABLES, frame_from_records
from football_intelligence.data.validation import validate

COHORT = "wsl_2023_24"


def settings(root: Path) -> dict:
    return yaml.safe_load((root / "config/cohorts.yaml").read_text())


def config(root: Path, name: str = COHORT) -> dict:
    cfg = settings(root)["cohorts"][name]
    if not re.fullmatch(r"[0-9a-f]{40}", cfg["revision"]):
        raise ValueError("Cohort requires a full pinned commit")
    return cfg


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def retrieve(root: Path, name: str = COHORT, max_matches: int | None = None) -> dict:
    cfg = config(root, name)
    directory = root / "data/raw/cohorts" / name / cfg["revision"]
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = root / "config" / f"{name}.sources.json"
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else {}
    if lock and lock["revision"] != cfg["revision"]:
        raise ValueError("Source lock differs from configured revision")
    expected = {r["path"]: r for r in lock.get("files", [])}
    cache_manifest = directory / "manifest.json"
    previous = json.loads(cache_manifest.read_text()) if cache_manifest.exists() else {}
    cached = {r["path"]: r for r in previous.get("files", [])}
    requests = 0
    with httpx.Client(timeout=60, follow_redirects=True) as client:

        def get(path: str) -> dict:
            nonlocal requests
            target = directory / path
            sidecar = target.with_suffix(".sha.json")
            record = (
                expected.get(path)
                or cached.get(path)
                or (json.loads(sidecar.read_text()) if sidecar.exists() else None)
            )
            if target.exists() and record:
                if digest(target.read_bytes()) != record["sha256"]:
                    raise ValueError(f"Cache checksum mismatch: {path}")
                return record
            url = f"https://raw.githubusercontent.com/{cfg['repository']}/{cfg['revision']}/{path}"
            for attempt in range(4):
                try:
                    requests += 1
                    with client.stream("GET", url) as response:
                        response.raise_for_status()
                        payload = bytearray()
                        for chunk in response.iter_bytes():
                            payload.extend(chunk)
                            if len(payload) > 25_000_000:
                                raise ValueError("Source file exceeds 25 MB ceiling")
                    json.loads(payload)
                    break
                except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code not in (
                        429,
                        500,
                        502,
                        503,
                        504,
                    ):
                        raise
                    if attempt == 3:
                        raise
                    time.sleep(2**attempt)
            sha = digest(payload)
            if path in expected and expected[path]["sha256"] != sha:
                raise ValueError(f"Pinned checksum mismatch: {path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_suffix(".tmp")
            temp.write_bytes(payload)
            temp.replace(target)
            record = dict(path=path, url=url, sha256=sha, bytes=len(payload))
            write(sidecar, record)
            return record

        records = [
            get("data/competitions.json"),
            get(f"data/matches/{cfg['competition']}/{cfg['season']}.json"),
        ]
        matches = json.loads((directory / records[1]["path"]).read_text())
        matches = sorted(matches, key=lambda m: (m["match_date"], m["match_id"]))
        limit = max_matches or cfg.get("max_matches")
        selected = matches[:limit] if limit else matches
        paths = [
            f"data/{kind}/{m['match_id']}.json" for m in selected for kind in ("events", "lineups")
        ]
        with ThreadPoolExecutor(max_workers=3) as pool:
            for i, record in enumerate(pool.map(get, paths), 1):
                records.append(record)
                if i % 20 == 0 or i == len(paths):
                    print(f"Source files verified: {i}/{len(paths)}", flush=True)
    manifest = dict(
        cohort=name,
        revision=cfg["revision"],
        competition=cfg["competition"],
        season=cfg["season"],
        complete=len(selected) == len(matches),
        match_ids=[m["match_id"] for m in selected],
        files=sorted(records, key=lambda r: r["path"]),
    )
    write(cache_manifest, manifest)
    if not lock and manifest["complete"]:
        write(lock_path, manifest)
    print(f"Cohort cache: {len(records)} files; {requests} network requests", flush=True)
    return manifest


def source_dir(root: Path, name: str = COHORT) -> Path:
    return root / "data/raw/cohorts" / name / config(root, name)["revision"]


def discover(root: Path, name: str = COHORT) -> list[dict]:
    directory = source_dir(root, name)
    path = directory / "data/competitions.json"
    if not path.exists():
        retrieve(root, name, 1)
    return json.loads(path.read_text())


def build_cohort(root: Path, name: str = COHORT, max_matches: int | None = None) -> dict:
    manifest = retrieve(root, name, max_matches)
    raw_dir = source_dir(root, name)
    cfg = config(root, name)
    comp = next(
        c
        for c in json.loads((raw_dir / "data/competitions.json").read_text())
        if c["competition_id"] == cfg["competition"] and c["season_id"] == cfg["season"]
    )
    match_lookup = {
        m["match_id"]: m
        for m in json.loads(
            (raw_dir / f"data/matches/{cfg['competition']}/{cfg['season']}.json").read_text()
        )
    }
    # Separate development snapshots; they cannot overwrite published full-season evidence.
    label = name if manifest["complete"] else f"{name}_dev_{len(manifest['match_ids'])}"
    target = root / "data/processed/cohorts" / label
    staging = root / "data/interim" / label
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    dimensions: dict[str, dict[str, dict]] = {
        t: {} for t in ("competitions", "seasons", "teams", "players", "matches")
    }
    counts: Counter = Counter()
    quality: Counter = Counter()
    warnings: list[dict] = []
    seen_events: set[str] = set()
    provenance = digest(json.dumps(manifest, sort_keys=True).encode())
    for i, mid in enumerate(manifest["match_ids"], 1):
        raw = dict(
            competition=comp,
            match=match_lookup[mid],
            events=json.loads((raw_dir / f"data/events/{mid}.json").read_text()),
            lineups=json.loads((raw_dir / f"data/lineups/{mid}.json").read_text()),
        )
        rows = StatsBombAdapter().normalise(raw, provenance)
        tables = {t: frame_from_records(TABLES[t], r) for t, r in rows.items()}
        ids = set(tables["events"]["id"].to_list())
        if seen_events.intersection(ids):
            raise ValueError("Duplicate event ID across cohort matches")
        seen_events.update(ids)
        report = validate(tables)
        for t, mapping in dimensions.items():
            for row in rows[t]:
                old = mapping.get(row["id"])
                if old and {k: v for k, v in old.items() if k != "observed_on"} != {
                    k: v for k, v in row.items() if k != "observed_on"
                }:
                    raise ValueError(f"Conflicting provider entity across matches: {t}/{row['id']}")
                if not old or row["observed_on"] < old["observed_on"]:
                    mapping[row["id"]] = row
        partition = staging / "matches" / str(mid)
        partition.mkdir(parents=True)
        for t in ("events", "lineups", "provider_entity_map"):
            tables[t].sort("canonical_id" if t == "provider_entity_map" else "id").write_parquet(
                partition / f"{t}.parquet", compression="zstd"
            )
        for r in rows["lineups"]:
            quality[r.get("minutes_quality", "unavailable")] += 1
        counts.update({t: len(v) for t, v in rows.items() if t not in dimensions})
        if report["warnings"]:
            warnings.append(dict(match_id=mid, warnings=report["warnings"]))
        if i % 20 == 0 or i == len(manifest["match_ids"]):
            print(f"Canonical matches validated: {i}/{len(manifest['match_ids'])}", flush=True)
    for t, mapping in dimensions.items():
        frame_from_records(TABLES[t], list(mapping.values())).sort("id").write_parquet(
            staging / f"{t}.parquet", compression="zstd"
        )
        counts[t] = len(mapping)
    report = dict(
        cohort=label,
        complete=manifest["complete"],
        competition=comp["competition_name"],
        season=comp["season_name"],
        source_revision=cfg["revision"],
        provenance_id=provenance,
        counts=dict(counts),
        minutes_quality=dict(quality),
        warnings=warnings,
        dates=sorted({match_lookup[m]["match_date"] for m in manifest["match_ids"]}),
        match_ids=manifest["match_ids"],
    )
    write(staging / "cohort.json", report)
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.with_name(target.name + ".previous")
    if backup.exists():
        shutil.rmtree(backup)
    if target.exists():
        target.rename(backup)
    staging.rename(target)
    if backup.exists():
        shutil.rmtree(backup)
    return report


def local_cohort(root: Path, name: str = COHORT) -> Path:
    return root / "data/processed/cohorts" / name


def partitions(root: Path, name: str = COHORT):
    directory = local_cohort(root, name)
    for path in sorted((directory / "matches").glob("*"), key=lambda p: int(p.name)):
        yield (
            path,
            pl.read_parquet(path / "events.parquet"),
            pl.read_parquet(path / "lineups.parquet"),
        )
