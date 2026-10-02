"""Fresh official-source metadata audit; no performance event downloads."""

import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from football_intelligence.profiles.cache import Cache, checksum, write_json

ROOT = Path(__file__).resolve().parents[1]
REPOS = {
    "statsbomb": ("hudl/open-data", "master"),
    "openfootball-europe": ("openfootball/europe", "master"),
    "openfootball-clubs": ("openfootball/clubs", "master"),
    "openfootball-players": ("openfootball/players", "master"),
    "openfootball-json": ("openfootball/football.json", "master"),
    "skillcorner": ("SkillCorner/opendata", "master"),
    "idsse": ("spoho-datascience/idsse-data", "main"),
    "metrica": ("metrica-sports/sample-data", "master"),
    "driblab": ("driblab/open-data", "main"),
}


def main():
    cache = Cache(ROOT / "data/raw/v12/audit")
    cache.client.headers["User-Agent"] = "FootballRecruitmentIntelligence/1.2 source-audit"
    # Optional existing gh login is used only for the official GitHub API.
    gh = shutil.which("gh")
    token = (
        subprocess.run(
            [gh, "auth", "token"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        if gh
        else ""
    )

    def api(path):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = cache.client.get("https://api.github.com/" + path, headers=headers)
        response.raise_for_status()
        return response.json()

    repos = {}
    for key, (repo, branch) in REPOS.items():
        metadata = api(f"repos/{repo}")
        branch = metadata["default_branch"]
        commit = api(f"repos/{repo}/commits/{branch}")
        revision = commit["sha"]
        tree = api(f"repos/{repo}/git/trees/{revision}?recursive=1")
        if tree.get("truncated"):
            raise ValueError(f"Incomplete inventory: {repo}")
        write_json(cache.root / key / revision / "tree.json", tree)
        files = []
        for row in tree["tree"]:
            if row["path"].lower() in {
                "readme.md",
                "license",
                "license.md",
                "license.pdf",
                "licence",
                "licence.md",
            }:
                path = cache.get(
                    f"{key}/{revision}/{row['path']}",
                    f"https://raw.githubusercontent.com/{repo}/{revision}/{row['path']}",
                )
                files.append(
                    {"path": row["path"], "sha256": checksum(path), "bytes": path.stat().st_size}
                )
        repos[key] = {
            "repository": repo,
            "revision": revision,
            "committed_at": commit["commit"]["committer"]["date"],
            "official_url": f"https://github.com/{repo}",
            "github_license": metadata.get("license"),
            "files": files,
            "inventory_files": sum(r["type"] == "blob" for r in tree["tree"]),
        }
        print(f"Audited {key}: {revision}", flush=True)
    revision = repos["statsbomb"]["revision"]
    base = f"https://raw.githubusercontent.com/hudl/open-data/{revision}/"
    competitions = cache.json(
        f"statsbomb/{revision}/data/competitions.json", base + "data/competitions.json"
    )
    tree = json.loads((cache.root / "statsbomb" / revision / "tree.json").read_text())
    paths = {r["path"] for r in tree["tree"]}

    def season(c):
        relative = f"data/matches/{c['competition_id']}/{c['season_id']}.json"
        path = cache.get(f"statsbomb/{revision}/{relative}", base + relative)
        matches = json.loads(path.read_text())
        teams = {m[side][side + "_id"] for m in matches for side in ("home_team", "away_team")}
        pairs = [(m["home_team"]["home_team_id"], m["away_team"]["away_team_id"]) for m in matches]
        # Known domestic league structures, never estimated from a tiny sample.
        expected = (
            306
            if c["competition_id"] == 9
            else 380
            if c["competition_id"] in {2, 7, 11, 12}
            else None
        )
        if c["competition_id"] in {2, 7, 11, 12} and c["season_name"].split("/")[0] < "1995":
            expected = None
        ratio = len(matches) / expected if expected else None
        balanced = len(pairs) == len(set(pairs)) == len(teams) * (len(teams) - 1)
        status = (
            "complete"
            if ratio == 1 and balanced
            else "near_complete"
            if ratio and 0.95 <= ratio < 1
            else "partial"
            if ratio and ratio >= 0.25
            else "sample"
        )
        return {
            **c,
            "catalogue_matches": len(matches),
            "metadata_matches": len({m["match_id"] for m in matches}),
            "teams": len(teams),
            "match_ids": sorted(m["match_id"] for m in matches),
            "events_available": sum(f"data/events/{m['match_id']}.json" in paths for m in matches),
            "lineups_available": sum(
                f"data/lineups/{m['match_id']}.json" in paths for m in matches
            ),
            "expected_domestic_matches": expected,
            "coverage_status": status,
            "balanced_home_away_schedule": balanced,
            "coverage_note": "Expected domestic round-robin schedule"
            if expected
            else "No full-season denominator asserted; competition-only sample",
            "matches_sha256": checksum(path),
            "first_date": min((m["match_date"] for m in matches), default=None),
            "last_date": max((m["match_date"] for m in matches), default=None),
        }

    with ThreadPoolExecutor(max_workers=4) as pool:
        catalogue = list(pool.map(season, competitions))
    articles = []
    for aid in [7770599, 7770422, 7765196, 7765310, 7765316, 11743818, 11743836]:
        response = cache.client.get(f"https://api.figshare.com/v2/articles/{aid}")
        response.raise_for_status()
        value = response.json()
        articles.append(
            {
                k: value[k]
                for k in ["id", "title", "version", "doi", "license", "files", "url_public_html"]
            }
        )
    write_json(
        ROOT / "artifacts/v12/source-audit.json",
        {
            "audited_at": datetime.now(UTC).isoformat(),
            "repositories": repos,
            "statsbomb_catalogue": catalogue,
            "figshare_articles": articles,
            "note": "Metadata audit only. File presence does not establish reliable event minutes or recruitment eligibility.",
        },
    )
    print(
        f"Catalogue audited: {len(catalogue)} competition-seasons; {sum(c['catalogue_matches'] for c in catalogue)} matches",
        flush=True,
    )


if __name__ == "__main__":
    main()
