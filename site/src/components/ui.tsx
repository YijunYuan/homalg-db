import { Link } from "react-router";
import type { ReactNode } from "react";
import { t } from "../i18n/t";
import { DataError } from "../data/source";
import type { NodeSummary, NodeRef } from "../data/types";
import { glyphs } from "../data/graph/presentation.mjs";
export { glyphs } from "../data/graph/presentation.mjs";
export const nodeUrl = (id: string) => `/node/${id.replace(".", "/")}`;
export const blueprintUrl = (id: string) => `/doc/${id.replace(".", "/node/")}`;
export function Loading() {
  return (
    <div role="status" className="empty">
      <span className="spinner" />
      {t("app.loading")}
    </div>
  );
}
export function ErrorView({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => void;
}) {
  const message =
    error instanceof DataError
      ? error.code === "schema"
        ? t("data.schema", { version: error.detail })
        : error.code === "redeployed"
          ? t("data.redeployed")
          : error.code === "missing"
            ? t("data.missing")
            : t("data.network")
      : t("app.error");
  return (
    <div role="alert" className="notice error">
      <p>{message}</p>
      {retry && <button onClick={retry}>{t("app.retry")}</button>}
    </div>
  );
}
export function PageTitle({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <header className="page-title">
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h1>{title}</h1>
      {description && <p>{description}</p>}
      {children}
    </header>
  );
}
export function StatusBadge({
  node,
}: {
  node: Pick<NodeSummary, "headline" | "status">;
}) {
  return (
    <span
      className={`badge status ${node.headline || "muted"}`}
      title={t(`enum.Status.${node.status}`)}
    >
      <span aria-hidden="true">{glyphs[node.status]}</span>
      {node.headline
        ? t(`enum.HeadlineStatus.${node.headline}`)
        : t(`enum.Status.${node.status}`)}
    </span>
  );
}
export function NodeBadges({ node }: { node: NodeSummary }) {
  return (
    <div className="badges">
      <StatusBadge node={node} />
      <span className={`badge ${node.fidelity_status}`}>
        {t(`enum.FidelityStatus.${node.fidelity_status}`)}
      </span>
      {node.is_aux && (
        <span className="badge">
          {node.aux_kind === "bridge" ? t("node.bridge") : t("node.auxiliary")}
        </span>
      )}
      {node.local_id.startsWith("Cited_") && (
        <span className="badge cited">{t("node.cited")}</span>
      )}
      {node.status === "proved-modulo-citations" && (
        <span className="badge cited">{t("node.modulo")}</span>
      )}
      {node.disputed && node.headline !== "error" && (
        <span className="badge raised">{t("node.disputeRaised")}</span>
      )}
      {node.needs_repair && (
        <span className="badge warning">{t("node.repair")}</span>
      )}
      {node.reopened && (
        <span className="badge warning">{t("node.reopened")}</span>
      )}
      {node.deps_mismatch && (
        <span className="badge warning">{t("node.mismatch")}</span>
      )}
    </div>
  );
}
export function NodeLinks({ nodes }: { nodes: NodeRef[] }) {
  return nodes.length ? (
    <ul className="node-links">
      {nodes.map((node) => (
        <li key={node.id}>
          <Link to={nodeUrl(node.id)}>
            {node.label}
            <code>{node.id}</code>
          </Link>
          <StatusBadge node={node} />
        </li>
      ))}
    </ul>
  ) : (
    <p className="muted">{t("node.none")}</p>
  );
}
export function Section({
  title,
  children,
  id,
}: {
  title: string;
  children: ReactNode;
  id?: string;
}) {
  return (
    <section className="section" id={id}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
