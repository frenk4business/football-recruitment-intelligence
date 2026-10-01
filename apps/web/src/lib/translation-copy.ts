export const translationCopy = {
  en: {
    title: "Historical translation",
    intro:
      "Historical WSL research only. This is not a current or cross-league forecast.",
    search: "Find a player",
    player: "Player",
    source: "Observed source environment",
    target: "Target environment",
    role: "Assumed target role",
    selectNote:
      "Sources: 2019/20 · targets: 2020/21 · FA Women’s Super League. Other observed seasons remain visible with their exclusions.",
    loading: "Loading the player’s historical evidence…",
    error:
      "This player could not be loaded. Reload the page if retrying does not help.",
    retry: "Try again",
    empty: "No players match this search.",
    observed: "Observed source",
    expected: "Expected target",
    range: "80% prediction range",
    per90: "per 90 minutes",
    metric: "Action",
    method: "Method",
    minutes: "reliable minutes",
    appearances: "appearances",
    unsupported: "No supported estimate for this scenario",
    supported: "Historical scenario · conditional estimate",
    results: "Expected performance, with room for uncertainty",
    intervalNote:
      "The shaded bar is a range for a future observed rate, not a confidence interval for a model coefficient. The hollow dot is the source observation; the solid dot is the expected target rate. Each row has its own scale.",
    baselineNote:
      "Default ranges use errors from earlier player-separated validation folds. They reflect season windows with at least 600 minutes and are not adjusted to a precise exposure. The optional research model simulates a 900-minute observation.",
    calibrationNote:
      "Ranges are imperfect: the selected 80% ranges covered 74% of shots, 71% of progressive passes, 80% of carries and 76% of pressures in the later season. Pass and shot uncertainty is understated.",
    evidence: "How much evidence supports this?",
    direct: "matching source-team → target-team / role episodes",
    teamRole: "target-team / role episodes",
    roleCount: "episodes in this target role",
    development: "earlier development episodes",
    pooling:
      "Sparse direct evidence. This scenario relies mainly on shared patterns across players and teams. It is not a directly observed transfer effect.",
    directNote:
      "These counts refer to earlier observed episodes, not to this hypothetical move. Even a supported scenario is not a club recommendation.",
    context: "Historical team context available through",
    contextMatches: "source / target team matches",
    unseen:
      "The target team was not represented in model fitting; the research model uses a population team prior.",
    research: "Compare the Bayesian research model",
    researchNote:
      "Research comparison only. It did not pass every validation selection rule and is not the default. These are posterior predictive ranges, including observation noise; they condition on the measured source profile.",
    limits: "Read this as a small historical study",
    limitsBody:
      "65 development episodes and 76 later-season episodes; just 4 held-out team changes. Most observations are the same player at the same club in a later season. Target role is a scenario assumption. Destination minutes and survival in the dataset are selected, so non-playing and failed moves are underrepresented. There is no causal league-strength estimate and no current-season forecast.",
    methodology: "Methods, calibration and limitations",
    evaluation: "What happened in the later season?",
    evaluationIntro:
      "Methods were selected on 12 validation players, then fitted on 65 earlier episodes. The 76 later episodes were untouched until selection was frozen. Lower error is better; coverage should be close to the nominal 80% without unnecessarily wide ranges.",
    calibration: "Coverage of the nominal 80% range",
    mae: "Mean absolute error",
    width: "Mean 80% width",
    selected: "Default",
    allResults: "All held-out results",
    study: "Study design and model",
    studyBody:
      "Three baselines were compared with four hierarchical negative-binomial count models. Minutes enter as exposure; role and team effects are partially pooled. Source activity and only pre-change team context are inputs. Four chains per target had zero divergences and maximum R-hat below 1.006. Good sampling does not guarantee good prediction.",
    decisions:
      "Ridge was selected for shots and progressive passes. Unchanged source rates were selected for carries and pressures. Changing the target team therefore does not change those two default point estimates. No Bayesian target met all validation rules; later results did not change that decision.",
  },
  nl: {
    title: "Prestaties veranderen met de context.",
    intro:
      "Verken een historisch WSL-seizoensscenario met een verwachte waarde, een zichtbare voorspellingsband en de bijbehorende onderbouwing. Dit onderzoek ondersteunt geen vertaling tussen competities.",
    search: "Zoek een speler",
    player: "Speler",
    source: "Waargenomen bronomgeving",
    target: "Doelomgeving",
    role: "Aangenomen doelrol",
    selectNote:
      "Bronnen: 2019/20 · doelen: 2020/21 · FA Women’s Super League. Andere waargenomen seizoenen blijven zichtbaar met hun uitsluitingsredenen.",
    loading: "Historische spelersgegevens laden…",
    error:
      "Deze speler kon niet worden geladen. Vernieuw de pagina als opnieuw proberen niet helpt.",
    retry: "Opnieuw proberen",
    empty: "Geen spelers gevonden voor deze zoekopdracht.",
    observed: "Waargenomen bron",
    expected: "Verwacht in doelomgeving",
    range: "80%-voorspellingsband",
    per90: "per 90 minuten",
    metric: "Actie",
    method: "Methode",
    minutes: "betrouwbare minuten",
    appearances: "optredens",
    unsupported: "Geen onderbouwde schatting voor dit scenario",
    supported: "Historisch scenario · voorwaardelijke schatting",
    results: "Verwachte prestaties, met zichtbare onzekerheid",
    intervalNote:
      "De balk toont een band voor een toekomstige waargenomen waarde, geen betrouwbaarheidsinterval van een modelcoëfficiënt. De open stip is de bronwaarneming; de volle stip is de verwachte waarde. Elke rij heeft een eigen schaal.",
    baselineNote:
      "De standaardbanden gebruiken fouten uit eerdere, op speler gescheiden validatiegroepen. Ze beschrijven seizoensvensters van minimaal 600 minuten en zijn niet aangepast aan een exact aantal speelminuten. Het optionele onderzoeksmodel simuleert een waarneming van 900 minuten.",
    calibrationNote:
      "De banden zijn onvolmaakt: de gekozen 80%-banden omvatten in het latere seizoen 74% van de schoten, 71% van de progressieve passes, 80% van de dribbels en 76% van de drukacties. De onzekerheid bij passes en schoten wordt onderschat.",
    evidence: "Hoeveel waarnemingen ondersteunen dit?",
    direct: "episodes met dit bronteam → doelteam en deze rol",
    teamRole: "episodes met dit doelteam en deze rol",
    roleCount: "episodes in deze doelrol",
    development: "eerdere ontwikkel-episodes",
    pooling:
      "Weinig directe waarnemingen. Dit scenario steunt vooral op gedeelde patronen tussen spelers en teams. Het is geen rechtstreeks waargenomen transfereffect.",
    directNote:
      "Deze aantallen gaan over eerdere waarnemingen, niet over deze hypothetische overstap. Een ondersteund scenario is geen clubaanbeveling.",
    context: "Historische teamcontext beschikbaar tot",
    contextMatches: "wedstrijden van bronteam / doelteam",
    unseen:
      "Het doelteam kwam niet voor bij het schatten van het model; het onderzoeksmodel gebruikt daarom een algemene teamaanname.",
    research: "Vergelijk het Bayesiaanse onderzoeksmodel",
    researchNote:
      "Alleen als onderzoeksvergelijking. Dit model voldeed niet aan alle validatieregels en is daarom niet de standaard. De posterior-predictieve banden bevatten waarnemingsruis en zijn voorwaardelijk op het gemeten bronprofiel.",
    limits: "Lees dit als een klein historisch onderzoek",
    limitsBody:
      "65 ontwikkel-episodes en 76 episodes uit een later seizoen; slechts 4 teamwissels in de test. De meeste waarnemingen gaan over dezelfde speler bij dezelfde club in een later seizoen. De doelrol is een scenarioaanname. De selectie op speelminuten en beschikbaarheid ondervertegenwoordigt spelers die niet spelen en mislukte overstappen. Dit is geen causale schatting van competitiesterkte of voorspelling voor het huidige seizoen.",
    methodology: "Methoden, kalibratie en beperkingen",
    evaluation: "Wat gebeurde er in het latere seizoen?",
    evaluationIntro:
      "Methoden zijn gekozen met 12 validatiespelers en daarna geschat op 65 eerdere episodes. De 76 latere episodes bleven buiten beschouwing tot de keuze vaststond. Een lagere fout is beter; de dekking hoort bij 80% te liggen zonder onnodig brede banden.",
    calibration: "Dekking van de nominale 80%-band",
    mae: "Gemiddelde absolute fout",
    width: "Gemiddelde 80%-breedte",
    selected: "Standaard",
    allResults: "Alle testresultaten",
    study: "Onderzoeksopzet en model",
    studyBody:
      "Drie basismodellen zijn vergeleken met vier hiërarchische negatief-binomiale telmodellen. Speelminuten bepalen de blootstelling; rol- en teameffecten worden gedeeltelijk gezamenlijk geschat. Bronactiviteit en uitsluitend eerdere teamcontext vormen de invoer. Vier ketens per kenmerk hadden nul divergenties en een maximale R-hat onder 1,006. Goed convergeren garandeert geen goede voorspellingen.",
    decisions:
      "Ridge-regressie is gekozen voor schoten en progressieve passes. Voor dribbels en drukacties is de ongewijzigde bronwaarde gekozen. Een ander doelteam verandert die twee standaardpuntwaarden dus niet. Geen Bayesiaans model voldeed aan alle validatieregels; de latere test veranderde die keuze niet.",
  },
};
export const translationMethods: Record<string, [string, string]> = {
  unchanged_source: ["Unchanged source", "Ongewijzigde bron"],
  role_mean: ["Role average", "Rolgemiddelde"],
  ridge: ["Ridge regression", "Ridge-regressie"],
  hierarchical_nb: ["Hierarchical count model", "Hiërarchisch telmodel"],
};
export const translationExclusions: Record<string, [string, string]> = {
  outside_source_season: [
    "Only 2019/20 sources support this historical scenario.",
    "Alleen bronnen uit 2019/20 ondersteunen dit historische scenario.",
  ],
  identity_quarantined: [
    "Conflicting identity metadata requires review.",
    "Tegenstrijdige identiteitsgegevens vereisen controle.",
  ],
  below_600_reliable_minutes: [
    "Fewer than 600 reliable source minutes.",
    "Minder dan 600 betrouwbare bronminuten.",
  ],
  unsupported_source_role: [
    "The source role is missing or outside the outfield study.",
    "De bronrol ontbreekt of valt buiten het onderzoek naar veldspelers.",
  ],
  missing_source_features: [
    "Required source observations are unavailable.",
    "Vereiste bronwaarnemingen ontbreken.",
  ],
  source_outside_development_range: [
    "At least one source action rate falls outside the earlier development range.",
    "Minstens één bronkenmerk valt buiten het eerdere ontwikkelbereik.",
  ],
  unsupported_role_change: [
    "This role change lies outside the same or adjacent role study.",
    "Deze rolwissel valt buiten het onderzoek naar dezelfde of aangrenzende rollen.",
  ],
  fewer_than_5_role_episodes: [
    "Fewer than five earlier episodes support this target role.",
    "Minder dan vijf eerdere episodes ondersteunen deze doelrol.",
  ],
  missing_prechange_team_context: [
    "Fewer than three earlier team matches are available before the source observation ends.",
    "Minder dan drie eerdere teamwedstrijden zijn beschikbaar vóór het einde van de bronwaarneming.",
  ],
};
