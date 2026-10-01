import test from "node:test";
import assert from "node:assert/strict";
import {
  mkdtempSync,
  mkdirSync,
  writeFileSync,
  readFileSync,
  rmSync,
} from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { createHash } from "node:crypto";
import { creditsHtml } from "./player-image-credits.mjs";
import {
  validateImages,
  publishImages,
  validatePublishedImages,
} from "./player-image-guard.mjs";
const bytes = Buffer.from(
  "UklGRroAAABXRUJQVlA4IK4AAAAwEQCdASoAAQABPmEwlkikIyIhICgAgAwJaW7hdrEe3AAAFpbJyHvtk5D32ych77ZOQ99snIe+2TkPfbJyHvtk5D32ych77ZOQ99snIe+2TkPfbJyHvtk5D32ych77ZOQ99snIe+2TkPfbJyHvtk5D32ych77ZOQ99snIe+2TkPfbJyHvtk5D32ych77ZOQ99qwAD+/v/f/+oiIKSWH/90GWcM5gAAAAAAAAAAAAA=",
  "base64",
);
const hash = createHash("sha256").update(bytes).digest("hex");
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "fri-image-guard-"));
  for (const p of [
    "artifacts/player-images/assets",
    "artifacts/v11/public",
    "config/player-images",
    "apps/web/src/lib",
  ])
    mkdirSync(join(root, p), { recursive: true });
  const write = (p, v) => writeFileSync(join(root, p), JSON.stringify(v));
  const manifest = {
    version: "player-images-v1",
    assets: {
      [hash]: {
        path: `players/images/${hash}.webp`,
        sha256: hash,
        bytes: bytes.length,
        width: 256,
        height: 256,
        source: "Wikimedia Commons",
        commons_page_url: "https://commons.wikimedia.org/wiki/File:Test.png",
        commons_filename: "File:Test.png",
        original_image_url:
          "https://upload.wikimedia.org/wikipedia/commons/a/ab/Test.png",
        source_hash: hash,
        commons_metadata_sha256: hash,
        retrieved_at: "2026-10-01T00:00:00Z",
        license_id: "CC-BY-SA-4.0",
        license_name: "CC BY-SA 4.0",
        license_url: "https://creativecommons.org/licenses/by-sa/4.0/",
        author: "Synthetic test author",
        attribution: "",
        credit: "",
        attribution_links: [],
        transformation: "Synthetic fixture; resized",
        licence_metadata: {
          LicenseShortName: { value: "CC BY-SA 4.0" },
          LicenseUrl: {
            value: "https://creativecommons.org/licenses/by-sa/4.0/",
          },
          Artist: { value: "Synthetic test author" },
        },
      },
    },
    identities: {
      "statsbomb:1": {
        asset: hash,
        wikidata_id: "Q123",
        wikidata_url: "https://www.wikidata.org/wiki/Q123",
        wikidata_metadata_sha256: hash,
        wikidata_image_title: "Test.png",
        match_status: "verified",
        match_method: "manual_metadata_review",
        profiles: ["statsbomb-1-1-1"],
        name: "Test Person",
        source_files: [{ path: "statsbomb/fixture.json", sha256: hash }],
      },
    },
    legacy: {},
  };
  const manual = {
    version: 1,
    players: {
      "statsbomb:1": {
        status: "verified",
        wikidata_id: "Q123",
        reason: "Synthetic metadata test",
        reviewer: "Test",
        reviewed_at: "2026-10-01",
        evidence_urls: [
          "https://example.org/test",
          "https://www.wikidata.org/wiki/Q123",
        ],
      },
    },
  };
  write("config/player-images/overrides.json", manual);
  write("config/v11-sources.json", {
    files: [{ path: "statsbomb/fixture.json", sha256: hash }],
  });
  write("artifacts/v11/public/index.json", {
    profiles: [{ id: "statsbomb-1-1-1" }],
  });
  write("artifacts/player-images/review.json", [
    {
      identity: "statsbomb:1",
      asset: hash,
      wikidata_metadata_sha256: { Q123: hash },
      match: {
        status: "verified",
        qid: "Q123",
        candidates: [{ qid: "Q123", images: ["Test.png"] }],
      },
    },
  ]);
  writeFileSync(
    join(root, "artifacts/player-images/assets", hash + ".webp"),
    bytes,
  );
  write("artifacts/player-images/manifest.json", manifest);
  return {
    root,
    manifest,
    manual,
    write,
    clean: () => rmSync(root, { recursive: true, force: true }),
  };
}
test("verified images publish, validate and reproduce offline", () => {
  const f = fixture();
  try {
    publishImages(f.root);
    validatePublishedImages(f.root, join(f.root, "apps/web/public"));
    const first = readFileSync(
      join(f.root, "apps/web/src/lib/player-image-reference.json"),
    );
    publishImages(f.root);
    assert.deepEqual(
      readFileSync(
        join(f.root, "apps/web/src/lib/player-image-reference.json"),
      ),
      first,
    );
  } finally {
    f.clean();
  }
});
test("official deed URL is validated against its canonical licence", () => {
  const f = fixture();
  try {
    f.manifest.assets[hash].licence_metadata.LicenseUrl.value += "deed.en";
    f.write("artifacts/player-images/manifest.json", f.manifest);
    validateImages(f.root);
  } finally {
    f.clean();
  }
});
test("static credits escape source text and remain bilingual without scripts", () => {
  const f = fixture();
  try {
    f.manifest.assets[hash].author = "<script>alert(1)</script>";
    const en = creditsHtml(f.manifest, "en");
    assert.ok(en.includes("&lt;script&gt;"));
    assert.ok(!en.includes("<script>"));
    assert.ok(en.includes('lang="en"'));
    assert.ok(creditsHtml(f.manifest, "nl").includes('lang="nl"'));
  } finally {
    f.clean();
  }
});
for (const [name, mutate] of [
  [
    "unverified identity",
    (f) => (f.manifest.identities["statsbomb:1"].match_status = "likely"),
  ],
  [
    "missing identity snapshot",
    (f) => delete f.manifest.identities["statsbomb:1"].wikidata_metadata_sha256,
  ],
  [
    "wrong identity snapshot",
    (f) =>
      (f.manifest.identities["statsbomb:1"].wikidata_metadata_sha256 =
        "0".repeat(64)),
  ],
  [
    "unreviewed P18 image",
    (f) =>
      (f.manifest.identities["statsbomb:1"].wikidata_image_title = "Other.png"),
  ],
  [
    "unsafe licence",
    (f) => (f.manifest.assets[hash].license_id = "CC-BY-NC-4.0"),
  ],
  [
    "forged licence URL",
    (f) =>
      (f.manifest.assets[hash].license_url = "https://example.org/license"),
  ],
  [
    "commercial image source",
    (f) =>
      (f.manifest.assets[hash].original_image_url =
        "https://example.org/Test.png"),
  ],
  [
    "wrong provider mapping",
    (f) => (f.manifest.identities["statsbomb:1"].profiles = ["wyscout-1-1-1"]),
  ],
  [
    "hidden legacy name join",
    (f) =>
      (f.manifest.legacy["00000000-0000-0000-0000-000000000000"] =
        "statsbomb:1"),
  ],
  ["path traversal", (f) => (f.manifest.assets[hash].path = "../image.webp")],
  [
    "unpinned player source",
    (f) =>
      (f.manifest.identities["statsbomb:1"].source_files[0].sha256 = "0".repeat(
        64,
      )),
  ],
  [
    "agency provenance despite licence label",
    (f) =>
      (f.manifest.assets[hash].licence_metadata.Credit = { value: "Reuters" }),
  ],
  [
    "hash mismatch",
    (f) =>
      writeFileSync(
        join(f.root, "artifacts/player-images/assets", hash + ".webp"),
        "bad",
      ),
  ],
])
  test(`publication rejects ${name}`, () => {
    const f = fixture();
    try {
      mutate(f);
      f.write("artifacts/player-images/manifest.json", f.manifest);
      assert.throws(() => validateImages(f.root));
    } finally {
      f.clean();
    }
  });
test("manual exclusion blocks previously published imagery", () => {
  const f = fixture();
  try {
    f.manual.players["statsbomb:1"] = {
      status: "excluded",
      reason: "withdraw image",
    };
    f.write("config/player-images/overrides.json", f.manual);
    assert.throws(() => validateImages(f.root), /excluded/);
  } finally {
    f.clean();
  }
});
test("unlisted public images are rejected before copy and in export", () => {
  const f = fixture();
  try {
    publishImages(f.root);
    writeFileSync(
      join(f.root, "apps/web/public/players/images/rogue.webp"),
      bytes,
    );
    assert.throws(() => publishImages(f.root), /unlisted/);
    assert.throws(
      () => validatePublishedImages(f.root, join(f.root, "apps/web/public")),
      /unexpected/,
    );
  } finally {
    f.clean();
  }
});

test("different reviewed QIDs share one asset while retaining independent identity evidence", () => {
  const f = fixture();
  try {
    const secondHash = "b".repeat(64);
    f.manifest.identities["statsbomb:2"] = {
      ...f.manifest.identities["statsbomb:1"],
      wikidata_id: "Q456",
      wikidata_url: "https://www.wikidata.org/wiki/Q456",
      wikidata_metadata_sha256: secondHash,
      profiles: ["statsbomb-1-1-2"],
    };
    f.manual.players["statsbomb:2"] = {
      ...f.manual.players["statsbomb:1"],
      wikidata_id: "Q456",
      evidence_urls: [
        "https://example.org/second",
        "https://www.wikidata.org/wiki/Q456",
      ],
    };
    f.write("config/player-images/overrides.json", f.manual);
    f.write("artifacts/player-images/manifest.json", f.manifest);
    f.write("artifacts/v11/public/index.json", {
      profiles: [{ id: "statsbomb-1-1-1" }, { id: "statsbomb-1-1-2" }],
    });
    f.write("artifacts/player-images/review.json", [
      {
        identity: "statsbomb:1",
        asset: hash,
        wikidata_metadata_sha256: { Q123: hash },
        match: {
          status: "verified",
          qid: "Q123",
          candidates: [{ qid: "Q123", images: ["Test.png"] }],
        },
      },
      {
        identity: "statsbomb:2",
        asset: hash,
        wikidata_metadata_sha256: { Q456: secondHash },
        match: {
          status: "verified",
          qid: "Q456",
          candidates: [{ qid: "Q456", images: ["Test.png"] }],
        },
      },
    ]);
    publishImages(f.root);
    validatePublishedImages(f.root, join(f.root, "apps/web/public"));
    assert.equal(Object.keys(validateImages(f.root).assets).length, 1);
    f.manifest.identities["statsbomb:2"].wikidata_metadata_sha256 = hash;
    f.write("artifacts/player-images/manifest.json", f.manifest);
    assert.throws(
      () => validateImages(f.root),
      /per-identity image provenance/,
    );
  } finally {
    f.clean();
  }
});
