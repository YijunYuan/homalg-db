import { expect, test } from "@playwright/test";
import {
  glyphs,
  nodeCard,
  NODE_FONT_SIZE,
} from "../src/data/graph/presentation.mjs";

test("manual card wrapping fits real browser glyph widths without secondary wrapping", async ({
  page,
}) => {
  const characters = [
    ..."ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789æœßéØÅϕ𝔄张",
  ];
  const cards = characters.flatMap((character) =>
    [false, true].flatMap((is_aux) =>
      Object.keys(glyphs).flatMap((status) =>
        [false, true].map((needs_repair) => ({
          sample: `${character}:${is_aux ? "auxiliary" : "source"}:${status}:${needs_repair}`,
          ...nodeCard({
            title: character.repeat(66),
            is_aux,
            status,
            needs_repair,
          }),
        })),
      ),
    ),
  );
  // A real browser font metric catches underestimated widths that pure string
  // wrapping tests miss: Cytoscape otherwise wraps again without raising the card.
  const overwide = await page.evaluate(
    ({ cards, fontSize }) => {
      const context = document.createElement("canvas").getContext("2d")!;
      context.font = `500 ${fontSize}px system-ui`;
      return cards.flatMap((card) => {
        const width = Math.max(
          ...card.label
            .split("\n")
            .map((line) => context.measureText(line).width),
        );
        return width > card.textWidth
          ? [{ sample: card.sample, width, textWidth: card.textWidth }]
          : [];
      });
    },
    { cards, fontSize: NODE_FONT_SIZE },
  );
  expect(overwide).toEqual([]);
});
