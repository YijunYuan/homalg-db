// @vitest-environment node
import { expect, it } from "vitest";
import { styles } from "../features/blueprint/Blueprint";
function contrast(a: string, b: string) {
  const lum = (hex: string) => {
    const rgb = hex
      .slice(1)
      .match(/../g)!
      .map((v) => parseInt(v, 16) / 255)
      .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
    return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  };
  const [x, y] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (x + 0.05) / (y + 0.05);
}
it("keeps graph text readable and node outlines discernible in both page themes", () => {
  const base = styles[0].style as Record<string, unknown>;
  for (const style of styles.filter((item) =>
    item.selector.startsWith("node"),
  )) {
    const values = { ...base, ...style.style } as Record<string, string>;
    expect(
      contrast(values.color, values["background-color"]),
      style.selector,
    ).toBeGreaterThanOrEqual(4.5);
    // The map uses a fixed light canvas in both page themes. WCAG permits a contrasting boundary.
    for (const canvas of ["#f6f8f6", "#e8efe9"])
      expect(
        contrast(values["border-color"], canvas),
        style.selector,
      ).toBeGreaterThanOrEqual(3);
  }
});
