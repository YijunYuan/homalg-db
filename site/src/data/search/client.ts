import type { SearchRecord } from "../types";
import type { SearchQuery, SearchResult } from "../source";
import type { SerializedIndex } from "./engine";
/** The worker is only constructed after the user enters a search-capable route. */
export class SearchClient {
  private worker: Worker;
  private sequence = 0;
  private pending = new Map<
    number,
    { resolve: (data: unknown) => void; reject: (reason: Error) => void }
  >();
  constructor() {
    this.worker = new Worker(new URL("./worker.ts", import.meta.url), {
      type: "module",
    });
    this.worker.onmessage = ({ data }) => {
      const promise = this.pending.get(data.request);
      if (data.error) promise?.reject(new Error(data.error));
      else promise?.resolve(data.data);
      this.pending.delete(data.request);
    };
    this.worker.onerror = () => {
      for (const promise of this.pending.values())
        promise.reject(new Error("search worker failed"));
      this.pending.clear();
    };
  }
  private call<T>(action: string, data: object): Promise<T> {
    return new Promise((resolve, reject) => {
      const request = this.sequence++;
      this.pending.set(request, {
        resolve: (value) => resolve(value as T),
        reject,
      });
      this.worker.postMessage({ request, action, ...data });
    });
  }
  init(
    records: SearchRecord[],
    hash: string,
    serialized?: SerializedIndex,
  ): Promise<boolean> {
    return this.call("init", { records, hash, serialized });
  }
  query(query: SearchQuery): Promise<SearchResult> {
    return this.call("query", { query });
  }
  dispose(): void {
    this.worker.terminate();
  }
}
