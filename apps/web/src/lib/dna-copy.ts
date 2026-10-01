import type { Locale } from "./content";
const en = {
  title: "Player DNA",
  intro: "Compare role-aware player profiles derived from open event data.",
  season: "Season",
  team: "Team",
  role: "Role",
  all: "All",
  threshold: "Minimum reliable minutes",
  search: "Find a player",
  select: "Select player",
  results: "matching players",
  minutes: "reliable minutes",
  matches: "matches",
  profile: "Playing profile",
  compared: "Compared with eligible players in the same role and season.",
  cohort: "players in this comparison cohort",
  version: "Profile version",
  multi: "Multiple roles",
  roleMix: "Share of reliable minutes by role",
  neighbors: "Closest observed profiles",
  distance: "Distance",
  stability: "Top-10 stability",
  compare: "Compare",
  stabilityNote:
    "Frequency in the top 10 across 100 match bootstrap samples. This is sampling stability, not a probability of similarity. Small role cohorts inflate top-10 stability.",
  distanceNote:
    "Smaller distances mean closer observed profiles. Five feature families have equal weight. Goals and xG do not drive this ranking.",
  similar: "Most similar in",
  different: "Largest differences",
  contribution: "Contribution to squared distance",
  compareTitle: "Profile comparison",
  percentile: "Role percentile",
  more: "More is not necessarily better.",
  low: "This player does not meet the current evidence threshold.",
  below_minutes: "Reliable minutes are below the selected minimum.",
  goalkeeper_excluded:
    "Goalkeeper similarity requires a dedicated feature set and is excluded from this release.",
  uncertain_role:
    "The available role minutes do not support a sufficiently clear primary role.",
  missing_core_features: "Required core features are unavailable.",
  sparse_role:
    "Fewer than 12 eligible players share this role. Similarity is unavailable.",
  unavailable: "Not available",
  loading: "Loading player evidence…",
  error:
    "The player evidence could not be loaded. Reload the page if retrying does not help.",
  retry: "Try again",
  empty: "No players match these filters.",
  methodology: "View methodology",
  map: "Player profile map",
  mapNote:
    "This 2D PCA view is a projection for exploration. Distances are simplified and are not the production similarity calculation. Cross-role proximity has no comparison meaning.",
  mapLegend:
    "A × marks the selected player. Outlined dots mark neighbours. Player and role details are available by keyboard focus or in the table.",
  mapTable: "Map as a player table",
  selectMap: "Explore the player map",
  territory: "Action territory",
  territoryNote:
    "Pass, carry and shot starts, aggregated over reliable matches into 12 × 8 cells. Attacking left to right. Darker cells contain more actions.",
  territoryTable: "Territory as a data table",
  count: "Actions",
  cell: "Pitch cell",
  evidence: "Representation stability",
  evaluationNote:
    "Temporal retrieval measures whether a first-window profile retrieves the same player in a later window. It measures consistency, not scouting quality. Candidate groups are small; see the random baseline.",
  method: "Method",
  queries: "Paired queries",
  jaccard: "Top-10 Jaccard",
  random: "Random Recall@5",
  output: "Observed output · outside the style distance",
  notQuality:
    "Similarity is not quality, tactical fit, transfer success or future performance. One season in one competition cannot establish cross-league comparability.",
  methodsTitle: "How Player DNA is calculated",
  definitions: "Feature definitions",
  methods: [
    [
      "Evidence first",
      "WSL 2023/24 is a complete 132-match cohort. Playing time is reconciled from starting XIs, substitutions, temporary exits, cards and actual period ends, including stoppage time. Conflicting player-match records are excluded together with their events. The short SkillCorner sample is not used for similarity.",
    ],
    [
      "Roles and thresholds",
      "Choose 450, 600, 900 or 1,200 reliable minutes. The default is 900. The six supported roles stay separate; at least 12 eligible players are required. Goalkeepers and sparse attacking-midfield cohorts are excluded. Role shares describe observed time; they are not permanent identities.",
    ],
    [
      "Features and distance",
      "18 style features form five equally weighted families. Each feature is centred on its role-cohort mean and divided by its population standard deviation. Constant features contribute nothing. Distance is the square root of the average within-family mean squared difference. There is no clipping or probability score. Percentiles use the same role, season and threshold; tied values share their midpoint percentile.",
    ],
    [
      "Progression and chance creation",
      "A progressive completed open-play pass or carry reduces Euclidean distance to the opponent goal centre by at least 10 reference metres and at least 25% of the starting distance. Passes exclude restarts. Penalty-area entries start outside the 16.5 × 40.32 m box and end inside. Shot assists and xA require reciprocal event links; xA uses the linked non-penalty shot’s provider xG. Set-piece assists are included. Shootouts and own goals are excluded.",
    ],
    [
      "Stability and evaluation",
      "Bootstrap samples resample each player’s whole matches with replacement, rebuild features and refit scaling. Eligibility and roles remain fixed. Inclusion rates count appearances in the top 10; Jaccard measures overlap with the original neighbour set. Temporal evaluation uses disjoint calendar windows and fits scaling on the earlier window only. The experiments also compare cosine, PCA, robust/global scaling, possession context and family ablations.",
    ],
    [
      "What the experiments did not prove",
      "Role-specific robust scaling and equal family weights did not outperform every control. Standard scaling improved both retrieval and bootstrap stability over the robust baseline. Global scaling performed better on these consistency measures, but is not used for role-relative product interpretation. PCA offered no consistent advantage. Higher thresholds reduce coverage and shrink candidate groups; the resulting increase in stability is not pure evidence of a minutes effect.",
    ],
  ],
};
const nl: typeof en = {
  title: "Spelers-DNA",
  intro:
    "Vergelijk positiegebonden spelersprofielen op basis van open eventdata.",
  season: "Seizoen",
  team: "Team",
  role: "Rol",
  all: "Alle",
  threshold: "Minimaal betrouwbare minuten",
  search: "Zoek een speler",
  select: "Selecteer speler",
  results: "gevonden spelers",
  minutes: "betrouwbare minuten",
  matches: "wedstrijden",
  profile: "Speelprofiel",
  compared:
    "Vergelijking met spelers met voldoende data in dezelfde rol en hetzelfde seizoen.",
  cohort: "spelers in deze vergelijkingsgroep",
  version: "Profielversie",
  multi: "Meerdere rollen",
  roleMix: "Aandeel betrouwbare minuten per rol",
  neighbors: "Meest vergelijkbare waargenomen profielen",
  distance: "Afstand",
  stability: "Top 10-stabiliteit",
  compare: "Vergelijk",
  stabilityNote:
    "Frequentie in de top 10 over 100 bootstrapsteekproeven van wedstrijden. Dit meet steekproefstabiliteit, niet de kans op gelijkenis. Kleine rolgroepen verhogen de top 10-stabiliteit.",
  distanceNote:
    "Een kleinere afstand betekent meer overeenkomst in het waargenomen profiel. Vijf kenmerkfamilies wegen even zwaar. Doelpunten en xG bepalen deze rangorde niet.",
  similar: "Meeste overeenkomst in",
  different: "Grootste verschillen",
  contribution: "Bijdrage aan de gekwadrateerde afstand",
  compareTitle: "Profielvergelijking",
  percentile: "Percentiel binnen rol",
  more: "Meer is niet noodzakelijk beter.",
  low: "Deze speler voldoet niet aan de huidige minimale datadekking.",
  below_minutes: "De betrouwbare minuten liggen onder het gekozen minimum.",
  goalkeeper_excluded:
    "Vergelijking van keepers vraagt om eigen kenmerken en valt buiten deze versie.",
  uncertain_role:
    "De beschikbare rolminuten onderbouwen geen voldoende duidelijke primaire rol.",
  missing_core_features: "Vereiste kernkenmerken zijn niet beschikbaar.",
  sparse_role:
    "Minder dan 12 spelers met voldoende data delen deze rol. Vergelijking is niet beschikbaar.",
  unavailable: "Niet beschikbaar",
  loading: "Spelersgegevens worden geladen…",
  error:
    "De spelersgegevens konden niet worden geladen. Vernieuw de pagina als opnieuw proberen niet helpt.",
  retry: "Opnieuw proberen",
  empty: "Geen spelers gevonden met deze filters.",
  methodology: "Bekijk methodologie",
  map: "Kaart van spelersprofielen",
  mapNote:
    "Deze tweedimensionale PCA-weergave is een verkennende projectie. Afstanden zijn vereenvoudigd en bepalen niet de daadwerkelijke profielvergelijking. Nabijheid tussen verschillende rollen heeft geen vergelijkingsbetekenis.",
  mapLegend:
    "Een × markeert de geselecteerde speler. Omlijnde punten markeren nabije profielen. Speler- en roldetails zijn beschikbaar via toetsenbordfocus of in de tabel.",
  mapTable: "Kaart als spelerstabel",
  selectMap: "Verken de spelerskaart",
  territory: "Actiegebied",
  territoryNote:
    "Startpunten van passes, baldribbels en schoten, gegroepeerd over betrouwbare wedstrijden in 12 × 8 veldvakken. Aanval van links naar rechts. Donkerdere vakken bevatten meer acties.",
  territoryTable: "Actiegebied als datatabel",
  count: "Acties",
  cell: "Veldvak",
  evidence: "Stabiliteit van de representatie",
  evaluationNote:
    "Temporele evaluatie meet of een profiel uit de eerste periode dezelfde speler in een latere periode terugvindt. Dit meet consistentie, geen scoutingkwaliteit. De vergelijkingsgroepen zijn klein; bekijk de willekeurige referentie.",
  method: "Methode",
  queries: "Gekoppelde profielen",
  jaccard: "Top 10-Jaccard",
  random: "Willekeurige Recall@5",
  output: "Waargenomen resultaat · buiten de stijlafstand",
  notQuality:
    "Gelijkenis is geen kwaliteit, tactische passendheid, transfersucces of toekomstige prestatie. Eén seizoen in één competitie onderbouwt geen vergelijkbaarheid tussen competities.",
  methodsTitle: "Hoe spelers-DNA wordt berekend",
  definitions: "Kenmerkdefinities",
  methods: [
    [
      "Eerst de onderbouwing",
      "WSL 2023/24 is een volledig cohort van 132 wedstrijden. Speeltijd wordt gereconcilieerd met basisopstellingen, wissels, tijdelijke afwezigheid, kaarten en werkelijke periode-einden, inclusief blessuretijd. Tegenstrijdige speler-wedstrijdrecords worden samen met hun events uitgesloten. De korte SkillCorner-steekproef wordt niet voor gelijkenis gebruikt.",
    ],
    [
      "Rollen en drempels",
      "Kies 450, 600, 900 of 1.200 betrouwbare minuten. Standaard is dit 900. De zes ondersteunde rollen blijven gescheiden; minimaal 12 spelers met voldoende data zijn vereist. Keepers en te kleine groepen aanvallende middenvelders worden uitgesloten. Rolpercentages beschrijven waargenomen tijd, geen blijvende identiteit.",
    ],
    [
      "Kenmerken en afstand",
      "18 stijlkenmerken vormen vijf even zwaar gewogen families. Elk kenmerk wordt gecentreerd rond het gemiddelde van de rolgroep en gedeeld door de populatiestandaardafwijking. Constante kenmerken dragen niet bij. De afstand is de wortel van het gemiddelde van de gemiddelde gekwadrateerde verschillen per familie. Er is geen afkapping of kansscore. Percentielen gebruiken dezelfde rol, hetzelfde seizoen en dezelfde drempel; gelijke waarden delen het middenpercentiel.",
    ],
    [
      "Progressie en kansen creëren",
      "Een progressieve aangekomen pass in open spel of baldribbel verkleint de rechte afstand tot het midden van het doel met minstens 10 referentiemeter én minstens 25% van de beginafstand. Spelhervattingen tellen niet mee als passes. Acties naar het strafschopgebied beginnen buiten het gebied van 16,5 × 40,32 meter en eindigen erin. Schotassists en xA vereisen wederzijdse eventkoppelingen; xA gebruikt de bron-xG van het gekoppelde schot zonder penalty. Assists uit spelhervattingen tellen wel mee. Strafschoppenseries en eigen doelpunten zijn uitgesloten.",
    ],
    [
      "Stabiliteit en evaluatie",
      "Bootstrapsteekproeven trekken volledige wedstrijden per speler met teruglegging, berekenen kenmerken opnieuw en passen schaling opnieuw toe. Toelating en rollen blijven gelijk. Inclusiefrequenties tellen verschijningen in de top 10; Jaccard meet overlap met de oorspronkelijke groep. Temporele evaluatie gebruikt gescheiden kalenderperioden en leert schaling uitsluitend op de eerste periode. De experimenten vergelijken ook cosinus, PCA, robuuste en globale schaling, balbezitcontext en weglating van families.",
    ],
    [
      "Wat de experimenten niet bewezen",
      "Robuuste schaling per rol en gelijke familieweging presteerden niet beter dan elke referentiemethode. Standaardschaling verbeterde zowel herkenning als bootstrapstabiliteit ten opzichte van de robuuste basis. Globale schaling scoorde beter op deze consistentiematen, maar wordt niet gebruikt voor rolgebonden productinterpretatie. PCA bood geen consistent voordeel. Hogere drempels verkleinen de dekking en de vergelijkingsgroepen; de hogere stabiliteit bewijst daardoor niet uitsluitend een minuteneffect.",
    ],
  ],
};
export const dnaCopy: Record<Locale, typeof en> = { en, nl };
export const families: Record<Locale, Record<string, string>> = {
  en: {
    shooting: "Shooting",
    creation: "Chance creation",
    passing: "Passing",
    carrying: "Carrying",
    defending: "Defensive activity",
  },
  nl: {
    shooting: "Schieten",
    creation: "Kansen creëren",
    passing: "Passen",
    carrying: "Baldribbels",
    defending: "Verdedigende activiteit",
  },
};
export const methods: Record<Locale, Record<string, string>> = {
  en: {
    standard_scaling: "Selected · standard Euclidean",
    euclidean: "Robust Euclidean",
    cosine: "Robust cosine",
    pca: "Robust PCA",
    global_scaling: "Global robust scaling",
    naive_features: "Unbalanced features",
    winsor_scaling: "Clipped robust scaling",
    possession_context: "Possession adjustment",
  },
  nl: {
    standard_scaling: "Gekozen · standaard Euclidisch",
    euclidean: "Robuust Euclidisch",
    cosine: "Robuuste cosinus",
    pca: "Robuuste PCA",
    global_scaling: "Globale robuuste schaling",
    naive_features: "Ongebalanceerde kenmerken",
    winsor_scaling: "Afgekapte robuuste schaling",
    possession_context: "Balbezitcorrectie",
  },
};
