import test from "node:test";
import assert from "node:assert/strict";
import { filterPlayers, metric } from "../src/lib/explorer.ts";
import { copy, route, sections } from "../src/lib/content.ts";
test("missing metric differs from zero", () => {
  assert.equal(metric(null, "en", "Not available"), "Not available");
  assert.equal(metric(0, "en", "Not available"), "0");
});
test("search handles accents and team context", () => {
  const rows = [
    { name: "TEST FIXTURE José", team: "Test A" },
    { name: "TEST FIXTURE Alex", team: "Test B" },
  ];
  assert.equal(filterPlayers(rows, "Test A", "jose").length, 1);
  assert.equal(filterPlayers(rows, "Test B", "jose").length, 0);
});
test("language switch preserves section", () => {
  for (const s of sections) {
    assert.ok(route("nl", s).startsWith("/nl/"));
    assert.ok(copy.en.nav[s]);
    assert.ok(copy.nl.nav[s]);
  }
  assert.equal(route("en", "home"), "/");
  assert.equal(route("nl", "explorer"), "/nl/explorer/");
});
test("manual dictionaries have equivalent keys and phase counts", () => {
  assert.deepEqual(Object.keys(copy.en).sort(), Object.keys(copy.nl).sort());
  assert.equal(copy.en.phases.length, 5);
  assert.equal(copy.nl.phases.length, 5);
  assert.equal(copy.nl.methodSections.length, copy.en.methodSections.length);
});
