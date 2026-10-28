/** Pure search/filter code shared with the worker and contract tests. */
import MiniSearch from "minisearch";
import { INDEX_OPTIONS, SEARCH_OPTIONS } from "./options.mjs";
import type { SearchRecord } from "../types";
import type { SearchQuery, SearchResult } from "../source";
export type SerializedIndex = ReturnType<MiniSearch["toJSON"]>;
export async function createIndex(
  records: SearchRecord[],
  serialized?: SerializedIndex,
): Promise<MiniSearch<SearchRecord>> {
  if (serialized) {
    try {
      return await MiniSearch.loadJSAsync(serialized, INDEX_OPTIONS);
    } catch {
      /* Rebuild incompatible serialized data. */
    }
  }
  const index = new MiniSearch<SearchRecord>(INDEX_OPTIONS);
  await index.addAllAsync(records, { chunkSize: 500 });
  return index;
}
const members = (value?: string) => value?.split(",").filter(Boolean) || [];
export function runSearch(
  index: MiniSearch<SearchRecord>,
  records: SearchRecord[],
  query: SearchQuery,
): SearchResult {
  const text = query.q?.trim() || "";
  // Whole identifiers are exact terms; the generic fuzzy rule must not conflate Thm_1 and Thm_2.
  const exact = /[A-Za-z][A-Za-z0-9]*(?:[._][A-Za-z0-9]+)+/.test(text);
  const options = {
    ...SEARCH_OPTIONS,
    combineWith: "AND" as const,
    ...(exact ? { fuzzy: false, prefix: false } : {}),
  };
  const results = text ? index.search(text, options) : null;
  const scores = new Map(
    results?.map((result) => [String(result.id), result.score]),
  );
  const candidates = results
    ? records.filter((record) => scores.has(record.id))
    : [...records];
  const selected = (filter: string | undefined, value: string | null) =>
    !filter || members(filter).includes(value || "");
  const includes = (filter: string | undefined, values: string[]) =>
    !filter || members(filter).some((value) => values.includes(value));
  const [first, last] = (query.year || "").split("-").map(Number);
  const filtered = candidates.filter(
    (record) =>
      selected(query.doc, record.doc) &&
      includes(query.author, record.authors) &&
      selected(query.kind, record.kind) &&
      selected(query.headline, record.headline) &&
      selected(query.status, record.status) &&
      selected(query.fidelity, record.fidelity) &&
      includes(query.tags, record.tags) &&
      includes(query.concepts, record.concepts) &&
      (!query.year ||
        (record.year >= first && record.year <= (last || first))) &&
      (!query.mathlib || record.has_mathlib === (query.mathlib === "yes")) &&
      (!query.aux || record.is_aux === (query.aux === "yes")),
  );
  const facets: SearchResult["facets"] = {};
  for (const key of [
    "headline",
    "doc",
    "author",
    "year",
    "kind",
    "status",
    "tags",
    "concepts",
    "fidelity",
    "mathlib",
    "aux",
  ])
    facets[key] = {};
  for (const record of filtered) {
    const values: Record<string, string[]> = {
      headline: record.headline ? [record.headline] : [],
      doc: [record.doc],
      author: record.authors,
      year: [String(record.year)],
      kind: [record.kind],
      status: [record.status],
      tags: record.tags,
      concepts: record.concepts,
      fidelity: [record.fidelity],
      mathlib: [record.has_mathlib ? "yes" : "no"],
      aux: [record.is_aux ? "yes" : "no"],
    };
    for (const [key, items] of Object.entries(values))
      for (const value of items)
        facets[key][value] = (facets[key][value] || 0) + 1;
  }
  filtered.sort((a, b) =>
    query.sort === "year-desc"
      ? b.year - a.year || a.id.localeCompare(b.id)
      : query.sort === "year"
        ? a.year - b.year || a.id.localeCompare(b.id)
        : query.sort === "id"
          ? a.id.localeCompare(b.id)
          : (scores.get(b.id) || 0) - (scores.get(a.id) || 0) ||
            a.year - b.year ||
            a.id.localeCompare(b.id),
  );
  const page = Math.max(1, Number(query.page) || 1),
    page_size = 30;
  return {
    records: filtered.slice((page - 1) * page_size, page * page_size),
    total: filtered.length,
    page,
    page_size,
    facets,
    truncated: false,
  };
}
