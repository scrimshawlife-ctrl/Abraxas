import { defineConfig } from "vitest/config";

export default defineConfig({
  // This package uses no CSS, but Vite's PostCSS loader searches UP the directory
  // tree and finds the repository-root postcss.config.js, which requires tailwindcss
  // and autoprefixer -- neither installed here. Declaring an inline (empty) PostCSS
  // config stops that upward search, so `vitest run` does not depend on an unrelated
  // root config. Previously this never surfaced because `npm ci` failed first.
  css: {
    postcss: { plugins: [] },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
  },
});
