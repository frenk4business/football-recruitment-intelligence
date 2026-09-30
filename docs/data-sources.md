# Source decision matrix

Audited 30 September 2026 against official repositories, provider documents and original publications. The field-by-field audit is [config/data_sources.yaml](../config/data_sources.yaml). Unknown sizes/coverage are explicitly unmeasured. An accessible download is not a redistribution grant.

| Source | Evidence and format | Licence / publishing boundary | Decision |
|---|---|---|---|
| [StatsBomb / Hudl](https://github.com/hudl/open-data) | Nested events + lineups JSON | [Public Data User Agreement](https://github.com/hudl/open-data/blob/master/LICENSE.pdf), non-commercial research; no raw redistribution; name + logo for published analysis | CORE, one full event match |
| [SkillCorner](https://github.com/SkillCorner/opendata) | Metadata JSON + tracking JSONL; optional CSV and body pose | [MIT](https://github.com/SkillCorner/opendata/blob/master/LICENSE); retain notice | CORE, bounded tracking window |
| [Metrica Sports](https://github.com/metrica-sports/sample-data) | Synchronized CSV / FIFA EPTS; three anonymized games | README requests attribution; broader redistribution grant not verified | SECONDARY, defer |
| [IDSSE / DFL](https://github.com/spoho-datascience/idsse-data) | Seven synchronized event/tracking matches, DFL XML | CC BY 4.0, credit DFL and Bassek et al. | SECONDARY, next tracking candidate |
| [Wyscout / Figshare](https://figshare.com/collections/Soccer_match_event_dataset/4415000) | 2017/18 five leagues; 2018 World Cup; Euro 2016; JSON | CC BY 4.0; cite [data descriptor](https://www.nature.com/articles/s41597-019-0247-7), collection and requested paper | SECONDARY, event cohort expansion |
| [OpenFootball](https://github.com/openfootball/football.json) | Season results and schedules, JSON / text | Public domain dedication in repository | SECONDARY, metadata only |
| [SoccerNet](https://www.soccer-net.org/data) | Video benchmarks, task annotations / tracklets | [Research/non-commercial](https://www.soccer-net.org/faq), video NDA and per-subset terms | RESEARCH EXTENSION |
| [football-data.co.uk](https://football-data.co.uk/data.php) | Match results/statistics/odds CSV | License/redistribution terms require further verification | REJECT for Phase 1 |
| [Last-Row](https://github.com/Friends-of-Tracking-Data-FoTD/Last-Row) | Short manually tracked goal sequences | License/redistribution terms require further verification | RESEARCH EXTENSION |

The chosen pair proves nested event and frame/object ingestion without pretending the matches or identities overlap. SkillCorner's inspected tree has 20 match directories although its README says 10; the preview reports only the one selected match. No commercial APIs, scraping, transfer-value estimates or paid datasets are used.

## Tool assessment

| Tool | Assessment |
|---|---|
| [Kloppy](https://kloppy.pysport.org/) | Good standardization reference and future provider expansion path. Direct small adapters preserve original payloads and make coordinate assumptions inspectable; no runtime dependency yet. |
| [socceraction](https://socceraction.readthedocs.io/en/latest/) | Relevant SPADL/action-value pipeline for later research. Deferred; no VAEP/xT training in Phase 1. |
| [mplsoccer](https://mplsoccer.readthedocs.io/) | Useful for offline publication plots. Browser pitch uses simple accessible SVG, so no plotting dependency needed now. |
| [Polars](https://docs.pola.rs/) | Typed transformations, aggregations and Parquet writes. In-memory execution is measured and adequate for this bounded sample. |
| [DuckDB](https://duckdb.org/docs/stable/data/parquet/overview) | SQL over Parquet, local analytical marts and projection/filter pushdown without a server. |
| [PyArrow](https://arrow.apache.org/docs/python/parquet.html) | Arrow interchange for DuckDB and explicit Parquet interoperability tests. |
| Pydantic / Pandera | Pydantic supplies row and public API contracts. Additional frame invariants use Polars; Pandera would duplicate the current small contract layer. |

Read source terms again before expanding the use case or introducing commercial use. Repository code is MIT; data rights are separate.
