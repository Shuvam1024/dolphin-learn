import { defineConfig, devices } from "@playwright/test";

const apiPython = process.env.API_PYTHON ?? "../services/api/.venv/bin/python";

/** Golden release suite — curated specs for first ship (S103). */
export default defineConfig({
  testDir: "./e2e",
  testMatch: [
    "**/quick-learn.spec.ts",
    "**/math-windows.spec.ts",
    "**/e2e-03-organized.spec.ts",
    "**/studio-v2.spec.ts",
    "**/free-recall.spec.ts",
    "**/tutor.spec.ts",
    "**/refresh-resume.spec.ts",
    "**/snooze.spec.ts",
    "**/general-route.spec.ts",
    "**/wizard-v2.spec.ts",
    "**/settings.spec.ts",
    "**/no-raw-keys.spec.ts",
    "**/security.spec.ts",
    "**/release/catalog.spec.ts",
  ],
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  timeout: 90_000,
  webServer: [
    {
      command: `${apiPython} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: "../services/api",
      url: "http://127.0.0.1:8000/health",
      // Locally Makefile starts API with the correct AI_* env; CI spawns fresh.
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        DATABASE_URL:
          process.env.DATABASE_URL ??
          "postgresql+psycopg://dolphin:dolphin@127.0.0.1:5432/dolphin",
        ENVIRONMENT: "development",
        NEXT_PUBLIC_ENVIRONMENT: "development",
        AI_PROVIDER: process.env.AI_PROVIDER ?? "",
        AI_GATEWAY_ENABLED: process.env.AI_GATEWAY_ENABLED ?? "",
        DOLPHIN_E2E_FAST_CLOCK: "1",
      },
    },
    {
      command: "npx next dev --turbopack -p 3000",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        NEXT_PUBLIC_ENVIRONMENT: "development",
      },
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
