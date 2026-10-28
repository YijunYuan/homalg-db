import strings from "./en.json";
/** Small English-only dictionary; identifiers and source prose are never translated. */
export function t(
  key: string,
  params: Record<string, string | number> = {},
): string {
  const value = (strings as Record<string, string>)[key];
  if (value === undefined) throw new Error(`Missing UI text: ${key}`);
  return value.replace(/\{([^}]+)\}/g, (_, name: string) =>
    String(params[name] ?? `{${name}}`),
  );
}
