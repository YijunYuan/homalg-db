import { Link, useNavigate, useParams } from "react-router";
import { useEffect } from "react";
import { useSearch, useTaxonomy } from "../../data/loaders";
import {
  ErrorView,
  Loading,
  PageTitle,
  StatusBadge,
  nodeUrl,
} from "../../components/ui";
import { t } from "../../i18n/t";
export default function Tags() {
  const { id } = useParams(),
    taxonomy = useTaxonomy(),
    results = useSearch(id ? { tags: id, sort: "year" } : {}),
    navigate = useNavigate();
  const tag = taxonomy.data?.tags.find((item) => item.id === id);
  useEffect(() => {
    if (tag?.merged_into)
      navigate(`/tags/${tag.merged_into}`, { replace: true });
  }, [tag, navigate]);
  if (taxonomy.error) return <ErrorView error={taxonomy.error} />;
  if (!taxonomy.data) return <Loading />;
  const branch = (parent: string | null): React.ReactNode => (
    <ul>
      {taxonomy
        .data!.tags.filter(
          (item) => item.parent === parent && !item.merged_into,
        )
        .map((item) => (
          <li key={item.id}>
            <Link
              className={id === item.id ? "active" : ""}
              to={`/tags/${item.id}`}
            >
              {item.label}
            </Link>
            {branch(item.id)}
          </li>
        ))}
    </ul>
  );
  return (
    <div className="page">
      <PageTitle
        title={tag?.label || t("taxonomy.tagsTitle")}
        description={tag?.description || t("taxonomy.tagsDescription")}
      />
      <div className="taxonomy-layout">
        <nav className="tag-tree" aria-label={t("nav.tags")}>
          {branch(null)}
        </nav>
        <section>
          {id ? (
            <>
              <h2>{t("taxonomy.nodes", { kind: t("taxonomy.tag") })}</h2>
              {results.isLoading && <Loading />}
              {results.error && <ErrorView error={results.error} />}
              <ul className="audit-list">
                {results.data?.records.map((node) => (
                  <li key={node.id}>
                    <Link to={nodeUrl(node.id)}>
                      {node.label}
                      <small>
                        {node.doc_title}
                        {" · "}
                        {node.year}
                      </small>
                    </Link>
                    <StatusBadge node={node} />
                  </li>
                ))}
              </ul>
              <Link to={`/search?tags=${id}&sort=year`}>{t("nav.search")}</Link>
            </>
          ) : (
            <div className="tag-cloud">
              {taxonomy.data.tags
                .filter((item) => !item.parent)
                .map((item) => (
                  <Link key={item.id} to={`/tags/${item.id}`}>
                    {item.label}
                  </Link>
                ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
