import { createIndex, runSearch, type SerializedIndex } from "./engine";
import { cache, cached } from "../cache";
import type { SearchRecord } from "../types";
import type { SearchQuery } from "../source";
let records: SearchRecord[] = [];
let index: Awaited<ReturnType<typeof createIndex>>;
self.onmessage = async (
  event: MessageEvent<{
    request: number;
    action: string;
    records: SearchRecord[];
    serialized?: SerializedIndex;
    hash: string;
    query: SearchQuery;
  }>,
) => {
  const { request, action } = event.data;
  try {
    if (action === "init") {
      records = event.data.records;
      const key = `search:${event.data.hash}`;
      const stored = await cached<SerializedIndex>(key);
      index = await createIndex(records, event.data.serialized || stored);
      if (!stored) void cache(key, index.toJSON(), 3);
      self.postMessage({ request, data: true });
    } else {
      self.postMessage({
        request,
        data: runSearch(index, records, event.data.query),
      });
    }
  } catch (error) {
    self.postMessage({ request, error: String(error) });
  }
};
