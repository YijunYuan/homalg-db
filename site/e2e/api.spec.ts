import { test, expect } from "@playwright/test";
const source = "/?source=api&api=http://127.0.0.1:8788";

test("uses the live SQLite API for search, node and global views", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(`${source}#/search?q=Fixture2000.Thm_1`);
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
  await expect(
    page.getByRole("heading", { name: "Statement", exact: true }),
  ).toBeVisible();
  await page.goto(`${source}#/doc/Fixture2000/fidelity`);
  await expect(
    page.getByRole("tab", { name: "Fidelity", exact: true }),
  ).toHaveAttribute("data-state", "active");
  await page.goto(`${source}#/timeline`);
  await page.getByRole("tab", { name: "Table", exact: true }).click();
  await expect(page.locator("table")).toContainText("chain-complex");
  await page.goto(`${source}#/concepts/chain-complex`);
  await expect(page.locator(".definition-comparison")).toHaveCount(1);
  await expect(page.getByRole("alert")).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("large API documents request an overview and only the selected chapter", async ({
  page,
}) => {
  const calls: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/documents/Fixture2000"))
      calls.push(request.url());
  });
  // Promote the fixture's manifest count to exercise the same threshold as a large database.
  // The overview and chapter payloads still come from the actual server and SQLite snapshot.
  await page.route("http://127.0.0.1:8788/api/manifest", async (route) => {
    const response = await route.fetch();
    const manifest = await response.json();
    manifest.documents.find(
      (doc: { doc_key: string }) => doc.doc_key === "Fixture2000",
    ).node_counts.planned = 6001;
    await route.fulfill({ response, json: manifest });
  });
  await page.goto(`${source}#/doc/Fixture2000`);
  await expect(
    page.getByRole("heading", { name: "Chapter overview", exact: true }),
  ).toBeVisible();
  expect(calls.every((url) => new URL(url).searchParams.has("chapter"))).toBe(
    true,
  );
  expect(
    calls.some((url) => new URL(url).searchParams.get("chapter") === ""),
  ).toBe(true);
  await page.locator(".chapter-cards button").first().click();
  await expect(page.locator(".graph-canvas")).toBeVisible();
  expect(calls.some((url) => !!new URL(url).searchParams.get("chapter"))).toBe(
    true,
  );
  expect(calls.every((url) => new URL(url).searchParams.has("chapter"))).toBe(
    true,
  );
  await page.getByRole("tab", { name: "List", exact: true }).click();
  await expect(
    page.getByRole("link", { name: "Theorem 1", exact: true }),
  ).toBeVisible();
});
