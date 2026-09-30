"""Executable bilingual feature definitions. Higher means more, not better."""

from pydantic import BaseModel, ConfigDict

VERSION = "features-v1"
DNA_VERSION = "player-dna-v1"


class FeatureDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label_en: str
    label_nl: str
    family: str
    unit: str
    formula: str
    note_en: str
    note_nl: str
    core: bool
    intended_use: str
    source: str = "StatsBomb"
    higher_is: str = "descriptive"
    eligibility: str = "Reliable participation time; complete relevant event fields; role cohort; selected minute threshold."
    null_semantics: str = (
        "Unavailable evidence or zero denominator is null; measured absence is zero."
    )
    version: str = VERSION


SPECS = [
    (
        "shots",
        "Non-penalty shots",
        "Schoten zonder penalty's",
        "shooting",
        "Shot, excluding Penalty and period 5",
    ),
    (
        "box_shots",
        "Shots from the box",
        "Schoten uit het strafschopgebied",
        "shooting",
        "Non-penalty Shot starting in x>=88.5, 13.84<=y<=54.16",
    ),
    (
        "shot_assists",
        "Shot assists",
        "Schotassists",
        "creation",
        "Pass with explicit assisted_shot_id and reciprocal shot.key_pass_id; non-penalty Shot",
    ),
    (
        "box_passes",
        "Passes into the box",
        "Passes naar het strafschopgebied",
        "creation",
        "Completed open-play Pass from outside to inside penalty area",
    ),
    (
        "crosses",
        "Completed crosses",
        "Aangekomen voorzetten",
        "creation",
        "Completed open-play Pass with pass.cross=true",
    ),
    (
        "passes",
        "Passing volume",
        "Passvolume",
        "passing",
        "All attempted open-play Pass events; exclude Corner, Free Kick, Throw-in, Kick Off, Goal Kick",
    ),
    (
        "progressive_passes",
        "Progressive passes",
        "Progressieve passes",
        "passing",
        "Completed open-play Pass reducing distance to goal (105,34) by >=max(10m,25% of starting distance)",
    ),
    (
        "final_third_passes",
        "Final-third entries by pass",
        "Passes naar het laatste derde",
        "passing",
        "Completed open-play Pass from x<70 to end_x>=70",
    ),
    (
        "long_passes",
        "Long passes",
        "Lange passes",
        "passing",
        "Open-play Pass with canonical Euclidean start-to-end distance >=30m; attempts",
    ),
    (
        "carries",
        "Carrying volume",
        "Baldribbelvolume",
        "carrying",
        "Provider Carry event count; no synthetic carries",
    ),
    (
        "progressive_carries",
        "Progressive carries",
        "Progressieve baldribbels",
        "carrying",
        "Carry reducing distance to goal (105,34) by >=max(10m,25% of starting distance)",
    ),
    (
        "carry_distance",
        "Carry distance",
        "Baldribbelafstand",
        "carrying",
        "Sum of Euclidean Carry displacement in reference metres; not physical tracking distance",
    ),
    (
        "box_carries",
        "Carries into the box",
        "Baldribbels naar het strafschopgebied",
        "carrying",
        "Carry from outside to inside penalty area",
    ),
    (
        "pressures",
        "Pressures",
        "Drukacties",
        "defending",
        "Provider Pressure event count; no inferred off-ball pressure",
    ),
    (
        "counterpressures",
        "Counterpressures",
        "Tegendrukacties",
        "defending",
        "Pressure with counterpress=true",
    ),
    ("tackles", "Tackles", "Tackles", "defending", "Duel with type Tackle; all outcomes"),
    (
        "interceptions",
        "Interceptions",
        "Onderscheppingen",
        "defending",
        "Interception event count; all outcomes",
    ),
    (
        "recoveries",
        "Ball recoveries",
        "Balheroveringen",
        "defending",
        "Ball Recovery event count; all outcomes",
    ),
]

REGISTRY = [
    FeatureDefinition(
        id=key + "_per90",
        label_en=en,
        label_nl=nl,
        family=family,
        unit="m / 90" if key == "carry_distance" else "per90",
        formula=f"90 * sum({definition}) / sum(reliable elapsed minutes)",
        note_en="Observed behaviour in this season; includes stoppage time in the denominator. More is not necessarily better.",
        note_nl="Waargenomen gedrag in dit seizoen; de noemer bevat blessuretijd. Meer is niet noodzakelijk beter.",
        core=True,
        intended_use="style similarity",
    )
    for key, en, nl, family, definition in SPECS
]

for key, en, nl, unit, formula in [
    (
        "goals",
        "Goals",
        "Doelpunten",
        "count",
        "Non-penalty Shot with outcome Goal; own goals excluded",
    ),
    (
        "npxg_per90",
        "Non-penalty xG",
        "xG zonder penalty's",
        "per90",
        "90 * sum(provider xG of non-penalty shots) / reliable minutes",
    ),
    (
        "xg_per_shot",
        "xG per shot",
        "xG per schot",
        "xG / shot",
        "Non-penalty xG / non-penalty shots; no shots -> null",
    ),
    (
        "xa_per90",
        "Linked expected assists",
        "Gekoppelde verwachte assists",
        "per90",
        "90 * sum(non-penalty shot xG linked reciprocally to assist pass) / reliable minutes; includes set pieces",
    ),
    (
        "pass_completion",
        "Open-play pass completion",
        "Passnauwkeurigheid in open spel",
        "fraction",
        "Completed open-play passes / attempted open-play passes; no passes -> null",
    ),
    (
        "pressures_per100_opponent",
        "Pressures per 100 opponent possessions",
        "Drukacties per 100 balbezitreeksen tegenstander",
        "per100",
        "100 * Pressure / distinct opponent (match, period, possession) sequences with an event during participation",
    ),
    (
        "interceptions_per100_opponent",
        "Interceptions per 100 opponent possessions",
        "Onderscheppingen per 100 balbezitreeksen tegenstander",
        "per100",
        "100 * Interception / distinct opponent possession sequences during participation",
    ),
    (
        "progressive_passes_per100_team",
        "Progressive passes per 100 team possessions",
        "Progressieve passes per 100 eigen balbezitreeksen",
        "per100",
        "100 * progressive Pass / distinct own-team possession sequences during participation",
    ),
    (
        "team_pass_share",
        "Share of team passes while playing",
        "Aandeel teampasses tijdens speeltijd",
        "fraction",
        "Player open-play attempts / team open-play attempts during player participation",
    ),
]:
    REGISTRY.append(
        FeatureDefinition(
            id=key,
            label_en=en,
            label_nl=nl,
            family="context" if "100" in key or key == "team_pass_share" else "output",
            unit=unit,
            formula=formula,
            note_en="Display or research context only; excluded from the default style distance.",
            note_nl="Alleen voor weergave of contextonderzoek; buiten de standaard stijlafstand.",
            core=False,
            intended_use="display and context research",
        )
    )

CORE = [f.id for f in REGISTRY if f.core]
FAMILIES = {f.id: f.family for f in REGISTRY if f.core}
BY_ID = {f.id: f for f in REGISTRY}

# Provider field identifiers remain technical; product explanations are authored in both languages.
DUTCH_DEFINITIONS = {
    "shots_per90": "Schoten zonder penalty's, per 90 betrouwbare minuten; geen strafschoppenserie.",
    "box_shots_per90": "Schoten zonder penalty's vanuit het strafschopgebied, per 90 betrouwbare minuten.",
    "shot_assists_per90": "Passes met een expliciete wederzijdse koppeling naar een volgend schot zonder penalty, per 90; inclusief spelhervattingen.",
    "box_passes_per90": "Aangekomen passes in open spel van buiten naar binnen het strafschopgebied, per 90.",
    "crosses_per90": "Aangekomen voorzetten in open spel volgens de bronmarkering, per 90.",
    "passes_per90": "Alle passpogingen in open spel, per 90; zonder corners, vrije trappen, inworpen, aftrappen en doeltrappen.",
    "progressive_passes_per90": "Aangekomen passes in open spel die de afstand tot het midden van het doel met minstens 10 meter én 25% verkleinen, per 90.",
    "final_third_passes_per90": "Aangekomen passes in open spel van vóór naar voorbij de grens van het laatste derde (70 meter), per 90.",
    "long_passes_per90": "Passpogingen in open spel met minstens 30 meter rechte verplaatsing op het referentieveld, per 90.",
    "carries_per90": "Baldribbels zoals geregistreerd door de databron, per 90. Er worden geen acties bijgemaakt.",
    "progressive_carries_per90": "Baldribbels die de afstand tot het midden van het doel met minstens 10 meter én 25% verkleinen, per 90.",
    "carry_distance_per90": "Som van rechte verplaatsingen tijdens baldribbels in referentiemeters, per 90; geen fysieke trackingafstand.",
    "box_carries_per90": "Baldribbels van buiten naar binnen het strafschopgebied, per 90.",
    "pressures_per90": "Drukacties geregistreerd door de databron, per 90; geen afgeleide druk zonder bal.",
    "counterpressures_per90": "Drukacties met de bronmarkering voor tegendruk, per 90.",
    "tackles_per90": "Duels met type tackle, ongeacht uitkomst, per 90.",
    "interceptions_per90": "Geregistreerde onderscheppingsacties, ongeacht uitkomst, per 90.",
    "recoveries_per90": "Geregistreerde balheroveringsacties, ongeacht uitkomst, per 90.",
    "goals": "Doelpunten uit schoten zonder penalty's; eigen doelpunten en strafschoppenseries uitgesloten.",
    "npxg_per90": "Som van bron-xG van schoten zonder penalty's, per 90 betrouwbare minuten.",
    "xg_per_shot": "Bron-xG gedeeld door schoten zonder penalty's. Geen schoten betekent niet beschikbaar.",
    "xa_per90": "Bron-xG van expliciet gekoppelde schoten zonder penalty's, per 90; inclusief assists uit spelhervattingen.",
    "pass_completion": "Aangekomen passes gedeeld door pogingen in open spel. Geen pogingen betekent niet beschikbaar.",
    "pressures_per100_opponent": "Drukacties per 100 unieke balbezitreeksen van de tegenstander met een event tijdens de speeltijd van de speler.",
    "interceptions_per100_opponent": "Onderscheppingen per 100 unieke balbezitreeksen van de tegenstander tijdens de speeltijd.",
    "progressive_passes_per100_team": "Progressieve passes per 100 unieke eigen balbezitreeksen tijdens de speeltijd.",
    "team_pass_share": "Eigen passpogingen in open spel gedeeld door die van het team tijdens de speeltijd.",
}
for feature in REGISTRY:
    feature.note_en = feature.formula + ". " + feature.note_en
    feature.note_nl = DUTCH_DEFINITIONS[feature.id] + " " + feature.note_nl
BY_ID["goals"].label_en = "Non-penalty goals"
BY_ID["goals"].label_nl = "Doelpunten zonder penalty's"
