import { defineConfig, devices } from "@playwright/test";

const apiPython = process.env.API_PYTHON ?? ".venv/bin/python";

export default defineConfig({
  testDir: "./e2e",
  testIgnore: [/perf\.spec\.ts/],
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:3000",
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
        AI_PROVIDER: process.env.AI_PROVIDER ?? "",
        AI_GATEWAY_ENABLED: process.env.AI_GATEWAY_ENABLED ?? "",
      },
    },
    {
      command: "npx next dev --turbopack -p 3000",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
