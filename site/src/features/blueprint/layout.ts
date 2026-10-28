/** Browser ELK API only; the 1.4 MB engine lives exclusively in its worker asset. */
import ELK, { type ELK as ElkInstance } from "elkjs/lib/elk-api.js";
import {
  graphInput,
  layoutOptions,
  positions,
} from "../../../scripts/layout.mjs";
import { cache, cached } from "../../data/cache";
import type {
  NodeSummary,
  NodeRef,
  Edge,
  SiteDocumentBundle,
} from "../../data/types";
let elk: ElkInstance | undefined;
export async function layout(
  nodes: (NodeSummary | NodeRef)[],
  edges: Edge[],
  chapters: SiteDocumentBundle["chapters"],
  key: string,
  direction: string,
) {
  const options = JSON.stringify({
    view: key,
    ...layoutOptions(nodes.length, "browser", direction),
  });
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(options),
  );
  const optionsHash = [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
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
