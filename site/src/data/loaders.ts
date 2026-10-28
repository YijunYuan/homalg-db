/** Components access data exclusively through these query hooks. */
import { useQuery } from "@tanstack/react-query";
import { StaticJsonSource } from "./static";
import { ApiSource } from "./api";
import type { DataSource, Direction, SearchQuery } from "./source";
const params = new URLSearchParams(window.location.search);
const api =
  params.get("api") || import.meta.env.VITE_API_URL || window.location.origin;
export const source: DataSource =
  (params.get("source") || import.meta.env.VITE_DATA_SOURCE) === "api"
    ? new ApiSource(api)
    : new StaticJsonSource();
export const useManifest = () =>
  useQuery({
    queryKey: ["manifest"],
    queryFn: () => source.manifest(),
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  });
export const useDocument = (doc: string, chapter?: string, enabled = true) => {
  const manifest = useManifest();
  const entry = manifest.data?.documents.find((item) => item.doc_key === doc);
  return useQuery({
    queryKey: ["document", doc, entry?.graph_hash, chapter],
    queryFn: () => source.document(doc, chapter),
    enabled: !!manifest.data && enabled,
    staleTime: Infinity,
  });
};
export const useNode = (id: string) => {
  const manifest = useManifest();
  return useQuery({
    queryKey: ["node", id, manifest.data?.commit],
    queryFn: () => source.node(id),
    enabled: !!manifest.data && !!id,
    staleTime: Infinity,
  });
};
export const useSearch = (query: SearchQuery) => {
  const manifest = useManifest();
  return useQuery({
    queryKey: ["search", manifest.data?.search_hash, query],
    queryFn: () => source.search(query),
    enabled: !!manifest.data,
    staleTime: Infinity,
  });
};
export const useTaxonomy = () =>
  useQuery({
    queryKey: ["taxonomy"],
    queryFn: () => source.taxonomy(),
    staleTime: 60_000,
  });
export const useGlobalGraph = () =>
  useQuery({
    queryKey: ["global-graph"],
    queryFn: () => source.globalGraph(),
    staleTime: 60_000,
  });
export const useGlobalDag = (range?: [number, number]) =>
  useQuery({
    queryKey: ["global-dag", range],
    queryFn: () => source.globalDag(range!),
    enabled: !!range,
    staleTime: Infinity,
  });
export const useEvolution = (concept: string) =>
  useQuery({
    queryKey: ["evolution", concept],
    queryFn: () => source.evolution(concept),
    staleTime: 60_000,
  });
export const useHealth = () =>
  useQuery({
    queryKey: ["health"],
    queryFn: () => source.health(),
    staleTime: 60_000,
  });
export const useNeighbors = (
  id: string,
  direction: Direction,
  depth: number,
  enabled: boolean,
) =>
  useQuery({
    queryKey: ["neighbors", id, direction, depth],
    queryFn: () => source.neighbors(id, direction, depth),
    enabled,
    staleTime: 60_000,
  });
