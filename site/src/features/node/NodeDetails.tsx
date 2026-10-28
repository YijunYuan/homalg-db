import { useState } from "react";
import { Link } from "react-router";
import { useNode, useNeighbors, useManifest } from "../../data/loaders";
import {
  ErrorView,
  Loading,
  NodeBadges,
  NodeLinks,
  Section,
  nodeUrl,
  blueprintUrl,
} from "../../components/ui";
import { Markdown } from "../../components/markdown/Markdown";
import { t } from "../../i18n/t";
import type { Direction } from "../../data/source";
export default function NodeDetails({ id }: { id: string }) {
  const manifest = useManifest();
  const retired = manifest.data?.retired?.find((record) => record.id === id);
  const query = useNode(id),
    [expanded, setExpanded] = useState(false),
    [direction, setDirection] = useState<Direction>("up"),
    [depth, setDepth] = useState(1);
  const closure = useNeighbors(id, direction, depth, expanded);
  const retirement = retired && (
    <aside className="notice" role="status">
      <h2>{t("node.retired")}</h2>
      <p>
        {retired.kind === "moved"
          ? t("node.retired.moved", { id, on: retired.on, by: retired.by })
          : retired.kind === "merged"
            ? t("node.retired.merged", { id, on: retired.on, by: retired.by })
            : t("node.retired.pruned", { id, on: retired.on, by: retired.by })}
      </p>
      <p>{retired.reason}</p>
      {query.data ? (
        <Link to={nodeUrl(query.data.summary.id)}>
          {t("node.retired.open", { id: query.data.summary.id })}
        </Link>
      ) : query.error ? (
        <p>{t("node.retired.unavailable")}</p>
      ) : null}
    </aside>
  );
  if (query.error)
    return retired ? retirement : <ErrorView error={query.error} />;
  if (!query.data) return <Loading />;
  const {
    summary: node,
    authored,
    derived,
    global,
    lean,
    links,
    relations,
  } = query.data;
  const reviewed = authored.fidelity?.reviewed;
  const textSections = [
    ["node.statement", authored.statement_md],
    ["node.original", authored.statement_original_md],
    ["node.corrected", authored.statement_corrected_md],
  ];
  return (
    <article className="node-details">
      {retirement}
      <NodeBadges node={node} />
      <h1>
        {node.label}
        {node.title && <small>{node.title}</small>}
      </h1>
      <p className="source-line">
        <Link to={`/doc/${node.doc}`}>
          {t("node.source", {
            title: global.doc_title,
            year: global.doc_year,
            chapter: node.chapter || "—",
            section: node.section || "—",
            pages: node.pages.join(", "),
          })}
        </Link>
      </p>
      <code className="node-id">{node.id}</code>
      {textSections.map(
        ([key, text]) =>
          text && (
            <Section
              key={key}
              title={
                key === "node.statement"
                  ? t("node.statement")
                  : key === "node.original"
                    ? t("node.original")
                    : t("node.corrected")
              }
            >
              <Markdown text={text} />
            </Section>
          ),
      )}
      <Section title={t("node.lean")}>
        {lean.signature_html ? (
          <div
            className="lean-code"
            dangerouslySetInnerHTML={{ __html: lean.signature_html }}
          />
        ) : (
          <pre>
            {derived.decl_info
              .filter((decl) => authored.decls?.includes(decl.name))
              .map((decl) => `${decl.name} : ${decl.type}`)
              .join("\n\n")}
          </pre>
        )}
        <details>
          <summary>{t("node.fullSource")}</summary>
          {lean.source_html ? (
            <div
              className="lean-code"
              dangerouslySetInnerHTML={{ __html: lean.source_html }}
            />
          ) : (
            <pre>{lean.source_text}</pre>
          )}
        </details>
        <div className="link-row">
          <a href={links.github_blob} target="_blank" rel="noreferrer">
            {t("node.github")}
          </a>
          <a href={links.github_blame} target="_blank" rel="noreferrer">
            {t("node.blame")}
          </a>
          <Link to={blueprintUrl(node.id)}>{t("search.openBlueprint")}</Link>
        </div>
      </Section>
      <Section title={t("node.faithfulness")}>
        <p>
          <span className="badge">
            {t(`enum.FidelityStatus.${node.fidelity_status}`)}
          </span>
        </p>
        <p>
          {reviewed
            ? t("node.reviewed", { by: reviewed.by, on: reviewed.on })
            : t("node.unreviewed")}
        </p>
        {reviewed?.note && <p>{reviewed.note}</p>}
        {authored.fidelity?.deviations?.map((deviation, i) => (
          <div className="notice warning" key={i}>
            <strong>{t(`enum.DeviationKind.${deviation.kind}`)}</strong>
            <p>{deviation.what}</p>
            <p>{deviation.why}</p>
          </div>
        ))}
        {authored.dispute && (
          <div
            className={`notice ${authored.dispute.confirmed_by ? "error" : "raised"}`}
          >
            <h3>{t("node.dispute")}</h3>
            <p>{authored.dispute.reason}</p>
            <p>
              {authored.dispute.confirmed_by
                ? t("node.confirmed", {
                    by: authored.dispute.confirmed_by,
                    on: authored.dispute.confirmed_on || "",
                  })
                : t("node.unconfirmed")}
            </p>
          </div>
        )}
        {node.status === "proved-with-axioms" && (
          <div className="notice warning">
            <strong>{t("node.axioms")}</strong>
            <ul>
              {[
                ...new Set(
                  Object.values(global.decl_axioms).flatMap(
                    (decl) => decl.axioms,
                  ),
                ),
              ].map((axiom) => (
                <li key={axiom}>
                  <code>{axiom}</code>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Section>
      {authored.mathlib && (
        <Section title={t("node.mathlib")}>
          <p>{t(`enum.MathlibRelation.${authored.mathlib.relation}`)}</p>
          {authored.mathlib.note && <p>{authored.mathlib.note}</p>}
          <ul>
            {authored.mathlib.decls?.map((decl) => (
              <li key={decl}>
                <a
                  href={`https://leanprover-community.github.io/mathlib4_docs/find/#doc/${encodeURIComponent(decl)}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <code>{decl}</code>
                </a>
              </li>
            ))}
          </ul>
          {authored.mathlib.bridge && (
            <Link to={nodeUrl(authored.mathlib.bridge)}>
              {t("node.bridge")}
            </Link>
          )}
        </Section>
      )}
      {authored.proof_md && (
        <Section title={t("node.proof")}>
          <Markdown text={authored.proof_md} />
        </Section>
      )}
      {authored.notes_md && (
        <Section title={t("node.notes")}>
          <Markdown text={authored.notes_md} />
        </Section>
      )}
      {(authored.history_md || authored.history?.length) && (
        <Section title={t("node.history")}>
          {authored.history_md && <Markdown text={authored.history_md} />}
          <ul>
            {authored.history?.map((entry, i) => (
              <li key={i}>
                {entry.claim}
                {entry.ref && <p>{entry.ref}</p>}
              </li>
            ))}
          </ul>
        </Section>
      )}
      <Section title={t("node.dependencies")}>
        <h3>{t("node.statementDeps")}</h3>
        <NodeLinks nodes={query.data.dependencies.statement} />
        <h3>{t("node.proofDeps")}</h3>
        <NodeLinks nodes={query.data.dependencies.proof} />
        <div className="dependency-flags">
          {[
            ...query.data.dependencies.statement,
            ...query.data.dependencies.proof,
          ].map((dependency) => (
            <p key={dependency.id}>
              <code>{dependency.id}</code>
              {[...authored.deps.statement, ...authored.deps.proof].includes(
                dependency.id,
              ) && <span className="badge">{t("node.declared")}</span>}
              {[
                ...derived.verified_deps.statement,
                ...derived.verified_deps.proof,
              ].includes(dependency.id) && (
                <span className="badge">{t("node.verified")}</span>
              )}
            </p>
          ))}
        </div>
        <h3>{t("node.dependents")}</h3>
        <NodeLinks nodes={query.data.dependents} />
        {global.closure.blocked_by.length > 0 && (
          <>
            <h3>{t("node.blocked")}</h3>
            <ul>
              {global.closure.blocked_by.map((blocked) => (
                <li key={blocked}>
                  <Link to={nodeUrl(blocked)}>{blocked}</Link>
                </li>
              ))}
            </ul>
          </>
        )}
        <details onToggle={(event) => setExpanded(event.currentTarget.open)}>
          <summary>{t("node.transitive")}</summary>
          <div className="controls">
            <label>
              {t("search.direction")}
              <select
                value={direction}
                onChange={(event) =>
                  setDirection(event.target.value as Direction)
                }
              >
                <option value="up">{t("search.up")}</option>
                <option value="down">{t("search.down")}</option>
              </select>
            </label>
            <label>
              {t("search.depth")}
              <select
                value={depth}
                onChange={(event) => setDepth(Number(event.target.value))}
              >
                {[1, 2, 3].map((n) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
          </div>
          {closure.isLoading && <Loading />}
          {closure.error && <ErrorView error={closure.error} />}
          <ul>
            {[...new Set(closure.data?.flatMap((edge) => [edge.from, edge.to]))]
              .filter((other) => other !== id)
              .map((other) => (
                <li key={other}>
                  <Link to={nodeUrl(other)}>{other}</Link>
                </li>
              ))}
          </ul>
          {closure.data?.truncated && <p>{t("search.truncated")}</p>}
        </details>
      </Section>
      <Section title={t("node.concepts")}>
        <div className="chips">
          {[...new Set([...node.concepts_defines, ...node.concepts_uses])].map(
            (concept) => (
              <Link key={concept} to={`/concepts/${concept}`}>
                {concept}
              </Link>
            ),
          )}
        </div>
      </Section>
      {relations.length > 0 && (
        <Section title={t("node.relations")}>
          <ul className="relation-list">
            {relations.map((relation) => (
              <li key={relation.id}>
                <span>{t(`enum.RelationType.${relation.type}`)}</span>
                <Link
                  to={nodeUrl(
                    relation.source === id ? relation.target : relation.source,
                  )}
                >
                  {relation.source === id ? relation.target : relation.source}
                </Link>
                <span className="badge">{relation.review.status}</span>
                {relation.note && <p>{relation.note}</p>}
                <p className="muted">
                  {t("node.provenance")}
                  {": "}
                  {relation.provenance.handle ||
                    relation.provenance.model ||
                    relation.provenance.by}
                  {" · "}
                  {relation.provenance.on}
                </p>
              </li>
            ))}
          </ul>
        </Section>
      )}
      <Section title={t("node.tags")}>
        <div className="chips">
          {node.tags.map((tag) => (
            <Link key={tag} to={`/tags/${tag}`}>
              {tag}
            </Link>
          ))}
        </div>
      </Section>
      {authored.authors_of_formalization?.length && (
        <Section title={t("node.contributors")}>
          <p>{authored.authors_of_formalization.join(", ")}</p>
        </Section>
      )}
    </article>
  );
}
