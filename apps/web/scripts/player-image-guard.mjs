import {
  readFileSync,
  existsSync,
  readdirSync,
  mkdirSync,
  rmSync,
  writeFileSync,
  copyFileSync,
} from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";
import { creditsHtml } from "./player-image-credits.mjs";
const sha = (v) => createHash("sha256").update(v).digest("hex");
const check = (condition, message) => {
  if (!condition) throw new Error(`Player images: ${message}`);
};
const hex = /^[0-9a-f]{64}$/;
const canonicalLicenceUrl = (value) =>
  value
    ?.replace(/^http:/, "https:")
    .replace(/\/$/, "")
    .replace(/\/deed\.(en|nl)$/, "");
const licences = new Map([
  ...["2.0", "2.5", "3.0", "4.0"].flatMap((v) => [
    [
      `CC-BY-${v}`,
      [`CC BY ${v}`, `https://creativecommons.org/licenses/by/${v}/`],
    ],
    [
      `CC-BY-SA-${v}`,
      [`CC BY-SA ${v}`, `https://creativecommons.org/licenses/by-sa/${v}/`],
    ],
  ]),
  ["CC0-1.0", ["CC0", "https://creativecommons.org/publicdomain/zero/1.0/"]],
  [
    "PUBLIC-DOMAIN",
    ["Public domain", "https://creativecommons.org/publicdomain/mark/1.0/"],
  ],
]);
function https(value, host) {
  const url = new URL(value);
  check(
    url.protocol === "https:" &&
      !url.username &&
      !url.password &&
      (!host || url.hostname === host),
    "unsafe attribution/source URL",
  );
}
function canonicalIdentity(id) {
  const [provider, player] = id.split(":");
  const bytes = createHash("sha1")
    .update(Buffer.from("6ba7b8119dad11d180b400c04fd430c8", "hex"))
    .update(`fri:${provider}:players:${player}`)
    .digest()
    .subarray(0, 16);
  bytes[6] = (bytes[6] & 15) | 80;
  bytes[8] = (bytes[8] & 63) | 128;
  const h = bytes.toString("hex");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}
export function validateImages(root) {
  const dir = join(root, "artifacts/player-images");
  const manifest = JSON.parse(readFileSync(join(dir, "manifest.json")));
  const overrides = JSON.parse(
    readFileSync(join(root, "config/player-images/overrides.json")),
  ).players;
  const review = new Map(
    JSON.parse(readFileSync(join(dir, "review.json"))).map((r) => [
      r.identity,
      r,
    ]),
  );
  const profiles = JSON.parse(
    readFileSync(join(root, "artifacts/v11/public/index.json")),
  ).profiles;
  const profileIds = new Set(profiles.map((p) => p.id));
  const sourcePins = new Map(
    JSON.parse(readFileSync(join(root, "config/v11-sources.json"))).files.map(
      (f) => [f.path, f.sha256],
    ),
  );
  check(manifest.version === "player-images-v1", "unknown manifest version");
  const listed = Object.keys(manifest.assets).sort();
  check(
    JSON.stringify(readdirSync(join(dir, "assets")).sort()) ===
      JSON.stringify(listed.map((h) => h + ".webp").sort()),
    "unlisted or missing source image",
  );
  let bytes = 0;
  const referenced = new Set();
  for (const [id, person] of Object.entries(manifest.identities)) {
    check(/^(statsbomb|wyscout):[0-9]+$/.test(id), "invalid provider identity");
    check(
      person.match_status === "verified" &&
        /^Q[1-9][0-9]*$/.test(person.wikidata_id),
      "unverified identity",
    );
    check(overrides[id]?.status !== "excluded", "excluded identity published");
    check(
      person.source_files?.length > 0 &&
        person.source_files.every(
          (f) => sourcePins.get(f.path) === f.sha256 && hex.test(f.sha256),
        ),
      "unpinned provider identity evidence",
    );
    check(
      person.profiles.length > 0 &&
        person.profiles.every(
          (p) =>
            profileIds.has(p) &&
            p.split("-")[0] === id.split(":")[0] &&
            p.split("-").at(-1) === id.split(":")[1],
        ),
      "profile/provider mapping mismatch",
    );
    const match = review.get(id)?.match;
    check(
      match?.status === "verified" &&
        match.qid === person.wikidata_id &&
        review.get(id)?.asset === person.asset,
      "missing reviewed identity provenance",
    );
    if (person.match_method === "manual_metadata_review") {
      const o = overrides[id];
      check(
        o?.status === "verified" &&
          o.wikidata_id === person.wikidata_id &&
          o.reason &&
          o.reviewer &&
          o.reviewed_at &&
          o.evidence_urls?.length >= 2,
        "invalid manual verification",
      );
      o.evidence_urls.forEach((u) => https(u));
      check(
        new Set(o.evidence_urls.map((u) => new URL(u).hostname)).size >= 2,
        "manual evidence needs independent source domains",
      );
    } else {
      check(
        person.match_method === "name_dob_occupation_citizenship" &&
          match.candidates.length === 1 &&
          !review.get(id)?.common_name_review,
        "unsafe automatic method",
      );
      const c = match.candidates[0],
        s = c.signals;
      check(
        c.qid === person.wikidata_id &&
          c.automatic &&
          s.name_or_alias &&
          s.label_name_compatible &&
          s.dob_match &&
          s.footballer &&
          s.nationality_match &&
          !s.dob_conflict &&
          !s.nationality_conflict &&
          !s.gender_conflict,
        "automatic evidence insufficient",
      );
    }
    check(
      manifest.assets[person.asset]?.wikidata_id === person.wikidata_id,
      "identity/image QID differs",
    );
    referenced.add(person.asset);
  }
  check(referenced.size === listed.length, "unreferenced image asset");
  for (const [uuid, id] of Object.entries(manifest.legacy)) {
    check(
      uuid === canonicalIdentity(id) && manifest.identities[id],
      "invalid legacy mapping",
    );
    // UUID is derived from the existing provider-scoped mapping by the offline pipeline.
    // No name join or cross-provider merge is permitted here.
  }
  for (const [hash, asset] of Object.entries(manifest.assets)) {
    check(
      hex.test(hash) &&
        asset.path === `players/images/${hash}.webp` &&
        asset.sha256 === hash,
      "unsafe image path/hash",
    );
    const data = readFileSync(join(dir, "assets", hash + ".webp"));
    check(
      sha(data) === hash && data.length === asset.bytes && data.length <= 40000,
      "image integrity/size differs",
    );
    check(
      data.toString("ascii", 0, 4) === "RIFF" &&
        data.toString("ascii", 8, 12) === "WEBP" &&
        data.readUInt32LE(4) + 8 === data.length,
      "invalid WebP container",
    );
    // Pipeline emits ordinary lossy VP8 frames, with a fixed 256px canvas.
    check(
      data.toString("ascii", 12, 16) === "VP8 " &&
        (data.readUInt16LE(26) & 0x3fff) === 256 &&
        (data.readUInt16LE(28) & 0x3fff) === 256 &&
        asset.width === 256 &&
        asset.height === 256,
      "unexpected image dimensions/encoding",
    );
    const l = licences.get(asset.license_id);
    check(
      l &&
        l[0] === asset.license_name &&
        l[1] === asset.license_url &&
        asset.author?.trim(),
      "unsupported licence or attribution",
    );
    const ext = asset.licence_metadata;
    check(
      ext?.LicenseShortName?.value === asset.license_name &&
        !ext.Restrictions?.value &&
        !/^(true|yes|1)$/i.test(ext.NonFree?.value ?? ""),
      "rights snapshot differs",
    );
    if (asset.license_id === "PUBLIC-DOMAIN")
      check(
        ext.Copyrighted?.value?.toLowerCase() === "false" &&
          /^(pd|public domain)$/i.test(ext.License?.value) &&
          (!ext.LicenseUrl?.value ||
            canonicalLicenceUrl(ext.LicenseUrl.value) ===
              asset.license_url.replace(/\/$/, "")),
        "unclear public domain basis",
      );
    else
      check(
        canonicalLicenceUrl(ext.LicenseUrl?.value) ===
          asset.license_url.replace(/\/$/, ""),
        "licence URL snapshot differs",
      );
    check(
      !/fair[ -]?use|non[ -]?commercial|no[ -]?derivatives|all rights reserved|editorial|\bby-n[cd]\b/i.test(
        [
          "License",
          "LicenseShortName",
          "UsageTerms",
          "Restrictions",
          "Permission",
          "Attribution",
          "Credit",
        ]
          .map((k) => ext[k]?.value ?? "")
          .join(" "),
      ),
      "restricted rights",
    );
    check(
      !/getty\s*images|reuters|agence france[ -]?presse|\bafp\b|associated press|apimages\.com|apnews\.com|\bap\s+(?:photo|images)\b/i.test(
        ["Artist", "Credit", "Source", "Attribution", "ImageDescription"]
          .map((k) => ext[k]?.value ?? "")
          .join(" "),
      ),
      "commercial photo agency provenance",
    );
    for (const key of [
      "source_hash",
      "commons_metadata_sha256",
      "wikidata_metadata_sha256",
    ])
      check(hex.test(asset[key]), "missing source hash");
    check(
      asset.transformation &&
        asset.commons_filename?.startsWith("File:") &&
        asset.commons_filename.length > 5 &&
        asset.source === "Wikimedia Commons" &&
        Number.isFinite(Date.parse(asset.retrieved_at)),
      "missing provenance",
    );
    https(asset.commons_page_url, "commons.wikimedia.org");
    https(asset.original_image_url, "upload.wikimedia.org");
    check(
      new URL(asset.original_image_url).pathname.startsWith(
        "/wikipedia/commons/",
      ),
      "non-Commons source",
    );
    https(asset.wikidata_url, "www.wikidata.org");
    asset.attribution_links.forEach((u) => https(u));
    bytes += data.length;
  }
  check(bytes <= 4000000, "image budget exceeded");
  return manifest;
}
export function imageIndex(manifest) {
  const keys = [
    "path",
    "author",
    "license_id",
    "license_name",
    "license_url",
    "commons_page_url",
    "commons_filename",
    "attribution",
    "credit",
    "copyright_notice",
    "attribution_links",
    "transformation",
  ];
  return {
    version: manifest.version,
    identities: Object.fromEntries(
      Object.entries(manifest.identities).map(([k, v]) => [k, v.asset]),
    ),
    legacy: manifest.legacy,
    assets: Object.fromEntries(
      Object.entries(manifest.assets).map(([k, v]) => [
        k,
        Object.fromEntries(keys.map((key) => [key, v[key]])),
      ]),
    ),
  };
}
export function publishImages(root) {
  const manifest = validateImages(root);
  const data = JSON.stringify(imageIndex(manifest)) + "\n";
  check(
    Buffer.byteLength(data) <= 650000,
    "presentation index budget exceeded",
  );
  const path = `players/images/index-${sha(data)}.json`;
  const publicDir = join(root, "apps/web/public/players/images");
  if (existsSync(publicDir)) {
    const refFile = join(root, "apps/web/src/lib/player-image-reference.json");
    check(existsSync(refFile), "untracked existing player image directory");
    const ref = JSON.parse(readFileSync(refFile));
    check(
      /^\/players\/images\/index-[0-9a-f]{64}\.json$/.test(ref.path),
      "unsafe previous index path",
    );
    const previous = readFileSync(join(root, "apps/web/public", ref.path));
    check(sha(previous) === ref.sha256, "previous index integrity differs");
    const old = JSON.parse(previous);
    const expected = [
      ref.path.split("/").at(-1),
      ...Object.keys(old.assets).map((h) => h + ".webp"),
      ...Object.keys(ref.credits ?? {}),
    ].sort();
    check(
      JSON.stringify(readdirSync(publicDir).sort()) ===
        JSON.stringify(expected),
      "unlisted existing public image",
    );
    for (const [name, hash] of Object.entries(ref.credits ?? {}))
      check(
        /^credits-(en|nl)\.html$/.test(name) &&
          sha(readFileSync(join(publicDir, name))) === hash,
        "previous credits integrity differs",
      );
    for (const h of Object.keys(old.assets))
      check(
        hex.test(h) && sha(readFileSync(join(publicDir, h + ".webp"))) === h,
        "previous public image integrity differs",
      );
  }
  rmSync(publicDir, { recursive: true, force: true });
  mkdirSync(publicDir, { recursive: true });
  for (const [hash, a] of Object.entries(manifest.assets))
    copyFileSync(
      join(root, "artifacts/player-images/assets", hash + ".webp"),
      join(root, "apps/web/public", a.path),
    );
  writeFileSync(join(root, "apps/web/public", path), data);
  const credits = {};
  for (const locale of ["en", "nl"]) {
    const name = "credits-" + locale + ".html";
    const html = creditsHtml(manifest, locale);
    writeFileSync(join(publicDir, name), html);
    credits[name] = sha(html);
  }
  writeFileSync(
    join(root, "apps/web/src/lib/player-image-reference.json"),
    JSON.stringify({ path: "/" + path, sha256: sha(data), credits }) + "\n",
  );
  return {
    manifest,
    path,
    data,
    creditPaths: Object.keys(credits).map((name) => "players/images/" + name),
  };
}
export function validatePublishedImages(root, output) {
  const manifest = validateImages(root);
  const data = JSON.stringify(imageIndex(manifest)) + "\n";
  const indexName = `index-${sha(data)}.json`;
  const dir = join(output, "players/images");
  check(existsSync(dir), "missing published image directory");
  const names = [
    indexName,
    ...Object.keys(manifest.assets).map((h) => h + ".webp"),
    "credits-en.html",
    "credits-nl.html",
  ].sort();
  check(
    JSON.stringify(readdirSync(dir).sort()) === JSON.stringify(names),
    "unexpected published image files",
  );
  check(
    readFileSync(join(dir, indexName), "utf8") === data,
    "image index differs",
  );
  for (const locale of ["en", "nl"])
    check(
      readFileSync(join(dir, "credits-" + locale + ".html"), "utf8") ===
        creditsHtml(manifest, locale),
      "published credits differ",
    );
  for (const hash of Object.keys(manifest.assets))
    check(
      sha(readFileSync(join(dir, hash + ".webp"))) === hash,
      "published thumbnail differs",
    );
}
