import { parentPort, workerData } from "node:worker_threads";
import ELK from "elkjs";
import { graphInput, positions } from "./layout.mjs";
const elk = new ELK();
try {
  const { nodes, edges, chapters, mode } = workerData;
  parentPort.postMessage({
    positions: positions(
      await elk.layout(graphInput(nodes, edges, chapters, mode)),
    ),
  });
} catch (error) {
  parentPort.postMessage({ error: String(error) });
}
