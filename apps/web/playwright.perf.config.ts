import { defineConfig, devices } from "@playwright/test";

/**
 * S51 perf project: measures against a production Next build on :3100.
 * API still comes from the default reuse on :8000 when available, else starts one.
 */
const apiPython = process.env.API_PYTHON ?? "../services/api/.venv/bin/python";

export default defineConfig({
  testDir: "./e2e",
  testMatch: /perf\.spec\.ts/,
  fullyParallel: false,
  retries: 0,
  timeout: 180_000,
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "off",
  },
  webServer: [
    {
      command: `${apiPython} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: "../services/api",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        DATABASE_URL:
          process.env.DATABASE_URL ??
          "postgresql+psycopg://dolphin:dolphin@127.0.0.1:5432/dolphin",
        ENVIRONMENT: "development",
      },
    },
    {
      command: "npx next build && npx next start -p 3100",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: !process.env.CI,
      timeout: 300_000,
      env: {
        ...process.env,
        PORT: "3100",
      },
    },
  ],
  projects: [{ name: "perf", use: { ...devices["Desktop Chrome"] } }],
});
