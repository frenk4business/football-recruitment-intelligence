# Player image enrichment — delivery audit

Audit date: 2026-10-01. Additive product work based on `d833ad2157b0724e56d16aa0de3154a167b58e2d`; scientific version remains **1.1.0**. Counts below describe the actual complete database batch, not a sample run. Storage units are decimal bytes/MB.

## A. Architecture

`src/football_intelligence/images/` implements the offline CLI (`fri images enrich`, `fri images review`). `artifacts/player-images/` holds approved WebP files, their manifest, review and coverage. Raw responses/originals and staged output stay in ignored `data/raw/player-images/`. Core website builds consume reviewed artifacts without external APIs. Frontend integration is optional presentation lookup only.

See [operating instructions](README.md), [manifest](../../artifacts/player-images/manifest.json), [coverage](../../artifacts/player-images/coverage.json) and [all identity reviews](../../artifacts/player-images/review.json).

## B. Identity resolution

Automatic acceptance requires exactly one search candidate, exact normalized name/alias, an aligned multi-token display label, exact Gregorian day-level DOB, footballer occupation, compatible citizenship and no contradictory DOB/country/explicit source-gender evidence. A conflicting additional DOB also blocks acceptance. Mononyms/repeated source names, substantially different aliases, multiple candidates or missing DOB require explicit review. Historical club agreement supports evidence; a changed current club alone never rejects a player. UK citizenship is explicitly compatible with recorded UK constituent-country labels.

Provider identities remain separate. Existing provider UUIDs are reproduced exactly for the legacy Recruitment view; no name-based or scientific cross-provider join is introduced. Manual overrides require reviewer, reason, date and independent metadata-source URLs, and never bypass image licensing.

## C. Sources

Actual discovery uses the official Wikidata Action API: `wbsearchentities` (five candidates, one recorded-alias retry if empty), `wbgetentities` (twenty-item batches). Related country/club requests retrieve labels/aliases only. Commons `imageinfo` supplies original URL, SHA1, dimensions, MIME and licence/credit `extmetadata`. Originals are fetched solely from `upload.wikimedia.org/wikipedia/commons/`, with redirects disabled.

One worker, at least one second between requests, descriptive User-Agent, bounded retries/timeouts and checksum-verified cache. No SPARQL, commercial-site scraping, Openverse, face recognition, inferred appearance or runtime Wikimedia requests. Source credits may link to an original photographer/Flickr page; these are attribution links, not download providers.

## D. Coverage

**3,005 provider identities / 3,074 profiles processed. 482 identities have an approved image (16.04%); 485 profiles reference them (15.78%).**

| Provider | Identities | Verified | Likely | Ambiguous | None | Excluded | Photos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| statsbomb | 1118 | 7 | 1073 | 23 | 15 | 0 | 7 |
| wyscout | 1887 | 1051 | 333 | 394 | 108 | 1 | 475 |

Image outcomes: **482 published; 87 verified identities without P18; 77 rights rejections; 22 file-processing rejections; 390 deferred by the 4 MB budget; 1,947 unverified/excluded identities**. The 390 deferred candidates have P18 but their reuse eligibility is not claimed: further rights/download work was deliberately deferred. Per-competition-season outcomes are in `coverage.json`.

## E. Confidence

**Verified 1,058 · Likely 1,406 · Ambiguous 417 · None 123 · Excluded 1.** Seven verified identities use documented explicit metadata review; the remaining 1,051 meet the deterministic rule. Verification is a rule outcome, not a calibrated probability or a claim that Wikidata is infallible.

## F. Licensing

| Accepted licence | Images |
| --- | --- |
| CC-BY-2.0 | 37 |
| CC-BY-3.0 | 26 |
| CC-BY-4.0 | 15 |
| CC-BY-SA-2.0 | 28 |
| CC-BY-SA-3.0 | 197 |
| CC-BY-SA-4.0 | 147 |
| CC0-1.0 | 23 |
| PUBLIC-DOMAIN | 9 |

**77 rejections:** 63 additional restrictions; 14 unsupported licence labels/ported variants. A familiar free-licence label does not override extra restrictions.

| Rejected metadata label | Count |
| --- | --- |
| Attribution | 4 |
| CC BY 3.0 | 2 |
| CC BY 3.0 br | 2 |
| CC BY 4.0 | 1 |
| CC BY-SA 3.0 | 5 |
| CC BY-SA 3.0 at | 9 |
| CC BY-SA 3.0 ch | 2 |
| CC BY-SA 4.0 | 50 |
| Copyrighted free use | 2 |

Exact approved canonical URLs are required. Official English/Dutch deed URLs are normalized to that same canonical licence, as shown by the [CC0 deed](https://creativecommons.org/publicdomain/zero/1.0/deed.en). Arbitrary URLs are rejected. No CC0 case is accepted merely because a string contains “Creative Commons”. Derived files retain their licence/share-alike conditions; the repository MIT licence does not cover photos.

## G. Manual review

**32 metadata cases / 16 image compositions inspected**, recorded in [manual-identity-review.json](manual-identity-review.json). This is explicit Codex metadata/composition inspection, not an assertion of separate human legal sign-off. The sample spans both providers, men/women recorded in source context, common/ambiguous names, accented names, multi-club histories and every accepted licence class.

Seven StatsBomb identities without DOB were explicitly confirmed from named source records, source competition context, nationality and historical clubs. Three others were withheld. Twelve Wyscout cases were inspected without adding an override. One record with a suspicious display-name discrepancy was explicitly excluded. Nine automatically accepted cases were audited, including a CC0 file with the official deed URL. Alias/display-label discrepancies found during review now force review for the entire batch. Nationality discrepancies remain unresolved rather than silently changing football data. Images were inspected only for composition, not identity or personal attributes.

## H. Assets and reproducibility

**482 × 256px WebP, 3,964,182 bytes total**; one source per approved image for 32/64/96px display. Each file is under 40 KB. Originals are limited to 12 MB, 32 million pixels, 12,000px maximum side; only verified JPEG/PNG single-frame input is decoded. EXIF orientation is applied, aspect ratio preserved, full composition padded without cropping. Twenty MIME/decoded-format rejections were MPO multi-image files labelled JPEG; two other sources exceeded supported source limits. There were no unresolved network-download failures in the final report.

Pillow 12.3.0 and the encoder version/parameters are recorded. Source SHA1/SHA256, metadata-response hashes, derivative SHA256, dimensions, bytes, retrieval time, source title, author, credit, copyright/byline notices and original links are retained. Wikidata provenance is stored per provider identity, including QID, URL, response hash and P18 title, so independently verified identities can safely share the same Commons asset. Different original/rights snapshots producing the same derivative are withheld for review. Any failed identity search or Commons metadata/original retrieval prevents promotion and retains all approved artifacts; regression tests cover partial search/Commons/download failures, shared derivatives and provenance collisions. A cached rerun reproduced **all 485 enrichment files byte-for-byte with zero network requests**; see [reproducibility.json](reproducibility.json).

## I. Repository / deployment size

Approved images add 3.96 MB. The complete enrichment artifacts (including the 2.90 MB manifest and 5.73 MB review JSON) occupy 12.59 MB uncompressed. The measured pre-commit new-file set was 12.77 MB; individually zlib-compressed new blobs total approximately **5.26 MB**, an estimate of incremental clone impact before Git tree/pack/delta overhead. The implementation commit’s actual incremental Git pack measures **5,407,237 bytes (5.41 MB)** against the baseline; see [git-impact.json](git-impact.json). This measurement precedes the small documentation-only audit commit. Raw originals and API cache are excluded. No Git LFS, object store, new service or paid infrastructure is needed.

Static export: **57,324,260 → 62,541,902 bytes (+5,217,642; +9.1%)**, below the unchanged 65 MB ceiling. Scientific public JSON remains 47,430,174 bytes. Credits are generated once per language as static HTML rather than duplicated through Next.js RSC; the original full React listing exceeded the limit and was replaced before completion. The final export contains 20 application routes and 5,870 checksummed build files, including two secondary credits documents.

## J. Frontend

32px list/shortlist avatars, 64px comparison avatars and 96px profile avatar. Existing list density, hierarchy and analytical interactions remain intact. Photos and initials have identical boxes and selection treatment. The new lookup cannot affect eligibility, ranking, scores, uncertainty or model inputs. `next/image` follows the existing static/unoptimized setup; no image server is added.

EN/NL desktop/mobile captures cover lists, profile, comparison and actual shortlist rows. Both real-photo and fallback-heavy views were inspected. No horizontal page overflow occurred in any of the sixteen final view/locale/width observations.

## K. Fallbacks

**2,523 identities / 2,589 profiles** use initials. Missing/unverified/excluded/budget-deferred images, unavailable image index and broken WebP requests all fail closed to the same geometry. Initials are deterministic Unicode first/last letter tokens; mononyms use one initial and empty input uses `?`. No stock, generated or inferred human appearance. Duplicate row/comparison marks are decorative; the larger profile mark has localized accessible text.

## L. Attribution

Profile Data quality & methodology contains Commons source, original file title, author, licence, required credit/byline/copyright notices and transformation notice. Research links to [English credits](https://football-recruitment-intelligence.onrender.com/players/images/credits-en.html) and [Dutch credits](https://football-recruitment-intelligence.onrender.com/players/images/credits-nl.html), accessible without JavaScript. Every approved image appears there, with licence/source/derived-file links. New HTML escapes source text, is bilingual and is covered by the publication hash gate. [ATTRIBUTION.md](../../ATTRIBUTION.md) keeps image licences distinct from football-data licences.

## M. Performance

Same baseline commit, Chromium on Apple M5 Pro, localhost, fresh context per observation, no CPU/network throttling. Each cell is the median of EN/NL × 1440/375px. Ready time ends when the requested analytical view is visible; screenshots follow a short settling period. Comparison and shortlist are scrolled into view. This is a local lab sample, not field Core Web Vitals or statistically significant latency evidence.

| View | Transfer before → after (bytes) | Ready before → after (ms) | Maximum CLS before → after |
| --- | --- | --- | --- |
| players | 408,995 → 576,862 | 80.8 → 80.4 | 0.00000 → 0.00000 |
| profile | 445,109 → 548,046 | 149.2 → 148.6 | 0.00000 → 0.00000 |
| comparison | 451,159 → 591,689 | 125.2 → 125.6 | 0.00000 → 0.00000 |
| recruitment | 368,228 → 462,705 | 80.7 → 83.7 | 0.09144 → 0.09144 |

Profile click-to-visible median: **63.5 → 72.6 ms**. Photos add about 95–168 KB transfer to these views; the additional bandwidth is real, even though local readiness stays similar. Player/profile/comparison CLS remains zero; the existing Recruitment shift is unchanged at 0.09144 in the final comparable capture. **Zero runtime Wikimedia requests**, all views.

The existing player-search budget also passes: per-viewport median fill-to-render **8.3–10.8 ms (<100 ms)**, no initial full-profile requests and no page overflow. [before.json](before.json), [after.json](after.json), [search-performance.json](search-performance.json) retain observations and environment details. Content-hashed photos use the existing `/players*` revalidation/ETag policy; no immutable header is applied to changing credit documents.

## N. Tests and release gate

- **205 Python tests**; Ruff lint/format; mypy across 62 source files.
- **55 frontend unit tests**; ESLint; TypeScript; Prettier.
- **210 Chromium/Firefox/WebKit tests**, including EN/NL, mobile, keyboard, accessibility, blocked index, broken images, local-only requests and static credits. All pass.
- Production build and release validation pass: all image identity/source/licence/hash/dimension checks, exact published-file inventory, no unexpected image files, 2,146 frozen research hashes and existing public-data allowlist.
- npm audit: zero known vulnerabilities; Python dependency audit: no known vulnerabilities. Focused secret scan: no findings in reachable history or working files. This scanner is not a claim of exhaustive secret detection.
- Offline deterministic resume: 485 identical files, zero requests.

## O. Scientific integrity

The baseline comparison covers **28,064 existing data/artifact/scientific-source/brand files**. Only `src/football_intelligence/cli.py` differs, to register the isolated image commands; **28,063 files are byte-identical**. All 2,146 frozen research files validate. Player DNA, similarity, league translation, recruitment mathematics, scientific schemas, provider identity joins, source football data, branding and favicon are unchanged. No scientific release version or existing tag is modified. See [integrity.json](integrity.json).

## P. Limitations

Coverage is deliberately low. StatsBomb lacks source DOB; most identities remain pending explicit review. Commons and Wikidata can contain errors or change after retrieval; cached hashes preserve this audited build, not universal truth. Club labels/aliases may be incomplete. A photo may depict a different season or kit. Multi-image JPEG/MPO, large originals, unsupported licence variants and additional restrictions remain excluded. The four-megabyte limit defers 390 P18 candidates in stable provider-ID order, not by player quality; it is not a representative sample of football ability or data quality.

Copyright checks do not provide universal privacy/personality-right clearance. No endorsement is implied. Metadata review used no face recognition or inference of identity, age, race, gender or emotion from photographs. Network failure leaves the existing approved publication usable; public image failure uses initials. A deliberate metadata refresh can change results and requires repeating the audit/release gate.
