import {
  chapterGroups,
  CHAPTER_PADDING,
  packGroups,
} from "../../../scripts/layout.mjs";
import { nodeCard } from "./presentation.mjs";

/** Complete chapter-local dependency ranks give an immediate, size-aware worker fallback.
 * @returns {Record<string, {x: number, y: number}>}
 */
export function seedPositions(nodes, edges, chapters, direction = "DOWN") {
  const horizontal = direction === "RIGHT";
  const groups = chapterGroups(nodes, edges, chapters).map((group) => {
    const pending = new Map(group.nodes.map((node) => [node.id, 0]));
    const users = new Map(group.nodes.map((node) => [node.id, []]));
    const levels = new Map(group.nodes.map((node) => [node.id, 0]));
    for (const edge of group.edges) {
      pending.set(edge.from, pending.get(edge.from) + 1);
      users.get(edge.to).push(edge.from);
    }
    const ready = group.nodes
      .filter((node) => pending.get(node.id) === 0)
      .map((node) => node.id);
    for (let index = 0; index < ready.length; index++)
      for (const id of users.get(ready[index])) {
        levels.set(id, Math.max(levels.get(id), levels.get(ready[index]) + 1));
        pending.set(id, pending.get(id) - 1);
        if (pending.get(id) === 0) ready.push(id);
      }
    const ranks = [];
    let averageWidth = 0,
      averageHeight = 0;
    for (const node of group.nodes) {
      const card = nodeCard(node);
      averageWidth += card.width;
      averageHeight += card.height;
      const rank = levels.get(node.id);
      (ranks[rank] ??= []).push({ id: node.id, ...card });
    }
    const columns = Math.max(
      1,
      Math.ceil(
        Math.sqrt(
          (group.nodes.length *
            (horizontal ? averageWidth : averageHeight) *
            1.35) /
            (horizontal ? averageHeight : averageWidth),
        ),
      ),
    );
    const local = {};
    let rankOffset = 0,
      breadth = 0;
    for (const rank of ranks) {
      if (!rank) continue;
      for (let first = 0; first < rank.length; first += columns) {
        const row = rank.slice(first, first + columns);
        let across = 0,
          depth = 0;
        for (const card of row) {
          const span = horizontal ? card.height : card.width;
          const extent = horizontal ? card.width : card.height;
          local[card.id] = horizontal
            ? { x: rankOffset + extent / 2, y: across + span / 2 }
            : { x: across + span / 2, y: rankOffset + extent / 2 };
          across += span + 28;
          depth = Math.max(depth, extent);
        }
        breadth = Math.max(breadth, across - 28);
        rankOffset += depth + 48;
      }
    }
    const depth = Math.max(0, rankOffset - 48);
    return {
      width:
        (horizontal ? depth : breadth) +
        CHAPTER_PADDING.left +
        CHAPTER_PADDING.right,
      height:
        (horizontal ? breadth : depth) +
        CHAPTER_PADDING.top +
        CHAPTER_PADDING.bottom,
      local,
    };
  });
  const offsets = packGroups(groups);
  const result = {};
  groups.forEach((group, index) => {
    for (const [id, point] of Object.entries(group.local))
      result[id] = {
        x: point.x + offsets[index].x + CHAPTER_PADDING.left,
        y: point.y + offsets[index].y + CHAPTER_PADDING.top,
      };
  });
  return result;
}
