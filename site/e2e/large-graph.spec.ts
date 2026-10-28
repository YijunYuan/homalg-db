import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";

async function largeDocument(page: Page) {
  const base = new URL("../fixtures/data/", import.meta.url);
  const manifest = JSON.parse(
    await readFile(new URL("manifest.json", base), "utf8"),
  );
  const entry = manifest.documents[0];
  const bundle = JSON.parse(
    await readFile(new URL(entry.files.document, base), "utf8"),
  );
  const sample = bundle.nodes.find(
    (node: { id: string }) => node.id === "Fixture2000.Thm_1",
  );
  bundle.nodes = Array.from({ length: 20_001 }, (_, i) => ({
    ...sample,
    id: `Fixture2000.Thm_${i + 1}`,
    local_id: `Thm_${i + 1}`,
    label: `Theorem ${i + 1}`,
    is_aux: false,
    aux_parent: null,
  }));
  bundle.edges = bundle.nodes
    .slice(1)
    .map((node: { id: string }, i: number) => ({
      from: node.id,
      to: bundle.nodes[i].id,
      kind: "proof",
      verified: true,
      declared: true,
    }));
  bundle.external_nodes = [];
  bundle.chapters = [
    {
      chapter: "1",
      title: "Synthetic stress fixture",
      node_ids: bundle.nodes.map((node: { id: string }) => node.id),
    },
  ];
  bundle.layout = {
    view: "aux-collapsed",
    nodes: Object.fromEntries(
      bundle.nodes.map((node: { id: string }, i: number) => [
        node.id,
        { x: i % 142, y: Math.floor(i / 142) },
      ]),
    ),
  };
  entry.node_counts = { theorem: 20_001 };
  await page.route("**/data/manifest.json", (route) =>
    route.fulfill({ json: manifest }),
  );
  await page.route(`**/data/${entry.files.document}`, (route) =>
    route.fulfill({ json: bundle }),
  );
  await page.addInitScript(() =>
    sessionStorage.setItem("chapters:Fixture2000", "[]"),
  );
}

test("explicit expansion renders every large-graph node and edge in WebGL", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await largeDocument(page);
  await page.goto("/#/doc/Fixture2000");
  const canvas = page.locator('.graph-canvas[data-renderer="webgl"]');
  await expect(canvas).toHaveAttribute("data-ready", "true", {
    timeout: 20_000,
  });
  await expect(canvas).toHaveAttribute("data-visible-nodes", "20001");
  await expect(canvas).toHaveAttribute("data-visible-edges", "20000");
  expect(await canvas.locator("canvas").count()).toBeGreaterThan(0);
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export PNG" }).click();
  expect((await downloaded).suggestedFilename()).toBe("Fixture2000.png");
  await page
    .getByRole("button", { name: "Collapse chapters", exact: true })
    .click();
  await expect(
    page.locator('.graph-canvas:not([data-renderer="webgl"])'),
  ).toHaveAttribute("data-ready", "true");
  await expect(canvas).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("WebGL failure keeps the complete accessible list available", async ({
  page,
}) => {
  await largeDocument(page);
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      ...args
    ) {
      if (String(args[0]).startsWith("webgl")) return null;
      return Reflect.apply(original, this, args);
    } as typeof original;
  });
  await page.goto("/#/doc/Fixture2000");
  await expect(
    page.getByText(
      "WebGL is unavailable. Open the node list or collapse chapters to continue.",
    ),
  ).toBeVisible();
  await page.getByRole("link", { name: "Open accessible node list" }).click();
  await expect(
    page.getByRole("link", { name: "Theorem 1", exact: true }),
  ).toBeVisible();
});
