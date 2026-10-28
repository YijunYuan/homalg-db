import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";
import path from "node:path";
const data = path.resolve(import.meta.dirname, "../fixtures/data");
const json = async (file: string) =>
  JSON.parse(await readFile(path.join(data, file), "utf8"));

test("explores a document, node details and search", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/#/");
  await expect(
    page.getByRole("heading", { name: "Follow the argument." }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Toy chain complexes", exact: true })
    .click();
  await expect(
    page.getByRole("tab", { name: "Blueprint", exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "List", exact: true }).click();
  await page.getByRole("link", { name: "Theorem 1", exact: true }).click();
  await expect(
    page.getByRole("complementary", { name: "Node details" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Statement", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close details" }).click();
  await expect(
    page.getByRole("complementary", { name: "Node details" }),
  ).toHaveCount(0);
  await page.goto("/#/search?q=Fixture2000.Thm_1");
  await expect(page.locator(".search-result")).toHaveCount(1);
  await expect(page.locator(".search-result")).toContainText(
    "Fixture2000.Thm_1",
  );
  await page
    .getByRole("link", { name: "Open in blueprint", exact: true })
    .click();
  await expect(
    page.getByRole("complementary", { name: "Node details" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("deep links expand collapsed chapters and retain desktop drawer focus", async ({
  page,
}) => {
  await page.goto("/#/doc/Fixture2000");
  await page
    .getByRole("button", { name: "Collapse chapters", exact: true })
    .click();
  await page.goto("/#/doc/Fixture2000/node/Thm_1");
  await expect(
    page.getByRole("complementary", { name: "Node details" }),
  ).toBeVisible();
  await page.locator(".graph-canvas").focus();
  await page.keyboard.press("/");
  await expect(
    page.getByPlaceholder("Find a node in this document"),
  ).toBeFocused();
  await expect(
    page.getByRole("complementary", { name: "Node details" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("complementary", { name: "Node details" }),
  ).toHaveCount(0);
});

test("has real Shiki colors in both themes and a keyboard-safe mobile drawer", async ({
  page,
}) => {
  await page.goto("/#/node/Fixture2000/Thm_1");
  await page.getByText("Show full Lean source", { exact: true }).click();
  const keyword = page
    .locator(".lean-code .shiki span")
    .filter({ hasText: /^theorem$/ })
    .first();
  await expect(keyword).toBeVisible();
  for (const name of ["Light", "Dark"]) {
    await page.getByRole("button", { name: "Color theme" }).click();
    await page.getByRole("menuitemradio", { name, exact: true }).click();
    const colors = await keyword.evaluate((element) => ({
      syntax: getComputedStyle(element).color,
      body: getComputedStyle(document.body).color,
    }));
    expect(colors.syntax).not.toBe(colors.body);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#/doc/Fixture2000/node/Thm_1");
  await expect(
    page.getByRole("dialog", { name: "Node details" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close details" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("recovers transparently when a deployment replaces a content hash", async ({
  page,
}) => {
  const manifest = await json("manifest.json"),
    entry = manifest.documents.find(
      (item: { doc_key: string }) => item.doc_key === "Fixture2000",
    );
  const fresh = structuredClone(manifest);
  fresh.documents.find(
    (item: { doc_key: string }) => item.doc_key === "Fixture2000",
  ).files.document = "documents/redeployed.json";
  let requests = 0;
  await page.route("**/data/manifest.json", async (route) => {
    requests++;
    await route.fulfill({ json: requests === 1 ? manifest : fresh });
  });
  await page.route(`**/data/${entry.files.document}`, async (route) =>
    route.fulfill({ status: 404, body: "" }),
  );
  await page.route("**/data/documents/redeployed.json", async (route) =>
    route.fulfill({ json: await json(entry.files.document) }),
  );
  await page.goto("/#/doc/Fixture2000");
  await expect(
    page.getByRole("tab", { name: "Blueprint", exact: true }),
  ).toBeVisible();
  expect(requests).toBeGreaterThanOrEqual(2);
  await expect(page.getByRole("alert")).toHaveCount(0);
});

for (const route of [
  "/#/",
  "/#/doc/Fixture2000",
  "/#/doc/Fixture2000/node/Thm_1",
  "/#/search?q=chain",
  "/#/timeline",
  "/#/concepts/chain-complex",
])
  test(`accessible ${route}`, async ({ page }) => {
    await page.goto(route);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main h1").first()).toBeVisible();
    await expect(page.getByRole("alert")).toHaveCount(0);
    const results = await new AxeBuilder({ page }).analyze();
    expect(
      results.violations.filter(
        (issue) => issue.impact === "serious" || issue.impact === "critical",
      ),
    ).toEqual([]);
  });

test("expands an individual parent and preserves its state", async ({
  page,
}) => {
  await page.goto("/#/doc/Fixture2000/node/Thm_1");
  await page
    .getByRole("button", {
      name: "Expand this node’s auxiliaries",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Collapse this node’s auxiliaries",
      exact: true,
    }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("button", {
      name: "Collapse this node’s auxiliaries",
      exact: true,
    }),
  ).toBeVisible();
});

test("keeps the dark document page accessible", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("homalg-theme", "dark"));
  await page.goto("/#/doc/Fixture2000/node/Thm_1");
  await expect(
    page.getByRole("heading", { name: "Statement", exact: true }),
  ).toBeVisible();
  const results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter((item) =>
      ["serious", "critical"].includes(item.impact || ""),
    ),
  ).toEqual([]);
});
