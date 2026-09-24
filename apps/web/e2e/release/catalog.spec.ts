/**
 * Golden release suite (S103).
 * Maps first-ship E2E ids to existing Playwright specs.
 * Run twice: AI_PROVIDER= and AI_PROVIDER=fake.
 */
import { test } from "@playwright/test";

// Re-export by requiring the suite files below via playwright project grep.
// This file documents the mapping; the release config selects the real specs.

test.describe.configure({ mode: "serial" });

test("release suite catalog is documented", async () => {
  const catalog = [
    "E2E-01 quick-learn.spec.ts",
    "E2E-02 math-windows.spec.ts",
    "E2E-03 e2e-03-organized.spec.ts",
    "E2E-05 studio-v2.spec.ts",
    "E2E-06 free-recall.spec.ts",
    "E2E-07 (api) test_e2e_07_delayed_check.py",
    "E2E-08 tutor.spec.ts",
    "E2E-09 refresh-resume.spec.ts",
    "E2E-10 (ai-eval injection) covered by make ai-eval",
    "E2E-12 snooze.spec.ts",
    "E2E-14 general-route.spec.ts",
    "E2E-15 wizard-v2.spec.ts",
    "E2E-16 placement via wizard-v2 / general-route",
    "E2E-17 (ai-eval fabricated lessons) make ai-eval",
    "E2E-18 settings.spec.ts",
    "E2E-20 no-raw-keys.spec.ts",
  ];
  test.info().annotations.push({ type: "catalog", description: catalog.join("\n") });
});
