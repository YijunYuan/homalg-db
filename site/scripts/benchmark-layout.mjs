/** Reproducible 2,000-node browser-option ELK benchmark. Add --chain for a stress case. */
import { Worker } from "node:worker_threads";
const count = 2000,
  stride = process.argv.includes("--chain") ? 1 : 100;
const nodes = Array.from({ length: count }, (_, i) => ({ id: `n${i}` }));
const edges = nodes.flatMap((node, i) =>
  i >= stride ? [{ from: node.id, to: `n${i - stride}` }] : [],
);
const chapters = Array.from({ length: 10 }, (_, i) => ({
  node_ids: nodes.slice(i * 200, i * 200 + 200).map((node) => node.id),
}));
const start = performance.now();
const worker = new Worker(new URL("./layout-worker.mjs", import.meta.url), {
  workerData: { nodes, edges, chapters, mode: "browser" },
});
const result = await new Promise((resolve, reject) => {
  worker.once("message", resolve);
  worker.once("error", reject);
});
await worker.terminate();
if (result.error) throw new Error(result.error);
const elapsed = performance.now() - start;
console.log(
  JSON.stringify({
    nodes: count,
    edges: edges.length,
    scenario: stride === 1 ? "single-chain-stress" : "100-parallel-chains",
    elapsed_ms: Math.round(elapsed),
    budget_ms: 3000,
    within_budget: elapsed < 3000,
  }),
);
if (process.argv.includes("--enforce") && elapsed >= 3000) process.exitCode = 1;
