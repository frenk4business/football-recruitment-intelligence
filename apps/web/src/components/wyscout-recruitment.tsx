"use client";
import { useEffect, useMemo, useState } from "react";
import type { Locale } from "@/lib/content";
import { route } from "@/lib/content";
import { fetchArtifact } from "@/lib/artifact";
import type { NativeLeague, NativeRegistry } from "@/lib/expansion-contracts";
import type { ProfileIndexEntry } from "@/lib/player-view";
import {
  defaultNative,
  nativeURL,
  rankNative,
  validateNative,
  type NativeScenario,
} from "@/lib/wyscout-recruitment";
import { PlayerAvatar } from "./player-avatar";

export function useExpansion<T>(path: string | null) {
  const [state, setState] = useState<{
    path: string;
    data?: T;
    error?: boolean;
  }>();
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    fetchArtifact<T>(path, controller.signal)
      .then((data) => setState({ path, data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ path, error: true });
      });
    return () => controller.abort();
  }, [path, attempt]);
  return {
    data: state?.path === path ? state.data : undefined,
    error: state?.path === path && state.error,
    retry: () => setAttempt((n) => n + 1),
  };
}
export const crossLeagueCopy = (locale: Locale) =>
  locale === "en"
    ? "Players from different leagues are compared on observed provider-native event profiles. No league-performance translation or adjustment for competition strength is applied. This is criteria matching, not expected fit at the target club."
    : "Spelers uit verschillende competities worden vergeleken op geobserveerde kenmerken van dezelfde provider. Er wordt geen competitievertaling of correctie voor competitiesterkte toegepast. Dit is een vergelijking met criteria, geen verwachte geschiktheid voor de doelclub.";
const roleLabel = (role: string, locale: Locale) =>
  ({
    DEF: locale === "en" ? "Defender" : "Verdediger",
    MID: locale === "en" ? "Midfielder" : "Middenvelder",
    FWD: locale === "en" ? "Forward" : "Aanvaller",
  })[role] ?? role;
function Loading({
  locale,
  error,
  retry,
}: {
  locale: Locale;
  error?: boolean;
  retry: () => void;
}) {
  return (
    <p role={error ? "alert" : "status"}>
      {error
        ? locale === "en"
          ? "Data could not be loaded."
          : "Gegevens konden niet worden geladen."
        : locale === "en"
          ? "Loading data…"
          : "Gegevens laden…"}
      {error && (
        <button onClick={retry}>{locale === "en" ? "Retry" : "Opnieuw"}</button>
      )}
    </p>
  );
}
export function WyscoutRecruitment({ locale }: { locale: Locale }) {
  const registry = useExpansion<NativeRegistry>(
    "/data/v12/recruitment/index.json",
  );
  const [scope, setScope] = useState(() =>
    typeof window !== "undefined"
      ? (new URLSearchParams(window.location.search).get("scope") ?? "")
      : "",
  );
  const summary =
    registry.data?.leagues.find((l) => l.scope === scope) ??
    registry.data?.leagues[0];
  const league = useExpansion<NativeLeague>(summary?.path ?? null);
  return (
    <section className="native-recruitment">
      <p className="eyebrow">
        {locale === "en"
          ? "Historical dataset · Men · 2017/18"
          : "Historische dataset · Mannen · 2017/18"}
      </p>
      <h2>
        {locale === "en"
          ? "Big Five recruitment"
          : "Recruitment in de Big Five"}
      </h2>
      <p>
        {locale === "en"
          ? "Explore observed player profiles across five European competitions."
          : "Verken geobserveerde spelersprofielen uit vijf Europese competities."}
      </p>
      {registry.data && (
        <div className="player-filters">
          <label>
            {locale === "en" ? "Competition" : "Competitie"}
            <select
              value={summary?.scope}
              onChange={(e) => {
                setScope(e.target.value);
                window.history.replaceState(
                  null,
                  "",
                  `?dataset=wyscout&scope=${e.target.value}`,
                );
              }}
            >
              {registry.data.leagues.map((l) => (
                <option key={l.scope} value={l.scope}>
                  {l.competition} · {l.season} · {l.clubs} clubs
                </option>
              ))}
            </select>
          </label>
        </div>
      )}
      {registry.data && league.data ? (
        <NativeBoard
          key={league.data.scope}
          locale={locale}
          registry={registry.data}
          league={league.data}
        />
      ) : (
        <Loading
          locale={locale}
          error={registry.error || league.error}
          retry={() => {
            registry.retry();
            league.retry();
          }}
        />
      )}
    </section>
  );
}
function NativeBoard({
  locale,
  registry,
  league,
}: {
  locale: Locale;
  registry: NativeRegistry;
  league: NativeLeague;
}) {
  const en = locale === "en";
  const [initial] = useState(() => {
    const raw = new URLSearchParams(window.location.search).get("scenario");
    try {
      return {
        scenario: raw
          ? validateNative(JSON.parse(raw), league, registry)
          : defaultNative(league),
        invalid: false,
      };
    } catch {
      return { scenario: defaultNative(league), invalid: true };
    }
  });
  const [scenario, setScenario] = useState(initial.scenario);
  const [wider, setWider] = useState<NativeLeague[]>([]);
  const [widerError, setWiderError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [feature, setFeature] = useState(registry.features[0].id);
  const [selected, setSelected] = useState("");
  const [shared, setShared] = useState("");
  const club = league.clubs.find((c) => c.id === scenario.club)!;
  const context = club.roles.find((r) => r.role === scenario.role)!;
  const update = (patch: Partial<NativeScenario>) => {
    const next = { ...scenario, ...patch };
    setScenario(next);
    setSelected("");
    setShared("");
    window.history.replaceState(null, "", nativeURL(next));
  };
  useEffect(() => {
    const link = document.querySelector<HTMLAnchorElement>("a.language");
    if (link)
      link.href = route(en ? "nl" : "en", "recruitment") + nativeURL(scenario);
  }, [scenario, en]);
  useEffect(() => {
    if (!scenario.wider) return;
    const controller = new AbortController();
    setWiderError(false);
    Promise.all(
      registry.leagues.map((l) =>
        l.scope === league.scope
          ? Promise.resolve(league)
          : fetchArtifact<NativeLeague>(l.path, controller.signal),
      ),
    )
      .then(setWider)
      .catch(() => {
        if (!controller.signal.aborted) setWiderError(true);
      });
    return () => controller.abort();
  }, [scenario.wider, registry, league, retry]);
  const ready = !scenario.wider || wider.length === registry.leagues.length;
  const results = useMemo(
    () => (ready ? rankNative(league, wider, scenario) : []),
    [league, wider, scenario, ready],
  );
  const detail = results.find((r) => r.player.id === selected);
  const fmt = (n: number) =>
    n.toLocaleString(locale, { maximumFractionDigits: 2 });
  return (
    <>
      {initial.invalid && (
        <p role="alert">
          {en
            ? "The shared scenario was incompatible. Default requirements restored."
            : "Het gedeelde scenario was niet compatibel. Standaardcriteria zijn hersteld."}
        </p>
      )}
      <div className="player-filters">
        <label>
          {en ? "Target club" : "Doelclub"}
          <select
            value={scenario.club}
            onChange={(e) => {
              const target = league.clubs.find((c) => c.id === e.target.value)!;
              update({
                club: target.id,
                role: target.roles[0].role,
                requirements: [],
              });
            }}
          >
            {league.clubs.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          {en ? "Role" : "Rol"}
          <select
            value={scenario.role}
            onChange={(e) => update({ role: e.target.value, requirements: [] })}
          >
            {club.roles.map((r) => (
              <option key={r.role} value={r.role}>
                {roleLabel(r.role, locale)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="small">
        {en
          ? "Observed historical profiles"
          : "Geobserveerde historische profielen"}{" "}
        · {league.competition} {league.season} · Pappalardo/Wyscout · ≥
        {league.minutes_threshold} min.{" "}
        {en
          ? "Broad provider positions; no inferred specialist roles."
          : "Brede providerposities; geen afgeleide specialistische rollen."}
      </p>
      <details>
        <summary>
          {en ? "Club role context" : "Clubcontext per rol"} · {club.name}
        </summary>
        <p>
          {context.players.length}{" "}
          {en ? "eligible roster members" : "geschikte selectiespelers"} ·{" "}
          {fmt(context.minutes)} {en ? "club minutes" : "clubminuten"}.{" "}
          {en
            ? "Medians and interquartile ranges describe eligible players’ full-season profiles, including other clubs for transferred players. These are roster summaries, not possession-adjusted team totals."
            : "Medianen en interkwartielafstanden beschrijven volledige seizoensprofielen van geschikte selectiespelers, inclusief andere clubs bij transfers. Dit zijn selectiesamenvattingen, geen teamtotalen gecorrigeerd voor balbezit."}
        </p>
        <div
          className="table-wrap"
          tabIndex={0}
          role="region"
          aria-label={
            locale === "en"
              ? "Scrollable data table"
              : "Scrollbare gegevenstabel"
          }
        >
          <table>
            <thead>
              <tr>
                <th>{en ? "Feature" : "Kenmerk"}</th>
                <th>{en ? "Median" : "Mediaan"}</th>
                <th>Q25–Q75</th>
              </tr>
            </thead>
            <tbody>
              {registry.features.map((f) => (
                <tr key={f.id}>
                  <th>
                    {f[locale]} {f.unit === "per90" ? "/ 90" : "%"}
                  </th>
                  <td>{fmt(context.median[f.id])}</td>
                  <td>
                    {fmt(context.q25[f.id])}–{fmt(context.q75[f.id])}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      <h3>{en ? "Recruitment requirements" : "Recruitmentcriteria"}</h3>
      <p className="small">
        {en
          ? "With no custom requirements, match the club-role median across all 24 features. Adding a requirement switches to your selected criteria. Changing club or role resets criteria."
          : "Zonder eigen criteria vergelijken we met de club-rolmediaan op alle 24 kenmerken. Na toevoeging gelden alleen je gekozen criteria. Bij een andere club of rol worden criteria gewist."}
      </p>
      <div className="profile-actions">
        <label>
          {en ? "Feature" : "Kenmerk"}
          <select value={feature} onChange={(e) => setFeature(e.target.value)}>
            {registry.features.map((f) => (
              <option key={f.id} value={f.id}>
                {f[locale]} {f.unit === "per90" ? "/ 90" : "%"}
              </option>
            ))}
          </select>
        </label>
        <button
          disabled={scenario.requirements.some((r) => r.feature === feature)}
          onClick={() =>
            update({
              requirements: [
                ...scenario.requirements,
                {
                  feature,
                  value: context.median[feature],
                  direction: "near",
                  weight: 1,
                },
              ],
            })
          }
        >
          {en ? "Add requirement" : "Criterium toevoegen"}
        </button>
        <button onClick={() => update({ requirements: [] })}>
          {en ? "Use club median" : "Gebruik clubmediaan"}
        </button>
      </div>
      {scenario.requirements.map((r, i) => (
        <div className="native-requirement" key={r.feature}>
          <strong>
            {registry.features.find((f) => f.id === r.feature)![locale]}
          </strong>
          <label>
            {en ? "Direction" : "Richting"}
            <select
              value={r.direction}
              onChange={(e) =>
                update({
                  requirements: scenario.requirements.map((v, j) =>
                    j === i
                      ? {
                          ...v,
                          direction: e.target.value as typeof r.direction,
                        }
                      : v,
                  ),
                })
              }
            >
              <option value="near">{en ? "Near" : "Dicht bij"}</option>
              <option value="at_least">{en ? "At least" : "Minimaal"}</option>
              <option value="at_most">{en ? "At most" : "Maximaal"}</option>
            </select>
          </label>
          <label>
            {en ? "Target value" : "Doelwaarde"}
            <input
              type="number"
              min="0"
              max="1000"
              step="0.1"
              value={r.value}
              onChange={(e) => {
                const value = Number(e.target.value);
                if (Number.isFinite(value) && value >= 0 && value <= 1000)
                  update({
                    requirements: scenario.requirements.map((v, j) =>
                      j === i ? { ...v, value } : v,
                    ),
                  });
              }}
            />
          </label>
          <label>
            {en ? "Weight" : "Gewicht"}
            <select
              value={r.weight}
              onChange={(e) =>
                update({
                  requirements: scenario.requirements.map((v, j) =>
                    j === i ? { ...v, weight: Number(e.target.value) } : v,
                  ),
                })
              }
            >
              {[0.5, 1, 2].map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
          </label>
          <button
            aria-label={`${en ? "Remove" : "Verwijder"} ${registry.features.find((f) => f.id === r.feature)![locale]}`}
            onClick={() =>
              update({
                requirements: scenario.requirements.filter((_, j) => j !== i),
              })
            }
          >
            ×
          </button>
        </div>
      ))}
      <label className="native-wider">
        <input
          type="checkbox"
          checked={scenario.wider}
          onChange={(e) => update({ wider: e.target.checked })}
        />
        {en
          ? "Include players from other Wyscout leagues"
          : "Neem spelers uit andere Wyscout-competities mee"}
      </label>
      <p className={scenario.wider ? "notice" : "small"}>
        {scenario.wider
          ? crossLeagueCopy(locale)
          : en
            ? "Candidate universe: same competition. Current target-club roster members are excluded."
            : "Kandidaten: dezelfde competitie. Selectiespelers uit de doelclub in dit seizoen zijn uitgesloten."}
      </p>
      {!ready && (
        <Loading
          locale={locale}
          error={widerError}
          retry={() => setRetry((n) => n + 1)}
        />
      )}
      <div className="profile-actions">
        <h3>{en ? "Criteria shortlist" : "Shortlist op criteria"}</h3>
        <button
          onClick={() =>
            setShared(
              window.location.origin +
                window.location.pathname +
                nativeURL(scenario),
            )
          }
        >
          {en ? "Share scenario" : "Scenario delen"}
        </button>
      </div>
      {shared && (
        <label>
          {en ? "Share URL" : "Deellink"}
          <input readOnly value={shared} onFocus={(e) => e.target.select()} />
        </label>
      )}
      <p aria-live="polite">
        {results.length}{" "}
        {en
          ? "eligible candidates; showing the first 30. Lower distance means a closer observed criteria match, not higher player quality."
          : "geschikte kandidaten; de eerste 30 worden getoond. Een kleinere afstand betekent een betere overeenkomst met de criteria, geen hogere spelerskwaliteit."}
      </p>
      <ul className="profile-results native-results">
        {results.slice(0, 30).map((r) => (
          <li key={r.player.id}>
            <PlayerAvatar
              id={r.player.id}
              name={r.player.name}
              locale={locale}
            />
            <div>
              <button
                className="profile-name"
                onClick={() => setSelected(r.player.id)}
              >
                {r.player.name}
              </button>
              <p className="small">
                {
                  registry.leagues.find((l) => l.scope === r.player.scope)
                    ?.competition
                }{" "}
                · {league.season} · {fmt(r.player.minutes)} min
              </p>
            </div>
            <span>
              {en ? "Distance" : "Afstand"} {fmt(r.distance)}
            </span>
          </li>
        ))}
      </ul>
      {detail && (
        <section
          className="profile-detail"
          aria-label={en ? "Candidate evidence" : "Onderbouwing kandidaat"}
        >
          <h3>{detail.player.name}</h3>
          <p>
            {en
              ? "Observed criteria contributions; own-league percentiles are descriptive only."
              : "Bijdragen van geobserveerde kenmerken; percentielen binnen de eigen competitie zijn alleen beschrijvend."}
          </p>
          <div
            className="table-wrap"
            tabIndex={0}
            role="region"
            aria-label={
              locale === "en"
                ? "Scrollable data table"
                : "Scrollbare gegevenstabel"
            }
          >
            <table>
              <thead>
                <tr>
                  <th>{en ? "Feature" : "Kenmerk"}</th>
                  <th>{en ? "Observed" : "Geobserveerd"}</th>
                  <th>{en ? "Target" : "Doel"}</th>
                  <th>
                    {en
                      ? "Own league-role percentile"
                      : "Percentiel eigen competitie-rol"}
                  </th>
                  <th>
                    {en
                      ? "Weighted squared difference"
                      : "Gewogen gekwadrateerd verschil"}
                  </th>
                </tr>
              </thead>
              <tbody>
                {detail.contributions.map((r) => (
                  <tr key={r.feature}>
                    <th>
                      {
                        registry.features.find((f) => f.id === r.feature)![
                          locale
                        ]
                      }
                    </th>
                    <td>{fmt(r.observed)}</td>
                    <td>{fmt(r.target)}</td>
                    <td>{fmt(detail.player.percentiles[r.feature])}</td>
                    <td>{fmt(r.loss)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <a href={route(locale, "players") + "?profile=" + detail.player.id}>
            {en ? "Open full profile" : "Volledig profiel openen"}
          </a>
        </section>
      )}
      <details>
        <summary>{en ? "Data & methodology" : "Data & methodologie"}</summary>
        <p>
          {registry.license}.{" "}
          <a href={registry.source}>{en ? "Source" : "Bron"}</a> ·{" "}
          <a href={registry.evaluation_path}>
            {en
              ? "League-specific evaluation and random baselines"
              : "Evaluatie per competitie en willekeurige referenties"}
          </a>
        </p>
        <p>
          {en
            ? "24 native features; equal family weights and within-family feature weights. Distances use target-league role standard deviations. Retrieval tests support profile repeatability, not transfer success."
            : "24 providerkenmerken; gelijke gewichten per familie en per kenmerk binnen de familie. Afstanden gebruiken standaardafwijkingen van de doelcompetitie en rol. Retrievaltests ondersteunen herhaalbaarheid van profielen, geen transfersucces."}
        </p>
        {registry.features.map((f) => (
          <details key={f.id}>
            <summary>{f[locale]}</summary>
            <p>
              {f.formula} · {f.event_mapping} · {f.null_semantics}
            </p>
          </details>
        ))}
      </details>
    </>
  );
}
export function NativeComparison({
  locale,
  ids,
  entries,
}: {
  locale: Locale;
  ids: string[];
  entries: ProfileIndexEntry[];
}) {
  const selected = entries.filter((e) => ids.includes(e.id));
  const registry = useExpansion<NativeRegistry>(
    selected.every((p) => p.provider === "wyscout")
      ? "/data/v12/recruitment/index.json"
      : null,
  );
  const [data, setData] = useState<{ key: string; leagues: NativeLeague[] }>();
  const [error, setError] = useState(false);
  const key = [...new Set(selected.map((p) => p.scope))].sort().join(",");
  useEffect(() => {
    if (!registry.data) return;
    const controller = new AbortController();
    setError(false);
    Promise.all(
      registry.data.leagues
        .filter((l) => key.split(",").includes(l.scope))
        .map((l) => fetchArtifact<NativeLeague>(l.path, controller.signal)),
    )
      .then((leagues) => setData({ key, leagues }))
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      });
    return () => controller.abort();
  }, [key, registry.data]);
  if (!selected.every((p) => p.provider === "wyscout"))
    return (
      <p className="notice">
        {locale === "en"
          ? "Cross-provider comparison uses common-profile features only."
          : "Vergelijking tussen providers gebruikt alleen geharmoniseerde profielkenmerken."}
      </p>
    );
  if (error || registry.error)
    return (
      <p role="alert">
        {locale === "en"
          ? "Rich comparison could not be loaded."
          : "Uitgebreide vergelijking kon niet worden geladen."}
      </p>
    );
  if (!registry.data || data?.key !== key) return null;
  const players = ids
    .map((id) =>
      data.leagues.flatMap((l) => l.players).find((p) => p.id === id),
    )
    .filter((p) => p !== undefined);
  if (players.length !== ids.length)
    return (
      <p>
        {locale === "en"
          ? "Rich recruitment features are unavailable for at least one selected profile at the validated evidence threshold."
          : "Uitgebreide recruitmentkenmerken zijn bij de gevalideerde bewijsdrempel niet beschikbaar voor minstens één geselecteerd profiel."}
      </p>
    );
  return (
    <details open>
      <summary>
        {locale === "en"
          ? "Wyscout native comparison · 24 features"
          : "Wyscout-vergelijking · 24 providerkenmerken"}
      </summary>
      {data.leagues.length > 1 && (
        <p className="notice">{crossLeagueCopy(locale)}</p>
      )}
      <div
        className="table-wrap"
        tabIndex={0}
        role="region"
        aria-label={
          locale === "en" ? "Scrollable data table" : "Scrollbare gegevenstabel"
        }
      >
        <table>
          <thead>
            <tr>
              <th>
                {locale === "en" ? "Observed feature" : "Geobserveerd kenmerk"}
              </th>
              {players.map((p) => (
                <th key={p.id}>
                  {p.name}
                  <small>
                    {
                      registry.data?.leagues.find((l) => l.scope === p.scope)
                        ?.competition
                    }{" "}
                    · 2017/18
                  </small>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {registry.data.features.map((f) => (
              <tr key={f.id}>
                <th>
                  {f[locale]} {f.unit === "per90" ? "/ 90" : "%"}
                </th>
                {players.map((p) => (
                  <td key={p.id}>
                    {p.features[f.id].toLocaleString(locale, {
                      maximumFractionDigits: 2,
                    })}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
