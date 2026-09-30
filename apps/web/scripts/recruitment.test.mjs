import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  rankCandidates,
  scenarioStability,
  encodeScenario,
  decodeScenario,
  paretoFrontier,
} from "../src/lib/recruitment.ts";
const load = (name) =>
  JSON.parse(
    readFileSync(
      new URL(`../../../artifacts/phase4/${name}`, import.meta.url),
      "utf8",
    ),
  );
const index = load("public/index.json"),
  fixtures = load("reference_cases.json");
function equivalent(actual, expected, path = "") {
  if (typeof expected === "number") {
    assert.ok(
      Math.abs(actual - expected) <= 1e-7,
      `${path}: ${actual} vs ${expected}`,
    );
    return;
  }
  if (Array.isArray(expected)) {
    assert.equal(actual.length, expected.length, path);
    expected.forEach((x, i) => equivalent(actual[i], x, `${path}[${i}]`));
    return;
  }
  if (expected && typeof expected === "object") {
    assert.deepEqual(
      Object.keys(actual).sort(),
      Object.keys(expected).sort(),
      path,
    );
    for (const [k, v] of Object.entries(expected))
      equivalent(actual[k], v, `${path}.${k}`);
    return;
  }
  assert.equal(actual, expected, path);
}
for (const fixture of fixtures.cases)
  test(`Python/browser recruitment parity: ${fixture.name}`, () => {
    const scenario = fixture.scenario,
      bootstrap = load(
        `public/bootstrap/${scenario.target_role.replaceAll("/", "-")}.json`,
      );
    equivalent(
      rankCandidates(index.players, scenario, index.method),
      fixture.result,
    );
    equivalent(
      scenarioStability(index.players, scenario, index.method, bootstrap),
      fixture.stability,
    );
    const restored = decodeScenario(encodeScenario(scenario, index), index);
    equivalent(
      rankCandidates(index.players, restored, index.method),
      fixture.result,
    );
  });
test("Scenario URLs reject unsupported data and malformed assumptions", () => {
  const good = encodeScenario(fixtures.cases[0].scenario, index);
  for (const bad of [
    good.replace("v=1", "v=9"),
    `${good}&age=20`,
    `${good}&min=400`,
    `${good}&e=NaN`,
    `${good}&q=0:1:150:1:0:0:0`,
    `${good}&role=GK`,
    `${good}&ref=unknown`,
    `${good}&q=0:1:70:1:0:0:0,0:1:70:1:0:0:0`,
  ])
    assert.throws(() => decodeScenario(bad, index));
});
test("Pareto preserves ties and ignores dominated candidates", () => {
  assert.deepEqual(
    [...paretoFrontier({ a: [0, 2], b: [2, 0], c: [3, 3], d: [0, 2] })],
    ["a", "b", "d"],
  );
});

test("Recruitment translations expose the same controls and explanations", async () => {
  const { recruitmentCopy } = await import("../src/lib/recruitment-copy.ts");
  assert.deepEqual(
    Object.keys(recruitmentCopy.en).sort(),
    Object.keys(recruitmentCopy.nl).sort(),
  );
  assert.equal(recruitmentCopy.en.methodDefinitions.length, 6);
  assert.equal(recruitmentCopy.nl.methodDefinitions.length, 6);
});
