"""Single-worker Wikimedia client: bounded, rate-limited, cached and resumable."""

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from football_intelligence.profiles.cache import write_json

USER_AGENT = "FootballRecruitmentIntelligence/1.1 (offline image research; https://github.com/frenk4business/football-recruitment-intelligence)"
ALLOWED_HOSTS = {"www.wikidata.org", "commons.wikimedia.org", "upload.wikimedia.org"}


def safe_url(url: str) -> str:
    p = urlparse(url)
    if (
        p.scheme != "https"
        or p.hostname not in ALLOWED_HOSTS
        or p.username
        or p.password
        or p.port not in (None, 443)
    ):
        raise ValueError("Unapproved Wikimedia URL")
    if p.hostname == "upload.wikimedia.org" and not p.path.startswith("/wikipedia/commons/"):
        raise ValueError("Only Commons uploads are permitted")
    return url


class Wikimedia:
    def __init__(self, cache: Path, *, refresh: bool = False, interval: float = 1.0):
        self.cache = cache
        self.refresh = refresh
        self.interval = max(interval, 1.0)
        self.last_request = 0.0
        self.client = httpx.Client(
            timeout=30, headers={"User-Agent": USER_AGENT}, follow_redirects=False
        )
        self.requests = 0
        self.entity_cache: dict[str, tuple[dict, dict]] | None = None
        self.label_cache: dict[str, dict] | None = None

    def get(self, url: str, *, limit: int = 12_000_000, refresh: bool | None = None):
        safe_url(url)
        key = hashlib.sha256(url.encode()).hexdigest()
        target = self.cache / key
        sidecar = self.cache / (key + ".json")
        if (
            target.exists()
            and sidecar.exists()
            and not (self.refresh if refresh is None else refresh)
        ):
            metadata = json.loads(sidecar.read_text())
            data = target.read_bytes()
            if (
                metadata["url"] != url
                or hashlib.sha256(data).hexdigest() != metadata["sha256"]
                or len(data) > limit
            ):
                raise ValueError("Cached Wikimedia data failed integrity verification")
            return data, metadata
        for attempt in range(4):
            time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            self.requests += 1
            try:
                with self.client.stream("GET", url) as response:
                    if response.status_code in (429, 500, 502, 503, 504):
                        delay = response.headers.get("retry-after", "")
                        time.sleep(min(30, int(delay) if delay.isdigit() else 2 ** (attempt + 1)))
                        continue
                    response.raise_for_status()
                    if int(response.headers.get("content-length", "0")) > limit:
                        raise ValueError("Wikimedia response exceeds byte budget")
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > limit:
                            raise ValueError("Wikimedia response exceeds byte budget")
                        chunks.append(chunk)
                    data = b"".join(chunks)
                    mime = response.headers.get("content-type", "").split(";")[0]
                if mime == "application/json":
                    payload = json.loads(data)
                    if payload.get("error"):
                        if payload["error"].get("code") in {
                            "maxlag",
                            "cirrussearch-too-busy-error",
                            "ratelimited",
                        }:
                            delay = response.headers.get("retry-after", "")
                            time.sleep(
                                min(
                                    30,
                                    max(5, int(delay) if delay.isdigit() else 2 ** (attempt + 1)),
                                )
                            )
                            continue
                        raise ValueError(f"Wikimedia API error: {payload['error'].get('code')}")
                metadata = {
                    "url": url,
                    "mime": mime,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                    "retrieved_at": datetime.now(UTC).isoformat(),
                }
                self.cache.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix(".part")
                temporary.write_bytes(data)
                temporary.replace(target)
                write_json(sidecar, metadata)
                return data, metadata
            except httpx.TransportError:
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 1))
        raise ValueError("Wikimedia unavailable after bounded retries")

    def api(self, host: str, **params):
        # These Action API reads do not use SPARQL. Rate control follows real HTTP/API
        # throttling (including Retry-After), not the unrelated WDQS replication clock.
        url = f"https://{host}/w/api.php?" + urlencode({"format": "json", **params})
        if not self.refresh:
            previous_url = f"https://{host}/w/api.php?" + urlencode(
                {"format": "json", "maxlag": 10, **params}
            )
            previous_key = hashlib.sha256(previous_url.encode()).hexdigest()
            if (self.cache / previous_key).exists():
                url = previous_url
        data, metadata = self.get(url, limit=15_000_000)
        return json.loads(data), metadata

    def search(self, name: str):
        value, metadata = self.api(
            "www.wikidata.org",
            action="wbsearchentities",
            search=name,
            language="en",
            uselang="en",
            type="item",
            limit=5,
        )
        return value.get("search", []), metadata

    def entities(self, ids: list[str]):
        if not ids:
            return {}, {}
        if len(ids) > 50 or any(not q.startswith("Q") or not q[1:].isdigit() for q in ids):
            raise ValueError("Bounded entity IDs required")
        if self.entity_cache is None:
            self.entity_cache = {}
            for sidecar in sorted(self.cache.glob("*.json")):
                source = json.loads(sidecar.read_text())
                params = parse_qs(urlparse(source["url"]).query)
                if (
                    params.get("action") != ["wbgetentities"]
                    or params.get("props") != ["labels|aliases|claims"]
                    or params.get("languages") != ["en|nl|es|fr|pt|de|it"]
                ):
                    continue
                raw = sidecar.with_suffix("").read_bytes()
                if hashlib.sha256(raw).hexdigest() != source["sha256"]:
                    raise ValueError("Entity response cache integrity differs")
                for q, value in json.loads(raw).get("entities", {}).items():
                    old = self.entity_cache.get(q)
                    if not old or old[1]["retrieved_at"] < source["retrieved_at"]:
                        self.entity_cache[q] = (value, source)
        missing = sorted(set(ids) if self.refresh else set(ids) - self.entity_cache.keys())
        if missing:
            value, source = self.api(
                "www.wikidata.org",
                action="wbgetentities",
                ids="|".join(missing),
                props="labels|aliases|claims",
                languages="en|nl|es|fr|pt|de|it",
                languagefallback=1,
            )
            for q, e in value.get("entities", {}).items():
                self.entity_cache[q] = (e, source)
        entities = {q: self.entity_cache[q][0] for q in ids if q in self.entity_cache}
        sources = {q: self.entity_cache[q][1] for q in entities}
        aggregate = json.dumps(entities, sort_keys=True, ensure_ascii=False).encode()
        return entities, {
            "sha256": hashlib.sha256(aggregate).hexdigest(),
            "entity_sources": sources,
        }

    def labels(self, ids: list[str]):
        """Related clubs/countries need names, not their complete claim graphs."""
        if len(ids) > 50 or any(not q.startswith("Q") or not q[1:].isdigit() for q in ids):
            raise ValueError("Bounded entity IDs required")
        if self.label_cache is None:
            self.label_cache = {}
            dates: dict[str, str] = {}
            for sidecar in sorted(self.cache.glob("*.json")):
                source = json.loads(sidecar.read_text())
                params = parse_qs(urlparse(source["url"]).query)
                if (
                    params.get("action") != ["wbgetentities"]
                    or params.get("props") != ["labels|aliases"]
                    or params.get("languages") != ["en|nl|es|fr|pt|de|it"]
                ):
                    continue
                raw = sidecar.with_suffix("").read_bytes()
                if hashlib.sha256(raw).hexdigest() != source["sha256"]:
                    raise ValueError("Label response cache integrity differs")
                for q, value in json.loads(raw).get("entities", {}).items():
                    if source["retrieved_at"] >= dates.get(q, ""):
                        self.label_cache[q] = value
                        dates[q] = source["retrieved_at"]
            # Previously cached full entities provide the same label evidence.
            for q, (value, source) in (self.entity_cache or {}).items():
                if source["retrieved_at"] >= dates.get(q, ""):
                    self.label_cache[q] = value
                    dates[q] = source["retrieved_at"]
        missing = sorted(set(ids) if self.refresh else set(ids) - self.label_cache.keys())
        if missing:
            value, _ = self.api(
                "www.wikidata.org",
                action="wbgetentities",
                ids="|".join(missing),
                props="labels|aliases",
                languages="en|nl|es|fr|pt|de|it",
                languagefallback=1,
            )
            self.label_cache.update(value.get("entities", {}))
        return {q: self.label_cache[q] for q in ids if q in self.label_cache}

    def commons(self, title: str):
        value, metadata = self.api(
            "commons.wikimedia.org",
            action="query",
            prop="imageinfo",
            titles="File:" + title.removeprefix("File:"),
            iiprop="url|size|mime|sha1|extmetadata",
            iiextmetadatalanguage="en",
            redirects=1,
        )
        pages = list(value.get("query", {}).get("pages", {}).values())
        if len(pages) != 1 or not pages[0].get("imageinfo"):
            raise ValueError("Commons file unavailable")
        return pages[0], metadata
