"""Measure the static route bootstrap and a single lazy player payload."""

import gzip
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

from football_intelligence.dna.cohort import write


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources: set[str] = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.sources.add(values["src"])


def size(path: Path):
    data = path.read_bytes()
    return dict(bytes=len(data), gzip_bytes=len(gzip.compress(data, mtime=0)))


def measure(root: Path):
    output = root / "apps/web/out"
    index = json.loads((output / "data/phase3/index.json").read_text())
    default = next(p for p in index["players"] if p["supported_sources"])
    pages = {}
    for route in ["translation", "nl/translation"]:
        path = output / route / "index.html"
        parser = Scripts()
        parser.feed(path.read_text())
        js = {name: size(output / unquote(name).lstrip("/")) for name in sorted(parser.sources)}
        pages[route] = dict(
            html=size(path),
            initial_javascript_files=len(js),
            initial_javascript_bytes=sum(v["bytes"] for v in js.values()),
            initial_javascript_gzip_bytes=sum(v["gzip_bytes"] for v in js.values()),
            scripts=js,
        )
    result = dict(
        routes=pages,
        default_player=default["name"],
        default_lazy_player=size(output / "data/phase3/players" / f"{default['player_id']}.json"),
        index=size(output / "data/phase3/index.json"),
        note="Static bootstrap script references; browser prefetch, HTTP headers and CDN compression can change transferred totals. One player detail is fetched on initial interaction load; no posterior samples.",
    )
    write(root / "artifacts/phase3/payload.json", result)
    return result


if __name__ == "__main__":
    print(json.dumps(measure(Path.cwd()), indent=2))
