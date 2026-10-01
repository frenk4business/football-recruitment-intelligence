"""Focused, redacted secret-pattern scan of working files and reachable Git history.

Not an exhaustive secret detector. Prints rule/path only, never matching text.
"""

import json
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "private-key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "github-token": rb"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}",
    "aws-access-id": rb"AKIA[0-9A-Z]{16}",
    "render-key": rb"rnd_[A-Za-z0-9]{24,}",
}


def findings(data: bytes, path: str) -> list[dict[str, str]]:
    if b"\0" in data[:8000]:
        return []
    return [
        {"rule": name, "path": path}
        for name, pattern in PATTERNS.items()
        if re.search(pattern, data)
    ]


def main() -> None:
    objects = subprocess.check_output(["git", "rev-list", "--objects", "--all"]).splitlines()
    paths = {}
    for item in objects:
        oid, _, path = item.partition(b" ")
        paths.setdefault(oid.decode(), path.decode())
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    output, _ = process.communicate(("\n".join(paths) + "\n").encode())
    offset = 0
    hits = []
    blobs = 0
    while offset < len(output):
        end = output.index(b"\n", offset)
        oid, kind, length = output[offset:end].split()
        offset = end + 1
        size = int(length)
        if kind == b"blob":
            blobs += 1
            hits.extend(findings(output[offset : offset + size], paths[oid.decode()]))
        offset += size + 1
    working = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
        )
        .decode()
        .split("\0")
    )
    for name in filter(None, working):
        path = Path(name)
        if path.is_file():
            hits.extend(findings(path.read_bytes(), name))
    report = {"unique_history_blobs": blobs, "findings": hits, "scope": "focused patterns only"}
    print(json.dumps(report, indent=2))
    if hits:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
