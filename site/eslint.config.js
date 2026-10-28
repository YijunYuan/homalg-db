import js from "@eslint/js";
import tseslint from "typescript-eslint";
import react from "eslint-plugin-react";
export default tseslint.config(
  {
    ignores: ["dist/**", "node_modules/**", "src/data/types.ts", "fixtures/**"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx,mjs}"],
    languageOptions: {
      globals: {
        window: "readonly",
        document: "readonly",
        navigator: "readonly",
        fetch: "readonly",
        URL: "readonly",
        URLSearchParams: "readonly",
        Worker: "readonly",
        MessageEvent: "readonly",
        Response: "readonly",
        Request: "readonly",
        self: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        localStorage: "readonly",
        sessionStorage: "readonly",
        matchMedia: "readonly",
        console: "readonly",
        process: "readonly",
        React: "readonly",
        __SEARCH_OPTIONS_HASH__: "readonly",
      },
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_" },
      ],
    },
  },
  {
    files: ["**/*.tsx"],
    plugins: { react },
    settings: { react: { version: "detect" } },
    rules: {
      "react/jsx-no-literals": [
        "error",
        {
          noStrings: true,
          ignoreProps: true,
          allowedStrings: ["⌕", "×", "↗", " · ", ": ", "—", "–", " (", ")"],
        },
      ],
      "no-restricted-syntax": [
        "error",
        {
          selector:
            "JSXAttribute[name.name=/^(aria-label|aria-description|title|placeholder|alt)$/] > Literal",
          message: "Use a translation key for visible attributes.",
        },
      ],
    },
  },
);
