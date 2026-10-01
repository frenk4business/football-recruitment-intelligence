"""Exact licence allowlist and bounded raster-only, no-crop thumbnail conversion."""

import hashlib
import io
import re
import warnings
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse

from PIL import Image, ImageOps

MAX_BYTES = 12_000_000
MAX_PIXELS = 32_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS
LICENSES = {
    **{
        f"CC BY{suffix} {version}": {
            "id": f"CC-BY{'-SA' if suffix else ''}-{version}",
            "url": f"https://creativecommons.org/licenses/by{'-sa' if suffix else ''}/{version}/",
        }
        for suffix in ("", "-SA")
        for version in ("2.0", "2.5", "3.0", "4.0")
    },
    "CC0": {"id": "CC0-1.0", "url": "https://creativecommons.org/publicdomain/zero/1.0/"},
    "Public domain": {
        "id": "PUBLIC-DOMAIN",
        "url": "https://creativecommons.org/publicdomain/mark/1.0/",
    },
}


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.links: list[str] = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    value = "https:" + v if v.startswith("//") else v
                    p = urlparse(value)
                    if p.scheme == "https" and p.hostname and not p.username:
                        self.links.append(value)


def plain(value: str):
    parser = TextOnly()
    parser.feed(value)
    return " ".join(unescape(" ".join(parser.parts)).split())


def licence(info: dict) -> dict:
    ext = info.get("extmetadata")
    if not isinstance(ext, dict):
        raise ValueError("missing_licence_metadata")

    def value(key):
        v = ext.get(key, {}).get("value", "")
        if not isinstance(v, str):
            raise ValueError("malformed_licence_metadata")
        return plain(v)

    name = value("LicenseShortName")
    url = value("LicenseUrl").replace("http://", "https://").rstrip("/")
    # Official human-readable deeds identify the same canonical licence.
    url = re.sub(r"/deed\.(en|nl)$", "", url)
    terms = " ".join(
        value(k)
        for k in (
            "License",
            "LicenseShortName",
            "UsageTerms",
            "Restrictions",
            "Permission",
            "Attribution",
            "Credit",
        )
    )
    if re.search(
        r"fair[ -]?use|non[ -]?commercial|no[ -]?derivatives|all rights reserved|editorial|\bby-n[cd]\b",
        terms,
        re.I,
    ):
        raise ValueError("restricted_licence")
    if value("Restrictions") or value("NonFree").lower() in ("true", "yes", "1"):
        raise ValueError("additional_restrictions_require_review")
    if name not in LICENSES:
        raise ValueError("unsupported_licence")
    accepted = LICENSES[name]
    if name == "Public domain":
        if value("Copyrighted").lower() != "false" or value("License").lower() not in (
            "pd",
            "public domain",
        ):
            raise ValueError("unclear_public_domain_basis")
        if url and url.rstrip("/") != accepted["url"].rstrip("/"):
            raise ValueError("unsupported_public_domain_terms")
    elif url.rstrip("/") != accepted["url"].rstrip("/"):
        raise ValueError("licence_name_url_mismatch")
    origin_text = " ".join(
        value(k) for k in ("Artist", "Credit", "Source", "Attribution", "ImageDescription")
    )
    if re.search(
        r"getty\s*images|reuters|agence france[ -]?presse|\bafp\b|associated press|apimages\.com|apnews\.com|\bap\s+(?:photo|images)\b",
        origin_text,
        re.I,
    ):
        raise ValueError("commercial_agency_origin_requires_review")
    author = value("Artist")
    if not author or author.casefold() in {"unknown", "unknown author", "anonymous"}:
        raise ValueError("unclear_attribution")
    links = TextOnly()
    for k in ("Artist", "Attribution", "Credit", "ImageDescription"):
        links.feed(ext.get(k, {}).get("value", ""))
    return {
        "license_id": accepted["id"],
        "license_name": name,
        "license_url": accepted["url"],
        "author": author,
        "attribution": value("Attribution")
        or (
            value("ImageDescription")
            if re.search(
                r"\b(?:photo|foto|photograph|photographer)\s*(?::|by\b)",
                value("ImageDescription"),
                re.I,
            )
            else ""
        ),
        "credit": value("Credit"),
        "description": value("ImageDescription"),
        "source_text": value("Source"),
        "copyright_notice": value("ImageDescription")
        if re.search(r"©|\bcopyright\b|\(c\)", value("ImageDescription"), re.I)
        else "",
        "attribution_links": sorted(set(links.links)),
        "share_alike": name.startswith("CC BY-SA"),
        "transformation": "EXIF orientation; proportional resize and padding to 256×256; WebP conversion; no crop. Derived image retains the source licence.",
    }


def thumbnail(raw: bytes, mime: str, filename: str) -> bytes:
    if len(raw) > MAX_BYTES or mime not in {"image/jpeg", "image/png"}:
        raise ValueError("unsupported_or_oversized_raster")
    suffix = filename.rsplit(".", 1)[-1].lower()
    if suffix not in ({"jpg", "jpeg"} if mime == "image/jpeg" else {"png"}):
        raise ValueError("image_extension_mime_mismatch")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(raw)) as image:
            if image.format != ("JPEG" if mime == "image/jpeg" else "PNG"):
                raise ValueError("decoded_format_mismatch")
            if (
                image.width * image.height > MAX_PIXELS
                or max(image.size) > 12000
                or min(image.size) < 64
            ):
                raise ValueError("unsafe_or_insufficient_image_dimensions")
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError("animated_image_not_supported")
            image.verify()
        with Image.open(io.BytesIO(raw)) as original:
            oriented = ImageOps.exif_transpose(original).convert("RGB")
            oriented.thumbnail((256, 256), Image.Resampling.LANCZOS, reducing_gap=3)
            # Letterbox preserves the whole composition; no face localisation or crop.
            canvas = Image.new("RGB", (256, 256), (233, 237, 240))
            canvas.paste(oriented, ((256 - oriented.width) // 2, (256 - oriented.height) // 2))
            output = io.BytesIO()
            canvas.save(output, "WEBP", quality=82, method=6, exact=True)
    data = output.getvalue()
    if len(data) > 40_000:
        raise ValueError("thumbnail_byte_budget_exceeded")
    return data


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
