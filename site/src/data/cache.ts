/** Best-effort IndexedDB caches never block a usable in-memory result. */
import { openDB } from "idb";
const database = () =>
  openDB("homalg-cache", 1, {
    upgrade(db) {
      db.createObjectStore("entries");
    },
  });
export async function cached<T>(key: string): Promise<T | undefined> {
  try {
    const db = await database();
    const value = await db.get("entries", key);
    if (value) await db.put("entries", { ...value, at: Date.now() }, key);
    db.close();
    return value?.data;
  } catch {
    return undefined;
  }
}
export async function cache(
  key: string,
  data: unknown,
  limit = 20,
): Promise<void> {
  try {
    const db = await database();
    const tx = db.transaction("entries", "readwrite");
    await tx.store.put({ data, at: Date.now() }, key);
    const entries = await tx.store.getAll();
    const keys = await tx.store.getAllKeys();
    const family = key.split(":")[0];
    const oldest = keys
      .map((id, i) => ({ id, at: entries[i].at }))
      .filter(({ id }) => String(id).split(":")[0] === family)
      .sort((a, b) => a.at - b.at);
    for (const item of oldest.slice(0, Math.max(0, oldest.length - limit)))
      await tx.store.delete(item.id);
    await tx.done;
    db.close();
  } catch {
    /* Private browsing and storage limits must not break the site. */
  }
}
