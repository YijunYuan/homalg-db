import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import {
  useEvolution,
  useGlobalGraph,
  useSearch,
  useTaxonomy,
} from "../../data/loaders";
import {
  ErrorView,
  Loading,
  PageTitle,
  Section,
  StatusBadge,
  nodeUrl,
} from "../../components/ui";
import { Markdown } from "../../components/markdown/Markdown";
import { t } from "../../i18n/t";
import { DefinitionComparison } from "./DefinitionComparison";
import { ConceptArcView } from "../timeline/GlobalViews";
function ConceptDetail({ id }: { id: string }) {
  const taxonomy = useTaxonomy(),
    results = useSearch({ concepts: id, sort: "year" }),
    evolution = useEvolution(id),
    graph = useGlobalGraph(),
    [unreviewed, setUnreviewed] = useState(false),
    navigate = useNavigate();
  const concept = taxonomy.data?.concepts.find((item) => item.id === id);
  useEffect(() => {
    if (concept?.merged_into)
      navigate(`/concepts/${concept.merged_into}`, { replace: true });
  }, [concept, navigate]);
  if (!concept)
    return taxonomy.isLoading ? (
      <Loading />
    ) : (
      <ErrorView error={new Error("Unknown concept")} />
    );
  const lane = graph.data?.concepts.find((item) => item.id === id),
    relatedIds = new Set(lane?.arcs.flatMap((arc) => [arc.source, arc.target])),
    relations = taxonomy.data?.relations.filter(
      (relation) =>
        (relation.review.status === "accepted" ||
          (unreviewed && relation.review.status === "unreviewed")) &&
        (relatedIds.has(relation.source) ||
          relatedIds.has(relation.target) ||
          results.data?.records.some(
            (node) =>
              node.id === relation.source || node.id === relation.target,
          )),
    );
  return (
    <>
      <PageTitle title={concept.name} description={concept.description} />
      {concept.aliases && concept.aliases.length > 0 && (
        <p className="muted">
          {t("taxonomy.aliases")}
          {": "}
          {concept.aliases.join(", ")}
        </p>
      )}
      {concept.parents && concept.parents.length > 0 && (
        <div className="chips">
          <span>{t("taxonomy.parents")}</span>
          {concept.parents.map((parent) => (
            <Link key={parent} to={`/concepts/${parent}`}>
              {parent}
            </Link>
          ))}
        </div>
      )}
      <Section title={t("taxonomy.timeline")}>
        {lane && <ConceptArcView concept={lane} unreviewed={unreviewed} />}
        <table>
          <thead>
            <tr>
              <th>{t("timeline.year")}</th>
              <th>{t("timeline.document")}</th>
              <th>{t("timeline.defines")}</th>
              <th>{t("timeline.uses")}</th>
            </tr>
          </thead>
          <tbody>
            {lane?.lanes.map((entry) => (
              <tr key={entry.doc}>
                <td>{entry.year}</td>
                <td>
                  <Link to={`/doc/${entry.doc}`}>{entry.doc}</Link>
                </td>
                <td>
                  {entry.defines.map((node) => (
                    <Link key={node.id} to={nodeUrl(node.id)}>
                      {node.label}
                    </Link>
                  ))}
                </td>
                <td>{entry.uses_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
      <Section title={t("taxonomy.compareDefinitions")}>
        <div className="definition-comparisons">
          {lane?.lanes
            .flatMap((entry) => entry.defines)
            .map((node) => (
              <DefinitionComparison key={node.id} id={node.id} />
            ))}
        </div>
      </Section>
      <Section title={t("taxonomy.bridges")}>
        <ul>
          {relations
            ?.filter((relation) => relation.bridge)
            .map((relation) => (
              <li key={relation.id}>
                <Link to={nodeUrl(relation.bridge!)}>{relation.bridge}</Link> ·{" "}
                {t(`enum.RelationType.${relation.type}`)}
              </li>
            ))}
        </ul>
      </Section>
      <Section title={t("taxonomy.nodes", { kind: t("taxonomy.concept") })}>
        {results.isLoading && <Loading />}
        {results.error && <ErrorView error={results.error} />}
        <ul className="audit-list">
          {results.data?.records.map((node) => (
            <li key={node.id}>
              <Link to={nodeUrl(node.id)}>
                {node.label}
                <small>
                  {node.doc_title}
                  {" · "}
                  {node.year}
                </small>
              </Link>
              <StatusBadge node={node} />
            </li>
          ))}
        </ul>
        <Link to={`/search?concepts=${id}&sort=year`}>{t("nav.search")}</Link>
      </Section>
      <Section title={t("node.relations")}>
        <label className="check-label">
          <input
            type="checkbox"
            checked={unreviewed}
            onChange={(event) => setUnreviewed(event.target.checked)}
          />
          {t("taxonomy.unreviewedRelations")}
        </label>
        <ul className="relation-list">
          {relations?.map((relation) => (
            <li key={relation.id}>
              <Link to={nodeUrl(relation.source)}>{relation.source}</Link>
              <span>{t(`enum.RelationType.${relation.type}`)}</span>
              <Link to={nodeUrl(relation.target)}>{relation.target}</Link>
              <span className="badge">
                {t(`enum.Review.${relation.review.status}`)}
              </span>
              {relation.review.kind === "agent" && (
                <span className="badge">
                  {t("taxonomy.agentReview", { by: relation.review.by || "" })}
                </span>
              )}
              {relation.bridge && (
                <Link to={nodeUrl(relation.bridge)}>
                  {t("taxonomy.bridges")}
                </Link>
              )}
            </li>
          ))}
        </ul>
      </Section>
      <Section title={t("taxonomy.summary")}>
        {evolution.error && <ErrorView error={evolution.error} />}{" "}
        {!evolution.data?.summaries.length && <p>{t("taxonomy.noSummary")}</p>}
        {evolution.data?.summaries
          .slice()
          .reverse()
          .map((summary) => (
            <article className="evolution-summary" key={summary.version}>
              <div className="badges">
                <span className="badge">
                  {t(`enum.Review.${summary.review.status}`)}
                </span>
                <span className="badge">
                  {t("taxonomy.version", { version: summary.version })}
                </span>
                {summary.review.kind === "agent" && (
                  <span className="badge">
                    {t("taxonomy.agentReview", { by: summary.review.by || "" })}
                  </span>
                )}
                {summary.stale && (
                  <span className="badge warning">
                    {t("taxonomy.stale", { date: summary.provenance.on })}
                  </span>
                )}
              </div>
              <Markdown text={summary.narrative_md} />
              <ol>
                {summary.stages.map((stage, i) => (
                  <li key={i}>
                    <strong>{stage.period}</strong>
                    <p>{stage.change}</p>
                    <div className="chips">
                      {stage.nodes.map((node) => (
                        <Link key={node} to={nodeUrl(node)}>
                          {node}
                        </Link>
                      ))}
                    </div>
                  </li>
                ))}
              </ol>
              {summary.open_questions && summary.open_questions.length > 0 && (
                <>
                  <h3>{t("taxonomy.openQuestions")}</h3>
                  <ul>
                    {summary.open_questions.map((question, i) => (
                      <li key={i}>{question}</li>
                    ))}
                  </ul>
                </>
              )}
              {summary.proposed_aliases &&
                summary.proposed_aliases.length > 0 && (
                  <p>
                    {t("taxonomy.aliasSuggestions")}
                    {": "}
                    {summary.proposed_aliases.join(", ")}
                  </p>
                )}
              <p className="muted">
                {t("node.provenance")}
                {": "}
                {summary.provenance.model ||
                  summary.provenance.handle ||
                  summary.provenance.by}
                {" · "}
                {summary.provenance.on}
                {summary.provenance.provider && (
                  <> · {summary.provenance.provider}</>
                )}
                {summary.provenance.prompt_version && (
                  <>
                    {" "}
                    ·{" "}
                    {t("taxonomy.promptVersion", {
                      version: summary.provenance.prompt_version,
                    })}
                  </>
                )}
                {summary.provenance.usage && (
                  <>
                    {" "}
                    ·{" "}
                    {t("taxonomy.tokenUsage", {
                      input: summary.provenance.usage.input_tokens,
                      output: summary.provenance.usage.output_tokens,
                    })}
                  </>
                )}
                {summary.provenance.cost_usd !== undefined && (
                  <>
                    {" "}
                    ·{" "}
                    {t("taxonomy.cost", {
                      cost: summary.provenance.cost_usd.toFixed(4),
                    })}
                  </>
                )}
              </p>
            </article>
          ))}
      </Section>
    </>
  );
}
export default function Concepts() {
  const { id } = useParams(),
    query = useTaxonomy();
  if (query.error) return <ErrorView error={query.error} />;
  if (!query.data) return <Loading />;
  return (
    <div className="page">
      {id ? (
        <ConceptDetail id={id} />
      ) : (
        <>
          <PageTitle
            title={t("taxonomy.conceptsTitle")}
            description={t("taxonomy.conceptsDescription")}
          />
          <div className="document-grid">
            {query.data.concepts
              .filter((concept) => !concept.merged_into)
              .map((concept) => (
                <article className="document-card" key={concept.id}>
                  <h2>
                    <Link to={`/concepts/${concept.id}`}>{concept.name}</Link>
                  </h2>
                  <p>{concept.description}</p>
                  <div className="chips">
                    {concept.related_tags?.map((tag) => (
                      <Link key={tag} to={`/tags/${tag}`}>
                        {tag}
                      </Link>
                    ))}
                  </div>
                </article>
              ))}
          </div>
        </>
      )}
    </div>
  );
}
