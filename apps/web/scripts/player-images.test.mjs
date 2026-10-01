import test from "node:test";
import assert from "node:assert/strict";
import { initials, providerIdentity, photo } from "../src/lib/player-images.ts";
for (const [name, expected] of [
  ["Lauren Hemp", "LH"],
  ["Pelé", "P"],
  ["Jean-Pierre van der Berg", "JB"],
  ["Éva O’Connor", "ÉC"],
  ["", "?"],
  ["  123! ", "?"],
  ["K. de Bruyne", "KB"],
]) {
  test(`deterministic initials: ${name || "empty"}`, () => {
    assert.equal(initials(name), expected);
    assert.equal(initials(name), initials(name));
  });
}
test("image identities never join on names or across providers", () => {
  assert.equal(providerIdentity("statsbomb-37-90-123"), "statsbomb:123");
  assert.equal(providerIdentity("wyscout:123"), "wyscout:123");
  assert.equal(providerIdentity("Lauren Hemp"), null);
  const index = {
    version: "player-images-v1",
    identities: { "statsbomb:123": "hash" },
    legacy: {},
    assets: { hash: { path: "players/images/hash.webp" } },
  };
  assert.equal(
    photo(index, "statsbomb-37-90-123")?.path,
    "players/images/hash.webp",
  );
  assert.equal(photo(index, "wyscout:123"), null);
  assert.equal(photo(null, "statsbomb:123"), null);
});
