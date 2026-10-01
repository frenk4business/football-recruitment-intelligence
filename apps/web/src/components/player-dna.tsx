"use client";
import { fetchArtifact } from "@/lib/artifact";
import { useEffect, useMemo, useState } from "react";
import type {
  DNAIndex,
  DNAProfile,
  DNAEvaluation,
  DNAMap,
  FeatureDefinition,
} from "@/lib/contracts";
import type { Locale } from "@/lib/content";
import { dnaCopy, families, methods } from "@/lib/dna-copy";
import { route } from "@/lib/content";

const displayed = [
  "shots_per90",
  "box_shots_per90",
  "shot_assists_per90",
  "box_passes_per90",
  "passes_per90",
  "progressive_passes_per90",
  "carries_per90",
  "progressive_carries_per90",
  "pressures_per90",
  "interceptions_per90",
];
const normalize = (s: string) =>
  s
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
function useArtifact<T>(url: string | null, retry: number = 0) {
  const [state, setState] = useState<{
    url: string;
    data?: T;
    error?: boolean;
  }>();
  useEffect(() => {
    if (!url) return;
    setState({ url });
    const controller = new AbortController();
    fetchArtifact<T>(url, controller.signal)
      .then((data) => setState({ url, data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ url, error: true });
      });
    return () => controller.abort();
  }, [url, retry]);
  return state?.url === url ? state : undefined;
}
export function PlayerDNA({
  locale,
  index,
  registry,
  evaluation,
}: {
  locale: Locale;
  index: DNAIndex;
  registry: FeatureDefinition[];
  evaluation: DNAEvaluation;
}) {
  const c = dnaCopy[locale];
  const [threshold, setThreshold] = useState(index.default_threshold);
  const [query, setQuery] = useState("");
  const [team, setTeam] = useState("");
  const [role, setRole] = useState("");
  const initial = index.players
    .filter((p) => p.eligibility[String(index.default_threshold)].length === 0)
    .sort((a, b) => b.minutes - a.minutes)[0];
  const [selected, setSelected] = useState(initial.player_id);
  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("player");
    if (requested && index.players.some((p) => p.player_id === requested))
      setSelected(requested);
  }, [index]);
  const [comparison, setComparison] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [mapOpen, setMapOpen] = useState(false);
  const filtered = useMemo(
    () =>
      index.players.filter(
        (p) =>
          (!team || p.teams.includes(team)) &&
          (!role || p.primary_role === role) &&
          normalize(p.name).includes(normalize(query)),
      ),
    [index, query, team, role],
  );
  const activeId = filtered.some((p) => p.player_id === selected)
    ? selected
    : filtered[0]?.player_id;
  const profile = useArtifact<DNAProfile>(
    activeId ? `/data/phase2/${threshold}/${activeId}.json` : null,
    retry,
  );
  const detail = profile?.data;
  const pair = useArtifact<DNAProfile>(
    comparison && detail?.neighbors.some((n) => n.player_id === comparison)
      ? `/data/phase2/${threshold}/${comparison}.json`
      : null,
    retry,
  );
  const map = useArtifact<DNAMap>(
    mapOpen ? `/data/phase2/map-${threshold}.json` : null,
    retry,
  );
  const definitions = Object.fromEntries(registry.map((f) => [f.id, f]));
  const label = (id: string) =>
    locale === "nl" ? definitions[id]?.label_nl : definitions[id]?.label_en;
  const number = (n: number | null | undefined, digits = 1) =>
    n == null
      ? c.unavailable
      : n.toLocaleString(locale, { maximumFractionDigits: digits });
  const choose = (id: string) => {
    setSelected(id);
    setComparison(null);
  };
  const compare = detail?.neighbors.find((n) => n.player_id === comparison);
  const teamNames = [...new Set(index.players.flatMap((p) => p.teams))].sort();
  const roles = [
    ...new Set(
      index.players.map((p) => p.primary_role).filter((p): p is string => !!p),
    ),
  ].sort();
  return (
    <div className="dna">
      <div className="dna-filters">
        <label>
          {c.season}
          <select
            aria-label={c.season}
            value={index.season}
            onChange={() => {}}
          >
            <option>{index.season}</option>
          </select>
        </label>
        <label>
          {c.team}
          <select
            value={team}
            onChange={(e) => {
              setTeam(e.target.value);
              setComparison(null);
            }}
          >
            <option value="">{c.all}</option>
            {teamNames.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </label>
        <label>
          {c.role}
          <select
            value={role}
            onChange={(e) => {
              setRole(e.target.value);
              setComparison(null);
            }}
          >
            <option value="">{c.all}</option>
            {roles.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </label>
        <label>
          {c.threshold}
          <select
            aria-label={c.threshold}
            value={threshold}
            onChange={(e) => {
              setThreshold(Number(e.target.value));
              setComparison(null);
            }}
          >
            {index.thresholds.map((t) => (
              <option key={t} value={t}>
                {number(t, 0)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="dna-selection">
        <label>
          {c.search}
          <input
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setComparison(null);
            }}
            placeholder={c.search}
          />
        </label>
        <label>
          {c.select}
          <select
            value={activeId ?? ""}
            disabled={!filtered.length}
            onChange={(e) => choose(e.target.value)}
          >
            {filtered.length ? (
              filtered.map((p) => (
                <option key={p.player_id} value={p.player_id}>
                  {p.name} · {p.teams.join(", ")} · {p.primary_role ?? "—"} ·{" "}
                  {number(p.minutes, 0)} min
                </option>
              ))
            ) : (
              <option value="">{c.empty}</option>
            )}
          </select>
        </label>
        <span className="note" aria-live="polite">
          {filtered.length} {c.results}
        </span>
      </div>
      {!activeId ? (
        <p className="state">{c.empty}</p>
      ) : profile?.error ? (
        <div className="state" role="alert">
          <p>{c.error}</p>
          <button onClick={() => setRetry(retry + 1)}>{c.retry}</button>
        </div>
      ) : !detail ? (
        <p className="state" role="status">
          {c.loading}
        </p>
      ) : (
        <>
          <section className="dna-header" aria-label={c.profile}>
            <p className="eyebrow">
              {index.competition} / {index.season}
            </p>
            <h2>{detail.player.name}</h2>
            <p className="dna-team">
              {detail.player.teams.join(" · ")} ·{" "}
              {detail.player.primary_role ?? c.unavailable}
              {detail.player.multi_role ? ` · ${c.multi}` : ""}
            </p>
            <dl className="dna-evidence">
              <div>
                <dt>{c.minutes}</dt>
                <dd>{number(detail.player.minutes, 0)}</dd>
              </div>
              <div>
                <dt>{c.matches}</dt>
                <dd>{detail.player.appearances}</dd>
              </div>
              <div>
                <dt>{c.threshold}</dt>
                <dd>{number(threshold, 0)}</dd>
              </div>
              <div>
                <dt>{c.version}</dt>
                <dd>{detail.version}</dd>
              </div>
            </dl>
            <p className="note">
              {c.compared}{" "}
              {detail.eligible && (
                <strong>
                  {detail.comparison_size} {c.cohort}.
                </strong>
              )}{" "}
              <a href={route(locale, "methodology") + "#player-dna"}>
                {c.methodology} ↗
              </a>
            </p>
            <p className="note">
              {c.roleMix}:{" "}
              {Object.entries(detail.player.role_shares)
                .sort((a, b) => b[1] - a[1])
                .map(([r, s]) => `${r} ${number(s * 100, 0)}%`)
                .join(" · ") || c.unavailable}
            </p>
          </section>
          {!detail.eligible ? (
            <section className="dna-ineligible" role="status">
              <h3>{c.low}</h3>
              {detail.exclusions.map((reason) => (
                <p key={reason}>{c[reason as keyof typeof c] as string}</p>
              ))}
            </section>
          ) : null}
          <div className="dna-main-grid">
            <section className="dna-profile">
              <h3>{c.profile}</h3>
              <p className="note">
                {c.percentile} · {c.more}
              </p>
              {Object.entries(families[locale]).map(([family, name]) => (
                <div className="dna-family" key={family}>
                  <h4>{name}</h4>
                  {detail.features
                    .filter(
                      (f) =>
                        displayed.includes(f.id) &&
                        definitions[f.id].family === family,
                    )
                    .map((f) => (
                      <div className="dna-bar-row" key={f.id}>
                        <span
                          title={
                            locale === "nl"
                              ? definitions[f.id].note_nl
                              : definitions[f.id].note_en
                          }
                        >
                          {label(f.id)}
                        </span>
                        <span className="dna-bar" aria-hidden="true">
                          <span style={{ width: `${f.percentile ?? 0}%` }} />
                        </span>
                        <strong>
                          {f.percentile == null
                            ? c.unavailable
                            : number(f.percentile, 0)}
                        </strong>
                        <small>
                          {number(f.value)} {definitions[f.id].unit}
                        </small>
                      </div>
                    ))}
                </div>
              ))}
              <details className="dna-outputs">
                <summary>{c.output}</summary>
                <dl className="event-list">
                  {detail.features
                    .filter((f) => definitions[f.id].family === "output")
                    .map((f) => (
                      <div key={f.id}>
                        <dt>{label(f.id)}</dt>
                        <dd>
                          {number(f.value)} {definitions[f.id].unit}
                        </dd>
                      </div>
                    ))}
                </dl>
              </details>
            </section>
            <section className="dna-neighbors">
              <h3>{c.neighbors}</h3>
              <p className="note">{c.distanceNote}</p>
              {detail.eligible ? (
                <>
                  <div className="table-wrap">
                    <table>
                      <caption className="sr-only">{c.neighbors}</caption>
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>{c.select}</th>
                          <th>{c.distance}</th>
                          <th>{c.stability}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.neighbors.slice(0, 10).map((n) => (
                          <tr
                            key={n.player_id}
                            className={
                              comparison === n.player_id ? "selected-row" : ""
                            }
                          >
                            <td>{n.rank}</td>
                            <th scope="row">
                              <button
                                className="text-button"
                                onClick={() => setComparison(n.player_id)}
                                aria-pressed={comparison === n.player_id}
                                aria-label={`${c.compare} ${n.name}`}
                              >
                                {n.name}
                              </button>
                              <small>
                                {n.teams.join(" / ")} · {n.role} ·{" "}
                                {number(n.minutes, 0)} min
                              </small>
                            </th>
                            <td className="num">{number(n.distance, 2)}</td>
                            <td className="num">
                              {number(n.stability * 100, 0)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="note">{c.stabilityNote}</p>
                  <p className="note">
                    {c.jaccard}: {number(detail.neighbor_jaccard, 2)}
                  </p>
                </>
              ) : (
                <p className="state">{c.unavailable}</p>
              )}
            </section>
          </div>
          {compare && (
            <section className="dna-comparison" aria-label={c.compareTitle}>
              <h3>{c.compareTitle}</h3>
              <h2>
                {detail.player.name} <span> / </span>
                {compare.name}
              </h2>
              <p className="note">
                {detail.player.primary_role} · {index.season} ·{" "}
                {number(detail.player.minutes, 0)} /{" "}
                {number(compare.minutes, 0)} {c.minutes}
              </p>
              <div className="dna-comparison-notes">
                <div>
                  <h4>{c.similar}</h4>
                  <ul>
                    {compare.similar.map((id) => (
                      <li key={id}>{label(id)}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4>{c.different}</h4>
                  <ul>
                    {compare.different.map((id) => (
                      <li key={id}>
                        {label(id)}:{" "}
                        {compare.contributions.find((v) => v.feature === id)!
                          .standardized_difference > 0
                          ? compare.name
                          : detail.player.name}{" "}
                        {locale === "en" ? "higher" : "hoger"}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4>{c.contribution}</h4>
                  <dl className="event-list">
                    {Object.entries(compare.family_contributions).map(
                      ([f, v]) => (
                        <div key={f}>
                          <dt>{families[locale][f]}</dt>
                          <dd>{number(100 * v, 1)}%</dd>
                        </div>
                      ),
                    )}
                  </dl>
                </div>
              </div>
              {pair?.error ? (
                <p role="alert">
                  {c.error}{" "}
                  <button onClick={() => setRetry(retry + 1)}>{c.retry}</button>
                </p>
              ) : !pair?.data ? (
                <p role="status">{c.loading}</p>
              ) : (
                <div className="table-wrap">
                  <table>
                    <caption>
                      {c.percentile} · {c.more}
                    </caption>
                    <thead>
                      <tr>
                        <th>{c.profile}</th>
                        <th>{detail.player.name}</th>
                        <th>{pair.data.player.name}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.features
                        .filter((f) => displayed.includes(f.id))
                        .map((f) => (
                          <tr key={f.id}>
                            <th>{label(f.id)}</th>
                            <td>
                              {number(f.percentile, 0)}{" "}
                              <small>
                                {number(f.value)} {definitions[f.id].unit}
                              </small>
                            </td>
                            <td>
                              {number(
                                pair.data?.features.find((q) => q.id === f.id)
                                  ?.percentile,
                                0,
                              )}{" "}
                              <small>
                                {number(
                                  pair.data?.features.find((q) => q.id === f.id)
                                    ?.value,
                                )}{" "}
                                {definitions[f.id].unit}
                              </small>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}
          <div className="dna-secondary-grid">
            <section>
              <h3>{c.territory}</h3>
              <svg
                viewBox="0 0 105 68"
                className="dna-territory"
                role="img"
                aria-label={`${c.territory}: ${detail.player.name}`}
              >
                <rect width="105" height="68" fill="#eef2ec" />
                {detail.bins.map(([x, y, count]) => (
                  <rect
                    key={`${x}-${y}`}
                    x={(x * 105) / 12}
                    y={((7 - y) * 68) / 8}
                    width={105 / 12}
                    height={68 / 8}
                    fill="#17583f"
                    opacity={
                      0.12 +
                      (0.8 * count) /
                        Math.max(1, ...detail.bins.map((b) => b[2]))
                    }
                  />
                ))}
                <g fill="none" stroke="#52675b" strokeWidth=".3">
                  <rect x=".5" y=".5" width="104" height="67" />
                  <path d="M52.5 0v68M0 13.84h16.5v40.32H0M105 13.84H88.5v40.32H105" />
                  <circle cx="52.5" cy="34" r="9.15" />
                </g>
              </svg>
              <p className="note">{c.territoryNote}</p>
              <details>
                <summary>{c.territoryTable}</summary>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>{c.cell}</th>
                        <th>{c.count}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.bins.map(([x, y, v]) => (
                        <tr key={`${x}-${y}`}>
                          <td>
                            {x + 1}, {y + 1}
                          </td>
                          <td>{v}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            </section>
            <section>
              <h3>{c.map}</h3>
              <p className="note">{c.mapNote}</p>
              <button
                onClick={() => setMapOpen(!mapOpen)}
                aria-expanded={mapOpen}
              >
                {c.selectMap}
              </button>
              {mapOpen &&
                (map?.error ? (
                  <p role="alert">{c.error}</p>
                ) : !map?.data ? (
                  <p role="status">{c.loading}</p>
                ) : (
                  <ProfileMap
                    data={map.data}
                    selected={activeId!}
                    neighbors={detail.neighbors
                      .slice(0, 10)
                      .map((n) => n.player_id)}
                    locale={locale}
                    select={(id) => {
                      setQuery("");
                      setTeam("");
                      setRole("");
                      choose(id);
                    }}
                  />
                ))}
            </section>
          </div>
        </>
      )}
      <Evaluation
        locale={locale}
        evaluation={evaluation}
        threshold={threshold}
      />
      <p className="note dna-limits">{c.notQuality}</p>
    </div>
  );
}
function ProfileMap({
  data,
  selected,
  neighbors,
  locale,
  select,
}: {
  data: DNAMap;
  selected: string;
  neighbors: string[];
  locale: Locale;
  select: (id: string) => void;
}) {
  const c = dnaCopy[locale];
  const maxX = Math.max(...data.points.map((p) => Math.abs(p.x)), 1);
  const maxY = Math.max(...data.points.map((p) => Math.abs(p.y)), 1);
  const symbols: Record<string, string> = {
    CB: "●",
    CM: "■",
    DM: "◆",
    "FB/WB": "▲",
    ST: "▼",
    W: "✚",
  };
  return (
    <>
      <svg
        className="dna-map"
        viewBox="0 0 500 330"
        role="group"
        aria-label={c.map}
      >
        {data.points.map((p) => (
          <g
            key={p.player_id}
            role="button"
            tabIndex={0}
            aria-label={`${p.name}, ${p.teams.join(", ")}, ${p.role}, ${Math.round(p.minutes)} min`}
            onClick={() => select(p.player_id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                select(p.player_id);
              }
            }}
          >
            <title>
              {p.name} · {p.role} · {Math.round(p.minutes)} min
            </title>
            {neighbors.includes(p.player_id) && (
              <circle
                cx={250 + (p.x / maxX) * 220}
                cy={165 - (p.y / maxY) * 140}
                r="9"
                fill="none"
                stroke="#9b512b"
              />
            )}
            <text
              x={250 + (p.x / maxX) * 220}
              y={165 - (p.y / maxY) * 140}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={p.player_id === selected ? 23 : 10}
              fill={p.player_id === selected ? "#9b512b" : "#17583f"}
            >
              {p.player_id === selected ? "×" : (symbols[p.role] ?? "●")}
            </text>
          </g>
        ))}
      </svg>
      <p className="note">
        {Object.entries(symbols)
          .map(([r, s]) => `${s} ${r}`)
          .join(" · ")}
        <br />
        {c.mapLegend}
      </p>
      <details>
        <summary>{c.mapTable}</summary>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{c.select}</th>
                <th>{c.role}</th>
                <th>{c.minutes}</th>
              </tr>
            </thead>
            <tbody>
              {data.points.map((p) => (
                <tr key={p.player_id}>
                  <th>
                    <button
                      className="text-button"
                      onClick={() => select(p.player_id)}
                    >
                      {p.name}
                    </button>
                  </th>
                  <td>{p.role}</td>
                  <td>{Math.round(p.minutes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
export function Evaluation({
  locale,
  evaluation,
  threshold = 900,
}: {
  locale: Locale;
  evaluation: DNAEvaluation;
  threshold?: number;
}) {
  const c = dnaCopy[locale];
  const fmt = (v: number | null | undefined) =>
    v == null ? "—" : v.toLocaleString(locale, { maximumFractionDigits: 3 });
  return (
    <section className="dna-evaluation">
      <h3>{c.evidence}</h3>
      <p className="note">{c.evaluationNote}</p>
      <div className="table-wrap">
        <table>
          <caption>
            {c.threshold}: {threshold}
          </caption>
          <thead>
            <tr>
              <th>{c.method}</th>
              <th>{c.queries}</th>
              <th>Recall@1</th>
              <th>Recall@5</th>
              <th>Recall@10</th>
              <th>MRR</th>
              <th>{c.jaccard}</th>
            </tr>
          </thead>
          <tbody>
            {evaluation.rows
              .filter(
                (r) =>
                  r.threshold === threshold &&
                  [
                    "standard_scaling",
                    "euclidean",
                    "cosine",
                    "pca",
                    "global_scaling",
                  ].includes(r.method),
              )
              .map((r) => (
                <tr key={r.method}>
                  <th>{methods[locale][r.method]}</th>
                  <td>{r.queries}</td>
                  <td>{fmt(r.recall1)}</td>
                  <td>{fmt(r.recall5)}</td>
                  <td>{fmt(r.recall10)}</td>
                  <td>{fmt(r.mrr)}</td>
                  <td>{fmt(r.bootstrap_jaccard)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <p className="note">
        {c.random}:{" "}
        {fmt(
          evaluation.rows.find((r) => r.threshold === threshold)
            ?.random_recall5,
        )}{" "}
        · {evaluation.bootstrap_samples} bootstrap · seed {evaluation.seed}
      </p>
    </section>
  );
}
