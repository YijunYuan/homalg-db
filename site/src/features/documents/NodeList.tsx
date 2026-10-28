import { useRef, useState } from "react";
import { Link } from "react-router";
import { useVirtualizer } from "@tanstack/react-virtual";
import type { NodeSummary, Edge } from "../../data/types";
import { blueprintUrl, StatusBadge } from "../../components/ui";
import { t } from "../../i18n/t";
export function NodeList({
  nodes,
  edges,
}: {
  nodes: NodeSummary[];
  edges: Edge[];
}) {
  const [sort, setSort] = useState("rank"),
    parent = useRef<HTMLDivElement>(null);
  const sorted = [...nodes].sort((a, b) =>
    sort === "label"
      ? a.label.localeCompare(b.label)
      : a.rank - b.rank || a.id.localeCompare(b.id),
  );
  const virtual = useVirtualizer({
    count: sorted.length,
    getScrollElement: () => parent.current,
    estimateSize: () => 78,
    overscan: 10,
    enabled: sorted.length > 500,
  });
  const row = (node: NodeSummary) => (
    <>
      <div role="cell">
        <Link to={blueprintUrl(node.id)}>{node.label}</Link>
        <small>{node.title || node.id}</small>
      </div>
      <div role="cell">
        <StatusBadge node={node} />
      </div>
      <div role="cell">{node.chapter || "—"}</div>
      <div role="cell">
        {edges.filter((edge) => edge.from === node.id).length}
      </div>
    </>
  );
  return (
    <>
      <div className="list-toolbar">
        <label>
          {t("search.sort")}
          <select
            value={sort}
            onChange={(event) => setSort(event.target.value)}
          >
            <option value="rank">{t("doc.rank")}</option>
            <option value="label">{t("doc.nodeColumn")}</option>
          </select>
        </label>
      </div>
      <div
        className="node-table"
        role="table"
        aria-label={t("doc.list")}
        aria-rowcount={nodes.length + 1}
      >
        <div className="table-row table-head" role="row">
          <span role="columnheader">{t("doc.nodeColumn")}</span>
          <span role="columnheader">{t("doc.progressColumn")}</span>
          <span role="columnheader">{t("doc.chapterColumn")}</span>
          <span role="columnheader">{t("doc.dependenciesColumn")}</span>
        </div>
        <div
          ref={parent}
          className={nodes.length > 500 ? "virtual-list" : ""}
          role="rowgroup"
        >
          {nodes.length > 500 ? (
            <div
              style={{ height: virtual.getTotalSize(), position: "relative" }}
            >
              {virtual.getVirtualItems().map((item) => (
                <div
                  key={sorted[item.index].id}
                  role="row"
                  className="table-row"
                  aria-rowindex={item.index + 2}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    transform: `translateY(${item.start}px)`,
                    minHeight: item.size,
                  }}
                >
                  {row(sorted[item.index])}
                </div>
              ))}
            </div>
          ) : (
            sorted.map((node) => (
              <div key={node.id} role="row" className="table-row">
                {row(node)}
              </div>
            ))
          )}
        </div>
      </div>
      {!nodes.length && <p className="empty">{t("doc.empty")}</p>}
    </>
  );
}
