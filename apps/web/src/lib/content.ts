import release from "./release-version.json" with { type: "json" };
export type Locale = "en" | "nl";
export type Section =
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
const en = {
  nav: {
    home: "Overview",
    players: "Players",
    "player-dna": "Player DNA",
    translation: "Translation",
    recruitment: "Recruitment",
    explorer: "Data explorer",
    coverage: "Coverage",
    methodology: "Methodology",
    roadmap: "Roadmap",
  },
  skip: "Skip to content",
  language: "Taal wijzigen naar Nederlands",
  phase: `RELEASE v${release.version} / OPEN RESEARCH`,
  title: "Recruitment research starts with the evidence.",
  intro:
    "Explore what open football data can tell us — and where it stops. A research platform for player profiles, competition context and, eventually, recruitment decisions.",
  open: "Explore the player database",
  methods: "Read the methodology",
  sample: "The working sample",
  sampleIntro:
    "Two providers. Different matches, formats and assumptions. Every number below comes from the ingestion pipeline.",
  noModels:
    "Compare observed profiles against explicit requirements, with club context, visible trade-offs and separate evidence.",
  source: "Source",
  match: "Match",
  competition: "Competition / season",
  records: "Ingested records",
  eventRecords: "event records",
  frames: "tracking frames",
  players: "roster players",
  explorerTitle: "Two views of the game.",
  explorerIntro:
    "Inspect an event match or a short tracking sequence. Source context stays attached to the evidence.",
  team: "Team",
  allTeams: "All teams",
  search: "Find a player",
  searchPlaceholder: "Player name…",
  player: "Player",
  position: "Position",
  minutes: "Minutes",
  shots: "Shots",
  passes: "Passes",
  xg: "Provider xG",
  unavailable: "Not available",
  noRows: "No players match these filters.",
  loading: "Loading the selected sample…",
  error:
    "This sample could not be loaded. Reload the page if retrying does not help.",
  retry: "Try again",
  spatial: "Where actions were recorded",
  tracking: "A minute in position",
  spatialNote:
    "All located actions, grouped into 12 × 8 pitch cells. Both teams attack left to right. This is match-level analysis; player filters apply to the table.",
  trackingNote:
    "Fixed pitch orientation. A circle is a detected player; a square is extrapolated. The ball is labelled B. Reference dimensions: 105 × 68 m.",
  sampled: "located actions",
  count: "Count",
  frame: "Sample time",
  detected: "Detected",
  extrapolated: "Extrapolated",
  fullMatch: "Full match + extra time",
  trackingSample: "60-second sample · 1 Hz",
  shootout:
    "The score is after extra time. Shootout events are ingested but excluded from player totals and spatial analysis.",
  minutesNote:
    "Minutes include stoppage time where intervals are consistent. Missing or conflicting source intervals stay unavailable. SkillCorner minutes describe the full match, not the sampled minute.",
  xgNote:
    "xG is a model estimate supplied by StatsBomb, not a model built in this project.",
  previous: "Previous",
  next: "Next",
  page: "Page",
  of: "of",
  showing: "players shown",
  coverageTitle: "Know the limits of the sample.",
  coverageIntro:
    "Counts describe the data actually ingested here, not the provider’s entire catalogue. Roster counts include unused substitutes.",
  date: "Match date",
  events: "Events",
  objects: "Tracked objects",
  quality: "Data quality",
  qualityIntro:
    "The pipeline validates schemas, references, time and coordinates. Source anomalies remain visible.",
  missingPlayers: "Events without a player ID",
  missingMinutes: "Lineups with unavailable minutes",
  inversions: "Timestamp inversions in provider order",
  extrapolatedCount: "Extrapolated object positions",
  available: "Available measures",
  provenance: "Source and licence",
  generated: "Artifact generated",
  methodologyTitle: "Comparable structure. Different evidence.",
  methodologyIntro:
    "A shared schema makes data queryable. It does not make providers, competitions or players interchangeable.",
  methodSections: [
    [
      "01",
      "Keep identities honest",
      "Provider identifiers become stable, namespaced IDs. Players are not joined by similar names. A mapping table records the basis for each identity; no cross-provider identity matches are claimed.",
    ],
    [
      "02",
      "Make coordinates explicit",
      "Both sources map to a 105 × 68 m reference pitch, with the origin at the bottom left. StatsBomb events are relative to the acting team. SkillCorner positions retain fixed pitch orientation and the original pitch dimensions. These are transformed coordinates, not new measurements.",
    ],
    [
      "03",
      "Treat missing as missing",
      "Absent tracking, unavailable xG and unreliable minutes are shown as unavailable. A recorded zero is different. Per-90 values require at least 30 reliable minutes and remain descriptive in this small sample.",
    ],
    [
      "04",
      "Preserve the audit trail",
      "Every input is pinned to a source revision, checksummed and timestamped. Typed records pass validation before Parquet is written. DuckDB produces the analytical tables; validated JSON supplies both the website and the local API.",
    ],
    [
      "05",
      "Respect the publication boundary",
      "StatsBomb raw events stay local. This release publishes research aggregates and binned spatial analysis with the required attribution. SkillCorner samples retain their MIT notice. No transfer values, recommendations or invented scores are included.",
    ],
    [
      "06",
      "Prepare for temporal evaluation",
      "Match dates, observation dates and extraction times remain distinct. Later work must evaluate on genuinely later periods. A World Cup final and one minute of A-League tracking cannot establish recruitment accuracy or league strength.",
    ],
  ],
  roadmapTitle: "One foundation. Five research phases.",
  roadmapIntro:
    "Five completed phases, with scientific limits preserved. A stable research release with explicit data and model limitations.",
  phases: [
    [
      "Data foundation",
      "Source audit, canonical data model, reproducible ingestion, validation and an honest explorer.",
    ],
    [
      "Player DNA & similarity",
      "Position-aware features and transparent similarity baselines, evaluated for sample sensitivity.",
    ],
    [
      "League translation",
      "Competition and team context, hierarchical models and temporal evaluation.",
    ],
    [
      "Recruitment intelligence",
      "Explainable candidate comparison, tactical context and explicit uncertainty.",
    ],
    [
      "Production hardening",
      "Versioned release, artifact integrity, accessibility, browser validation and operational documentation.",
    ],
  ],
  current: "Current phase",
  planned: "Planned",
  footer: "Independent non-commercial research by Frenk Kester.",
  repo: "Source code",
  limitations: "Observed profiles. No recruitment recommendations.",
  pipelineTitle: "From source file to inspectable evidence",
  pipeline: [
    "Pinned sources",
    "Typed contracts",
    "Parquet + DuckDB",
    "Research explorer",
  ],
};
export type Copy = typeof en;
const nl: Copy = {
  nav: {
    home: "Overzicht",
    players: "Spelers",
    "player-dna": "Spelers-DNA",
    translation: "Prestatievertaling",
    recruitment: "Recruitment",
    explorer: "Dataverkenner",
    coverage: "Datadekking",
    methodology: "Methodologie",
    roadmap: "Routekaart",
  },
  skip: "Ga naar inhoud",
  language: "Switch language to English",
  phase: `RELEASE v${release.version} / OPEN ONDERZOEK`,
  title: "Recruitmentonderzoek begint bij de onderbouwing.",
  intro:
    "Onderzoek wat open voetbaldata ons vertelt — en waar de grenzen liggen. Een onderzoeksplatform voor spelersprofielen, competitiecontext en uiteindelijk recruitmentbeslissingen.",
  open: "Verken de spelersdatabase",
  methods: "Lees de methodologie",
  sample: "De gebruikte steekproef",
  sampleIntro:
    "Twee databronnen. Andere wedstrijden, formaten en aannames. Alle aantallen hieronder komen uit de datapijplijn.",
  noModels:
    "Vergelijk waargenomen profielen met expliciete eisen, clubcontext, zichtbare afwegingen en afzonderlijke onderbouwing.",
  source: "Databron",
  match: "Wedstrijd",
  competition: "Competitie / seizoen",
  records: "Ingelezen records",
  eventRecords: "eventrecords",
  frames: "trackingframes",
  players: "spelers in selectie",
  explorerTitle: "Twee perspectieven op het spel.",
  explorerIntro:
    "Bekijk een wedstrijd met eventdata of een korte trackingreeks. De broncontext blijft altijd zichtbaar.",
  team: "Team",
  allTeams: "Alle teams",
  search: "Zoek een speler",
  searchPlaceholder: "Naam van speler…",
  player: "Speler",
  position: "Positie",
  minutes: "Minuten",
  shots: "Schoten",
  passes: "Passes",
  xg: "xG van databron",
  unavailable: "Niet beschikbaar",
  noRows: "Geen spelers gevonden met deze filters.",
  loading: "De geselecteerde steekproef wordt geladen…",
  error:
    "Deze steekproef kon niet worden geladen. Vernieuw de pagina als opnieuw proberen niet helpt.",
  retry: "Opnieuw proberen",
  spatial: "Waar acties plaatsvonden",
  tracking: "Een minuut in positie",
  spatialNote:
    "Alle acties met locatie, gegroepeerd in 12 × 8 veldvakken. Beide teams vallen van links naar rechts aan. Dit is wedstrijdanalyse; spelersfilters gelden voor de tabel.",
  trackingNote:
    "Vaste veldoriëntatie. Cirkels tonen gedetecteerde spelers; vierkanten geëxtrapoleerde posities. B is de bal. Referentieafmetingen: 105 × 68 m.",
  sampled: "acties met locatie",
  count: "Aantal",
  frame: "Tijd in steekproef",
  detected: "Gedetecteerd",
  extrapolated: "Geëxtrapoleerd",
  fullMatch: "Volledige wedstrijd + verlenging",
  trackingSample: "60 seconden · 1 Hz",
  shootout:
    "De stand is na verlenging. De strafschoppenserie is ingelezen, maar uitgesloten van spelerstotalen en ruimtelijke analyse.",
  minutesNote:
    "Minuten zijn inclusief blessuretijd als de intervallen kloppen. Ontbrekende of tegenstrijdige intervallen blijven onbekend. SkillCorner-minuten betreffen de hele wedstrijd, niet de onderzochte minuut.",
  xgNote:
    "xG is een modelschatting van StatsBomb, geen model dat voor dit project is gebouwd.",
  previous: "Vorige",
  next: "Volgende",
  page: "Pagina",
  of: "van",
  showing: "spelers getoond",
  coverageTitle: "Ken de grenzen van de steekproef.",
  coverageIntro:
    "De aantallen beschrijven wat hier daadwerkelijk is ingelezen, niet de volledige broncatalogus. Selecties tellen ook ongebruikte wisselspelers mee.",
  date: "Wedstrijddatum",
  events: "Events",
  objects: "Gevolgde objecten",
  quality: "Datakwaliteit",
  qualityIntro:
    "De pijplijn controleert schema’s, verwijzingen, tijd en coördinaten. Afwijkingen in de bron blijven zichtbaar.",
  missingPlayers: "Events zonder speler-ID",
  missingMinutes: "Selectieregels zonder betrouwbare minuten",
  inversions: "Teruglopende tijdstempels in bronvolgorde",
  extrapolatedCount: "Geëxtrapoleerde objectposities",
  available: "Beschikbare metingen",
  provenance: "Bron en licentie",
  generated: "Artifact gegenereerd",
  methodologyTitle: "Vergelijkbare structuur. Verschillende onderbouwing.",
  methodologyIntro:
    "Een gedeeld schema maakt data bevraagbaar. Dat maakt databronnen, competities of spelers nog niet onderling uitwisselbaar.",
  methodSections: [
    [
      "01",
      "Houd identiteiten betrouwbaar",
      "Bron-ID’s krijgen stabiele ID’s binnen een eigen naamruimte. Spelers worden niet op gelijkende namen samengevoegd. Een koppeltabel legt de basis van elke identiteit vast; er zijn geen spelers tussen bronnen gekoppeld.",
    ],
    [
      "02",
      "Maak coördinaten expliciet",
      "Beide bronnen worden omgerekend naar een referentieveld van 105 × 68 meter, met de oorsprong linksonder. StatsBomb-events zijn relatief aan het handelende team. SkillCorner behoudt de vaste veldoriëntatie en oorspronkelijke afmetingen. Dit zijn transformaties, geen nieuwe metingen.",
    ],
    [
      "03",
      "Laat ontbrekende waarden ontbreken",
      "Ontbrekende tracking, niet-beschikbare xG en onbetrouwbare minuten blijven zichtbaar als niet beschikbaar. Een gemeten nul is iets anders. Waarden per 90 minuten vereisen minstens 30 betrouwbare minuten en blijven beschrijvend.",
    ],
    [
      "04",
      "Bewaar de herkomst",
      "Elke invoer heeft een vaste bronversie, controlesom en ophaaltijd. Getypeerde records worden gevalideerd voordat Parquet wordt geschreven. DuckDB maakt de analysetabellen; gevalideerde JSON voedt de website en lokale API.",
    ],
    [
      "05",
      "Respecteer publicatievoorwaarden",
      "Ruwe StatsBomb-events blijven lokaal. Deze release publiceert onderzoeksaggregaten en gegroepeerde veldanalyses met bronvermelding. SkillCorner behoudt de MIT-licentie. Er zijn geen transferwaarden, aanbevelingen of verzonnen scores.",
    ],
    [
      "06",
      "Bereid temporele evaluatie voor",
      "Wedstrijddatum, observatiedatum en ophaaltijd blijven gescheiden. Latere modellen moeten op werkelijk latere perioden worden getoetst. Eén WK-finale en één minuut A-League-tracking onderbouwen geen recruitmentnauwkeurigheid of competitiesterkte.",
    ],
  ],
  roadmapTitle: "Eén fundament. Vijf onderzoeksfasen.",
  roadmapIntro:
    "Vijf afgeronde fasen met behoud van wetenschappelijke beperkingen. Een stabiele onderzoeksversie met expliciete beperkingen van data en modellen.",
  phases: [
    [
      "Datafundament",
      "Bronnenonderzoek, canoniek datamodel, reproduceerbare verwerking, validatie en een heldere dataverkenner.",
    ],
    [
      "Spelers-DNA en gelijkenis",
      "Positieafhankelijke kenmerken en uitlegbare vergelijkingsmethoden, getoetst op steekproefgevoeligheid.",
    ],
    [
      "Vertaling tussen competities",
      "Competitie- en teamcontext, hiërarchische modellen en temporele evaluatie.",
    ],
    [
      "Recruitmentondersteuning",
      "Uitlegbare spelersvergelijking, tactische context en expliciete onzekerheid.",
    ],
    [
      "Productieversteviging",
      "Een versiegebonden release, artifactintegriteit, toegankelijkheid, browsertests en operationele documentatie.",
    ],
  ],
  current: "Huidige fase",
  planned: "Gepland",
  footer: "Onafhankelijk, niet-commercieel onderzoek door Frenk Kester.",
  repo: "Broncode",
  limitations: "Waargenomen profielen. Geen recruitmentaanbevelingen.",
  pipelineTitle: "Van bronbestand naar controleerbare onderbouwing",
  pipeline: [
    "Vaste bronversies",
    "Getypeerde contracten",
    "Parquet + DuckDB",
    "Dataverkenner",
  ],
};
export const copy = { en, nl };
