import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";
import type { Core, NodeSingular } from "cytoscape";
import type { DocumentBundle, Manifest } from "../src/data/source";

const parentId = "Fixture2000.Thm_1";
const auxiliaryId = "Fixture2000.Aux_Thm_1_step";
const bridgeId = "Fixture2000.Bridge_Def_1_mathlib";
const title = "Nonzero derivations of inseparable fields";

/** Public fixture records with a deliberately long title and multi-chapter DAG. */
async function readableDocument(page: Page) {
  const base = new URL("../fixtures/data/", import.meta.url);
  const manifest: Manifest = JSON.parse(
    await readFile(new URL("manifest.json", base), "utf8"),
  );
  const entry = manifest.documents.find(
    (document) => document.doc_key === "Fixture2000",
  )!;
  const bundle: DocumentBundle = JSON.parse(
    await readFile(new URL(entry.files.document, base), "utf8"),
  );
  const sample = bundle.nodes.find((node) => node.id === parentId)!;
  const auxiliary = bundle.nodes.find((node) => node.id === auxiliaryId)!;
  const bridge = bundle.nodes.find((node) => node.id === bridgeId)!;
  const source = Array.from({ length: 12 }, (_, index) => ({
    ...sample,
    id: index ? `Fixture2000.Thm_readability_${index}` : parentId,
    local_id: index ? `Thm_readability_${index}` : "Thm_1",
    label: index ? `Theorem ${index + 1}` : "Lemma 4.1",
    title: index ? `A synthetic dependency result ${index + 1}` : title,
    chapter: index < 6 ? "1" : "2",
    rank: index,
  }));
  bundle.nodes = [
    ...source,
    { ...auxiliary, chapter: "1", aux_parent: parentId },
    {
      ...bridge,
      chapter: "1",
      aux_parent: parentId,
      title: "Compatibility of scalar extension with tensor products",
    },
  ];
  bundle.external_nodes = [];
  bundle.edges = [
    ...source.slice(1).map((node, index) => ({
      from: node.id,
      to: source[index].id,
      kind: "proof" as const,
      declared: true,
      verified: true,
    })),
    {
      from: parentId,
      to: auxiliaryId,
      kind: "proof",
      declared: true,
      verified: true,
    },
    {
      from: bridgeId,
      to: parentId,
      kind: "statement",
      declared: true,
      verified: true,
    },
  ];
  bundle.chapters = ["1", "2"].map((chapter) => ({
    chapter,
    title: `Synthetic chapter ${chapter}`,
    sections: [],
    node_ids: bundle.nodes
      .filter((node) => node.chapter === chapter)
      .map((node) => node.id),
  }));
  // Exercise the actual asynchronous browser layout, not only preset positions.
  bundle.layout = null;
  await page.route("**/data/manifest.json", (route) =>
    route.fulfill({ json: manifest }),
  );
  await page.route(`**/data/${entry.files.document}`, (route) =>
    route.fulfill({ json: bundle }),
  );
}

async function graphState(page: Page, id = parentId) {
  return page.locator(".graph-canvas").evaluate((element, id) => {
    // Read renderer geometry without changing its viewport or emitting fake taps.
    const core = (element as HTMLElement & { _cyreg: { cy: Core } })._cyreg.cy;
    const node = core.getElementById(id);
    return {
      count: core.nodes().not(":parent").length,
      positions: Object.fromEntries(
        core
          .nodes()
          .not(":parent")
          .map((item) => [item.id(), { ...(item as NodeSingular).position() }]),
      ),
      expanded: sessionStorage.getItem("homalg:aux:Fixture2000"),
      zoom: core.zoom(),
      font: Number.parseFloat(node.style("font-size")),
      label: String(node.data("label")),
      shape: node.style("shape"),
      center: { ...node.position() },
      renderedPosition: { ...node.renderedPosition() },
      width: node.width(),
      height: node.height(),
      labelBounds: node.boundingBox({
        includeNodes: false,
        includeEdges: false,
        includeLabels: true,
        includeOverlays: false,
      }),
      renderedBounds: node.renderedBoundingBox({ includeOverlays: false }),
      graphBounds: core.elements().renderedBoundingBox(),
      viewport: {
        width: core.width(),
        height: core.height(),
        containerWidth: element.clientWidth,
      },
      profile: JSON.parse((element as HTMLElement).dataset.profile || "{}"),
    };
  }, id);
}

async function settled(page: Page) {
  await expect(page.locator(".graph-canvas")).toHaveAttribute(
    "data-layout-ready",
    "true",
  );
}

test("keeps only one Blueprint popup open when operated by keyboard", async ({
  page,
}) => {
  await readableDocument(page);
  await page.goto("/#/doc/Fixture2000");
  await settled(page);
  const popups = page.locator(
    ".document-options, .blueprint-legend-disclosure, .graph-menu",
  );
  for (const label of [
    "View options",
    "Legend",
    "Export",
    "Help",
    "View options",
  ]) {
    const toggle = page
      .locator("summary")
      .filter({ hasText: new RegExp(`^${label}$`) });
    await toggle.focus();
    await toggle.press("Enter");
    await expect(toggle.locator("..")).toHaveAttribute("open", "");
    await expect(popups.locator("xpath=self::*[@open]")).toHaveCount(1);
    await expect(toggle).toBeFocused();
  }
});

test("handles arrow keys on an empty filtered Blueprint without navigation or errors", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await readableDocument(page);
  await page.goto("/#/doc/Fixture2000");
  await settled(page);
  const filter = page.getByRole("textbox", {
    name: "Find a node in this document",
    exact: true,
  });
  await filter.fill("no-such-blueprint-node-72916");
  const canvas = page.locator(".graph-canvas");
  await expect(canvas).toHaveAttribute("data-visible-nodes", "0");
  await settled(page);
  const url = page.url();
  await canvas.focus();
  for (const key of ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"])
    await canvas.press(key);
  await expect(page).toHaveURL(url);
  await expect(canvas).toBeFocused();
  expect(errors).toEqual([]);
  await filter.fill("");
  await expect(canvas).not.toHaveAttribute("data-visible-nodes", "0");
  await settled(page);
  expectReadable(await graphState(page));
  expect(errors).toEqual([]);
});

function expectReadable(state: Awaited<ReturnType<typeof graphState>>) {
  expect(state.font * state.zoom).toBeGreaterThanOrEqual(12);
  expect(state.renderedBounds.x1).toBeGreaterThanOrEqual(0);
  expect(state.renderedBounds.y1).toBeGreaterThanOrEqual(0);
  expect(state.renderedBounds.x2).toBeLessThanOrEqual(state.viewport.width);
  expect(state.renderedBounds.y2).toBeLessThanOrEqual(state.viewport.height);
}

test("renders complete wrapped titles at readable scale before and after layout", async ({
  page,
}) => {
  await readableDocument(page);
  await page.goto("/#/doc/Fixture2000");
  await expect(page.locator(".graph-canvas")).toHaveAttribute(
    "data-ready",
    "true",
  );
  expectReadable(await graphState(page));
  await settled(page);
  const state = await graphState(page);
  expectReadable(state);
  expect(state.profile.precomputed).toBe(false);
  expect(state.label.replace(/\s+/g, " ")).toContain(title);
  expect(state.label).not.toContain("Lemma 4.1");
  expect(state.label.split("\n").length).toBeGreaterThanOrEqual(2);
  expect(state.label).not.toContain(title); // The full title actually wraps.
  const visibleCanvasHeight = await page
    .locator(".graph-canvas")
    .evaluate((element) => {
      const box = element.getBoundingClientRect();
      return Math.max(
        0,
        Math.min(innerHeight, box.bottom) - Math.max(0, box.top),
      );
    });
  // The graph must occupy the screen, not only a tall area below the fold.
  expect(visibleCanvasHeight).toBeGreaterThanOrEqual(650);
  expect(state.labelBounds.x1).toBeGreaterThanOrEqual(
    state.center.x - state.width / 2,
  );
  expect(state.labelBounds.x2).toBeLessThanOrEqual(
    state.center.x + state.width / 2,
  );
  expect(state.labelBounds.y1).toBeGreaterThanOrEqual(
    state.center.y - state.height / 2,
  );
  expect(state.labelBounds.y2).toBeLessThanOrEqual(
    state.center.y + state.height / 2,
  );

  const bridge = await graphState(page, bridgeId);
  expect(bridge.shape).toBe("diamond");
  expect(bridge.label.replace(/\s+/g, " ")).toContain(
    "Compatibility of scalar extension with tensor products",
  );
  // A label can fit the bounding rectangle while protruding from a diamond.
  for (const x of [bridge.labelBounds.x1, bridge.labelBounds.x2])
    for (const y of [bridge.labelBounds.y1, bridge.labelBounds.y2])
      expect(
        Math.abs(x - bridge.center.x) / (bridge.width / 2) +
          Math.abs(y - bridge.center.y) / (bridge.height / 2),
      ).toBeLessThanOrEqual(1);
  await page.getByRole("button", { name: "Focus view", exact: true }).click();
  await expect
    .poll(() =>
      page.locator(".graph-canvas").evaluate((element) => {
        const box = element.getBoundingClientRect();
        return Math.min(innerHeight, box.bottom) - Math.max(0, box.top);
      }),
    )
    .toBeGreaterThanOrEqual(850);
  const focused = await graphState(page);
  expectReadable(focused);
  expect(focused.positions).toEqual(state.positions);
  await page.getByRole("button", { name: "Exit focus", exact: true }).click();
});

test("selects an auxiliary parent without expanding or moving the graph", async ({
  page,
}) => {
  await readableDocument(page);
  await page.goto("/#/doc/Fixture2000");
  await settled(page);
  const before = await graphState(page);
  const canvasBounds = (await page.locator(".graph-canvas").boundingBox())!;
  await page.mouse.click(
    canvasBounds.x + before.renderedPosition.x,
    canvasBounds.y + before.renderedPosition.y,
  );
  await expect(page).toHaveURL(/\/node\/Thm_1\?view=blueprint$/);
  await expect(
    page.getByRole("button", { name: "Close details" }),
  ).toBeVisible();
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  );
  await settled(page);
  const selected = await graphState(page);
  expect(selected.count).toBe(before.count);
  expect(selected.positions).toEqual(before.positions);
  expect(selected.expanded).toBe(before.expanded);
  expectReadable(selected);

  await page
    .getByRole("button", {
      name: "Expand this node’s auxiliaries",
      exact: true,
    })
    .click();
  await expect
    .poll(async () => (await graphState(page)).count)
    .toBe(before.count + 1);
  await settled(page);
  const expanded = await graphState(page);
  expect(Object.keys(expanded.positions)).toContain(auxiliaryId);
  expect(JSON.parse(expanded.expanded!)).toEqual([parentId]);
  expectReadable(expanded);

  await page
    .getByRole("button", {
      name: "Collapse this node’s auxiliaries",
      exact: true,
    })
    .click();
  await expect
    .poll(async () => (await graphState(page)).count)
    .toBe(before.count);
  await settled(page);
  await page.getByRole("button", { name: "Close details" }).click();
  await expect(page).toHaveURL(/\/doc\/Fixture2000\?view=blueprint$/);
  await expect
    .poll(async () => {
      const { viewport } = await graphState(page);
      return viewport.width === viewport.containerWidth;
    })
    .toBe(true);
  expect((await graphState(page)).positions).toEqual(before.positions);
});

test("preserves the mobile Blueprint when a node is opened and closed", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await readableDocument(page);
  await page.goto("/#/doc/Fixture2000?view=blueprint");
  await settled(page);
  await page.locator(".graph-canvas").scrollIntoViewIfNeeded();
  const before = await graphState(page);
  const canvasBounds = (await page.locator(".graph-canvas").boundingBox())!;
  await page.mouse.click(
    canvasBounds.x + before.renderedPosition.x,
    canvasBounds.y + before.renderedPosition.y,
  );
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page).toHaveURL(/\/node\/Thm_1\?view=blueprint$/);
  await expect(page.locator(".graph-canvas")).toHaveCount(1);
  await page.getByRole("button", { name: "Close details" }).click();
  await expect(page).toHaveURL(/\/doc\/Fixture2000\?view=blueprint$/);
  await settled(page);
  const after = await graphState(page);
  expect(after.positions).toEqual(before.positions);
  expect(after.expanded).toBe(before.expanded);
  expectReadable(after);
});

test("keeps deep links readable and makes overview an explicit reversible choice", async ({
  page,
}) => {
  await readableDocument(page);
  await page.goto("/#/doc/Fixture2000/node/Thm_1");
  await settled(page);
  expectReadable(await graphState(page));
  await page.getByRole("button", { name: "Fit all", exact: true }).click();
  const overview = await graphState(page);
  expect(overview.font * overview.zoom).toBeLessThan(12);
  expect(overview.graphBounds.x1).toBeGreaterThanOrEqual(0);
  expect(overview.graphBounds.y1).toBeGreaterThanOrEqual(0);
  expect(overview.graphBounds.x2).toBeLessThanOrEqual(overview.viewport.width);
  expect(overview.graphBounds.y2).toBeLessThanOrEqual(overview.viewport.height);
  await page.getByRole("button", { name: "Read labels", exact: true }).click();
  const readable = await graphState(page);
  expectReadable(readable);
  await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  expect((await graphState(page)).zoom).toBeGreaterThan(readable.zoom);
  await page.getByRole("button", { name: "Zoom out", exact: true }).click();
  expect((await graphState(page)).zoom).toBeCloseTo(readable.zoom);
});

for (const theme of ["light", "dark"])
  test(`shows truthful color and shape explanations in the ${theme} theme`, async ({
    page,
  }) => {
    await page.addInitScript(
      (theme) => localStorage.setItem("homalg-theme", theme),
      theme,
    );
    await readableDocument(page);
    await page.goto("/#/doc/Fixture2000");
    await settled(page);
    expect(
      await page
        .locator("html")
        .evaluate((element) => element.classList.contains("dark")),
    ).toBe(theme === "dark");
    expectReadable(await graphState(page));
    const legend = page.getByRole("region", { name: "Blueprint legend" });
    await expect(legend).toBeVisible();
    expect((await legend.boundingBox())!.height).toBeLessThanOrEqual(40);
    const toggle = legend.locator("summary").filter({ hasText: "Legend" });
    await toggle.focus();
    await toggle.press("Enter");
    for (const label of [
      "In progress",
      "Statement complete",
      "Proof complete",
      "Confirmed error",
      "Source item",
      "Technical auxiliary",
      "Bridge",
      "Cited result",
    ])
      await expect(legend.getByText(label, { exact: true })).toBeVisible();
    const colors = legend.getByRole("group", { name: "Node colors" });
    const fills = await colors
      .locator("svg rect")
      .evaluateAll((symbols) =>
        symbols.map((symbol) => symbol.getAttribute("fill")),
      );
    expect(new Set(fills).size).toBe(fills.length);
    const shapes = legend.getByRole("group", { name: "Node shapes" });
    await expect(shapes.locator("svg polygon")).toHaveCount(2);
    await expect(shapes.locator("svg rect")).toHaveCount(3);
    await expect(
      legend.getByText("Proof dependency", { exact: true }),
    ).toBeVisible();
    await expect(
      legend.getByText(
        "Arrows point from a prerequisite to the node that uses it.",
        { exact: true },
      ),
    ).toBeVisible();
    await expect(
      legend.getByText(
        "Completion can rely on cited results or extra axioms. Select a node for its proof and review details.",
        { exact: true },
      ),
    ).toBeVisible();
    await legend.scrollIntoViewIfNeeded();
    const accessibility = await new AxeBuilder({ page })
      .include(".blueprint-legend")
      .analyze();
    expect(
      accessibility.violations.filter((issue) =>
        ["serious", "critical"].includes(issue.impact || ""),
      ),
    ).toEqual([]);
  });
