export type Locale = "en" | "nl";
export type Section =
  | "research"
  | "home"
  | "players"
  | "player-dna"
  | "recruitment"
  | "translation"
  | "explorer"
  | "coverage"
  | "methodology"
  | "roadmap";
export const sections: Section[] = [
  "home",
  "research",
  "players",
  "player-dna",
  "translation",
  "recruitment",
  "explorer",
  "coverage",
  "methodology",
  "roadmap",
];
export const route = (locale: Locale, section: Section) =>
  `${locale === "nl" ? "/nl" : ""}/${section === "home" ? "" : section + "/"}`;
