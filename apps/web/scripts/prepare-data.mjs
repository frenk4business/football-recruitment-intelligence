import { cp, mkdir, readFile, rm } from "node:fs/promises";
const src = new URL("../../../artifacts/", import.meta.url);
const dest = new URL("../public/data/", import.meta.url);
const coverage = JSON.parse(
  await readFile(new URL("data_coverage.json", src), "utf8"),
);
if (coverage.validation_status !== "passed" || coverage.providers.length !== 2)
  throw new Error(
    "Build requires validated real data artifacts. Run make data-bootstrap.",
  );
await rm(dest, { recursive: true, force: true });
await mkdir(dest, { recursive: true });
for (const name of [
  "data_coverage.json",
  "sources.json",
  "matches.json",
  "competitions.json",
  "metrics.json",
  "explorer",
])
  await cp(new URL(name, src), new URL(name, dest), { recursive: true });
await cp(new URL("phase2/public/", src), new URL("phase2/", dest), {
  recursive: true,
});
console.log("Prepared validated aggregate artifacts.");
