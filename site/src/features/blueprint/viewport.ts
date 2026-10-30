import type { Core, NodeSingular } from "cytoscape";
import { NODE_FONT_SIZE } from "../../data/graph/presentation.mjs";

export const READABLE_ZOOM = 12 / NODE_FONT_SIZE;

/** Start at a real source item, rather than the empty center of a large graph. */
function readingStart(core: Core): NodeSingular | undefined {
  const source = core.nodes("[sourceItem = 1]");
  return (source.length ? source : core.nodes().not(":parent")).sort(
    (a, b) =>
      a.data("chapterOrder") - b.data("chapterOrder") ||
      a.position("y") - b.position("y") ||
      a.position("x") - b.position("x"),
  )[0];
}

/** Fit small graphs; use readable text and a source anchor for larger graphs. */
export function readLabels(core: Core, selected?: string) {
  core.resize();
  const bounds = core.elements().boundingBox();
  const fit = Math.min(
    (core.width() - 70) / Math.max(1, bounds.w),
    (core.height() - 70) / Math.max(1, bounds.h),
  );
  const zoom = Math.min(1, Math.max(READABLE_ZOOM, fit));
  const focused = selected ? core.getElementById(selected) : undefined;
  const anchor = focused?.length ? focused : readingStart(core);
  if (!anchor) return;
  if (!focused?.length && fit >= READABLE_ZOOM) {
    core.viewport({
      zoom,
      pan: {
        x: (core.width() - (bounds.x1 + bounds.x2) * zoom) / 2,
        y: (core.height() - (bounds.y1 + bounds.y2) * zoom) / 2,
      },
    });
  } else {
    const position = anchor.position();
    core.viewport({
      zoom,
      pan: {
        x: core.width() / 2 - position.x * zoom,
        y: (focused?.length ? core.height() / 2 : 130) - position.y * zoom,
      },
    });
  }
}

/** Selection never changes scale or positions; move only if the card is offscreen. */
export function revealSelection(core: Core, selected?: string) {
  core.elements().removeClass("focus neighbor");
  core.resize();
  if (!selected) return;
  const node = core.getElementById(selected);
  if (!node.length) return;
  node.addClass("focus");
  node.neighborhood().edges().addClass("focus");
  core.resize();
  const box = node.renderedBoundingBox();
  const padding = 24;
  if (
    box.x1 < padding ||
    box.y1 < padding ||
    box.x2 > core.width() - padding ||
    box.y2 > core.height() - padding
  )
    core.center(node);
}
