"use client";
import { WyscoutRecruitment } from "./wyscout-recruitment";
import { PlayerAvatar } from "./player-avatar";
import { fetchArtifact } from "@/lib/artifact";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Locale } from "@/lib/content";
import { route } from "@/lib/content";
import type {
  ClubContext,
  RecruitmentBootstrap,
  RecruitmentIndex,
} from "@/lib/contracts";
import {
  activeRequirements,
  defaultScenario,
  newRequirement,
  replaceProfile,
  rankCandidates,
  scenarioStability,
  encodeScenario,
  decodeScenario,
  type Requirement,
  type Scenario,
} from "@/lib/recruitment";
import {
  recruitmentCopy,
  recruitmentFamilies,
  requirementSources,
  recruitmentExclusions,
} from "@/lib/recruitment-copy";

function useArtifact<T>(path: string | null) {
  const [loaded, setLoaded] = useState<{ path: string; value: T } | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    fetchArtifact<T>(`/data/phase4/${path}`, controller.signal)
      .then((value) => {
        setLoaded({ path, value });
        setFailed(null);
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(path);
      });
    return () => controller.abort();
  }, [path, attempt]);
  return {
    data: loaded?.path === path ? loaded.value : null,
    error: failed === path && path !== null,
    retry: () => {
      setFailed(null);
      setAttempt((n) => n + 1);
    },
  };
}
function LegacyRecruitment({ locale }: { locale: Locale }) {
  const c = recruitmentCopy[locale],
    resource = useArtifact<RecruitmentIndex>("index.json");
  if (resource.error)
    return (
      <div className="recruitment-status" role="alert">
        <p>{c.error}</p>
        <button onClick={resource.retry}>{c.retry}</button>
      </div>
    );
  if (!resource.data)
    return (
      <p className="recruitment-status" role="status">
        {c.loading}
      </p>
    );
  return <RecruitmentBoard locale={locale} index={resource.data} />;
}
function RecruitmentBoard({
  locale,
  index,
}: {
  locale: Locale;
  index: RecruitmentIndex;
}) {
  const c = recruitmentCopy[locale],
    language = locale === "en" ? 0 : 1;
  const initial = useMemo(() => {
    try {
      return {
        scenario: window.location.search
          ? decodeScenario(
              window.location.search === "?dataset=wsl"
                ? ""
                : window.location.search,
              index,
            )
          : defaultScenario(index),
        invalid: false,
      };
    } catch {
      return { scenario: defaultScenario(index), invalid: true };
    }
  }, [index]);
  const comparisonRef = useRef<HTMLElement>(null);
  const [inspect, setInspect] = useState(false);
  useEffect(() => {
    if (inspect) {
      comparisonRef.current?.focus();
      setInspect(false);
    }
  }, [inspect]);
  const [scenario, setScenario] = useState<Scenario>(initial.scenario);
  const [invalid, setInvalid] = useState(initial.invalid);
  const [view, setView] = useState<"find" | "replace" | "context">(
    initial.scenario.mode,
  );
  const [advanced, setAdvanced] = useState(false),
    [robustOpen, setRobustOpen] = useState(false);
  const [selected, setSelected] = useState<string[]>([]),
    [shared, setShared] = useState(""),
    [copied, setCopied] = useState(false);
  const context = useArtifact<ClubContext>(`clubs/${scenario.club_id}.json`);
  const result = useMemo(
    () => rankCandidates(index.players, scenario, index.method),
    [index, scenario],
  );
  const bootstrap = useArtifact<RecruitmentBootstrap>(
    robustOpen && result.status === "ok"
      ? `bootstrap/${scenario.target_role.replaceAll("/", "-")}.json`
      : null,
  );
  const stability = useMemo(
    () =>
      robustOpen
        ? scenarioStability(
            index.players,
            scenario,
            index.method,
            bootstrap.data ?? undefined,
          )
        : null,
    [index, scenario, robustOpen, bootstrap.data],
  );
  const active = activeRequirements(scenario),
    roleContext = context.data?.roles.find(
      (r) => r.role === scenario.target_role,
    );
  const players = new Map(index.players.map((p) => [p.player_id, p])),
    features = new Map(index.features.map((f) => [f.id, f]));
  const label = (id: string) => {
    const f = features.get(id);
    return f ? (locale === "en" ? f.label_en : f.label_nl) : id;
  };
  const number = (v: number, d = 1) =>
    v.toLocaleString(locale, { maximumFractionDigits: d });
  const percent = (v: number) => `${number(v * 100, 0)}%`;
  const references = index.players.filter(
    (p) =>
      p.eligible &&
      p.team_ids.includes(scenario.club_id) &&
      p.role === scenario.target_role,
  );
  const selectedRanks = result.rankings.filter((r) =>
    selected.includes(r.player_id),
  );
  const query = encodeScenario(scenario, index);
  useEffect(() => {
    const url = `${window.location.pathname}?${query}`;
    window.history.replaceState(null, "", url);
    const languageLink =
      document.querySelector<HTMLAnchorElement>("a.language");
    if (languageLink)
      languageLink.href = `${route(locale === "en" ? "nl" : "en", "recruitment")}?${query}`;
  }, [query, locale]);
  useEffect(() => {
    const restore = () => {
      try {
        const restored = decodeScenario(
          window.location.search === "?dataset=wsl"
            ? ""
            : window.location.search,
          index,
        );
        setScenario(restored);
        setView(restored.mode);
        setInvalid(false);
      } catch {
        setScenario(defaultScenario(index));
        setInvalid(true);
      }
      setSelected([]);
      setShared("");
      setCopied(false);
    };
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, [index]);
  function update(next: Scenario) {
    const nextQuery = encodeScenario(next, index);
    if (nextQuery !== query)
      window.history.pushState(
        null,
        "",
        `${window.location.pathname}?${nextQuery}`,
      );
    setScenario(next);
    setShared("");
    setCopied(false);
    setInvalid(false);
  }
  function choose(
    next: Scenario,
    mode: "find" | "replace" = view === "replace" ? "replace" : "find",
  ) {
    setSelected([]);
    if (mode === "replace") {
      const reference = index.players.find(
        (p) =>
          p.eligible &&
          p.team_ids.includes(next.club_id) &&
          p.role === next.target_role,
      );
      update(
        reference
          ? replaceProfile(next, reference)
          : {
              ...next,
              mode: "find",
              replacement_player_id: null,
              requirements: [],
              created_from: "custom",
            },
      );
    } else
      update({
        ...next,
        mode: "find",
        replacement_player_id: null,
        created_from: "custom",
      });
  }
  function requirement(id: string, patch: Partial<Requirement>) {
    const previous =
      scenario.requirements.find((r) => r.feature_id === id) ??
      newRequirement(id);
    const changed = { ...previous, ...patch };
    if (changed.preference !== "minimum" && changed.preference !== "maximum")
      changed.hard_constraint = false;
    update({
      ...scenario,
      created_from:
        scenario.mode === "replace" ? "adjusted_replacement" : "custom",
      requirements: [
        ...scenario.requirements.filter((r) => r.feature_id !== id),
        changed,
      ],
    });
  }
  function editRequirement(id: string, patch: Partial<Requirement>) {
    requirement(id, {
      ...patch,
      source: "user_defined",
      type: "style_preference",
    });
  }
  function adopt(
    id: string,
    value: number,
    source: Requirement["source"],
    preference: Requirement["preference"],
  ) {
    requirement(id, {
      preference,
      value,
      source,
      type:
        source === "observed_club_context" ? "club_context" : "target_profile",
      hard_constraint: false,
    });
    setView(scenario.mode);
  }
  async function share() {
    const url = `${window.location.origin}${route(locale, "recruitment")}?${query}`;
    setShared(url);
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }
  const evidenceNote = (
    <aside className="recruitment-translation">
      <span className="eyebrow">{c.translationTitle}</span>
      <p>{c.translationWarning}</p>
      <small>{c.translationPeriod}</small>
      <a href={route(locale, "translation")}>{c.translationLink} ↗</a>
    </aside>
  );
  return (
    <div
      className={`recruitment ${advanced ? "requirements-advanced" : "requirements-simple"}`}
    >
      <div className="recruitment-toolbar">
        <p className="eyebrow">
          {index.competition} · {c.observed}
        </p>
        <div>
          {result.status === "ok" && view !== "context" && (
            <a className="shortlist-jump" href="#shortlist-title">
              {c.shortlist} ↓
            </a>
          )}
          <button
            onClick={() => {
              update(defaultScenario(index));
              setView("find");
              setSelected([]);
              setAdvanced(false);
              setRobustOpen(false);
            }}
          >
            {c.reset}
          </button>
          <button onClick={share}>{copied ? c.copied : c.share} ↗</button>
        </div>
      </div>
      {shared && (
        <div className="share-result" role="status">
          <label>
            {copied ? c.copied : c.shareError}
            <input
              aria-label={c.shareFallback}
              value={shared}
              readOnly
              onFocus={(e) => e.currentTarget.select()}
            />
          </label>
        </div>
      )}
      {invalid && (
        <p className="recruitment-warning" role="alert">
          {c.invalid}
        </p>
      )}
      <div
        className="recruitment-modes"
        aria-label={
          locale === "en" ? "Recruitment views" : "Recruitmentweergaven"
        }
      >
        {(["find", "replace", "context"] as const).map((mode) => (
          <button
            key={mode}
            aria-pressed={view === mode}
            onClick={() => {
              setView(mode);
              if (mode === "find")
                choose(
                  {
                    ...scenario,
                    requirements:
                      scenario.mode === "replace" ? [] : scenario.requirements,
                  },
                  mode,
                );
              if (mode === "replace") choose(scenario, mode);
            }}
          >
            {c[mode]}
          </button>
        ))}
      </div>
      <ol
        className="recruitment-steps"
        aria-label={
          locale === "en" ? "Build a shortlist" : "Shortlist samenstellen"
        }
      >
        <li>1. {locale === "en" ? "Club" : "Club"}</li>
        <li>2. {locale === "en" ? "Position" : "Positie"}</li>
        <li>
          3.{" "}
          {view === "replace"
            ? locale === "en"
              ? "Reference player"
              : "Referentiespeler"
            : locale === "en"
              ? "Requirements"
              : "Eisen"}
        </li>
        <li>4. {c.shortlist}</li>
      </ol>
      <div className="recruitment-selectors">
        <label>
          {c.club}
          <select
            value={scenario.club_id}
            onChange={(e) => choose({ ...scenario, club_id: e.target.value })}
          >
            {index.clubs.map((club) => (
              <option key={club.club_id} value={club.club_id}>
                {club.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          {c.role}
          <select
            value={scenario.target_role}
            onChange={(e) =>
              choose({
                ...scenario,
                target_role: e.target.value as Scenario["target_role"],
              })
            }
          >
            {!index.roles.includes(scenario.target_role) && (
              <option value={scenario.target_role} disabled>
                {c.sparseRole}
              </option>
            )}
            {index.roles.map((role) => (
              <option key={role} value={role}>
                {role === "AM" ? c.sparseRole : role}
              </option>
            ))}
          </select>
        </label>
        {view === "replace" && (
          <label>
            {c.reference}
            <select
              value={scenario.replacement_player_id ?? ""}
              disabled={!references.length}
              onChange={(e) => {
                update(replaceProfile(scenario, players.get(e.target.value)!));
                setSelected([]);
              }}
            >
              {!references.length && <option value="">{c.unavailable}</option>}
              {references.map((p) => (
                <option key={p.player_id} value={p.player_id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      {context.data && view !== "context" && (
        <p className="club-summary">
          {context.data.name} · {scenario.target_role} · {context.data.matches}{" "}
          {c.matches} · 2023/24
        </p>
      )}
      {view !== "context" ? (
        <>
          <div className="recruitment-workspace">
            <div className="recruitment-setup">
              {view === "replace" && !references.length ? (
                <p role="status" className="recruitment-warning">
                  {c.noReference}
                </p>
              ) : (
                <details
                  key={view}
                  open={view !== "replace"}
                  className="requirements-disclosure"
                >
                  <summary>
                    {view === "replace"
                      ? locale === "en"
                        ? "Adjust requirements"
                        : "Eisen aanpassen"
                      : locale === "en"
                        ? "3. What are you looking for?"
                        : "3. Wat zoek je?"}
                  </summary>
                  <section
                    className="requirements-panel"
                    aria-labelledby="requirements-title"
                  >
                    <div className="recruitment-section-heading">
                      <div>
                        <h2 id="requirements-title">{c.custom}</h2>
                      </div>
                      <label className="check-label">
                        <input
                          type="checkbox"
                          checked={advanced}
                          onChange={(e) => setAdvanced(e.target.checked)}
                        />
                        {c.advanced}
                      </label>
                    </div>
                    <p className="section-intro">
                      {scenario.mode === "replace"
                        ? c.replacementNote
                        : c.customNote}
                    </p>
                    {scenario.replacement_player_id &&
                      players.get(scenario.replacement_player_id)
                        ?.multi_club && <p className="note">{c.multiClub}</p>}

                    {!advanced &&
                      (scenario.requirements.some(
                        (r) => r.hard_constraint || r.weight !== 1,
                      ) ||
                        Object.values(scenario.family_weights).some(
                          (w) => w !== 1,
                        )) && (
                        <p className="small">
                          {locale === "en"
                            ? "This scenario includes advanced weights or constraints. Open Advanced requirements to inspect them."
                            : "Dit scenario bevat geavanceerde wegingen of voorwaarden. Open Geavanceerde eisen om ze te bekijken."}
                        </p>
                      )}
                    <div className="requirement-groups">
                      {Object.entries(recruitmentFamilies).map(
                        ([family, names]) => {
                          const visible = index.features.filter(
                            (f) =>
                              f.core &&
                              f.family === family &&
                              (advanced ||
                                index.features
                                  .filter(
                                    (feature) =>
                                      feature.core &&
                                      feature.default_visibility.includes(
                                        scenario.target_role,
                                      ),
                                  )
                                  .slice(0, 5)
                                  .some((feature) => feature.id === f.id) ||
                                scenario.requirements.some(
                                  (r) =>
                                    r.feature_id === f.id &&
                                    r.preference !== "neutral",
                                )),
                          );
                          if (!visible.length) return null;
                          return (
                            <fieldset
                              className="requirement-family"
                              key={family}
                            >
                              <legend>{names[language]}</legend>
                              <label className="family-weight">
                                {c.familyImportance}
                                <select
                                  value={scenario.family_weights[family] ?? 1}
                                  onChange={(e) =>
                                    update({
                                      ...scenario,
                                      family_weights: {
                                        ...scenario.family_weights,
                                        [family]: Number(e.target.value) as
                                          1 | 2 | 3,
                                      },
                                    })
                                  }
                                >
                                  {[c.low, c.medium, c.high].map((name, i) => (
                                    <option key={name} value={i + 1}>
                                      {name}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              {visible.map((f) => {
                                const r =
                                    scenario.requirements.find(
                                      (r) => r.feature_id === f.id,
                                    ) ?? newRequirement(f.id),
                                  median = roleContext?.median[f.id];
                                return (
                                  <div
                                    key={f.id}
                                    className={`requirement-row ${r.preference !== "neutral" ? "is-active" : ""}`}
                                    data-feature={f.id}
                                  >
                                    <div className="requirement-name">
                                      <strong>{label(f.id)}</strong>
                                      <details className="requirement-context">
                                        <summary>
                                          {locale === "en"
                                            ? "Club reference & source"
                                            : "Clubreferentie & bron"}
                                        </summary>
                                        <small>
                                          {c.source}:{" "}
                                          {
                                            requirementSources[r.source][
                                              language
                                            ]
                                          }
                                        </small>
                                        {median !== undefined && (
                                          <small>
                                            {c.roleMedian}: {number(median)} ·{" "}
                                            {c.roleRange}:{" "}
                                            {number(roleContext!.minimum[f.id])}
                                            –
                                            {number(roleContext!.maximum[f.id])}{" "}
                                            <button
                                              className="inline-button"
                                              onClick={() =>
                                                adopt(
                                                  f.id,
                                                  median,
                                                  "derived_roster_gap",
                                                  "exact",
                                                )
                                              }
                                            >
                                              {c.useMedian}
                                            </button>
                                          </small>
                                        )}
                                      </details>
                                    </div>
                                    <label>
                                      {advanced
                                        ? c.preference
                                        : locale === "en"
                                          ? "Looking for"
                                          : "Gezocht profiel"}
                                      <select
                                        aria-label={`${label(f.id)}: ${c.preference}`}
                                        value={r.preference}
                                        onChange={(e) =>
                                          editRequirement(f.id, {
                                            preference: e.target
                                              .value as Requirement["preference"],
                                          })
                                        }
                                      >
                                        {(
                                          [
                                            "neutral",
                                            "exact",
                                            "minimum",
                                            "maximum",
                                          ] as const
                                        )
                                          .filter(
                                            (p) =>
                                              advanced ||
                                              p !== "maximum" ||
                                              r.preference === "maximum",
                                          )
                                          .map((p) => (
                                            <option key={p} value={p}>
                                              {c[p]}
                                            </option>
                                          ))}
                                      </select>
                                    </label>
                                    <label>
                                      {c.target}
                                      <input
                                        aria-label={`${label(f.id)}: ${c.target}`}
                                        type="number"
                                        min={0}
                                        max={100}
                                        step="any"
                                        disabled={r.preference === "neutral"}
                                        value={r.value}
                                        onChange={(e) =>
                                          editRequirement(f.id, {
                                            value: Math.min(
                                              100,
                                              Math.max(
                                                0,
                                                Number(e.target.value),
                                              ),
                                            ),
                                          })
                                        }
                                      />
                                    </label>
                                    <label>
                                      {c.importance}
                                      <select
                                        aria-label={`${label(f.id)}: ${c.importance}`}
                                        disabled={r.preference === "neutral"}
                                        value={r.weight}
                                        onChange={(e) =>
                                          editRequirement(f.id, {
                                            weight: Number(e.target.value) as
                                              1 | 2 | 3,
                                          })
                                        }
                                      >
                                        {[c.low, c.medium, c.high].map(
                                          (name, i) => (
                                            <option key={name} value={i + 1}>
                                              {name}
                                            </option>
                                          ),
                                        )}
                                      </select>
                                    </label>
                                    <label
                                      className="check-label hard-constraint"
                                      hidden={!advanced}
                                    >
                                      <input
                                        aria-label={`${label(f.id)}: ${c.required}`}
                                        type="checkbox"
                                        checked={r.hard_constraint}
                                        disabled={
                                          !["minimum", "maximum"].includes(
                                            r.preference,
                                          )
                                        }
                                        onChange={(e) =>
                                          editRequirement(f.id, {
                                            hard_constraint: e.target.checked,
                                          })
                                        }
                                      />
                                      {c.required}
                                    </label>
                                  </div>
                                );
                              })}
                            </fieldset>
                          );
                        },
                      )}
                    </div>
                    <details className="feature-definitions">
                      <summary>{c.definitions}</summary>
                      <p>{c.defaultWeights}</p>
                      {index.features
                        .filter((f) => f.core)
                        .map((f) => (
                          <p key={f.id}>
                            <strong>
                              {label(f.id)} · {f.unit}
                            </strong>
                            <br />
                            {locale === "en" ? f.note_en : f.note_nl}
                          </p>
                        ))}
                    </details>
                  </section>
                </details>
              )}
              <details className="recruitment-filters">
                <summary>{c.constraints}</summary>
                <div>
                  <label>
                    {c.minimumMinutes}
                    <select
                      value={scenario.hard_constraints.minimum_minutes}
                      onChange={(e) =>
                        update({
                          ...scenario,
                          hard_constraints: {
                            ...scenario.hard_constraints,
                            minimum_minutes: Number(e.target.value),
                          },
                        })
                      }
                    >
                      {[
                        ...new Set([
                          900,
                          1200,
                          1800,
                          scenario.hard_constraints.minimum_minutes,
                        ]),
                      ]
                        .sort((a, b) => a - b)
                        .map((n) => (
                          <option key={n} value={n}>
                            {n}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    {c.evidenceThreshold}
                    <select
                      value={
                        scenario.hard_constraints.minimum_neighbor_stability
                      }
                      onChange={(e) =>
                        update({
                          ...scenario,
                          hard_constraints: {
                            ...scenario.hard_constraints,
                            minimum_neighbor_stability: Number(e.target.value),
                          },
                        })
                      }
                    >
                      {[
                        ...new Set([
                          0,
                          0.5,
                          0.7,
                          scenario.hard_constraints.minimum_neighbor_stability,
                        ]),
                      ]
                        .sort((a, b) => a - b)
                        .map((n) => (
                          <option key={n} value={n}>
                            {n === 0 ? c.anyEvidence : number(n, 2)}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    {c.candidateTeam}
                    <select
                      value={scenario.hard_constraints.candidate_team_id ?? ""}
                      onChange={(e) =>
                        update({
                          ...scenario,
                          hard_constraints: {
                            ...scenario.hard_constraints,
                            candidate_team_id: e.target.value || null,
                          },
                        })
                      }
                    >
                      <option value="">{c.allTeams}</option>
                      {index.clubs.map((club) => (
                        <option key={club.club_id} value={club.club_id}>
                          {club.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="check-label">
                    <input
                      type="checkbox"
                      checked={scenario.hard_constraints.exclude_same_club}
                      onChange={(e) =>
                        update({
                          ...scenario,
                          hard_constraints: {
                            ...scenario.hard_constraints,
                            exclude_same_club: e.target.checked,
                          },
                        })
                      }
                    />
                    {c.excludeClub}
                  </label>
                </div>
              </details>
              <a
                className="primary-action shortlist-action"
                href="#shortlist-title"
              >
                {locale === "en" ? "Find candidates" : "Vind kandidaten"} →
              </a>
              <span className="live-hint">
                {locale === "en"
                  ? "Updates as you adjust requirements"
                  : "Werkt bij zodra je eisen aanpast"}
              </span>
            </div>
            <section
              className="recruitment-results"
              aria-labelledby="shortlist-title"
            >
              <div className="recruitment-section-heading">
                <div>
                  <h2 id="shortlist-title">{c.shortlist}</h2>
                </div>
                <p className="candidate-count" role="status">
                  <strong>{result.eligible_count}</strong> {c.available}
                  <br />
                  <small>
                    {result.exclusions.length} {c.excluded}
                  </small>
                </p>
              </div>
              <p className="section-intro">{c.shortlistNote}</p>

              {result.status !== "ok" ? (
                <div className="recruitment-empty" role="status">
                  {result.status === "no_requirements"
                    ? c.noRequirements
                    : c.noCandidates}
                </div>
              ) : (
                <>
                  <div className="table-wrap recruitment-table">
                    <table>
                      <caption className="sr-only">{c.shortlist}</caption>
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>{c.player}</th>
                          <th>{c.fit}</th>
                          <th>{c.evidence}</th>
                          <th>
                            {c.keyMatch} / {c.mismatch}
                          </th>
                          <th>{c.compare}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.rankings.slice(0, 10).map((r) => {
                          const p = players.get(r.player_id)!,
                            strong = r.contributions.find(
                              (x) => x.feature_id === r.strong_matches[0],
                            ),
                            weak = r.contributions.find(
                              (x) => x.feature_id === r.main_mismatches[0],
                            );
                          return (
                            <tr key={p.player_id} data-player={p.player_id}>
                              <td className="rank-number">
                                {r.rank.toString().padStart(2, "0")}
                              </td>
                              <th scope="row" className="candidate-identity">
                                <PlayerAvatar
                                  id={p.player_id}
                                  name={p.name}
                                  locale={locale}
                                />
                                <button
                                  className="candidate-name"
                                  onClick={() => {
                                    setSelected([p.player_id]);
                                    setInspect(true);
                                  }}
                                  aria-label={`${locale === "en" ? "Why this player matches" : "Waarom deze speler past"}: ${p.name}`}
                                >
                                  {p.name}
                                </button>
                                <small>
                                  {p.teams.join(" · ")} · {p.role}
                                </small>
                                {p.multi_club && <small>{c.multiClub}</small>}
                              </th>
                              <td>
                                <strong className="fit-distance">
                                  {number(r.distance)}
                                </strong>
                                <small>{c.gap}</small>
                              </td>
                              <td>
                                {number(p.minutes, 0)} {c.minutes.toLowerCase()}
                                <details>
                                  <summary>
                                    {locale === "en"
                                      ? "Profile stability"
                                      : "Profielstabiliteit"}
                                  </summary>
                                  <small>
                                    {c.neighbor}:{" "}
                                    {p.neighbor_stability === null
                                      ? c.unavailable
                                      : number(p.neighbor_stability, 2)}
                                  </small>
                                </details>
                              </td>
                              <td className="match-explanation">
                                <span>
                                  +{" "}
                                  {strong
                                    ? `${label(strong.feature_id)} · ${number(strong.mismatch)} ${c.gap}`
                                    : c.unavailable}
                                </span>
                                <small>
                                  ↔{" "}
                                  {weak
                                    ? `${label(weak.feature_id)} · ${number(weak.mismatch)} ${c.gap}`
                                    : c.none}
                                </small>
                              </td>
                              <td>
                                <input
                                  type="checkbox"
                                  aria-label={`${c.compare}: ${p.name}`}
                                  checked={selectedRanks.some(
                                    (x) => x.player_id === p.player_id,
                                  )}
                                  disabled={
                                    selectedRanks.length >= 3 &&
                                    !selected.includes(p.player_id)
                                  }
                                  onChange={(e) =>
                                    setSelected(
                                      e.target.checked
                                        ? [
                                            ...selectedRanks.map(
                                              (x) => x.player_id,
                                            ),
                                            p.player_id,
                                          ]
                                        : selected.filter(
                                            (id) => id !== p.player_id,
                                          ),
                                    )
                                  }
                                />
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <p className="note">
                    {c.compareMax} · {selectedRanks.length} {c.selected}
                  </p>
                  <details className="frontier-explanation">
                    <summary>
                      {result.frontier_count} / {result.eligible_count}{" "}
                      {c.frontierCount}
                    </summary>
                    <p>{c.frontierNote}</p>
                    <p>{c.cohortNote}</p>
                    {result.frontier_count > result.eligible_count / 2 && (
                      <p>{c.frontierMany}</p>
                    )}
                  </details>
                  <details
                    className="robustness-panel"
                    open={robustOpen}
                    onToggle={(e) => setRobustOpen(e.currentTarget.open)}
                  >
                    <summary>{c.robustness}</summary>
                    <div className="robustness-notes">
                      <p>
                        <strong>{c.weights}</strong>
                        <br />
                        {c.weightNote}
                      </p>
                      <p>
                        <strong>{c.profiles}</strong>
                        <br />
                        {c.profileNote}
                      </p>
                    </div>
                    {result.eligible_count <= 10 && (
                      <p className="recruitment-warning">{c.smallPool}</p>
                    )}
                    {bootstrap.error ? (
                      <p role="alert">
                        {c.profileError}{" "}
                        <button onClick={bootstrap.retry}>{c.retry}</button>
                      </p>
                    ) : (
                      !bootstrap.data && <p role="status">{c.profileLoading}</p>
                    )}
                    {stability && (
                      <div
                        className="table-wrap"
                        tabIndex={0}
                        role="region"
                        aria-label={c.evidence}
                      >
                        <table>
                          <caption>
                            {c.inclusion} · {c.rankRange}
                          </caption>
                          <thead>
                            <tr>
                              <th>{c.player}</th>
                              <th>{c.weights}</th>
                              <th>{c.profiles}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {result.rankings.slice(0, 10).map((r) => {
                              const w = stability.weight.players[r.player_id],
                                p = stability.profile?.players[r.player_id];
                              return (
                                <tr key={r.player_id}>
                                  <th scope="row">
                                    {players.get(r.player_id)!.name}
                                  </th>
                                  <td>
                                    {percent(w.top_k_inclusion)} ·{" "}
                                    {number(w.rank_p10)}–{number(w.rank_p90)}
                                  </td>
                                  <td>
                                    {p
                                      ? `${percent(p.top_k_inclusion)} · ${number(p.rank_p10)}–${number(p.rank_p90)}`
                                      : c.unavailable}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </details>
                </>
              )}
            </section>
          </div>
          {selectedRanks.length > 0 && (
            <section
              className="candidate-comparison"
              ref={comparisonRef}
              tabIndex={-1}
            >
              <h2>
                {selectedRanks.length === 1
                  ? locale === "en"
                    ? "Why this player appears here"
                    : "Waarom deze speler hier verschijnt"
                  : c.compareTitle}
              </h2>
              <p>{c.compareNote}</p>
              <div className="comparison-grid">
                {selectedRanks.map((r) => {
                  const p = players.get(r.player_id)!;
                  return (
                    <article key={p.player_id}>
                      <header>
                        <span className="eyebrow">
                          {p.role} · {p.teams.join(" / ")}
                        </span>
                        <h3 className="candidate-photo-heading">
                          <PlayerAvatar
                            id={p.player_id}
                            name={p.name}
                            locale={locale}
                            size="medium"
                          />
                          {p.name}
                        </h3>
                        {r.frontier && (
                          <p title={c.frontierNote}>{c.frontier}</p>
                        )}
                        <p>
                          {number(r.distance)} {c.gap} · {number(p.minutes, 0)}{" "}
                          {c.minutes.toLowerCase()}
                        </p>
                        <small>
                          {c.neighbor}:{" "}
                          {p.neighbor_stability === null
                            ? c.unavailable
                            : number(p.neighbor_stability, 2)}
                        </small>
                      </header>
                      {active.map((req) => {
                        const contribution = r.contributions.find(
                            (x) => x.feature_id === req.feature_id,
                          )!,
                          median = roleContext?.median[req.feature_id];
                        return (
                          <div
                            key={req.feature_id}
                            className="comparison-feature"
                          >
                            <strong>{label(req.feature_id)}</strong>
                            <div
                              className="percentile-track"
                              aria-hidden="true"
                            >
                              <span
                                style={{ width: `${contribution.candidate}%` }}
                              />
                              <i style={{ left: `${req.value}%` }} />
                            </div>
                            <p>
                              {c.playerValue}:{" "}
                              <b>{number(contribution.candidate)}</b> ·{" "}
                              {c[req.preference]}: <b>{number(req.value)}</b>
                            </p>
                            <small>
                              {c.contribution}: {percent(contribution.share)} ·{" "}
                              {c.source}:{" "}
                              {requirementSources[req.source][language]}
                            </small>
                            {median !== undefined && (
                              <small>
                                {c.roleMedian}: {number(median)} · {c.roleRange}
                                : {number(roleContext!.minimum[req.feature_id])}
                                –{number(roleContext!.maximum[req.feature_id])}
                              </small>
                            )}
                          </div>
                        );
                      })}
                      <details>
                        <summary>{c.familyImportance}</summary>
                        {Object.entries(r.family_contributions).map(
                          ([family, share]) => (
                            <p key={family}>
                              {recruitmentFamilies[family][language]}:{" "}
                              {percent(share)} {c.contribution.toLowerCase()}
                            </p>
                          ),
                        )}
                      </details>
                      <a
                        href={
                          route(locale, "player-dna") + "?player=" + p.player_id
                        }
                      >
                        {c.fullDNA} ↗
                      </a>
                    </article>
                  );
                })}
              </div>
            </section>
          )}
          <details className="recruitment-exclusions">
            <summary>
              {c.exclusionsTitle} · {result.exclusions.length}
            </summary>
            <ul tabIndex={0} aria-label={c.exclusionsTitle}>
              {result.exclusions.map((x) => (
                <li key={x.player_id}>
                  <strong>{players.get(x.player_id)?.name}</strong> —{" "}
                  {x.reasons
                    .map((reason) => {
                      const [code, feature] = reason.split(":");
                      return `${recruitmentExclusions[code]?.[language] ?? c.unavailable}${feature ? `: ${label(feature)}` : ""}`;
                    })
                    .join("; ")}
                </li>
              ))}
            </ul>
          </details>
        </>
      ) : (
        <section className="club-context">
          {context.error ? (
            <div role="alert">
              <p>{c.error}</p>
              <button onClick={context.retry}>{c.retry}</button>
            </div>
          ) : !context.data ? (
            <p role="status">{c.loading}</p>
          ) : (
            <>
              <div className="recruitment-section-heading">
                <div>
                  <span className="eyebrow">
                    {c.window}: {context.data.observation_start} →{" "}
                    {context.data.observation_end}
                  </span>
                  <h2>{context.data.name}</h2>
                </div>
                <span className="club-match-count">
                  {context.data.matches}
                  <small>{c.matches}</small>
                </span>
              </div>
              <h3>{c.teamStyle}</h3>
              <p className="section-intro">{c.contextNote}</p>
              <p className="recruitment-warning">{c.adoptNote}</p>
              <div className="team-feature-grid">
                {context.data.features.map((f) => (
                  <article key={f.feature_id}>
                    <h4>
                      {features.has(f.feature_id)
                        ? label(f.feature_id)
                        : locale === "en"
                          ? "Non-penalty xG"
                          : "xG zonder penalty's"}
                    </h4>
                    <div className="percentile-track" aria-hidden="true">
                      <span style={{ width: `${f.percentile ?? 0}%` }} />
                    </div>
                    <p>
                      <b>
                        {f.percentile === null
                          ? c.unavailable
                          : number(f.percentile)}
                      </b>{" "}
                      {c.teamPercentile.toLowerCase()}{" "}
                      <span>
                        {f.value === null ? c.unavailable : number(f.value)}{" "}
                        {c.raw.toLowerCase()}
                      </span>
                    </p>
                    {features.get(f.feature_id)?.core &&
                      f.percentile !== null && (
                        <button
                          onClick={() =>
                            adopt(
                              f.feature_id,
                              f.percentile!,
                              "observed_club_context",
                              "minimum",
                            )
                          }
                        >
                          {c.adopt} ↗
                        </button>
                      )}
                  </article>
                ))}
              </div>
              <h3>{c.roster}</h3>
              <p>{c.rosterNote}</p>
              <div
                className="table-wrap"
                tabIndex={0}
                role="region"
                aria-label={c.evidence}
              >
                <table>
                  <caption className="sr-only">{c.roster}</caption>
                  <thead>
                    <tr>
                      <th>{c.role}</th>
                      <th>{c.depth}</th>
                      <th>{c.profileDepth}</th>
                      <th>{c.minutes}</th>
                      <th>{c.concentration}</th>
                      <th>{c.hhi}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {context.data.roles.map((r) => (
                      <tr key={r.role}>
                        <th scope="row">
                          {r.role === "unknown" ? c.unavailable : r.role}
                        </th>
                        <td>{r.roster_depth}</td>
                        <td>{r.profile_depth}</td>
                        <td>{number(r.reliable_minutes, 0)}</td>
                        <td>
                          {r.top_player_minutes_share === null
                            ? c.unavailable
                            : percent(r.top_player_minutes_share)}
                        </td>
                        <td>
                          {r.minutes_hhi === null
                            ? c.unavailable
                            : number(r.minutes_hhi, 2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <h3>
                {scenario.target_role} · {c.roleMedian}
              </h3>
              {!roleContext?.profile_depth ? (
                <p>{c.noRoster}</p>
              ) : (
                <div className="roster-reference-grid">
                  {index.features
                    .filter((f) => f.core)
                    .map((f) => {
                      const median = roleContext.median[f.id];
                      return (
                        <article key={f.id}>
                          <strong>{label(f.id)}</strong>
                          <p>
                            {c.roleMedian}: {number(median)} · {c.roleRange}:{" "}
                            {number(roleContext.minimum[f.id])}–
                            {number(roleContext.maximum[f.id])}
                          </p>
                          <small>
                            P25–P75: {number(roleContext.p25[f.id])}–
                            {number(roleContext.p75[f.id])}
                          </small>
                          <button
                            onClick={() =>
                              adopt(f.id, median, "derived_roster_gap", "exact")
                            }
                          >
                            {c.useMedian} ↗
                          </button>
                        </article>
                      );
                    })}
                </div>
              )}
            </>
          )}
        </section>
      )}
      {context.error && view !== "context" && (
        <p role="alert">
          {c.error} <button onClick={context.retry}>{c.retry}</button>
        </p>
      )}
      {evidenceNote}
      <div className="recruitment-bottom">
        <p>{c.principle}</p>
        <a href={`${route(locale, "methodology")}#recruitment`}>
          {c.methods} ↗
        </a>
      </div>
    </div>
  );
}

export function Recruitment({ locale }: { locale: Locale }) {
  const [dataset, setDataset] = useState("pending");
  useEffect(() => {
    const restore = () => {
      const params = new URLSearchParams(window.location.search);
      setDataset(
        params.get("dataset") === "wyscout" || !window.location.search
          ? "wyscout"
          : "wsl",
      );
    };
    restore();
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, []);
  const [changed, setChanged] = useState(false);
  return (
    <div className="recruitment-workspace">
      <label className="dataset-selector">
        {locale === "en" ? "Dataset / provider" : "Dataset / provider"}
        <select
          value={dataset === "pending" ? "wyscout" : dataset}
          onChange={(e) => {
            setDataset(e.target.value);
            setChanged(true);
            window.history.replaceState(
              null,
              "",
              e.target.value === "wyscout"
                ? "?dataset=wyscout"
                : "?dataset=wsl",
            );
          }}
        >
          <option value="wyscout">
            Wyscout / Pappalardo — Big Five 2017/18
          </option>
          <option value="wsl">StatsBomb — WSL 2023/24</option>
        </select>
      </label>
      {changed && (
        <p role="status">
          {locale === "en"
            ? "Available recruitment features have changed for this dataset. Incompatible requirements were reset."
            : "De beschikbare recruitmentkenmerken zijn gewijzigd voor deze dataset. Incompatibele criteria zijn gewist."}
        </p>
      )}
      {dataset === "pending" ? (
        <p role="status">
          {locale === "en" ? "Loading dataset…" : "Dataset laden…"}
        </p>
      ) : dataset === "wyscout" ? (
        <WyscoutRecruitment locale={locale} />
      ) : (
        <LegacyRecruitment locale={locale} />
      )}
    </div>
  );
}
