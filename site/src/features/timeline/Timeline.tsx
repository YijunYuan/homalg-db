import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router";
import { Tabs } from "radix-ui";
import Graph from "graphology";
import Sigma from "sigma";
import { useGlobalGraph, useGlobalDag, useManifest } from "../../data/loaders";
import { ErrorView, Loading, PageTitle, nodeUrl } from "../../components/ui";
import type { GlobalDagShard } from "../../data/source";
import { t } from "../../i18n/t";
import { ConceptArcView, DocumentGraph } from "./GlobalViews";
function Dag({
  shard,
  unreviewed,
  auxiliary,
}: {
  shard: GlobalDagShard;
  unreviewed: boolean;
  auxiliary: boolean;
}) {
  const container = useRef<HTMLDivElement>(null),
    navigate = useNavigate(),
    [error, setError] = useState(false);
  useEffect(() => {
    if (!container.current) return;
    const graph = new Graph({ multi: true, type: "directed" });
    for (const node of shard.nodes)
      graph.addNode(node.id, {
        x: node.x,
        y: -node.y,
        label: node.id,
        size: 5,
        color:
          node.headline === "proof-complete"
            ? "#247347"
            : node.headline === "error"
              ? "#b02e22"
              : "#789981",
      });
    shard.edges
      .filter(
        (edge) =>
          (!edge.relation ||
            edge.review_status === "accepted" ||
            (unreviewed && edge.review_status === "unreviewed")) &&
          (auxiliary || !edge.via_aux),
      )
      .forEach((edge, i) => {
        if (graph.hasNode(edge.from) && graph.hasNode(edge.to))
          graph.addEdgeWithKey(`e${i}`, edge.to, edge.from, {
            size: 1,
            color: edge.review_status === "unreviewed" ? "#bba16d" : "#c2cec4",
          });
      });
    let renderer: Sigma;
    try {
      renderer = new Sigma(graph, container.current);
      renderer.on("clickNode", ({ node }) => navigate(nodeUrl(node)));
    } catch {
      setError(true);
      return;
    }
    return () => renderer.kill();
  }, [shard, unreviewed, auxiliary, navigate]);
  return error ? (
    <p className="notice">{t("timeline.webgl")}</p>
  ) : (
    <div
      className="timeline-canvas"
      ref={container}
      role="img"
      aria-label={t("timeline.globalDag")}
      aria-describedby="timeline-help"
    />
  );
}
export default function Timeline() {
  const query = useGlobalGraph(),
    manifest = useManifest(),
    [unreviewed, setUnreviewed] = useState(false),
    [auxiliary, setAuxiliary] = useState(false),
    [range, setRange] = useState(-1),
    [selectedConcepts, setSelectedConcepts] = useState<string[]>([]);
  const ranges = manifest.data?.global_dag_files || [];
  const file =
      range >= 0
        ? ranges[range]
        : ranges.length
          ? {
              from: Math.min(...ranges.map((item) => item.from)),
              to: Math.max(...ranges.map((item) => item.to)),
            }
          : undefined,
    dag = useGlobalDag(file ? [file.from, file.to] : undefined);
  if (query.error) return <ErrorView error={query.error} />;
  if (!query.data) return <Loading />;
  const graph = query.data;
  const concepts = graph.concepts.filter(
    (concept) =>
      !selectedConcepts.length || selectedConcepts.includes(concept.id),
  );
  return (
    <div className="page">
      <PageTitle
        title={t("timeline.title")}
        description={t("timeline.description")}
      />
      <Tabs.Root defaultValue="graph">
        <Tabs.List className="tabs" aria-label={t("nav.timeline")}>
          <Tabs.Trigger value="graph">{t("timeline.graph")}</Tabs.Trigger>
          <Tabs.Trigger value="documents">
            {t("timeline.documentGraph")}
          </Tabs.Trigger>
          <Tabs.Trigger value="table">{t("timeline.table")}</Tabs.Trigger>
          <Tabs.Trigger value="dag">{t("timeline.globalDag")}</Tabs.Trigger>
        </Tabs.List>
        <div className="controls">
          <label>
            {t("timeline.chooseConcepts")}
            <select
              multiple
              aria-label={t("timeline.chooseConcepts")}
              value={selectedConcepts}
              onChange={(event) =>
                setSelectedConcepts(
                  Array.from(
                    event.target.selectedOptions,
                    (option) => option.value,
                  ),
                )
              }
            >
              {graph.concepts.map((concept) => (
                <option key={concept.id} value={concept.id}>
                  {concept.id}
                </option>
              ))}
            </select>
          </label>
          <button onClick={() => setSelectedConcepts([])}>
            {t("timeline.allConcepts")}
          </button>
          <label className="check-label">
            <input
              type="checkbox"
              checked={unreviewed}
              onChange={(event) => setUnreviewed(event.target.checked)}
            />
            {t("taxonomy.unreviewedRelations")}
          </label>
        </div>
        <p id="timeline-help" className="sr-only">
          {t("timeline.tableHelp")}
        </p>
        <Tabs.Content value="graph">
          <div
            className="concept-timeline"
            role="region"
            aria-label={t("timeline.summary", {
              documents: graph.documents.length,
              concepts: graph.concepts.length,
            })}
            aria-describedby="timeline-help"
          >
            {concepts.map((concept) => (
              <div className="concept-lane" key={concept.id}>
                <h2>
                  <Link to={`/concepts/${concept.id}`}>{concept.id}</Link>
                </h2>
                <ConceptArcView concept={concept} unreviewed={unreviewed} />
                <div className="lane-points">
                  {concept.lanes.map((lane) => (
                    <div className="lane-point" key={lane.doc}>
                      <span className="year">{lane.year}</span>
                      <Link to={`/doc/${lane.doc}`}>{lane.doc}</Link>
                      <div>
                        {lane.defines.map((node) => (
                          <Link
                            key={node.id}
                            className="badge"
                            to={nodeUrl(node.id)}
                          >
                            {node.label}
                          </Link>
                        ))}
                      </div>
                      <small>
                        {t("timeline.uses")}
                        {": "}
                        {lane.uses_count}
                      </small>
                    </div>
                  ))}
                </div>
                <ul className="timeline-arcs">
                  {concept.arcs
                    .filter(
                      (arc) =>
                        arc.review_status === "accepted" ||
                        (unreviewed && arc.review_status === "unreviewed"),
                    )
                    .map((arc, i) => (
                      <li key={i}>
                        <Link to={nodeUrl(arc.source)}>{arc.source}</Link>
                        <span>{t(`enum.RelationType.${arc.type}`)}</span>
                        <Link to={nodeUrl(arc.target)}>{arc.target}</Link>
                        <span className="badge">
                          {t(`enum.Review.${arc.review_status}`)}
                        </span>
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </div>
        </Tabs.Content>
        <Tabs.Content value="documents">
          <DocumentGraph graph={graph} unreviewed={unreviewed} />
        </Tabs.Content>
        <Tabs.Content value="table">
          <div className="table-scroll">
            <table>
              <caption>{t("timeline.tableHelp")}</caption>
              <thead>
                <tr>
                  <th>{t("timeline.concept")}</th>
                  {graph.documents.map((doc) => (
                    <th key={doc.doc_key}>
                      <Link to={`/doc/${doc.doc_key}`}>{doc.doc_key}</Link>
                      <small>{doc.year}</small>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {concepts.map((concept) => (
                  <tr key={concept.id}>
                    <th>
                      <Link to={`/concepts/${concept.id}`}>{concept.id}</Link>
                    </th>
                    {graph.documents.map((doc) => {
                      const lane = concept.lanes.find(
                        (item) => item.doc === doc.doc_key,
                      );
                      return (
                        <td key={doc.doc_key}>
                          {lane ? (
                            <Link
                              to={`/search?doc=${doc.doc_key}&concepts=${concept.id}`}
                            >
                              {t("timeline.cell", {
                                defines: lane.defines.length,
                                uses: lane.uses_count,
                              })}
                            </Link>
                          ) : (
                            "—"
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Tabs.Content>
        <Tabs.Content value="dag">
          <div className="controls">
            <label>
              {t("timeline.range")}
              <select
                value={range}
                onChange={(event) => setRange(Number(event.target.value))}
              >
                <option value={-1}>{t("timeline.allYears")}</option>
                {manifest.data?.global_dag_files.map((file, i) => (
                  <option key={file.file} value={i}>
                    {file.from}
                    {"–"}
                    {file.to}
                  </option>
                ))}
              </select>
            </label>
            <label className="check-label">
              <input
                type="checkbox"
                checked={auxiliary}
                onChange={(event) => setAuxiliary(event.target.checked)}
              />
              {t("timeline.auxiliary")}
            </label>
          </div>
          {dag.isLoading && <Loading />}
          {dag.error && <ErrorView error={dag.error} />}{" "}
          {dag.data && (
            <Dag
              shard={dag.data}
              unreviewed={unreviewed}
              auxiliary={auxiliary}
            />
          )}
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
