import {
  CARD_LAYOUT_VERSION,
  nodeCard,
} from "../src/data/graph/presentation.mjs";

export const LAYOUT_VERSION = "chapter-pages-v1";
export const CHAPTER_PADDING = { top: 56, right: 32, bottom: 32, left: 32 };

/** Shared geometry and algorithm version also invalidate prerender/browser caches. */
export function layoutOptions(count, mode = "browser", direction = "DOWN") {
  return {
    "homalg.layout.version": LAYOUT_VERSION,
    "homalg.card.version": CARD_LAYOUT_VERSION,
    "elk.algorithm": "layered",
    "elk.direction": direction,
    "elk.hierarchyHandling": "SEPARATE_CHILDREN",
    "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
    "elk.layered.nodePlacement.strategy":
      count <= 100 || (mode === "ci" && count <= 1500)
        ? "BRANDES_KOEPF"
        : "SIMPLE",
    "elk.layered.thoroughness": mode === "ci" ? "7" : "1",
    "elk.spacing.nodeNode": "28",
    "elk.spacing.componentComponent": "36",
    "elk.layered.spacing.nodeNodeBetweenLayers": "48",
    "elk.padding": "[top=56,left=32,bottom=32,right=32]",
  };
}

/** Only authored chapter membership groups nodes; unassigned nodes share a neutral tail. */
export function chapterGroups(nodes, edges, chapters) {
  const remaining = new Map(nodes.map((node) => [node.id, node]));
  const groups = [];
  const groupOf = new Map();
  const append = (members, id) => {
    if (!members.length) return;
    const group = { id, nodes: members, edges: [] };
    groups.push(group);
    for (const node of members) groupOf.set(node.id, group);
  };
  chapters.forEach((chapter, index) => {
    const members = [];
    for (const id of chapter.node_ids) {
      const node = remaining.get(id);
      if (node) {
        members.push(node);
        remaining.delete(id);
      }
    }
    append(members, `layout:chapter:${index}`);
  });
  append([...remaining.values()], "layout:unassigned");
  for (const edge of edges) {
    const group = groupOf.get(edge.from);
    if (group && group === groupOf.get(edge.to) && edge.from !== edge.to)
      group.edges.push(edge);
  }
  return groups;
}

/** Shelf-pack chapter rectangles in reading order, choosing a compact landscape extent. */
export function packGroups(groups, aspect = 1.35, gap = 64) {
  if (!groups.length) return [];
  const widest = groups.reduce(
    (width, group) => Math.max(width, group.width),
    0,
  );
  const area = groups.reduce(
    (sum, group) => sum + (group.width + gap) * (group.height + gap),
    0,
  );
  const naturalWidth = Math.sqrt(area * aspect);
  let best;
  for (const factor of [0.65, 0.85, 1, 1.2, 1.5, 2]) {
    const limit = Math.max(widest, naturalWidth * factor);
    const offsets = [];
    let x = 0,
      y = 0,
      rowHeight = 0,
      width = 0;
    for (const group of groups) {
      if (x && x + group.width > limit) {
        x = 0;
        y += rowHeight + gap;
        rowHeight = 0;
      }
      offsets.push({ x, y });
      width = Math.max(width, x + group.width);
      rowHeight = Math.max(rowHeight, group.height);
      x += group.width + gap;
    }
    const height = y + rowHeight;
    const score = Math.max(width / aspect, height);
    if (
      !best ||
      score < best.score ||
      (score === best.score && width * height < best.area)
    )
      best = { offsets, score, area: width * height };
  }
  return best.offsets;
}

/** Lay out each explicit chapter's DAG independently; renderers keep all cross-chapter edges. */
export function graphInput(
  nodes,
  edges,
  chapters,
  mode = "browser",
  direction = "DOWN",
) {
  const groups = chapterGroups(nodes, edges, chapters);
  return {
    id: "root",
    layoutOptions: {
      ...layoutOptions(nodes.length, mode, direction),
      "elk.algorithm": "box",
    },
    children: groups.map((group) => ({
      id: group.id,
      layoutOptions: layoutOptions(group.nodes.length, mode, direction),
      children: group.nodes.map((node) => {
        const { width, height } = nodeCard(node);
        return { id: node.id, width, height };
      }),
      edges: group.edges.map((edge, index) => ({
        id: `${group.id}:edge:${index}`,
        sources: [edge.to],
        targets: [edge.from],
      })),
    })),
    edges: [],
  };
}

/** Convert ELK's corner coordinates to actual card centers and preserve chapter order.
 * @returns {Record<string, {x: number, y: number}>}
 */
export function positions(graph) {
  const children = graph.children || [];
  const grouped = children.some((node) => node.children?.length);
  const offsets = grouped ? packGroups(children) : [];
  const result = {};
  const collect = (node, x = 0, y = 0) => {
    if (node.children?.length) {
      for (const child of node.children)
        collect(child, x + (node.x || 0), y + (node.y || 0));
    } else {
      result[node.id] = {
        x: x + (node.x || 0) + (node.width || 0) / 2,
        y: y + (node.y || 0) + (node.height || 0) / 2,
      };
    }
  };
  children.forEach((node, index) => {
    if (grouped) collect({ ...node, x: offsets[index].x, y: offsets[index].y });
    else collect(node);
  });
  return result;
}
