import { useEffect, useState } from "react";
import { DropdownMenu } from "radix-ui";
import { t } from "../i18n/t";
type Theme = "light" | "dark" | "system";
export function ThemeSwitch() {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const value = localStorage.getItem("homalg-theme");
      return value === "light" || value === "dark" ? value : "system";
    } catch {
      return "system";
    }
  });
  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const update = () =>
      document.documentElement.classList.toggle(
        "dark",
        theme === "dark" || (theme === "system" && media.matches),
      );
    update();
    media.addEventListener("change", update);
    try {
      localStorage.setItem("homalg-theme", theme);
    } catch {
      /* Optional persistence. */
    }
    return () => media.removeEventListener("change", update);
  }, [theme]);
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger className="icon-button" aria-label={t("app.theme")}>
        {theme === "dark" ? "☾" : "☼"}
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content className="menu" align="end">
          <DropdownMenu.RadioGroup
            value={theme}
            onValueChange={(value) => setTheme(value as Theme)}
          >
            <DropdownMenu.RadioItem className="menu-item" value="light">
              {t("app.light")}
            </DropdownMenu.RadioItem>
            <DropdownMenu.RadioItem className="menu-item" value="dark">
              {t("app.dark")}
            </DropdownMenu.RadioItem>
            <DropdownMenu.RadioItem className="menu-item" value="system">
              {t("app.system")}
            </DropdownMenu.RadioItem>
          </DropdownMenu.RadioGroup>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
