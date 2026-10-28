/** Contract auxiliary nodes while retaining every projected dependency edge. */
export function contractAux(nodes, edges, collapsedSet) {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const parent = (id) => {
    const via = [],
      seen = new Set();
    while (collapsedSet.has(id) && byId.get(id)?.aux_parent) {
      if (seen.has(id)) throw new Error(`Auxiliary parent cycle at ${id}`);
      seen.add(id);
      via.push(id);
      id = byId.get(id).aux_parent;
    }
    return { id, via };
  };
  const result = new Map();
  for (const edge of edges) {
    const from = parent(edge.from),
      to = parent(edge.to);
    if (from.id === to.id) continue;
    const key = `${from.id}\0${to.id}`,
      old = result.get(key);
    const via = [
      ...new Set([
        ...(old?.via || []),
        ...(edge.via || []),
        ...from.via,
        ...to.via,
      ]),
    ].sort();
    result.set(key, {
      from: from.id,
      to: to.id,
      kind:
        old?.kind === "statement" || edge.kind === "statement"
          ? "statement"
          : "proof",
      declared: !!(old?.declared || edge.declared),
      verified: !!(old?.verified || edge.verified),
      ...(via.length ? { via } : {}),
    });
  }
  return [...result.values()].sort(
    (a, b) => a.from.localeCompare(b.from) || a.to.localeCompare(b.to),
  );
}
export function defaultCollapsed(nodes) {
  return new Set(
    nodes
      .filter(
        (node) => node.is_aux && node.aux_kind !== "bridge" && node.aux_parent,
      )
      .map((node) => node.id),
  );
}
export function toMermaid(nodes, edges) {
  const ids = new Map(nodes.map((node, i) => [node.id, `n${i}`]));
  const safe = (text) =>
    String(text)
      .replaceAll("&", "&amp;")
      .replaceAll('"', "&quot;")
      .replace(/[\r\n]/g, " ");
  return [
    "flowchart TD",
    ...nodes.map((node) => `  ${ids.get(node.id)}["${safe(node.label)}"]`),
    ...edges
      .filter((edge) => ids.has(edge.from) && ids.has(edge.to))
      .map(
        (edge) =>
          `  ${ids.get(edge.to)} ${edge.verified ? "-->" : "-.->"} ${ids.get(edge.from)}`,
      ),
  ].join("\n");
}

/** Merge dependency edges projected onto the same visible chapter pair. */
export function aggregateEdges(edges) {
  const grouped = new Map();
  for (const edge of edges) {
    if (edge.from === edge.to) continue;
    const key = `${edge.from}\0${edge.to}`;
    const old = grouped.get(key);
    const via = [...new Set([...(old?.via || []), ...(edge.via || [])])].sort();
    grouped.set(key, {
      from: edge.from,
      to: edge.to,
      kind:
        old?.kind === "statement" || edge.kind === "statement"
          ? "statement"
          : "proof",
      declared: !!(old?.declared || edge.declared),
      verified: !!(old?.verified || edge.verified),
      aggregate_count:
        (old?.aggregate_count || 0) + (edge.aggregate_count || 1),
      ...(via.length ? { via } : {}),
    });
  }
  return [...grouped.values()];
}
