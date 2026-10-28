import { Link } from "react-router";
import { useNode } from "../../data/loaders";
import { Markdown } from "../../components/markdown/Markdown";
import { ErrorView, Loading, nodeUrl, StatusBadge } from "../../components/ui";
import { t } from "../../i18n/t";
export function DefinitionComparison({ id }: { id: string }) {
  const query = useNode(id);
  if (query.error) return <ErrorView error={query.error} />;
  if (!query.data) return <Loading />;
  const { summary, authored, lean, global } = query.data;
  return (
    <article className="definition-comparison">
      <h3>
        <Link to={nodeUrl(id)}>
          {global.doc_title} · {global.doc_year}
        </Link>
      </h3>
      <p>{summary.label}</p>
      <StatusBadge node={summary} />
      <Markdown text={authored.statement_md} />
      <h4>{t("node.lean")}</h4>
      {lean.signature_html ? (
        <div
          className="lean-code"
          dangerouslySetInnerHTML={{ __html: lean.signature_html }}
        />
      ) : (
        <pre>
          {query.data.derived?.decl_info
            .map((decl) => `${decl.name} : ${decl.type}`)
            .join("\n\n")}
        </pre>
      )}
      <p className="muted">
        {t(`enum.FidelityStatus.${summary.fidelity_status}`)}
      </p>
    </article>
  );
}
