# Attribution and data rights

Project code: © 2026 Frenk Kester, MIT. Third-party data and trademarks are excluded from that licence.

**StatsBomb Open Data** — [official repository](https://github.com/hudl/open-data), [Public Data User Agreement](https://github.com/hudl/open-data/blob/master/LICENSE.pdf). This is independent non-commercial football research. StatsBomb does not endorse these results. Published analysis displays the StatsBomb name and official logo. The agreement restricts redistribution of underlying data and commercial exploitation. Raw JSON, canonical event records and Parquet remain local and ignored by Git. Published JSON contains derived player totals, count summaries and coarse spatial bins, not event feeds. Users retrieve the original inputs directly from StatsBomb and remain subject to its terms, including its request to register interest.

The StatsBomb logo is retrieved from the provider's own `img/SB - Icon Lockup - Colour positive.png`, pinned to the same revision as the data. Its use is solely attribution; it is not project branding or a sponsorship claim.

**SkillCorner Open Data / PySport** — [official repository](https://github.com/SkillCorner/opendata). Copyright (c) 2020 Skillcorner. MIT permission and warranty notice are retained in [the bundled licence](apps/web/public/skillcorner-license.txt), also served by the website. The sample is transformed into reference-pitch coordinates and downsampled from 10 Hz to 1 Hz. Extrapolated positions remain identified.

Only synthetic, explicitly labelled automated-test fixtures are committed as provider-shaped raw records. They never appear in production output. No source videos, commercial feed data or copied third-party code are included.

**Wyscout public soccer match event dataset (Pappalardo et al., 2019)** — [official Figshare collection](https://figshare.com/collections/Soccer_match_event_dataset/4415000), [data descriptor](https://doi.org/10.1038/s41597-019-0247-7), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Phase 3 uses player/team/competition/match metadata only for a separate derived identity and transition-feasibility audit. IDs are isolated from StatsBomb; no Wyscout event metrics enter the model. Published audit counts are transformations of the original metadata; source files remain local. Exact file IDs and checksums are in `config/phase3.sources.json`.

Phase 3 StatsBomb outputs add derived environment summaries, action-rate predictions, interval summaries and aggregate research evaluation. Raw events/lineups and full posterior draws remain excluded. Source terms were rechecked against the pinned official licence; there is no claim that model outputs erase the underlying data-use restrictions.
