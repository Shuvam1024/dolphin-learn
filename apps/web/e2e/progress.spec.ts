import { expect, test } from "@playwright/test";

test("progress explains unassessed gaps and shows a real facet", async ({ page }) => {
  const email = `s34-${Date.now()}@example.com`;
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();

  await page.goto("/app/progress");
  await expect(page.getByRole("heading", { name: "No evidence yet" })).toBeVisible();
  await expect(page.getByText("stay unassessed")).toBeVisible();
  await expect(page.getByText("% mastered")).toHaveCount(0);

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
  await page.request.post(`http://127.0.0.1:8000/api/v1/sessions/${sessionId}/attempts`, {
    headers,
    data: { idempotency_key: "once", choice: "b" },
  });

  await page.goto("/app/progress");
  await expect(page.getByText("python.names: independently_demonstrated")).toBeVisible();
  await expect(page.getByText("python.calls: unassessed")).toBeVisible();
  await expect(page.getByText("% mastered")).toHaveCount(0);
});
