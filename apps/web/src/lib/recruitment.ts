import spec from "./recruitment-spec.json" with { type: "json" };
import type {
  RecruitmentScenario,
  RecruitmentRequirement,
  RecruitmentConstraints,
  RecruitmentCandidate,
  RecruitmentResult,
  RecruitmentContribution,
  RecruitmentIndex,
  RecruitmentBootstrap,
} from "./contracts";

export type Requirement = Required<RecruitmentRequirement>;
export type Scenario = Required<
  Omit<RecruitmentScenario, "requirements" | "hard_constraints">
> & {
  requirements: Requirement[];
  hard_constraints: Required<RecruitmentConstraints>;
};
const families: Record<string, string> = spec.families;
const compareId = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0);
export const familyOf = (feature: string) => families[feature];
export const activeRequirements = (s: Scenario) =>
  s.requirements
    .filter((r) => r.preference !== "neutral")
    .sort((a, b) => compareId(a.feature_id, b.feature_id));
export const newRequirement = (id: string): Requirement => ({
  requirement_id: id,
  type: "style_preference",
  source: "user_defined",
  feature_id: id,
  preference: "neutral",
  value: 75,
  weight: 1,
  hard_constraint: false,
});
export function defaultScenario(index: RecruitmentIndex): Scenario {
  return {
    version: "requirements-v1",
    fit_method_version: "recruitment-fit-v1",
    club_id: (
      index.clubs.find((c) => c.name === "Chelsea FCW") ?? index.clubs[0]
    ).club_id,
    season: "2023/2024",
    target_role: "FB/WB",
    mode: "find",
    replacement_player_id: null,
    requirements: [],
    hard_constraints: {
      source: "user_defined",
      minimum_minutes: 900,
      minimum_neighbor_stability: 0,
      exclude_same_club: true,
      candidate_team_id: null,
      provider: "statsbomb",
      comparison_cohort: "wsl_2023_24",
    },
    family_weights: {},
    translation_mode: "observed_only",
    created_from: "custom",
  };
}
export function replaceProfile(s: Scenario, p: RecruitmentCandidate): Scenario {
  if (!p.eligible || !p.role) throw new Error("Unsupported reference profile");
  return {
    ...s,
    mode: "replace",
    replacement_player_id: p.player_id,
    target_role: p.role as Scenario["target_role"],
    family_weights: {},
    created_from: "replacement",
    requirements: Object.keys(families)
      .sort(compareId)
      .map((f) => ({
        ...newRequirement(f),
        preference: "exact",
        value: p.percentiles[f],
        source: "replacement_player",
        type: "target_profile",
      })),
  };
}
export function mismatch(
  value: number,
  target: number,
  preference: Requirement["preference"],
) {
  const loss = spec.loss[preference],
    delta = value - target;
  return loss === "ignore"
    ? 0
    : loss === "shortfall"
      ? Math.max(0, -delta)
      : loss === "excess"
        ? Math.max(0, delta)
        : Math.abs(delta);
}
function weights(
  req: Requirement[],
  s: Scenario,
  method: string,
  factors: Record<string, number> = {},
) {
  const result: Record<string, number> = {};
  for (const r of req)
    result[r.feature_id] =
      r.weight *
      (s.family_weights[families[r.feature_id]] ?? 1) *
      (factors[r.feature_id] ?? 1);
  if (method === "family_rms") {
    const totals: Record<string, number> = {};
    for (const r of req)
      totals[families[r.feature_id]] =
        (totals[families[r.feature_id]] ?? 0) + result[r.feature_id];
    for (const r of req)
      result[r.feature_id] =
        (result[r.feature_id] / totals[families[r.feature_id]]) *
        (s.family_weights[families[r.feature_id]] ?? 1);
  }
  return result;
}
export function distance(
  values: Record<string, number>,
  req: Requirement[],
  s: Scenario,
  method: string,
  factors: Record<string, number> = {},
) {
  const w = weights(req, s, method, factors);
  const contributions: RecruitmentContribution[] = req.map((r) => {
    const value = values[r.feature_id];
    if (!Number.isFinite(value) || value < 0 || value > 100)
      throw new Error("Invalid percentile");
    const gap = mismatch(value, r.value, r.preference);
    return {
      feature_id: r.feature_id,
      family: families[r.feature_id],
      candidate: value,
      target: r.value,
      mismatch: gap,
      effective_weight: w[r.feature_id],
      squared_contribution: w[r.feature_id] * gap ** spec.power,
      share: 0,
      source: r.source,
    };
  });
  const total = contributions.reduce(
      (sum, c) => sum + c.squared_contribution,
      0,
    ),
    denominator = Object.values(w).reduce((a, b) => a + b, 0);
  for (const c of contributions)
    c.share = total ? c.squared_contribution / total : 0;
  return {
    distance: denominator ? (total / denominator) ** (1 / spec.power) : 0,
    contributions,
  };
}
function rankKey(value: number) {
  const scale = 10 ** spec.ranking_round_decimals;
  return Math.floor(value * scale + 0.5) / scale;
}
export function filterCandidates(players: RecruitmentCandidate[], s: Scenario) {
  const eligible: RecruitmentCandidate[] = [],
    exclusions: RecruitmentResult["exclusions"] = [],
    req = activeRequirements(s);
  for (const p of [...players].sort((a, b) =>
    compareId(a.player_id, b.player_id),
  )) {
    const reasons = p.eligible ? [] : [...p.exclusions],
      h = s.hard_constraints;
    if (p.role !== s.target_role) reasons.push("wrong_role");
    if (p.minutes < h.minimum_minutes) reasons.push("below_minutes");
    if (
      h.minimum_neighbor_stability > 0 &&
      (p.neighbor_stability === null ||
        p.neighbor_stability < h.minimum_neighbor_stability)
    )
      reasons.push("below_evidence_threshold");
    if (h.exclude_same_club && p.team_ids.includes(s.club_id))
      reasons.push("same_club_excluded");
    if (h.candidate_team_id && !p.team_ids.includes(h.candidate_team_id))
      reasons.push("candidate_team_filter");
    if (p.player_id === s.replacement_player_id)
      reasons.push("replacement_reference");
    for (const r of req) {
      if (!(r.feature_id in p.percentiles))
        reasons.push("missing_required_feature");
      else if (
        r.hard_constraint &&
        mismatch(p.percentiles[r.feature_id], r.value, r.preference) >
          spec.epsilon
      )
        reasons.push(`hard_feature_constraint:${r.feature_id}`);
    }
    if (reasons.length)
      exclusions.push({
        player_id: p.player_id,
        reasons: [...new Set(reasons)].sort(compareId),
      });
    else eligible.push(p);
  }
  return { eligible, exclusions };
}
export function paretoFrontier(losses: Record<string, number[]>) {
  const entries = Object.entries(losses);
  return new Set(
    entries
      .filter(
        ([id, v]) =>
          !entries.some(
            ([other, x]) =>
              other !== id &&
              x.every((a, i) => a <= v[i] + spec.epsilon) &&
              x.some((a, i) => a < v[i] - spec.epsilon),
          ),
      )
      .map(([id]) => id),
  );
}
export function rankCandidates(
  players: RecruitmentCandidate[],
  s: Scenario,
  method: string,
): RecruitmentResult {
  const { eligible, exclusions } = filterCandidates(players, s),
    req = activeRequirements(s);
  if (!req.length || !eligible.length)
    return {
      version: "recruitment-fit-v1",
      status: !req.length ? "no_requirements" : "no_candidates",
      eligible_count: eligible.length,
      active_requirements: req.length,
      frontier_count: 0,
      rankings: [],
      exclusions,
    };
  const frontier = paretoFrontier(
    Object.fromEntries(
      eligible.map((p) => [
        p.player_id,
        req.map((r) =>
          mismatch(p.percentiles[r.feature_id], r.value, r.preference),
        ),
      ]),
    ),
  );
  const ranked = eligible
    .map((p) => ({
      player_id: p.player_id,
      ...distance(p.percentiles, req, s, method),
    }))
    .sort(
      (a, b) =>
        rankKey(a.distance) - rankKey(b.distance) ||
        compareId(a.player_id, b.player_id),
    );
  return {
    version: "recruitment-fit-v1",
    status: "ok",
    eligible_count: eligible.length,
    active_requirements: req.length,
    frontier_count: frontier.size,
    exclusions,
    rankings: ranked.map((row, i) => {
      const groups: Record<string, number> = {};
      for (const c of row.contributions)
        groups[c.family] = (groups[c.family] ?? 0) + c.share;
      return {
        ...row,
        rank: i + 1,
        family_contributions: groups,
        frontier: frontier.has(row.player_id),
        strong_matches: [...row.contributions]
          .sort(
            (a, b) =>
              a.mismatch - b.mismatch || compareId(a.feature_id, b.feature_id),
          )
          .slice(0, 3)
          .map((c) => c.feature_id),
        main_mismatches: [...row.contributions]
          .sort(
            (a, b) =>
              b.squared_contribution - a.squared_contribution ||
              compareId(a.feature_id, b.feature_id),
          )
          .filter((c) => c.mismatch > spec.epsilon)
          .slice(0, 3)
          .map((c) => c.feature_id),
      };
    }),
  };
}
export type RankSummary = {
  samples: number;
  mean_jaccard: number | null;
  players: Record<
    string,
    { top_k_inclusion: number; rank_p10: number; rank_p90: number }
  >;
};
export type Stability = { weight: RankSummary; profile: RankSummary | null };
function quantile(values: number[], q: number) {
  const sorted = [...values].sort((a, b) => a - b),
    at = (sorted.length - 1) * q,
    lower = Math.floor(at);
  return sorted[lower] + (sorted[Math.ceil(at)] - sorted[lower]) * (at - lower);
}
function rankSummary(reference: string[], draws: string[][]): RankSummary {
  if (!reference.length) return { samples: 0, mean_jaccard: null, players: {} };
  const k = Math.min(spec.top_k, reference.length),
    top = new Set(reference.slice(0, k)),
    ranks: Record<string, number[]> = {},
    overlaps: number[] = [];
  for (const id of reference) ranks[id] = [];
  for (const draw of draws) {
    const selected = new Set(draw.slice(0, k)),
      overlap = [...top].filter((id) => selected.has(id)).length;
    overlaps.push(overlap / (top.size + selected.size - overlap));
    draw.forEach((id, i) => ranks[id].push(i + 1));
  }
  return {
    samples: draws.length,
    mean_jaccard: overlaps.reduce((a, b) => a + b, 0) / draws.length,
    players: Object.fromEntries(
      Object.entries(ranks).map(([id, values]) => [
        id,
        {
          top_k_inclusion: values.filter((v) => v <= k).length / values.length,
          rank_p10: quantile(values, spec.rank_quantiles[0]),
          rank_p90: quantile(values, spec.rank_quantiles[1]),
        },
      ]),
    ),
  };
}
export function scenarioStability(
  players: RecruitmentCandidate[],
  s: Scenario,
  method: string,
  bootstrap?: RecruitmentBootstrap,
): Stability {
  const { eligible } = filterCandidates(players, s),
    req = activeRequirements(s);
  if (!eligible.length || !req.length)
    return { weight: rankSummary([], []), profile: null };
  const values = Object.fromEntries(
    eligible.map((p) => [p.player_id, p.percentiles]),
  );
  const order = (
    vectors: Record<string, Record<string, number>>,
    factors: Record<string, number> = {},
  ) =>
    Object.keys(vectors)
      .map((id) => ({
        id,
        distance: rankKey(
          distance(vectors[id], req, s, method, factors).distance,
        ),
      }))
      .sort((a, b) => a.distance - b.distance || compareId(a.id, b.id))
      .map((r) => r.id);
  const reference = order(values),
    draws: string[][] = [];
  let state = spec.seed;
  for (let i = 0; i < spec.weight_samples; i++) {
    const factors: Record<string, number> = {};
    for (const r of req) {
      state =
        (Math.imul(spec.lcg.multiplier, state) + spec.lcg.increment) >>> 0;
      factors[r.feature_id] =
        spec.weight_range[0] +
        ((spec.weight_range[1] - spec.weight_range[0]) * state) /
          spec.lcg.modulus;
    }
    draws.push(order(values, factors));
  }
  let profile: RankSummary | null = null;
  if (bootstrap) {
    if (
      bootstrap.role !== s.target_role ||
      eligible.some((p) => !bootstrap.player_ids.includes(p.player_id))
    )
      throw new Error("Bootstrap cohort mismatch");
    const positions = Object.fromEntries(
      bootstrap.player_ids.map((id, i) => [id, i]),
    );
    profile = rankSummary(
      reference,
      bootstrap.values.map((sample) =>
        order(
          Object.fromEntries(
            eligible.map((p) => [
              p.player_id,
              Object.fromEntries(
                bootstrap.feature_ids.map((f, j) => [
                  f,
                  sample[positions[p.player_id]][j] / bootstrap.scale,
                ]),
              ),
            ]),
          ),
        ),
      ),
    );
  }
  return { weight: rankSummary(reference, draws), profile };
}
const preferences = ["exact", "minimum", "maximum", "neutral"] as const;
const sources = [
  "user_defined",
  "observed_club_context",
  "replacement_player",
  "derived_roster_gap",
] as const;
const types = ["style_preference", "target_profile", "club_context"] as const;
export function encodeScenario(s: Scenario, index: RecruitmentIndex) {
  const p = new URLSearchParams({
    v: "1",
    club: s.club_id,
    role: s.target_role,
  });
  if (s.mode === "replace") p.set("ref", s.replacement_player_id ?? "");
  if (s.requirements.length)
    p.set(
      "q",
      s.requirements
        .map((r) =>
          [
            index.features.findIndex((f) => f.id === r.feature_id),
            preferences.indexOf(r.preference),
            r.value,
            r.weight,
            Number(r.hard_constraint),
            sources.indexOf(r.source),
            types.indexOf(r.type),
          ].join(":"),
        )
        .join(","),
    );
  const h = s.hard_constraints;
  if (h.minimum_minutes !== 900) p.set("min", String(h.minimum_minutes));
  if (h.minimum_neighbor_stability)
    p.set("e", String(h.minimum_neighbor_stability));
  if (!h.exclude_same_club) p.set("own", "1");
  if (h.candidate_team_id) p.set("team", h.candidate_team_id);
  if (Object.keys(s.family_weights).length)
    p.set(
      "w",
      Object.entries(s.family_weights)
        .sort(([a], [b]) => compareId(a, b))
        .map(([k, v]) => `${k}:${v}`)
        .join(","),
    );
  return p.toString();
}
export function decodeScenario(
  search: string,
  index: RecruitmentIndex,
): Scenario {
  const p = new URLSearchParams(search),
    s = defaultScenario(index);
  if (!p.size) return s;
  if (search.length > 5000 || p.get("v") !== "1")
    throw new Error("Unsupported scenario URL");
  const allowed = new Set([
    "v",
    "club",
    "role",
    "ref",
    "q",
    "min",
    "e",
    "own",
    "team",
    "w",
  ]);
  if ([...p.keys()].some((k) => !allowed.has(k) || p.getAll(k).length > 1))
    throw new Error("Unknown or duplicate scenario fields");
  if (
    !index.clubs.some((c) => c.club_id === p.get("club")) ||
    ![...index.roles, "AM"].includes(p.get("role") ?? "")
  )
    throw new Error("Unsupported club or role");
  s.club_id = p.get("club")!;
  s.target_role = p.get("role") as Scenario["target_role"];
  if (p.has("ref")) {
    const ref = index.players.find((r) => r.player_id === p.get("ref"));
    if (
      !ref?.eligible ||
      !ref.team_ids.includes(s.club_id) ||
      ref.role !== s.target_role
    )
      throw new Error("Unsupported replacement reference");
    s.mode = "replace";
    s.replacement_player_id = ref.player_id;
    s.created_from = "replacement";
  }
  const requirements = (p.get("q") ?? "").split(",").filter(Boolean);
  if (requirements.length > 18) throw new Error("Too many requirements");
  s.requirements = requirements.map((text) => {
    const tokens = text.split(":");
    if (
      tokens.length !== 7 ||
      tokens.some((t) => t === "" || !Number.isFinite(Number(t)))
    )
      throw new Error("Invalid requirement");
    const [feature, pref, value, weight, hard, source, type] =
      tokens.map(Number);
    if (
      !Number.isInteger(feature) ||
      !index.features[feature] ||
      !preferences[pref] ||
      !sources[source] ||
      !types[type] ||
      value < 0 ||
      value > 100 ||
      ![1, 2, 3].includes(weight) ||
      ![0, 1].includes(hard) ||
      (hard && ![1, 2].includes(pref))
    )
      throw new Error("Invalid requirement value");
    return {
      ...newRequirement(index.features[feature].id),
      preference: preferences[pref],
      value,
      weight: weight as 1 | 2 | 3,
      hard_constraint: Boolean(hard),
      source: sources[source],
      type: types[type],
    };
  });
  if (
    new Set(s.requirements.map((r) => r.feature_id)).size !==
    s.requirements.length
  )
    throw new Error("Duplicate feature");
  const min = Number(p.get("min") ?? 900),
    evidence = Number(p.get("e") ?? 0);
  if (
    !Number.isInteger(min) ||
    min < 900 ||
    min > 10000 ||
    !Number.isFinite(evidence) ||
    evidence < 0 ||
    evidence > 1 ||
    (p.has("own") && p.get("own") !== "1")
  )
    throw new Error("Invalid constraints");
  if (p.has("team") && !index.clubs.some((c) => c.club_id === p.get("team")))
    throw new Error("Unknown candidate team");
  s.hard_constraints = {
    ...s.hard_constraints,
    minimum_minutes: min,
    minimum_neighbor_stability: evidence,
    exclude_same_club: !p.has("own"),
    candidate_team_id: p.get("team"),
  };
  const seen = new Set<string>();
  for (const entry of (p.get("w") ?? "").split(",").filter(Boolean)) {
    const [family, value, ...extra] = entry.split(":");
    if (
      extra.length ||
      !Object.values(families).includes(family) ||
      seen.has(family) ||
      ![1, 2, 3].includes(Number(value))
    )
      throw new Error("Invalid family weight");
    seen.add(family);
    s.family_weights[family] = Number(value) as 1 | 2 | 3;
  }
  return s;
}
