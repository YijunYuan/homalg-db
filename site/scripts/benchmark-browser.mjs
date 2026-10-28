/** Measure actual browser paint with 2k precomputed nodes and optional 100k API data. */
import { chromium } from "playwright";
import { createHash } from "node:crypto";
import { layoutOptions } from "./layout.mjs";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { Worker } from "node:worker_threads";
import { createServer } from "node:http";
import { gzipSync } from "node:zlib";
import path from "node:path";
const site = path.resolve(import.meta.dirname, "..");
const fixtures = path.join(site, "fixtures/data");
const json = async (file) =>
  JSON.parse(await readFile(path.join(fixtures, file), "utf8"));
const api = process.argv.find((arg) => arg.startsWith("--api="))?.slice(6);
const overrides = new Map();
const server = createServer(async (request, response) => {
  try {
    const route = decodeURIComponent(
      new URL(request.url, "http://localhost").pathname,
    );
    const data = route.startsWith("/data/");
    const base = data ? fixtures : path.join(site, "dist");
    const file = path.resolve(
      base,
      data ? route.slice(6) : route === "/" ? "index.html" : route.slice(1),
    );
    if (!file.startsWith(base + path.sep)) {
      response.writeHead(404).end();
      return;
    }
    const body = overrides.get(route) || (await readFile(file));
    const mime =
      {
        ".html": "text/html",
        ".js": "text/javascript",
        ".css": "text/css",
        ".json": "application/json",
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".ttf": "font/ttf",
      }[path.extname(file)] || "application/octet-stream";
    response.writeHead(200, {
      "Content-Type": mime,
      "Content-Encoding": "gzip",
      "Cache-Control": "no-cache",
    });
    response.end(gzipSync(body));
  } catch {
    response.writeHead(404).end();
  }
});
await new Promise((resolve, reject) => {
  server.once("error", reject);
  server.listen(4181, "127.0.0.1", resolve);
});
const browser = await chromium.launch();
const report = {
  measured_at: new Date().toISOString(),
  browser: browser.version(),
  static: [],
  api: [],
};
try {
  const manifest = await json("manifest.json");
  const entry = manifest.documents[0];
  const bundle = await json(entry.files.document);
  const prototype = bundle.nodes.find((node) => node.local_id === "Thm_1");
  bundle.nodes = Array.from({ length: 2000 }, (_, i) => ({
    ...prototype,
    id: `${entry.doc_key}.Thm_${i + 1}`,
    local_id: `Thm_${i + 1}`,
    label: `Theorem ${i + 1}`,
    is_aux: false,
    rank: Math.floor(i / 100),
  }));
  bundle.edges = bundle.nodes.flatMap((node, i) =>
    i >= 100
      ? [
          {
            from: node.id,
            to: bundle.nodes[i - 100].id,
            kind: "proof",
            declared: true,
            verified: true,
          },
        ]
      : [],
  );
  bundle.external_nodes = [];
  bundle.chapters = Array.from({ length: 10 }, (_, i) => ({
    chapter: String(i + 1),
    title: `Synthetic chapter ${i + 1}`,
    sections: [],
    node_ids: bundle.nodes.slice(i * 200, i * 200 + 200).map((node) => node.id),
  }));
  const worker = new Worker(new URL("./layout-worker.mjs", import.meta.url), {
    workerData: {
      nodes: bundle.nodes,
      edges: bundle.edges,
      chapters: bundle.chapters,
      mode: "ci",
    },
  });
  const positions = await new Promise((resolve, reject) => {
    worker.once("message", resolve);
    worker.once("error", reject);
  });
  await worker.terminate();
  if (positions.error) throw new Error(positions.error);
  bundle.layout = {
    view: "aux-collapsed",
    options_hash: createHash("sha256")
      .update(
        JSON.stringify({ view: "aux-collapsed", ...layoutOptions(2000, "ci") }),
      )
      .digest("hex")
      .slice(0, 16),
    nodes: positions.positions,
  };
  entry.items_total = 2000;
  entry.node_counts = { ...entry.node_counts, proved: 2000 };
  overrides.set("/data/manifest.json", Buffer.from(JSON.stringify(manifest)));
  overrides.set(
    `/data/${entry.files.document}`,
    Buffer.from(JSON.stringify(bundle)),
  );
  for (const expanded of [false, true]) {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1000 },
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    if (expanded)
      await page.addInitScript(
        (key) => sessionStorage.setItem(`chapters:${key}`, "[]"),
        entry.doc_key,
      );
    await page.goto(`http://127.0.0.1:4181/#/doc/${entry.doc_key}`, {
      waitUntil: "domcontentloaded",
    });
    await page.locator('.graph-canvas[data-ready="true"]').waitFor();
    const measured = await page
      .locator(".graph-canvas")
      .evaluate((element) => ({
        navigation_to_paint_ms: Math.round(Number(element.dataset.readyAt)),
        visible_nodes: Number(element.dataset.visibleNodes),
        profile: JSON.parse(element.dataset.profile || "{}"),
        document_response_end_ms: Math.round(
          performance
            .getEntriesByType("resource")
            .filter((entry) => entry.name.includes("/data/documents/"))
            .at(-1)?.responseEnd || 0,
        ),
      }));
    report.static.push({
      nodes: 2000,
      view: expanded ? "expanded" : "default-chapter-collapse",
      ...measured,
      budget_ms: 500,
      within_budget: measured.navigation_to_paint_ms < 500,
    });
    await context.close();
  }
  if (api) {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1000 },
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    await page.goto(
      `http://127.0.0.1:4181/?source=api&api=${encodeURIComponent(api)}#/doc/Benchmark2000`,
      { waitUntil: "domcontentloaded" },
    );
    await page
      .getByRole("heading", { name: "Chapter overview", exact: true })
      .waitFor();
    const overview = await page.evaluate(() => performance.now());
    report.api.push({
      nodes: 100000,
      view: "chapter-overview",
      navigation_to_ready_ms: Math.round(overview),
      budget_ms: 1000,
      within_budget: overview < 1000,
    });
    const start = await page.evaluate(() => performance.now());
    await page.locator(".chapter-cards button").first().click();
    await page
      .locator('.graph-canvas[data-ready="true"]')
      .waitFor({ timeout: 60000 });
    const detail = await page.locator(".graph-canvas").evaluate((element) => ({
      paint: Number(element.dataset.readyAt),
      profile: JSON.parse(element.dataset.profile || "{}"),
      requests: performance
        .getEntriesByType("resource")
        .filter((entry) => entry.name.includes("/api/documents/"))
        .map((entry) => ({
          name: entry.name.split("?")[1] || "all",
          start: entry.startTime,
          end: entry.responseEnd,
        })),
    }));
    const paint = detail.paint;
    report.api.push({
      nodes: 1000,
      view: "selected-chapter",
      action_to_paint_ms: Math.round(paint - start),
      action_at: start,
      profile: detail.profile,
      requests: detail.requests,
      budget_ms: 1000,
      within_budget: paint - start < 1000,
    });
    await context.close();
  }
  await mkdir(path.join(site, "../build"), { recursive: true });
  await writeFile(
    path.join(site, "../build/browser-benchmark.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  console.log(JSON.stringify(report, null, 2));
  if (
    process.argv.includes("--enforce") &&
    (!report.static[0].within_budget ||
      report.api.some((item) => !item.within_budget))
  )
    process.exitCode = 1;
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
