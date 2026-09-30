"""Bounded official-source discovery; provider payloads remain in ignored storage."""

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from football_intelligence.dna.cohort import write


class SourceCache:
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(timeout=90, follow_redirects=True)
        self.expected = {}
        for ancestor in directory.parents:
            lock = ancestor / "config/phase3.sources.json"
            if lock.exists():
                prefix = ancestor / "data/raw/phase3"
                for record in json.loads(lock.read_text())["files"]:
                    self.expected[str(prefix / record["provider"] / record["path"])] = record[
                        "sha256"
                    ]
                break

    def get(self, relative: str, url: str, limit: int = 30_000_000) -> bytes:
        path = self.directory / relative
        sidecar = path.with_suffix(path.suffix + ".sha.json")
        if path.exists() and sidecar.exists():
            payload = path.read_bytes()
            record = json.loads(sidecar.read_text())
            if (
                record["url"] != url
                or hashlib.sha256(payload).hexdigest() != record["sha256"]
                or record["sha256"] != self.expected.get(str(path), record["sha256"])
            ):
                raise ValueError(f"Source cache mismatch: {relative}")
            return payload
        for attempt in range(5):
            try:
                with self.client.stream("GET", url) as response:
                    response.raise_for_status()
                    payload = bytearray()
                    for chunk in response.iter_bytes():
                        payload.extend(chunk)
                        if len(payload) > limit:
                            raise ValueError(f"Source exceeds size bound: {relative}")
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
                if attempt == 4:
                    raise
                time.sleep(2**attempt)
        if (
            str(path) in self.expected
            and hashlib.sha256(payload).hexdigest() != self.expected[str(path)]
        ):
            raise ValueError(f"Pinned source checksum mismatch: {relative}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.with_suffix(path.suffix + ".tmp").write_bytes(payload)
        path.with_suffix(path.suffix + ".tmp").replace(path)
        write(
            sidecar, dict(url=url, sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))
        )
        return bytes(payload)

    def json(self, relative: str, url: str):
        return json.loads(self.get(relative, url))


def catalogue(root: Path, revision: str, lineups: bool = False) -> dict:
    cache = SourceCache(root / "data/raw/phase3/statsbomb" / revision)
    base = f"https://raw.githubusercontent.com/statsbomb/open-data/{revision}/"
    competitions = cache.json("data/competitions.json", base + "data/competitions.json")
    cache.get("LICENSE.pdf", base + "LICENSE.pdf")

    def season(c):
        path = f"data/matches/{c['competition_id']}/{c['season_id']}.json"
        matches = cache.json(path, base + path)
        teams = sorted(
            {m[side][side + "_id"] for m in matches for side in ("home_team", "away_team")}
        )
        return dict(
            **c,
            matches=len(matches),
            teams=len(teams),
            first_date=min(m["match_date"] for m in matches),
            last_date=max(m["match_date"] for m in matches),
            match_ids=[m["match_id"] for m in matches],
        )

    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(season, competitions))
    mids = sorted({m for r in rows for m in r["match_ids"]})
    print(f"Catalogue: {len(rows)} competition-seasons; {len(mids)} unique matches", flush=True)
    if lineups:

        def fetch(mid):
            path = f"data/lineups/{mid}.json"
            return cache.json(path, base + path)

        with ThreadPoolExecutor(max_workers=3) as pool:
            for i, _ in enumerate(pool.map(fetch, mids), 1):
                if i % 100 == 0 or i == len(mids):
                    print(f"Lineups verified: {i}/{len(mids)}", flush=True)
    report = dict(
        provider="statsbomb",
        revision=revision,
        competition_seasons=rows,
        matches=len(mids),
        lineup_audit_complete=lineups,
    )
    write(root / "artifacts/phase3/source_catalogue.json", report)
    return report
