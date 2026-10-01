import test from "node:test";
import { URLSearchParams } from "node:url";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { performance } from "node:perf_hooks";
import {
  defaults,
  detailPath,
  filterProfiles,
  filterURL,
  normalizeName,
  readFilters,
} from "../src/lib/player-search.ts";
const index = JSON.parse(
  readFileSync(
    new URL("../../../artifacts/v11/public/index.json", import.meta.url),
  ),
);
test("full production index exposes distinct provider identities and all supported filters", () => {
  assert(index.profiles.length > 3000);
  for (const state of [
    { provider: "wyscout" },
    { competition: "premier-league" },
    { season: "2017/2018" },
    { team: index.profiles[0].teams[0] },
    { role: "DEF" },
    { role: "CB" },
    { minutes: "900" },
    { kind: "common" },
    { kind: "similarity" },
  ]) {
    const found = filterProfiles(index, { ...defaults, ...state });
    assert(found.length > 0);
    assert(found.length < index.profiles.length);
    for (const p of found) {
      if (state.provider) assert.equal(p.provider, state.provider);
      if (state.competition)
        assert.equal(
          index.scopes.find((s) => s.id === p.scope).competition_key,
          state.competition,
        );
      if (state.season)
        assert.equal(
          index.scopes.find((s) => s.id === p.scope).season,
          state.season,
        );
      if (state.team) assert(p.teams.includes(state.team));
      if (state.role)
        assert(p.role === state.role || p.role_family === state.role);
      if (state.minutes) assert(p.minutes >= 900);
      if (state.kind) assert(p.capabilities[state.kind]);
    }
  }
});
test("search is accent-insensitive, token-based and never uses names as identity", () => {
  const fixture = {
    ...index,
    profiles: [
      { ...index.profiles[0], id: "wyscout-1-1-1", name: "José Example" },
      { ...index.profiles[0], id: "wyscout-1-1-2", name: "José Example" },
    ],
  };
  const rows = filterProfiles(fixture, { ...defaults, q: "example jose" });
  assert.equal(rows.length, 2);
  assert.notEqual(rows[0].id, rows[1].id);
  assert.equal(normalizeName("Néstor"), "nestor");
});
test("URL roundtrip preserves filters and sanitises unsupported paths and values", () => {
  const state = {
    ...defaults,
    q: "François & Alex",
    provider: "wyscout",
    minutes: "600",
    kind: "common",
    profile: index.profiles[0].id,
  };
  assert.deepEqual(
    readFilters(new URLSearchParams(filterURL(state)), index),
    state,
  );
  const bad = readFilters(
    new URLSearchParams(
      "profile=../../secret&compare=https://other.test/&minutes=0&provider=bad&role=invented&page=NaN",
    ),
    index,
  );
  assert.deepEqual(bad, defaults);
  assert.throws(() => detailPath("../../secret"));
  assert.match(
    detailPath(index.profiles[0].id),
    /^\/data\/v11\/profiles\/\d{2}\//,
  );
});
test("5,000-row searches remain bounded and deterministic", () => {
  const large = {
    ...index,
    profiles: Array.from({ length: 5000 }, (_, i) => ({
      ...index.profiles[i % index.profiles.length],
      id: `wyscout-1-1-${i}`,
    })),
  };
  const names = new Map(
    large.profiles.map((p) => [p.id, normalizeName(p.name)]),
  );
  const state = { ...defaults, provider: "wyscout", minutes: "900", q: "a" };
  const start = performance.now();
  const results = Array.from({ length: 25 }, () =>
    filterProfiles(large, state, names),
  );
  assert.deepEqual(results[0], results.at(-1));
  assert.equal(results[0].slice(0, 50).length, 50);
  assert(
    (performance.now() - start) / 25 < 100,
    "Typical filter exceeds 100 ms budget",
  );
});
