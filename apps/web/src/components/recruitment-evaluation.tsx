import type { Locale } from "@/lib/content";
import type {
  RecruitmentEvaluation as Evaluation,
  RecruitmentEvaluationRow,
} from "@/lib/contracts";
import { recruitmentCopy, recruitmentMethods } from "@/lib/recruitment-copy";
const report =
  "https://github.com/frenk4business/football-recruitment-intelligence/blob/main/docs/recruitment-fit-evaluation.md";
export function RecruitmentEvaluation({
  locale,
  evaluation,
}: {
  locale: Locale;
  evaluation: Evaluation;
}) {
  const c = recruitmentCopy[locale],
    language = locale === "en" ? 0 : 1;
  const format = (n: number | null) =>
    n === null
      ? "—"
      : n.toLocaleString(locale, {
          minimumFractionDigits: 3,
          maximumFractionDigits: 3,
        });
  function table(rows: RecruitmentEvaluationRow[], caption: string) {
    const baseline = rows[0];
    return (
      <div
        className="table-wrap"
        tabIndex={0}
        role="region"
        aria-label={caption}
      >
        <table>
          <caption>{caption}</caption>
          <thead>
            <tr>
              <th>{c.method}</th>
              <th>{c.queries}</th>
              <th>{c.recall5}</th>
              <th>{c.recall10}</th>
              <th>MRR</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.method}>
                <th scope="row">
                  {recruitmentMethods[r.method]?.[language] ?? r.method}
                  {r.method === evaluation.selected_method ? " *" : ""}
                </th>
                <td>{r.queries}</td>
                <td>{format(r.recall5)}</td>
                <td>{format(r.recall10)}</td>
                <td>{format(r.mrr)}</td>
              </tr>
            ))}
            {baseline && (
              <tr>
                <th scope="row">{c.random}</th>
                <td>{baseline.queries}</td>
                <td>{format(baseline.random_recall5)}</td>
                <td>{format(baseline.random_recall10)}</td>
                <td>{format(baseline.random_mrr)}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  }
  return (
    <section id="recruitment" className="recruitment-evaluation">
      <span className="eyebrow">
        RECRUITMENT-FIT-V1 · REQUIREMENTS-V1 · CLUB-CONTEXT-V1
      </span>
      <h2>{c.methods}</h2>
      <p>{c.methodsIntro}</p>
      <div className="method-list">
        {c.methodDefinitions.map(([title, body], i) => (
          <section key={title}>
            <span className="section-number">{i + 1}</span>
            <div>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          </section>
        ))}
      </div>
      <h3>{c.evaluationTitle}</h3>
      <p>{c.evaluationNote}</p>
      {table(
        evaluation.rows.filter(
          (r) => r.stage === "final" && r.task === "temporal",
        ),
        `${c.final} · ${c.temporal}`,
      )}
      <p className="note">
        {locale === "en"
          ? "* Selected on development queries before the final query evaluation. MRR is mean reciprocal rank: higher means the designated peer appears earlier. This peer is a representation-derived label, not an expert judgement."
          : "* Geselecteerd op ontwikkelvragen vóór de finale evaluatie. MRR is de gemiddelde reciproke rang: hoger betekent dat de aangewezen buur eerder verschijnt. Deze buur komt uit het profielmodel, niet uit een expertoordeel."}
      </p>
      <details>
        <summary>{c.allMethods}</summary>
        {(["development", "final"] as const).map((stage) => (
          <div key={stage}>
            {(["temporal", "roster", "context_ablation"] as const)
              .filter((task) => stage !== "final" || task !== "temporal")
              .map((task) => (
                <div key={task}>
                  {table(
                    evaluation.rows.filter(
                      (r) => r.stage === stage && r.task === task,
                    ),
                    `${c[stage]} · ${task === "temporal" ? c.temporal : task === "roster" ? c.rosterTest : c.ablation}`,
                  )}
                </div>
              ))}
          </div>
        ))}
      </details>
      <p className="recruitment-warning">{c.robustSummary}</p>
      <p>
        <a href={report}>{c.researchLink} ↗</a>
      </p>
    </section>
  );
}
