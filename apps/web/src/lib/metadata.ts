import type { Metadata } from "next";
import { copy, route, type Locale, type Section } from "./content";
export const origin = "https://football-recruitment-intelligence.onrender.com";
export function pageMetadata(locale: Locale, section: Section): Metadata {
  const description =
    locale === "en"
      ? "Independent, non-commercial football research: observed Player DNA, historical translation limits and explicit recruitment requirements. No transfer predictions."
      : "Onafhankelijk, niet-commercieel voetbalonderzoek: geobserveerd Player DNA, grenzen van historische vertaling en expliciete wervingseisen. Geen transfervoorspellingen.";
  return {
    title:
      section === "home"
        ? "Football Recruitment Intelligence"
        : copy[locale].nav[section],
    description,
    alternates: {
      canonical: origin + route(locale, section),
      languages: {
        en: origin + route("en", section),
        nl: origin + route("nl", section),
        "x-default": origin + route("en", section),
      },
    },
    openGraph: {
      type: "website",
      title: copy[locale].nav[section] + " · Football Recruitment Intelligence",
      description,
      url: origin + route(locale, section),
      locale: locale === "en" ? "en_GB" : "nl_NL",
      siteName: "Football Recruitment Intelligence",
    },
    robots: { index: true, follow: true },
  };
}
