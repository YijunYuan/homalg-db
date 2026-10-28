import { source, useHealth, useManifest } from "../../data/loaders";
import { ErrorView, Loading, PageTitle, Section } from "../../components/ui";
import { t } from "../../i18n/t";
export default function About() {
  const query = useManifest(),
    health = useHealth();
  if (query.error) return <ErrorView error={query.error} />;
  if (!query.data) return <Loading />;
  const manifest = query.data;
  const stats = [
    [t("about.stale"), manifest.health.summaries_stale],
    [t("about.unreviewed"), manifest.health.llm_relations_unreviewed],
    [t("about.mismatch"), manifest.health.deps_mismatch],
    [t("about.repairs"), manifest.health.needs_repair],
    [t("about.disputed"), manifest.health.disputed],
    [t("about.markdown"), manifest.health.markdown_findings],
  ];
  return (
    <div className="page prose-page">
      <PageTitle
        title={t("about.title")}
        description={t("about.description")}
      />
      <Section title={t("about.build")}>
        <dl>
          <dt>{t("about.commit")}</dt>
          <dd>
            <code>{manifest.commit}</code>
          </dd>
          <dt>{t("about.schema")}</dt>
          <dd>{manifest.schema_version}</dd>
          <dt>{t("about.toolchain")}</dt>
          <dd>
            <code>{manifest.lean.toolchain}</code>
          </dd>
          <dt>{t("about.mathlib")}</dt>
          <dd>
            <code>{manifest.lean.mathlib_rev}</code>
          </dd>
        </dl>
        <a
          className="button"
          href={source.resourceUrl(manifest.index_file)}
          download
        >
          {t("about.download")}
        </a>
      </Section>
      <Section title={t("about.health")}>
        <div className="health-grid">
          {stats.map(([label, count]) => (
            <div key={label}>
              <strong>{count}</strong>
              <span>{label}</span>
            </div>
          ))}
        </div>
        {manifest.prerender.layout_failed?.length && (
          <>
            <h3>{t("about.layouts")}</h3>
            <ul>
              {manifest.prerender.layout_failed.map((doc) => (
                <li key={doc}>{doc}</li>
              ))}
            </ul>
          </>
        )}
        {health.error && <ErrorView error={health.error} />}
        <h3>{t("about.findings")}</h3>
        {health.data?.markdown_findings.length ? (
          <table>
            <thead>
              <tr>
                <th>{t("doc.nodeColumn")}</th>
                <th>{t("about.field")}</th>
                <th>{t("about.message")}</th>
              </tr>
            </thead>
            <tbody>
              {health.data.markdown_findings.slice(0, 200).map((finding, i) => (
                <tr key={i}>
                  <td>{finding.where}</td>
                  <td>{finding.field}</td>
                  <td>{finding.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>{t("about.healthEmpty")}</p>
        )}
      </Section>
      <Section title={t("about.contribute")}>
        <p>{t("about.contributeText")}</p>
        <a
          href={`${manifest.repo_url}/blob/main/docs/CONTRIBUTING.md`}
          target="_blank"
          rel="noreferrer"
        >
          {t("about.guide")}
        </a>
      </Section>
      <Section title={t("about.license")}>
        <p>{t("about.licenseText")}</p>
      </Section>
    </div>
  );
}
