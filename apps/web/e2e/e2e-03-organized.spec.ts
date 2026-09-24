/**
 * E2E-03 — Organized and adaptive (Phase 4).
 * Home next action → Learn shelf → path with minutes → Progress by goal → Review fit copy.
 */
import { expect, test } from "@playwright/test";

test("E2E-03 organized home learn path progress and review", async ({ page }) => {
  const email = `e2e03-${Date.now()}@example.com`;
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();

  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const headers = { Authorization: `Bearer ${token}` };
  const created = await page.request.post("http://127.0.0.1:8000/api/v1/goals", {
    headers,
    data: {
      title: "Learn Python",
      domain_key: "python",
      raw_request: "Names and calls.",
      priority: "understand",
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

  await page.goto("/app");
  await expect(page.getByRole("link", { name: "Learn Python" }).first()).toBeVisible();
  await expect(page.getByText(/streak|mastery %/i)).toHaveCount(0);

  await page.goto("/app/learn");
  await expect(page.getByRole("heading", { name: "Your goals" })).toBeVisible();
  await expect(page.getByText("Learn Python").first()).toBeVisible();
  await expect(page.getByText("Active")).toBeVisible();

  await page.goto(`/app/goals/${goalId}`);
  await expect(page.getByRole("heading", { name: "Learn Python" })).toBeVisible();
  await expect(page.getByText(/About \d+ of \d+ minutes left/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Lessons" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Not in this plan" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Update plan" })).toBeVisible();
  await expect(page.getByText(/python\./)).toHaveCount(0);

  await page.goto("/app/progress");
  await expect(page.getByRole("heading", { name: "Evidence by goal" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Upcoming reviews" })).toBeVisible();
  await expect(page.getByText("% mastered")).toHaveCount(0);

  await page.goto("/app/review");
  await expect(page.getByText(/overdue|missed|streak/i)).toHaveCount(0);
  await expect(page.getByRole("heading", { name: /Due now|Nothing is due/ })).toBeVisible();

  await page.goto("/app/help");
  await expect(page.getByRole("heading", { name: "How Dolphin talks about learning" })).toBeVisible();
});
