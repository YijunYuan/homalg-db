import { Link, useNavigate } from "react-router";
import { useManifest } from "../../data/loaders";
import { Loading, ErrorView, PageTitle } from "../../components/ui";
import { t } from "../../i18n/t";
import { claimState } from "../../data/claims";
export default function Home() {
  const query = useManifest(),
    navigate = useNavigate();
  if (query.error) return <ErrorView error={query.error} />;
  if (!query.data) return <Loading />;
  const manifest = query.data,
    total = manifest.documents.reduce((sum, doc) => sum + doc.items_total, 0),
    proved = manifest.documents.reduce(
      (sum, doc) => sum + doc.headline_counts["proof-complete"],
      0,
    );
  return (
    <div className="page home">
      <PageTitle
        eyebrow={t("home.eyebrow")}
        title={t("home.title")}
        description={t("home.description")}
      />
      <form
        className="hero-search"
        onSubmit={(event) => {
          event.preventDefault();
          const data = new FormData(event.currentTarget);
          navigate(
            `/search?q=${encodeURIComponent(String(data.get("q") || ""))}`,
          );
        }}
      >
        <label className="sr-only" htmlFor="home-search">
          {t("search.query")}
        </label>
        <span aria-hidden="true">⌕</span>
        <input
          id="home-search"
          data-search
          name="q"
          placeholder={t("search.placeholder")}
        />
        <button className="primary">{t("search.submit")}</button>
      </form>
      <div className="stats">
        <div>
          <strong>{manifest.documents.length}</strong>
          <span>{t("home.documents")}</span>
        </div>
        <div>
          <strong>{total}</strong>
          <span>{t("home.nodes")}</span>
        </div>
        <div>
          <strong>{proved}</strong>
          <span>{t("home.proved")}</span>
        </div>
        <div>
          <strong>{manifest.concepts_count}</strong>
          <span>{t("home.concepts")}</span>
        </div>
      </div>
      <section className="catalog">
        <div className="section-heading">
          <h2>{t("home.catalog")}</h2>
          <p>{t("home.catalogHint")}</p>
        </div>
        <div className="document-grid">
          {manifest.documents.map((doc) => (
            <article className="document-card" key={doc.doc_key}>
              <div className="card-top">
                <span className="year">{doc.year}</span>
                {doc.type === "synthetic" && (
                  <span className="badge muted">{t("home.synthetic")}</span>
                )}
              </div>
              <h3>
                <Link to={`/doc/${doc.doc_key}`}>{doc.title}</Link>
              </h3>
              <p className="authors">
                {doc.authors
                  .map((author) =>
                    [author.given, author.family].filter(Boolean).join(" "),
                  )
                  .join(", ")}
              </p>
              <code>{doc.doc_key}</code>
              <span className="badge claim-badge">
                {claimState(doc.claim, Date.now()) === "active"
                  ? `${t("claims.active")}: ${doc.claim.holder}`
                  : claimState(doc.claim, Date.now()) === "expired"
                    ? t("claims.expired")
                    : t("claims.unclaimed")}
              </span>
              <div
                className="progress"
                role="img"
                aria-label={t("home.progress", {
                  done: doc.headline_counts["proof-complete"],
                  total: doc.items_total,
                })}
              >
                <span
                  style={{
                    width: `${doc.items_total ? (100 * doc.headline_counts["proof-complete"]) / doc.items_total : 0}%`,
                  }}
                />
              </div>
              <div className="card-bottom">
                <span>
                  {t("home.progress", {
                    done: doc.headline_counts["proof-complete"],
                    total: doc.items_total,
                  })}
                </span>
                <Link
                  to={`/doc/${doc.doc_key}`}
                  aria-label={`${t("home.open")}: ${doc.title}`}
                >
                  ↗
                </Link>
              </div>
            </article>
          ))}
        </div>
        {!manifest.documents.length && <p>{t("home.empty")}</p>}
      </section>
    </div>
  );
}
