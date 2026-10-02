"""Explicitly selected official inputs, pinned independently of the v1.1 cache."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from football_intelligence.profiles.cache import Cache, checksum, write_json


class Sources:
    def __init__(self, root: Path):
        self.root = root
        self.audit = json.loads((root / "artifacts/v12/source-audit.json").read_text())
        self.cache = Cache(root / "data/raw/v12/sources")
        self.cache.client.headers["User-Agent"] = (
            "FootballRecruitmentIntelligence/1.2 offline-data-build"
        )
        self.revision = self.audit["repositories"]["statsbomb"]["revision"]
        self.old = {
            r["path"]: r
            for r in json.loads((root / "config/v11-sources.json").read_text())["files"]
        }
        lock = root / "config/v12-sources.json"
        self.expected = (
            {r["path"]: r for r in json.loads(lock.read_text())["files"]} if lock.exists() else {}
        )

    def get(self, source: str, path: str) -> Path:
        repo = self.audit["repositories"][source]
        relative = f"{source}/{repo['revision']}/{path}"
        old = self.old.get(relative, {})
        expected = self.expected.get(relative, old).get("sha256")
        seed = self.root / "data/raw/v11/sources" / relative
        audited = self.root / "data/raw/v12/audit" / relative
        if audited.exists():
            expected = expected or checksum(audited)
            seed = audited
        return self.cache.get(
            relative,
            f"https://raw.githubusercontent.com/{repo['repository']}/{repo['revision']}/{path}",
            sha256=expected,
            seed=seed,
            limit=30_000_000,
        )

    def sb(self, path: str) -> Path:
        return self.get("statsbomb", path)

    def inventory(self, source: str) -> list[dict]:
        revision = self.audit["repositories"][source]["revision"]
        tree = json.loads(
            (self.root / "data/raw/v12/audit" / source / revision / "tree.json").read_text()
        )
        return [r for r in tree["tree"] if r["type"] == "blob"]

    def seasons(self) -> list[dict]:
        # Explicit catalogue IDs; every season stays an independent source scope.
        competitions = {2, 7, 9, 11, 12, 16, 35, 43, 55, 87, 223, 1238, 1267, 1470}
        old = {
            tuple(x)
            for x in json.loads((self.root / "config/v11-expansion.json").read_text())[
                "statsbomb_seasons"
            ]
        }
        return [
            c
            for c in self.audit["statsbomb_catalogue"]
            if c["competition_gender"] == "male"
            and c["competition_id"] in competitions
            and (c["competition_id"], c["season_id"]) not in old
            and c["events_available"] == c["lineups_available"] == c["catalogue_matches"]
        ]

    def fetch(self):
        if not (self.root / "docs/v1.2-open-data-landscape.md").exists():
            raise ValueError("Source audit must precede ingestion")
        if self.expected:
            # Clean-machine rebuild uses the committed allowlist, never a fresh source tree.
            tasks = []
            for relative in self.expected:
                source, revision, path = relative.split("/", 2)
                if revision != self.audit["repositories"][source]["revision"]:
                    raise ValueError("Pinned source revision differs from reviewed audit")
                tasks.append((source, path))
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(lambda task: self.get(*task), sorted(tasks)))
            return
        tasks = []
        for c in self.seasons():
            tasks.append(("statsbomb", f"data/matches/{c['competition_id']}/{c['season_id']}.json"))
            for mid in c["match_ids"]:
                tasks.extend(
                    ("statsbomb", f"data/{kind}/{mid}.json") for kind in ["lineups", "events"]
                )
        for source in [
            "openfootball-europe",
            "openfootball-clubs",
            "openfootball-players",
            "openfootball-json",
            "skillcorner",
        ]:
            for row in self.inventory(source):
                path = row["path"]
                include = (
                    source == "openfootball-europe"
                    and path.endswith(".txt")
                    or source == "openfootball-clubs"
                    and path.startswith("europe/")
                    and (path.endswith(".clubs.txt") or path.endswith(".stadiums.txt"))
                    or source == "openfootball-players"
                    and path.startswith("europe/")
                    and path.endswith(".players.txt")
                    or source == "openfootball-json"
                    and path.endswith(".json")
                    and "/" in path
                    and path.split("/")[0][:4].isdigit()
                    or source == "skillcorner"
                    and (
                        path.startswith("data/aggregates/")
                        and path.endswith(".csv")
                        or path == "data/matches.json"
                    )
                )
                if include:
                    tasks.append((source, path))
        tasks = sorted(set(tasks))
        # Four bounded workers; source URLs are constructed from the audited registry.
        with ThreadPoolExecutor(max_workers=4) as pool:
            for n, _ in enumerate(pool.map(lambda task: self.get(*task), tasks), 1):
                if n % 100 == 0 or n == len(tasks):
                    print(f"v1.2 verified source files: {n}/{len(tasks)}", flush=True)
        self.write_lock()

    def write_lock(self):
        rows = []
        for sidecar in sorted(self.cache.root.rglob("*.sha.json")):
            path = sidecar.with_name(sidecar.name.removesuffix(".sha.json"))
            record = json.loads(sidecar.read_text())
            if checksum(path) != record["sha256"]:
                raise ValueError(f"Source differs: {path}")
            rows.append({"path": str(path.relative_to(self.cache.root)), **record})
        write_json(
            self.root / "config/v12-sources.json",
            {
                "version": "v12-sources-v1",
                "audit_sha256": checksum(self.root / "artifacts/v12/source-audit.json"),
                "files": rows,
            },
        )
