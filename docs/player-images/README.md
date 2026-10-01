# Player image enrichment

Player images are optional **presentation metadata**. The pipeline never writes canonical football data, Player DNA, similarity, recruitment or translation features. Provider IDs remain isolated. A repeated Wikidata QID is external evidence, never permission to join football providers.

## Sources and identity

The offline `fri images` command reads the existing 3,074-profile index and groups profiles by the exact `provider:player_id`. Pinned Wyscout player metadata supplies birth date and passport country. Pinned StatsBomb lineups supply names, aliases and football nationality; they do not supply a birth date. Every input file is checked against `config/v11-sources.json`. Competition, season, explicitly recorded gender and historical teams remain review context.

Discovery uses the official Wikidata Action API (`wbsearchentities`, maximum five candidates and one recorded-alias retry when the primary name returns none; `wbgetentities`, batches of at most twenty). Related club/country requests retrieve only labels and aliases, reusing already cached full entities where available. No SPARQL, commercial image source, search-engine image result, face recognition or inferred personal attribute is used. A single worker waits at least one second between requests, sends a descriptive project User-Agent, uses thirty-second timeouts and bounded backoff for HTTP 429/5xx and API overload responses. A circuit breaker stops an unavailable batch instead of repeatedly querying the service. Any failed identity search or Commons metadata/original retrieval aborts promotion and records the error in `run-error.json`; even a single temporary lookup failure preserves every previously approved mapping and image. It is never treated as a confirmed negative match. Replies and originals are hashed in the ignored `data/raw/player-images/http` cache. The optional `maxlag` parameter was removed after an upstream WDQS replication delay blocked unrelated Action API reads; actual HTTP/API throttling and Retry-After remain honoured.

Automatic `verified` requires **one search candidate**, exact normalized name or recorded alias, exact day-precision Gregorian birth date, association-footballer occupation and matching citizenship, without a DOB, citizenship or explicit gender conflict. Accents and punctuation are normalized deterministically. The English entity label must also contain at least two name tokens, all present in a recorded source name; significantly different aliases, unexplained label changes and mononym labels require explicit review even when another alias matches. Missing birth dates, mononyms, repeated same-provider names or multiple search results always require manual review. Multiple credible candidates or contradictory metadata are `ambiguous`. Current-club mismatch alone never rejects a historical player. Club agreement cannot substitute for birth date. UK citizenship is explicitly compatible with source England/Scotland/Wales/Northern Ireland labels; this compatibility signal is recorded separately. `likely`, `ambiguous` and `none` never receive automatic imagery. No probabilistic identity score or LLM judgement is used.

## Manual decisions

Review `artifacts/player-images/review.json`. It contains source-qualified identities and profile context, source DOB/country, candidate names/QIDs, identity signals, club/country evidence, P18 availability, image outcomes and licence rejection reasons where checked. `coverage.json` summarizes status and image outcomes per provider and competition-season.

Edit `config/player-images/overrides.json`, not code:

```json
{
  "version": 1,
  "players": {
    "statsbomb:123": {
      "status": "verified",
      "wikidata_id": "Q123",
      "reason": "Document the independent metadata reviewed and any discrepancy",
      "reviewer": "Reviewer name",
      "reviewed_at": "2026-10-01",
      "evidence_urls": ["https://provider.example/pinned-source", "https://www.wikidata.org/wiki/Q123"]
    },
    "wyscout:456": {"status": "excluded", "reason": "Ambiguous identity; do not publish"}
  }
}
```

These are schema examples, not real player mappings. Verified overrides require the fetched QID, a reviewer, reason/date and two independent evidence URLs. Exclusions take precedence. Overrides are never rewritten by enrichment. An override changes identity acceptance only; it cannot bypass licence, download, processing or publication checks. Metadata review may assess historical teams, source nationality and documented name aliases; it never identifies a person from a face. Review common names, missing DOB, multiple candidates and material context conflicts explicitly. An incorrect override remains a human-error risk; inspect and document decisions.

## Copyright reuse and processing

P18 only identifies a candidate Commons file. The official Commons `imageinfo` API supplies title, page, original URL, MIME, dimensions, SHA1 and `extmetadata`. An exact name/URL allowlist accepts CC BY and CC BY-SA versions 2.0, 2.5, 3.0 and 4.0; CC0 1.0; or explicit public-domain metadata. Official `/deed.en` and `/deed.nl` pages are normalized only to the exact same allowlisted canonical licence; arbitrary URLs or custom terms remain rejected. A generic “Creative Commons” claim is insufficient. Unsupported, unclear, fair-use, NC, ND, editorial, additional restricted or unattributed images fail closed. Identified commercial photo-agency provenance is rejected even if a free-licence label is present. Multi-licence or ported-licence strings outside the explicit allowlist require future review; they are not guessed.

Only JPEG/PNG originals from `upload.wikimedia.org/wikipedia/commons/` are downloaded, without redirects, up to 12 MB and 32 million pixels, with maximum dimension 12,000 and minimum dimension 64. The original is SHA1-checked against Commons and SHA256-recorded. Pillow 12.3.0 verifies decoding, rejects animations and oversized inputs, applies EXIF orientation, resizes proportionally and pads a 256×256 canvas. There is **no crop or face detection**. One WebP at quality 82/method 6, maximum 40 KB, serves every UI size. Extra EXIF is omitted, while required credits and copyright notices remain in the manifest/UI. Identical verified bytes share an asset only when the original hash and Commons rights snapshot also agree. Each provider identity retains its own Wikidata QID, URL, metadata hash and P18 title, independently checked against its review record. Equal derivatives with different source/rights provenance are withheld for review. Existing verified derived bytes are reused on resume.

Derived images retain the original licence. CC BY-SA thumbnails remain under their applicable share-alike terms. The project MIT licence does not cover these photographs. Copyright checks do not establish universal privacy/personality-right clearance in every jurisdiction. The use is informational football research, not endorsement.

Primary references: [Wikidata data access](https://www.wikidata.org/wiki/Wikidata:Data_access), [Commons machine-readable metadata](https://commons.wikimedia.org/wiki/Commons:Machine-readable_data), [MediaWiki imageinfo API](https://www.mediawiki.org/wiki/API:Imageinfo), [Commons reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [CC0 deed and canonical URL](https://creativecommons.org/publicdomain/zero/1.0/deed.en), [Pillow image safety](https://pillow.readthedocs.io/en/stable/reference/Image.html).

## Static publication

Approved derivatives, their manifest and review/coverage reports live in `artifacts/player-images/`. Originals and raw API replies remain ignored. The manifest includes source/derived hashes, metadata hashes, original dimensions/MIME, retrieval date, artist/credit/licence and transformation notice. A maximum 4 MB image budget and 650 KB presentation-index budget protect the existing 65 MB static export ceiling. Identities are processed in stable provider-ID order. When less than the maximum 40 KB thumbnail allowance remains, further P18 candidates are deferred before rights/download work; their reuse eligibility is not claimed. Extra imagery is reported as deferred by budget instead of silently increasing limits or provisioning paid storage.

`prepare-data.mjs` validates every identity, override, licence, source host, file path, hash, byte count and WebP dimensions before copying only listed files to `public/players/images/`. It rejects unexpected pre-existing generated images. `release-output.mjs` repeats validation on the actual export. Every asset also appears in the release's complete build-file hash manifest. Scientific publication inventories and frozen versions are unchanged. The current `/players*` cache policy revalidates these assets with ETags; content-hashed filenames additionally prevent stale replacement. No dynamic image optimizer or runtime Wikimedia request is needed.

## UI, accessibility and attribution

Players lists use 32px avatars, comparisons 64px, and profile headers 96px. Recruitment uses the same boxes and exact existing provider UUID mapping. Missing, excluded, ambiguous, failed or unavailable images use understated navy initials in identical geometry. List/comparison avatars are decorative beside names; the profile avatar has a localized description. Initials stay visible beneath pending images, and broken image requests fall back to those same initials. All image requests are local and lazy; one SHA256-verified presentation index is shared per page. Image failures never block football data or analytics.

Initials use Unicode letter tokens, first letter of the first and last token, uppercased deterministically. A mononym uses one initial; empty or non-letter input uses `?`. Multi-part/hyphenated surnames and punctuation follow the same documented rule, without attempting cultural name inference.

Profile **Data quality & methodology** contains each compared player's photo attribution. The footer links to a central EN/NL **Image credits** section under Research links to two ordinary static credits pages, available without JavaScript, listing source titles/pages, authors, licences, original credit links and transformed files. Credits are rendered once per language into manifest-validated HTML, avoiding repeated serialization into Next.js RSC payloads. Images have no bearing on ranking, eligibility, confidence, comparison or selection styling.

## Commands

```sh
uv sync --frozen
uv run fri images enrich
uv run fri images review
uv run fri images enrich --refresh-player 'statsbomb:123'
uv run fri images enrich --refresh-metadata
make test release-build release-validate
npm --prefix apps/web run check:format
npm --prefix apps/web run test:smoke
```

The raw football metadata must already be present from the pinned existing data pipeline. Do not rerun football research to generate images. Routine website builds are offline and consume only the reviewed committed enrichment. A deliberate metadata refresh is separate from the core build. New derivatives are staged in the ignored cache while network/decoding work runs; the approved asset directory is only updated after the batch completes. On an identity lookup, Commons retrieval or global API failure, the previous publication remains intact and `run-error.json` explains the interrupted stage; rerunning resumes from verified HTTP-cache entries. Remove an approved image by adding an exclusion and rerunning enrichment. A stale publication conflicting with that exclusion fails the release gate.

Actual coverage, sampled review findings, final size/performance and release validation are recorded separately in `delivery.md` after the real batch and UI checks complete.
