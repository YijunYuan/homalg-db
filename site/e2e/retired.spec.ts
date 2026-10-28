import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
test("historical links explain a move and pruning without invented node contents", async ({
  page,
}) => {
  const manifest = JSON.parse(
    await readFile(
      new URL("../fixtures/data/manifest.json", import.meta.url),
      "utf8",
    ),
  );
  manifest.retired = [
    {
      id: "Fixture2000.Aux_Old",
      kind: "moved",
      moved_to: "Fixture2000.Thm_1",
      by: "fixture-reviewer",
      on: "2001-01-01",
      reason: "Synthetic move for reuse.",
    },
    {
      id: "Fixture2000.Aux_Removed",
      kind: "pruned",
      by: "fixture-reviewer",
      on: "2001-01-01",
      reason: "Synthetic unused result.",
    },
  ];
  await page.route("**/data/manifest.json", (route) =>
    route.fulfill({ json: manifest }),
  );
  await page.goto("/#/node/Fixture2000/Aux_Old");
  await expect(
    page.getByRole("heading", { name: "Retired identifier" }),
  ).toBeVisible();
  await expect(page.getByText("Synthetic move for reuse.")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Statement", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Open current node: Fixture2000.Thm_1" })
    .click();
  await expect(page).toHaveURL(/\/node\/Fixture2000\/Thm_1$/);
  await expect(
    page.getByRole("heading", { name: "Retired identifier" }),
  ).toHaveCount(0);
  await page.goto("/#/node/Fixture2000/Aux_Removed");
  await expect(page.getByText("Synthetic unused result.")).toBeVisible();
  await expect(
    page.getByText("No live replacement is available in this snapshot."),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Statement", exact: true }),
  ).toHaveCount(0);
});
