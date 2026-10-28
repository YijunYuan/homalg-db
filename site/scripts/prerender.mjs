/** Enrich generated site data with highlighting, search, layouts and diagnostics. */
import { readFile, writeFile, readdir, rename, mkdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import { Worker } from "node:worker_threads";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHighlighter } from "shiki";
import MiniSearch from "minisearch";
import { INDEX_OPTIONS } from "../src/data/search/options.mjs";
import { contractAux, defaultCollapsed } from "../src/data/graph/contract.mjs";
import { markdownProcessor } from "../src/components/markdown/pipeline.mjs";
import { layoutOptions } from "./layout.mjs";
const scripts = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2),
  dataArg = args.indexOf("--data");
if (dataArg < 0 || !args[dataArg + 1])
  throw new Error(
    "Usage: prerender.mjs --data <directory> [--skip shiki,search,layout,markdown]",
  );
const directory = path.resolve(args[dataArg + 1]);
const skip = new Set(
  (args[args.indexOf("--skip") + 1] && args.includes("--skip")
    ? args[args.indexOf("--skip") + 1]
    : ""
  ).split(","),
);
const read = async (file) =>
  JSON.parse(await readFile(path.join(directory, file), "utf8"));
const canonical = (value) =>
  Array.isArray(value)
    ? value.map(canonical)
    : value && typeof value === "object"
      ? Object.fromEntries(
          Object.entries(value)
            .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
            .map(([key, item]) => [key, canonical(item)]),
        )
      : value;
const write = async (file, value) => {
  const destination = path.join(directory, file),
    temporary = `${destination}.${process.pid}.tmp`;
  await writeFile(temporary, JSON.stringify(canonical(value), null, 2) + "\n");
  await rename(temporary, destination);
};
const hash = (value) => createHash("sha256").update(value).digest("hex");
const manifest = await read("manifest.json");
const generatedIndex = await read(manifest.index_file);
const activeIds = new Set(generatedIndex.nodes.map((node) => node.id));
const files = (
  await readdir(path.join(directory, "nodes"), { recursive: true })
)
  .filter(
    (file) =>
      file.endsWith(".json") &&
      activeIds.has(file.replaceAll(path.sep, ".").slice(0, -5)),
  )
  .sort();
const records = await Promise.all(files.map((file) => read(`nodes/${file}`)));
const nodeIds = new Set(records.map((record) => record.summary.id));
const health = { markdown_findings: [], per_doc: {} };
for (const doc of manifest.documents)
  health.per_doc[doc.doc_key] = {
    markdown_findings: 0,
    deps_mismatch: 0,
    needs_repair: 0,
    disputed: 0,
  };
const highlighter = skip.has("shiki")
  ? null
  : await createHighlighter({
      themes: ["github-light", "github-dark"],
      langs: ["lean"],
    });
const highlight = (source) =>
  highlighter.codeToHtml(source, {
    lang: "lean",
    themes: { light: "github-light", dark: "github-dark" },
    defaultColor: false,
  });
const processor = markdownProcessor({ nodeIds });
function checkMarkdown(where, field, text, doc) {
  if (skip.has("markdown") || !text) return;
  const file = processor.processSync(text);
  for (const message of file.messages) {
    const rule =
      message.source === "rehype-katex" && message.ruleId === "parseerror"
        ? "katex-parse-error"
        : message.ruleId || "markdown";
    health.markdown_findings.push({
      where,
      field,
      rule,
      message: message.reason,
    });
    if (doc) health.per_doc[doc].markdown_findings++;
  }
}
for (let i = 0; i < records.length; i++) {
  const record = records[i];
  if (highlighter) {
    record.lean.signature_html = highlight(
      record.derived.decl_info
        .filter((decl) => record.authored.decls?.includes(decl.name))
        .map((decl) => `${decl.name} : ${decl.type}`)
        .join("\n\n"),
    );
    record.lean.source_html = highlight(record.lean.source_text);
  }
  for (const [field, text] of Object.entries(record.authored))
    if (field.endsWith("_md") && typeof text === "string")
      checkMarkdown(record.summary.id, field, text, record.summary.doc);
  for (const field of ["deps_mismatch", "needs_repair", "disputed"])
    if (record.summary[field]) health.per_doc[record.summary.doc][field]++;
  await write(`nodes/${files[i]}`, record);
}
highlighter?.dispose();
const evolutionFiles = await readdir(path.join(directory, "evolution")).catch(
  (error) => (error.code === "ENOENT" ? [] : Promise.reject(error)),
);
const activeEvolution = new Set(
  generatedIndex.evolution.map((item) => `${item.concept}.json`),
);
for (const file of evolutionFiles.filter((file) => activeEvolution.has(file))) {
  const evolution = await read(`evolution/${file}`);
  for (const summary of evolution.summaries)
    checkMarkdown(evolution.concept, "narrative_md", summary.narrative_md);
}
if (!skip.has("search")) {
  const thresholdNodes = Number(process.env.HOMALG_SEARCH_SHARD_NODES || 50000);
  const thresholdBytes = Number(
    process.env.HOMALG_SEARCH_SHARD_BYTES || 30000000,
  );
  const shards = await Promise.all(
    manifest.documents.map(async (doc) => ({
      doc,
      records: await read(doc.files.search_shard),
    })),
  );
  const optionsHash = hash(
    await readFile(path.join(scripts, "../src/data/search/options.mjs")),
  ).slice(0, 16);
  let partitioned =
    shards.reduce((sum, shard) => sum + shard.records.length, 0) >
    thresholdNodes;
  let serialized;
  if (!partitioned) {
    const index = new MiniSearch(INDEX_OPTIONS);
    await index.addAllAsync(shards.flatMap((shard) => shard.records));
    serialized = index.toJSON();
    partitioned =
      Buffer.byteLength(JSON.stringify(serialized)) > thresholdBytes;
  }
  for (const { doc } of shards) delete doc.files.search_index;
  delete manifest.search_index_file;
  if (partitioned) {
    await mkdir(path.join(directory, "search-index"), { recursive: true });
    for (const { doc, records } of shards) {
      const index = new MiniSearch(INDEX_OPTIONS);
      await index.addAllAsync(records);
      const shardHash =
        doc.files.search_shard.match(/\.([a-f0-9]{16})\.json$/)?.[1] ||
        hash(JSON.stringify(records)).slice(0, 16);
      doc.files.search_index = `search-index/${doc.doc_key}.${shardHash}.${optionsHash}.json`;
      await write(doc.files.search_index, index.toJSON());
    }
  } else {
    manifest.search_index_file = `search-index.${manifest.search_hash}.json`;
    await write(manifest.search_index_file, serialized);
  }
}

async function computeLayout(bundle, mode) {
  const collapsed = defaultCollapsed(bundle.nodes),
    edges = contractAux(bundle.nodes, bundle.edges, collapsed);
  const nodes = [
    ...bundle.nodes.filter((node) => !collapsed.has(node.id)),
    ...bundle.external_nodes,
  ];
  return new Promise((resolve) => {
    const worker = new Worker(new URL("./layout-worker.mjs", import.meta.url), {
      workerData: { nodes, edges, chapters: bundle.chapters, mode },
    });
    const timeout = setTimeout(
      () => {
        void worker.terminate();
        resolve(null);
      },
      Number(process.env.HOMALG_LAYOUT_TIMEOUT_MS || 180000),
    );
    const end = (result) => {
      clearTimeout(timeout);
      void worker.terminate();
      resolve(result);
    };
    worker.once("message", (result) =>
      end(result.error ? null : result.positions),
    );
    worker.once("error", () => end(null));
  });
}
const failures = [];
if (!skip.has("layout"))
  for (const doc of manifest.documents) {
    const bundle = await read(doc.files.document);
    let mode = "ci",
      nodes = await computeLayout(bundle, mode);
    if (!nodes) {
      mode = "browser";
      nodes = await computeLayout(bundle, mode);
    }
    bundle.layout = nodes
      ? {
          view: "aux-collapsed",
          nodes,
          options_hash: hash(
            JSON.stringify({
              view: "aux-collapsed",
              ...layoutOptions(Object.keys(nodes).length, mode),
            }),
          ).slice(0, 16),
        }
      : null;
    if (!nodes) failures.push(doc.doc_key);
    await write(doc.files.document, bundle);
  }
manifest.prerender = {
  shiki: !skip.has("shiki"),
  search_index: !skip.has("search"),
  layout: !skip.has("layout"),
  search_options_hash: hash(
    await readFile(path.join(scripts, "../src/data/search/options.mjs")),
  ),
  ...(failures.length ? { layout_failed: failures } : {}),
};
manifest.health.markdown_findings = health.markdown_findings.length;
await write("health.json", health);
await write("manifest.json", manifest);
console.log(
  `Prerendered ${records.length} nodes; ${failures.length} layout fallbacks; ${health.markdown_findings.length} Markdown findings.`,
);
