import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { useSearch } from "../../data/loaders";
import {
  ErrorView,
  Loading,
  PageTitle,
  StatusBadge,
  nodeUrl,
  blueprintUrl,
} from "../../components/ui";
import type { SearchQuery } from "../../data/source";
import { t } from "../../i18n/t";
export function Highlight({ text, query }: { text: string; query: string }) {
  const term = query.trim().split(/\s+/)[0];
  if (!term) return <>{text}</>;
  const index = text.toLowerCase().indexOf(term.toLowerCase());
  return index < 0 ? (
    <>{text}</>
  ) : (
    <>
      {text.slice(0, index)}
      <mark>{text.slice(index, index + term.length)}</mark>
      {text.slice(index + term.length)}
    </>
  );
}
export default function Search() {
  const [params, setParams] = useSearchParams(),
    [text, setText] = useState(params.get("q") || "");
  useEffect(() => setText(params.get("q") || ""), [params]);
  const query = {
      ...Object.fromEntries(params),
      page: Number(params.get("page") || 1),
      depth: Number(params.get("depth") || 1),
    } as SearchQuery,
    result = useSearch(query);
  const update = (key: string, value: string) =>
    setParams((previous) => {
      if (value) previous.set(key, value);
      else previous.delete(key);
      previous.delete("page");
      return previous;
    });
  const filters = [
    ["headline", t("search.headline")],
    ["doc", t("search.doc")],
    ["author", t("search.author")],
    ["kind", t("search.kind")],
    ["status", t("search.status")],
    ["tags", t("search.tags")],
    ["concepts", t("search.concepts")],
    ["fidelity", t("search.fidelity")],
    ["mathlib", t("search.mathlib")],
    ["aux", t("search.aux")],
  ];
  const label = (key: string, value: string) =>
    key === "headline"
      ? t(`enum.HeadlineStatus.${value}`)
      : key === "status"
        ? t(`enum.Status.${value}`)
        : key === "kind"
          ? t(`enum.Kind.${value}`)
          : key === "fidelity"
            ? t(`enum.FidelityStatus.${value}`)
            : value === "yes"
              ? t("search.yes")
              : value === "no"
                ? t("search.no")
                : value;
  return (
    <div className="page">
      <PageTitle
        title={t("search.title")}
        description={t("search.description")}
      />
      <form
        className="hero-search compact-search"
        onSubmit={(event) => {
          event.preventDefault();
          update("q", text);
        }}
      >
        <label className="sr-only" htmlFor="search-query">
          {t("search.query")}
        </label>
        <input
          autoFocus
          data-search
          id="search-query"
          value={text}
          placeholder={t("search.placeholder")}
          onChange={(event) => setText(event.target.value)}
        />
        <button className="primary">{t("search.submit")}</button>
      </form>
      <div className="search-layout">
        <aside className="facets" aria-label={t("search.filters")}>
          <h2>{t("search.filters")}</h2>
          {filters.map(([key, title]) => (
            <label key={key}>
              {title}
              <select
                value={params.get(key) || ""}
                onChange={(event) => update(key, event.target.value)}
              >
                <option value="">{t("search.all")}</option>
                {[
                  ...new Set([
                    ...Object.keys(result.data?.facets[key] || {}),
                    ...(params.get(key) ? [params.get(key)!] : []),
                  ]),
                ]
                  .sort()
                  .map((value) => (
                    <option key={value} value={value}>
                      {label(key, value)}
                      {" ("}
                      {result.data?.facets[key]?.[value] || 0}
                      {")"}
                    </option>
                  ))}
              </select>
            </label>
          ))}
          <label>
            {t("search.year")}
            <input
              defaultValue={params.get("year") || ""}
              placeholder={t("search.yearHint")}
              onBlur={(event) => update("year", event.target.value)}
            />
          </label>
          <label>
            {t("search.deps")}
            <input
              defaultValue={params.get("deps") || ""}
              onBlur={(event) => update("deps", event.target.value)}
            />
          </label>
          <label>
            {t("search.direction")}
            <select
              value={params.get("dir") || "down"}
              onChange={(event) => update("dir", event.target.value)}
            >
              <option value="up">{t("search.up")}</option>
              <option value="down">{t("search.down")}</option>
            </select>
          </label>
          <label>
            {t("search.depth")}
            <select
              value={params.get("depth") || "1"}
              onChange={(event) => update("depth", event.target.value)}
            >
              {[1, 2, 3].map((depth) => (
                <option key={depth}>{depth}</option>
              ))}
            </select>
          </label>
          <button onClick={() => setParams(query.q ? { q: query.q } : {})}>
            {t("search.clear")}
          </button>
        </aside>
        <section
          className="search-results"
          aria-label={t("search.results", { total: result.data?.total || 0 })}
        >
          <div className="results-heading">
            <h2 aria-live="polite">
              {t("search.results", { total: result.data?.total || 0 })}
            </h2>
            <label className="sort-label">
              <span className="sr-only">{t("search.sort")}</span>
              <select
                value={params.get("sort") || "relevance"}
                onChange={(event) => update("sort", event.target.value)}
              >
                <option value="relevance">{t("search.relevance")}</option>
                <option value="year">{t("search.yearAscending")}</option>
                <option value="year-desc">{t("search.yearDescending")}</option>
                <option value="id">{t("search.identifier")}</option>
              </select>
            </label>
          </div>
          {result.isLoading && <Loading />}
          {result.error && <ErrorView error={result.error} />}
          <div className="result-list">
            {result.data?.records.map((node) => (
              <article className="search-result" key={node.id}>
                <div className="result-meta">
                  <Link to={`/doc/${node.doc}`}>{node.doc_title}</Link>
                  <span>{node.year}</span>
                  <StatusBadge node={node} />
                </div>
                <h3>
                  <Link to={nodeUrl(node.id)}>
                    <Highlight
                      text={`${node.label}${node.title ? ` · ${node.title}` : ""}`}
                      query={query.q || ""}
                    />
                  </Link>
                </h3>
                <code>{node.id}</code>
                <p>
                  <Highlight
                    text={node.statement_text || node.description_text}
                    query={query.q || ""}
                  />
                </p>
                <div className="result-footer">
                  <div className="chips">
                    {node.tags.map((tag) => (
                      <Link key={tag} to={`/tags/${tag}`}>
                        {tag}
                      </Link>
                    ))}
                  </div>
                  <Link to={blueprintUrl(node.id)}>
                    {t("search.openBlueprint")}
                  </Link>
                </div>
              </article>
            ))}
          </div>
          {result.data && !result.data.total && (
            <p className="empty">{t("search.noResults")}</p>
          )}
          {result.data?.truncated && (
            <p className="notice">{t("search.truncated")}</p>
          )}
          {result.data && result.data.total > result.data.page_size && (
            <nav
              className="pagination"
              aria-label={t("search.page", { page: query.page || 1 })}
            >
              <button
                disabled={(query.page || 1) <= 1}
                onClick={() =>
                  setParams((previous) => {
                    previous.set("page", String((query.page || 1) - 1));
                    return previous;
                  })
                }
              >
                {t("search.previous")}
              </button>
              <span>{t("search.page", { page: query.page || 1 })}</span>
              <button
                disabled={
                  (query.page || 1) * result.data.page_size >= result.data.total
                }
                onClick={() =>
                  setParams((previous) => {
                    previous.set("page", String((query.page || 1) + 1));
                    return previous;
                  })
                }
              >
                {t("search.next")}
              </button>
            </nav>
          )}
        </section>
      </div>
    </div>
  );
}
