import { expect, test, type Page } from "@playwright/test";
import { execSync } from "node:child_process";
import path from "node:path";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
}

test("sitting chooser sets about 15 minutes; resume skips chooser", async ({ page }) => {
  await signIn(page, `s66-size-${Date.now()}@example.com`);
  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const headers = { Authorization: `Bearer ${token}` };
  const created = await page.request.post("http://127.0.0.1:8000/api/v1/goals", {
    headers,
    data: {
      title: "Learn Python",
      domain_key: "python",
      raw_request: "Names.",
      time_budget: {
        mode: "one_off",
        one_off_minutes: 120,
        preferred_session_minutes: 30,
      },
    },
  });
  const goalId = (await created.json()).id as string;
  await page.request.post(`http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`, {
    headers,
  });

  await page.goto(`/app/goals/${goalId}/start`);
  await expect(page.getByText("How long do you have right now?")).toBeVisible();
  await page.getByLabel("15 minutes").check();
  await page.getByRole("button", { name: "Start sitting" }).click();
  await expect(page.getByText(/About 15 minutes/i)).toBeVisible();
  await expect(page.getByText(/minutes left in this sitting/i)).toBeVisible();

  const sessionUrl = page.url();
  await page.getByRole("button", { name: "Pause" }).click();
  await page.goto(`/app/goals/${goalId}`);
  await page.getByRole("link", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/app\/learn\//);
  await expect(page.getByText("How long do you have right now?")).toHaveCount(0);
  expect(page.url()).toContain("/app/learn/");
  void sessionUrl;
});

test("fast clock reaches a good stopping point without countdown copy", async ({ page }) => {
  await signIn(page, `s67-stop-${Date.now()}@example.com`);
  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const headers = { Authorization: `Bearer ${token}` };
  const created = await page.request.post("http://127.0.0.1:8000/api/v1/goals", {
    headers,
    data: {
      title: "Learn Python",
      domain_key: "python",
      raw_request: "Names.",
      time_budget: {
        mode: "one_off",
        one_off_minutes: 120,
        preferred_session_minutes: 25,
      },
    },
  });
  const goalId = (await created.json()).id as string;
  await page.request.post(`http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`, {
    headers,
  });
  const started = await page.request.post("http://127.0.0.1:8000/api/v1/sessions", {
    headers,
    data: { goal_id: goalId, target_minutes: 5 },
  });
  const sessionId = (await started.json()).id as string;
  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByText(/About 5 minutes/i)).toBeVisible();
  await expect(page.getByText(/minutes left in this sitting/i)).toBeVisible();

  // DOLPHIN_E2E_FAST_CLOCK=1 → one wall second ≈ one active minute
  await page.waitForTimeout(6500);
  await page.reload();
  await expect(page.getByText("Good place to stop")).toBeVisible();
  await expect(page.getByRole("button", { name: "Finish session" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Keep going" })).toBeVisible();
  await expect(page.getByText(/countdown/i)).toHaveCount(0);
  await expect(page.getByText(/time's up/i)).toHaveCount(0);
});

test("apps/web has no countdown or timer guilt copy", async () => {
  const webRoot = path.resolve(__dirname, "..");
  const out = execSync(
    `rg -n -i "countdown|time's up|\\\\btimer\\\\b" --glob '!node_modules/**' --glob '!.next/**' --glob '!e2e/**' . || true`,
    { cwd: webRoot, encoding: "utf8" },
  );
  expect(out.trim()).toBe("");
});
