// End-to-end tests: real browsers drive the real app (React + FastAPI + the trained model).
// The tests start their own backend and frontend on separate ports with a temporary database,
// so they never touch your real data or a dev server you already have running.
// Run:  npx playwright test            (all browsers)   |   npx playwright test --project=firefox
import { defineConfig, devices } from "@playwright/test";
import os from "node:os";
import path from "node:path";

const API_PORT = 8010;
const WEB_PORT = 5180;
const TMP = path.join(os.tmpdir(), `skin-e2e-${process.pid}`);
const PYTHON = process.env.E2E_PYTHON
  || (process.platform === "win32" ? "../backend/.venv/Scripts/python.exe" : "../backend/.venv/bin/python");

// Chromium and Firefox can use a built-in fake camera; WebKit cannot, so camera tests skip there.
const chromiumCamera = { args: ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"] };
const firefoxCamera = { firefoxUserPrefs: { "media.navigator.streams.fake": true, "media.navigator.permission.disabled": true } };

export default defineConfig({
  testDir: "./e2e",
  timeout: 180_000,             // the first prediction on a laptop CPU can take tens of seconds
  expect: { timeout: 120_000 },
  workers: 1,                   // one model, one prediction at a time: keeps timings honest on a laptop
  reporter: [["list"], ["json", { outputFile: "test-results/e2e_results.json" }]],   // raw report stays local
  use: { baseURL: `http://localhost:${WEB_PORT}`, trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"], launchOptions: chromiumCamera, permissions: ["camera"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"], launchOptions: firefoxCamera } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
    { name: "mobile-chrome", use: { ...devices["Pixel 7"], launchOptions: chromiumCamera, permissions: ["camera"] } },
    { name: "mobile-safari", use: { ...devices["iPhone 13"] } },
  ],
  webServer: [
    {
      command: `"${PYTHON}" -m uvicorn app.main:app --port ${API_PORT}`,
      cwd: "../backend",
      url: `http://localhost:${API_PORT}/health`,
      timeout: 180_000,
      reuseExistingServer: false,
      env: {
        SECRET_KEY: "e2e-test-secret-key-that-is-long-enough-0123456789",
        DATABASE_URL: `sqlite:///${path.join(TMP, "e2e.db").replace(/\\/g, "/")}`,
        STORAGE_DIR: path.join(TMP, "storage"),
        CORS_ORIGINS: JSON.stringify([`http://localhost:${WEB_PORT}`, `http://127.0.0.1:${WEB_PORT}`]),
      },
    },
    {
      command: `npx vite --port ${WEB_PORT} --strictPort`,
      url: `http://localhost:${WEB_PORT}`,
      timeout: 60_000,
      reuseExistingServer: false,
      env: { VITE_API_URL: `http://localhost:${API_PORT}` },
    },
  ],
});
