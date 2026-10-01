"use client";
import { useEffect, useState } from "react";
import { fetchArtifact } from "@/lib/artifact";
import type { DNAProfile, FeatureDefinition } from "@/lib/contracts";
import type { Locale } from "@/lib/content";
export function ProfileStyle({ id, locale }: { id: string; locale: Locale }) {
  const [loaded, setLoaded] = useState<{
    id: string;
    profile: DNAProfile;
    definitions: FeatureDefinition[];
  }>();
  const [failed, setFailed] = useState(false),
    [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setFailed(false);
    Promise.all([
      fetchArtifact<DNAProfile>(
        `/data/phase2/900/${id}.json`,
        controller.signal,
      ),
      fetchArtifact<FeatureDefinition[]>(
        "/data/phase2/features.json",
        controller.signal,
      ),
    ])
      .then(([profile, definitions]) => setLoaded({ id, profile, definitions }))
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [id, attempt]);
  if (failed)
    return (
      <p role="alert">
        {locale === "en"
          ? "Playing style could not be loaded."
          : "De speelstijl kon niet worden geladen."}{" "}
        <button onClick={() => setAttempt(attempt + 1)}>
          {locale === "en" ? "Try again" : "Opnieuw proberen"}
        </button>
      </p>
    );
  if (loaded?.id !== id)
    return (
      <p className="detail-skeleton" role="status">
        {locale === "en" ? "Loading playing style…" : "Speelstijl laden…"}
      </p>
    );
  if (!loaded.profile.eligible) return null;
  const definitions = new Map(loaded.definitions.map((f) => [f.id, f]));
  const features = loaded.profile.features.filter(
    (f) => f.percentile !== null && definitions.get(f.id)?.core,
  );
  const families: Record<string, [string, string]> = {
    creation: ["Chance creation", "Kansen creëren"],
    shooting: ["Shooting", "Schieten"],
    passing: ["Passing", "Passing"],
    carrying: ["Ball carrying", "Dribbelen"],
    defending: ["Defensive activity", "Verdedigende acties"],
    possession: ["Possession", "Balbezit"],
    pressing: ["Pressing", "Druk zetten"],
  };
  // Presentation selection only: two observed core metrics per family, up to ten.
  const seen = new Map<string, number>();
  const featured = features
    .filter((f) => {
      const family = definitions.get(f.id)!.family;
      const n = seen.get(family) ?? 0;
      seen.set(family, n + 1);
      return n < 2;
    })
    .slice(0, 10);
  const bars = (items: typeof features) => (
    <div className="profile-style-bars">
      {items.map((f) => (
        <div key={f.id}>
          <span
            title={
              locale === "en"
                ? definitions.get(f.id)?.note_en
                : definitions.get(f.id)?.note_nl
            }
          >
            {locale === "en"
              ? definitions.get(f.id)?.label_en
              : definitions.get(f.id)?.label_nl}
          </span>
          <span className="style-track" aria-hidden="true">
            <span style={{ width: `${f.percentile}%` }} />
          </span>
          <strong>{Math.round(f.percentile!)}</strong>
        </div>
      ))}
    </div>
  );
  return (
    <div className="integrated-style">
      <p className="small">
        {locale === "en"
          ? "Role-relative percentiles · WSL 2023/24"
          : "Percentielen binnen de rol · WSL 2023/24"}
      </p>
      <div className="style-families">
        {[...new Set(featured.map((f) => definitions.get(f.id)!.family))].map(
          (family) => (
            <section key={family}>
              <h4>{families[family]?.[locale === "en" ? 0 : 1] ?? family}</h4>
              {bars(
                featured.filter(
                  (f) => definitions.get(f.id)!.family === family,
                ),
              )}
            </section>
          ),
        )}
      </div>
      <details>
        <summary>
          {locale === "en"
            ? "Show all metrics & observed rates"
            : "Alle kenmerken & geobserveerde waarden"}
        </summary>
        {bars(features.filter((f) => !featured.includes(f)))}
        <dl>
          {features.map((f) => (
            <div key={f.id}>
              <dt>
                {locale === "en"
                  ? definitions.get(f.id)?.label_en
                  : definitions.get(f.id)?.label_nl}
              </dt>
              <dd>
                {f.value?.toLocaleString(locale, { maximumFractionDigits: 2 })}{" "}
                {definitions.get(f.id)?.unit}
              </dd>
            </div>
          ))}
        </dl>
        <p>
          {loaded.profile.threshold} min · {loaded.profile.comparison_size}{" "}
          {locale === "en" ? "comparison profiles" : "vergelijkingsprofielen"} ·{" "}
          {loaded.profile.version}
        </p>
      </details>
    </div>
  );
}
