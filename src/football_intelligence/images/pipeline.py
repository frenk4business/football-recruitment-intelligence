"""Additive offline enrichment. Core builds only validate already approved static output."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

from PIL import __version__ as pillow_version
from PIL import features

from football_intelligence.data.schema import canonical_id
from football_intelligence.images.assets import MAX_BYTES, MAX_PIXELS, digest, licence, thumbnail
from football_intelligence.images.client import Wikimedia, safe_url
from football_intelligence.images.identity import evaluate, identities, values
from football_intelligence.profiles.cache import write_json

VERSION = "player-images-v1"
BUDGET = 4_000_000
PROCESSING = f"thumbnail-v1 / Pillow {pillow_version} / libwebp {features.version('webp')} / WebP quality 82 method 6 / 256 square / no crop"


def overrides(root: Path, people: list[dict]) -> dict:
    raw = json.loads((root / "config/player-images/overrides.json").read_text())
    if raw.get("version") != 1 or set(raw) != {"version", "players"}:
        raise ValueError("Invalid image override document")
    valid = {p["id"] for p in people}
    for key, value in raw["players"].items():
        if (
            key not in valid
            or value.get("status") not in {"verified", "excluded"}
            or not value.get("reason")
        ):
            raise ValueError(f"Invalid provider-scoped override: {key}")
        if value["status"] == "verified":
            if (
                not re.fullmatch(r"Q[1-9][0-9]*", value.get("wikidata_id", ""))
                or not value.get("reviewer")
                or not value.get("reviewed_at")
                or len(value.get("evidence_urls", [])) < 2
            ):
                raise ValueError(f"Incomplete manual identity evidence: {key}")
            if len({urlparse(url).hostname for url in value["evidence_urls"]}) < 2:
                raise ValueError("Manual verification requires independent source domains")
            for url in value["evidence_urls"]:
                if urlparse(url).scheme != "https":
                    raise ValueError("Manual evidence URLs must use HTTPS")
    return raw["players"]


def enrich(root: Path, *, refresh_metadata: bool = False, refresh_player: str | None = None):
    if pillow_version != "12.3.0":
        raise ValueError("Use the pinned Pillow decoder via uv sync --frozen")
    people = identities(root)
    manual = overrides(root, people)
    if refresh_player and refresh_player not in {p["id"] for p in people}:
        raise ValueError("Unknown provider identity")
    output = root / "artifacts/player-images"
    cache_root = root / "data/raw/player-images"
    client = Wikimedia(cache_root / "http", refresh=refresh_metadata)
    searches: dict[str, list] = {}
    all_entities, entity_sources = {}, {}
    errors = {}
    # Resume at the HTTP-cache level, with every cached byte rehashed before use.
    for n, person in enumerate(people, 1):
        key = person["id"]
        if manual.get(key, {}).get("status") == "excluded":
            searches[key] = []
            continue
        client.refresh = refresh_metadata or key == refresh_player
        try:
            if manual.get(key, {}).get("wikidata_id"):
                searches[key] = [{"id": manual[key]["wikidata_id"]}]
            else:
                matches, _ = client.search(" ".join(person["names"][0].split()))
                if not matches and len(person["names"]) > 1:
                    matches, _ = client.search(" ".join(person["names"][1].split()))
                searches[key] = matches
        except Exception as error:
            errors[key] = f"search: {type(error).__name__}: {error}"
            searches[key] = []
        if n % 100 == 0:
            print(f"Identity discovery {n}/{len(people)}; errors {len(errors)}", flush=True)
        if len(errors) >= 10 and not searches.get(key):
            # Do not hammer an unavailable service. Preserve current published output.
            write_json(output / "run-error.json", {"stage": "search", "errors": errors})
            raise ValueError("Wikimedia unavailable; previous publication retained; resume later")
    if errors:
        write_json(output / "run-error.json", {"stage": "search", "errors": errors})
        raise ValueError("Identity lookup failed; previous publication retained; resume later")
    qids = sorted({m["id"] for matches in searches.values() for m in matches})
    client.refresh = refresh_metadata
    for start in range(0, len(qids), 20):
        batch = qids[start : start + 20]
        value, source = client.entities(batch)
        all_entities.update(value)
        entity_sources.update({q: source.get("entity_sources", {}).get(q, source) for q in value})
    if refresh_player:
        qs = [m["id"] for m in searches[refresh_player]]
        client.refresh = True
        value, source = client.entities(qs)
        all_entities.update(value)
        entity_sources.update({q: source.get("entity_sources", {}).get(q, source) for q in value})
        client.refresh = refresh_metadata
    related_qids = sorted(
        {
            v["id"]
            for entity in all_entities.values()
            for prop in ("P27", "P54")
            for v in values(entity, prop)
            if isinstance(v, dict) and "id" in v
        }
    )
    related = {}
    for start in range(0, len(related_qids), 20):
        related.update(client.labels(related_qids[start : start + 20]))
        if start % 400 == 0:
            print(f"Related labels {start}/{len(related_qids)}", flush=True)
    records: list[dict] = []
    assets: dict[str, dict] = {}
    mapping: dict[str, dict] = {}
    legacy: dict[str, str] = {}
    previous_file = output / "manifest.json"
    previous_document = json.loads(previous_file.read_text()) if previous_file.exists() else {}
    previous = (
        previous_document.get("assets", {})
        if previous_document.get("processing") == PROCESSING
        else {}
    )
    destination = output / "assets"
    destination.mkdir(parents=True, exist_ok=True)
    staged = cache_root / "derived"
    staged.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    for n, person in enumerate(people, 1):
        if n > 1 and (n - 1) % 100 == 0:
            print(
                f"Images {n - 1}/{len(people)}; {len(assets)} unique assets, {total_bytes} bytes",
                flush=True,
            )
            write_json(cache_root / "progress.json", records)
        key = person["id"]
        candidates = [
            all_entities[m["id"]]
            for m in searches[key]
            if m["id"] in all_entities and "missing" not in all_entities[m["id"]]
        ]
        match = evaluate(person, candidates, related, manual.get(key))
        record = {
            "identity": key,
            "name": person["names"][0],
            "profiles": person["profiles"],
            "contexts": person["contexts"],
            "teams": person["teams"],
            "dob": person["dob"],
            "nationalities": person["nationalities"],
            "source_files": person["source_files"],
            "wikidata_metadata_sha256": {
                c["id"]: entity_sources[c["id"]]["sha256"] for c in candidates
            },
            "match": match,
            "common_name_review": person.get("common_name_review", False),
            "image_status": "not_verified",
        }
        if match["status"] == "verified":
            qid = match["qid"]
            images = values(all_entities[qid], "P18")
            record["image_status"] = "no_image"
            if images:
                if total_bytes > BUDGET - 40_000:
                    # Leave room for a maximum-sized thumbnail. Do not download
                    # more originals when this run cannot safely publish them.
                    record["image_status"] = "deferred_size_budget"
                    record["reason"] = "identity_verified_rights_and_download_deferred_by_budget"
                    records.append(record)
                    continue
                # First non-deprecated P18 only; a poor composition can be excluded manually.
                title = images[0]
                client.refresh = refresh_metadata or key == refresh_player
                try:
                    page, commons_source = client.commons(title)
                    info = page["imageinfo"][0]
                    record["commons_filename"] = page["title"]
                    record["license_name"] = (
                        info.get("extmetadata", {}).get("LicenseShortName", {}).get("value")
                    )
                    try:
                        rights = licence(info)
                    except ValueError as error:
                        record.update(image_status="rejected_licence", error=str(error))
                        records.append(record)
                        continue
                    if (
                        info["mime"] not in {"image/jpeg", "image/png"}
                        or info["size"] > MAX_BYTES
                        or info["width"] * info["height"] > MAX_PIXELS
                    ):
                        raise ValueError("unsupported_or_oversized_source")
                    url = safe_url(info["url"])
                    if urlparse(url).hostname != "upload.wikimedia.org":
                        raise ValueError("Original must be a Commons upload")
                    raw, source = client.get(url, refresh=False)
                    # Commons exposes SHA1 for the original file; compare before conversion.
                    import hashlib

                    if hashlib.sha1(raw).hexdigest() != info.get("sha1"):
                        raw, source = client.get(url, refresh=True)
                        if hashlib.sha1(raw).hexdigest() != info.get("sha1"):
                            raise ValueError("Commons original checksum differs")
                    reused = next(
                        (
                            a
                            for a in previous.values()
                            if a["source_hash"] == digest(raw)
                            and a["commons_metadata_sha256"] == commons_source["sha256"]
                        ),
                        None,
                    )
                    prior = destination / (reused["sha256"] + ".webp") if reused else None
                    if (
                        reused
                        and prior
                        and prior.exists()
                        and digest(prior.read_bytes()) == reused["sha256"]
                    ):
                        encoded = prior.read_bytes()
                    else:
                        encoded = thumbnail(raw, source["mime"], page["title"])
                    hashed = digest(encoded)
                    path = f"players/images/{hashed}.webp"
                    if hashed in assets and (
                        assets[hashed]["source_hash"] != digest(raw)
                        or assets[hashed]["commons_metadata_sha256"] != commons_source["sha256"]
                    ):
                        record.update(
                            image_status="source_collision_requires_review",
                            error="Identical derivative has different source/rights provenance",
                        )
                        records.append(record)
                        continue
                    if hashed not in assets and total_bytes + len(encoded) > BUDGET:
                        record["image_status"] = "deferred_size_budget"
                    else:
                        if hashed not in assets:
                            (staged / f"{hashed}.webp").write_bytes(encoded)
                            assets[hashed] = {
                                "path": path,
                                "sha256": hashed,
                                "bytes": len(encoded),
                                "width": 256,
                                "height": 256,
                                "source": "Wikimedia Commons",
                                "commons_filename": page["title"],
                                "commons_page_url": info["descriptionurl"],
                                "original_image_url": url,
                                "source_hash": digest(raw),
                                "source_sha1": info["sha1"],
                                "source_bytes": len(raw),
                                "source_width": info["width"],
                                "source_height": info["height"],
                                "source_mime": info["mime"],
                                "retrieved_at": commons_source["retrieved_at"],
                                "commons_metadata_sha256": commons_source["sha256"],
                                "licence_metadata": info["extmetadata"],
                                **rights,
                            }
                            total_bytes += len(encoded)
                        mapping[key] = {
                            "asset": hashed,
                            "wikidata_id": qid,
                            "wikidata_url": f"https://www.wikidata.org/wiki/{qid}",
                            "wikidata_metadata_sha256": entity_sources[qid]["sha256"],
                            "wikidata_image_title": title,
                            "match_status": "verified",
                            "match_method": match["method"],
                            "name": person["names"][0],
                            "profiles": person["profiles"],
                            "source_files": person["source_files"],
                        }
                        legacy[
                            str(
                                canonical_id(
                                    person["provider"], "players", person["provider_player_id"]
                                )
                            )
                        ] = key
                        record.update(image_status="published", asset=hashed)
                except Exception as error:
                    record.update(image_status="error", error=f"{type(error).__name__}: {error}")
        records.append(record)
    manifest = {
        "version": VERSION,
        "processing": PROCESSING,
        "assets": assets,
        "identities": mapping,
        "legacy": legacy,
    }
    # Network/decode work never modifies the currently approved asset directory.
    # Promote only after the complete batch has produced its reviewable result.
    for hashed in assets:
        target = destination / f"{hashed}.webp"
        if not target.exists() or digest(target.read_bytes()) != hashed:
            target.write_bytes((staged / f"{hashed}.webp").read_bytes())
    write_json(output / "manifest.json", manifest)
    write_json(output / "review.json", records, compact=True)
    # Remove only previously generated assets no longer referenced after overrides/refresh.
    for file in destination.glob("*.webp"):
        if file.stem not in assets:
            file.unlink()
    statuses = Counter(r["match"]["status"] for r in records)
    images = Counter(r["image_status"] for r in records)
    groups: dict[str, Counter] = defaultdict(Counter)
    for r in records:
        for group in {r["identity"].split(":")[0], *(c["id"] for c in r["contexts"])}:
            groups[group][r["match"]["status"]] += 1
            groups[group]["images_" + r["image_status"]] += 1
    report = {
        "version": VERSION,
        "identities_processed": len(records),
        "profiles": sum(len(p["profiles"]) for p in people),
        "match_status": dict(statuses),
        "image_status": dict(images),
        "published_assets": len(assets),
        "published_identities": len(mapping),
        "published_bytes": total_bytes,
        "licences": dict(Counter(a["license_id"] for a in assets.values())),
        "rejected_licences": dict(
            Counter(
                r.get("license_name") or "missing"
                for r in records
                if r["image_status"] == "rejected_licence"
            )
        ),
        "groups": {k: dict(v) for k, v in sorted(groups.items())},
        "source_index_sha256": digest((root / "artifacts/v11/public/index.json").read_bytes()),
        "overrides_sha256": digest((root / "config/player-images/overrides.json").read_bytes()),
    }
    write_json(output / "coverage.json", report)
    write_json(cache_root / "last-run.json", {"requests_this_run": client.requests})
    return report
