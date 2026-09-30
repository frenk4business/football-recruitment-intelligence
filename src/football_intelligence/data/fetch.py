"""Pinned public retrieval with bounded reads, checksummed cache and atomic writes."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from football_intelligence import __version__


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_config(root: Path) -> dict:
    return json.loads((root / "config/sample.json").read_text())


def fetch(root: Path, provider: str) -> dict:
    cfg = read_config(root)[provider]
    directory = root / "data/raw" / provider
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    files = []
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for key, source_path in cfg["files"].items():
            tracking = key == "tracking"
            host = "media.githubusercontent.com/media" if tracking else "raw.githubusercontent.com"
            url = f"https://{host}/{cfg['repository']}/{cfg['revision']}/{source_path}"
            target = directory / (key + (".jsonl" if tracking else ".json"))
            selection = (
                {"start_frame": cfg["start_frame"], "stop_frame": cfg["stop_frame"]}
                if tracking
                else None
            )
            old = next(
                (
                    f
                    for f in previous.get("files", [])
                    if f["key"] == key and f["url"] == url and f["selection"] == selection
                ),
                None,
            )
            if target.exists() and old:
                payload = target.read_bytes()
                if digest(payload) != old["sha256"]:
                    raise ValueError(
                        f"Cache checksum mismatch: {target}; remove this cache file and retry"
                    )
                record = old
            else:
                with client.stream("GET", url) as response:
                    response.raise_for_status()
                    if tracking:
                        lines = []
                        consumed = 0
                        for line in response.iter_lines():
                            consumed += len(line)
                            if consumed > 100_000_000:
                                raise ValueError("Tracking prefix exceeds 100 MB limit")
                            row = json.loads(line)
                            if row["frame"] >= cfg["stop_frame"]:
                                break
                            if row["frame"] >= cfg["start_frame"]:
                                lines.append(line)
                        payload = ("\n".join(lines) + "\n").encode()
                        if len(lines) != cfg["stop_frame"] - cfg["start_frame"]:
                            raise ValueError("Incomplete tracking sample")
                    else:
                        chunks = []
                        size = 0
                        for chunk in response.iter_bytes():
                            size += len(chunk)
                            if size > 20_000_000:
                                raise ValueError("JSON input exceeds 20 MB limit")
                            chunks.append(chunk)
                        payload = b"".join(chunks)
                        json.loads(payload)
                expected = cfg.get("sha256", {}).get(key)
                if expected and expected != digest(payload):
                    raise ValueError(f"Pinned checksum mismatch: {provider}/{key}")
                temporary = target.with_suffix(".tmp")
                temporary.write_bytes(payload)
                temporary.replace(target)
                record = dict(
                    key=key,
                    url=url,
                    source_revision=cfg["revision"],
                    retrieved_at=datetime.now(UTC).isoformat(),
                    sha256=digest(payload),
                    bytes=len(payload),
                    selection=selection,
                )
            expected = cfg.get("sha256", {}).get(key)
            if expected and expected != record["sha256"]:
                raise ValueError("Cached content does not match configured source checksum")
            files.append(record)
    manifest = dict(
        provider=provider,
        license=cfg["license"],
        ingestion_version=__version__,
        transformation_version=__version__,
        files=files,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_raw(root: Path, provider: str) -> tuple[dict, dict]:
    cfg = read_config(root)[provider]
    directory = root / "data/raw" / provider
    manifest = json.loads((directory / "manifest.json").read_text())
    raw = {}
    for f in manifest["files"]:
        target = directory / (f["key"] + (".jsonl" if f["key"] == "tracking" else ".json"))
        payload = target.read_bytes()
        if digest(payload) != f["sha256"] or f["source_revision"] != cfg["revision"]:
            raise ValueError("Raw cache checksum/revision mismatch; fetch the configured version")
        if cfg.get("sha256", {}).get(f["key"], f["sha256"]) != f["sha256"]:
            raise ValueError("Raw cache differs from pinned checksum")
        raw[f["key"]] = (
            [json.loads(line) for line in payload.splitlines()]
            if f["key"] == "tracking"
            else json.loads(payload)
        )
    if provider == "statsbomb":
        raw["match"] = next(m for m in raw["matches"] if m["match_id"] == cfg["match_id"])
        raw["competition"] = next(
            c
            for c in raw["competitions"]
            if c["competition_id"] == cfg["competition_id"] and c["season_id"] == cfg["season_id"]
        )
    else:
        raw["tracking"] = [
            f for f in raw["tracking"] if (f["frame"] - cfg["start_frame"]) % cfg["stride"] == 0
        ]
    return raw, manifest
