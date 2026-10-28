// @vitest-environment node
import { expect, it } from "vitest";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import en from "../i18n/en.json";
const root = path.resolve(import.meta.dirname, "..");
it("keeps every literal UI key present and every non-enum key used", async () => {
  const files = (await readdir(root, { recursive: true })).filter(
    (file) =>
      /\.(tsx?|mjs)$/.test(file) &&
      !file.includes("test/") &&
      !file.endsWith(".test.ts"),
  );
  const used = new Set<string>();
  for (const file of files) {
    const text = await readFile(path.join(root, file), "utf8");
    for (const match of text.matchAll(/\bt\(['"]([^'"]+)['"]/g))
      used.add(match[1]);
  }
  expect([...used].filter((key) => !(key in en))).toEqual([]);
  expect(
    Object.keys(en).filter((key) => !key.startsWith("enum.") && !used.has(key)),
  ).toEqual([]);
});
it("covers every schema enum used for display", async () => {
  const schema = JSON.parse(
    await readFile(path.join(root, "../../schema/common.schema.json"), "utf8"),
  );
  for (const name of [
    "HeadlineStatus",
    "Status",
    "DeviationKind",
    "RelationType",
    "ReviewStatus",
    "FidelityStatus",
    "Kind",
    "MathlibRelation",
    "LocalStatus",
  ])
    for (const value of schema.$defs[name].enum)
      expect(en).toHaveProperty(`enum.${name}.${value}`);
});
