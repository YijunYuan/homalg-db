/** Shared browser/API boundary. All records come from the generated schema types. */
import type {
  SiteManifest,
  SiteDocumentBundle,
  SiteNodeRecord,
  SiteTaxonomy,
  SiteGlobalGraph,
  SiteGlobalDag,
  SiteEvolution,
  SiteHealth,
  Edge,
  SearchRecord,
} from "./types";
export type Manifest = SiteManifest;
export type DocumentBundle = SiteDocumentBundle;
export type NodeRecord = SiteNodeRecord;
export type Taxonomy = SiteTaxonomy;
export type GlobalGraph = SiteGlobalGraph;
export type GlobalDagShard = SiteGlobalDag;
export type EvolutionRecord = SiteEvolution;
export const SUPPORTED_SCHEMA_VERSION = 1;
export type Direction = "up" | "down";
export interface SearchQuery {
  q?: string;
  doc?: string;
  author?: string;
  year?: string;
  kind?: string;
  headline?: string;
  status?: string;
  tags?: string;
  concepts?: string;
  fidelity?: string;
  mathlib?: string;
  aux?: string;
  deps?: string;
  dir?: Direction;
  depth?: number;
  sort?: string;
  page?: number;
}
export interface SearchResult {
  records: SearchRecord[];
  total: number;
  page: number;
  page_size: number;
  facets: Record<string, Record<string, number>>;
  truncated: boolean;
}
export type NeighborEdges = Edge[] & { truncated?: boolean };
export interface DataSource {
  readonly kind: "static" | "api";
  manifest(): Promise<Manifest>;
  document(docKey: string, chapter?: string): Promise<DocumentBundle>;
  node(id: string): Promise<NodeRecord>;
  search(query: SearchQuery): Promise<SearchResult>;
  neighbors(id: string, dir: Direction, depth: number): Promise<NeighborEdges>;
  taxonomy(): Promise<Taxonomy>;
  globalGraph(): Promise<GlobalGraph>;
  globalDag(range: [number, number]): Promise<GlobalDagShard>;
  evolution(concept: string): Promise<EvolutionRecord | null>;
  health(): Promise<SiteHealth>;
  resourceUrl(file: string): string;
}
export class DataError extends Error {
  constructor(
    readonly code: "schema" | "redeployed" | "missing" | "network",
    readonly detail = "",
  ) {
    super(`${code}: ${detail}`);
  }
}
export function nodeParts(id: string): [string, string] {
  const match =
    /^([A-Z][A-Za-z]*[0-9]{4}[A-Za-z0-9]*)\.([A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*)$/.exec(
      id,
    );
  if (!match) throw new DataError("missing", id);
  return [match[1], match[2]];
}
export function searchParams(query: SearchQuery): URLSearchParams {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query))
    if (value !== undefined && value !== "") params.set(key, String(value));
  return params;
}
