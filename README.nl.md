# Football Recruitment Intelligence

**Fase 2 — Spelers-DNA en gelijkenis** is geïmplementeerd op `phase/02-player-dna`, bovenop de nog niet samengevoegde Fase 1-branch. WSL 2023/24: 132 wedstrijden, 336 selectiespelers, 138 vergelijkbare profielen bij 900 betrouwbare minuten. Achttien stijlkenmerken, schaling per rol, gelijk gewogen kenmerkfamilies, top 10-vergelijkingen, uitlegbare verschillen en bootstrapstabiliteit. Engels `/player-dna/`, Nederlands `/nl/player-dna/`.

Gebruik `make setup`, `make test`, `make phase2-build`, `make build`. De onderzoeksbuild downloadt het vastgezette seizoen één keer en gebruikt daarna de gecontroleerde cache. De website gebruikt uitsluitend toegestane onderzoeksaggregaten. Zie [evaluatie](docs/player-similarity-evaluation.md), [kenmerken](docs/player-features.md), [methode](docs/player-similarity.md) en [overdracht naar Fase 3](docs/phase-3-handoff.md). De vaste infrastructuurkosten blijven €0 per maand binnen de bestaande Render-limieten. Gelijkenis is geen kwaliteit, tactische passendheid of transfervoorspelling.

Hieronder volgt de oorspronkelijke documentatie van het Fase 1-datafundament.


Onderzoek met open voetbaldata, expliciete herkomst, canonieke event- en trackingcontracten en reproduceerbare analysetabellen.

[Live preview](https://football-recruitment-intelligence.onrender.com/) · [Phase 1 PR](https://github.com/frenk4business/football-recruitment-intelligence/pull/1) · [English](README.md) · [Nederlands](README.nl.md) · [Bronnenonderzoek](docs/data-sources.md) · [Architectuur](docs/architecture.md)

**Fase 1: datafundament.** De tweetalige dataverkenner gebruikt werkelijk ingelezen observaties. Spelersvergelijking, competitievertaling en recruitmentaanbevelingen zijn gepland en nog niet geïmplementeerd. Dit is onafhankelijk onderzoek; er worden geen bedrijfseigen methoden nagebouwd.

Onderzoeksvraag: **Hoe kan open voetbaldata bruikbare, uitlegbare recruitmentbeslissingen ondersteunen, met zichtbare onzekerheid?** Eerst moet de onderliggende informatie betrouwbaar te structureren en te onderzoeken zijn.

## Wat deze fase bevat

- StatsBomb-eventadapter en SkillCorner-trackingadapter, vaste bronversies, gecontroleerde caches en stabiele ID’s.
- Getypeerde tabellen, coördinatentransformaties, kwaliteitsrapportage, Parquet en DuckDB-tabellen op speler-wedstrijd-, speler-seizoen- en team-seizoenniveau.
- FastAPI-contracten, gegenereerde TypeScript-typen en een Next.js-product in Nederlands en Engels.
- Wedstrijdselectie, spelersfilters, gegroepeerde veldanalyse, trackingtijdlijn, datadekking en methodologie.
- Kleine offline testfixtures, GitHub Actions en configuratie voor een statische Render-preview. Geen betaalde data, model-API of clouddatabase.

Architectuur: **vaste bronbestanden → adapters en validatie → Parquet → DuckDB → getypeerde onderzoeksaggregaten → lokale API en statische website**. [Ontwerp en afwegingen](docs/architecture.md) · [Datamodel](docs/data-model.md) · [Architectuurbesluiten](docs/adr/001-duckdb-parquet.md).

## Werkelijk gebruikte data

| Databron | Observatie | Records | Afbakening |
|---|---|---|---|
| StatsBomb | Argentinië–Frankrijk, 18 december 2022, WK | 4.407 events; 50 selectiespelers | Inclusief verlenging en strafschoppenserie; publieke statistieken sluiten de serie uit |
| SkillCorner | Western United–Sydney FC, 27 april 2025, A-League 2024/25 | 60 frames; 1.380 objectposities; 36 selectiespelers | Eerste minuut op 1 Hz; selectie- en minutenmetadata betreffen de hele wedstrijd |

De bronnen beschrijven verschillende wedstrijden; identiteiten worden niet op naam gekoppeld. Selecties bevatten ongebruikte wisselspelers. Zes inconsistente StatsBomb-minutenintervallen en vijf ontbrekende SkillCorner-speeltijden blijven onbekend. Twee teruglopende tijdstempels en 29 events zonder speler-ID blijven zichtbaar. [Methoden en beperkingen](docs/methodology.md).

**De softwarelicentie geldt niet voor alle data.** StatsBomb beperkt verspreiding van onderliggende data en commercieel gebruik. Alleen afgeleide onderzoeksaggregaten en veldvakken worden gepubliceerd. De MIT-vermelding van SkillCorner blijft behouden. Bronvermelding, licentielinks en het StatsBomb-logo staan in de interface. Ruwe bestanden en Parquet blijven buiten Git. Lees [ATTRIBUTION.md](ATTRIBUTION.md) voor hergebruik.

## Lokaal starten

Vereisten: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node **24.19.0**, npm en Make. Gebruik de vastgelegde versies en lockfiles. De kern werkt zonder account of geheime sleutel; gebruik van brondata blijft onder de bronvoorwaarden vallen.

```sh
git clone --branch phase/01-data-foundation https://github.com/frenk4business/football-recruitment-intelligence.git
cd football-recruitment-intelligence
make setup
make test
make data-bootstrap
make dev
```

De Engelse versie staat op `http://localhost:3000/`, Nederlands op `/nl/`. Gepubliceerde aggregaten zijn meegeleverd, zodat webtests en de webbuild ook zonder ruwe downloads werken. `make api` start de optionele lokale API apart.

## Datapijplijn

```sh
make data-bootstrap    # kleine vaste downloads, validatie, Parquet, analysetabellen en aggregaten
make data-statsbomb    # alleen StatsBomb-invoer ophalen/cachen
make data-tracking     # alleen de afgebakende trackingselectie ophalen/cachen
make data-build        # offline opnieuw bouwen uit gecontroleerde caches
make data-validate     # opgeslagen canonieke Parquet valideren
make data-coverage     # werkelijke datadekking tonen
uv run fri data discover statsbomb
```

Tabellen staan in `data/processed/`. `football_intelligence.data.marts.connect(Path('data/processed'))` maakt DuckDB-views over de Parquet-bestanden. Oorspronkelijke ID’s, payloads, datums en kwaliteitsinformatie blijven lokaal beschikbaar. [Herkomst en reproduceerbaarheid](docs/data-provenance.md).

## Verificatie, website en API

```sh
make test
make build
cd apps/web && npx playwright install chromium && cd ../..
make smoke
make api              # localhost:8000; interactieve documentatie op /docs
make contracts        # TypeScript-, JSON- en OpenAPI-contracten opnieuw genereren
```

Tests controleren adapters, coördinaten, identiteiten, verwijzingen, ontbrekende waarden, SQL, reproduceerbare Parquet-uitvoer en API-validatie. Browsertests controleren beide talen, interactie, mobiel, toegankelijkheid en foutafhandeling. CI downloadt geen grote voetbalbestanden. Synthetische testfixtures verschijnen nooit als productiedata. [API-contract](docs/api.md).

## Hosting en kosten

Render bouwt een statische website uit beoordeelde aggregaten. De API blijft lokaal; een slapende backend of gehoste database voegt hier weinig toe. Vaste terugkerende projectkosten: **€0 per maand**, binnen de gedeelde bandbreedte- en bouwminutenlimieten van de bestaande workspace. Overschrijding kan volgens de accountinstellingen worden gefactureerd. Er wordt geen betaalde dienst of tijdelijke proefdatabase ingericht. [Hostingdetails](docs/deployment.md).

## Vervolg en leeropbrengst

1. Datafundament — huidige fase
2. Spelers-DNA en gelijkenis — gepland
3. Competitievertaling en prestatieoverdracht — gepland
4. Recruitmentondersteuning — gepland
5. Productversteviging en portfolio-integratie — gepland

Dit project voegt vooral heterogene dataverwerking, canonieke identiteiten, herkomstregistratie, datacontracten, analytische SQL, bronbewuste UX en reproduceerbare tests toe aan het portfolio. [Portfoliocontext](docs/portfolio-context.md) · [Routekaart](docs/roadmap.md) · [Overdracht naar fase 2](docs/phase-2-handoff.md).

De steekproef onderbouwt geen spelerskwaliteit, competitiesterkte of transfersucces. Tracking op 1 Hz wordt niet gebruikt voor fysieke prestatieclaims. Een bredere vaste cohort, betrouwbare speelminuten en temporele dekking gaan vóór een vergelijkingsmodel. De lokale build ondersteunt één gelijktijdige schrijver. Werkelijke beperkingen staan in de architectuur- en brondocumenten.

Software © 2026 Frenk Kester, MIT. Brondata en logo’s behouden hun eigen rechten. Bronvermelding: StatsBomb, SkillCorner en PySport; zie [ATTRIBUTION.md](ATTRIBUTION.md).
