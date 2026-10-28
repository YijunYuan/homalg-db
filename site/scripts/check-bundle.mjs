/** Enforce the documented compressed-JS and deployment-size budgets. */
import { readFile, readdir, stat } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import path from "node:path";
import { execFileSync } from "node:child_process";
const site = path.resolve(import.meta.dirname, ".."),
  dist = path.join(site, "dist");
const manifest = JSON.parse(
  await readFile(path.join(dist, ".vite/manifest.json"), "utf8"),
);
const budgets = JSON.parse(
  await readFile(path.join(site, "budgets.json"), "utf8"),
);
const all = (await readdir(dist, { recursive: true })).sort();
let size = 0;
for (const file of all) {
  const info = await stat(path.join(dist, file));
  if (info.isFile()) size += info.size;
}
if (size > budgets.site_bytes) throw new Error(`Site budget exceeded: ${size}`);
const entries = Object.values(manifest).filter((item) => item.isEntry);
const reachable = new Set();
function visit(name) {
  if (reachable.has(name)) return;
  reachable.add(name);
  for (const next of manifest[name]?.imports || []) visit(next);
}
for (const [name, item] of Object.entries(manifest))
  if (item.isEntry) visit(name);
let entryBytes = 0;
for (const name of reachable) {
  const item = manifest[name];
  if (item?.file.endsWith(".js"))
    entryBytes += gzipSync(await readFile(path.join(dist, item.file))).length;
}
if (entryBytes > budgets.entry_gzip_bytes)
  throw new Error(`Entry JS exceeds gzip budget: ${entryBytes}`);
for (const item of Object.values(manifest).filter(
  (item) => item.isDynamicEntry,
)) {
  const bytes = gzipSync(await readFile(path.join(dist, item.file))).length;
  if (bytes > budgets.route_gzip_bytes)
    throw new Error(`Route gzip budget exceeded: ${item.file} (${bytes})`);
}
const workers = all.filter((file) => /elk-worker.*\.js$/.test(file));
if (workers.length !== 1)
  throw new Error(`Expected one isolated ELK worker, found ${workers.length}`);
for (const item of Object.values(manifest))
  if (item.file.endsWith(".js")) {
    const text = await readFile(path.join(dist, item.file), "utf8");
    if (
      text.includes("org.eclipse.elk") ||
      text.includes("org.eclipse.elk.alg")
    )
      throw new Error(`ELK implementation leaked into ${item.file}`);
  }
const tree = JSON.parse(
  execFileSync("npm", ["ls", "katex", "--all", "--json"], {
    cwd: site,
    encoding: "utf8",
  }),
);
const versions = new Set();
function scan(value) {
  for (const [key, item] of Object.entries(value.dependencies || {})) {
    if (key === "katex") versions.add(item.version);
    scan(item);
  }
}
scan(tree);
if (versions.size !== 1)
  throw new Error(
    `Expected one KaTeX version, found ${[...versions].join(", ")}`,
  );
console.log(
  `Bundle budgets passed: ${(entryBytes / 1024).toFixed(1)} KiB entry gzip, ${workers.length} ELK worker, KaTeX ${[...versions][0]}, ${(size / 1024 / 1024).toFixed(1)} MiB site.`,
);
