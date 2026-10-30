/** Browser ELK API only; the 1.4 MB engine lives exclusively in its worker asset. */
import ELK, { type ELK as ElkInstance } from "elkjs/lib/elk-api.js";
import {
  graphInput,
  layoutOptions,
  positions,
} from "../../../scripts/layout.mjs";
import { cache, cached } from "../../data/cache";
import { nodeCard } from "../../data/graph/presentation.mjs";
import type {
  NodeSummary,
  NodeRef,
  Edge,
  SiteDocumentBundle,
} from "../../data/types";
let elk: ElkInstance | undefined;
/** Match only current geometry/algorithm versions, including the CI retry mode. */
export async function compatiblePrecomputed(
  bundle: Pick<SiteDocumentBundle, "layout">,
): Promise<boolean> {
  if (bundle.layout?.view !== "aux-collapsed") return false;
  const count = Object.keys(bundle.layout.nodes).length;
  for (const mode of ["ci", "browser"])
    if (
      bundle.layout.options_hash ===
      (await optionsDigest({
        view: "aux-collapsed",
        ...layoutOptions(count, mode),
      }))
    )
      return true;
  return false;
}

/** Use the same truncated SHA-256 representation as prerendered options hashes. */
async function optionsDigest(options: unknown): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(JSON.stringify(options)),
  );
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
}

/** Recompute chapter-local positions only when graph topology or actual card sizes change. */
export async function layout(
  nodes: (NodeSummary | NodeRef)[],
  edges: Edge[],
  chapters: SiteDocumentBundle["chapters"],
  key: string,
  direction: string,
) {
  const optionsHash = await optionsDigest({
    view: key,
    ...layoutOptions(nodes.length, "browser", direction),
    geometry: nodes.map((node) => {
      const { width, height } = nodeCard(node);
      return [node.id, width, height];
    }),
    chapters: chapters.map((chapter) => chapter.node_ids),
    dependencies: edges.map((edge) => [edge.from, edge.to]),
  });
  const cacheKey = `layout:${key.split(":").slice(0, 2).join(":")}:${optionsHash}`;
  const stored =
    await cached<Record<string, { x: number; y: number }>>(cacheKey);
  if (stored) return stored;
  elk ??= new ELK({
    workerFactory: () =>
      new Worker(new URL("elkjs/lib/elk-worker.min.js", import.meta.url)),
  });
  const result = positions(
    await elk.layout(graphInput(nodes, edges, chapters, "browser", direction)),
  );
  void cache(cacheKey, result);
  return result as Record<string, { x: number; y: number }>;
}
