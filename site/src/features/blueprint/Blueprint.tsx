import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import cytoscape, {
  type Core,
  type ElementDefinition,
  type StylesheetStyle,
} from "cytoscape";
import { useNavigate } from "react-router";
import {
  contractAux,
  aggregateEdges,
  defaultCollapsed,
  toMermaid,
} from "../../data/graph/contract.mjs";
import { layout, compatiblePrecomputed } from "./layout";
import {
  nodeCard,
  NODE_FONT_SIZE,
  CARD_LAYOUT_VERSION,
} from "../../data/graph/presentation.mjs";
import { BlueprintLegend } from "./BlueprintLegend";
import {
  blueprintColors as colors,
  blueprintShapes as shapes,
} from "./appearance";
import { readLabels, revealSelection } from "./viewport";
import { seedPositions } from "../../data/graph/seed.mjs";
import { blueprintUrl, ErrorView, Loading } from "../../components/ui";
import type { DocumentBundle, Manifest } from "../../data/source";
import type { NodeSummary, NodeRef, Edge } from "../../data/types";
import { t } from "../../i18n/t";
type GraphNode = (NodeSummary | NodeRef) & { chapterSummary?: boolean };
const WebGLBlueprint = lazy(() => import("./WebGLBlueprint"));
export const styles: StylesheetStyle[] = [
  {
    selector: "node",
    style: {
      shape: shapes.source,
      width: "data(width)",
      height: "data(height)",
      "background-color": colors.inProgress.fill,
      "border-width": 2,
      "border-color": colors.inProgress.border,
      label: "data(label)",
      color: "#183426",
      "font-family": "system-ui",
      "font-size": NODE_FONT_SIZE,
      "font-weight": 500,
      "line-height": 1.25,
      "text-wrap": "wrap",
      "text-max-width": "data(textWidth)",
      "text-overflow-wrap": "anywhere",
      "text-valign": "center",
      "text-halign": "center",
      "min-zoomed-font-size": 8,
    },
  },
  {
    selector: 'node[headline = "statement-complete"]',
    style: {
      "background-color": colors.statementComplete.fill,
      "border-color": colors.statementComplete.border,
    },
  },
  {
    selector: 'node[headline = "proof-complete"]',
    style: {
      "background-color": colors.proofComplete.fill,
      color: colors.inProgress.fill,
      "border-color": colors.proofComplete.border,
    },
  },
  {
    selector: 'node[headline = "error"]',
    style: {
      "background-color": colors.error.fill,
      "border-color": colors.error.border,
      color: "#7d2018",
    },
  },
  {
    selector: 'node[headline = "none"]',
    style: { "background-color": colors.informalOrPruned },
  },
  {
    selector: 'node[status = "pruned"]',
    style: {
      "background-color": colors.informalOrPruned,
      "background-opacity": 0.5,
    },
  },
  {
    selector: 'node[status = "proved-modulo-citations"]',
    style: { "border-style": "dashed", "border-width": 3 },
  },
  {
    selector: 'node[status = "proved-pending-deps"]',
    style: {
      "border-style": "dashed",
      "border-width": 3,
      "background-image": `data:image/svg+xml;charset=utf-8,${encodeURIComponent(
        '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><path d="M0 8L8 0" stroke="#597d60" stroke-opacity=".25"/></svg>',
      )}`,
      "background-repeat": "repeat",
      "background-width": "8px",
      "background-height": "8px",
    },
  },
  {
    selector: 'node[status = "proved-with-axioms"]',
    style: { "border-color": colors.extraAxioms, "border-width": 4 },
  },
  {
    selector: 'node[fidelity = "foundation"]',
    style: { "border-color": colors.foundation, "border-width": 3 },
  },
  {
    selector: 'node[fidelity = "deviates"]',
    style: { "border-color": colors.deviation, "border-width": 3 },
  },
  {
    selector: "node[raised = 1]",
    style: {
      "border-color": colors.dispute,
      "border-style": "dashed",
      "border-width": 3,
    },
  },
  { selector: "node[aux = 1]", style: { shape: shapes.auxiliary } },
  { selector: "node[bridge = 1]", style: { shape: shapes.bridge } },
  {
    selector: "node[cited = 1]",
    style: { shape: shapes.cited, "border-style": "dashed" },
  },
  {
    selector: "node[external = 1]",
    style: { "border-style": "dashed", "background-color": colors.external },
  },
  {
    selector: "node[chapterSummary = 1]",
    style: {
      "background-color": colors.external,
      color: "#183426",
      "border-color": colors.inProgress.border,
      "border-style": "solid",
      "font-weight": "bold",
    },
  },
  {
    selector: ":parent",
    style: {
      "background-color": "#e8efe9",
      "background-opacity": 0.35,
      "border-width": 1,
      "border-color": "#c2d0c5",
      label: "data(label)",
      "text-valign": "top",
      "text-max-width": "480px",
      "font-weight": "bold",
      padding: "28px",
      shape: "roundrectangle",
    },
  },
  {
    selector: "edge",
    style: {
      width: 1.8,
      opacity: 0.35,
      "line-color": colors.edge,
      "target-arrow-color": colors.edge,
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      "arrow-scale": 0.9,
      label: "data(viaLabel)",
      "font-size": 11,
      color: "#385543",
      "text-background-color": colors.inProgress.fill,
      "text-background-opacity": 0.9,
      "text-background-padding": "3px",
    },
  },
  { selector: "edge[verified = 0]", style: { "line-style": "dashed" } },
  {
    selector: "edge[declared = 0]",
    style: {
      "line-color": colors.undeclaredEdge,
      "target-arrow-color": colors.undeclaredEdge,
    },
  },
  {
    selector: 'edge[kind = "proof"]',
    style: { "target-arrow-fill": "hollow" },
  },
  {
    selector: "node.focus",
    style: {
      "underlay-color": "#268651",
      "underlay-opacity": 0.2,
      "underlay-padding": 10,
    },
  },
  { selector: ".neighbor", style: { "border-width": 4 } },
  { selector: "edge.focus", style: { opacity: 1, width: 2.5 } },
];
export function Blueprint({
  bundle,
  manifest,
  selected,
  chapter,
  filter,
  headline,
  expandAux,
  collapsedChapters,
  onToggleChapter,
  direction,
  edgeMode,
}: {
  bundle: DocumentBundle;
  manifest: Manifest;
  selected?: string;
  chapter: string;
  filter: string;
  headline: string;
  expandAux: boolean;
  collapsedChapters: Set<string>;
  onToggleChapter: (chapter: string) => void;
  direction: string;
  edgeMode: string;
}) {
  const container = useRef<HTMLDivElement>(null),
    cy = useRef<Core | null>(null),
    navigate = useNavigate();
  const selection = useRef(selected);
  selection.current = selected;
  const viewMode = useRef<"readable" | "overview">("readable");
  const userMoved = useRef(false);
  const [zoom, setZoom] = useState(1);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<unknown>(),
    [tooltip, setTooltip] = useState(""),
    [context, setContext] = useState<NodeSummary>(),
    [notice, setNotice] = useState("");
  const auxStorageKey = `homalg:aux:${bundle.document.doc_key}`;
  const [expandedParents, setExpandedParents] = useState<Set<string>>(() => {
    try {
      return new Set(JSON.parse(sessionStorage.getItem(auxStorageKey) || "[]"));
    } catch {
      return new Set();
    }
  });
  const nodeById = useMemo(
    () => new Map(bundle.nodes.map((node) => [node.id, node])),
    [bundle],
  );
  const auxParents = useMemo(
    () =>
      new Set(
        bundle.nodes
          .filter((node) => node.is_aux && node.aux_kind !== "bridge")
          .map((node) => node.aux_parent),
      ),
    [bundle],
  );
  const toggleAux = (id: string) =>
    setExpandedParents((previous) => {
      const next = new Set(previous);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      try {
        sessionStorage.setItem(auxStorageKey, JSON.stringify([...next]));
      } catch {
        /* Storage is optional. */
      }
      return next;
    });
  const entry = manifest.documents.find(
    (doc) => doc.doc_key === bundle.document.doc_key,
  )!;
  const graph = useMemo(() => {
    const computedAt = performance.now();
    const collapsed: Set<string> = expandAux
      ? new Set()
      : defaultCollapsed(bundle.nodes);
    for (const node of bundle.nodes) {
      if (node.aux_parent && expandedParents.has(node.aux_parent))
        collapsed.delete(node.id);
    }
    if (selected) {
      let node = nodeById.get(selected);
      while (node) {
        collapsed.delete(node.id);
        node = nodeById.get(node.aux_parent || "");
      }
    }
    const edges = contractAux(
      bundle.nodes,
      bundle.edges,
      collapsed,
    ) as (Edge & { via?: string[] })[];
    let nodes: GraphNode[] = bundle.nodes.filter(
      (node) => !collapsed.has(node.id),
    );
    const chapterOf = new Map(
      bundle.chapters.flatMap((item) =>
        item.node_ids.map((id) => [id, item.chapter] as const),
      ),
    );
    const replaced = new Map<string, string>();
    for (const item of bundle.chapters) {
      if (
        collapsedChapters.has(item.chapter) &&
        !item.node_ids.includes(selected || "")
      ) {
        const members = nodes.filter(
          (node) => chapterOf.get(node.id) === item.chapter,
        );
        if (members.length) {
          const id = `chapter:${item.chapter}`;
          members.forEach((node) => replaced.set(node.id, id));
          nodes = nodes.filter(
            (node) => chapterOf.get(node.id) !== item.chapter,
          );
          nodes.push({
            ...members[0],
            id,
            label: `${item.chapter} · ${item.title || ""}\n${t("doc.more", { count: members.length })}`,
            chapterSummary: true,
          });
        }
      }
    }
    nodes = nodes.filter(
      (node) =>
        node.id === selected ||
        ((!chapter ||
          chapterOf.get(node.id) === chapter ||
          node.id === `chapter:${chapter}`) &&
          (!filter ||
            `${node.id} ${node.label} ${"title" in node ? node.title : ""}`
              .toLowerCase()
              .includes(filter.toLowerCase())) &&
          (!headline || node.headline === headline)),
    );
    const ids = new Set(nodes.map((node) => node.id));
    const visibleEdges = aggregateEdges(
      edges
        .map((edge) => ({
          ...edge,
          from: replaced.get(edge.from) || edge.from,
          to: replaced.get(edge.to) || edge.to,
        }))
        .filter(
          (edge) =>
            edge.from !== edge.to &&
            ids.has(edge.from) &&
            (edgeMode !== "verified" || edge.verified) &&
            (edgeMode !== "declared" || edge.declared),
        ),
    ) as (Edge & { via?: string[]; aggregate_count: number })[];
    const externals = bundle.external_nodes.filter((node) =>
      visibleEdges.some((edge) => edge.to === node.id),
    );
    nodes.push(...externals);
    externals.forEach((node) => ids.add(node.id));
    return {
      nodes,
      edges: visibleEdges.filter((edge) => ids.has(edge.to)),
      chapterOf,
      collapsed,
      replaced,
      computedAt,
      computeMs: performance.now() - computedAt,
    };
  }, [
    bundle,
    nodeById,
    expandedParents,
    selected,
    chapter,
    filter,
    headline,
    expandAux,
    collapsedChapters,
    edgeMode,
  ]);
  // Selecting an already visible node must not recreate or relayout the graph.
  const layoutKey = `${entry.doc_key}:${entry.graph_hash}:${CARD_LAYOUT_VERSION}:${direction}:${graph.nodes.map((node) => node.id).join(",")}:${graph.edges.map((edge) => `${edge.from}>${edge.to}:${edge.kind}`).join(",")}`;
  useEffect(() => {
    const instance = cy.current;
    if (!instance) return;
    const frame = requestAnimationFrame(() => {
      if (!instance.destroyed()) revealSelection(instance, selected);
    });
    return () => cancelAnimationFrame(frame);
  }, [selected]);
  useEffect(() => {
    // Expanding a large document must not allocate a second Canvas renderer.
    if (graph.nodes.length > 20_000) return;
    let cancelled = false;
    let resizeObserver: ResizeObserver | undefined;
    let resizeFrame = 0;
    setError(undefined);
    const apply = async () => {
      const applyAt = performance.now();
      if (!container.current) return;
      setBusy(true);
      const defaults =
        !chapter &&
        !filter &&
        !headline &&
        !expandAux &&
        !expandedParents.size &&
        !collapsedChapters.size &&
        direction === "DOWN" &&
        edgeMode === "all" &&
        !selection.current?.includes(".Aux_");
      const key = layoutKey;
      const chapters = bundle.chapters.map((item) => ({
        ...item,
        node_ids: [...item.node_ids, `chapter:${item.chapter}`],
      }));
      const precomputed =
        bundle.layout?.view === "aux-collapsed" &&
        (await compatiblePrecomputed(bundle))
          ? bundle.layout.nodes
          : undefined;
      const projected = precomputed ? { ...precomputed } : undefined;
      const refinement =
        defaults && projected
          ? undefined
          : layout(graph.nodes, graph.edges, chapters, key, direction);
      const positions =
        defaults && projected
          ? projected
          : seedPositions(graph.nodes, graph.edges, chapters, direction);
      if (cancelled) return;
      const elements: ElementDefinition[] = [];
      for (const item of bundle.chapters)
        if (
          graph.nodes.some(
            (node) =>
              graph.chapterOf.get(node.id) === item.chapter &&
              !node.chapterSummary,
          )
        )
          elements.push({
            data: {
              id: `group:${item.chapter}`,
              label: `${item.chapter} · ${item.title || ""}`,
              chapter: item.chapter,
              width: 264,
              height: 64,
              textWidth: 480,
            },
          });
      const auxCounts = new Map<string, number>();
      for (const item of bundle.nodes)
        if (item.aux_parent && graph.collapsed.has(item.id))
          auxCounts.set(
            item.aux_parent,
            (auxCounts.get(item.aux_parent) || 0) + 1,
          );
      const chapterOrder = new Map(
        bundle.chapters.map((item, i) => [item.chapter, i]),
      );
      for (const node of graph.nodes) {
        const card = nodeCard(node);
        const local = nodeById.get(node.id),
          auxCount = auxCounts.get(node.id) || 0;
        elements.push({
          data: {
            id: node.id,
            auxCount,
            ...card,
            label: `${card.label}${auxCount ? `\n${t("doc.auxCount", { count: auxCount })}` : ""}`,
            sourceItem:
              local && !local.is_aux && !local.local_id.startsWith("Cited_")
                ? 1
                : 0,
            chapterOrder:
              chapterOrder.get(graph.chapterOf.get(node.id) || "") ??
              bundle.chapters.length,
            headline: node.headline || "none",
            status: node.status,
            fidelity: local?.fidelity_status,
            raised: local?.disputed && local.headline !== "error" ? 1 : 0,
            aux: local?.is_aux ? 1 : 0,
            bridge: local?.aux_kind === "bridge" ? 1 : 0,
            cited: local?.local_id.startsWith("Cited_") ? 1 : 0,
            external: !local && !node.chapterSummary ? 1 : 0,
            parent:
              !node.chapterSummary && graph.chapterOf.has(node.id)
                ? `group:${graph.chapterOf.get(node.id)}`
                : undefined,
            chapterSummary: node.chapterSummary ? 1 : 0,
          },
          position: positions[node.id] || { x: 0, y: 0 },
        });
      }
      graph.edges.forEach((edge, i) =>
        elements.push({
          data: {
            id: `edge:${i}`,
            source: edge.to,
            target: edge.from,
            kind: edge.kind,
            declared: edge.declared ? 1 : 0,
            verified: edge.verified ? 1 : 0,
            viaLabel:
              edge.aggregate_count > 1
                ? t("doc.edgeCount", { count: edge.aggregate_count })
                : edge.via?.length
                  ? `+${edge.via.length}`
                  : "",
            via: edge.via?.join(", ") || "",
          },
        }),
      );
      cy.current?.destroy();
      container.current.dataset.ready = "false";
      container.current.dataset.layoutReady = "false";
      const constructAt = performance.now();
      const instance = cytoscape({
        container: container.current,
        elements,
        style: styles,
        layout: { name: "preset" },
        hideEdgesOnViewport: graph.nodes.length > 1500,
        textureOnViewport: graph.nodes.length > 1500,
        wheelSensitivity: 0.2,
        // Sparse documents can still have very tall dependency layouts.
        minZoom: 0.002,
        maxZoom: 3,
      });
      const constructMs = performance.now() - constructAt;
      cy.current = instance;
      userMoved.current = false;
      instance.on("zoom", () => setZoom(instance.zoom()));
      instance.on("dragpan scrollzoom pinchzoom", () => {
        userMoved.current = true;
      });
      const applyView = () => {
        if (viewMode.current === "overview") instance.fit(undefined, 35);
        else readLabels(instance, selection.current);
        revealSelection(instance, selection.current);
      };
      instance.one("render", () => {
        if (!cancelled && container.current) {
          container.current.dataset.ready = "true";
          container.current.dataset.readyAt = String(performance.now());
          container.current.dataset.visibleNodes = String(graph.nodes.length);
          container.current.dataset.profile = JSON.stringify({
            graphAt: graph.computedAt,
            graphMs: graph.computeMs,
            applyAt,
            constructAt,
            constructMs,
            visibleEdges: graph.edges.length,
            precomputed: !!(defaults && projected),
          });
        }
      });
      instance.on("tap", "node", (event) => {
        const node = event.target;
        if (node.isParent()) onToggleChapter(node.data("chapter"));
        else if (node.data("chapterSummary"))
          onToggleChapter(node.id().slice(8));
        else {
          navigate(`${blueprintUrl(node.id())}?view=blueprint`);
        }
      });
      instance.on("dbltap", "node", (event) => {
        const node = event.target;
        instance.elements().removeClass("neighbor");
        node.closedNeighborhood().addClass("neighbor");
        readLabels(instance, node.id());
      });
      instance.on("mouseover", "node", (event) => {
        const node = nodeById.get(event.target.id());
        setTooltip(node?.statement_first_line || event.target.data("label"));
      });
      instance.on("mouseover", "edge", (event) =>
        setTooltip(event.target.data("via")),
      );
      instance.on("mouseout", () => setTooltip(""));
      instance.on("cxttap", "node", (event) =>
        setContext(nodeById.get(event.target.id())),
      );
      applyView();
      resizeObserver = new ResizeObserver(() => {
        cancelAnimationFrame(resizeFrame);
        resizeFrame = requestAnimationFrame(() => {
          if (!cancelled && !instance.destroyed()) {
            instance.resize();
            revealSelection(instance, selection.current);
          }
        });
      });
      resizeObserver.observe(container.current);
      if (refinement)
        void refinement
          .then((refined) => {
            if (cancelled || instance.destroyed()) return;
            instance.batch(() => {
              for (const node of graph.nodes)
                if (refined[node.id])
                  instance.getElementById(node.id).position(refined[node.id]);
            });
            if (!userMoved.current) applyView();
            container.current?.setAttribute("data-layout-ready", "true");
            setBusy(false);
          })
          .catch((reason) => {
            if (!cancelled) {
              setError(reason);
              setBusy(false);
            }
          });
      else {
        setBusy(false);
        container.current?.setAttribute("data-layout-ready", "true");
      }
    };
    void apply().catch((reason) => {
      if (!cancelled) {
        setError(reason);
        setBusy(false);
      }
    });
    return () => {
      cancelled = true;
      resizeObserver?.disconnect();
      cancelAnimationFrame(resizeFrame);
      cy.current?.destroy();
      cy.current = null;
    };
  }, [bundle, layoutKey, nodeById, onToggleChapter]);
  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setNotice(t("doc.copyDone"));
    } catch {
      setNotice(t("doc.copyFailed"));
    }
  };
  if (graph.nodes.length > 20_000)
    return (
      <Suspense fallback={<Loading />}>
        <WebGLBlueprint
          nodes={graph.nodes}
          edges={graph.edges}
          bundle={bundle}
          selected={selected}
          direction={direction}
          onToggleChapter={onToggleChapter}
        />
      </Suspense>
    );
  return (
    <div className="blueprint">
      <div className="graph-actions">
        <div
          className="graph-view-controls"
          role="group"
          aria-label={t("doc.readableView")}
        >
          <button
            onClick={() => {
              if (!cy.current) return;
              viewMode.current = "readable";
              userMoved.current = false;
              readLabels(cy.current, selected);
            }}
          >
            {t("doc.readableView")}
          </button>
          <button
            onClick={() => {
              if (!cy.current) return;
              viewMode.current = "overview";
              userMoved.current = false;
              cy.current.fit(undefined, 35);
            }}
          >
            {t("doc.fitAll")}
          </button>
          <button
            aria-label={t("doc.zoomOut")}
            onClick={() => {
              if (!cy.current) return;
              userMoved.current = true;
              cy.current.zoom({
                level: cy.current.zoom() / 1.25,
                renderedPosition: {
                  x: cy.current.width() / 2,
                  y: cy.current.height() / 2,
                },
              });
            }}
          >
            {t("doc.zoomOutSymbol")}
          </button>
          <output className="graph-zoom">
            {t("doc.zoomLevel", { percent: Math.round(zoom * 100) })}
          </output>
          <button
            aria-label={t("doc.zoomIn")}
            onClick={() => {
              if (!cy.current) return;
              userMoved.current = true;
              cy.current.zoom({
                level: cy.current.zoom() * 1.25,
                renderedPosition: {
                  x: cy.current.width() / 2,
                  y: cy.current.height() / 2,
                },
              });
            }}
          >
            {t("doc.zoomInSymbol")}
          </button>
        </div>
        {selected && auxParents.has(selected) && !expandAux && (
          <button onClick={() => toggleAux(selected)}>
            {expandedParents.has(selected)
              ? t("doc.collapseParentAux")
              : t("doc.expandParentAux")}
          </button>
        )}
        <div className="graph-utilities">
          <BlueprintLegend />
          <details className="graph-menu" name="blueprint-tools">
            <summary>{t("doc.export")}</summary>
            <div className="graph-menu-panel">
              <button
                onClick={() => {
                  if (!cy.current) return;
                  const link = document.createElement("a");
                  link.href = cy.current.png({
                    full: true,
                    scale: 2,
                    bg: "#f6f8f6",
                  });
                  link.download = `${entry.doc_key}.png`;
                  link.click();
                }}
              >
                {t("doc.exportPng")}
              </button>
              <button
                onClick={() => void copy(toMermaid(graph.nodes, graph.edges))}
              >
                {t("doc.exportMermaid")}
              </button>
            </div>
          </details>
          <details className="graph-menu" name="blueprint-tools">
            <summary>{t("doc.help")}</summary>
            <div className="graph-menu-panel graph-help-panel">
              <p>{t("doc.panHelp")}</p>
              <p>{t("doc.chapterLayoutHelp")}</p>
              <p>{t("doc.overviewHelp")}</p>
            </div>
          </details>
        </div>
      </div>
      {!!error && <ErrorView error={error} />}
      <p id="graph-help" className="sr-only">
        {t("doc.graphHelp")}
      </p>
      <div
        ref={container}
        className="graph-canvas"
        role="img"
        tabIndex={0}
        aria-label={t("doc.graphSummary", {
          doc: entry.doc_key,
          count: graph.nodes.length,
          proved: entry.headline_counts["proof-complete"],
          chapters: bundle.chapters.length,
        })}
        aria-describedby="graph-help"
        onKeyDown={(event) => {
          if (!event.key.startsWith("Arrow") || !cy.current) return;
          event.preventDefault();
          const current = selected
            ? cy.current.getElementById(selected)
            : cy.current.nodes().not(":parent").first();
          const neighbors = current.neighborhood().nodes().not(":parent");
          const target = neighbors.length
            ? neighbors[
                event.key === "ArrowUp" || event.key === "ArrowLeft"
                  ? 0
                  : neighbors.length - 1
              ]
            : current;
          if (target?.length)
            navigate(`${blueprintUrl(target.id())}?view=blueprint`);
        }}
      />
      {busy && (
        <div className="layout-status" role="status">
          {t("doc.layout")}
        </div>
      )}
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
      {context && (
        <div className="graph-context" role="menu" aria-label={t("doc.menu")}>
          <button
            role="menuitem"
            onClick={() => {
              void copy(context.id);
              setContext(undefined);
            }}
          >
            {t("doc.copyId")}
          </button>
          <button
            role="menuitem"
            onClick={() => {
              void copy(context.decl_names.join("\n"));
              setContext(undefined);
            }}
          >
            {t("doc.copyLean")}
          </button>
          <a
            role="menuitem"
            href={`${manifest.repo_url}/blob/${manifest.commit}/HomAlg/${context.doc}/${context.local_id}.lean`}
            target="_blank"
            rel="noreferrer"
          >
            {t("node.github")}
          </a>
          <button
            role="menuitem"
            onClick={() =>
              navigate(`/search?deps=${context.id}&dir=up&depth=2`)
            }
          >
            {t("doc.transitive")}
          </button>
          <button role="menuitem" onClick={() => setContext(undefined)}>
            {t("node.close")}
          </button>
        </div>
      )}
    </div>
  );
}
