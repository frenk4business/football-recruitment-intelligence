import hashlib

import httpx
import pytest

from football_intelligence.profiles.cache import Cache


def test_verified_cache_is_reused_and_tampering_rejected(tmp_path):
    cache = Cache(tmp_path)
    calls = []
    cache.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: calls.append(request.url) or httpx.Response(200, content=b"synthetic")
        )
    )
    sha = hashlib.sha256(b"synthetic").hexdigest()
    path = cache.get("fixture.json", "https://example.test/file", sha256=sha)
    assert cache.get("fixture.json", "https://example.test/file", sha256=sha) == path
    assert len(calls) == 1
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="SHA256"):
        cache.get("fixture.json", "https://example.test/file", sha256=sha)
    with pytest.raises(ValueError, match="Unsafe"):
        cache.get("../escape", "https://example.test/file")


def test_resumption_validates_range_and_complete_checksum(tmp_path):
    cache = Cache(tmp_path)
    (tmp_path / "fixture.json.part").write_bytes(b"syn")

    def response(request):
        assert request.headers["range"] == "bytes=3-"
        return httpx.Response(206, headers={"Content-Range": "bytes 3-8/9"}, content=b"thetic")

    cache.client = httpx.Client(transport=httpx.MockTransport(response))
    path = cache.get(
        "fixture.json", "https://example.test/file", md5=hashlib.md5(b"synthetic").hexdigest()
    )
    assert path.read_bytes() == b"synthetic"


def test_download_size_is_bounded_and_bad_checksum_fails_closed(tmp_path):
    cache = Cache(tmp_path)
    cache.client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"synthetic"))
    )
    with pytest.raises(ValueError, match="size bound"):
        cache.get("large.json", "https://example.test/file", limit=3)
    with pytest.raises(ValueError, match="MD5"):
        cache.get("bad.json", "https://example.test/file", md5="wrong")
