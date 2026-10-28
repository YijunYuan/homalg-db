/** One sanitized math/Markdown pipeline for React and build-time diagnostics. */
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import remarkRehype from "remark-rehype";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import rehypeKatex from "rehype-katex";
import rehypeReact from "rehype-react";
import rehypeStringify from "rehype-stringify";
import { visit, SKIP } from "unist-util-visit";
const nodePattern =
  /^([A-Z][A-Za-z]*[0-9]{4}[A-Za-z0-9]*)\.([A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*)$/;
export function rehypeNodeLinks(options = {}) {
  return (tree, file) => {
    visit(tree, "element", (node) => {
      if (
        (node.properties?.className || []).some((name) =>
          String(name).startsWith("katex"),
        )
      )
        return SKIP;
      if (
        node.tagName !== "code" ||
        node.children.length !== 1 ||
        node.children[0].type !== "text"
      )
        return;
      const id = node.children[0].value,
        match = nodePattern.exec(id);
      if (!match) return;
      if (options.nodeIds && !options.nodeIds.has(id)) {
        file.message(`Unknown node ${id}`, {
          source: "homalg",
          ruleId: "dangling-node-link",
        });
        return;
      }
      node.tagName = "a";
      node.properties = {
        href: `#/node/${match[1]}/${match[2]}`,
        className: ["node-link"],
      };
    });
  };
}
export function markdownProcessor(options = {}) {
  const schema = {
    ...defaultSchema,
    tagNames: defaultSchema.tagNames.filter((tag) => tag !== "img"),
  };
  const processor = unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkMath)
    .use(remarkRehype)
    .use(rehypeSanitize, schema)
    .use(rehypeKatex, { strict: "ignore", trust: false })
    .use(rehypeNodeLinks, { nodeIds: options.nodeIds });
  return options.react
    ? processor.use(rehypeReact, options.react)
    : processor.use(rehypeStringify);
}
