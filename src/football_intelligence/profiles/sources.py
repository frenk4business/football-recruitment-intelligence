"""Pinned metadata, full catalogue screening and separately cached event downloads."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from football_intelligence.data.positions import position_group
from football_intelligence.profiles.cache import Cache, checksum, write_json


class Sources:
    def __init__(self, root: Path):
        self.root = root
        self.audit = json.loads((root / "artifacts/v11/source-audit.json").read_text())
        self.config = json.loads((root / "config/v11-expansion.json").read_text())
        self.revision = self.audit["statsbomb_revision"]
        self.cache = Cache(root / "data/raw/v11/sources")
        self.old = {
            (r["provider"] + "/" + r["path"]): r
            for r in json.loads((root / "config/phase3.sources.json").read_text())["files"]
        }
        lock = root / "config/v11-sources.json"
        self.expected = (
            {r["path"]: r for r in json.loads(lock.read_text())["files"]} if lock.exists() else {}
        )

    def sb(self, path: str) -> Path:
        key = f"statsbomb/{self.revision}/{path}"
        expected = self.expected.get(key, self.old.get(key, {})).get("sha256")
        seed = self.root / "data/raw/phase3" / key
        if path.startswith("data/matches/"):
            c = next(
                c
                for c in self.audit["statsbomb_catalogue"]
                if path == f"data/matches/{c['competition_id']}/{c['season_id']}.json"
            )
            expected = c["matches_sha256"]
            seed = self.root / "data/raw/v11/audit" / key
        return self.cache.get(
            key,
            f"https://raw.githubusercontent.com/hudl/open-data/{self.revision}/{path}",
            sha256=expected,
            seed=seed,
        )

    def seasons(self) -> list[dict]:
        return [
            c
            for c in self.audit["statsbomb_catalogue"]
            if [c["competition_id"], c["season_id"]] in self.config["statsbomb_seasons"]
        ]

    def wyscout(self, *, events: bool = True):
        for article in self.audit["figshare_articles"]:
            if article["license"]["name"] != "CC BY 4.0":
                raise ValueError("Unreviewed Figshare licence")
            for file in article["files"]:
                if file["name"] == "events.zip" and not events:
                    continue
                key = "wyscout/" + file["name"]
                self.cache.get(
                    key,
                    file["download_url"],
                    md5=file["computed_md5"],
                    sha256=self.expected.get(key, {}).get("sha256"),
                    limit=file["size"],
                    seed=self.root / "data/raw/phase3/wyscout/files" / file["name"],
                )

    def download(self, max_matches: int | None = None):
        if not (self.root / "docs/v1.1-data-expansion-audit.md").exists():
            raise ValueError("Source/licence audit must precede ingestion")
        self.wyscout()
        tasks: list[str] = []
        for c in self.seasons():
            matches = json.loads(
                self.sb(f"data/matches/{c['competition_id']}/{c['season_id']}.json").read_text()
            )
            matches.sort(key=lambda m: (m["match_date"], m["match_id"]))
            for m in matches[:max_matches]:
                tasks.extend(f"data/{kind}/{m['match_id']}.json" for kind in ("events", "lineups"))
        with ThreadPoolExecutor(max_workers=6) as pool:
            for n, _ in enumerate(pool.map(self.sb, tasks), 1):
                if n % 100 == 0 or n == len(tasks):
                    print(f"Verified selected StatsBomb files {n}/{len(tasks)}", flush=True)
        if max_matches is None:
            self.write_lock()

    def write_lock(self):
        records = []
        for sidecar in sorted(self.cache.root.rglob("*.sha.json")):
            record = json.loads(sidecar.read_text())
            path = sidecar.with_name(sidecar.name.removesuffix(".sha.json"))
            if checksum(path) != record["sha256"]:
                raise ValueError("Source lock checksum mismatch")
            records.append({"path": str(path.relative_to(self.cache.root)), **record})
        write_json(
            self.root / "config/v11-sources.json",
            {
                "version": "v11-sources-v1",
                "statsbomb_revision": self.revision,
                "figshare_collection_version": 5,
                "files": records,
            },
        )

    def audit_catalogue(self):
        rows = self.audit["statsbomb_catalogue"]
        mids = sorted({mid for c in rows for mid in c["match_ids"]})
        lookup = {}

        def lineups(mid):
            data = json.loads(self.sb(f"data/lineups/{mid}.json").read_text())
            players = [p for team in data for p in team["lineup"]]
            return mid, {
                "ids": {p["player_id"] for p in players},
                "rows": len(players),
                "position_rows": sum(
                    any(position_group(q.get("position")) for q in p.get("positions", []))
                    for p in players
                ),
                "interval_rows": sum(bool(p.get("positions")) for p in players),
            }

        with ThreadPoolExecutor(max_workers=6) as pool:
            for n, (mid, result) in enumerate(pool.map(lineups, mids), 1):
                lookup[mid] = result
                if n % 500 == 0:
                    print(f"Catalogue lineup audit {n}/{len(mids)}", flush=True)
        tree = self.cache.json(
            "statsbomb/tree.json",
            f"https://api.github.com/repos/hudl/open-data/git/trees/{self.revision}?recursive=1",
        )
        if tree.get("truncated"):
            raise ValueError("Truncated official file inventory")
        paths = {r["path"] for r in tree["tree"]}
        result = []
        for c in rows:
            entries = [lookup[mid] for mid in c["match_ids"]]
            total = sum(e["rows"] for e in entries)
            selected = [c["competition_id"], c["season_id"]] in self.config["statsbomb_seasons"]
            result.append(
                {
                    **c,
                    "player_ids": len(set().union(*(e["ids"] for e in entries))),
                    "lineup_rows": total,
                    "position_coverage": round(sum(e["position_rows"] for e in entries) / total, 6)
                    if total
                    else 0,
                    "interval_coverage": round(sum(e["interval_rows"] for e in entries) / total, 6)
                    if total
                    else 0,
                    "event_files_present": sum(
                        f"data/events/{mid}.json" in paths for mid in c["match_ids"]
                    ),
                    "minutes_audit": "selected_event_reconciliation_in_build"
                    if selected
                    else "lineup_intervals_only_not_reconciled",
                    "event_completeness": "file_presence_only_full_quality_validation_for_selection",
                    "selected": selected,
                }
            )
        write_json(
            self.root / "artifacts/v11/catalogue-audit.json",
            {"revision": self.revision, "competition_seasons": result},
        )
        self.write_lock()
        return result
