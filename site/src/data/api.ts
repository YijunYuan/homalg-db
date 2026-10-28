/** API adapter returns the same contracts as static JSON files. */
import {
  DataError,
  SUPPORTED_SCHEMA_VERSION,
  nodeParts,
  searchParams,
  type DataSource,
  type Manifest,
  type DocumentBundle,
  type NodeRecord,
  type SearchQuery,
  type SearchResult,
  type Direction,
  type NeighborEdges,
  type Taxonomy,
  type GlobalGraph,
  type GlobalDagShard,
  type EvolutionRecord,
} from "./source";
import type { SiteHealth } from "./types";
export class ApiSource implements DataSource {
  readonly kind = "api";
  constructor(
    private base: string,
    private fetcher: typeof fetch = (input, init) => fetch(input, init),
  ) {}
  resourceUrl(file: string): string {
    return `${this.base.replace(/\/$/, "")}/data/${file}`;
  }
  private async get<T>(route: string): Promise<T> {
    let response: Response;
    try {
      response = await this.fetcher(
        `${this.base.replace(/\/$/, "")}/api/${route}`,
        { cache: "no-cache" },
      );
    } catch (error) {
      throw new DataError("network", String(error));
    }
    if (!response.ok)
      throw new DataError(
        response.status === 404 ? "missing" : "network",
        route,
      );
    const data = (await response.json()) as T;
    if (
      Array.isArray(data) &&
      response.headers.get("X-Homalg-Truncated") === "true"
    )
      Object.assign(data, { truncated: true });
    return data;
  }
  async manifest(): Promise<Manifest> {
    const manifest = await this.get<Manifest>("manifest");
    if (Number(manifest.schema_version) !== SUPPORTED_SCHEMA_VERSION)
      throw new DataError("schema", String(manifest.schema_version));
    return manifest;
  }
  document(docKey: string, chapter?: string): Promise<DocumentBundle> {
    return this.get(
      `documents/${encodeURIComponent(docKey)}${chapter !== undefined ? `?chapter=${encodeURIComponent(chapter)}` : ""}`,
    );
  }
  node(id: string): Promise<NodeRecord> {
    return this.get(`nodes/${nodeParts(id).map(encodeURIComponent).join("/")}`);
  }
  search(query: SearchQuery): Promise<SearchResult> {
    return this.get(`search?${searchParams(query)}`);
  }
  neighbors(id: string, dir: Direction, depth: number): Promise<NeighborEdges> {
    return this.get(
      `nodes/${nodeParts(id).map(encodeURIComponent).join("/")}/neighbors?dir=${dir}&depth=${Math.min(3, Math.max(1, depth))}`,
    );
  }
  taxonomy(): Promise<Taxonomy> {
    return this.get("taxonomy");
  }
  globalGraph(): Promise<GlobalGraph> {
    return this.get("global-graph");
  }
  globalDag([from, to]: [number, number]): Promise<GlobalDagShard> {
    return this.get(`global-dag?from=${from}&to=${to}`);
  }
  async evolution(concept: string): Promise<EvolutionRecord | null> {
    try {
      return await this.get(`evolution/${encodeURIComponent(concept)}`);
    } catch (error) {
      if (error instanceof DataError && error.code === "missing") return null;
      throw error;
    }
  }
  health(): Promise<SiteHealth> {
    return this.get("health");
  }
}
