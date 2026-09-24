import { expect, test } from "@playwright/test";

test("review page shows the scheduled reason and no streak", async ({ page }) => {
  const email = `s32-${Date.now()}@example.com`;
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();

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
  const accepted = await page.request.post(
    `http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`,
    { headers },
  );
  const question = (
    (await accepted.json()).activities as Array<{ id: string; title: string }>
  ).find((item) => item.title.endsWith("objective"));
  const started = await page.request.post("http://127.0.0.1:8000/api/v1/sessions", {
    headers,
    data: { goal_id: goalId },
  });
  const sessionId = (await started.json()).id as string;
  await page.request.patch(`http://127.0.0.1:8000/api/v1/sessions/${sessionId}`, {
    headers,
    data: {
      event: {
        client_event_id: "to-question",
        event_type: "progress",
        payload: { plan_activity_id: question?.id },
      },
    },
  });
  const attempt = await page.request.post(
    `http://127.0.0.1:8000/api/v1/sessions/${sessionId}/attempts`,
    { headers, data: { idempotency_key: "once", choice: "b" } },
  );
  expect(attempt.ok()).toBeTruthy();

  await page.goto("/app/review");
  await expect(page.getByRole("heading", { name: "Nothing is due" })).toBeVisible();
  await expect(page.getByText("Not retention")).toBeVisible();
  await expect(page.getByText("day streak")).toHaveCount(0);
});
