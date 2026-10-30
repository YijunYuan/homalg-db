/** Shared label geometry for the canvas, ELK and prerendered layouts. */
export const CARD_LAYOUT_VERSION = "readable-cards-v3";
export const NODE_FONT_SIZE = 14;

/** Status symbols share the same wrapping and geometry as the title. */
export const glyphs = {
  planned: "○",
  stated: "◐",
  "proved-pending-deps": "◑",
  "proved-modulo-citations": "◕",
  proved: "●",
  "proved-with-axioms": "⚠",
  disputed: "✕",
  pruned: "⊘",
};

/** Wrap complete titles, including long identifiers, without dropping words. */
export function wrapTitle(text, limit = 26) {
  // Conservative system-font widths keep wide capitals and Unicode identifiers
  // inside the same box on both CI and the browser, without measuring a canvas.
  const units = (value) =>
    [...value].reduce(
      (sum, character) =>
        sum +
        (/[MWmw@#%&]/.test(character)
          ? 1.8
          : character.codePointAt(0) > 0x7f
            ? 2
            : /[A-Z]/.test(character)
              ? 1.35
              : 1.1),
      0,
    );
  const lines = [];
  let line = "";
  for (const word of String(text || "")
    .trim()
    .split(/\s+/)) {
    const pieces = [];
    let part = "";
    for (const character of word) {
      if (part && units(part + character) > limit) {
        pieces.push(part);
        part = "";
      }
      part += character;
    }
    if (part) pieces.push(part);
    for (const piece of pieces) {
      if (line && units(`${line} ${piece}`) > limit) {
        lines.push(line);
        line = "";
      }
      line = line ? `${line} ${piece}` : piece;
    }
  }
  if (line) lines.push(line);
  return lines;
}

/** Keep cards compact: source numbering remains available in the node details. */
export function nodeCard(node) {
  const bridge = node.aux_kind === "bridge";
  const cited = node.local_id?.startsWith("Cited_");
  const auxiliary = node.is_aux && !bridge;
  const title = node.chapterSummary ? node.label : node.title || node.label;
  const prefix = node.chapterSummary
    ? ""
    : `${node.needs_repair ? "⚒ " : ""}${glyphs[node.status] ? `${glyphs[node.status]} ` : ""}`;
  const lines = wrapTitle(`${prefix}${title || ""}`, auxiliary ? 21 : 22);
  const textWidth = auxiliary ? 172 : 184;
  // A diamond has only half its outer width available across the text block.
  const width = bridge ? 340 : cited ? 248 : auxiliary ? 204 : 220;
  const textHeight = Math.max(2, lines.length) * 18;
  const height = bridge
    ? Math.max(148, textHeight * 2 + 34)
    : Math.max(70, textHeight + 34);
  return { label: lines.join("\n"), width, height, textWidth };
}
