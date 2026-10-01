"""Bounded, resumable official-source cache with upstream and local checksums."""

import hashlib
import json
import shutil
import time
from pathlib import Path

import httpx


def checksum(path: Path, algorithm: str = "sha256") -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def write_json(path: Path, value, *, compact: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":") if compact else None,
                      indent=None if compact else 2) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text)
    temporary.replace(path)


class Cache:
    def __init__(self, root: Path):
        self.root = root
        self.client = httpx.Client(timeout=120, follow_redirects=True)

    def get(self, relative: str, url: str, *, sha256: str | None = None,
            md5: str | None = None, limit: int = 30_000_000,
            seed: Path | None = None) -> Path:
        path = self.root / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("Unsafe cache path")
        sidecar = path.with_suffix(path.suffix + ".sha.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        expected = sha256
        if path.exists():
            record = json.loads(sidecar.read_text()) if sidecar.exists() else {}
            if record.get("url") != url:
                raise ValueError(f"Unverifiable cached source: {relative}")
            expected = sha256 or record["sha256"]
        elif seed and seed.exists() and (sha256 or md5):
            if ((not sha256 or checksum(seed) == sha256)
                    and (not md5 or checksum(seed, "md5") == md5)):
                shutil.copyfile(seed, path)
        if not path.exists():
            partial = path.with_suffix(path.suffix + ".part")
            for attempt in range(5):
                try:
                    offset = partial.stat().st_size if partial.exists() else 0
                    headers = {"Range": f"bytes={offset}-"} if offset else {}
                    with self.client.stream("GET", url, headers=headers) as response:
                        if response.status_code == 416 and offset:
                            partial.unlink()
                            continue
                        response.raise_for_status()
                        resume = response.status_code == 206 and offset > 0
                        if resume and not response.headers.get("content-range", "").startswith(f"bytes {offset}-"):
                            raise ValueError("Invalid resume range")
                        total = offset if resume else 0
                        with partial.open("ab" if resume else "wb") as stream:
                            for chunk in response.iter_bytes():
                                total += len(chunk)
                                if total > limit:
                                    raise ValueError(f"Source size bound exceeded: {relative}")
                                stream.write(chunk)
                    partial.replace(path)
                    break
                except (httpx.TransportError, httpx.HTTPStatusError):
                    if attempt == 4:
                        raise
                    time.sleep(min(2**attempt, 8))
        if not path.exists() or path.stat().st_size > limit:
            raise ValueError(f"Missing/oversized source: {relative}")
        digest = checksum(path)
        if expected and digest != expected:
            raise ValueError(f"Source SHA256 mismatch: {relative}")
        if md5 and checksum(path, "md5") != md5:
            raise ValueError(f"Upstream MD5 mismatch: {relative}")
        write_json(sidecar, dict(url=url, sha256=digest, bytes=path.stat().st_size,
                                upstream_md5=md5))
        return path

    def json(self, relative: str, url: str, **kwargs):
        return json.loads(self.get(relative, url, **kwargs).read_text())
