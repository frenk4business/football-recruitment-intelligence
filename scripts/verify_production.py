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


def verify_cache(path, headers):
    immutable = path.lstrip("/").startswith(("_next/static/", "integrity/"))
    expected = {"public", "no-transform"} | (
        {"max-age=31536000", "immutable"} if immutable else {"max-age=0", "must-revalidate"}
    )
    actual = {part.strip().lower() for part in headers.get("cache-control", "").split(",")}
    assert actual == expected, f"Cache policy mismatch: {path}: {actual}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", default="/tmp/fri-production-verification.json")
    args = parser.parse_args()
    status, manifest_headers, body = fetch("/release-manifest.json")
    assert status == 200, "Missing release manifest"
    verify_cache("/release-manifest.json", manifest_headers)
    assert manifest_headers.get("x-robots-tag") == "noindex", "Manifest indexing policy differs"
    assert "application/json" in manifest_headers.get("content-type", ""), "Manifest MIME differs"
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
            verify_cache(path, headers)
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
        verify_cache(path, headers)
        if path.startswith("data/"):
            assert headers.get("x-robots-tag") == "noindex", path
            assert "application/json" in headers.get("content-type", ""), path
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
        "complete_cache_policies_match": True,
        "manifest_headers": manifest_headers,
        "passed": True,
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(f"Verified {len(routes)} routes and {len(sizes)} files at {args.commit}")


if __name__ == "__main__":
    main()
