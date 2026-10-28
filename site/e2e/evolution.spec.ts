import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";
import path from "node:path";
const data = path.resolve(import.meta.dirname, "../fixtures/data");
const json = async (file: string) =>
  JSON.parse(await readFile(path.join(data, file), "utf8"));

test("isolates proposed relations and renders versioned evolution evidence", async ({
  page,
}) => {
  const manifest = await json("manifest.json");
  const graph = await json(manifest.global_graph_file);
  const taxonomy = await json("taxonomy.json");
  const second = await json("nodes/Fixture2001/Def_1.json");
  const lane = graph.concepts.find(
    (item: { id: string }) => item.id === "chain-complex",
  );
  lane.lanes.push({
    doc: "Fixture2001",
    year: 2001,
    uses_count: 1,
    defines: [
      {
        id: second.summary.id,
        doc: "Fixture2001",
        label: second.summary.label,
        headline: second.summary.headline,
        status: second.summary.status,
        x: 240120,
        y: 0,
      },
    ],
  });
  lane.arcs.push({
    type: "reformulates",
    source: second.summary.id,
    target: "Fixture2000.Def_1",
    review_status: "unreviewed",
  });
  graph.document_edges[0].relations.unreviewed = 1;
  taxonomy.relations.push({
    id: "rel-fixture",
    type: "reformulates",
    source: second.summary.id,
    target: "Fixture2000.Def_1",
    review: { status: "unreviewed" },
    provenance: { by: "llm", on: "2001-01-02" },
  });
  await page.route(`**/data/${manifest.global_graph_file}`, (route) =>
    route.fulfill({ json: graph }),
  );
  await page.route("**/data/taxonomy.json", (route) =>
    route.fulfill({ json: taxonomy }),
  );
  await page.route("**/data/evolution/chain-complex.json", (route) =>
    route.fulfill({
      json: {
        concept: "chain-complex",
        current_bundle_sha256: "0".repeat(64),
        summaries: [
          {
            version: 1,
            stale: true,
            narrative_md:
              "Synthetic comparison of `Fixture2000.Def_1` and `Fixture2001.Def_1`.",
            stages: [
              {
                period: "2001",
                doc: "Fixture2001",
                nodes: [second.summary.id],
                change: "A synthetic second definition.",
              },
            ],
            proposed_relations: [],
            proposed_aliases: ["synthetic complex"],
            open_questions: ["Does the synthetic construction extend?"],
            provenance: {
              by: "llm",
              model: "offline-fixture",
              provider: "fixture",
              on: "2001-01-02",
              prompt_version: 1,
              bundle_commit: "fixture",
              bundle_sha256: "1".repeat(64),
              usage: { input_tokens: 100, output_tokens: 50 },
              cost_usd: 0.001,
              max_cost_usd: 1,
            },
            review: { status: "unreviewed" },
          },
        ],
      },
    }),
  );
  await page.goto("/#/concepts/chain-complex");
  await expect(page.locator(".definition-comparison")).toHaveCount(2);
  await expect(
    page.locator(".definition-comparison").first().locator(".lean-code"),
  ).toBeVisible();
  await expect(page.locator(".relation-arc")).toHaveCount(0);
  await expect(page.locator(".evolution-summary")).toContainText(
    "offline-fixture",
  );
  await expect(page.locator(".evolution-summary")).toContainText(
    "Stale: inputs changed since 2001-01-02",
  );
  await expect(page.locator(".evolution-summary")).toContainText(
    "Does the synthetic construction extend?",
  );
  await page
    .getByRole("checkbox", { name: "Show unreviewed relations" })
    .check();
  await expect(
    page.locator('.relation-arc[data-review="unreviewed"]'),
  ).toHaveAttribute("stroke-dasharray", "6 5");
  const audit = await new AxeBuilder({ page }).analyze();
  expect(
    audit.violations.filter((issue) =>
      ["serious", "critical"].includes(issue.impact || ""),
    ),
  ).toEqual([]);
  await page.goto("/#/timeline");
  await expect(page.locator(".relation-arc")).toHaveCount(0);
  await page
    .getByRole("checkbox", { name: "Show unreviewed relations" })
    .check();
  await expect(page.locator(".relation-arc")).toHaveCount(1);
  await page.getByRole("tab", { name: "Document graph", exact: true }).click();
  await page.getByRole("button", { name: /Fixture2001.*Fixture2000/ }).click();
  await expect(page.locator(".document-graph .relation-list")).toContainText(
    "Fixture2001.Def_1",
  );
  await page.getByRole("tab", { name: "Table", exact: true }).click();
  await page.getByLabel("Compare concepts").selectOption(["chain-complex"]);
  await expect(page.locator("table tbody tr")).toHaveCount(1);
});
