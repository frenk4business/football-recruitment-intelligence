"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { fetchArtifact } from "@/lib/artifact";
import { route, type Locale } from "@/lib/content";
import { normalizeName, profileSearchText } from "@/lib/player-search";
import type { ProfileIndex } from "@/lib/profile-contracts";

/** Progressive enhancement: native GET search remains usable without JavaScript. */
export function GlobalSearch({ locale }: { locale: Locale }) {
  const nl = locale === "nl";
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(false);
  const [index, setIndex] = useState<ProfileIndex>();
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (!active || index) return;
    const controller = new AbortController();
    fetchArtifact<ProfileIndex>("/data/v11/index.json", controller.signal)
      .then(setIndex)
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [active, index, retry]);
  const names = useMemo(
    () =>
      index?.profiles.map((p) => ({ p, text: profileSearchText(index, p) })),
    [index],
  );
  const tokens = normalizeName(query.trim()).split(/\s+/).filter(Boolean);
  const matches = (text: string) =>
    tokens.every((t) => normalizeName(text).includes(t));
  const players = names?.filter(({ text }) => matches(text)).slice(0, 4) ?? [];
  const teams = Object.entries(index?.teams ?? {})
    .filter(([, name]) => matches(name))
    .slice(0, 2);
  const competitions = [
    ...new Map(
      index?.scopes
        .filter((s) => matches(s.competition))
        .map((s) => [s.competition_key, s.competition]),
    ).entries(),
  ]
    .filter(([, name]) => matches(name))
    .slice(0, 2);
  const href = (key: string, value: string) =>
    route(locale, "players") + "?" + new URLSearchParams({ [key]: value });
  return (
    <form
      className="global-search"
      role="search"
      action={route(locale, "players")}
      method="get"
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setActive(false);
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") {
          input.current?.focus();
          setActive(false);
        }
      }}
    >
      <label className="sr-only" htmlFor="home-query">
        {nl
          ? "Zoek speler, club of competitie"
          : "Search player, club or competition"}
      </label>
      <div className="global-search-field">
        <input
          id="home-query"
          ref={input}
          name="q"
          type="search"
          autoComplete="off"
          maxLength={100}
          value={query}
          placeholder={
            nl
              ? "Zoek speler, club of competitie…"
              : "Search player, club or competition…"
          }
          onFocus={() => setActive(true)}
          onChange={(e) => {
            setQuery(e.target.value);
            setActive(true);
          }}
        />
        <button type="submit">
          {nl ? "Spelers zoeken" : "Search players"}
        </button>
      </div>
      {active && tokens.length > 0 && (
        <div className="global-search-results">
          {!index && (
            <p role="status">
              {failed
                ? nl
                  ? "Zoeksuggesties niet beschikbaar."
                  : "Search suggestions unavailable."
                : nl
                  ? "Zoeken…"
                  : "Searching…"}
              {failed && (
                <button
                  type="button"
                  onClick={() => {
                    setFailed(false);
                    setRetry(retry + 1);
                  }}
                >
                  {nl ? "Opnieuw proberen" : "Try again"}
                </button>
              )}
            </p>
          )}
          {players.length > 0 && (
            <>
              <h2>{nl ? "Spelers" : "Players"}</h2>
              <ul>
                {players.map(({ p }) => (
                  <li key={p.id}>
                    <a href={href("profile", p.id)}>
                      {p.name}
                      <small>
                        {p.teams.map((t) => index!.teams[t]).join(" / ")} ·{" "}
                        {index!.scopes.find((s) => s.id === p.scope)?.season}
                      </small>
                    </a>
                  </li>
                ))}
              </ul>
            </>
          )}
          {teams.length > 0 && (
            <>
              <h2>{nl ? "Clubs" : "Teams"}</h2>
              <ul>
                {teams.map(([id, name]) => (
                  <li key={id}>
                    <a href={href("team", id)}>{name}</a>
                  </li>
                ))}
              </ul>
            </>
          )}
          {competitions.length > 0 && (
            <>
              <h2>{nl ? "Competities" : "Competitions"}</h2>
              <ul>
                {competitions.map(([id, name]) => (
                  <li key={id}>
                    <a href={href("competition", id)}>{name}</a>
                  </li>
                ))}
              </ul>
            </>
          )}
          <a className="search-all" href={href("q", query)}>
            {nl ? "Alle resultaten bekijken" : "View all results"} →
          </a>
        </div>
      )}
    </form>
  );
}
