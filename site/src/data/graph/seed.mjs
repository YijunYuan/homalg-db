/** Linear-time dependency ranks give a complete usable view while ELK refines it.
 * @returns {Record<string, {x: number, y: number}>}
 */
export function seedPositions(nodes, edges, chapters, direction = "DOWN") {
  const ids = new Set(nodes.map((node) => node.id));
  const pending = new Map(nodes.map((node) => [node.id, 0]));
  const users = new Map(nodes.map((node) => [node.id, []]));
  for (const edge of edges)
    if (ids.has(edge.from) && ids.has(edge.to) && edge.from !== edge.to) {
      pending.set(edge.from, pending.get(edge.from) + 1);
      users.get(edge.to).push(edge.from);
    }
  const levels = new Map(nodes.map((node) => [node.id, 0]));
  const ready = nodes
    .filter((node) => pending.get(node.id) === 0)
    .map((node) => node.id);
  for (let i = 0; i < ready.length; i++)
    for (const id of users.get(ready[i])) {
      levels.set(id, Math.max(levels.get(id), levels.get(ready[i]) + 1));
      pending.set(id, pending.get(id) - 1);
      if (pending.get(id) === 0) ready.push(id);
    }
  const chapterOf = new Map(
    chapters.flatMap((chapter, i) => chapter.node_ids.map((id) => [id, i])),
  );
  const buckets = new Map();
  for (const node of nodes) {
    const chapter = chapterOf.get(node.id) ?? chapters.length;
    const level = pending.get(node.id)
      ? Math.max(0, node.rank || 0)
      : levels.get(node.id);
    const key = `${chapter}:${level}`;
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(node.id);
  }
  const widths = Array.from({ length: chapters.length + 1 }, () => 280);
  for (const [key, ids] of buckets)
    widths[Number(key.split(":")[0])] = Math.max(
      widths[Number(key.split(":")[0])],
      ids.length * 240 + 40,
    );
  const offsets = widths.map((_, i) =>
    widths.slice(0, i).reduce((sum, width) => sum + width, 0),
  );
  const result = {};
  for (const [key, ids] of buckets) {
    const [chapter, level] = key.split(":").map(Number);
    ids.forEach((id, i) => {
      const point = {
        x: offsets[chapter] + 130 + i * 240,
        y: 80 + level * 140,
      };
      result[id] = direction === "RIGHT" ? { x: point.y, y: point.x } : point;
    });
  }
  return result;
}
