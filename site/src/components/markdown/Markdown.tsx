import { useMemo, Fragment } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import { markdownProcessor } from "./pipeline.mjs";
import "katex/dist/katex.min.css";
/** Source text is sanitized before trusted KaTeX rendering; raw HTML is disabled. */
export function Markdown({ text }: { text: string }) {
  const content = useMemo(
    () =>
      markdownProcessor({ react: { Fragment, jsx, jsxs } }).processSync(text)
        .result,
    [text],
  );
  return <div className="markdown">{content}</div>;
}
