import type {
  NativeLeague,
  NativePlayer,
  NativeRegistry,
} from "./expansion-contracts.ts";
export const nativeVersion = "recruitment-fit-wyscout-v1";
export const featureVersion = "wyscout-recruitment-features-v1";
export type NativeRequirement = {
  feature: string;
  value: number;
  direction: "near" | "at_least" | "at_most";
  weight: number;
};
export type NativeScenario = {
  version: typeof nativeVersion;
  provider: "wyscout";
  scope: string;
  competition: string;
  season: string;
  club: string;
  role: string;
  feature_registry_version: typeof featureVersion;
  wider: boolean;
  requirements: NativeRequirement[];
};
export function defaultNative(league: NativeLeague): NativeScenario {
  const club = league.clubs[0],
    role = club.roles[0].role;
  return {
    version: nativeVersion,
    provider: "wyscout",
    scope: league.scope,
    competition: league.competition_id,
    season: league.season_id,
    club: club.id,
    role,
    feature_registry_version: featureVersion,
    wider: false,
    requirements: [],
  };
}
export function validateNative(
  value: unknown,
  league: NativeLeague,
  registry: NativeRegistry,
): NativeScenario {
  const fallback = defaultNative(league);
  if (!value || typeof value !== "object") throw new Error("Invalid scenario");
  const s = value as NativeScenario;
  if (
    s.version !== nativeVersion ||
    s.provider !== "wyscout" ||
    s.feature_registry_version !== featureVersion ||
    s.scope !== league.scope ||
    s.competition !== league.competition_id ||
    s.season !== league.season_id ||
    !league.clubs.some(
      (c) => c.id === s.club && c.roles.some((r) => r.role === s.role),
    ) ||
    typeof s.wider !== "boolean" ||
    !Array.isArray(s.requirements) ||
    s.requirements.length > registry.features.length
  )
    throw new Error("Incompatible scenario");
  const seen = new Set<string>();
  for (const r of s.requirements) {
    if (
      !r ||
      !registry.features.some((f) => f.id === r.feature) ||
      seen.has(r.feature) ||
      !Number.isFinite(r.value) ||
      r.value < 0 ||
      r.value > 1000 ||
      !Number.isFinite(r.weight) ||
      r.weight < 0.1 ||
      r.weight > 5 ||
      !["near", "at_least", "at_most"].includes(r.direction)
    )
      throw new Error("Invalid requirement");
    seen.add(r.feature);
  }
  return {
    ...fallback,
    club: s.club,
    role: s.role,
    wider: s.wider,
    requirements: s.requirements.map((r) => ({
      feature: r.feature,
      value: r.value,
      weight: r.weight,
      direction: r.direction,
    })),
  };
}
export function nativeURL(s: NativeScenario) {
  return `?dataset=wyscout&scope=${encodeURIComponent(s.scope)}&scenario=${encodeURIComponent(JSON.stringify(s))}`;
}
export function rankNative(
  league: NativeLeague,
  all: NativeLeague[],
  scenario: NativeScenario,
) {
  const role = league.clubs
    .find((c) => c.id === scenario.club)
    ?.roles.find((r) => r.role === scenario.role);
  if (!role) return [];
  const requirements = scenario.requirements.length
    ? scenario.requirements
    : Object.entries(role.median).map(([feature, value]) => ({
        feature,
        value,
        direction: "near" as const,
        weight: 1,
      }));
  const candidates = (scenario.wider ? all : [league]).flatMap(
    (l) => l.players,
  );
  const seen = new Set<string>();
  return candidates
    .filter(
      (p) =>
        p.role === scenario.role &&
        !p.teams.includes(scenario.club) &&
        (scenario.wider || p.scope === league.scope) &&
        !seen.has(p.id) &&
        Boolean(seen.add(p.id)),
    )
    .map((player) => {
      let sum = 0,
        weight = 0;
      const contributions = requirements.map((r) => {
        const delta = player.features[r.feature] - r.value;
        const error =
          r.direction === "at_least"
            ? Math.min(0, delta)
            : r.direction === "at_most"
              ? Math.max(0, delta)
              : delta;
        const w = league.weights[scenario.role][r.feature] * r.weight;
        const loss = (error / league.scales[scenario.role][r.feature]) ** 2 * w;
        sum += loss;
        weight += w;
        return {
          feature: r.feature,
          observed: player.features[r.feature],
          target: r.value,
          loss,
        };
      });
      return {
        player,
        distance: weight ? Math.sqrt(sum / weight) : null,
        contributions,
      };
    })
    .filter(
      (
        r,
      ): r is {
        player: NativePlayer;
        distance: number;
        contributions: typeof r.contributions;
      } => r.distance !== null,
    )
    .sort(
      (a, b) =>
        a.distance - b.distance || a.player.id.localeCompare(b.player.id),
    );
}
