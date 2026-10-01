export const recruitmentCopy = {
  en: {
    title: "Build a shortlist",
    intro:
      "Build an explicit profile, compare observed playing styles and inspect the evidence behind the ordering. WSL 2023/24 only.",
    find: "Find Candidates",
    replace: "Replace a Player",
    context: "Club Context",
    club: "Target club",
    role: "Target role",
    reference: "Reference player",
    observed: "Observed season: 2023/24",
    principle:
      "Rankings organise evidence under the selected criteria; they do not make a transfer decision.",
    loading: "Loading the observed cohort…",
    error:
      "The recruitment data could not be loaded. Reload the page if retrying does not help.",
    retry: "Try again",
    invalid:
      "This shared scenario is invalid or uses unsupported data. Start a new scenario below.",
    reset: "Reset scenario",
    share: "Copy scenario link",
    copied: "Link copied",
    shareFallback: "Copy this scenario link",
    shareError: "Copy the link below to share this scenario.",
    custom: "Your requirements",
    customNote:
      "Start with the characteristics that matter to you. Nothing is ranked until you select at least one requirement.",
    replacementNote:
      "The reference player's whole-season profile sets exact targets. Adjust any preference to create an adjusted replacement; the reference player is excluded.",
    noReference:
      "No eligible replacement profile exists at this club and role. Choose another role or build custom requirements.",
    advanced: "Advanced requirements · all 18 features",
    preference: "Preference",
    target: "Target percentile",
    importance: "Importance",
    required: "Hard constraint",
    exact: "Similar to",
    minimum: "At least",
    maximum: "At most",
    neutral: "Ignore",
    low: "Low · 1",
    medium: "Medium · 2",
    high: "High · 3",
    familyImportance: "Family importance",
    defaultWeights:
      "All explicit requirements have equal weight by default. Family importance multiplies feature importance.",
    definitions: "Feature definitions",
    assumption: "Analyst requirement",
    source: "Source",
    roleMedian: "Club role median",
    roleRange: "Club role range",
    useMedian: "Use role median",
    constraints: "Candidate filters",
    minimumMinutes: "Minimum reliable minutes",
    evidenceThreshold: "Minimum neighbour stability",
    anyEvidence: "No extra threshold",
    candidateTeam: "Candidate team",
    allTeams: "All teams",
    excludeClub: "Exclude players already at this club",
    cohort: "Comparison cohort",
    cohortNote:
      "138 eligible observed profiles across six roles at 900 minutes. Percentiles stay relative to the original role cohort when filters change.",
    available: "eligible candidates",
    excluded: "excluded profiles",
    shortlist: "Candidate shortlist",
    shortlistNote:
      "Top 10 under your selected criteria. A smaller mismatch means a closer profile; it does not mean a better player.",
    noRequirements: "Choose a requirement to create a shortlist.",
    noCandidates:
      "No candidates satisfy these constraints. Review the filters or choose a supported role.",
    player: "Player / team",
    minutes: "Minutes",
    fit: "Fit distance",
    gap: "pt mismatch",
    evidence: "Evidence",
    neighbor: "Neighbour stability",
    keyMatch: "Key match",
    mismatch: "Main mismatch",
    none: "No mismatch",
    compare: "Compare",
    compareMax: "Select up to three candidates",
    selected: "selected",
    frontier: "Trade-off candidate",
    frontierCount: "on the trade-off frontier",
    frontierNote:
      "No eligible candidate is at least as close on every selected criterion and closer on at least one. Ties can share the frontier; this is not an optimal-player label.",
    frontierMany:
      "With many criteria, most candidates can be non-dominated. Inspect the actual differences.",
    robustness: "How stable is this ordering?",
    weights: "Weight sensitivity",
    profiles: "Profile sampling",
    inclusion: "Top-10 inclusion",
    rankRange: "10th–90th rank range",
    weightNote:
      "100 weight changes within ±20%; the target and candidate profiles stay fixed.",
    profileNote:
      "100 player-match bootstraps; requirements and eligibility stay fixed. This does not measure success probability.",
    smallPool:
      "There are ten or fewer candidates: everyone necessarily enters the top 10. Inspect rank ranges instead.",
    profileLoading: "Loading profile sensitivity…",
    profileError:
      "Profile sensitivity is unavailable; observed rankings remain available.",
    compareTitle: "Compare the shortlist",
    compareNote:
      "Role-relative percentiles: higher means more activity, not better performance. Requirement targets and club roster references are shown separately.",
    playerValue: "Candidate",
    contribution: "Share of mismatch",
    fullDNA: "Open observed Player DNA",
    multiClub: "Whole-season profile across multiple clubs",
    noRoster:
      "No complete club-stint profile meets the 900-minute threshold in this role.",
    roster: "Observed roster by role",
    depth: "Observed players",
    profileDepth: "Eligible stint profiles",
    concentration: "Largest minutes share",
    hhi: "Minutes concentration (HHI)",
    rosterNote:
      "Roster profiles use each player's events at this club, with at least 900 reliable stint minutes. A selected target above a roster characteristic describes a data-defined gap, not a transfer need.",
    teamStyle: "Observed team behaviour",
    contextNote:
      "Team events per 90 actual match minutes, including goalkeepers. Percentiles compare the 12 clubs in this season. These describe an observation window, not a permanent club identity.",
    window: "Observation window",
    matches: "matches",
    raw: "Team actions /90",
    teamPercentile: "Team percentile",
    adopt: "Use as a requirement",
    adoptNote:
      "Adoption sets a player-role minimum at this team percentile. That mapping is your explicit assumption, not a validated recruitment rule.",
    exclusionsTitle: "Inspect exclusions",
    unavailable: "Unavailable",
    sparseRole: "AM · insufficient comparison evidence",
    translationTitle: "Observed Fit · translation unsupported",
    translationWarning:
      "No validated translation model is available for this environment. Ranking uses observed profile only.",
    translationLink: "Open historical translation research",
    translationPeriod:
      "Research period: 2019/20 → 2020/21. It does not forecast 2024/25 or translate between leagues.",
    methods: "Recruitment methodology",
    methodsIntro:
      "Data, assumptions, ranking and evidence have different meanings. Keep them visible when interpreting a shortlist.",
    methodDefinitions: [
      [
        "Observed profile",
        "What a player did in the selected season, using the existing 18 Player DNA features.",
      ],
      [
        "Requirement profile",
        "What the analyst asks for: exact, minimum, maximum or neutral preferences with visible weights and sources.",
      ],
      [
        "Club context",
        "Observed team behaviour and role-specific roster distributions. Context does not silently add ranking criteria.",
      ],
      [
        "Fit",
        "Weighted root mean squared percentile-point mismatch. Lower means closer to the selected requirements. Hard constraints remove candidates first.",
      ],
      [
        "Evidence",
        "Reliable minutes and existing neighbour stability. Evidence is never averaged into football fit.",
      ],
      [
        "Translation",
        "Only the separate historical environments supported by Phase 3. Its simple defaults and calibration limitations remain unchanged.",
      ],
    ],
    evaluationTitle: "What the evaluation establishes",
    evaluationNote:
      "The four final query clubs were held out from method selection. The 2023/24 season had already been examined in Phase 2. These small retrospective tests measure representation consistency and roster alignment, not transfer success.",
    temporal: "Later-half peer retrieval",
    rosterTest: "Roster holdout",
    ablation: "Club-context ablation",
    method: "Method",
    queries: "Queries",
    recall5: "Recall@5",
    recall10: "Recall@10",
    random: "Random expectation",
    allMethods: "All development and final comparisons",
    development: "Development",
    final: "Final queries",
    researchLink: "Read the complete evaluation and limitations",
    robustSummary:
      "Mean top-10 Jaccard across 205 scenarios: weights 0.950; profile sampling 0.723. Fourteen scenarios have at most ten candidates, which inflates inclusion. Context gains are mixed and do not establish recruitment value.",
  },
  nl: {
    title: "Stel een shortlist samen",
    intro:
      "Stel een expliciet profiel samen, vergelijk waargenomen speelstijlen en bekijk de onderbouwing van de ranglijst. Alleen WSL 2023/24.",
    find: "Kandidaten zoeken",
    replace: "Speler vervangen",
    context: "Clubcontext",
    club: "Doelclub",
    role: "Doelrol",
    reference: "Referentiespeler",
    observed: "Waargenomen seizoen: 2023/24",
    principle:
      "De ranglijst ordent de beschikbare data op basis van de gekozen criteria; ze neemt geen transferbeslissing.",
    loading: "De waargenomen spelersgroep laden…",
    error:
      "De recruitmentdata kon niet worden geladen. Vernieuw de pagina als opnieuw proberen niet helpt.",
    retry: "Opnieuw proberen",
    invalid:
      "Dit gedeelde scenario is ongeldig of gebruikt niet-ondersteunde data. Begin hieronder een nieuw scenario.",
    reset: "Scenario herstellen",
    share: "Scenariolink kopiëren",
    copied: "Link gekopieerd",
    shareFallback: "Kopieer deze scenariolink",
    shareError: "Kopieer de onderstaande link om dit scenario te delen.",
    custom: "Jouw eisen",
    customNote:
      "Begin met de kenmerken die voor jou belangrijk zijn. Er verschijnt pas een ranglijst als je minstens één eis kiest.",
    replacementNote:
      "Het volledige seizoensprofiel van de referentiespeler bepaalt de exacte doelen. Pas een voorkeur aan voor een aangepaste vervanging; de referentiespeler wordt uitgesloten.",
    noReference:
      "Deze club en rol hebben geen geschikt referentieprofiel. Kies een andere rol of stel eigen eisen samen.",
    advanced: "Geavanceerde eisen · alle 18 kenmerken",
    preference: "Voorkeur",
    target: "Doelpercentiel",
    importance: "Belang",
    required: "Harde eis",
    exact: "Vergelijkbaar met",
    minimum: "Minstens",
    maximum: "Hoogstens",
    neutral: "Negeren",
    low: "Laag · 1",
    medium: "Middel · 2",
    high: "Hoog · 3",
    familyImportance: "Belang van kenmerkgroep",
    defaultWeights:
      "Elke expliciete eis weegt standaard even zwaar. Het groepsbelang vermenigvuldigt het belang van het kenmerk.",
    definitions: "Kenmerkdefinities",
    assumption: "Eis van de analist",
    source: "Herkomst",
    roleMedian: "Clubmediaan voor de rol",
    roleRange: "Clubbereik voor de rol",
    useMedian: "Rolmediaan gebruiken",
    constraints: "Kandidaatfilters",
    minimumMinutes: "Minimale betrouwbare minuten",
    evidenceThreshold: "Minimale stabiliteit van buren",
    anyEvidence: "Geen extra drempel",
    candidateTeam: "Club van kandidaat",
    allTeams: "Alle clubs",
    excludeClub: "Spelers van deze club uitsluiten",
    cohort: "Vergelijkingsgroep",
    cohortNote:
      "138 geschikte waargenomen profielen in zes rollen bij 900 minuten. Percentielen blijven relatief aan de oorspronkelijke rolgroep als filters veranderen.",
    available: "geschikte kandidaten",
    excluded: "uitgesloten profielen",
    shortlist: "Kandidatenlijst",
    shortlistNote:
      "De top 10 volgens jouw criteria. Een kleinere afwijking betekent een beter passend profiel; het betekent geen betere speler.",
    noRequirements: "Kies een eis om een kandidatenlijst te maken.",
    noCandidates:
      "Geen kandidaten voldoen aan deze voorwaarden. Bekijk de filters of kies een ondersteunde rol.",
    player: "Speler / club",
    minutes: "Minuten",
    fit: "Profielafstand",
    gap: "pt afwijking",
    evidence: "Onderbouwing",
    neighbor: "Stabiliteit van buren",
    keyMatch: "Sterkste overeenkomst",
    mismatch: "Grootste afwijking",
    none: "Geen afwijking",
    compare: "Vergelijken",
    compareMax: "Selecteer maximaal drie kandidaten",
    selected: "geselecteerd",
    frontier: "Kandidaat met afwegingen",
    frontierCount: "op de afwegingsgrens",
    frontierNote:
      "Geen geschikte kandidaat is op elk gekozen criterium minstens even dichtbij én op minstens één criterium dichterbij. Gelijke profielen kunnen de grens delen; dit betekent geen optimale speler.",
    frontierMany:
      "Bij veel criteria kunnen de meeste kandidaten niet-gedomineerd zijn. Bekijk de concrete verschillen.",
    robustness: "Hoe stabiel is deze ranglijst?",
    weights: "Gevoeligheid voor gewichten",
    profiles: "Steekproeven van profielen",
    inclusion: "Aanwezigheid in top 10",
    rankRange: "10e–90e percentiel van positie",
    weightNote:
      "100 wijzigingen van gewichten binnen ±20%; het doel en de kandidaatprofielen blijven gelijk.",
    profileNote:
      "100 bootstraps van spelerwedstrijden; eisen en geschiktheid blijven gelijk. Dit meet geen kans op succes.",
    smallPool:
      "Er zijn hoogstens tien kandidaten: iedereen staat noodzakelijk in de top 10. Bekijk het bereik van de rangposities.",
    profileLoading: "Profielgevoeligheid laden…",
    profileError:
      "Profielgevoeligheid is niet beschikbaar; de waargenomen ranglijst blijft beschikbaar.",
    compareTitle: "De kandidaten vergelijken",
    compareNote:
      "Percentielen binnen de rol: hoger betekent meer activiteit, geen betere prestatie. Eisen en clubreferenties worden afzonderlijk getoond.",
    playerValue: "Kandidaat",
    contribution: "Aandeel in afwijking",
    fullDNA: "Waargenomen spelers-DNA openen",
    multiClub: "Volledig seizoensprofiel over meerdere clubs",
    noRoster:
      "Geen volledig clubprofiel haalt in deze rol de drempel van 900 betrouwbare minuten.",
    roster: "Waargenomen selectie per rol",
    depth: "Waargenomen spelers",
    profileDepth: "Geschikte clubprofielen",
    concentration: "Grootste minutenaandeel",
    hhi: "Concentratie van minuten (HHI)",
    rosterNote:
      "Selectieprofielen gebruiken alleen acties bij deze club, met minstens 900 betrouwbare minuten daar. Een gekozen doel boven een selectiekenmerk beschrijft een dataverschil, geen transferbehoefte.",
    teamStyle: "Waargenomen teamgedrag",
    contextNote:
      "Teamacties per 90 werkelijke wedstrijdminuten, inclusief keepers. Percentielen vergelijken de 12 clubs in dit seizoen. Ze beschrijven een meetperiode, geen blijvende clubidentiteit.",
    window: "Meetperiode",
    matches: "wedstrijden",
    raw: "Teamacties /90",
    teamPercentile: "Teampercentiel",
    adopt: "Als eis gebruiken",
    adoptNote:
      "Dit stelt een minimum voor de spelersrol in op dit teampercentiel. Die vertaling is jouw expliciete aanname, geen gevalideerde recruitmentregel.",
    exclusionsTitle: "Uitsluitingen bekijken",
    unavailable: "Niet beschikbaar",
    sparseRole: "AM · onvoldoende vergelijkingsdata",
    translationTitle: "Waargenomen profielmatch · vertaling niet ondersteund",
    translationWarning:
      "Er is geen gevalideerd vertaalmodel beschikbaar voor deze omgeving. De ranglijst gebruikt alleen het waargenomen profiel.",
    translationLink: "Historisch vertaalonderzoek openen",
    translationPeriod:
      "Onderzoeksperiode: 2019/20 → 2020/21. Dit voorspelt geen 2024/25 en vertaalt niet tussen competities.",
    methods: "Recruitmentmethodologie",
    methodsIntro:
      "Data, aannames, ranglijsten en onderbouwing hebben verschillende betekenissen. Houd ze zichtbaar bij het beoordelen van kandidaten.",
    methodDefinitions: [
      [
        "Waargenomen profiel",
        "Wat een speler deed in het gekozen seizoen, met de bestaande 18 kenmerken van spelers-DNA.",
      ],
      [
        "Eisenprofiel",
        "Wat de analist vraagt: exacte, minimale, maximale of neutrale voorkeuren met zichtbare gewichten en herkomst.",
      ],
      [
        "Clubcontext",
        "Waargenomen teamgedrag en verdelingen van selectieprofielen per rol. Context voegt niet stilzwijgend criteria toe.",
      ],
      [
        "Profielmatch",
        "Gewogen wortel van de gemiddelde gekwadrateerde afwijking in percentielpunten. Lager is dichter bij de gekozen eisen. Harde voorwaarden sluiten eerst kandidaten uit.",
      ],
      [
        "Onderbouwing",
        "Betrouwbare minuten en bestaande stabiliteit van vergelijkbare spelers. Deze worden nooit gemiddeld met de profielmatch.",
      ],
      [
        "Vertaling",
        "Alleen de afzonderlijke historische omgevingen die Fase 3 ondersteunt. De eenvoudige standaardmodellen en kalibratiebeperkingen blijven behouden.",
      ],
    ],
    evaluationTitle: "Wat de evaluatie aantoont",
    evaluationNote:
      "De vier clubs met finale onderzoeksvragen bleven buiten de methodeselectie. Seizoen 2023/24 was al onderzocht in Fase 2. Deze kleine retrospectieve tests meten profielconsistentie en selectieovereenkomst, geen transfersucces.",
    temporal: "Buren terugvinden in de latere seizoenshelft",
    rosterTest: "Weggelaten selectiespeler",
    ablation: "Clubcontextvergelijking",
    method: "Methode",
    queries: "Onderzoeksvragen",
    recall5: "Recall@5",
    recall10: "Recall@10",
    random: "Verwachting bij toeval",
    allMethods: "Alle ontwikkel- en finale vergelijkingen",
    development: "Ontwikkeling",
    final: "Finale vragen",
    researchLink: "Volledige evaluatie en beperkingen lezen",
    robustSummary:
      "Gemiddelde top-10-Jaccard over 205 scenario's: gewichten 0,950; profielsteekproeven 0,723. Veertien scenario's hebben hoogstens tien kandidaten, waardoor aanwezigheid wordt overschat. Contextwinst is wisselend en bewijst geen recruitmentwaarde.",
  },
} as const;
export const recruitmentFamilies: Record<string, [string, string]> = {
  shooting: ["Shooting", "Schieten"],
  creation: ["Creation", "Creatie"],
  passing: ["Passing", "Passen"],
  carrying: ["Carrying", "Baldribbels"],
  defending: ["Defensive activity", "Verdedigende activiteit"],
};
export const requirementSources: Record<string, [string, string]> = {
  user_defined: ["Your choice", "Jouw keuze"],
  observed_club_context: [
    "Adopted club characteristic",
    "Overgenomen clubkenmerk",
  ],
  replacement_player: ["Reference player", "Referentiespeler"],
  derived_roster_gap: [
    "Observed roster reference",
    "Waargenomen selectiereferentie",
  ],
};
export const recruitmentExclusions: Record<string, [string, string]> = {
  wrong_role: ["Different role", "Andere rol"],
  below_minutes: ["Insufficient minutes", "Onvoldoende minuten"],
  below_evidence_threshold: [
    "Below stability threshold",
    "Onder stabiliteitsdrempel",
  ],
  same_club_excluded: ["Already at target club", "Al bij de doelclub"],
  candidate_team_filter: ["Outside selected team", "Buiten de gekozen club"],
  replacement_reference: [
    "Reference player excluded",
    "Referentiespeler uitgesloten",
  ],
  missing_required_feature: [
    "Required feature unavailable",
    "Vereist kenmerk ontbreekt",
  ],
  hard_feature_constraint: [
    "Fails a hard feature constraint",
    "Voldoet niet aan een harde kenmerkeis",
  ],
  uncertain_role: ["Uncertain role", "Onzekere rol"],
  goalkeeper_excluded: ["Goalkeeper excluded", "Keeper uitgesloten"],
  missing_core_features: [
    "Incomplete observed profile",
    "Onvolledig waargenomen profiel",
  ],
  sparse_role: ["Insufficient role cohort", "Onvoldoende spelers in de rol"],
  unsupported_role: ["Unsupported role", "Niet-ondersteunde rol"],
};
export const recruitmentMethods: Record<string, [string, string]> = {
  weighted_rms: ["Weighted requirement distance", "Gewogen eisenafstand"],
  family_rms: ["Family-balanced distance", "Afstand met gelijke groepen"],
  satisfaction: ["Threshold satisfaction", "Drempelovereenkomst"],
  hybrid: ["Threshold + distance", "Drempel + afstand"],
  dna_nearest_neighbor: ["Existing Player DNA", "Bestaand spelers-DNA"],
  requirements_only: ["Requirements only", "Alleen eisen"],
  plus_role_median: ["Requirements + role median", "Eisen + rolmediaan"],
  plus_full_context: ["Requirements + role + team", "Eisen + rol + team"],
};
