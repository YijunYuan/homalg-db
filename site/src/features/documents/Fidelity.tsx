import { Link } from "react-router";
import type { DocumentBundle } from "../../data/source";
import type { NodeSummary } from "../../data/types";
import { blueprintUrl, Section } from "../../components/ui";
import { t } from "../../i18n/t";
import { useNode } from "../../data/loaders";
function NodeTable({ nodes }: { nodes: NodeSummary[] }) {
  return nodes.length ? (
    <ul className="audit-list">
      {nodes.map((node) => (
        <li key={node.id}>
          <Link to={blueprintUrl(node.id)}>
            {node.label}
            <small>{node.title || node.id}</small>
          </Link>
          {node.aux_parent && <code>{node.aux_parent}</code>}
        </li>
      ))}
    </ul>
  ) : (
    <p className="muted">{t("node.none")}</p>
  );
}
function Deviations({ id }: { id: string }) {
  const query = useNode(id);
  return (
    <article className="foundation">
      <Link to={blueprintUrl(id)}>{id}</Link>
      {query.data?.authored.fidelity?.deviations?.map((item, i) => (
        <div key={i}>
          <h3>{t(`enum.DeviationKind.${item.kind}`)}</h3>
          <p>{item.what}</p>
          <p className="muted">{item.why}</p>
        </div>
      ))}
    </article>
  );
}
export function Fidelity({ bundle }: { bundle: DocumentBundle }) {
  return (
    <div className="fidelity">
      <h2>{t("fidelity.title")}</h2>
      <p className="muted">{t("fidelity.description")}</p>
      <div className="stats compact">
        {(["faithful", "foundation", "deviates"] as const).map((status) => (
          <div key={status}>
            <strong>
              {
                bundle.nodes.filter((node) => node.fidelity_status === status)
                  .length
              }
            </strong>
            <span>{t(`enum.FidelityStatus.${status}`)}</span>
          </div>
        ))}
        <div>
          <strong>{bundle.nodes.filter((node) => node.reviewed).length}</strong>
          <span>{t("fidelity.reviewed")}</span>
        </div>
      </div>
      <Section title={t("fidelity.foundations")}>
        {bundle.document.foundations.length ? (
          bundle.document.foundations.map((foundation, i) => (
            <article className="foundation" key={i}>
              <h3>
                {foundation.notion}
                <span className="badge">{foundation.status}</span>
              </h3>
              <p>{foundation.justification}</p>
              <div className="chips">
                {foundation.mathlib.map((decl) => (
                  <a
                    key={decl}
                    href={`https://leanprover-community.github.io/mathlib4_docs/find/#doc/${encodeURIComponent(decl)}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <code>{decl}</code>
                  </a>
                ))}
              </div>
              {foundation.evidence && (
                <>
                  <h4>{t("fidelity.evidence")}</h4>
                  <p>{foundation.evidence}</p>
                </>
              )}
              {foundation.confirmed_by && (
                <p className="muted">
                  {t("fidelity.confirmedBy", { by: foundation.confirmed_by })}
                </p>
              )}
            </article>
          ))
        ) : (
          <p>{t("fidelity.noFoundations")}</p>
        )}
      </Section>
      <Section title={t("fidelity.deviates")}>
        {bundle.nodes
          .filter((node) => node.fidelity_status === "deviates")
          .map((node) => (
            <Deviations key={node.id} id={node.id} />
          ))}
      </Section>
      <Section title={t("fidelity.mismatch")}>
        <NodeTable nodes={bundle.nodes.filter((node) => node.deps_mismatch)} />
      </Section>
      <Section title={t("fidelity.bridges")}>
        <NodeTable
          nodes={bundle.nodes.filter((node) => node.aux_kind === "bridge")}
        />
      </Section>
      <Section title={t("fidelity.unreviewed")}>
        <NodeTable nodes={bundle.nodes.filter((node) => !node.reviewed)} />
      </Section>
      <Section title={t("fidelity.reopened")}>
        <NodeTable nodes={bundle.nodes.filter((node) => node.reopened)} />
      </Section>
    </div>
  );
}
