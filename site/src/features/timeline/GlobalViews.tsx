import { useState } from "react";
import { Link } from "react-router";
import { useTaxonomy } from "../../data/loaders";
import type { GlobalGraph } from "../../data/source";
import { nodeUrl } from "../../components/ui";
import { t } from "../../i18n/t";
type Concept = GlobalGraph["concepts"][number];
function scale(values: number[], width = 820) {
  const minimum = Math.min(...values, 0),
    maximum = Math.max(...values, minimum + 1);
  const actualMinimum = values.length ? Math.min(...values) : minimum;
  return (value: number) =>
    80 +
    ((value - actualMinimum) / Math.max(120, maximum - actualMinimum)) * width;
}
export function ConceptArcView({
  concept,
  unreviewed,
}: {
  concept: Concept;
  unreviewed: boolean;
}) {
  const points = concept.lanes.flatMap((lane) => lane.defines),
    x = scale([
      ...concept.lanes.map((lane) => lane.year * 120),
      ...points.map((point) => point.x),
    ]);
  const byId = new Map(points.map((point) => [point.id, point]));
  const locate = (id: string) => {
    const point = byId.get(id);
    const lane = concept.lanes.find((item) => item.doc === id.split(".")[0]);
    return {
      x: x(point?.x ?? (lane?.year || 0) * 120),
      y: 110 + (point ? point.y % 30 : 0),
    };
  };
  const arcs = concept.arcs.filter(
    (arc) =>
      arc.review_status === "accepted" ||
      (unreviewed && arc.review_status === "unreviewed"),
  );
  return (
    <svg
      className="evolution-lane-svg"
      viewBox="0 0 1000 210"
      role="group"
      aria-label={t("timeline.laneLabel", { concept: concept.id })}
    >
      <line x1="60" x2="940" y1="125" y2="125" className="timeline-axis" />
      {arcs.map((arc, i) => {
        const a = locate(arc.source),
          b = locate(arc.target);
        return (
          <path
            key={i}
            className={`relation-arc ${arc.review_status}`}
            data-review={arc.review_status}
            d={`M ${a.x} ${a.y} Q ${(a.x + b.x) / 2} ${15 - (i % 3) * 6} ${b.x} ${b.y}`}
            fill="none"
            strokeDasharray={
              arc.review_status === "unreviewed" ? "6 5" : undefined
            }
          >
            <title>
              {t("timeline.relationDescription", {
                source: arc.source,
                type: t(`enum.RelationType.${arc.type}`),
                target: arc.target,
              })}
            </title>
          </path>
        );
      })}
      {concept.lanes.map((lane) => (
        <g key={lane.doc}>
          <text x={x(lane.year * 120)} y="174" textAnchor="middle">
            {lane.year}
          </text>
          <text x={x(lane.year * 120)} y="194" textAnchor="middle">
            {lane.doc}
          </text>
          {!!lane.uses_count && (
            <Link
              to={`/search?doc=${lane.doc}&concepts=${concept.id}`}
              aria-label={t("timeline.usageLink", {
                doc: lane.doc,
                count: lane.uses_count,
              })}
            >
              <circle
                cx={x(lane.year * 120) + 22}
                cy="85"
                r="15"
                className="usage-bubble"
              />
              <text x={x(lane.year * 120) + 22} y="90" textAnchor="middle">
                {lane.uses_count}
              </text>
            </Link>
          )}
        </g>
      ))}
      {points.map((point) => {
        const pos = locate(point.id);
        return (
          <Link
            key={point.id}
            to={nodeUrl(point.id)}
            aria-label={`${point.label} (${point.id})`}
          >
            <circle cx={pos.x} cy={pos.y} r="9" className="definition-point" />
            <title>{point.label}</title>
          </Link>
        );
      })}
    </svg>
  );
}
export function DocumentGraph({
  graph,
  unreviewed,
}: {
  graph: GlobalGraph;
  unreviewed: boolean;
}) {
  const taxonomy = useTaxonomy(),
    [selected, setSelected] = useState<{ from: string; to: string }>();
  const x = scale(
      graph.documents.map((doc) => doc.x),
      760,
    ),
    y = scale(
      graph.documents.map((doc) => doc.y),
      220,
    );
  const docs = new Map(graph.documents.map((doc) => [doc.doc_key, doc]));
  const relationships = taxonomy.data?.relations.filter(
    (relation) =>
      selected &&
      new Set([selected.from, selected.to]).has(
        relation.source.split(".")[0],
      ) &&
      new Set([selected.from, selected.to]).has(
        relation.target.split(".")[0],
      ) &&
      relation.source.split(".")[0] !== relation.target.split(".")[0] &&
      (relation.review.status === "accepted" ||
        (unreviewed && relation.review.status === "unreviewed")),
  );
  const edges = graph.document_edges.filter(
    (edge) =>
      edge.imports +
        edge.relations.accepted +
        (unreviewed ? edge.relations.unreviewed : 0) >
      0,
  );
  return (
    <div className="document-graph">
      <svg
        viewBox="0 0 1000 390"
        role="group"
        aria-label={t("timeline.documentGraph")}
      >
        {edges.map((edge) => {
          const a = docs.get(edge.from),
            b = docs.get(edge.to);
          if (!a || !b) return null;
          return (
            <line
              key={`${edge.from}:${edge.to}`}
              x1={x(a.x)}
              y1={y(a.y)}
              x2={x(b.x)}
              y2={y(b.y)}
              className="document-edge"
              strokeWidth={Math.min(
                12,
                2 +
                  Math.log2(
                    1 +
                      edge.imports +
                      edge.relations.accepted +
                      (unreviewed ? edge.relations.unreviewed : 0),
                  ),
              )}
            />
          );
        })}
        {graph.documents.map((doc) => (
          <Link
            key={doc.doc_key}
            to={`/doc/${doc.doc_key}`}
            aria-label={`${doc.doc_key} ${doc.year}`}
          >
            <circle
              cx={x(doc.x)}
              cy={y(doc.y)}
              r="12"
              className="definition-point"
            />
            <text x={x(doc.x) + 20} y={y(doc.y) + 5}>
              {doc.doc_key}
            </text>
            <text x={x(doc.x) + 20} y={y(doc.y) + 26}>
              {doc.year}
            </text>
          </Link>
        ))}
      </svg>
      <div className="chips">
        {edges.map((edge) => (
          <button
            key={`${edge.from}:${edge.to}`}
            onClick={() => setSelected(edge)}
          >
            {t("timeline.documentEdge", { from: edge.from, to: edge.to })}
            {" · "}
            {t("timeline.importCount", { count: edge.imports })} ·{" "}
            {t("timeline.relationCount", {
              count:
                edge.relations.accepted +
                (unreviewed ? edge.relations.unreviewed : 0),
            })}
          </button>
        ))}
      </div>
      {selected && (
        <ul className="relation-list">
          {relationships?.length ? (
            relationships.map((relation) => (
              <li key={relation.id}>
                <Link to={nodeUrl(relation.source)}>{relation.source}</Link>
                {t(`enum.RelationType.${relation.type}`)}
                <Link to={nodeUrl(relation.target)}>{relation.target}</Link>
                <span className="badge">
                  {t(`enum.Review.${relation.review.status}`)}
                </span>
              </li>
            ))
          ) : (
            <li>{t("timeline.noRelations")}</li>
          )}
        </ul>
      )}
    </div>
  );
}
