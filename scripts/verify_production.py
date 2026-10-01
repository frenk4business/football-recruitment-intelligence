"""Verify final public release identity, routes, headers and every exported file.

Read-only; never deploys, tags, sends credentials or alters live data.
"""

import argparse
import concurrent.futures
import hashlib
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

BASE = "https://football-recruitment-intelligence.onrender.com"
SECTIONS = [
    "",
    "explorer",
    "player-dna",
    "translation",
    "recruitment",
    "methodology",
    "coverage",
    "roadmap",
]


def fetch(path):
    try:
        response = urllib.request.urlopen(BASE + path, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", default="/tmp/fri-production-verification.json")
    args = parser.parse_args()
    status, _, body = fetch("/release-manifest.json")
    assert status == 200, "Missing release manifest"
    manifest = json.loads(body)
    assert manifest["git_commit"] == args.commit, "Deployed release SHA differs"
    assert manifest["version"] == Path("VERSION").read_text().strip(), "Release version differs"
    inventory = json.loads(Path("config/public-artifacts.json").read_text())["files"]
    expected = [{k: row[k] for k in ["path", "bytes", "sha256", "schema"]} for row in inventory]
    assert manifest["public_artifacts"] == expected, "Public scientific artifacts differ"
    assert (
        manifest["scientific_versions"]
        == json.loads(Path("config/scientific-lock.json").read_text())["versions"]
    )
    routes = []
    for locale in ["", "nl/"]:
        for section in SECTIONS:
            path = f"/{locale}{section}{'/' if section else ''}"
            code, headers, html = fetch(path)
            assert code == 200, path
            assert b"<h1" in html and b"<main" in html and b'rel="canonical"' in html, path
            assert b'content="noindex' not in html, path
            assert "frame-ancestors 'none'" in headers.get("content-security-policy", ""), path
            assert "unsafe-eval" not in headers["content-security-policy"], path
            assert headers.get("x-content-type-options") == "nosniff", path
            assert headers.get("referrer-policy") == "strict-origin-when-cross-origin", path
            assert "camera=()" in headers.get("permissions-policy", ""), path
            assert "max-age=" in headers.get("strict-transport-security", ""), path
            assert "max-age=0" in headers.get("cache-control", ""), path
            assert "noindex" not in headers.get("x-robots-tag", ""), path
            routes.append({"path": path, "status": code, "headers": headers})
    code, _, missing = fetch("/not-a-real-release-route/")
    assert code == 404 and b"Pagina niet gevonden" in missing, "404 recovery missing"
    code, _, robots = fetch("/robots.txt")
    assert code == 200 and b"Disallow: /\n" not in robots, "Indexing blocked"
    code, _, sitemap = fetch("/sitemap.xml")
    assert code == 200 and sitemap.count(b"<loc>") == 16, "Sitemap routes missing"

    def verify(item):
        path, metadata = item
        code, headers, content = fetch("/" + path)
        assert code == 200, f"Asset status {code}: {path}"
        assert len(content) == metadata["bytes"], f"Asset size mismatch: {path}"
        assert hashlib.sha256(content).hexdigest() == metadata["sha256"], (
            f"Asset hash mismatch: {path}"
        )
        if path.startswith("data/"):
            assert headers.get("x-robots-tag") == "noindex", path
            assert "application/json" in headers.get("content-type", ""), path
            assert "max-age=0" in headers.get("cache-control", ""), path
        if path.startswith(("_next/static/", "integrity/")):
            assert "immutable" in headers.get("cache-control", ""), path
        return len(content)

    sizes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for i, size in enumerate(executor.map(verify, manifest["build_files"].items()), 1):
            sizes.append(size)
            if i % 500 == 0:
                print(f"Verified {i} exported files", flush=True)
    report = {
        "commit": args.commit,
        "version": manifest["version"],
        "checked_at": datetime.now(UTC).isoformat(),
        "base": BASE,
        "routes": routes,
        "verified_exported_files": len(sizes),
        "verified_bytes": sum(sizes),
        "public_artifacts": len(inventory),
        "all_hashes_match": True,
        "unknown_route_status": 404,
        "passed": True,
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(f"Verified {len(routes)} routes and {len(sizes)} files at {args.commit}")


if __name__ == "__main__":
    main()
