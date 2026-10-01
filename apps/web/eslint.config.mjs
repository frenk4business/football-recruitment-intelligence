import js from "@eslint/js";
import tseslint from "typescript-eslint";
export default tseslint.config(
  { ignores: [".next/**", "out/**", "next-env.d.ts", "src/lib/contracts.ts"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: [
      "scripts/performance.mjs",
      "scripts/players-performance.mjs",
      "scripts/ui-review.mjs",
      "scripts/product-review.mjs",
    ],
    languageOptions: {
      globals: {
        window: "readonly",
        PerformanceObserver: "readonly",
        document: "readonly",
        innerWidth: "readonly",
        performance: "readonly",
        Event: "readonly",
        URLSearchParams: "readonly",
        location: "readonly",
      },
    },
  },
  {
    files: ["**/*.mjs"],
    languageOptions: {
      globals: {
        process: "readonly",
        console: "readonly",
        Buffer: "readonly",
        URL: "readonly",
      },
    },
  },
);
