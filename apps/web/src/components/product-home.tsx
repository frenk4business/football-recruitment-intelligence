import Link from "next/link";
import { route, type Locale, type Section } from "@/lib/content";
import expansion from "../../../../artifacts/v12/public/build-manifest.json";
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
        <div className="home-actions">
          <Link
            className="primary-action"
            prefetch={false}
            href={route(locale, "players")}
          >
            {nl ? "Spelers zoeken" : "Search players"}
          </Link>
          <Link
            prefetch={false}
            className="text-link"
            href={route(locale, "recruitment")}
          >
            {nl ? "Shortlist samenstellen" : "Build a shortlist"} →
          </Link>
        </div>
      </section>
      <div className="coverage-strip">
        <span>
          <strong>{expansion.counts.profiles.toLocaleString(locale)}</strong>{" "}
          {nl ? "speler-seizoensprofielen" : "player-season profiles"}
        </span>
        <span>
          <strong>{expansion.counts.competition_seasons}</strong>{" "}
          {nl ? "provider-competitieseizoenen" : "provider competition-seasons"}
        </span>
        <span>
          StatsBomb · Pappalardo/Wyscout · {expansion.counts.recruitment_clubs}{" "}
          {nl ? "clubseizoenen met recruitment" : "recruitment club-seasons"}
        </span>
      </div>
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
    <>
      <section
        className="research-conclusions"
        aria-label={nl ? "Onderzoeksconclusies" : "Research conclusions"}
      >
        <article>
          <h2>{nl ? "Spelersgelijkenis" : "Player similarity"}</h2>
          <p>
            {nl
              ? "Profielen tonen meetbare consistentie binnen het seizoen. Dit is geen onafhankelijke validatie van scouting of transfers."
              : "Observed profiles show measurable within-season consistency. This is not independent validation of scouting or transfers."}
          </p>
          <Link
            prefetch={false}
            href={route(locale, "methodology") + "#player-dna"}
          >
            {nl ? "Volledige evaluatie" : "Full evaluation"} →
          </Link>
        </article>
        <article>
          <h2>{nl ? "Historische vertaling" : "Historical translation"}</h2>
          <p>
            {nl
              ? "De beschikbare data onderbouwen geen brede vertaling tussen competities. Historische WSL-intervallen onderschatten onzekerheid voor sommige kenmerken."
              : "Available evidence does not support broad cross-league translation. Historical WSL intervals underestimate uncertainty for some features."}
          </p>
          <Link
            prefetch={false}
            href={route(locale, "methodology") + "#translation"}
          >
            {nl ? "Volledige evaluatie" : "Full evaluation"} →
          </Link>
        </article>
        <article>
          <h2>{nl ? "Recruitmentprofielen" : "Recruitment fit"}</h2>
          <p>
            {nl
              ? "De rangschikking toont signaal boven toeval, maar presteert niet consistent beter dan Spelers-DNA. Profielovereenkomst voorspelt geen transfersucces."
              : "Rankings show signal above chance but do not consistently outperform Player DNA. Profile fit does not predict transfer success."}
          </p>
          <Link
            prefetch={false}
            href={route(locale, "methodology") + "#recruitment"}
          >
            {nl ? "Volledige evaluatie" : "Full evaluation"} →
          </Link>
        </article>
      </section>
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
    </>
  );
}
