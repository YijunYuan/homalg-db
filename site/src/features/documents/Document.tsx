import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router";
import { Tabs } from "radix-ui";
import { source, useDocument, useManifest } from "../../data/loaders";
import { ErrorView, Loading } from "../../components/ui";
const blueprintModule = import("../blueprint/Blueprint");
void blueprintModule.catch(() => undefined);
type BlueprintComponent = typeof import("../blueprint/Blueprint").Blueprint;
let loadedBlueprint: BlueprintComponent | undefined;
void blueprintModule.then(
  (module) => {
    loadedBlueprint = module.Blueprint;
  },
  () => undefined,
);
import { NodeList } from "./NodeList";
import { Fidelity } from "./Fidelity";
const Drawer = lazy(() =>
  import("../node/Drawer").then((module) => ({ default: module.Drawer })),
);
import { t } from "../../i18n/t";
export default function Document() {
  const [Blueprint, setBlueprint] = useState(() => loadedBlueprint);
  const [blueprintError, setBlueprintError] = useState<unknown>();
  useEffect(() => {
    let active = true;
    void blueprintModule.then(
      (module) => {
        if (active) setBlueprint(() => module.Blueprint);
      },
      (error) => {
        if (active) setBlueprintError(error);
      },
    );
    return () => {
      active = false;
    };
  }, []);
  const { docKey = "", localId } = useParams(),
    manifest = useManifest(),
    location = useLocation(),
    navigate = useNavigate(),
    [params, setParams] = useSearchParams();
  const [filter, setFilter] = useState(""),
    [chapter, setChapter] = useState(""),
    [headline, setHeadline] = useState(""),
    [expandAux, setExpandAux] = useState(false),
    [direction, setDirection] = useState("DOWN"),
    [edgeMode, setEdgeMode] = useState("all");
  const entry = manifest.data?.documents.find(
    (item) => item.doc_key === docKey,
  );
  const totalNodes = Object.values(entry?.node_counts || {}).reduce(
    (sum, count) => sum + count,
    0,
  );
  const largeApi = source.kind === "api" && totalNodes > 5000;
  const overview = useDocument(docKey, largeApi ? "" : undefined);
  const selected = localId ? `${docKey}.${localId}` : undefined;
  const focusedChapter =
    selected && largeApi
      ? overview.data?.chapters.find((item) => item.node_ids.includes(selected))
          ?.chapter
      : undefined;
  const requestedChapter = largeApi
    ? focusedChapter !== undefined
      ? focusedChapter || "__unsectioned__"
      : chapter
    : undefined;
  const chapterQuery = useDocument(
    docKey,
    requestedChapter,
    largeApi && !!requestedChapter,
  );
  const query = largeApi && requestedChapter ? chapterQuery : overview;
  const chapterOverview = largeApi && !requestedChapter;
  const [savedCollapsed, setCollapsed] = useState<Set<string> | null>(null);
  const collapsed = useMemo(
    () =>
      savedCollapsed ??
      new Set(
        query.data && query.data.nodes.length > 1500
          ? query.data.chapters.map((item) => item.chapter)
          : [],
      ),
    [savedCollapsed, query.data],
  );
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(`chapters:${docKey}`);
      setCollapsed(saved ? new Set(JSON.parse(saved)) : null);
    } catch {
      setCollapsed(null);
    }
  }, [docKey]);
  const toggleChapter = useCallback(
    (key: string) =>
      setCollapsed((old) => {
        const next = new Set(old ?? collapsed);
        if (next.has(key)) next.delete(key);
        else next.add(key);
        try {
          sessionStorage.setItem(
            `chapters:${docKey}`,
            JSON.stringify([...next]),
          );
        } catch {
          /* Optional UI state. */
        }
        return next;
      }),
    [docKey, collapsed],
  );
  const close = useCallback(
    () => navigate(`/doc/${docKey}${location.search}`),
    [docKey, location.search, navigate],
  );
  useEffect(() => {
    if (!selected || !query.data) return;
    const group = query.data.chapters.find((item) =>
      item.node_ids.includes(selected),
    );
    if (group)
      setCollapsed((old) => {
        if (!(old ?? collapsed).has(group.chapter)) return old;
        const next = new Set(old ?? collapsed);
        next.delete(group.chapter);
        return next;
      });
    setChapter("");
    setFilter("");
    setHeadline("");
  }, [selected, query.data]);
  if (query.error) return <ErrorView error={query.error} />;
  if (!query.data || !manifest.data) return <Loading />;
  const bundle = query.data,
    allChapters =
      largeApi && overview.data ? overview.data.chapters : bundle.chapters,
    mobile = matchMedia("(max-width: 767px)").matches;
  const tab = location.pathname.endsWith("/fidelity")
    ? "fidelity"
    : params.get("view") || (mobile ? "list" : "blueprint");
  const nodes = bundle.nodes.filter(
    (node) =>
      (largeApi ||
        !chapter ||
        bundle.chapters
          .find((item) => item.chapter === chapter)
          ?.node_ids.includes(node.id)) &&
      (!filter ||
        `${node.id} ${node.label} ${node.title}`
          .toLowerCase()
          .includes(filter.toLowerCase())) &&
      (!headline || node.headline === headline),
  );
  return (
    <div className={`document-page ${selected ? "with-drawer" : ""}`}>
      <header className="document-header">
        <div>
          <p className="eyebrow">
            {docKey}
            {" · "}
            {bundle.document.year}
          </p>
          <h1>{bundle.document.title}</h1>
          <p className="muted">
            {bundle.document.authors
              .map((author) =>
                [author.given, author.family].filter(Boolean).join(" "),
              )
              .join(", ")}
          </p>
        </div>
        <span className="badge">
          {t("doc.items", {
            count: largeApi ? totalNodes : bundle.nodes.length,
          })}
        </span>
      </header>
      <div className="document-workspace">
        <aside className="chapter-sidebar" aria-label={t("doc.chapters")}>
          <h2>{t("doc.chapters")}</h2>
          <button
            className={!chapter ? "active" : ""}
            onClick={() => {
              setChapter("");
              if (selected) close();
            }}
          >
            {t("doc.allChapters")}
          </button>
          {allChapters.map((item) => (
            <div className="chapter-row" key={item.chapter}>
              <button
                className={chapter === item.chapter ? "active" : ""}
                onClick={() => {
                  setChapter(
                    largeApi ? item.chapter || "__unsectioned__" : item.chapter,
                  );
                  if (selected) close();
                }}
              >
                <span>{item.chapter}</span>
                {item.title}
              </button>
              <button
                className="chapter-toggle"
                aria-label={t("doc.chapterToggle", { chapter: item.chapter })}
                aria-expanded={!collapsed.has(item.chapter)}
                onClick={() =>
                  largeApi
                    ? setChapter(item.chapter || "__unsectioned__")
                    : toggleChapter(item.chapter)
                }
              >
                {collapsed.has(item.chapter) ? "+" : "−"}
              </button>
            </div>
          ))}
        </aside>
        <div className="document-main">
          <Tabs.Root
            value={tab}
            onValueChange={(value) => {
              if (value === "fidelity") navigate(`/doc/${docKey}/fidelity`);
              else if (location.pathname.endsWith("/fidelity"))
                navigate(`/doc/${docKey}?view=${value}`);
              else
                setParams((old) => {
                  old.set("view", value);
                  return old;
                });
            }}
          >
            <Tabs.List className="tabs" aria-label={t("doc.tabs")}>
              <Tabs.Trigger value="blueprint">
                {t("doc.blueprint")}
              </Tabs.Trigger>
              <Tabs.Trigger value="fidelity">{t("doc.fidelity")}</Tabs.Trigger>
              <Tabs.Trigger value="list">{t("doc.list")}</Tabs.Trigger>
            </Tabs.List>
            {tab !== "fidelity" && !chapterOverview && (
              <div className="document-controls">
                <label className="filter-input">
                  <span className="sr-only">{t("doc.filter")}</span>
                  <input
                    data-search
                    value={filter}
                    onChange={(event) => setFilter(event.target.value)}
                    placeholder={t("doc.filter")}
                  />
                </label>
                <label>
                  <span className="sr-only">{t("search.headline")}</span>
                  <select
                    value={headline}
                    onChange={(event) => setHeadline(event.target.value)}
                    aria-label={t("search.headline")}
                  >
                    <option value="">{t("search.all")}</option>
                    {[
                      "in-progress",
                      "statement-complete",
                      "proof-complete",
                      "error",
                    ].map((value) => (
                      <option key={value} value={value}>
                        {t(`enum.HeadlineStatus.${value}`)}
                      </option>
                    ))}
                  </select>
                </label>
                {tab === "blueprint" && (
                  <>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={expandAux}
                        onChange={(event) => setExpandAux(event.target.checked)}
                      />
                      {t("doc.includeAux")}
                    </label>
                    <select
                      aria-label={t("doc.edges")}
                      value={edgeMode}
                      onChange={(event) => setEdgeMode(event.target.value)}
                    >
                      <option value="all">{t("doc.edgesAll")}</option>
                      <option value="declared">{t("doc.edgesDeclared")}</option>
                      <option value="verified">{t("doc.edgesVerified")}</option>
                    </select>
                    <select
                      aria-label={t("doc.direction")}
                      value={direction}
                      onChange={(event) => setDirection(event.target.value)}
                    >
                      <option value="DOWN">{t("doc.down")}</option>
                      <option value="RIGHT">{t("doc.right")}</option>
                    </select>
                    <button
                      onClick={() =>
                        setCollapsed(
                          collapsed.size
                            ? new Set()
                            : new Set(
                                bundle.chapters.map((item) => item.chapter),
                              ),
                        )
                      }
                    >
                      {collapsed.size
                        ? t("doc.expandChapters")
                        : t("doc.collapseChapters")}
                    </button>
                  </>
                )}
              </div>
            )}
            <Tabs.Content value="blueprint">
              {chapterOverview ? (
                <ChapterOverview
                  chapters={bundle.chapters}
                  onSelect={setChapter}
                />
              ) : (
                <>
                  {blueprintError ? (
                    <ErrorView error={blueprintError} />
                  ) : !Blueprint ? (
                    <Loading />
                  ) : (
                    <Blueprint
                      key={bundle.document.doc_key}
                      bundle={bundle}
                      manifest={manifest.data}
                      selected={selected}
                      chapter={largeApi ? "" : chapter}
                      filter={filter}
                      headline={headline}
                      expandAux={expandAux}
                      collapsedChapters={collapsed}
                      onToggleChapter={toggleChapter}
                      direction={direction}
                      edgeMode={edgeMode}
                    />
                  )}
                </>
              )}
            </Tabs.Content>
            <Tabs.Content value="list">
              {chapterOverview ? (
                <ChapterOverview
                  chapters={bundle.chapters}
                  onSelect={setChapter}
                />
              ) : (
                <NodeList nodes={nodes} edges={bundle.edges} />
              )}
            </Tabs.Content>
            <Tabs.Content value="fidelity">
              {chapterOverview ? (
                <ChapterOverview
                  chapters={bundle.chapters}
                  onSelect={setChapter}
                />
              ) : (
                <Fidelity bundle={bundle} />
              )}
            </Tabs.Content>
          </Tabs.Root>
        </div>
        {selected && (
          <Suspense fallback={<Loading />}>
            <Drawer id={selected} onClose={close} />
          </Suspense>
        )}
      </div>
    </div>
  );
}

function ChapterOverview({
  chapters,
  onSelect,
}: {
  chapters: import("../../data/source").DocumentBundle["chapters"];
  onSelect: (chapter: string) => void;
}) {
  return (
    <section className="chapter-overview" aria-label={t("doc.chapterOverview")}>
      <h2>{t("doc.chapterOverview")}</h2>
      <p className="muted">{t("doc.chapterOverviewHelp")}</p>
      <div className="chapter-cards">
        {chapters.map((chapter) => (
          <button
            key={chapter.chapter}
            onClick={() => onSelect(chapter.chapter || "__unsectioned__")}
          >
            <strong>
              {chapter.title || chapter.chapter || t("doc.unsectioned")}
            </strong>
            <span>{t("doc.items", { count: chapter.node_ids.length })}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
