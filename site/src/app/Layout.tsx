import { Suspense, useEffect } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { ThemeSwitch } from "./theme";
import { t } from "../i18n/t";
import { source, useManifest } from "../data/loaders";
import { Loading, ErrorView } from "../components/ui";
export default function Layout() {
  const manifest = useManifest(),
    navigate = useNavigate(),
    location = useLocation();
  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if (
        event.key === "/" &&
        !["INPUT", "TEXTAREA", "SELECT"].includes(
          (event.target as HTMLElement)?.tagName,
        )
      ) {
        event.preventDefault();
        const input = document.querySelector<HTMLInputElement>("[data-search]");
        if (input) input.focus();
        else navigate("/search");
      }
    };
    document.addEventListener("keydown", handle);
    return () => document.removeEventListener("keydown", handle);
  }, [navigate]);
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [location.pathname]);
  return (
    <>
      <a
        className="skip-link"
        href="#content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("content")?.focus();
        }}
      >
        {t("app.skip")}
      </a>
      <header className="site-header">
        <NavLink to="/" className="brand">
          <span className="brand-mark">{t("brand.mark")}</span>
          <span>
            {t("brand.name")}
            <small>{t("brand.subtitle")}</small>
          </span>
        </NavLink>
        <nav aria-label={t("app.navigation")}>
          <NavLink to="/" end>
            {t("nav.library")}
          </NavLink>
          <NavLink to="/search">{t("nav.search")}</NavLink>
          <NavLink to="/tags">{t("nav.tags")}</NavLink>
          <NavLink to="/concepts">{t("nav.concepts")}</NavLink>
          <NavLink to="/timeline">{t("nav.timeline")}</NavLink>
          <NavLink to="/claims">{t("nav.claims")}</NavLink>
          <NavLink to="/about">{t("nav.about")}</NavLink>
        </nav>
        <div className="header-end">
          <span className="source-label">
            {t("app.source", { source: source.kind })}
          </span>
          <ThemeSwitch />
        </div>
      </header>
      <main id="content" tabIndex={-1}>
        {manifest.error ? (
          <ErrorView
            error={manifest.error}
            retry={() => void manifest.refetch()}
          />
        ) : (
          <Suspense fallback={<Loading />}>
            <Outlet />
          </Suspense>
        )}
      </main>
    </>
  );
}
