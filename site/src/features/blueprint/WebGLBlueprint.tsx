import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router";
import Graph from "graphology";
import Sigma from "sigma";
import { seedPositions } from "../../data/graph/seed.mjs";
import { toMermaid } from "../../data/graph/contract.mjs";
import { blueprintUrl, glyphs } from "../../components/ui";
import type { DocumentBundle } from "../../data/source";
import type { NodeSummary, NodeRef, Edge } from "../../data/types";
import { t } from "../../i18n/t";

type GraphNode = (NodeSummary | NodeRef) & { chapterSummary?: boolean };

/** Keep the full filtered graph when the user explicitly expands a large document. */
export default function WebGLBlueprint({
  nodes,
  edges,
  bundle,
  selected,
  direction,
  onToggleChapter,
}: {
  nodes: GraphNode[];
  edges: Edge[];
  bundle: DocumentBundle;
  selected?: string;
  direction: string;
  onToggleChapter: (chapter: string) => void;
}) {
  const container = useRef<HTMLDivElement>(null),
    renderer = useRef<Sigma | null>(null),
    navigate = useNavigate();
  const [unavailable, setUnavailable] = useState(false),
    [ready, setReady] = useState(false),
    [tooltip, setTooltip] = useState(""),
    [notice, setNotice] = useState("");
  useEffect(() => {
    const element = container.current;
    if (!element) return;
    setUnavailable(false);
    setReady(false);
    element.dataset.ready = "false";
    const start = performance.now();
    const graph = new Graph({ multi: true, type: "directed" });
    const nodeById = new Map(nodes.map((node) => [node.id, node]));
    const chapters = bundle.chapters.map((chapter) => ({
      ...chapter,
      node_ids: [...chapter.node_ids, `chapter:${chapter.chapter}`],
    }));
    // Prefer build-time coordinates; seeded dependency ranks cover expanded auxiliaries.
    const positions = seedPositions(nodes, edges, chapters, direction);
    for (const node of nodes) {
      const point = bundle.layout?.nodes[node.id];
      const position = point
        ? direction === "RIGHT"
          ? { x: point.y, y: point.x }
          : point
        : positions[node.id];
      graph.addNode(node.id, {
        x: position.x,
        y: -position.y,
        label: `${glyphs[node.status]} ${node.label}`,
        size: node.id === selected ? 7 : 4,
        color:
          node.headline === "proof-complete"
            ? "#247347"
            : node.headline === "error"
              ? "#b02e22"
              : node.headline === "statement-complete"
                ? "#789981"
                : "#849088",
      });
    }
    edges.forEach((edge, i) => {
      if (graph.hasNode(edge.from) && graph.hasNode(edge.to))
        graph.addEdgeWithKey(`e${i}`, edge.to, edge.from, {
          size: 1,
          color: edge.declared ? "#a1b4a7" : "#c6691b",
          opacity: edge.verified ? 1 : 0.55,
        });
    });
    let instance: Sigma | undefined;
    try {
      instance = new Sigma(graph, element, {
        settings: { hideLabelsOnMove: true, labelDensity: 0.2 },
        styles: { edges: { head: "arrow" } },
      });
      renderer.current = instance;
      instance.once("afterRender", () => {
        element.dataset.ready = "true";
        element.dataset.readyAt = String(performance.now());
        element.dataset.visibleNodes = String(graph.order);
        element.dataset.visibleEdges = String(graph.size);
        element.dataset.renderMs = String(performance.now() - start);
        setReady(true);
      });
      instance.on("clickNode", ({ node }) => {
        if (nodeById.get(node)?.chapterSummary) onToggleChapter(node.slice(8));
        else navigate(blueprintUrl(node));
      });
      instance.on("enterNode", ({ node }) => {
        const item = nodeById.get(node);
        setTooltip(
          item && "statement_first_line" in item
            ? item.statement_first_line
            : item?.label || node,
        );
      });
      instance.on("leaveNode", () => setTooltip(""));
      if (selected && graph.hasNode(selected)) {
        const point = instance.getNodeDisplayData(selected)!;
        instance.getCamera().setState({ x: point.x, y: point.y, ratio: 0.05 });
      }
      instance.scheduleRender();
    } catch {
      instance?.kill();
      instance = undefined;
      renderer.current = null;
      element.replaceChildren();
      setUnavailable(true);
    }
    return () => {
      if (renderer.current === instance) renderer.current = null;
      instance?.kill();
    };
  }, [nodes, edges, bundle, direction, selected, navigate, onToggleChapter]);

  const exportPng = () => {
    const instance = renderer.current;
    if (!instance || !container.current) return;
    // Copy synchronously after a fresh render, before WebGL discards its buffer.
    instance.once("afterRender", () => {
      try {
        const layers = Array.from(
          container.current!.querySelectorAll("canvas"),
        );
        const canvas = document.createElement("canvas");
        canvas.width = layers[0].width;
        canvas.height = layers[0].height;
        const context = canvas.getContext("2d")!;
        context.fillStyle = "#f6f8f6";
        context.fillRect(0, 0, canvas.width, canvas.height);
        for (const layer of layers) context.drawImage(layer, 0, 0);
        const link = document.createElement("a");
        link.href = canvas.toDataURL("image/png");
        link.download = `${bundle.document.doc_key}.png`;
        link.click();
      } catch {
        setNotice(t("doc.exportFailed"));
      }
    });
    instance.scheduleRender();
  };
  return (
    <div className="blueprint">
      <div className="graph-actions">
        <button disabled={!ready} onClick={exportPng}>
          {t("doc.exportPng")}
        </button>
        <button
          onClick={() => {
            void navigator.clipboard.writeText(toMermaid(nodes, edges)).then(
              () => setNotice(t("doc.copyDone")),
              () => setNotice(t("doc.copyFailed")),
            );
          }}
        >
          {t("doc.exportMermaid")}
        </button>
        <Link to={`/doc/${bundle.document.doc_key}?view=list`}>
          {t("doc.webglList")}
        </Link>
      </div>
      <p className="muted">{t("doc.webglMode")}</p>
      {unavailable && <p role="status">{t("doc.webglUnavailable")}</p>}
      <p id="graph-help" className="sr-only">
        {t("doc.graphHelp")}
      </p>
      <div
        ref={container}
        className="graph-canvas"
        data-renderer="webgl"
        hidden={unavailable}
        role="img"
        tabIndex={0}
        aria-label={t("doc.graphSummary", {
          doc: bundle.document.doc_key,
          count: nodes.length,
          proved: nodes.filter((node) => node.headline === "proof-complete")
            .length,
          chapters: bundle.chapters.length,
        })}
        aria-describedby="graph-help"
        onKeyDown={(event) => {
          if (!event.key.startsWith("Arrow")) return;
          event.preventDefault();
          const graph = renderer.current?.getGraph();
          const current = selected || nodes[0]?.id;
          if (!graph || !current || !graph.hasNode(current)) return;
          const neighbors = graph.neighbors(current);
          const id =
            neighbors[
              event.key === "ArrowUp" || event.key === "ArrowLeft"
                ? 0
                : neighbors.length - 1
            ] || current;
          if (id.startsWith("chapter:")) onToggleChapter(id.slice(8));
          else navigate(blueprintUrl(id));
        }}
      />
      {tooltip && (
        <div className="graph-tooltip" role="tooltip">
          {tooltip}
        </div>
      )}
      {notice && (
        <p className="graph-notice" role="status">
          {notice}
        </p>
      )}
    </div>
  );
}
