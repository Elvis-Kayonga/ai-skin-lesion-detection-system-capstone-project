import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  // Unit tests (Vitest) live next to the code in src/. The browser tests in e2e/ belong to Playwright.
  test: { include: ["src/**/*.test.{js,jsx}"] },
});
