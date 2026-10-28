// @vitest-environment node
import { expect, it } from "vitest";
import { readFile } from "node:fs/promises";
import { StaticJsonSource } from "../data/static";
import { resolveRetired, resolveVocabulary } from "../data/retired";
import type { Retired } from "../data/types";
const records: Retired = [
  {
    id: "Fixture2000.Aux_Old",
    kind: "moved",
    moved_to: "Fixture2000.Aux_Middle",
    by: "fixture-reviewer",
    on: "2001-01-01",
    reason: "Moved for reuse.",
  },
  {
    id: "Fixture2000.Aux_Middle",
    kind: "merged",
    merged_into: "Fixture2000.Thm_1",
    by: "fixture-reviewer",
    on: "2001-01-02",
    reason: "Same result.",
  },
  {
    id: "Fixture2000.Aux_Removed",
    kind: "pruned",
    by: "fixture-reviewer",
    on: "2001-01-01",
    reason: "Unused.",
  },
];
it("resolves moved/merged chains and retains a missing replacement for pruning", () => {
  expect(resolveRetired(records[0].id, records)).toBe("Fixture2000.Thm_1");
  expect(resolveRetired(records[2].id, records)).toBeNull();
  expect(() =>
    resolveRetired(records[0].id, [
      ...records,
      { ...records[0], id: "Fixture2000.Thm_1" },
    ]),
  ).toThrow("cycle");
  expect(() => resolveRetired(records[0].id, [records[0], records[0]])).toThrow(
    "duplicate",
  );
});
it("the static adapter loads the live target and does not fabricate pruned data", async () => {
  const requested: string[] = [];
  const source = new StaticJsonSource("/", async (input) => {
    const file = String(input).replace("/data/", "");
    requested.push(file);
    const payload = JSON.parse(
      await readFile(
        new URL(`../../fixtures/data/${file}`, import.meta.url),
        "utf8",
      ),
    );
    if (file === "manifest.json") payload.retired = records;
    return new Response(JSON.stringify(payload));
  });
  expect((await source.node(records[0].id)).summary.id).toBe(
    "Fixture2000.Thm_1",
  );
  expect(requested).toContain("nodes/Fixture2000/Thm_1.json");
  expect(requested).not.toContain("nodes/Fixture2000/Aux_Old.json");
  await expect(source.node(records[2].id)).rejects.toThrow("missing");
});

it("normalizes old vocabulary filters through multiple merges", () => {
  const entries = [
    { id: "old", merged_into: "middle" },
    { id: "middle", merged_into: "current" },
    { id: "current" },
  ];
  expect(resolveVocabulary("old", entries)).toBe("current");
  expect(resolveVocabulary("unknown", entries)).toBe("unknown");
  expect(() =>
    resolveVocabulary("old", [
      ...entries.slice(0, 2),
      { id: "current", merged_into: "old" },
    ]),
  ).toThrow("cycle");
});
