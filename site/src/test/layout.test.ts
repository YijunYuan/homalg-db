// @vitest-environment node
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import ELK from "elkjs";
import {
  chapterGroups,
  graphInput,
  layoutOptions,
  positions,
} from "../../scripts/layout.mjs";
import { nodeCard } from "../data/graph/presentation.mjs";
import { seedPositions } from "../data/graph/seed.mjs";
import { contractAux, defaultCollapsed } from "../data/graph/contract.mjs";
import { compatiblePrecomputed } from "../features/blueprint/layout";
import type { NodesFile, SiteDocumentBundle } from "../data/types";

type Point = { x: number; y: number };
type CardNode = {
  id: string;
  label: string;
  title?: string;
  local_id?: string;
  is_aux?: boolean;
  aux_kind?: string;
  aux_parent?: string;
};

/** Fail for intersecting rendered cards, including taller labels and wider bridge diamonds. */
function expectSeparated(nodes: CardNode[], points: Record<string, Point>) {
  for (let index = 0; index < nodes.length; index++) {
    const a = nodes[index],
      aSize = nodeCard(a),
      aPoint = points[a.id];
    expect(Number.isFinite(aPoint.x) && Number.isFinite(aPoint.y)).toBe(true);
    for (const b of nodes.slice(index + 1)) {
      const bSize = nodeCard(b),
        bPoint = points[b.id];
      const separateX =
        Math.abs(aPoint.x - bPoint.x) >= (aSize.width + bSize.width) / 2;
      const separateY =
        Math.abs(aPoint.y - bPoint.y) >= (aSize.height + bSize.height) / 2;
      expect(separateX || separateY, `${a.id} overlaps ${b.id}`).toBe(true);
    }
  }
}

/** Project the committed pilot metadata without reading generated public files or running Lean. */
async function pilot(expanded: boolean) {
  const document: NodesFile = JSON.parse(
    await readFile(
      new URL("../../../literature/Hochschild1945/nodes.json", import.meta.url),
      "utf8",
    ),
  );
  const all = document.nodes.map(({ id, authored }) => ({
    id,
    label: authored.source.label,
    title: authored.title,
    local_id: id.slice(id.indexOf(".") + 1),
    is_aux: Boolean(authored.aux),
    aux_kind: authored.aux?.kind,
    aux_parent: authored.aux?.parent,
  }));
  const edges = document.nodes.flatMap(({ id, authored, derived }) =>
    (["statement", "proof"] as const).flatMap((kind) =>
      [
        ...new Set([
          ...authored.deps[kind],
          ...(derived?.verified_deps[kind] || []),
        ]),
      ].map((to) => ({ from: id, to, kind, declared: true, verified: true })),
    ),
  );
  const chapters = ["1", "2", "3", "4", "5", "6"].map((chapter) => ({
    chapter,
    node_ids: document.nodes
      .filter((node) => node.authored.source.chapter === chapter)
      .map((node) => node.id),
  }));
  const collapsed = expanded ? new Set<string>() : defaultCollapsed(all);
  return {
    nodes: all.filter((node) => !collapsed.has(node.id)),
    edges: contractAux(all, edges, collapsed),
    chapters,
  };
}

describe("readable chapter layouts", () => {
  it("keeps source numbering in details instead of prefixing the card title", () => {
    const title = "Separable algebras and one-cocycles";
    const card = nodeCard({ id: "A", label: "Theorem 4.1", title });
    expect(card.label.replace(/\s+/g, " ")).toBe(title);
    expect(card.label).not.toContain("Theorem 4.1");
  });

  it("uses authored chapters, actual card dimensions, and leaves cross-chapter edges in the source graph", () => {
    const nodes = [
      { id: "A", label: "A" },
      {
        id: "B",
        label: "Bridge with a long comparison statement",
        aux_kind: "bridge",
      },
      { id: "C", label: "C" },
      { id: "D", label: "D", chapter: "invented", group: "invented" },
    ];
    const edges = [
      { from: "B", to: "A" },
      { from: "C", to: "B" },
    ];
    const chapters = [{ node_ids: ["A", "B"] }, { node_ids: ["C"] }];
    const graph = graphInput(nodes, edges, chapters);
    expect(graph.children.map((group: { id: string }) => group.id)).toEqual([
      "layout:chapter:0",
      "layout:chapter:1",
      "layout:unassigned",
    ]);
    expect(graph.children[0].children[1]).toMatchObject({
      id: "B",
      width: nodeCard(nodes[1]).width,
      height: nodeCard(nodes[1]).height,
    });
    expect(graph.children[0].edges).toHaveLength(1);
    expect(graph.children[1].edges).toHaveLength(0);
    expect(edges).toEqual([
      { from: "B", to: "A" },
      { from: "C", to: "B" },
    ]);
    expect(chapterGroups(nodes, edges, [])).toHaveLength(1);
  });

  it("uses real half sizes when flattening nested ELK coordinates", () => {
    const result = positions({
      children: [
        {
          id: "group",
          x: 900,
          y: 900,
          width: 450,
          height: 300,
          children: [{ id: "wide", x: 20, y: 30, width: 400, height: 180 }],
        },
      ],
    });
    expect(result).toEqual({ wide: { x: 220, y: 120 } });
  });

  it.each(["DOWN", "RIGHT"])(
    "keeps the real 39/44-node pilot compact and disjoint for %s",
    async (direction) => {
      const elk = new ELK();
      for (const expanded of [false, true]) {
        const graph = await pilot(expanded);
        expect(graph.nodes).toHaveLength(expanded ? 44 : 39);
        const output = await elk.layout(
          graphInput(
            graph.nodes,
            graph.edges,
            graph.chapters,
            "browser",
            direction,
          ),
        );
        const points = positions(output);
        expect(Object.keys(points)).toHaveLength(graph.nodes.length);
        expectSeparated(graph.nodes, points);
        expectSeparated(
          graph.nodes,
          seedPositions(graph.nodes, graph.edges, graph.chapters, direction),
        );
        const axis = direction === "DOWN" ? "y" : "x";
        for (const group of chapterGroups(
          graph.nodes,
          graph.edges,
          graph.chapters,
        ))
          for (const edge of group.edges)
            expect(
              points[edge.from][axis],
              `${edge.to} precedes ${edge.from}`,
            ).toBeGreaterThan(points[edge.to][axis]);
        const extents = graph.nodes.map((node) => ({
          ...points[node.id],
          ...nodeCard(node),
        }));
        const width =
          Math.max(...extents.map((node) => node.x + node.width / 2)) -
          Math.min(...extents.map((node) => node.x - node.width / 2));
        const height =
          Math.max(...extents.map((node) => node.y + node.height / 2)) -
          Math.min(...extents.map((node) => node.y - node.height / 2));
        expect(width / height).toBeGreaterThan(0.45);
        expect(width / height).toBeLessThan(3.5);
        expect(Math.max(width, height)).toBeLessThan(5500);
      }
    },
  );

  it("keeps the seed complete for a 20,001-node chain and for a cyclic input", () => {
    const nodes = Array.from({ length: 20_001 }, (_, index) => ({
      id: `n${index}`,
    }));
    const edges = nodes
      .slice(1)
      .map((node, index) => ({ from: node.id, to: nodes[index].id }));
    const points = seedPositions(nodes, edges, []);
    expect(Object.keys(points)).toHaveLength(nodes.length);
    expect(points.n20000.y).toBeGreaterThan(points.n0.y);
    const cyclic = seedPositions(
      nodes.slice(0, 2),
      [
        { from: "n0", to: "n1" },
        { from: "n1", to: "n0" },
      ],
      [],
    );
    expect(
      Object.values(cyclic).every(
        (point) => Number.isFinite(point.x) && Number.isFinite(point.y),
      ),
    ).toBe(true);
  });

  it("accepts current precomputed geometry and rejects old or wrong-view caches", async () => {
    for (const mode of ["ci", "browser"]) {
      const options_hash = createHash("sha256")
        .update(
          JSON.stringify({ view: "aux-collapsed", ...layoutOptions(1, mode) }),
        )
        .digest("hex")
        .slice(0, 16);
      const bundle = {
        layout: {
          view: "aux-collapsed" as const,
          options_hash,
          nodes: { A: { x: 0, y: 0 } },
        },
      };
      expect(await compatiblePrecomputed(bundle)).toBe(true);
      expect(
        await compatiblePrecomputed({
          layout: { ...bundle.layout, options_hash: "old-flat-geometry" },
        }),
      ).toBe(false);
    }
    expect(await compatiblePrecomputed({ layout: null })).toBe(false);
    expect(
      await compatiblePrecomputed({
        layout: { view: "other" },
      } as unknown as Pick<SiteDocumentBundle, "layout">),
    ).toBe(false);
  });
});
