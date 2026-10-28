/** Permanent aliases retain their reason and never impersonate a deleted node. */
import type { Retired } from "./types";
import { DataError } from "./source";
export function resolveRetired(
  id: string,
  records: Retired = [],
): string | null {
  const table = new Map(records.map((record) => [record.id, record]));
  if (table.size !== records.length)
    throw new DataError("schema", "duplicate retired id");
  const seen = new Set<string>();
  while (table.has(id)) {
    if (seen.has(id)) throw new DataError("schema", "retired node cycle");
    seen.add(id);
    const record = table.get(id)!;
    if (record.kind === "pruned") return null;
    const next = record.kind === "moved" ? record.moved_to : record.merged_into;
    if (!next) throw new DataError("schema", "missing retirement target");
    id = next;
  }
  return id;
}

/** Historical vocabulary filters have the same meaning as their surviving ids. */
export function resolveVocabulary(
  id: string,
  records: { id: string; merged_into?: string | null }[],
): string {
  const table = new Map(
    records.map((record) => [record.id, record.merged_into]),
  );
  const seen = new Set<string>();
  while (table.get(id)) {
    if (seen.has(id)) throw new DataError("schema", "taxonomy merge cycle");
    seen.add(id);
    id = table.get(id)!;
  }
  return id;
}
