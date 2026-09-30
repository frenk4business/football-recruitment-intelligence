import { readFileSync } from "node:fs";
import { join } from "node:path";
import type {
  Coverage,
  MatchSummary,
  Source,
  MetricDefinition,
} from "./contracts";
function load<T>(name: string): T {
  return JSON.parse(
    readFileSync(join(process.cwd(), "../../artifacts", name), "utf8"),
  ) as T;
}
export const coverage = () => load<Coverage>("data_coverage.json");
export const matches = () => load<MatchSummary[]>("matches.json");
export const sources = () => load<Source[]>("sources.json");
export const metrics = () => load<MetricDefinition[]>("metrics.json");
export const quality = () =>
  load<{ null_counts: { lineups: { minutes: number } } }>("validation.json");

export const dnaIndex = () =>
  load<import("./contracts").DNAIndex>("phase2/public/index.json");
export const dnaRegistry = () =>
  load<import("./contracts").FeatureDefinition[]>(
    "phase2/public/features.json",
  );
export const dnaEvaluation = () =>
  load<import("./contracts").DNAEvaluation>("phase2/public/evaluation.json");
