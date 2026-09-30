# ADR 007 — explicit weighted percentile mismatch

Status: selected on development queries only, before opening the registered final query partition. Evidence/schema checkpoint `b2a6d57`; experiment checkpoint `2aa494e`; scoring implementation `9a96a5a`.

Use `recruitment-fit-v1`: root weighted mean squared directional percentile-point mismatch. Exact preferences use absolute deviation; minimum/maximum only penalise the unsatisfied side; neutral features are ignored. Feature and family importance are explicit 1/2/3 values, defaulting to one. Consequently equally selected requirements receive equal default weight. Report distance (lower is closer), without a 0–100 suitability rating. Hard constraints precede ranking. Evidence is separate.

On 56 development temporal known-peer queries, weighted RMS MRR is **0.3912**, above random **0.2408**. Its 87 full-profile replacement scenarios have mean weight-perturbation top-10 Jaccard **0.9453**, above the registered .65 gate. Family-balanced RMS also passes (MRR .3881; Jaccard .9599), and better agrees with existing family-balanced DNA neighbours (.7663 versus .7212). Weighted RMS is retained under the preregistered transparency/equal-explicit-requirements preference, not because a .003 metric difference proves superiority. The unchanged raw-rate Player DNA baseline has higher development peer MRR (.4020).

Threshold satisfaction and hybrid orderings are reported but fail the desired continuous-severity semantics; binary threshold bins create ties and discontinuities. Their development peer MRRs are .3364 and .3512. No model is trained without recruitment labels.

The context ablation has mixed evidence. Among only 12 eligible temporal development queries, full context raises MRR from .4119 to .5135, while Recall@5 and @10 are unchanged. In 44 roster holdouts, full context raises requirement-only MRR from .2081 to .2467, still below the .2643 raw-DNA roster baseline. These observations do not justify hidden criteria or establish recruitment success. Public club context stays descriptive; an analyst can explicitly adopt a characteristic or roster reference as a requirement, with its source visible.

The final West Ham / Manchester City / Leicester / Brighton query partition is not yet evaluated. Freeze this selection in `artifacts/phase4/method_selection.json` before doing so. Preserve every registered method and ablation regardless of final results. Changes to public method semantics require a new version and registered experiment.
