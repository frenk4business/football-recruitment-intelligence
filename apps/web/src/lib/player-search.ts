import type { ProfileIndex, ProfileIndexEntry } from "./profile-contracts.ts";
export type PlayerFilters = {
  q: string;
  provider: string;
  competition: string;
  season: string;
  team: string;
  role: string;
  minutes: string;
  kind: string;
  page: number;
  profile: string;
  compare: string;
};
export const defaults: PlayerFilters = {
  q: "",
  provider: "",
  competition: "",
  season: "",
  team: "",
  role: "",
  minutes: "450",
  kind: "",
  page: 1,
  profile: "",
  compare: "",
};
export const normalizeName = (s: string) =>
  s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
export function readFilters(
  params: URLSearchParams,
  index: ProfileIndex,
): PlayerFilters {
  const state = { ...defaults };
  for (const key of [
    "q",
    "provider",
    "competition",
    "season",
    "team",
    "role",
    "minutes",
    "kind",
    "profile",
    "compare",
  ] as const)
    state[key] = (params.get(key) ?? state[key]).slice(0, 100);
  if (!["", "statsbomb", "wyscout"].includes(state.provider))
    state.provider = "";
  if (!index.scopes.some((s) => s.competition_key === state.competition))
    state.competition = "";
  if (!index.scopes.some((s) => s.season === state.season)) state.season = "";
  if (!Object.hasOwn(index.teams, state.team)) state.team = "";
  if (
    !index.profiles.some(
      (p) => p.role === state.role || p.role_family === state.role,
    )
  )
    state.role = "";
  if (!["450", "600", "900"].includes(state.minutes)) state.minutes = "450";
  if (!["", "common", "similarity"].includes(state.kind)) state.kind = "";
  if (!index.profiles.some((p) => p.id === state.profile)) state.profile = "";
  if (
    !index.profiles.some((p) => p.id === state.compare) ||
    state.compare === state.profile
  )
    state.compare = "";
  const page = Number(params.get("page"));
  state.page =
    Number.isSafeInteger(page) && page >= 1
      ? Math.min(page, Math.ceil(index.profiles.length / 50))
      : 1;
  return state;
}
export function filterProfiles(
  index: ProfileIndex,
  state: PlayerFilters,
  names?: Map<string, string>,
): ProfileIndexEntry[] {
  const scopes = new Map(index.scopes.map((s) => [s.id, s]));
  const tokens = normalizeName(state.q.trim()).split(/\s+/).filter(Boolean);
  return index.profiles.filter((p) => {
    const scope = scopes.get(p.scope)!;
    return (
      (!state.provider || p.provider === state.provider) &&
      (!state.competition || scope.competition_key === state.competition) &&
      (!state.season || scope.season === state.season) &&
      (!state.team || p.teams.includes(state.team)) &&
      (!state.role || p.role === state.role || p.role_family === state.role) &&
      p.minutes >= Number(state.minutes) &&
      (!state.kind ||
        (state.kind === "common"
          ? p.capabilities.common
          : p.capabilities.similarity)) &&
      tokens.every((t) =>
        (
          names?.get(p.id) ??
          normalizeName(
            [
              p.name,
              ...p.teams.map((id) => index.teams[id]),
              scope.competition,
              scope.season,
            ].join(" "),
          )
        ).includes(t),
      )
    );
  });
}
export function filterURL(state: PlayerFilters): string {
  const params = new URLSearchParams();
  for (const key of Object.keys(defaults) as (keyof PlayerFilters)[])
    if (state[key] !== defaults[key]) params.set(key, String(state[key]));
  const search = params.toString();
  return search ? `?${search}` : "";
}
export function detailPath(id: string) {
  if (!/^(statsbomb|wyscout)-\d+-\d+-\d+$/.test(id))
    throw new Error("Invalid profile identity");
  return `/data/v11/profiles/${id.split("-").at(-1)!.slice(-2).padStart(2, "0")}/${id}.json`;
}
