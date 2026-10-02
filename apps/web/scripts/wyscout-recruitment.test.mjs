import { performance } from "node:perf_hooks";
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  defaultNative,
  rankNative,
  validateNative,
  nativeURL,
} from "../src/lib/wyscout-recruitment.ts";
import { filterProfiles, defaults } from "../src/lib/player-search.ts";
const read = (p) =>
  JSON.parse(
    readFileSync(
      new URL(`../../../artifacts/v12/public/${p}`, import.meta.url),
    ),
  );
const registry = read("recruitment/index.json");
const leagues = registry.leagues.map((l) =>
  read(`recruitment/${l.scope}.json`),
);
test("native scenarios isolate all five leagues, supported roles, clubs and registries", () => {
  for (const league of leagues) {
    const scenario = defaultNative(league);
    const result = rankNative(league, leagues, scenario);
    assert(result.length > 20);
    assert(
      result.every(
        (r) =>
          r.player.scope === league.scope &&
          !r.player.teams.includes(scenario.club),
      ),
    );
    assert.deepEqual(validateNative(scenario, league, registry), scenario);
    const wider = rankNative(league, leagues, { ...scenario, wider: true });
    assert(wider.length > result.length);
    assert(wider.some((r) => r.player.scope !== league.scope));
    for (const r of result)
      assert.equal(
        wider.find((w) => w.player.id === r.player.id).distance,
        r.distance,
      );
    assert.throws(() =>
      validateNative(
        { ...scenario, feature_registry_version: "statsbomb" },
        league,
        registry,
      ),
    );
    assert.throws(() =>
      validateNative({ ...scenario, role: "CB" }, league, registry),
    );
    assert(nativeURL(scenario).includes("dataset=wyscout"));
  }
});
test("requirements are versioned native rates; unsupported, duplicated and nonfinite values rejected", () => {
  const league = leagues[0],
    s = defaultNative(league),
    r = {
      feature: registry.features[0].id,
      value: 2,
      direction: "at_least",
      weight: 1,
    };
  const ranked = rankNative(league, leagues, { ...s, requirements: [r] });
  assert(ranked.length);
  assert(
    ranked
      .filter((x) => x.player.features[r.feature] >= 2)
      .every((x) => x.distance === 0),
  );
  for (const requirements of [
    [{ ...r, value: NaN }],
    [{ ...r, feature: "pressures_per90" }],
    [r, r],
    [{ ...r, weight: -1 }],
  ])
    assert.throws(() =>
      validateNative({ ...s, requirements }, league, registry),
    );
});
test("performance index filters country and recruitment without enabling metadata", () => {
  const index = read("index.json");
  const result = filterProfiles(index, {
    ...defaults,
    country: "France",
    kind: "recruitment",
  });
  assert(result.length > 100);
  assert(
    result.every(
      (p) => p.provider === "wyscout" && p.capabilities_v12.recruitment,
    ),
  );
  assert.equal(
    filterProfiles(index, { ...defaults, kind: "translation" }).length,
    0,
  );
  const started = performance.now();
  for (let i = 0; i < 100; i++)
    filterProfiles(index, { ...defaults, q: "a", country: "France" });
  assert((performance.now() - started) / 100 < 100);
});
