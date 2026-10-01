import { ProductNavigation } from "./product-navigation";
import { Players } from "./players";
import { ProfileCoverage, ProfileMethodology } from "./profile-coverage";
import { playersCopy } from "@/lib/players-copy";
import release from "@/lib/release-version.json";
import Link from "next/link";
import Image from "next/image";
import { brandName } from "@/lib/brand";
import { copy, route, type Locale, type Section } from "@/lib/content";
import { coverage, matches, sources, metrics, quality } from "@/lib/data";
import { PlayerDNA, Evaluation } from "./player-dna";
import { dnaCopy } from "@/lib/dna-copy";
import { dnaIndex, dnaRegistry, dnaEvaluation } from "@/lib/data";
import { Translation, TranslationEvaluation } from "./translation";
import { translationCopy } from "@/lib/translation-copy";
import { translationIndex, translationEvaluation } from "@/lib/data";
import { Recruitment } from "./recruitment";
import { RecruitmentEvaluation } from "./recruitment-evaluation";
import { recruitmentCopy } from "@/lib/recruitment-copy";
import { recruitmentEvaluation } from "@/lib/data";
import { Explorer } from "./explorer";
const repo =
  "https://github.com/frenk4business/football-recruitment-intelligence";
export function Site({
  locale,
  section,
}: {
  locale: Locale;
  section: Section;
}) {
  const c = copy[locale],
    cov = coverage(),
    games = matches(),
    providers = sources();
  return (
    <>
      <a className="skip-link" href="#main">
        {c.skip}
      </a>
      <header className="site-header">
        <div className="header-inner">
          <Link
            prefetch={false}
            className="wordmark"
            href={route(locale, "home")}
          >
            <picture>
              <source
                media="(max-width: 480px)"
                srcSet="/brand/fri-emblem.webp"
                width={44}
                height={44}
              />
              <Image
                src="/brand/fri-horizontal.webp"
                width={196}
                height={63}
                alt={brandName}
                loading="eager"
              />
            </picture>
          </Link>
          <ProductNavigation locale={locale} section={section} />
          <a
            className="language"
            href={route(locale === "en" ? "nl" : "en", section)}
            lang={locale === "en" ? "nl" : "en"}
            aria-label={c.language}
          >
            {locale === "en" ? "NL" : "EN"}
          </a>
        </div>
      </header>
      <main id="main" tabIndex={-1}>
        <noscript>
          <p className="notice">
            {locale === "en"
              ? "Interactive exploration requires JavaScript. Methodology, coverage and research conclusions remain available below and in the repository."
              : "Interactieve verkenning vereist JavaScript. Methodologie, dekking en onderzoeksconclusies blijven hieronder en in de repository beschikbaar."}
          </p>
        </noscript>
        {section === "home" ? (
          <>
            <section className="hero">
              <div>
                <p className="eyebrow">
                  <span className="status-dot" />
                  {c.phase}
                </p>
                <h1>{c.title}</h1>
                <p className="lead">{c.intro}</p>
                <div className="hero-links">
                  <Link
                    prefetch={false}
                    className="primary-link"
                    href={route(locale, "players")}
                  >
                    {c.open}
                    <span aria-hidden="true">↗</span>
                  </Link>
                  <Link
                    prefetch={false}
                    className="text-link"
                    href={route(locale, "methodology")}
                  >
                    {c.methods}
                  </Link>
                </div>
              </div>
              <aside className="hero-aside">
                <span className="large-number">
                  05<span>/05</span>
                </span>
                <p>{c.noModels}</p>
                <div className="mini-field" aria-hidden="true">
                  <span />
                </div>
                <p className="small">{c.limitations}</p>
              </aside>
            </section>
            <section className="sample-section">
              <div className="section-heading">
                <p className="eyebrow">
                  {locale === "en" ? "SOURCE REGISTER" : "BRONNENREGISTER"}
                </p>
                <h2>{c.sample}</h2>
                <p>{c.sampleIntro}</p>
              </div>
              <div className="table-wrap">
                <table className="source-table">
                  <caption className="sr-only">{c.sample}</caption>
                  <thead>
                    <tr>
                      <th>{c.source}</th>
                      <th>{c.match}</th>
                      <th>{c.competition}</th>
                      <th>{c.records}</th>
                      <th>
                        <span className="sr-only">{c.open}</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {providers.map((s) => {
                      const m = games.find((g) => g.provider === s.id)!,
                        v = cov.providers.find((v) => v.provider === s.id)!;
                      return (
                        <tr key={s.id}>
                          <th scope="row">
                            {s.name}
                            <small>
                              {s.id === "statsbomb"
                                ? "JSON / Events"
                                : "JSONL / Tracking"}
                            </small>
                          </th>
                          <td>
                            {m.home}
                            <br />
                            {m.away}
                          </td>
                          <td>
                            {m.competition}
                            <small>{m.season}</small>
                          </td>
                          <td>
                            <strong>
                              {(
                                v.events ??
                                v.tracking_frames ??
                                0
                              ).toLocaleString(locale)}
                            </strong>
                            <small>
                              {v.events !== null ? c.eventRecords : c.frames}
                            </small>
                          </td>
                          <td>
                            <Link
                              prefetch={false}
                              href={route(locale, "explorer")}
                              aria-label={`${c.open}: ${s.name}`}
                            >
                              ↗
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
            <section className="pipeline-section">
              <h2>{c.pipelineTitle}</h2>
              <ol>
                {c.pipeline.map((p, i) => (
                  <li key={p}>
                    <span>0{i + 1}</span>
                    {p}
                  </li>
                ))}
              </ol>
            </section>
          </>
        ) : (
          <div className="page-heading">
            <h1>
              {section === "research"
                ? locale === "en"
                  ? "Research & methods"
                  : "Onderzoek & methoden"
                : section === "players"
                  ? playersCopy[locale].title
                  : section === "recruitment"
                    ? recruitmentCopy[locale].title
                    : section === "translation"
                      ? translationCopy[locale].title
                      : section === "player-dna"
                        ? dnaCopy[locale].title
                        : section === "explorer"
                          ? c.explorerTitle
                          : section === "coverage"
                            ? c.coverageTitle
                            : section === "methodology"
                              ? c.methodologyTitle
                              : c.roadmapTitle}
            </h1>
            <p className="lead">
              {section === "research"
                ? locale === "en"
                  ? "The evidence behind the profiles. Explore the methods, data and measured limits."
                  : "De onderbouwing van de profielen. Bekijk de methoden, data en vastgestelde grenzen."
                : section === "players"
                  ? playersCopy[locale].intro
                  : section === "recruitment"
                    ? recruitmentCopy[locale].intro
                    : section === "translation"
                      ? translationCopy[locale].intro
                      : section === "player-dna"
                        ? dnaCopy[locale].intro
                        : section === "explorer"
                          ? c.explorerIntro
                          : section === "coverage"
                            ? c.coverageIntro
                            : section === "methodology"
                              ? c.methodologyIntro
                              : c.roadmapIntro}
            </p>
          </div>
        )}
        {section === "players" && <Players locale={locale} />}
        {(section === "home" || section === "coverage") && (
          <ProfileCoverage locale={locale} compact={section === "home"} />
        )}
        {section === "methodology" && <ProfileMethodology locale={locale} />}
        {section === "recruitment" && <Recruitment locale={locale} />}
        {section === "translation" && (
          <Translation locale={locale} index={translationIndex()} />
        )}
        {section === "player-dna" && (
          <PlayerDNA
            locale={locale}
            index={dnaIndex()}
            registry={dnaRegistry()}
            evaluation={dnaEvaluation()}
          />
        )}
        {(section === "coverage" || section === "home") && (
          <section className="provenance">
            <h2>
              {locale === "en"
                ? "Player DNA cohort"
                : "Cohort voor spelers-DNA"}
            </h2>
            <p>
              {dnaIndex().competition} · {dnaIndex().season} ·{" "}
              {dnaIndex().matches} {locale === "en" ? "matches" : "wedstrijden"}{" "}
              · {dnaIndex().players.length}{" "}
              {locale === "en" ? "roster profiles" : "selectieprofielen"}
            </p>
            <p>
              {
                dnaIndex().players.filter(
                  (p) =>
                    p.eligibility[String(dnaIndex().default_threshold)]
                      .length === 0,
                ).length
              }{" "}
              {locale === "en"
                ? "eligible profiles at"
                : "profielen met voldoende data bij"}{" "}
              {dnaIndex().default_threshold}{" "}
              {locale === "en" ? "reliable minutes." : "betrouwbare minuten."}{" "}
              <Link prefetch={false} href={route(locale, "player-dna")}>
                {dnaCopy[locale].title} ↗
              </Link>
            </p>
          </section>
        )}
        {section === "explorer" && (
          <Explorer matches={games} sources={providers} locale={locale} />
        )}
        {section === "coverage" && (
          <>
            <div className="table-wrap">
              <table>
                <caption className="sr-only">{c.nav.coverage}</caption>
                <thead>
                  <tr>
                    <th>{c.source}</th>
                    <th>{c.competition}</th>
                    <th>{c.date}</th>
                    <th className="num">{c.players}</th>
                    <th className="num">{c.events}</th>
                    <th className="num">{c.frames}</th>
                    <th className="num">{c.objects}</th>
                  </tr>
                </thead>
                <tbody>
                  {cov.providers.map((p) => {
                    const m = games.find((m) => m.provider === p.provider)!;
                    return (
                      <tr key={p.provider}>
                        <th scope="row">
                          {providers.find((s) => s.id === p.provider)?.name}
                        </th>
                        <td>
                          {m.competition}
                          <small>{m.season}</small>
                        </td>
                        <td>{p.date_start}</td>
                        <td className="num">{p.players}</td>
                        <td className="num">
                          {p.events?.toLocaleString(locale) ?? c.unavailable}
                        </td>
                        <td className="num">
                          {p.tracking_frames ?? c.unavailable}
                        </td>
                        <td className="num">
                          {p.tracking_objects?.toLocaleString(locale) ??
                            c.unavailable}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="coverage-details">
              <section>
                <h2>{c.quality}</h2>
                <p>{c.qualityIntro}</p>
                <dl className="event-list">
                  <div>
                    <dt>{c.missingPlayers}</dt>
                    <dd>
                      {
                        cov.providers.find((p) => p.provider === "statsbomb")
                          ?.missing_player_events
                      }
                    </dd>
                  </div>
                  <div>
                    <dt>{c.missingMinutes}</dt>
                    <dd>{quality().null_counts.lineups.minutes}</dd>
                  </div>
                  <div>
                    <dt>{c.inversions}</dt>
                    <dd>
                      {cov.warnings
                        .find((w) => w.includes("timestamp inversions"))
                        ?.match(/\d+/)?.[0] ?? "0"}
                    </dd>
                  </div>
                  <div>
                    <dt>{c.extrapolatedCount}</dt>
                    <dd>
                      {
                        cov.providers.find((p) => p.provider === "skillcorner")
                          ?.undetected_objects
                      }
                    </dd>
                  </div>
                </dl>
                <p className="note">{c.minutesNote}</p>
              </section>
              <section>
                <h2>{c.available}</h2>
                <dl className="metric-list">
                  {metrics().map((m) => (
                    <div key={m.id}>
                      <dt>{locale === "nl" ? m.label_nl : m.label_en}</dt>
                      <dd>
                        {locale === "nl" ? m.description_nl : m.description_en}
                      </dd>
                    </div>
                  ))}
                </dl>
              </section>
            </div>
            <section className="provenance">
              <h2>{c.provenance}</h2>
              {providers.map((s) => (
                <p key={s.id}>
                  <a href={s.url}>{s.name}</a> ·{" "}
                  <a href={s.license_url}>{s.license}</a>
                  <br />
                  {locale === "nl" ? s.limitation_nl : s.limitation_en}
                </p>
              ))}
              <p className="note">
                {c.generated}: {cov.generated_at.slice(0, 10)} · Schema{" "}
                {cov.schema_version}
              </p>
            </section>
          </>
        )}
        {section === "methodology" && (
          <>
            <RecruitmentEvaluation
              locale={locale}
              evaluation={recruitmentEvaluation()}
            />
            <TranslationEvaluation
              locale={locale}
              index={translationIndex()}
              evaluation={translationEvaluation()}
            />
            <section id="player-dna" className="method-list dna-methods">
              <h2>{dnaCopy[locale].methodsTitle}</h2>
              {dnaCopy[locale].methods.map(([title, body], i) => (
                <section key={title}>
                  <span className="section-number">{i + 1}</span>
                  <div>
                    <h3>{title}</h3>
                    <p>{body}</p>
                  </div>
                </section>
              ))}
            </section>
            <section className="dna-definitions">
              <h2>{dnaCopy[locale].definitions}</h2>
              <dl className="metric-list">
                {dnaRegistry().map((f) => (
                  <div key={f.id}>
                    <dt>
                      {locale === "nl" ? f.label_nl : f.label_en} · {f.unit}
                    </dt>
                    <dd>{locale === "nl" ? f.note_nl : f.note_en}</dd>
                  </div>
                ))}
              </dl>
            </section>
            <Evaluation locale={locale} evaluation={dnaEvaluation()} />
            <div className="method-list">
              {c.methodSections.map(([n, title, body]) => (
                <section key={n}>
                  <span className="section-number">{n}</span>
                  <div>
                    <h2>{title}</h2>
                    <p>{body}</p>
                  </div>
                </section>
              ))}
            </div>
          </>
        )}
        {section === "roadmap" && (
          <ol className="roadmap-list">
            {c.phases.map(([title, body], i) => (
              <li key={title}>
                <span className="section-number">0{i + 1}</span>
                <div>
                  <span className="current-phase">
                    {locale === "en" ? "Complete" : "Voltooid"}
                  </span>
                  <h2>{title}</h2>
                  <p>{body}</p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </main>
      <footer>
        <div className="footer-top">
          <p>
            <strong>{brandName}</strong>
            <br />
            <span>
              {locale === "en"
                ? "Independent research by Frenk Kester"
                : "Onafhankelijk onderzoek door Frenk Kester"}
            </span>
          </p>
          <div>
            <a href={repo}>GitHub</a> ·{" "}
            <Link prefetch={false} href={route(locale, "methodology")}>
              {c.nav.methodology}
            </Link>{" "}
            ·{" "}
            <Link prefetch={false} href={route(locale, "coverage")}>
              {locale === "en" ? "Data sources" : "Databronnen"}
            </Link>
            <p className="small">
              <a href="/release-manifest.json">v{release.version}</a>
            </p>
          </div>
        </div>
        <div className="attribution">
          <Image
            src="/brand/statsbomb.png"
            width={140}
            height={35}
            alt="StatsBomb"
          />
          <p>
            {locale === "en"
              ? "Analysis uses StatsBomb Open Data. Tracking: SkillCorner / PySport."
              : "Analyse op basis van StatsBomb Open Data. Tracking: SkillCorner / PySport."}
            <br />
            <a href="https://github.com/hudl/open-data/blob/master/LICENSE.pdf">
              StatsBomb {locale === "en" ? "terms" : "voorwaarden"}
            </a>{" "}
            · <a href="/skillcorner-license.txt">SkillCorner MIT</a> ·{" "}
            <a href="https://doi.org/10.1038/s41597-019-0247-7">
              Pappalardo / Wyscout
            </a>{" "}
            ·{" "}
            <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>
          </p>
        </div>
      </footer>
    </>
  );
}
