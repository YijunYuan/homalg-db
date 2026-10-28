import { useEffect, useState } from "react";
import { Link } from "react-router";
import { useManifest } from "../../data/loaders";
import { ErrorView, Loading, PageTitle } from "../../components/ui";
import { t } from "../../i18n/t";
import { claimState } from "../../data/claims";
export default function Claims() {
  const query = useManifest(),
    [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 60_000);
    return () => clearInterval(timer);
  }, []);
  if (query.error) return <ErrorView error={query.error} />;
  if (!query.data) return <Loading />;
  return (
    <div className="page">
      <PageTitle
        title={t("claims.title")}
        description={t("claims.description")}
      />
      <div className="claim-grid">
        {query.data.documents.map((doc) => {
          const state = claimState(doc.claim, now),
            run = doc.claim.run;
          return (
            <article className="claim-card" key={doc.doc_key}>
              <header>
                <h2>
                  <Link to={`/doc/${doc.doc_key}`}>{doc.title}</Link>
                </h2>
                <span
                  className={`badge ${state === "expired" ? "warning" : ""}`}
                >
                  {state === "active"
                    ? t("claims.active")
                    : state === "expired"
                      ? t("claims.expired")
                      : t("claims.unclaimed")}
                </span>
              </header>
              <dl>
                <dt>{t("claims.holder")}</dt>
                <dd>{doc.claim.holder || "—"}</dd>
                <dt>{t("claims.expires")}</dt>
                <dd>
                  {doc.claim.effective_expires_at || doc.claim.expires_at
                    ? new Date(
                        doc.claim.effective_expires_at || doc.claim.expires_at!,
                      ).toLocaleString("en")
                    : "—"}
                </dd>
              </dl>
              <p>
                {t("home.progress", {
                  done: doc.headline_counts["proof-complete"],
                  total: doc.items_total,
                })}
              </p>
              {run && (
                <div className="notice">
                  <p>
                    {t("claims.run", {
                      time: new Date(run.generated_at).toLocaleString("en"),
                    })}
                  </p>
                  {now - Date.parse(run.generated_at) > 7 * 86400000 && (
                    <span className="badge warning">{t("claims.stale")}</span>
                  )}
                  <p>
                    {t("claims.counts", {
                      proved: run.counts.headline.proof_complete,
                      pages: run.counts.pages_reviewed,
                      issues: run.open_for_human,
                    })}
                  </p>
                </div>
              )}
              {doc.claim.pr && (
                <a
                  href={`${query.data!.repo_url}/pull/${doc.claim.pr}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  {t("claims.pr")}
                </a>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}
