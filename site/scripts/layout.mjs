/** Shared flat ELK graph and partition options; chapters remain in reading order. */
export function layoutOptions(count, mode = "browser", direction = "DOWN") {
  return {
    "elk.algorithm": "layered",
    "elk.direction": direction,
    "elk.partitioning.activate": "true",
    "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
    "elk.layered.nodePlacement.strategy":
      mode === "ci" && count <= 1500 ? "BRANDES_KOEPF" : "SIMPLE",
    "elk.layered.thoroughness": mode === "ci" ? "7" : "1",
    "elk.spacing.nodeNode": "36",
    "elk.layered.spacing.nodeNodeBetweenLayers": "68",
  };
}
export function graphInput(
  nodes,
  edges,
  chapters,
  mode = "browser",
  direction = "DOWN",
) {
  const partitions = new Map();
  chapters.forEach((chapter, i) =>
    chapter.node_ids.forEach((id) => partitions.set(id, i + 1)),
  );
  const ids = new Set(nodes.map((node) => node.id));
  return {
    id: "root",
    layoutOptions: layoutOptions(nodes.length, mode, direction),
    children: nodes.map((node) => ({
      id: node.id,
      width: 204,
      height: 70,
      layoutOptions: {
        "elk.partitioning.partition": String(partitions.get(node.id) ?? 0),
      },
    })),
    edges: edges
      .filter((edge) => ids.has(edge.from) && ids.has(edge.to))
      .map((edge, i) => ({
        id: `e${i}`,
        sources: [edge.to],
        targets: [edge.from],
      })),
  };
}
export function positions(graph) {
  return Object.fromEntries(
    (graph.children || []).map((node) => [
      node.id,
      { x: (node.x || 0) + 102, y: (node.y || 0) + 35 },
    ]),
  );
}
