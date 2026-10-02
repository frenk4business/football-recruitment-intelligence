"use client";
import { useMemo, useState } from "react";
import type { Locale } from "@/lib/content";
import { route } from "@/lib/content";
import type { ProfileIndex } from "@/lib/player-view";
import type {
  MetadataDirectory,
  MetadataClub,
  MetadataPeople,
  MetadataFixtures,
  PhysicalIndex,
  PhysicalPerson,
  ExpandedIndex,
} from "@/lib/expansion-contracts";
import { useExpansion } from "./wyscout-recruitment";
import { normalizeName } from "@/lib/player-search";

export function Discovery({
  locale,
  index,
}: {
  locale: Locale;
  index: ProfileIndex;
}) {
  const [mode, setMode] = useState("");
  const en = locale === "en";
  return (
    <section className="discovery">
      <div className="profile-actions">
        <button
          aria-expanded={mode === "competitions"}
          onClick={() => setMode(mode === "competitions" ? "" : "competitions")}
        >
          {en ? "Competitions & coverage" : "Competities & dekking"}
        </button>
        <button
          aria-expanded={mode === "clubs"}
          onClick={() => setMode(mode === "clubs" ? "" : "clubs")}
        >
          {en ? "Club directory" : "Clubdirectory"}
        </button>
        <button
          aria-expanded={mode === "metadata"}
          onClick={() => setMode(mode === "metadata" ? "" : "metadata")}
        >
          {en ? "Player metadata" : "Spelersmetadata"}
        </button>
        <button
          aria-expanded={mode === "physical"}
          onClick={() => setMode(mode === "physical" ? "" : "physical")}
        >
          {en ? "Physical research" : "Fysiek onderzoek"}
        </button>
      </div>
      {mode === "competitions" && (
        <CompetitionDirectory locale={locale} index={index} />
      )}
      {(mode === "clubs" || mode === "metadata") && (
        <MetadataBrowser key={mode} locale={locale} mode={mode} index={index} />
      )}
      {mode === "physical" && <PhysicalBrowser locale={locale} />}
    </section>
  );
}
function Status({
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
          ? "Loading…"
          : "Laden…"}
      {error && (
        <button onClick={retry}>{locale === "en" ? "Retry" : "Opnieuw"}</button>
      )}
    </p>
  );
}
function CompetitionDirectory({
  locale,
  index,
}: {
  locale: Locale;
  index: ProfileIndex;
}) {
  const [country, setCountry] = useState(""),
    [q, setQ] = useState("");
  const en = locale === "en";
  const rows = index.scopes.filter(
    (s) =>
      (!country || s.country === country) &&
      normalizeName(s.competition + " " + s.season).includes(normalizeName(q)),
  );
  return (
    <div className="discovery-panel">
      <h2>{en ? "Performance coverage" : "Dekking van prestatiegegevens"}</h2>
      <p>
        {en
          ? "Recruitment is available for the five Wyscout leagues and the validated WSL scope. Searchable partial seasons and tournament samples do not imply full club-season coverage."
          : "Recruitment is beschikbaar voor de vijf Wyscout-competities en de gevalideerde WSL-scope. Doorzoekbare deelcompetities en toernooisteekproeven zijn geen volledige clubseizoenen."}
      </p>
      <div className="player-filters">
        <label>
          {en ? "Competition or season" : "Competitie of seizoen"}
          <input value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
        <label>
          {en ? "Country" : "Land"}
          <select value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">{en ? "All" : "Alle"}</option>
            {[...new Set(index.scopes.map((s) => s.country))]
              .sort()
              .map((c) => (
                <option key={c}>{c}</option>
              ))}
          </select>
        </label>
      </div>
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
              {(en
                ? [
                    "Competition",
                    "Country",
                    "Season",
                    "Provider",
                    "Matches",
                    "Profiles",
                    "Clubs",
                    "Coverage",
                    "Capabilities",
                  ]
                : [
                    "Competitie",
                    "Land",
                    "Seizoen",
                    "Provider",
                    "Wedstrijden",
                    "Profielen",
                    "Clubs",
                    "Dekking",
                    "Mogelijkheden",
                  ]
              ).map((v) => (
                <th key={v}>{v}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id}>
                <th>
                  <a
                    href={
                      route(locale, "players") +
                      "?competition=" +
                      s.competition_key +
                      "&season=" +
                      encodeURIComponent(s.season)
                    }
                  >
                    {s.competition}
                  </a>
                </th>
                <td>{s.country}</td>
                <td>{s.season}</td>
                <td>{s.provider}</td>
                <td>{s.matches}</td>
                <td>{s.profiles}</td>
                <td>{s.clubs?.length}</td>
                <td>{coverageLabel(s.coverage, locale)}</td>
                <td>
                  {s.recruitment ? (
                    <a
                      href={
                        route(locale, "recruitment") +
                        (s.provider === "wyscout"
                          ? `?dataset=wyscout&scope=${s.id}`
                          : "?dataset=wsl")
                      }
                    >
                      Recruitment
                    </a>
                  ) : en ? (
                    "Profiles only"
                  ) : (
                    "Alleen profielen"
                  )}{" "}
                  ·{" "}
                  {s.similarity_profiles > 0
                    ? en
                      ? "Similarity"
                      : "Gelijkenis"
                    : en
                      ? "No validated similarity"
                      : "Geen gevalideerde gelijkenis"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="small">
        {en
          ? "Coverage: complete = 100% of expected domestic schedule, near complete ≥95%, partial ≥25%, sample below 25% or no verified denominator. Cup/international scopes remain tournament observations."
          : "Dekking: volledig = 100% van verwacht competitieschema, vrijwel volledig ≥95%, gedeeltelijk ≥25%, steekproef onder 25% of zonder geverifieerde noemer. Bekers en interlands blijven toernooiwaarnemingen."}
      </p>
    </div>
  );
}
export function coverageLabel(value: string, locale: Locale) {
  const en = locale === "en";
  return (
    {
      complete: en ? "Complete" : "Volledig",
      near_complete: en ? "Near complete" : "Vrijwel volledig",
      partial: en ? "Partial" : "Gedeeltelijk",
      sample: en ? "Sample" : "Steekproef",
    }[value] ?? value
  );
}
function MetadataBrowser({
  locale,
  mode,
  index,
}: {
  locale: Locale;
  mode: string;
  index: ProfileIndex;
}) {
  const resource = useExpansion<MetadataDirectory>(
    "/data/v12/metadata/index.json",
  );
  const [country, setCountry] = useState("Netherlands"),
    [q, setQ] = useState(""),
    [page, setPage] = useState(1),
    [selected, setSelected] = useState("");
  const detail = useExpansion<MetadataClub>(
    selected
      ? `/data/v12/metadata/clubs/${selected.slice(-2)}/${selected}.json`
      : null,
  );
  const [scope, setScope] = useState("");
  const fixtures = useExpansion<MetadataFixtures>(
    scope ? `/data/v12/metadata/fixtures/${scope}.json` : null,
  );
  const people = useExpansion<MetadataPeople>(
    mode === "metadata" ? (resource.data?.player_paths[country] ?? null) : null,
  );
  const en = locale === "en";
  const rows = useMemo(
    () =>
      resource.data?.clubs.filter(
        (c) =>
          (!country || c.country === country) &&
          normalizeName([c.name, ...c.aliases].join(" ")).includes(
            normalizeName(q),
          ),
      ) ?? [],
    [resource.data, country, q],
  );
  const persons = useMemo(
    () =>
      people.data?.players.filter((p) =>
        normalizeName(p.name).includes(normalizeName(q)),
      ) ?? [],
    [people.data, q],
  );
  if (!resource.data)
    return (
      <Status locale={locale} error={resource.error} retry={resource.retry} />
    );
  const data = resource.data,
    n = mode === "clubs" ? rows.length : persons.length;
  const clubNames = new Map(data.clubs.map((c) => [c.id, c.name]));
  const comp = data.competitions.find((s) => s.id === scope);
  return (
    <div className="discovery-panel">
      <h2>
        {mode === "clubs"
          ? en
            ? "Club and fixture metadata"
            : "Club- en wedstrijdmetadata"
          : en
            ? "Player metadata records"
            : "Spelersmetadatarecords"}
      </h2>
      <p className="notice">
        {en
          ? "OpenFootball metadata only. No event performance, Player DNA or recruitment is inferred from these records. Country identifies the source folder; historical performance stays in its original season."
          : "Alleen OpenFootball-metadata. Uit deze records worden geen wedstrijdprestaties, Player DNA of recruitmentmogelijkheden afgeleid. Land verwijst naar de bronmap; historische prestaties blijven bij het oorspronkelijke seizoen."}
      </p>
      <div className="player-filters">
        <label>
          {en ? "Country" : "Land"}
          <select
            value={country}
            onChange={(e) => {
              setCountry(e.target.value);
              setPage(1);
              setSelected("");
              setScope("");
            }}
          >
            {(mode === "metadata"
              ? Object.keys(data.player_countries)
              : [...new Set(data.clubs.map((c) => c.country))]
            )
              .sort()
              .map((c) => (
                <option key={c}>{c}</option>
              ))}
          </select>
        </label>
        <label>
          {en ? "Search metadata" : "Metadata zoeken"}
          <input
            type="search"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
          />
        </label>
      </div>
      <p aria-live="polite">
        {n.toLocaleString(locale)} {en ? "source records" : "bronrecords"} ·{" "}
        {data.license}
      </p>
      {mode === "clubs" ? (
        <ul className="directory-list">
          {rows.slice((page - 1) * 40, page * 40).map((c) => (
            <li key={c.id}>
              <button
                onClick={() => {
                  setSelected(c.id);
                  setScope("");
                }}
              >
                {c.name}
              </button>
              <span>
                {c.performance_scopes.length
                  ? en
                    ? "Historical performance links available"
                    : "Historische prestatielinks beschikbaar"
                  : en
                    ? "Performance data unavailable"
                    : "Prestatiegegevens niet beschikbaar"}
              </span>
            </li>
          ))}
        </ul>
      ) : people.data ? (
        <>
          <p className="small">
            {en ? "Metadata updated" : "Metadata bijgewerkt"}:{" "}
            {people.data.metadata_updated}.{" "}
            {en
              ? "No global person merge; same names may refer to different people."
              : "Geen globale persoonskoppeling; dezelfde naam kan verschillende personen betreffen."}
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
                  {(en
                    ? ["Name", "Position", "DOB", "Height", "Source"]
                    : ["Naam", "Positie", "Geboortedatum", "Lengte", "Bron"]
                  ).map((x) => (
                    <th key={x}>{x}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {persons.slice((page - 1) * 40, page * 40).map((p) => (
                  <tr key={p.id}>
                    <th>
                      {p.name}
                      {p.conflicting_source_rows ? " *" : ""}
                    </th>
                    <td>{p.position}</td>
                    <td>{p.dob ?? "—"}</td>
                    <td>{p.height_m ? `${p.height_m} m` : "—"}</td>
                    <td>
                      <a href={p.source + "#L" + p.source_line}>OpenFootball</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <Status locale={locale} error={people.error} retry={people.retry} />
      )}
      <nav
        className="profile-pagination"
        aria-label={en ? "Metadata pages" : "Metadatapagina’s"}
      >
        <button disabled={page === 1} onClick={() => setPage(page - 1)}>
          {en ? "Previous" : "Vorige"}
        </button>
        <span>
          {page} / {Math.max(1, Math.ceil(n / 40))}
        </span>
        <button disabled={page * 40 >= n} onClick={() => setPage(page + 1)}>
          {en ? "Next" : "Volgende"}
        </button>
      </nav>
      {selected &&
        (detail.data ? (
          <section className="profile-detail">
            <h3>{detail.data.name}</h3>
            <p>
              {detail.data.country} ·{" "}
              {detail.data.stadium ??
                (en ? "Stadium unavailable" : "Stadion onbekend")}
            </p>
            <p>
              {en ? "Aliases" : "Aliassen"}:{" "}
              {detail.data.aliases.join(" / ") || "—"}
            </p>
            <p className="small">
              {en ? "Metadata updated" : "Metadata bijgewerkt"}:{" "}
              {detail.data.metadata_updated} ·{" "}
              <a href={detail.data.source}>OpenFootball</a>
            </p>
            {!detail.data.performance_scopes.length && (
              <p className="notice">
                {en
                  ? "Performance data unavailable. This club cannot be a recruitment target."
                  : "Prestatiegegevens niet beschikbaar. Deze club kan geen recruitmentdoel zijn."}
              </p>
            )}
            {detail.data.performance_scopes.map((s) => {
              const p = index.scopes.find((v) => v.id === s);
              return (
                p && (
                  <p key={s}>
                    <a
                      href={
                        route(locale, "players") +
                        "?competition=" +
                        p.competition_key +
                        "&season=" +
                        encodeURIComponent(p.season)
                      }
                    >
                      {p.provider} · {p.competition} · {p.season}
                    </a>{" "}
                    ·{" "}
                    {en
                      ? "Explicit country + unique source alias match; historical metrics remain separate."
                      : "Expliciete koppeling via land en unieke bronalias; historische statistieken blijven gescheiden."}
                  </p>
                )
              );
            })}
            <label>
              {en ? "Fixture source / season" : "Wedstrijdbron / seizoen"}
              <select value={scope} onChange={(e) => setScope(e.target.value)}>
                <option value="">
                  {en ? "Select a source scope" : "Selecteer een bron-scope"}
                </option>
                {data.competitions
                  .filter((s) => detail.data!.seasons.includes(s.id))
                  .map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} · {s.season} · {s.provider}
                    </option>
                  ))}
              </select>
            </label>
            {scope &&
              (fixtures.data ? (
                <>
                  <p>
                    {comp?.season} · {en ? "Source updated" : "Bron bijgewerkt"}{" "}
                    {comp?.metadata_updated}.{" "}
                    {en
                      ? "Source-scoped fixture observations; overlapping repositories are not a count of unique matches. Dates are shown as recorded."
                      : "Wedstrijdwaarnemingen per bron; overlappende repositories zijn geen telling van unieke wedstrijden. Datums worden getoond zoals vastgelegd."}
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
                          {(en
                            ? ["Source date", "Home", "Away", "Result"]
                            : ["Brondatum", "Thuis", "Uit", "Uitslag"]
                          ).map((x) => (
                            <th key={x}>{x}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {fixtures.data.rows
                          .filter((r) => r[0] === selected || r[1] === selected)
                          .slice(0, 80)
                          .map((r, i) => (
                            <tr key={i}>
                              <td>{String(r[2] ?? "—")}</td>
                              <td>{clubNames.get(String(r[0]))}</td>
                              <td>{clubNames.get(String(r[1]))}</td>
                              <td>
                                {Array.isArray(r[4]) ? r[4].join("–") : "—"}{" "}
                                {r[5] && String(r[5])}
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <Status
                  locale={locale}
                  error={fixtures.error}
                  retry={fixtures.retry}
                />
              ))}
          </section>
        ) : (
          <Status locale={locale} error={detail.error} retry={detail.retry} />
        ))}
    </div>
  );
}
function PhysicalBrowser({ locale }: { locale: Locale }) {
  const index = useExpansion<PhysicalIndex>("/data/v12/physical/index.json");
  const [q, setQ] = useState(""),
    [selected, setSelected] = useState("");
  const detail = useExpansion<PhysicalPerson>(
    selected ? `/data/v12/physical/${selected}.json` : null,
  );
  const en = locale === "en";
  return (
    <div className="discovery-panel">
      <h2>
        {en ? "Physical / off-ball research" : "Fysiek / zonder-bal-onderzoek"}
      </h2>
      <p className="notice">
        {en
          ? "SkillCorner · Australian A-League 2024/25. Specialist aggregates for performances above 60 minutes; not European recruitment coverage. Physical minutes are average match minutes, not season totals. Off-ball run p30tip rates use 30 possession minutes."
          : "SkillCorner · Australische A-League 2024/25. Specialistische aggregaten voor optredens boven 60 minuten; geen Europese recruitmentdekking. Fysieke minuten zijn gemiddelde wedstrijdminuten, geen seizoenstotalen. Loopacties per p30tip gebruiken 30 minuten balbezit."}
      </p>
      {index.data ? (
        <>
          <p>
            {index.data.profiles.length}{" "}
            {en
              ? "specialist player-season records"
              : "specialistische speler-seizoenrecords"}{" "}
            · <a href={index.data.source}>SkillCorner</a> ·{" "}
            <a href="/skillcorner-license.txt">MIT</a>
          </p>
          <label>
            {en ? "Search physical profiles" : "Fysieke profielen zoeken"}
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </label>
          <ul className="directory-list">
            {index.data.profiles
              .filter((p) => normalizeName(p.name).includes(normalizeName(q)))
              .slice(0, 40)
              .map((p) => (
                <li key={p.id}>
                  <button onClick={() => setSelected(p.id)}>{p.name}</button>
                  <span>
                    {p.teams.join(" / ")} · {p.season}
                  </span>
                </li>
              ))}
          </ul>
          <p className="small">
            {en
              ? "First 40 matches; search to narrow."
              : "Eerste 40 resultaten; zoek om te verfijnen."}
          </p>
        </>
      ) : (
        <Status locale={locale} error={index.error} retry={index.retry} />
      )}
      {selected &&
        (detail.data ? (
          <section>
            <h3>{detail.data.name}</h3>
            {detail.data.records.map((record, i) => (
              <details key={i}>
                <summary>
                  {record.kind} ·{" "}
                  {record.values.position_group ?? record.values.position ?? ""}{" "}
                  · {detail.data!.teams[record.values.team_id]}
                </summary>
                <p className="small">
                  {en
                    ? "Original provider field names and units; no synthetic harmonisation."
                    : "Oorspronkelijke providerveldnamen en eenheden; geen synthetische harmonisatie."}
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
                    <tbody>
                      {Object.entries(record.values).map(([k, v]) => (
                        <tr key={k}>
                          <th>{k}</th>
                          <td>{v || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            ))}
          </section>
        ) : (
          <Status locale={locale} error={detail.error} retry={detail.retry} />
        ))}
    </div>
  );
}
export function ExpansionCoverage({ locale }: { locale: Locale }) {
  const data = useExpansion<ExpandedIndex>("/data/v12/index.json");
  return data.data ? (
    <>
      <p>
        {data.data.counts.profiles.toLocaleString(locale)}{" "}
        {locale === "en"
          ? "performance player-season profiles"
          : "prestatieprofielen per speler-seizoen"}{" "}
        · {data.data.counts.recruitment_clubs}{" "}
        {locale === "en"
          ? "recruitment club-seasons"
          : "clubseizoenen met recruitment"}
      </p>
      <Discovery locale={locale} index={data.data} />
    </>
  ) : (
    <Status locale={locale} error={data.error} retry={data.retry} />
  );
}
