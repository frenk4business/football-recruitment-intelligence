"use client";
import { fetchArtifact } from "@/lib/artifact";
import { useEffect, useState } from "react";
import type {
  TranslationIndex,
  TranslationPlayerDetail,
  TranslationEstimate,
  TranslationEvaluation as EvaluationData,
} from "@/lib/contracts";
import { route, type Locale } from "@/lib/content";
import {
  translationCopy,
  translationMethods,
  translationExclusions,
} from "@/lib/translation-copy";

const normalized = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
const number = (value: number, locale: Locale) =>
  value.toLocaleString(locale, {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  });
const methodName = (method: string, locale: Locale) =>
  translationMethods[method]?.[locale === "en" ? 0 : 1] ?? method;

function Ranges({
  estimates,
  index,
  locale,
}: {
  estimates: TranslationEstimate[];
  index: TranslationIndex;
  locale: Locale;
}) {
  const c = translationCopy[locale];
  return (
    <div className="translation-ranges">
      {estimates.map((e) => {
        const metric = index.metrics.find((m) => m.id === e.metric)!;
        const max =
          Math.max(e.p90, e.observed_source, e.expected_target, 0.1) * 1.12;
        const x = (value: number) => 12 + (376 * value) / max;
        return (
          <article className="translation-metric" key={e.metric}>
            <div className="translation-metric-title">
              <h3>{locale === "en" ? metric.label_en : metric.label_nl}</h3>
              <p>
                {methodName(e.method, locale)} · {c.per90}
              </p>
            </div>
            <div className="translation-range">
              <div className="translation-range-label">
                <strong>
                  {number(e.p10, locale)}–{number(e.p90, locale)}
                </strong>
                <span>{c.range}</span>
              </div>
              <svg
                viewBox="0 0 400 58"
                role="img"
                aria-label={`${c.range}: ${number(e.p10, locale)}–${number(e.p90, locale)}; ${c.observed}: ${number(e.observed_source, locale)}; ${c.expected}: ${number(e.expected_target, locale)}`}
              >
                <line x1="12" x2="388" y1="22" y2="22" stroke="#b9bdb4" />
                <rect
                  x={x(e.p10)}
                  y="15"
                  width={Math.max(1, x(e.p90) - x(e.p10))}
                  height="14"
                  rx="3"
                  fill="#bdcdc4"
                />
                <circle
                  cx={x(e.observed_source)}
                  cy="22"
                  r="5"
                  fill="#faf9f5"
                  stroke="#5e675f"
                  strokeWidth="2"
                />
                <circle
                  cx={x(e.expected_target)}
                  cy="22"
                  r="4"
                  fill="#173e32"
                />
                <text x="12" y="51" fontSize="11" fill="#5e675f">
                  0
                </text>
                <text
                  x="388"
                  y="51"
                  textAnchor="end"
                  fontSize="11"
                  fill="#5e675f"
                >
                  {number(max, locale)}
                </text>
              </svg>
            </div>
            <dl className="translation-values">
              <div>
                <dt>{c.observed}</dt>
                <dd>{number(e.observed_source, locale)}</dd>
              </div>
              <div>
                <dt>{c.expected}</dt>
                <dd>{number(e.expected_target, locale)}</dd>
              </div>
            </dl>
          </article>
        );
      })}
    </div>
  );
}

export function Translation({
  locale,
  index,
}: {
  locale: Locale;
  index: TranslationIndex;
}) {
  const c = translationCopy[locale];
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(
    index.players.find((p) => p.supported_sources > 0)!.player_id,
  );
  const [sourceId, setSourceId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [role, setRole] = useState("");
  const [retry, setRetry] = useState(0);
  const [state, setState] = useState<{
    id: string;
    data?: TranslationPlayerDetail;
    error?: boolean;
  }>();
  const filtered = index.players.filter((p) =>
    normalized(p.name).includes(normalized(query)),
  );
  const playerId = filtered.some((p) => p.player_id === selected)
    ? selected
    : filtered[0]?.player_id;
  useEffect(() => {
    if (!playerId) return;
    setState({ id: playerId });
    const controller = new AbortController();
    fetchArtifact<TranslationPlayerDetail>(
      `/data/phase3/players/${playerId}.json`,
      controller.signal,
    )
      .then((data) => setState({ id: playerId, data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ id: playerId, error: true });
      });
    return () => controller.abort();
  }, [playerId, retry]);
  const detail = state?.id === playerId ? state.data : undefined;
  const source =
    detail?.environments.find((e) => e.environment_id === sourceId) ??
    detail?.environments.find((e) => e.supported) ??
    detail?.environments[0];
  const target =
    index.targets.find((t) => t.environment_id === targetId) ??
    index.targets.find((t) => t.team_id === source?.team_id) ??
    index.targets[0];
  const targetRole =
    role ||
    (source?.role && index.roles.includes(source.role)
      ? source.role
      : index.roles[0]);
  const prediction = detail?.predictions.find(
    (p) =>
      p.source_environment_id === source?.environment_id &&
      p.target_environment_id === target.environment_id &&
      p.target_role === targetRole,
  );
  const exclusions = source?.supported
    ? (prediction?.exclusions ?? [])
    : (source?.exclusions ?? []);
  const evidence = prediction?.evidence;
  const resetPlayer = (value: string) => {
    setSelected(value);
    setSourceId("");
    setRole("");
  };
  return (
    <section className="translation-workflow">
      <div className="translation-selection">
        <label>
          {c.search}
          <input
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSourceId("");
              setRole("");
            }}
            placeholder={locale === "en" ? "Player name…" : "Naam van speler…"}
          />
        </label>
        <label>
          {c.player}
          <select
            aria-label={c.player}
            value={playerId ?? ""}
            onChange={(e) => resetPlayer(e.target.value)}
            disabled={!playerId}
          >
            {filtered.map((p) => (
              <option key={p.player_id} value={p.player_id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {!playerId ? (
        <p className="state" role="status">
          {c.empty}
        </p>
      ) : !detail ? (
        <div
          className="state"
          role={state?.id === playerId && state.error ? "alert" : "status"}
        >
          {state?.id === playerId && state.error ? (
            <>
              <p>{c.error}</p>
              <button onClick={() => setRetry(retry + 1)}>{c.retry}</button>
            </>
          ) : (
            c.loading
          )}
        </div>
      ) : (
        <>
          <div className="translation-scenario">
            <label>
              {c.source}
              <select
                aria-label={c.source}
                value={source!.environment_id}
                onChange={(e) => {
                  setSourceId(e.target.value);
                  setRole("");
                }}
              >
                {detail.environments.map((e) => (
                  <option key={e.environment_id} value={e.environment_id}>
                    {e.team} · {e.season} · {e.role ?? "?"}
                  </option>
                ))}
              </select>
            </label>
            <span className="translation-arrow" aria-hidden="true">
              →
            </span>
            <label>
              {c.target}
              <select
                aria-label={c.target}
                value={target.environment_id}
                onChange={(e) => setTargetId(e.target.value)}
              >
                {index.targets.map((t) => (
                  <option key={t.environment_id} value={t.environment_id}>
                    {t.team} · {t.season}
                  </option>
                ))}
              </select>
            </label>
            <label>
              {c.role}
              <select
                aria-label={c.role}
                value={targetRole}
                onChange={(e) => setRole(e.target.value)}
              >
                {index.roles.map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </label>
          </div>
          <p className="note">{c.selectNote}</p>
          <div className="translation-player">
            <h2>{detail.player.name}</h2>
            <p>
              {source!.competition} · {source!.team} · {source!.season}
            </p>
            <p>
              {Math.round(source!.reliable_minutes).toLocaleString(locale)}{" "}
              {c.minutes} · {source!.appearances} {c.appearances} ·{" "}
              {source!.start_date} – {source!.end_date}
            </p>
            <p>
              {source!.used_as_development_outcome
                ? locale === "en"
                  ? "This source season was also an earlier development outcome. Target-season outcomes remain held out."
                  : "Dit bronseizoen was ook een eerdere ontwikkelwaarneming. Waarnemingen uit het doelseizoen bleven buiten het schatten van het model."
                : locale === "en"
                  ? "This source observation was not used as a development outcome. Target-season outcomes remain held out."
                  : "Deze bronwaarneming is niet gebruikt als ontwikkeluitkomst. Waarnemingen uit het doelseizoen bleven buiten het schatten van het model."}
            </p>
          </div>
          {prediction?.status !== "supported" ? (
            <section className="translation-unavailable" role="status">
              <h3>{c.unsupported}</h3>
              <ul>
                {exclusions.map((r) => (
                  <li key={r}>
                    {translationExclusions[r]?.[locale === "en" ? 0 : 1] ?? r}
                  </li>
                ))}
              </ul>
            </section>
          ) : (
            <>
              <section className="translation-results">
                <p className="eyebrow">{c.supported}</p>
                <h2>{c.results}</h2>
                <p>{c.intervalNote}</p>
                <Ranges
                  estimates={prediction.estimates}
                  index={index}
                  locale={locale}
                />
                <p className="note">{c.baselineNote}</p>
                <p className="translation-caution">{c.calibrationNote}</p>
              </section>
              {evidence && (
                <section className="translation-evidence">
                  <h2>{c.evidence}</h2>
                  <dl>
                    <div>
                      <dd>{evidence.direct_episodes}</dd>
                      <dt>{c.direct}</dt>
                    </div>
                    <div>
                      <dd>{evidence.target_team_role_episodes}</dd>
                      <dt>{c.teamRole}</dt>
                    </div>
                    <div>
                      <dd>{evidence.role_episodes}</dd>
                      <dt>{c.roleCount}</dt>
                    </div>
                    <div>
                      <dd>{evidence.development_episodes}</dd>
                      <dt>{c.development}</dt>
                    </div>
                  </dl>
                  {evidence.relies_on_pooling && (
                    <p className="translation-pooling">{c.pooling}</p>
                  )}
                  <p>{c.directNote}</p>
                  <p className="note">
                    {c.context} {evidence.context_latest_date} ·{" "}
                    {evidence.source_context_matches} /{" "}
                    {evidence.target_context_matches} {c.contextMatches}.{" "}
                    {evidence.unseen_target_team ? c.unseen : ""}
                  </p>
                </section>
              )}
              <details className="translation-research">
                <summary>{c.research}</summary>
                <p>{c.researchNote}</p>
                <Ranges
                  estimates={prediction.research_estimates}
                  index={index}
                  locale={locale}
                />
              </details>
            </>
          )}
          <section className="translation-limits">
            <h2>{c.limits}</h2>
            <p>{c.limitsBody}</p>
            <a href={`${route(locale, "methodology")}#translation`}>
              {c.methodology} ↗
            </a>
          </section>
        </>
      )}
    </section>
  );
}

export function TranslationEvaluation({
  locale,
  index,
  evaluation,
}: {
  locale: Locale;
  index: TranslationIndex;
  evaluation: EvaluationData;
}) {
  const c = translationCopy[locale];
  const label = (id: string) => {
    const m = index.metrics.find((m) => m.id === id)!;
    return locale === "en" ? m.label_en : m.label_nl;
  };
  return (
    <section className="translation-evaluation" id="translation">
      <p className="eyebrow">WSL · 2018/19 → 2019/20 → 2020/21</p>
      <h2>{c.evaluation}</h2>
      <p>{c.evaluationIntro}</p>
      <h3>{c.calibration}</h3>
      <div className="translation-calibration">
        {evaluation.rows
          .filter((r) => r.selected)
          .map((r) => (
            <div key={r.metric}>
              <span>{label(r.metric)}</span>
              <div className="calibration-track">
                <span style={{ width: `${r.coverage80 * 100}%` }} />
                <i style={{ left: "80%" }} aria-hidden="true" />
              </div>
              <strong>{Math.round(r.coverage80 * 100)}%</strong>
            </div>
          ))}
      </div>
      <p className="note">
        {locale === "en"
          ? "Vertical marker: 80% nominal coverage. All rows use the later season (n = 76)."
          : "Verticale lijn: nominale dekking van 80%. Alle rijen gebruiken het latere seizoen (n = 76)."}
      </p>
      <p className="translation-caution">{c.calibrationNote}</p>
      <details>
        <summary>{c.allResults}</summary>
        <div className="table-wrap">
          <table>
            <caption>
              {c.per90} · n = {evaluation.test}
            </caption>
            <thead>
              <tr>
                <th>{c.metric}</th>
                <th>{c.method}</th>
                <th>{c.mae}</th>
                <th>RMSE</th>
                <th>50%</th>
                <th>80%</th>
                <th>95%</th>
                <th>{c.width}</th>
              </tr>
            </thead>
            <tbody>
              {evaluation.rows.map((r) => (
                <tr key={r.metric + r.method}>
                  <th scope="row">{label(r.metric)}</th>
                  <td>
                    {methodName(r.method, locale)}
                    {r.selected && <small>{c.selected}</small>}
                  </td>
                  <td>{number(r.mae, locale)}</td>
                  <td>{number(r.rmse, locale)}</td>
                  <td>{Math.round(r.coverage50 * 100)}%</td>
                  <td>{Math.round(r.coverage80 * 100)}%</td>
                  <td>{Math.round(r.coverage95 * 100)}%</td>
                  <td>{number(r.width80, locale)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      <h3>{c.study}</h3>
      <p>{c.studyBody}</p>
      <p>{c.decisions}</p>
      <p>{c.limitsBody}</p>
      <a href="https://github.com/frenk4business/football-recruitment-intelligence/blob/main/docs/model-card-phase3.md">
        {locale === "en"
          ? "Model card and reproducible research"
          : "Modelkaart en reproduceerbaar onderzoek"}{" "}
        ↗
      </a>
    </section>
  );
}
