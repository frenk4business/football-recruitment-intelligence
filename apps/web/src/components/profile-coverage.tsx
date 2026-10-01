import Link from "next/link";
import type { Locale } from "@/lib/content";
import { route } from "@/lib/content";
import { profileCoverage } from "@/lib/data";
import { playersCopy } from "@/lib/players-copy";
const repo =
  "https://github.com/frenk4business/football-recruitment-intelligence";
export function ProfileCoverage({
  locale,
  compact = false,
}: {
  locale: Locale;
  compact?: boolean;
}) {
  const c = playersCopy[locale],
    data = profileCoverage();
  return (
    <section className="provenance expanded-coverage">
      <h2>{c.coverageTitle}</h2>
      <div className="profile-counts">
        <p>
          <strong>{data.counts.profiles.toLocaleString(locale)}</strong>{" "}
          {c.profiles}
        </p>
        <p>
          <strong>
            {data.counts.provider_identities.toLocaleString(locale)}
          </strong>{" "}
          {c.identities}
        </p>
        <p>
          <strong>{data.counts.common_profiles.toLocaleString(locale)}</strong>{" "}
          {c.commonCount}
        </p>
      </div>
      <p>
        {data.counts.providers} {c.providers} · {data.counts.competitions}{" "}
        {c.competitions} · {data.counts.competition_seasons} {c.seasons} ·{" "}
        {data.counts.matches.toLocaleString(locale)} {c.matches}
      </p>
      <p className="small">{c.coverageNote}</p>
      <p>
        <Link prefetch={false} href={route(locale, "players")}>
          {c.title} ↗
        </Link>
      </p>
      {!compact && (
        <>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">{c.coverageTitle}</caption>
              <thead>
                <tr>
                  <th scope="col">{c.provider}</th>
                  <th scope="col">
                    {c.competition} / {c.season}
                  </th>
                  <th scope="col">{c.matches}</th>
                  <th scope="col">{c.profiles}</th>
                  <th scope="col">{c.commonCount}</th>
                  <th scope="col">{c.similarity}</th>
                </tr>
              </thead>
              <tbody>
                {data.scopes.map((s) => (
                  <tr key={s.id}>
                    <th scope="row">
                      {s.provider === "statsbomb"
                        ? "StatsBomb"
                        : "Pappalardo / Wyscout"}
                    </th>
                    <td>
                      {s.competition}
                      <small>
                        {s.season} · {c[s.gender]}
                      </small>
                      <small>
                        {s.coverage.startsWith("partial")
                          ? c.partial
                          : c.complete}
                      </small>
                      <small>
                        {s.first_date} – {s.last_date}
                      </small>
                    </td>
                    <td>{s.matches}</td>
                    <td>{s.profiles}</td>
                    <td>{s.common_profiles}</td>
                    <td>{s.similarity_profiles}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>{c.evidenceNote}</p>
          <p>{c.rolesNote}</p>
          <p>{c.rankingNote}</p>
        </>
      )}
    </section>
  );
}
export function ProfileMethodology({ locale }: { locale: Locale }) {
  const c = playersCopy[locale],
    data = profileCoverage();
  return (
    <section className="provenance profile-methodology">
      <h2>{c.methodologyTitle}</h2>
      <p>{c.methodology}</p>
      <h3>{c.harmonisationTitle}</h3>
      <p>{c.harmonisation}</p>
      <p>{c.evidenceNote}</p>
      <p>{c.disclaimer}</p>
      <h3>{c.evaluationTitle}</h3>
      <p>{c.evaluation}</p>
      <dl>
        <dt>{c.threshold}</dt>
        <dd>
          {data.common_threshold} {c.minutes.toLowerCase()}
        </dd>
        <dt>{c.auc}</dt>
        <dd>
          {data.provider_bias.auc.toLocaleString(locale, {
            maximumFractionDigits: 3,
          })}
        </dd>
        <dt>{c.balanced}</dt>
        <dd>
          {data.provider_bias.balanced_accuracy.toLocaleString(locale, {
            maximumFractionDigits: 3,
          })}
        </dd>
      </dl>
      <p>{c.rankingNote}</p>
      <p>{c.publication}</p>
      <p>
        <a href="https://doi.org/10.1038/s41597-019-0247-7">
          Pappalardo et al. (2019), A public data set of spatio-temporal match
          events in soccer
        </a>{" "}
        ·{" "}
        <a href="https://figshare.com/collections/Soccer_match_event_dataset/4415000/5">
          Figshare v5
        </a>{" "}
        · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>
      </p>
      <p>
        <a href={`${repo}/blob/main/docs/common-profile-evaluation.md`}>
          {c.research} ↗
        </a>
      </p>
    </section>
  );
}
