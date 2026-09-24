import { expect, test } from "@playwright/test";

test("review v2 shows fit line and snooze presets without forbidden words", async ({ page }) => {
  const email = `s78-${Date.now()}@example.com`;
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
      time_budget: {
        mode: "one_off",
        one_off_minutes: 120,
        preferred_session_minutes: 25,
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
        client_event_id: "to-q",
        event_type: "progress",
        payload: { plan_activity_id: question?.id },
      },
    },
  });
  await page.request.post(`http://127.0.0.1:8000/api/v1/sessions/${sessionId}/attempts`, {
    headers,
    data: { idempotency_key: "once", choice: "b" },
  });

  const due = await page.request.get("http://127.0.0.1:8000/api/v1/reviews/due", { headers });
  expect(due.ok()).toBeTruthy();
  const body = (await due.json()) as {
    due: Array<{ id: string; estimated_minutes: number }>;
    scheduled: Array<{ id: string; estimated_minutes: number }>;
    fits: { count: number; minutes: number };
    preferred_session_minutes: number;
  };
  expect(body.fits).toBeTruthy();
  expect(body.preferred_session_minutes).toBeGreaterThan(0);
  expect(
    [...body.due, ...body.scheduled].every((item) => item.estimated_minutes >= 1),
  ).toBeTruthy();

  await page.goto("/app/review");
  await expect(page.getByText(/overdue|missed|streak/i)).toHaveCount(0);
  if (body.due.length > 0) {
    await expect(page.getByText(/\d+ due · start with \d+/)).toBeVisible();
    await expect(page.getByRole("button", { name: "3h" })).toBeVisible();
    await expect(page.getByRole("button", { name: "24h" })).toBeVisible();
    await expect(page.getByRole("button", { name: "72h" })).toBeVisible();
  } else {
    await expect(page.getByRole("heading", { name: "Nothing is due" })).toBeVisible();
    if (body.scheduled.length > 0) {
      await expect(page.getByText(/About \d+ min/)).toBeVisible();
    }
  }
});
