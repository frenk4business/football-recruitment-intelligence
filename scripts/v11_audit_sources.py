"""Explicit online source audit. Metadata only; never downloads event archives."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import httpx

from football_intelligence.profiles.cache import Cache, checksum, write_json

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = [7770599, 7770422, 7765196, 7765310, 7765316, 11743818, 11743836]


def main():
    cache = Cache(ROOT / "data/raw/v11/audit")
    with httpx.Client(timeout=90, follow_redirects=True) as client:
        response = client.get("https://api.github.com/repos/hudl/open-data/commits/master")
        response.raise_for_status()
        revision = response.json()["sha"]
        articles = []
        for article_id in ARTICLES:
            response = client.get(f"https://api.figshare.com/v2/articles/{article_id}")
            response.raise_for_status()
            article = response.json()
            articles.append(
                {
                    k: article[k]
                    for k in (
                        "id",
                        "title",
                        "version",
                        "doi",
                        "license",
                        "url_public_html",
                        "files",
                        "description",
                    )
                }
            )
            write_json(cache.root / f"figshare-{article_id}.json", article)
    base = f"https://raw.githubusercontent.com/hudl/open-data/{revision}/"
    comps = cache.json(
        f"statsbomb/{revision}/data/competitions.json", base + "data/competitions.json"
    )
    license_path = cache.get(f"statsbomb/{revision}/LICENSE.pdf", base + "LICENSE.pdf")
    cache.get(f"statsbomb/{revision}/README.md", base + "README.md")

    def audit(c):
        relative = f"data/matches/{c['competition_id']}/{c['season_id']}.json"
        matches = cache.json(f"statsbomb/{revision}/{relative}", base + relative)
        teams = {m[s][s + "_id"] for m in matches for s in ("home_team", "away_team")}
        expected = len(teams) * (len(teams) - 1)
        return {
            **c,
            "matches": len(matches),
            "teams": len(teams),
            "first_date": min((m["match_date"] for m in matches), default=None),
            "last_date": max((m["match_date"] for m in matches), default=None),
            "double_round_robin_matches": expected,
            "coverage_status": "double_round_robin_count_candidate"
            if len(matches) == expected
            else "partial_or_non_round_robin",
            "match_ids": sorted(m["match_id"] for m in matches),
            "matches_sha256": checksum(cache.root / f"statsbomb/{revision}/{relative}"),
            "player_ids": None,
            "minutes_audit": "pending_lineup_and_event_validation",
            "event_completeness": "not_inferred_from_catalogue",
        }

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(audit, comps))
    report = {
        "audit_date": datetime.now(UTC).date().isoformat(),
        "statsbomb_revision": revision,
        "statsbomb_license_sha256": checksum(license_path),
        "statsbomb_catalogue": rows,
        "figshare_collection": "https://figshare.com/collections/Soccer_match_event_dataset/4415000/5",
        "figshare_articles": articles,
    }
    write_json(ROOT / "artifacts/v11/source-audit.json", report)
    print(
        json.dumps(
            {
                "revision": revision,
                "competition_seasons": len(rows),
                "matches": sum(c["matches"] for c in rows),
                "figshare": [
                    {
                        "id": a["id"],
                        "version": a["version"],
                        "license": a["license"],
                        "files": [
                            {k: f[k] for k in ("name", "size", "download_url", "computed_md5")}
                            for f in a["files"]
                        ],
                    }
                    for a in articles
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
