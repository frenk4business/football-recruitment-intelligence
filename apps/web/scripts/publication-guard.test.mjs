import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import Ajv from "ajv/dist/2020.js";
import { validatePublication } from "./publication-guard.mjs";
const validate = new Ajv().compile({
  type: "object",
  properties: { version: { const: "v1" } },
  required: ["version"],
  additionalProperties: false,
});
const record = (data) => ({
  source: "artifacts/example.json",
  path: "data/example.json",
  bytes: data.length,
  sha256: createHash("sha256").update(data).digest("hex"),
});
const good = Buffer.from('{"version":"v1"}');
test("publication guard rejects changed bytes even when JSON still parses", () => {
  validatePublication(record(good), good, validate);
  assert.throws(
    () =>
      validatePublication(
        record(good),
        Buffer.from('{"version":"v2"}'),
        validate,
      ),
    /hash mismatch/,
  );
});
test("publication guard rejects unknown contracts, extra raw fields and invalid JSON", () => {
  for (const text of [
    '{"version":"v2"}',
    '{"version":"v1","events":[]}',
    "null",
    "{",
  ]) {
    const data = Buffer.from(text);
    assert.throws(() => validatePublication(record(data), data, validate));
  }
});
test("publication guard rejects escaped paths and over-budget payloads", () => {
  for (const field of ["source", "path"])
    for (const path of [
      "../secret.json",
      "/tmp/secret.json",
      "data/../secret.json",
      "data//secret.json",
    ])
      assert.throws(
        () =>
          validatePublication(
            { ...record(good), [field]: path },
            good,
            validate,
          ),
        /Unsafe/,
      );
  const huge = Buffer.alloc(3_000_001);
  assert.throws(
    () => validatePublication(record(huge), huge, validate),
    /Oversized/,
  );
});
