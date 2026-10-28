/** Traverse lazily loaded records with a bounded, deterministic breadth-first search. */
import type { DataSource, Direction, NeighborEdges } from "../source";
import type { Edge } from "../types";
export async function neighbors(
  source: Pick<DataSource, "document" | "node">,
  id: string,
  direction: Direction,
  depth: number,
): Promise<NeighborEdges> {
  const seen = new Set([id]);
  const edges = new Map<string, Edge>();
  let frontier = [id],
    truncated = false;
  for (let level = 0; level < Math.min(3, Math.max(1, depth)); level++) {
    const next: string[] = [];
    for (const current of frontier) {
      const record = await source.node(current);
      const targets =
        direction === "up"
          ? [
              ...record.dependencies.statement,
              ...record.dependencies.proof,
            ].map((node) => node.id)
          : record.dependents.map((node) => node.id);
      const documents = new Map<
        string,
        Awaited<ReturnType<DataSource["document"]>>
      >();
      for (const target of targets) {
        if (seen.size >= 500 && !seen.has(target)) {
          truncated = true;
          continue;
        }
        const from = direction === "up" ? current : target,
          to = direction === "up" ? target : current;
        const doc = from.split(".")[0];
        if (!documents.has(doc)) documents.set(doc, await source.document(doc));
        const edge = documents
          .get(doc)!
          .edges.find((item) => item.from === from && item.to === to);
        if (edge) edges.set(`${from}:${to}`, edge);
        if (!seen.has(target)) {
          seen.add(target);
          next.push(target);
        }
      }
    }
    frontier = next;
  }
  const result: NeighborEdges = [...edges.values()];
  result.truncated = truncated;
  return result;
}
