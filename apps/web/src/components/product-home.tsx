import Link from "next/link";
import { route, type Locale, type Section } from "@/lib/content";
import { profileCoverage } from "@/lib/data";
export function ProductHome({ locale }: { locale: Locale }) {
  const nl = locale === "nl";
  return (
    <>
      <section className="product-hero">
        <h1>Football Recruitment Intelligence</h1>
        <p className="lead">
          {nl
            ? "Ontdek spelersprofielen, vergelijk speelstijlen en stel een onderbouwde shortlist samen met open voetbaldata."
            : "Explore player profiles, compare playing styles and build transparent recruitment shortlists from open football data."}
        </p>
        <form
          className="home-search"
          action={route(locale, "players")}
          method="get"
        >
          <label htmlFor="home-query">
            {nl ? "Wie zoek je?" : "Who are you looking for?"}
          </label>
          <div>
            <input
              id="home-query"
              name="q"
              type="search"
              maxLength={100}
              placeholder={
                nl
                  ? "Zoek op speler, club of competitie"
                  : "Search player, club or competition"
              }
            />
            <button className="primary-action">
              {nl ? "Spelers zoeken" : "Search players"}
            </button>
          </div>
        </form>
        <p className="home-coverage">
          {profileCoverage().counts.profiles.toLocaleString(locale)}{" "}
          {nl
            ? "geobserveerde speler-seizoensprofielen"
            : "observed player-season profiles"}{" "}
          · StatsBomb + Pappalardo/Wyscout
        </p>
        <Link
          prefetch={false}
          className="text-link"
          href={route(locale, "recruitment")}
        >
          {nl ? "Shortlist samenstellen" : "Build a shortlist"} →
        </Link>
      </section>
      <div className="task-links">
        {(nl
          ? [
              [
                "players",
                "Spelers ontdekken",
                "Zoek in duizenden spelersprofielen uit verschillende competities en databronnen.",
              ],
              [
                "recruitment",
                "Kandidaten vinden",
                "Stel een shortlist samen op basis van positie en je eigen eisen.",
              ],
              [
                "research",
                "Onderzoek & methoden",
                "Bekijk de methodologie, evaluaties, databronnen en beperkingen.",
              ],
            ]
          : [
              [
                "players",
                "Explore players",
                "Search thousands of observed player profiles across competitions and providers.",
              ],
              [
                "recruitment",
                "Find candidates",
                "Build a role-specific shortlist using explicit recruitment requirements.",
              ],
              [
                "research",
                "Research & methods",
                "Inspect methodology, evaluation, data provenance and limitations.",
              ],
            ]
        ).map(([section, title, body]) => (
          <section key={section}>
            <h2>
              <Link prefetch={false} href={route(locale, section as Section)}>
                {title} <span aria-hidden="true">→</span>
              </Link>
            </h2>
            <p>{body}</p>
          </section>
        ))}
      </div>
      <p className="trust-line">
        {nl
          ? "Open data · Reproduceerbaar onderzoek · Duidelijke beperkingen"
          : "Open data · Reproducible research · Explicit limitations"}
      </p>
    </>
  );
}
export function ResearchHub({ locale }: { locale: Locale }) {
  const nl = locale === "nl";
  const entries: [Section, string, string, string?][] = nl
    ? [
        [
          "methodology",
          "Methodologie",
          "Definities, aannames en reproduceerbare werkwijzen.",
        ],
        [
          "coverage",
          "Datadekking",
          "Welke spelers, seizoenen en bronnen beschikbaar zijn.",
        ],
        [
          "translation",
          "Historische vertaling",
          "Geobserveerde prestaties en verwachte bandbreedtes binnen historisch WSL-onderzoek.",
        ],
        [
          "explorer",
          "Data verkennen",
          "Bekijk wedstrijdgebeurtenissen en trackingdata.",
        ],
        [
          "methodology",
          "Evaluaties",
          "Gemeten resultaten, vergelijkingen en grenzen van de modellen.",
          "evaluation",
        ],
        [
          "player-dna",
          "Spelers-DNA onderzoeken",
          "De volledige WSL-weergave met percentielen, onzekerheid en representatie.",
        ],
      ]
    : [
        [
          "methodology",
          "Methodology",
          "Definitions, assumptions and reproducible methods.",
        ],
        [
          "coverage",
          "Data coverage",
          "Available players, seasons and sources.",
        ],
        [
          "translation",
          "Historical translation",
          "Observed performance and expected ranges in historical WSL research.",
        ],
        [
          "explorer",
          "Data explorer",
          "Inspect match events and tracking sequences.",
        ],
        [
          "methodology",
          "Evaluation",
          "Measured results, comparisons and model limitations.",
          "evaluation",
        ],
        [
          "player-dna",
          "Explore Player DNA",
          "The full WSL view with percentiles, uncertainty and representation.",
        ],
      ];
  return (
    <div className="research-links">
      {entries.map(([section, title, body, anchor]) => (
        <section key={title}>
          <h2>
            <Link
              prefetch={false}
              href={route(locale, section) + (anchor ? "#" + anchor : "")}
            >
              {title} →
            </Link>
          </h2>
          <p>{body}</p>
        </section>
      ))}
    </div>
  );
}
