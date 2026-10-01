"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { fetchArtifact } from "@/lib/artifact";
import type { Locale } from "@/lib/content";
import { route } from "@/lib/content";
import type {
  ProfileDetail,
  ProfileIndex,
  ProfileIndexEntry,
  ProfileMetricDefinition,
  ProfileRegistry,
} from "@/lib/profile-contracts";
import {
  defaults,
  normalizeName,
  detailPath,
  filterProfiles,
  filterURL,
  profileSearchText,
  readFilters,
  type PlayerFilters,
} from "@/lib/player-search";
import { ProfileStyle } from "./profile-style";
import { playersCopy } from "@/lib/players-copy";
const repo =
  "https://github.com/frenk4business/football-recruitment-intelligence";
const providerName = (s: string) =>
  s === "statsbomb" ? "StatsBomb" : "Pappalardo / Wyscout";
function useData<T>(path: string | null, retry: number) {
  const [state, setState] = useState<{
    path: string;
    data?: T;
    error?: boolean;
  }>();
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    setState({ path });
    fetchArtifact<T>(path, controller.signal)
      .then((data) => setState({ path, data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ path, error: true });
      });
    return () => controller.abort();
  }, [path, retry]);
  return state?.path === path ? state : undefined;
}
export function Players({ locale }: { locale: Locale }) {
  const c = playersCopy[locale];
  const [retry, setRetry] = useState(0);
  const data = useData<ProfileIndex>("/data/v11/index.json", retry);
  if (!data?.data)
    return (
      <div
        className={data?.error ? "notice" : "profile-loading"}
        role={data?.error ? "alert" : "status"}
      >
        {data?.error ? c.error : c.loading}
        {data?.error && (
          <button onClick={() => setRetry(retry + 1)}>{c.retry}</button>
        )}
      </div>
    );
  return <Database locale={locale} index={data.data} />;
}
function Database({ locale, index }: { locale: Locale; index: ProfileIndex }) {
  const c = playersCopy[locale];
  const [state, setState] = useState<PlayerFilters>(() =>
    typeof window === "undefined"
      ? defaults
      : readFilters(new URLSearchParams(window.location.search), index),
  );
  const [retry, setRetry] = useState(0);
  const [comparisonQuery, setComparisonQuery] = useState("");
  const detailRef = useRef<HTMLElement>(null);
  const lastOpened = useRef("");
  useEffect(() => {
    const restore = () =>
      setState(readFilters(new URLSearchParams(window.location.search), index));
    restore();
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, [index]);
  useEffect(() => {
    if (
      state.profile &&
      `${state.profile}:${state.compare}:${state.compare2}` !==
        lastOpened.current
    ) {
      detailRef.current?.focus();
      lastOpened.current = `${state.profile}:${state.compare}:${state.compare2}`;
    }
    if (!state.profile && lastOpened.current) {
      const previous = lastOpened.current.split(":")[0];
      document
        .querySelector<HTMLButtonElement>(`button[data-profile="${previous}"]`)
        ?.focus();
      lastOpened.current = "";
    }
    const link = document.querySelector<HTMLAnchorElement>("a.language");
    if (link)
      link.href =
        route(locale === "en" ? "nl" : "en", "players") + filterURL(state);
  }, [state, locale]);
  const update = (patch: Partial<PlayerFilters>, push = false) => {
    const next = { ...state, ...patch };
    setState(next);
    window.history[push ? "pushState" : "replaceState"](
      null,
      "",
      window.location.pathname + filterURL(next),
    );
  };
  const names = useMemo(
    () =>
      new Map(index.profiles.map((p) => [p.id, profileSearchText(index, p)])),
    [index],
  );
  const results = useMemo(() => {
    const found = filterProfiles(index, state, names);
    return state.sort === "minutes"
      ? found.toSorted(
          (a, b) => b.minutes - a.minutes || a.name.localeCompare(b.name),
        )
      : found;
  }, [index, state, names]);
  const pages = Math.max(1, Math.ceil(results.length / 50));
  const page = Math.min(state.page, pages);
  const rows = results.slice((page - 1) * 50, page * 50);
  const byId = useMemo(
    () => new Map(index.profiles.map((p) => [p.id, p])),
    [index],
  );
  const scopes = useMemo(
    () => new Map(index.scopes.map((s) => [s.id, s])),
    [index],
  );
  const selected = byId.get(state.profile);
  const profile = useData<ProfileDetail>(
    selected ? detailPath(selected.id) : null,
    retry,
  );
  const comparison = useData<ProfileDetail>(
    state.compare && selected ? detailPath(state.compare) : null,
    retry,
  );
  const comparison2 = useData<ProfileDetail>(
    state.compare2 && selected ? detailPath(state.compare2) : null,
    retry,
  );
  const addComparison = (id: string) => {
    if (
      !id ||
      id === state.profile ||
      id === state.compare ||
      id === state.compare2
    )
      return;
    if (!state.compare) update({ compare: id }, true);
    else if (!state.compare2) update({ compare2: id }, true);
  };
  const registry = useData<ProfileRegistry>(
    selected ? "/data/v11/registry.json" : null,
    retry,
  );
  const number = (n: number | null | undefined, digits = 1) =>
    n == null
      ? c.unavailable
      : n.toLocaleString(locale, { maximumFractionDigits: digits });
  const roleName = (key: string) => c.roles[key as keyof typeof c.roles] ?? key;
  const context = (p: ProfileIndexEntry) =>
    `${providerName(p.provider)} · ${scopes.get(p.scope)?.competition} ${scopes.get(p.scope)?.season} · ${p.teams.map((t) => index.teams[t]).join(" / ")}`;
  const open = (id: string) =>
    update({ profile: id, compare: "", compare2: "" }, true);
  const reset = () =>
    update({
      ...defaults,
      profile: state.profile,
      compare: state.compare,
      compare2: state.compare2,
    });
  const optionCounts = (get: (p: ProfileIndexEntry) => string[]) => {
    const counts = new Map<string, number>();
    index.profiles.forEach((p) =>
      get(p).forEach((v) => counts.set(v, (counts.get(v) ?? 0) + 1)),
    );
    return counts;
  };
  const providers = optionCounts((p) => [p.provider]);
  const competitions = optionCounts((p) => [
    scopes.get(p.scope)!.competition_key,
  ]);
  const seasons = optionCounts((p) => [scopes.get(p.scope)!.season]);
  const teams = optionCounts((p) => p.teams);
  const roles = optionCounts((p) => [
    ...new Set([p.role_family, ...(p.role ? [p.role] : [])]),
  ]);
  const choices = (
    key: keyof PlayerFilters,
    label: string,
    options: Map<string, number>,
    name: (v: string) => string,
  ) => (
    <label>
      <span id={`filter-label-${key}`}>{label}</span>
      <select
        aria-labelledby={`filter-label-${key}`}
        value={String(state[key])}
        onChange={(e) => update({ [key]: e.target.value, page: 1 })}
      >
        <option value="">{c.all}</option>
        {[...options]
          .sort((a, b) => name(a[0]).localeCompare(name(b[0]), locale))
          .map(([value, n]) => (
            <option key={value} value={value}>
              {name(value)} ({number(n, 0)})
            </option>
          ))}
      </select>
    </label>
  );
  const metrics = (
    definitions: ProfileMetricDefinition[],
    a: Record<string, number | null>,
    b?: Record<string, number | null>,
    third?: Record<string, number | null>,
  ) => (
    <div className="table-wrap">
      <table className="profile-metrics">
        <caption className="sr-only">
          {c.comparison} · {selected?.name}
        </caption>
        <thead>
          <tr>
            <th scope="col">{c.metric}</th>
            <th scope="col">{selected?.name}</th>
            {b && <th scope="col">{comparison?.data?.identity.name}</th>}
            {third && <th scope="col">{comparison2?.data?.identity.name}</th>}
          </tr>
        </thead>
        <tbody>
          {definitions.map((d) => (
            <tr key={d.id}>
              <th scope="row">
                <details>
                  <summary>
                    {d[locale]}
                    {d.unit === "per90" ? " / 90" : ""}
                  </summary>
                  <p>{locale === "en" ? d.definition_en : d.definition_nl}</p>
                </details>
              </th>
              <td>
                {d.unit === "fraction" && a[d.id] != null
                  ? `${number(a[d.id]! * 100)}%`
                  : number(a[d.id])}
              </td>
              {b && (
                <td>
                  {d.unit === "fraction" && b[d.id] != null
                    ? `${number(b[d.id]! * 100)}%`
                    : number(b[d.id])}
                </td>
              )}
              {third && (
                <td>
                  {d.unit === "fraction" && third[d.id] != null
                    ? `${number(third[d.id]! * 100)}%`
                    : number(third[d.id])}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
  return (
    <div className={`player-database ${selected ? "profile-is-open" : ""}`}>
      <label className="player-search">
        {c.search}
        <input
          type="search"
          value={state.q}
          placeholder={c.searchHint}
          maxLength={100}
          onChange={(e) => update({ q: e.target.value, page: 1 })}
        />
      </label>
      <div className="player-filters primary-filters">
        {" "}
        {choices("provider", c.provider, providers, providerName)}
        {choices(
          "competition",
          c.competition,
          competitions,
          (key) =>
            index.scopes.find((s) => s.competition_key === key)!.competition,
        )}
        {choices("season", c.season, seasons, (v) => v)}
        {choices("team", c.team, teams, (key) => index.teams[key])}
        {choices("role", c.role, roles, roleName)}
        <label>
          <span id="filter-label-minutes">{c.evidence}</span>
          <select
            aria-labelledby="filter-label-minutes"
            value={state.minutes}
            onChange={(e) => update({ minutes: e.target.value, page: 1 })}
          >
            {[450, 600, 900].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </div>
      <details className="player-filter-panel">
        <summary>{locale === "en" ? "More filters" : "Meer filters"}</summary>
        <div className="player-filters">
          {" "}
          <label>
            <span id="filter-label-kind">{c.kind}</span>
            <select
              aria-labelledby="filter-label-kind"
              value={state.kind}
              onChange={(e) => update({ kind: e.target.value, page: 1 })}
            >
              <option value="">
                {c.native} ({number(index.counts.native_profiles, 0)})
              </option>
              <option value="common">
                {c.common} ({number(index.counts.common_profiles, 0)})
              </option>
              <option value="similarity">
                {c.similarity} ({number(index.counts.similarity_profiles, 0)})
              </option>
            </select>
          </label>
        </div>
      </details>
      <div className="profile-actions filter-summary">
        <button type="button" onClick={reset}>
          {c.clear}
        </button>
        <p className="small">
          {[
            state.q,
            state.provider && providerName(state.provider),
            state.competition &&
              index.scopes.find((s) => s.competition_key === state.competition)
                ?.competition,
            state.season,
            state.team && index.teams[state.team],
            state.role && roleName(state.role),
            `≥${state.minutes} min`,
            state.kind && c[state.kind === "common" ? "common" : "similarity"],
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
        <a href={route(locale, "methodology")}>{c.methods} ↗</a>
      </div>
      <div className={`players-workspace ${selected ? "has-selection" : ""}`}>
        <section className="player-results">
          {" "}
          <div className="profile-actions">
            <h2 id="player-results-heading">{c.title}</h2>
            <label className="result-sort">
              <span className="sr-only">
                {locale === "en" ? "Sort results" : "Resultaten sorteren"}
              </span>
              <select
                value={state.sort}
                onChange={(e) => update({ sort: e.target.value, page: 1 })}
              >
                <option value="name">
                  {locale === "en" ? "Name" : "Naam"}
                </option>
                <option value="minutes">{c.minutes} ↓</option>
              </select>
            </label>
            <p
              role="status"
              aria-live="polite"
              data-testid="player-result-count"
            >
              {number(results.length, 0)} {c.results}
            </p>
          </div>
          <ul className="profile-list" aria-labelledby="player-results-heading">
            {rows.map((p) => (
              <li
                key={p.id}
                className={p.id === state.profile ? "is-selected" : undefined}
              >
                <div>
                  <button
                    className="profile-name"
                    data-profile={p.id}
                    onClick={() => open(p.id)}
                    aria-label={`${c.open}: ${p.name}, ${context(p)}`}
                  >
                    {p.name}
                  </button>
                  <p className="small">
                    {p.teams.map((t) => index.teams[t]).join(" / ")} ·{" "}
                    {roleName(p.role ?? p.role_family)}
                  </p>
                  <p className="small">
                    {scopes.get(p.scope)?.competition} ·{" "}
                    {scopes.get(p.scope)?.season} · {number(p.minutes)} min ·{" "}
                    {providerName(p.provider)}
                  </p>
                </div>
                {selected && (
                  <div className="profile-row-actions">
                    <button
                      disabled={
                        [state.profile, state.compare, state.compare2].includes(
                          p.id,
                        ) || Boolean(state.compare && state.compare2)
                      }
                      onClick={() => addComparison(p.id)}
                    >
                      {selected ? c.compare : c.open}
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
          {!rows.length && (
            <p className="notice">
              {c.empty}{" "}
              {locale === "en"
                ? "Try a shorter search or clear the filters."
                : "Probeer een kortere zoekterm of wis de filters."}
            </p>
          )}
          <nav className="profile-pagination" aria-label={c.page}>
            <button
              disabled={page === 1}
              onClick={() => update({ page: page - 1 }, true)}
            >
              {c.previous}
            </button>
            <span>
              {c.page} {page} {c.of} {pages}
            </span>
            <button
              disabled={page === pages}
              onClick={() => update({ page: page + 1 }, true)}
            >
              {c.next}
            </button>
          </nav>
        </section>
        <div className="player-profile-pane">
          {" "}
          {selected && (
            <section
              id="profile-detail"
              className="profile-detail"
              ref={detailRef}
              tabIndex={-1}
              aria-label={`${c.open}: ${selected.name}`}
            >
              <div className="profile-actions">
                <h2>{selected.name}</h2>
                <button
                  onClick={() =>
                    update({ profile: "", compare: "", compare2: "" }, true)
                  }
                >
                  {locale === "en"
                    ? "Back to results"
                    : "Terug naar resultaten"}
                </button>
              </div>
              <p>
                {selected.teams.map((t) => index.teams[t]).join(" / ")} ·{" "}
                {roleName(selected.role ?? selected.role_family)} ·{" "}
                {scopes.get(selected.scope)?.competition} ·{" "}
                {scopes.get(selected.scope)?.season}
              </p>
              <p className="small">
                {number(selected.minutes)} {c.minutes.toLowerCase()} ·{" "}
                {providerName(selected.provider)}
              </p>
              {(profile?.error ||
                registry?.error ||
                comparison?.error ||
                comparison2?.error) && (
                <p role="alert">
                  {c.error}{" "}
                  <button onClick={() => setRetry(retry + 1)}>{c.retry}</button>
                </p>
              )}
              {(!profile?.data || !registry?.data) &&
                !profile?.error &&
                !registry?.error && (
                  <p className="detail-skeleton" role="status">
                    {c.loading}
                  </p>
                )}
              {profile?.data && registry?.data && (
                <>
                  <p className="small">
                    {profile.data.appearances} {c.appearances.toLowerCase()} ·{" "}
                    {profile.data.first_date} – {profile.data.last_date}.{" "}
                    {selected.teams.length > 1 && c.shared}
                  </p>
                  <details
                    className="comparison-selection"
                    key={Boolean(state.compare || state.compare2).toString()}
                    open={Boolean(state.compare || state.compare2)}
                  >
                    <summary>
                      {locale === "en"
                        ? "Compare players · up to 3"
                        : "Spelers vergelijken · maximaal 3"}
                    </summary>
                    <div className="profile-actions">
                      <h3>{c.comparison}</h3>
                      <span className="small">
                        {1 +
                          Number(Boolean(state.compare)) +
                          Number(Boolean(state.compare2))}{" "}
                        / 3
                      </span>
                    </div>
                    <p className="small">
                      {locale === "en"
                        ? "Compare observed rates alongside each player's minutes. More is not necessarily better; no winner is assigned."
                        : "Vergelijk geobserveerde waarden en de minuten per speler. Meer is niet noodzakelijk beter; er wordt geen winnaar aangewezen."}
                    </p>
                    {[state.compare, state.compare2]
                      .filter(Boolean)
                      .map((id) => (
                        <div className="comparison-member" key={id}>
                          <span>
                            <strong>{byId.get(id)?.name}</strong>
                            <small>
                              {context(byId.get(id)!)} ·{" "}
                              {number(byId.get(id)?.minutes)} min
                            </small>
                          </span>
                          <button
                            onClick={() =>
                              update(
                                id === state.compare
                                  ? { compare: state.compare2, compare2: "" }
                                  : { compare2: "" },
                                true,
                              )
                            }
                            aria-label={`${c.removeComparison}: ${byId.get(id)?.name}`}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    {!(state.compare && state.compare2) && (
                      <div className="comparison-picker">
                        <label>
                          {locale === "en"
                            ? "Search comparison profiles"
                            : "Vergelijkingsprofielen zoeken"}
                          <input
                            type="search"
                            value={comparisonQuery}
                            onChange={(e) => setComparisonQuery(e.target.value)}
                          />
                        </label>
                        <label>
                          {locale === "en"
                            ? "Add a player to compare"
                            : "Voeg een speler toe om te vergelijken"}
                          <select
                            value=""
                            onChange={(e) => addComparison(e.target.value)}
                          >
                            <option value="">
                              {locale === "en"
                                ? "Select a profile…"
                                : "Selecteer een profiel…"}
                            </option>
                            {index.profiles
                              .filter(
                                (p) =>
                                  ![
                                    state.profile,
                                    state.compare,
                                    state.compare2,
                                  ].includes(p.id) &&
                                  (names.get(p.id) ?? "").includes(
                                    normalizeName(comparisonQuery),
                                  ),
                              )
                              .slice(0, 50)
                              .map((p) => (
                                <option key={p.id} value={p.id}>
                                  {p.name} · {scopes.get(p.scope)?.season} ·{" "}
                                  {providerName(p.provider)}
                                </option>
                              ))}
                          </select>
                        </label>
                        <small>
                          {locale === "en"
                            ? "Up to 50 choices. Search to narrow the list."
                            : "Maximaal 50 keuzes. Zoek om de lijst te verkleinen."}
                        </small>
                      </div>
                    )}
                    {((state.compare &&
                      !comparison?.data &&
                      !comparison?.error) ||
                      (state.compare2 &&
                        !comparison2?.data &&
                        !comparison2?.error)) && (
                      <p className="detail-skeleton" role="status">
                        {c.loading}
                      </p>
                    )}
                    <a href={route(locale, "methodology")}>{c.methods} ↗</a>
                  </details>
                  <nav
                    className="profile-sections"
                    aria-label={
                      locale === "en" ? "Profile sections" : "Profielonderdelen"
                    }
                  >
                    <a href="#profile-detail">
                      {locale === "en" ? "Overview" : "Overzicht"}
                    </a>
                    <a href="#playing-style">
                      {locale === "en" ? "Playing style" : "Speelstijl"}
                    </a>
                    <a href="#similar-players">
                      {locale === "en"
                        ? "Similar players"
                        : "Vergelijkbare spelers"}
                    </a>
                    <a href="#profile-quality">
                      {locale === "en" ? "Data quality" : "Datakwaliteit"}
                    </a>
                  </nav>
                  <section id="playing-style">
                    <h3>{locale === "en" ? "Playing style" : "Speelstijl"}</h3>
                    {profile.data.dna_player_id &&
                      selected.capabilities.validated_dna && (
                        <ProfileStyle
                          locale={locale}
                          id={profile.data.dna_player_id}
                        />
                      )}
                    <h4>{c.common}</h4>
                    <p className="small">
                      {locale === "en"
                        ? "Three harmonised metrics. Cross-provider rankings are unavailable because provider measurement differences remain detectable."
                        : "Drie geharmoniseerde kenmerken. Ranglijsten tussen providers ontbreken omdat meetverschillen aantoonbaar blijven."}
                    </p>
                    {profile.data.common ? (
                      (comparison?.data && !comparison.data.common) ||
                      (comparison2?.data && !comparison2.data.common) ? (
                        <p className="notice">{c.unsupported}</p>
                      ) : (
                        metrics(
                          registry.data.features,
                          profile.data.common,
                          comparison?.data?.common ?? undefined,
                          comparison2?.data?.common ?? undefined,
                        )
                      )
                    ) : (
                      <p className="notice">
                        {state.compare ? c.unsupported : c.unavailableCommon}
                      </p>
                    )}

                    <details
                      className="native-details"
                      open={
                        !state.compare && !selected.capabilities.validated_dna
                      }
                    >
                      <summary>
                        {locale === "en"
                          ? "Full provider profile"
                          : "Volledig providerprofiel"}
                      </summary>
                      <p>{c.nativeNote}</p>
                      {metrics(
                        registry.data[selected.provider],
                        profile.data.native,
                        comparison?.data?.identity.provider ===
                          selected.provider
                          ? comparison.data.native
                          : undefined,
                        comparison2?.data?.identity.provider ===
                          selected.provider
                          ? comparison2.data.native
                          : undefined,
                      )}
                    </details>
                  </section>
                  <section id="similar-players">
                    <h3>
                      {locale === "en"
                        ? "Similar players"
                        : "Vergelijkbare spelers"}
                    </h3>
                    {profile.data.neighbours.length ? (
                      <ol className="profile-neighbours">
                        {profile.data.neighbours.map((n) => (
                          <li key={n.id}>
                            <button
                              disabled={
                                [state.compare, state.compare2].includes(
                                  n.id,
                                ) || Boolean(state.compare && state.compare2)
                              }
                              onClick={() => addComparison(n.id)}
                            >
                              {byId.get(n.id)?.name}
                            </button>{" "}
                            <details>
                              <summary>{c.distance}</summary>
                              {number(n.distance, 3)}
                            </details>
                            <small>
                              {byId
                                .get(n.id)
                                ?.teams.map((t) => index.teams[t])
                                .join(" / ")}{" "}
                              · {number(byId.get(n.id)?.minutes)} min
                            </small>
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p>{c.noNeighbours}</p>
                    )}
                    <details>
                      <summary>
                        {locale === "en"
                          ? "How these profiles are compared"
                          : "Hoe deze profielen worden vergeleken"}
                      </summary>
                      <p>{c.neighboursNote}</p>
                    </details>
                  </section>
                  <details id="profile-quality">
                    <summary>
                      {locale === "en"
                        ? "Data quality & methodology"
                        : "Datakwaliteit & methodologie"}
                    </summary>{" "}
                    <div
                      className="profile-capabilities"
                      aria-label={c.capabilities}
                    >
                      {(
                        [
                          [c.native, true],
                          [c.common, selected.capabilities.common],
                          [c.similarity, selected.capabilities.similarity],
                          [c.dna, selected.capabilities.validated_dna],
                          [c.translation, selected.capabilities.translation],
                        ] as const
                      ).map(([label, available]) => (
                        <p key={label}>
                          {label}: <strong>{available ? c.yes : c.no}</strong>
                        </p>
                      ))}
                    </div>
                    <p>
                      {locale === "en"
                        ? "Recruitment: a separate validated WSL research cohort. Database eligibility alone does not establish recruitment eligibility."
                        : "Recruitment: een afzonderlijk gevalideerd WSL-onderzoekscohort. Beschikbaarheid in de database betekent niet automatisch geschiktheid voor recruitmentanalyse."}
                    </p>
                    <p>{c.disclaimer}</p>
                    <dl>
                      <dt>{c.nativeVersion}</dt>
                      <dd>{profile.data.version}</dd>
                      <dt>{c.commonVersion}</dt>
                      <dd>common-profile-v1</dd>
                      <dt>{c.broadRole}</dt>
                      <dd>
                        {profile.data.provider_role} / {selected.role_family}
                      </dd>
                      <dt>{c.source}</dt>
                      <dd className="break-text">
                        {profile.data.provenance.source_revision}
                      </dd>
                    </dl>
                    <p>{c.evidenceNote}</p>
                    <p>{c.rolesNote}</p>
                    <p>
                      <a href={profile.data.provenance.build_manifest}>
                        {c.build}
                      </a>{" "}
                      ·{" "}
                      <a
                        href={`${repo}/blob/${profile.data.provenance.code_commit}/config/v11-sources.json`}
                      >
                        {c.sourceManifest}
                      </a>
                    </p>
                    <p>
                      {selected.provider === "statsbomb" ? (
                        <a href="https://github.com/hudl/open-data">
                          StatsBomb Open Data
                        </a>
                      ) : (
                        <a href="https://doi.org/10.1038/s41597-019-0247-7">
                          Pappalardo et al. (2019), Soccer Match Event Dataset ·
                          CC BY 4.0
                        </a>
                      )}
                    </p>
                  </details>
                  {profile.data.dna_player_id && (
                    <p>
                      <a
                        href={
                          route(locale, "player-dna") +
                          "?player=" +
                          profile.data.dna_player_id
                        }
                      >
                        {c.dna} ↗
                      </a>
                    </p>
                  )}
                </>
              )}
            </section>
          )}
          {!selected && (
            <section className="profile-placeholder">
              <h2>
                {locale === "en" ? "Select a player" : "Selecteer een speler"}
              </h2>
              <p>
                {locale === "en"
                  ? "Search by name, club or competition. Open a profile to explore their playing style and compare similar players."
                  : "Zoek op naam, club of competitie. Open een profiel om de speelstijl te bekijken en vergelijkbare spelers te vergelijken."}
              </p>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
