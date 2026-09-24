import { expect, test } from "@playwright/test";

test("home shows the live session and feasibility, not a streak", async ({ page }) => {
  const email = `s33-${Date.now()}@example.com`;
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Create a goal" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Quick Learn" })).toBeVisible();

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
  const started = await page.request.post("http://127.0.0.1:8000/api/v1/sessions", {
    headers,
    data: { goal_id: goalId },
  });
  const sessionId = (await started.json()).id as string;

  await page.goto("/app");
  await expect(page.getByRole("heading", { name: "Resume your session" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Resume your session" })).toHaveAttribute(
    "href",
    `/app/learn/${sessionId}`,
  );
  await expect(page.getByText(/120 minutes left|of 120 minutes/i)).toBeVisible();
  await expect(page.getByText("% mastered")).toHaveCount(0);
  await expect(page.getByText("day streak")).toHaveCount(0);
});
