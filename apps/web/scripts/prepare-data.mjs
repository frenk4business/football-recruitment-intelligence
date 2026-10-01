import {
  validatePublication,
  validatePublicationPaths,
} from "./publication-guard.mjs";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import Ajv from "ajv/dist/2020.js";
import {
  root,
  read,
  json,
  sha,
  version,
  inventory,
  science,
  walk,
  git,
  verifyScience,
} from "./release-common.mjs";
verifyScience();
const staticAssets = new Set([
  "brand/statsbomb.png",
  "brand/fri-horizontal.webp",
  "brand/fri-emblem.webp",
  "brand/fri-social.png",
  "brand/favicon-32.png",
  "brand/favicon-192.png",
  "brand/apple-touch-icon.png",
  "favicon.ico",
  "robots.txt",
  "skillcorner-license.txt",
  "release-manifest.json",
]);
const publicRoot = join(root, "apps/web/public");
for (const path of walk(publicRoot)) {
  const name = path.slice(publicRoot.length + 1);
  if (
    !name.startsWith("data/") &&
    !name.startsWith("integrity/") &&
    !staticAssets.has(name)
  ) {
    throw new Error(`Unlisted static publication asset: ${name}`);
  }
}
if (
  json("apps/web/package.json").version !== version ||
  json("apps/web/package-lock.json").version !== version
)
  throw new Error("Package version must mirror VERSION");
const schemas = {
  ...json("artifacts/contracts.schema.json"),
  ...json("artifacts/v11/contracts.schema.json"),
};
const ajv = new Ajv({ strict: false, validateFormats: false });
const validators = new Map();
const listed = new Set(inventory.files.map((f) => f.source));
for (const dir of [
  "artifacts/explorer",
  "artifacts/v11/public",
  ...[2, 3, 4].map((n) => `artifacts/phase${n}/public`),
]) {
  for (const path of walk(join(root, dir))) {
    if (!listed.has(path.slice(root.length)))
      throw new Error(`Unlisted publication file: ${path.slice(root.length)}`);
  }
}
let total = 0;
const groups = {};
const dest = join(root, "apps/web/public/data");
rmSync(dest, { recursive: true, force: true });
rmSync(join(root, "apps/web/public/integrity"), {
  recursive: true,
  force: true,
});
for (const file of inventory.files) {
  validatePublicationPaths(file);
  const data = read(file.source);
  total += data.length;
  const key = `${file.schema}:${file.array}`;
  if (!validators.has(key))
    validators.set(
      key,
      ajv.compile({
        $defs: schemas,
        ...(file.array
          ? { type: "array", items: { $ref: `#/$defs/${file.schema}` } }
          : { $ref: `#/$defs/${file.schema}` }),
      }),
    );
  const validate = validators.get(key);
  validatePublication(file, data, validate);
  const output = join(root, "apps/web/public", file.path);
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, data);
  const parts = file.path.split("/");
  const prefix =
    parts.length > 3
      ? parts.slice(0, -1).join("/") + "/"
      : parts.slice(0, parts.length - 1).join("/") + "/";
  (groups[`/${prefix}`] ??= {})[`/${file.path}`] = file.sha256;
}
if (total > 55_000_000) throw new Error("Public JSON budget exceeded");
const groupIndex = [];
mkdirSync(join(root, "apps/web/public/integrity"), { recursive: true });
for (const [prefix, hashes] of Object.entries(groups)) {
  const bytes = JSON.stringify(hashes);
  const digest = sha(bytes);
  const path = `/integrity/${digest}.json`;
  writeFileSync(join(root, "apps/web/public", path), bytes);
  groupIndex.push({ prefix, path, sha256: digest });
}
groupIndex.sort(
  (a, b) =>
    b.prefix.length - a.prefix.length || a.prefix.localeCompare(b.prefix),
);
writeFileSync(
  join(root, "apps/web/src/lib/artifact-integrity.json"),
  JSON.stringify(groupIndex, null, 2) + "\n",
);
writeFileSync(
  join(root, "apps/web/src/lib/release-version.json"),
  JSON.stringify({ version }) + "\n",
);
const commit = git("rev-parse", "HEAD");
const manifest = {
  version,
  git_commit: commit,
  build_timestamp: git("show", "-s", "--format=%cI", "HEAD"),
  timestamp_policy: "Git commit time; deterministic, not wall-clock build time",
  scientific_versions: science.versions,
  expanded_profile_versions: [
    "statsbomb-profile-v2",
    "wyscout-profile-v1",
    "common-profile-v1",
    "common-similarity-v1",
  ],
  source_revisions: {
    v11: {
      revision: json("config/v11-sources.json").statsbomb_revision,
      config_sha256: sha(read("config/v11-sources.json")),
    },
    sample: Object.fromEntries(
      ["statsbomb", "skillcorner"].map((p) => [
        p,
        {
          revision: json("config/sample.json")[p].revision,
          config_sha256: sha(read("config/sample.json")),
        },
      ]),
    ),
    wsl: {
      revision: json("config/wsl_2023_24.sources.json").revision,
      config_sha256: sha(read("config/wsl_2023_24.sources.json")),
    },
    phase3: {
      revision: json("config/phase3.sources.json").revision,
      config_sha256: sha(read("config/phase3.sources.json")),
    },
  },
  public_artifacts: inventory.files.map(({ path, bytes, sha256, schema }) => ({
    path,
    bytes,
    sha256,
    schema,
  })),
  integrity_manifests: groupIndex,
  public_json_bytes: total,
};
writeFileSync(
  join(root, "apps/web/public/release-manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
);
console.log(
  `Validated ${inventory.files.length} public artifacts (${total} bytes), ${Object.keys(science.files).length} frozen research files; release ${version}.`,
);
