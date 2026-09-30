"use client";
import { useEffect, useState } from "react";
import type {
  Explorer as ExplorerData,
  MatchSummary,
  Source,
} from "@/lib/contracts";
import { copy, type Locale } from "@/lib/content";
import { filterPlayers, metric } from "@/lib/explorer";
import { Pitch } from "./pitch";
export function Explorer({
  matches,
  sources,
  locale,
}: {
  matches: MatchSummary[];
  sources: Source[];
  locale: Locale;
}) {
  const c = copy[locale];
  const [matchId, setMatchId] = useState(
    matches.find((m) => m.provider === "statsbomb")?.id ?? matches[0]?.id ?? "",
  );
  const [data, setData] = useState<ExplorerData | null>(null),
    [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [attempt, setAttempt] = useState(0),
    [team, setTeam] = useState(""),
    [query, setQuery] = useState(""),
    [page, setPage] = useState(0),
    [frame, setFrame] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`/data/explorer/${matchId}.json`, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error("Unavailable");
        return r.json();
      })
      .then((value: ExplorerData) => {
        if (
          !["1.0.0", "1.1.0"].includes(value.schema_version) ||
          value.match.id !== matchId
        )
          throw new Error("Invalid contract");
        setData(value);
        setStatus("ready");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [matchId, attempt]);
  const selected = matches.find((m) => m.id === matchId),
    source = sources.find((s) => s.id === selected?.provider);
  const rows = data ? filterPlayers(data.players, team, query) : [],
    pages = Math.max(1, Math.ceil(rows.length / 12));
  function changeMatch(id: string) {
    setMatchId(id);
    setStatus("loading");
    setData(null);
    setTeam("");
    setQuery("");
    setPage(0);
    setFrame(0);
  }
  return (
    <>
      <div className="filter-bar">
        <label>
          {c.source}
          <select
            aria-label={c.source}
            value={selected?.provider}
            onChange={(e) =>
              changeMatch(
                matches.find((m) => m.provider === e.target.value)!.id,
              )
            }
          >
            {sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label className="match-select">
          {c.match}
          <select value={matchId} onChange={(e) => changeMatch(e.target.value)}>
            {matches
              .filter((m) => m.provider === selected?.provider)
              .map((m) => (
                <option key={m.id} value={m.id}>
                  {m.home} — {m.away} · {m.date}
                </option>
              ))}
          </select>
        </label>
      </div>
      {status === "loading" && (
        <p className="state" role="status">
          {c.loading}
        </p>
      )}
      {status === "error" && (
        <div className="state" role="alert">
          <p>{c.error}</p>
          <button
            onClick={() => {
              setStatus("loading");
              setAttempt(attempt + 1);
            }}
          >
            {c.retry}
          </button>
        </div>
      )}
      {status === "ready" && data && (
        <>
          <div className="match-heading">
            <div>
              <p className="eyebrow">
                {data.match.competition} / {data.match.season}
              </p>
              <h2>
                {data.match.home}{" "}
                <span className="score">{data.match.score}</span>{" "}
                {data.match.away}
              </h2>
              <p>
                {data.match.date} ·{" "}
                {data.match.provider === "statsbomb"
                  ? c.fullMatch
                  : c.trackingSample}
              </p>
            </div>
            <span className="source-tag">{source?.name}</span>
          </div>
          <div className="analysis-grid">
            <div>
              <Pitch data={data} locale={locale} frameIndex={frame} />
              {data.tracking_snapshots.length > 0 && (
                <label className="time-control">
                  {c.frame}: {frame} s
                  <input
                    aria-label={c.frame}
                    type="range"
                    min="0"
                    max={data.tracking_snapshots.length - 1}
                    value={frame}
                    onChange={(e) => setFrame(Number(e.target.value))}
                  />
                </label>
              )}
            </div>
            <aside className="analysis-notes">
              <h3>{c.available}</h3>
              {data.event_counts.length > 0 ? (
                <dl className="event-list">
                  {data.event_counts.slice(0, 7).map((e) => (
                    <div key={e.event_type}>
                      <dt>
                        {locale === "nl"
                          ? ({
                              Pass: "Pass",
                              "Ball Receipt*": "Balontvangst",
                              Carry: "Dribbel",
                              Pressure: "Druk zetten",
                              "Ball Recovery": "Balverovering",
                              Duel: "Duel",
                              Shot: "Schot",
                            }[e.event_type] ?? e.event_type)
                          : e.event_type}
                      </dt>
                      <dd>{e.count.toLocaleString(locale)}</dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <dl className="event-list">
                  <div>
                    <dt>{c.frames}</dt>
                    <dd>{data.tracking_snapshots.length}</dd>
                  </div>
                  <div>
                    <dt>{c.players}</dt>
                    <dd>{data.players.length}</dd>
                  </div>
                  <div>
                    <dt>{c.events}</dt>
                    <dd>{c.unavailable}</dd>
                  </div>
                  <div>
                    <dt>{c.xg}</dt>
                    <dd>{c.unavailable}</dd>
                  </div>
                </dl>
              )}
              <p>
                {locale === "nl"
                  ? source?.limitation_nl
                  : source?.limitation_en}
              </p>
              {data.match.provider === "statsbomb" && <p>{c.shootout}</p>}
            </aside>
          </div>
          <section className="player-section">
            <div className="section-top">
              <h2>{c.players}</h2>
              <div className="table-filters">
                <label>
                  {c.team}
                  <select
                    value={team}
                    onChange={(e) => {
                      setTeam(e.target.value);
                      setPage(0);
                    }}
                  >
                    <option value="">{c.allTeams}</option>
                    {[...new Set(data.players.map((p) => p.team))].map((t) => (
                      <option key={t}>{t}</option>
                    ))}
                  </select>
                </label>
                <label>
                  {c.search}
                  <input
                    type="search"
                    placeholder={c.searchPlaceholder}
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setPage(0);
                    }}
                  />
                </label>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <caption className="sr-only">
                  {data.match.home} — {data.match.away}: {c.players}
                </caption>
                <thead>
                  <tr>
                    <th scope="col">{c.player}</th>
                    <th scope="col">{c.team}</th>
                    <th scope="col">{c.position}</th>
                    <th scope="col" className="num">
                      {c.minutes}
                    </th>
                    <th scope="col" className="num">
                      {c.shots}
                    </th>
                    <th scope="col" className="num">
                      {c.passes}
                    </th>
                    <th scope="col" className="num">
                      {c.xg}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {rows.slice(page * 12, page * 12 + 12).map((p) => (
                    <tr key={p.id}>
                      <th scope="row">{p.name}</th>
                      <td>{p.team}</td>
                      <td>{p.position ?? c.unavailable}</td>
                      <td
                        className="num"
                        title={p.minutes === null ? c.minutesNote : undefined}
                      >
                        {metric(p.minutes, locale, c.unavailable, 1)}
                      </td>
                      <td className="num">
                        {metric(p.shots, locale, c.unavailable)}
                      </td>
                      <td className="num">
                        {metric(p.passes, locale, c.unavailable)}
                      </td>
                      <td className="num">
                        {metric(p.xg, locale, c.unavailable, 2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!rows.length && (
                <p className="state" role="status">
                  {c.noRows}
                </p>
              )}
            </div>
            <div className="pagination">
              <p aria-live="polite">
                {rows.length} {c.showing} · {c.page} {page + 1} {c.of} {pages}
              </p>
              <div>
                <button disabled={page === 0} onClick={() => setPage(page - 1)}>
                  {c.previous}
                </button>
                <button
                  disabled={page >= pages - 1}
                  onClick={() => setPage(page + 1)}
                >
                  {c.next}
                </button>
              </div>
            </div>
            <p className="note">
              {c.minutesNote} {data.match.provider === "statsbomb" && c.xgNote}
            </p>
          </section>
        </>
      )}
      {source && (
        <div className="provenance">
          <h3>{c.provenance}</h3>
          <p>
            <a href={source.url}>{source.name}</a> ·{" "}
            <a href={source.license_url}>{source.license}</a>
          </p>
          <p>{source.attribution}</p>
          <details>
            <summary>
              {locale === "nl" ? "Bronversie en ID" : "Source revision and ID"}
            </summary>
            <p className="mono">
              {source.revision}
              <br />
              {matchId}
            </p>
          </details>
        </div>
      )}
    </>
  );
}
