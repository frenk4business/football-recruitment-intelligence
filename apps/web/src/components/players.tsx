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
  detailPath,
  filterProfiles,
  filterURL,
  normalizeName,
  readFilters,
  type PlayerFilters,
} from "@/lib/player-search";
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
  const [state, setState] = useState<PlayerFilters>(defaults);
  const [retry, setRetry] = useState(0);
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
      `${state.profile}:${state.compare}` !== lastOpened.current
    ) {
      detailRef.current?.focus();
      lastOpened.current = `${state.profile}:${state.compare}`;
    }
    if (!state.profile) lastOpened.current = "";
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
      new Map(
        index.profiles.map((p) => [
          p.id,
          normalizeName(
            [
              p.name,
              ...p.teams.map((id) => index.teams[id]),
              index.scopes.find((scope) => scope.id === p.scope)?.competition,
              index.scopes.find((scope) => scope.id === p.scope)?.season,
            ].join(" "),
          ),
        ]),
      ),
    [index],
  );
  const results = useMemo(
    () => filterProfiles(index, state, names),
    [index, state, names],
  );
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
  const open = (id: string) => update({ profile: id, compare: "" }, true);
  const reset = () =>
    update({ ...defaults, profile: state.profile, compare: state.compare });
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
  return (
    <div className="player-database">
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
      <details className="player-filter-panel">
        <summary>{locale === "en" ? "Filters" : "Filters"}</summary>
        <div className="player-filters">
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
                    onClick={() => open(p.id)}
                    aria-label={`${c.open}: ${p.name}, ${context(p)}`}
                  >
                    {p.name}
                  </button>
                  <p className="small">{context(p)}</p>
                  <p className="small">
                    {roleName(p.role ?? p.role_family)} · {number(p.minutes)}{" "}
                    {c.minutes.toLowerCase()}
                  </p>
                </div>
                <div className="profile-row-actions">
                  <button
                    disabled={p.id === state.profile}
                    onClick={() =>
                      selected ? update({ compare: p.id }, true) : open(p.id)
                    }
                  >
                    {selected ? c.compare : c.open}
                  </button>
                </div>
              </li>
            ))}
          </ul>
          {!rows.length && <p className="notice">{c.empty}</p>}
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
                  onClick={() => update({ profile: "", compare: "" }, true)}
                >
                  {locale === "en"
                    ? "Back to results"
                    : "Terug naar resultaten"}
                </button>
              </div>
              <p>{context(selected)}</p>
              <p className="small">
                {roleName(selected.role ?? selected.role_family)} ·{" "}
                {number(selected.minutes)} {c.minutes.toLowerCase()}
              </p>
              {(profile?.error || registry?.error || comparison?.error) && (
                <p role="alert">
                  {c.error}{" "}
                  <button onClick={() => setRetry(retry + 1)}>{c.retry}</button>
                </p>
              )}
              {(!profile?.data || !registry?.data) &&
                !profile?.error &&
                !registry?.error && <p role="status">{c.loading}</p>}
              {profile?.data && registry?.data && (
                <>
                  <p className="small">
                    {profile.data.appearances} {c.appearances.toLowerCase()} ·{" "}
                    {profile.data.first_date} – {profile.data.last_date}.{" "}
                    {selected.teams.length > 1 && c.shared}
                  </p>
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
                  {state.compare && (
                    <div className="notice">
                      <h3>
                        {c.comparison}:{" "}
                        {comparison?.data?.identity.name ??
                          byId.get(state.compare)?.name}
                      </h3>
                      <p>
                        {byId.has(state.compare) &&
                          context(byId.get(state.compare)!)}
                      </p>
                      <button onClick={() => update({ compare: "" })}>
                        {c.removeComparison}
                      </button>
                      {!comparison?.data && !comparison?.error && (
                        <p role="status">{c.loading}</p>
                      )}
                    </div>
                  )}
                  <h3>{c.common}</h3>
                  <p>{c.commonNote}</p>
                  {profile.data.common ? (
                    comparison?.data && !comparison.data.common ? (
                      <p className="notice">{c.unsupported}</p>
                    ) : (
                      metrics(
                        registry.data.features,
                        profile.data.common,
                        comparison?.data?.common ?? undefined,
                      )
                    )
                  ) : (
                    <p className="notice">
                      {state.compare ? c.unsupported : c.unavailableCommon}
                    </p>
                  )}
                  <p className="small">{c.disclaimer}</p>
                  <details className="native-details">
                    <summary>
                      {c.native} · {profile.data.version}
                    </summary>
                    <p>{c.nativeNote}</p>
                    {metrics(
                      registry.data[selected.provider],
                      profile.data.native,
                      comparison?.data?.identity.provider === selected.provider
                        ? comparison.data.native
                        : undefined,
                    )}
                  </details>
                  <details>
                    <summary>{c.neighbours}</summary>
                    <p>{c.neighboursNote}</p>
                    {profile.data.neighbours.length ? (
                      <ol className="profile-neighbours">
                        {profile.data.neighbours.map((n) => (
                          <li key={n.id}>
                            <button onClick={() => update({ compare: n.id })}>
                              {byId.get(n.id)?.name}
                            </button>{" "}
                            · {c.distance}: {number(n.distance, 3)}
                            <small>
                              {byId.has(n.id) && context(byId.get(n.id)!)}
                            </small>
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p>{c.noNeighbours}</p>
                    )}
                  </details>
                  <details>
                    <summary>{c.source}</summary>
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
                      <a href={route(locale, "player-dna")}>{c.dna} ↗</a>
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
