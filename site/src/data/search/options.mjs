/** Shared verbatim by browser workers and the build-time indexer. */
export function tokenize(text, field) {
  const parts = String(text)
    .split(/[\s\p{P}]+/u)
    .filter(Boolean);
  if (field === undefined || ["id", "decl_names", "label"].includes(field)) {
    const identifiers =
      String(text).match(/[A-Za-z][A-Za-z0-9]*(?:[._][A-Za-z0-9]+)+/g) || [];
    for (const identifier of identifiers) {
      parts.push(identifier);
      const segments = identifier.split(".");
      for (let i = 1; i < segments.length; i++)
        parts.push(segments.slice(i).join("."));
    }
  }
  return [...new Set(parts)];
}
export const INDEX_OPTIONS = {
  idField: "id",
  fields: [
    "title",
    "label",
    "id",
    "statement_text",
    "description_text",
    "tags",
    "concepts",
    "decl_names",
    "doc_title",
    "authors",
  ],
  storeFields: ["id"],
  stringifyField: (value) =>
    Array.isArray(value) ? value.join(" ") : String(value ?? ""),
  tokenize,
  processTerm: (term) => term.toLowerCase(),
};
export const SEARCH_OPTIONS = {
  boost: { title: 3, label: 3, id: 2, tags: 2, concepts: 2, decl_names: 2 },
  prefix: true,
  fuzzy: 0.2,
  combineWith: "AND",
};
