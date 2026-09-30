# Football Recruitment Intelligence

Open voetbaldata → waargenomen spelers-DNA → historische prestatievertaling, met zichtbare onzekerheid. Onafhankelijk, niet-commercieel onderzoek door Frenk Kester.

[Live prestatievertaling](https://football-recruitment-intelligence.onrender.com/nl/translation/) · [English](README.md) · [Spelers-DNA](https://football-recruitment-intelligence.onrender.com/nl/player-dna/) · [Evaluatie](docs/league-translation-evaluation.md) · [Modelkaart](docs/model-card-phase3.md)

## Fase 3: wat de gegevens onderbouwen

De volledige officiële StatsBomb-catalogus is gecontroleerd: **80 competitie-seizoenen, 3.961 wedstrijdselecties en 11.794 provideridentiteiten**. Een afzonderlijke Wyscout-audit loste het tekort aan longitudinale transferwaarnemingen niet op. Algemene vertaling tussen competities is **NO-GO**. Het uitgewerkte alternatief is een **voorwaardelijk historisch onderzoek naar seizoen- en teamcontext binnen de FA Women’s Super League**.

Vier WSL-seizoenen leveren 457 wedstrijden, 660 selectiespelers en 1.225 omgevingsperioden. Betrouwbare minuten, consistente identiteit, opeenvolgende observaties en rol-/contextdekking leiden tot **53 trainings-, 12 validatie- en 76 latere testepisodes**, met aan beide kanten minimaal 600 betrouwbare minuten. Slechts **vier testepisodes wisselen van team**. Het bronscenario betreft 2019/20 en het doelscenario 2020/21; dit voorspelt niet het huidige seizoen.

Drie basismodellen zijn vergeleken met vier hiërarchische Bayesiaanse negatief-binomiale telmodellen. Rol- en teameffecten worden gedeeltelijk gezamenlijk geschat; speelminuten bepalen de blootstelling. Teamcontext gebruikt uitsluitend eerdere informatie. Eén competitie rechtvaardigt geen competitiecoëfficiënt. Priors en onderzoeksopzet zijn vastgelegd vóór het schatten; de modelkeuze stond vast vóór de latere test.

| Kenmerk | Gekozen standaard | Test-MAE /90 | Dekking 80%-band | Gemiddelde breedte /90 |
|---|---|---:|---:|---:|
| Schoten zonder strafschoppen | Ridge-regressie | 0,397 | 73,7% | 0,969 |
| Progressieve passes | Ridge-regressie | 0,920 | 71,1% | 1,889 |
| Progressieve dribbels | Ongewijzigde bron | 0,500 | 80,3% | 1,552 |
| Drukacties | Ongewijzigde bron | 2,894 | 76,3% | 8,214 |

**Geen Bayesiaans model voldeed aan alle validatieregels voor de standaardmethode.** Het blijft beschikbaar als onderzoeksvergelijking. De primaire modellen hebben nul divergenties en een maximale R-hat van 1,0055; goede convergentie garandeerde geen betere voorspellingen. De banden voor schoten en passes onderschatten onzekerheid. De contexteffecten rechtvaardigen geen ranglijst van clubs of competities.

De tweetalige interface toont bron- en doelomgeving, rolaanname, waargenomen en verwachte waarden, een 80%-voorspellingsband, aantallen en waarschuwingen bij weinig directe onderbouwing. Niet-ondersteunde perioden, rollen, lage speeltijd, ontbrekende context en extrapolatie krijgen geen verzonnen schatting. Het waargenomen spelers-DNA blijft apart: WSL 2023/24, 132 wedstrijden, 336 selectiespelers, 138 vergelijkbare profielen bij 900 minuten en 18 stijlkenmerken.

## Lokaal starten en reproduceren

Vereisten: Python 3.12–3.13, [uv](https://docs.astral.sh/uv/), Node **24.19.0**, npm en Make. Gebruik de vastgelegde lockfiles.

```sh
git clone https://github.com/frenk4business/football-recruitment-intelligence.git
cd football-recruitment-intelligence
make setup
make test
make build
cd apps/web && npx playwright install chromium && cd ../..
make smoke
make dev
```

De webbuild gebruikt meegeleverde onderzoeksaggregaten, zonder bronbestanden te downloaden of modellen te schatten. Engels `/translation/`, Nederlands `/nl/translation/`. `make api` start de optionele lokale FastAPI; `/docs` beschrijft de contracten.

```sh
make data-bootstrap       # kleine event-/trackingsteekproef uit Fase 1
make phase2-build         # vastgezet WSL-seizoen 2023/24 en spelersgelijkenis
make translation-audit    # catalogus en aparte Wyscout-metadata-audit
make phase3-build         # WSL-data, vaste modelkeuze, evaluatie, publicatie en rapporten
uv run python scripts/phase3_reproduce.py  # offline herbouw + vier nieuwe modelschattingen
make contracts            # Pydantic → TypeScript / JSON Schema / OpenAPI
```

De eerste onderzoeksbuild downloadt begrensde, vastgezette bronbestanden. Herhaalde builds gebruiken de gecontroleerde cache. Volledige modelschatting draait niet in CI of Render. `make translation-validate` is de afzonderlijke historische modelkeuzestap; de vastgelegde v1-keuze blijft ongewijzigd vóór de test. [Architectuur](docs/architecture.md) · [API](docs/api.md) · [Herkomst](docs/data-provenance.md).

## Onderzoek, rechten en beperkingen

[Bewijsaudit](docs/phase-3-transfer-evidence.md) · [afbakening](docs/adr/006-phase3-evidence-scope.md) · [vastgelegde opzet](docs/phase-3-experiment-plan.md) · [prior-predictieve controle](docs/phase-3-prior-predictive.md) · [alle modellen en gevoeligheden](docs/league-translation-evaluation.md).

Selectie op speelminuten ondervertegenwoordigt spelers die niet spelen. Historische wedstrijden zijn niet volledig beschikbaar, doelrollen zijn aannames en team, vaardigheid en mogelijkheden zijn verstrengeld. Er is geen causale claim over competitiesterkte, marktwaardemodel of clubadvies. De standaardbanden beschrijven eerdere seizoensvensters van minimaal 600 minuten; alleen het Bayesiaanse onderzoeksmodel simuleert specifiek 900 minuten.

Ruwe StatsBomb-events, selecties, canonieke Parquet en volledige posteriorsteekproeven blijven lokaal. Alleen afgeleide onderzoeksaggregaten worden gepubliceerd, met bronvermelding en StatsBomb-logo. Wyscout-metadata krijgt aparte CC BY 4.0-vermelding. De ene minuut SkillCorner-tracking blijft een demonstratie van dataverwerking, geen fysiek spelersprofiel. [Bronvermelding en rechten](ATTRIBUTION.md).

## Hosting en vervolg

Eén bestaande statische Render-site serveert de aggregaten. **Er is geen aanvullende betaalde infrastructuur toegevoegd boven op het bestaande Render-workspace-/Starter-abonnement.** Er is geen backend, worker, database of schijf toegevoegd. Productie hoort `main` te volgen; de feitelijke verificatie staat in [hosting](docs/deployment.md) en [Fase 3 QA](docs/phase-3-qa.md). Voltooide fase-PR’s worden na geslaagde controles samengevoegd.

1. Datafundament — voltooid.
2. Spelers-DNA en gelijkenis — voltooid.
3. Competitievertaling en Bayesiaanse prestatieoverdracht — voltooid/huidig, binnen de smallere WSL-afbakening.
4. Recruitmentondersteuning en clubpassendheid — gepland.
5. Productieversteviging en portfolio-integratie — gepland.

Fase 3 voegt hiërarchische inferentie, prior-/posteriorcontroles, kalibratie, temporele evaluatie, negatieve resultaten en begrijpelijke voorspellingsonzekerheid toe. [Overdracht naar Fase 4](docs/phase-4-handoff.md).

Software © 2026 Frenk Kester, MIT. Brondata en logo’s behouden hun eigen rechten.
