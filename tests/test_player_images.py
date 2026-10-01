"""Synthetic metadata and raster fixtures only; no test faces or network calls."""

import io
from copy import deepcopy
from pathlib import Path

import httpx
import pytest
from PIL import Image

from football_intelligence.images.assets import licence, thumbnail
from football_intelligence.images.client import Wikimedia, safe_url
from football_intelligence.images.identity import evaluate, normalize


def claim(value):
    return {"mainsnak": {"snaktype": "value", "datavalue": {"value": value}}}


def person():
    return {
        "id": "wyscout:1",
        "provider": "wyscout",
        "names": ["Éva Example"],
        "dob": "1994-05-06",
        "nationalities": ["Netherlands"],
        "teams": ["Historical FC"],
        "contexts": [{"gender": "female"}],
    }


def entity():
    return {
        "id": "Q123",
        "labels": {"en": {"value": "Éva Example"}},
        "claims": {
            "P569": [
                claim(
                    {
                        "time": "+1994-05-06T00:00:00Z",
                        "precision": 11,
                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                    }
                )
            ],
            "P106": [claim({"id": "Q937857"})],
            "P27": [claim({"id": "Q55"})],
            "P54": [claim({"id": "Q500"})],
            "P21": [claim({"id": "Q6581072"})],
        },
    }


RELATED = {
    "Q55": {"labels": {"en": {"value": "Netherlands"}}},
    "Q500": {"labels": {"en": {"value": "Different current club"}}},
}


def test_exact_name_dob_occupation_citizenship_and_historical_club_mismatch():
    result = evaluate(person(), [entity()], RELATED)
    assert result["status"] == "verified"
    assert not result["candidates"][0]["signals"]["historical_club_match"]


def test_alias_dob():
    e = entity()
    p = person()
    p["names"] = ["Éva Maria Example"]
    e["aliases"] = {"en": [{"value": "Eva Maria Example"}]}
    assert evaluate(p, [e], RELATED)["status"] == "verified"


def test_significantly_different_alias_needs_explicit_review():
    e = entity()
    e["labels"]["en"]["value"] = "Eva Different"
    e["aliases"] = {"en": [{"value": "Eva Example"}]}
    assert evaluate(person(), [e], RELATED)["status"] == "likely"


def test_conflicting_birth_dates_require_review_even_when_one_matches():
    e = entity()
    extra = deepcopy(e["claims"]["P569"][0])
    extra["mainsnak"]["datavalue"]["value"]["time"] = "+1995-05-06T00:00:00Z"
    e["claims"]["P569"].append(extra)
    assert evaluate(person(), [e], RELATED)["status"] == "ambiguous"


@pytest.mark.parametrize("field", ["dob", "nationality", "gender"])
def test_conflicting_evidence_never_auto_publishes(field):
    p = person()
    if field == "dob":
        p["dob"] = "2000-01-01"
    elif field == "nationality":
        p["nationalities"] = ["Belgium"]
    else:
        p["contexts"] = [{"gender": "male"}]
    assert evaluate(p, [entity()], RELATED)["status"] == "ambiguous"


def test_multiple_candidates_and_no_dob_require_review():
    e2 = deepcopy(entity())
    e2["id"] = "Q456"
    assert evaluate(person(), [entity(), e2], RELATED)["status"] == "ambiguous"
    p = person()
    p["dob"] = None
    assert evaluate(p, [entity()], RELATED)["status"] == "likely"
    unrelated = {"id": "Q789", "labels": {"en": {"value": "Other person"}}}
    assert evaluate(person(), [entity(), unrelated], RELATED)["status"] == "likely"


def test_no_name_only_or_club_only_verification():
    e = entity()
    del e["claims"]["P569"]
    e["claims"]["P54"] = [claim({"id": "Q500"})]
    related = {**RELATED, "Q500": {"labels": {"en": {"value": "Historical FC"}}}}
    assert evaluate(person(), [e], related)["status"] == "likely"
    e["labels"]["en"]["value"] = "Another player"
    assert evaluate(person(), [e], related)["status"] == "none"


def test_exclusion_overrides_everything_and_verified_override_requires_evidence():
    assert (
        evaluate(person(), [entity()], RELATED, {"status": "excluded", "reason": "do not use"})[
            "status"
        ]
        == "excluded"
    )
    p = person()
    p["dob"] = None
    o = {
        "status": "verified",
        "wikidata_id": "Q123",
        "reason": "independent metadata reviewed",
        "reviewer": "Test reviewer",
        "evidence_urls": ["https://example.org/source", "https://www.wikidata.org/wiki/Q123"],
    }
    assert evaluate(p, [entity()], RELATED, o)["method"] == "manual_metadata_review"
    o["evidence_urls"] = []
    with pytest.raises(ValueError, match="two independent"):
        evaluate(p, [entity()], RELATED, o)


def test_inexact_birth_precision_does_not_verify():
    e = entity()
    e["claims"]["P569"][0]["mainsnak"]["datavalue"]["value"]["precision"] = 9
    assert evaluate(person(), [e], RELATED)["status"] == "likely"
    assert normalize("  Éva–Example! ") == "eva example"


def metadata(name="CC BY-SA 4.0", url="https://creativecommons.org/licenses/by-sa/4.0/"):
    return {
        "extmetadata": {
            k: {"value": v}
            for k, v in {
                "LicenseShortName": name,
                "LicenseUrl": url,
                "Artist": '<a href="https://commons.wikimedia.org/wiki/User:Example">Example photographer</a>',
                "Credit": "Own work",
                "Copyrighted": "True",
            }.items()
        }
    }


@pytest.mark.parametrize(
    "name,url,expected",
    [
        ("CC BY 2.0", "https://creativecommons.org/licenses/by/2.0/", "CC-BY-2.0"),
        ("CC BY 3.0", "https://creativecommons.org/licenses/by/3.0/", "CC-BY-3.0"),
        ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", "CC-BY-4.0"),
        ("CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0/", "CC-BY-SA-2.0"),
        ("CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0/", "CC-BY-SA-3.0"),
        ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/", "CC-BY-SA-4.0"),
        ("CC0", "https://creativecommons.org/publicdomain/zero/1.0/", "CC0-1.0"),
    ],
)
def test_known_licences_only(name, url, expected):
    result = licence(metadata(name, url))
    assert result["license_id"] == expected
    assert result["author"] == "Example photographer"
    assert result["attribution_links"] == ["https://commons.wikimedia.org/wiki/User:Example"]


def test_public_domain_requires_explicit_basis():
    m = metadata("Public domain", "")
    with pytest.raises(ValueError, match="basis"):
        licence(m)
    m["extmetadata"].update(Copyrighted={"value": "False"}, License={"value": "pd"})
    assert licence(m)["license_id"] == "PUBLIC-DOMAIN"


def test_official_english_deed_is_the_same_explicit_licence():
    m = metadata("CC0", "http://creativecommons.org/publicdomain/zero/1.0/deed.en")
    assert licence(m)["license_id"] == "CC0-1.0"
    m["extmetadata"]["LicenseUrl"]["value"] += "/unexpected"
    with pytest.raises(ValueError, match="mismatch"):
        licence(m)


def test_description_byline_and_copyright_notice_are_preserved():
    m = metadata()
    m["extmetadata"]["ImageDescription"] = {
        "value": "Event. Foto: Example photographer. © Example."
    }
    rights = licence(m)
    assert (
        rights["attribution"]
        == rights["copyright_notice"]
        == "Event. Foto: Example photographer. © Example."
    )


@pytest.mark.parametrize(
    "name",
    [
        "",
        "Creative Commons",
        "Unknown",
        "Fair use",
        "CC BY-NC 4.0",
        "CC BY-ND 4.0",
        "All rights reserved",
        "Editorial use only",
    ],
)
def test_unsafe_licences_rejected(name):
    with pytest.raises(ValueError):
        licence(metadata(name))


def test_malformed_licence_url_and_attribution_rejected():
    for m in [{}, metadata("CC BY-SA 4.0", "https://example.org/license"), metadata()]:
        if m == metadata():
            m["extmetadata"]["Artist"]["value"] = "Unknown"
        with pytest.raises(ValueError):
            licence(m)


@pytest.mark.parametrize(
    "format,mime,extension", [("JPEG", "image/jpeg", "jpg"), ("PNG", "image/png", "png")]
)
def test_safe_raster_deterministic_fixed_canvas(format, mime, extension):
    image = Image.new("RGB", (120, 240), "blue")
    stream = io.BytesIO()
    image.save(stream, format)
    first = thumbnail(stream.getvalue(), mime, "Example." + extension)
    assert first == thumbnail(stream.getvalue(), mime, "Example." + extension)
    with Image.open(io.BytesIO(first)) as output:
        assert output.format == "WEBP" and output.size == (256, 256)
        assert not output.info.get("exif")
        assert output.getpixel((0, 0)) != output.getpixel((128, 128))


def test_exif_orientation_keeps_full_composition():
    image = Image.new("RGB", (100, 200), "blue")
    exif = Image.Exif()
    exif[274] = 6
    stream = io.BytesIO()
    image.save(stream, "JPEG", exif=exif)
    data = thumbnail(stream.getvalue(), "image/jpeg", "portrait.jpg")
    with Image.open(io.BytesIO(data)) as output:
        assert output.getpixel((128, 0)) != output.getpixel((128, 128))
        assert output.getpixel((10, 128))[2] > 200


@pytest.mark.parametrize(
    "raw,mime,filename",
    [
        (b"bad", "image/jpeg", "test.jpg"),
        (b"<svg/>", "image/svg+xml", "test.svg"),
        (b"bad", "image/png", "test.jpg"),
        (b"x" * 12_000_001, "image/jpeg", "test.jpg"),
    ],
)
def test_untrusted_downloads_rejected(raw, mime, filename):
    with pytest.raises((ValueError, OSError)):
        thumbnail(raw, mime, filename)


def test_extreme_dimensions_rejected_before_decode():
    stream = io.BytesIO()
    Image.new("RGB", (12001, 64)).save(stream, "PNG")
    with pytest.raises(ValueError, match="dimensions"):
        thumbnail(stream.getvalue(), "image/png", "large.png")


@pytest.mark.parametrize(
    "url",
    [
        "http://upload.wikimedia.org/wikipedia/commons/a.jpg",
        "https://example.org/a.jpg",
        "https://upload.wikimedia.org/wikipedia/en/a.jpg",
        "https://user:password@commons.wikimedia.org/a",
        "https://commons.wikimedia.org:444/a",
    ],
)
def test_external_download_allowlist(url):
    with pytest.raises(ValueError):
        safe_url(url)


def test_cache_integrity_and_offline_resume(tmp_path: Path):
    client = Wikimedia(tmp_path)
    calls = []
    client.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: (calls.append(request), httpx.Response(200, json={"search": []}))[1]
        )
    )
    first, _ = client.search("Example")
    second, _ = client.search("Example")
    assert first == second == [] and len(calls) == 1
    next(p for p in tmp_path.iterdir() if p.suffix == "").write_text("changed")
    with pytest.raises(ValueError, match="integrity"):
        client.search("Example")


def test_common_source_name_is_review_only():
    p = person()
    p["common_name_review"] = True
    assert evaluate(p, [entity()], RELATED)["status"] == "likely"


def test_entity_cache_reuses_different_batches_with_original_provenance(tmp_path):
    client = Wikimedia(tmp_path)
    calls = []

    def response(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={"entities": {q: {"id": q} for q in request.url.params["ids"].split("|")}},
        )

    client.client = httpx.Client(transport=httpx.MockTransport(response))
    first, sources = client.entities(["Q1", "Q2", "Q3"])
    resumed = Wikimedia(tmp_path)
    resumed.client = httpx.Client(
        transport=httpx.MockTransport(lambda _: pytest.fail("cached entity must not hit network"))
    )
    subset, metadata = resumed.entities(["Q3", "Q1"])
    assert subset == {q: first[q] for q in ("Q3", "Q1")}
    assert metadata["entity_sources"]["Q3"] == sources["entity_sources"]["Q3"]
    assert len(calls) == 1
    next(p for p in tmp_path.iterdir() if p.suffix == "").write_text("changed")
    with pytest.raises(ValueError, match="integrity"):
        Wikimedia(tmp_path).entities(["Q1"])


def test_api_throttling_is_retried_and_error_is_not_cached(tmp_path, monkeypatch):
    from football_intelligence.images import client as module

    sleeps = []
    monkeypatch.setattr(module.time, "sleep", sleeps.append)
    responses = iter(
        [
            httpx.Response(429, headers={"Retry-After": "7"}),
            httpx.Response(200, json={"error": {"code": "cirrussearch-too-busy-error"}}),
            httpx.Response(200, json={"search": []}),
        ]
    )
    client = Wikimedia(tmp_path)
    client.client = httpx.Client(transport=httpx.MockTransport(lambda _: next(responses)))
    assert client.search("Example")[0] == []
    assert client.requests == 3 and 7 in sleeps
    assert client.search("Example")[0] == [] and client.requests == 3


def test_related_labels_are_bounded_and_never_replace_identity_claims(tmp_path, monkeypatch):
    from football_intelligence.images import client as module

    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    requested = []

    def response(request):
        props = request.url.params["props"]
        requested.append((request.url.params["ids"], props))
        return httpx.Response(
            200,
            json={
                "entities": {
                    q: {
                        "id": q,
                        "labels": {"en": {"value": q}},
                        **({"claims": {}} if "claims" in props else {}),
                    }
                    for q in request.url.params["ids"].split("|")
                }
            },
        )

    client = Wikimedia(tmp_path)
    client.client = httpx.Client(transport=httpx.MockTransport(response))
    client.entities(["Q1"])
    assert set(client.labels(["Q1", "Q2"])) == {"Q1", "Q2"}
    assert requested[-1] == ("Q2", "labels|aliases")
    assert "claims" in client.entities(["Q2"])[0]["Q2"]
    assert requested[-1] == ("Q2", "labels|aliases|claims")


@pytest.mark.parametrize(
    "scenario",
    [
        "resume",
        "partial_failure",
        "shared_image",
        "rights_collision",
        "commons_timeout",
        "download_timeout",
        "commons_unavailable",
        "download_unavailable",
    ],
)
def test_pipeline_end_to_end_isolated_from_football_data(tmp_path, monkeypatch, scenario):
    import hashlib
    import json

    from football_intelligence.images import pipeline

    p = person()
    p.update(
        names=["Éva Example"],
        profiles=["wyscout-1-1-1"],
        source_files=[],
        provider_player_id="1",
        contexts=[
            {
                "id": "wyscout-1-1",
                "gender": "female",
                "competition": "Test competition",
                "season": "2020/2021",
            }
        ],
    )
    p["id"] = "wyscout:1"
    raw = io.BytesIO()
    Image.new("RGB", (128, 256), "blue").save(raw, "JPEG")
    data = raw.getvalue()
    image_info = {
        **metadata(),
        "mime": "image/jpeg",
        "size": len(data),
        "width": 128,
        "height": 256,
        "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Test.jpg",
        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Test.jpg",
        "sha1": hashlib.sha1(data).hexdigest(),
    }
    e = entity()
    e["claims"]["P18"] = [claim("Test.jpg")]
    source = {"retrieved_at": "2026-10-01T00:00:00Z", "sha256": "a" * 64, "mime": "image/jpeg"}

    class Fake:
        refresh = False
        requests = 0

        def __init__(self, *args, **kwargs):
            pass

        def search(self, name):
            return [{"id": "Q123"}], source

        def entities(self, ids):
            return {q: e if q == "Q123" else RELATED[q] for q in ids}, source

        def commons(self, title):
            return {"title": "File:Test.jpg", "imageinfo": [image_info]}, source

        def labels(self, ids):
            return self.entities(ids)[0]

        def get(self, url, **kwargs):
            return data, source

    monkeypatch.setattr(pipeline, "Wikimedia", Fake)
    monkeypatch.setattr(pipeline, "identities", lambda root: [p])
    (tmp_path / "config/player-images").mkdir(parents=True)
    override = tmp_path / "config/player-images/overrides.json"
    override.write_text('{"version":1,"players":{}}')
    index = tmp_path / "artifacts/v11/public/index.json"
    index.parent.mkdir(parents=True)
    index.write_text('{"profiles":[]}')
    first = pipeline.enrich(tmp_path)
    assert first["published_assets"] == 1 and first["identities_processed"] == 1
    manifest_path = tmp_path / "artifacts/player-images/manifest.json"
    original = manifest_path.read_bytes()
    if scenario.endswith(("_timeout", "_unavailable")):
        published = tmp_path / "artifacts/player-images"
        before = {
            str(f.relative_to(published)): f.read_bytes()
            for f in published.rglob("*")
            if f.is_file()
        }

        def unavailable(*args, **kwargs):
            if scenario.endswith("_timeout"):
                raise httpx.ReadTimeout("Temporary network timeout")
            raise ValueError("Wikimedia unavailable after bounded retries")

        monkeypatch.setattr(
            Fake, "commons" if scenario.startswith("commons") else "get", unavailable
        )
        with pytest.raises(ValueError, match="previous publication retained"):
            pipeline.enrich(tmp_path)
        after = {
            str(f.relative_to(published)): f.read_bytes()
            for f in published.rglob("*")
            if f.is_file() and f.name != "run-error.json"
        }
        assert after == before
        assert json.loads((published / "run-error.json").read_text())["stage"] == "image_retrieval"
        return
    if scenario == "partial_failure":
        published = tmp_path / "artifacts/player-images"
        before = {f.name: f.read_bytes() for f in published.rglob("*") if f.is_file()}
        other = {**p, "id": "wyscout:2", "names": ["Eva Other"]}
        monkeypatch.setattr(pipeline, "identities", lambda root: [p, other])

        def partially_failed_search(self, name):
            if name == "Éva Example":
                raise httpx.ReadTimeout("Temporary lookup failure")
            return [], source

        monkeypatch.setattr(Fake, "search", partially_failed_search)
        with pytest.raises(ValueError, match="previous publication retained"):
            pipeline.enrich(tmp_path)
        after = {
            f.name: f.read_bytes()
            for f in published.rglob("*")
            if f.is_file() and f.name != "run-error.json"
        }
        assert after == before
        return
    if scenario in {"shared_image", "rights_collision"}:
        other = {
            **p,
            "id": "wyscout:2",
            "provider_player_id": "2",
            "names": ["Eva Other"],
            "profiles": ["wyscout-1-1-2"],
        }
        other_entity = deepcopy(e)
        other_entity.update(id="Q456", labels={"en": {"value": "Eva Other"}})
        if scenario == "rights_collision":
            other_entity["claims"]["P18"] = [claim("Other.jpg")]
        monkeypatch.setattr(pipeline, "identities", lambda root: [p, other])
        monkeypatch.setattr(
            Fake,
            "search",
            lambda self, name: ([{"id": "Q123" if name == "Éva Example" else "Q456"}], source),
        )
        monkeypatch.setattr(
            Fake,
            "entities",
            lambda self, ids: (
                {q: {"Q123": e, "Q456": other_entity, **RELATED}[q] for q in ids},
                {
                    **source,
                    "entity_sources": {
                        q: {**source, "sha256": ("b" if q == "Q456" else "a") * 64} for q in ids
                    },
                },
            ),
        )
        monkeypatch.setattr(
            Fake,
            "commons",
            lambda self, title: (
                {"title": f"File:{title}", "imageinfo": [image_info]},
                {**source, "sha256": ("c" if title == "Other.jpg" else "a") * 64},
            ),
        )
        result = pipeline.enrich(tmp_path)
        manifest = json.loads(manifest_path.read_text())
        assert result["published_assets"] == 1
        assert result["published_identities"] == (2 if scenario == "shared_image" else 1)
        assert "wikidata_id" not in next(iter(manifest["assets"].values()))
        if scenario == "shared_image":
            assert manifest["identities"]["wyscout:2"]["wikidata_id"] == "Q456"
            assert manifest["identities"]["wyscout:2"]["wikidata_metadata_sha256"] == "b" * 64
            assert manifest["identities"]["wyscout:1"]["wikidata_metadata_sha256"] == "a" * 64
            assert (
                manifest["identities"]["wyscout:1"]["asset"]
                == manifest["identities"]["wyscout:2"]["asset"]
            )
        else:
            assert result["image_status"]["source_collision_requires_review"] == 1
        return
    monkeypatch.setattr(
        pipeline, "thumbnail", lambda *a: pytest.fail("verified derived image must be reused")
    )
    pipeline.enrich(tmp_path)
    assert manifest_path.read_bytes() == original
    override.write_text(
        json.dumps(
            {
                "version": 1,
                "players": {"wyscout:1": {"status": "excluded", "reason": "test withdrawal"}},
            }
        )
    )
    final = pipeline.enrich(tmp_path)
    assert final["published_assets"] == 0 and final["match_status"] == {"excluded": 1}
    assert list((tmp_path / "artifacts/player-images/assets").iterdir()) == []
    assert index.read_text() == '{"profiles":[]}'


def test_uk_citizenship_is_compatible_with_source_home_nation():
    p = person()
    p["nationalities"] = ["England"]
    e = entity()
    e["claims"]["P27"] = [claim({"id": "Q145"})]
    related = {**RELATED, "Q145": {"labels": {"en": {"value": "United Kingdom"}}}}
    result = evaluate(p, [e], related)
    assert result["status"] == "verified"
    assert result["candidates"][0]["signals"]["uk_constituent_country_compatible"]
