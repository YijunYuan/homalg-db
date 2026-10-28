/** Static JSON source with manifest revalidation and one retry across deployments. */
import {
  DataError,
  SUPPORTED_SCHEMA_VERSION,
  nodeParts,
  type DataSource,
  type Manifest,
  type DocumentBundle,
  type NodeRecord,
  type SearchQuery,
  type SearchResult,
  type Direction,
  type Taxonomy,
  type GlobalGraph,
  type GlobalDagShard,
  type EvolutionRecord,
} from "./source";
import type { SearchRecord, SiteHealth } from "./types";
import { resolveRetired, resolveVocabulary } from "./retired";
import { neighbors } from "./graph/neighbors";
import type { SearchClient } from "./search/client";
import type { SerializedIndex } from "./search/engine";
type Fetcher = typeof fetch;
type SearchRunner = Pick<SearchClient, "init" | "query"> &
  Partial<Pick<SearchClient, "dispose">>;
export class StaticJsonSource implements DataSource {
  readonly kind = "static";
  private current?: Manifest;
  private documentCache = new Map<string, Promise<DocumentBundle>>();
  private nodeCache = new Map<string, Promise<NodeRecord>>();
  private searchPromises = new Map<string, Promise<SearchRunner>>();
  constructor(
    private base = import.meta.env.BASE_URL,
    private fetcher: Fetcher = (input, init) => fetch(input, init),
    private runner?: () => Promise<SearchRunner>,
  ) {}
  resourceUrl(file: string): string {
    return `${this.base.replace(/\/$/, "")}/data/${file}`;
  }
  private async json<T>(file: string, cache?: RequestCache): Promise<T> {
    let response: Response;
    try {
      response = await this.fetcher(this.resourceUrl(file), { cache });
    } catch (error) {
      throw new DataError("network", String(error));
    }
    if (!response.ok)
      throw new DataError(
        response.status === 404 ? "missing" : "network",
        file,
      );
    try {
      return (await response.json()) as T;
    } catch {
      throw new DataError("network", file);
    }
  }
  private async readManifest(cache: RequestCache): Promise<Manifest> {
    const data = await this.json<Manifest>("manifest.json", cache);
    if (Number(data.schema_version) !== SUPPORTED_SCHEMA_VERSION)
      throw new DataError("schema", String(data.schema_version));
    if (this.current && this.current.commit !== data.commit) {
      this.nodeCache.clear();
      this.documentCache.clear();
    }
    this.current = data;
    return data;
  }
  manifest(): Promise<Manifest> {
    return this.readManifest("no-cache");
  }
  private snapshot(): Promise<Manifest> {
    return this.current ? Promise.resolve(this.current) : this.manifest();
  }
  private async addressed<T>(
    select: (manifest: Manifest) => string | undefined,
  ): Promise<T> {
    const file = select(await this.snapshot());
    if (!file) throw new DataError("missing");
    try {
      return await this.json<T>(file);
    } catch (error) {
      if (!(error instanceof DataError) || error.code !== "missing")
        throw error;
      const next = select(await this.readManifest("reload"));
      if (!next) throw new DataError("redeployed");
      try {
        return await this.json<T>(next, "reload");
      } catch (retry) {
        if (retry instanceof DataError && retry.code === "missing")
          throw new DataError("redeployed");
        throw retry;
      }
    }
  }
  async document(docKey: string): Promise<DocumentBundle> {
    const manifest = await this.snapshot();
    const entry = manifest.documents.find((doc) => doc.doc_key === docKey);
    if (!entry) throw new DataError("missing", docKey);
    const key = `${docKey}:${entry.graph_hash}`;
    if (!this.documentCache.has(key))
      this.documentCache.set(
        key,
        this.addressed(
          (data) =>
            data.documents.find((doc) => doc.doc_key === docKey)?.files
              .document,
        ),
      );
    try {
      return await this.documentCache.get(key)!;
    } catch (error) {
      this.documentCache.delete(key);
      throw error;
    }
  }
  async node(id: string): Promise<NodeRecord> {
    const target = resolveRetired(id, (await this.snapshot()).retired);
    if (target === null) throw new DataError("missing", id);
    id = target;
    const [doc, local] = nodeParts(id);
    if (!this.nodeCache.has(id))
      this.nodeCache.set(id, this.json(`nodes/${doc}/${local}.json`));
    try {
      return await this.nodeCache.get(id)!;
    } catch (error) {
      this.nodeCache.delete(id);
      throw error;
    }
  }
  private async searcher(query: SearchQuery): Promise<SearchRunner> {
    const manifest = await this.snapshot();
    const partitioned = manifest.documents.some(
      (doc) => doc.files.search_index,
    );
    const chosen = partitioned
      ? query.doc?.split(",").filter(Boolean)
      : undefined;
    const documents = manifest.documents.filter(
      (doc) => !chosen || chosen.includes(doc.doc_key),
    );
    const scope = documents
      .map((doc) => doc.doc_key)
      .sort()
      .join(",");
    const key = `${manifest.search_hash}:${__SEARCH_OPTIONS_HASH__}:${scope}`;
    if (!this.searchPromises.has(key)) {
      const pending = (async () => {
        const shards = await Promise.all(
          documents.map((doc) =>
            this.addressed<SearchRecord[]>(
              (data) =>
                data.documents.find((item) => item.doc_key === doc.doc_key)
                  ?.files.search_shard,
            ),
          ),
        );
        const snapshot = await this.snapshot();
        const compatible =
          snapshot.prerender.search_index &&
          snapshot.prerender.search_options_hash === __SEARCH_OPTIONS_HASH__;
        const file =
          documents.length === 1
            ? snapshot.documents.find(
                (doc) => doc.doc_key === documents[0].doc_key,
              )?.files.search_index
            : undefined;
        const useGlobal = documents.length === snapshot.documents.length;
        const serialized =
          compatible && (file || (useGlobal && snapshot.search_index_file))
            ? await this.addressed<SerializedIndex>((data) =>
                file
                  ? data.documents.find(
                      (doc) => doc.doc_key === documents[0].doc_key,
                    )?.files.search_index
                  : data.search_index_file,
              ).catch(() => undefined)
            : undefined;
        const client = this.runner
          ? await this.runner()
          : new (await import("./search/client")).SearchClient();
        await client.init(shards.flat(), key, serialized);
        return client;
      })();
      this.searchPromises.set(key, pending);
      pending.catch(() => this.searchPromises.delete(key));
      if (this.searchPromises.size > 3) {
        const oldest = this.searchPromises.keys().next().value!;
        const retired = this.searchPromises.get(oldest)!;
        this.searchPromises.delete(oldest);
        // Retired scopes are released after pending queries have had a turn to settle.
        void retired.then(
          (client) => {
            if (client.dispose) setTimeout(() => client.dispose?.(), 30000);
          },
          () => undefined,
        );
      }
    }
    return this.searchPromises.get(key)!;
  }
  async search(query: SearchQuery): Promise<SearchResult> {
    if (query.deps) {
      const target = resolveRetired(
        query.deps,
        (await this.snapshot()).retired,
      );
      if (target === null) throw new DataError("missing", query.deps);
      query = { ...query, deps: target };
    }
    const request = { ...query };
    if (query.tags || query.concepts) {
      const taxonomy = await this.taxonomy();
      for (const field of ["tags", "concepts"] as const)
        if (query[field])
          request[field] = [
            ...new Set(
              query[field]!.split(",").map((id) =>
                resolveVocabulary(id, taxonomy[field]),
              ),
            ),
          ].join(",");
      const selected = new Set(request.tags?.split(",").filter(Boolean));
      let changed = true;
      while (changed) {
        changed = false;
        for (const tag of taxonomy.tags)
          if (tag.parent && selected.has(tag.parent) && !selected.has(tag.id)) {
            selected.add(tag.id);
            changed = true;
          }
      }
      if (request.tags) request.tags = [...selected].join(",");
    }
    const client = await this.searcher(request);
    if (!query.deps) return client.query(request);
    const edges = await this.neighbors(
      query.deps,
      query.dir || "down",
      query.depth || 1,
    );
    const ids = new Set(edges.flatMap((edge) => [edge.from, edge.to]));
    ids.delete(query.deps);
    // Dependency results are capped to 500. Gather filtered pages before intersecting.
    const first = await client.query({ ...request, page: 1 });
    const pages = await Promise.all(
      Array.from(
        { length: Math.max(0, Math.ceil(first.total / first.page_size) - 1) },
        (_, i) => client.query({ ...request, page: i + 2 }),
      ),
    );
    const all = [first, ...pages]
      .flatMap((page) => page.records)
      .filter((record) => ids.has(record.id));
    const page = Math.max(1, request.page || 1);
    return {
      ...first,
      records: all.slice((page - 1) * first.page_size, page * first.page_size),
      page,
      total: all.length,
      truncated: !!edges.truncated,
    };
  }
  async neighbors(id: string, direction: Direction, depth: number) {
    const target = resolveRetired(id, (await this.snapshot()).retired);
    if (target === null) throw new DataError("missing", id);
    return neighbors(this, target, direction, depth);
  }
  taxonomy(): Promise<Taxonomy> {
    return this.json("taxonomy.json");
  }
  globalGraph(): Promise<GlobalGraph> {
    return this.addressed((manifest) => manifest.global_graph_file);
  }
  async globalDag([first, last]: [number, number]): Promise<GlobalDagShard> {
    const manifest = await this.snapshot();
    const files = manifest.global_dag_files.filter(
      (file) => file.to >= first && file.from <= last,
    );
    const shards = await Promise.all(
      files.map((file) =>
        this.addressed<GlobalDagShard>(
          (current) =>
            current.global_dag_files.find(
              (item) => item.from === file.from && item.to === file.to,
            )?.file,
        ),
      ),
    );
    const nodes = [
      ...new Map(
        shards
          .flatMap((shard) => shard.nodes)
          .filter((node) => node.year >= first && node.year <= last)
          .map((node) => [node.id, node]),
      ).values(),
    ];
    const ids = new Set(nodes.map((node) => node.id));
    const edges = [
      ...new Map(
        shards
          .flatMap((shard) => shard.edges)
          .filter((edge) => ids.has(edge.from) && ids.has(edge.to))
          .map((edge) => [JSON.stringify(edge), edge]),
      ).values(),
    ];
    return { range: [first, last], nodes, edges };
  }
  async evolution(concept: string): Promise<EvolutionRecord | null> {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(concept))
      throw new DataError("missing", concept);
    try {
      return await this.json(`evolution/${concept}.json`);
    } catch (error) {
      if (error instanceof DataError && error.code === "missing") return null;
      throw error;
    }
  }
  health(): Promise<SiteHealth> {
    return this.json("health.json");
  }
}
