import { execFileSync } from "node:child_process";

import { expect, test } from "@playwright/test";

function makeReviewDue(reviewId: string) {
  execFileSync(
    "psql",
    [
      "-h",
      "127.0.0.1",
      "-U",
      "dolphin",
      "-d",
      "dolphin",
      "-c",
      `UPDATE review_items SET due_at = NOW() - INTERVAL '1 hour' WHERE id = '${reviewId}';`,
    ],
    {
      env: { ...process.env, PGPASSWORD: "dolphin" },
      stdio: "pipe",
    },
  );
}

test("not now delays a due review without claiming retention", async ({ page }) => {
  const email = `s46-${Date.now()}@example.com`;
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
  const questions = (
    (await accepted.json()) as { activities: { id: string; title: string }[] }
  ).activities.filter((item) => item.title.endsWith("objective"));
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
        payload: { plan_activity_id: questions[0].id },
      },
    },
  });
  await page.request.post(`http://127.0.0.1:8000/api/v1/sessions/${sessionId}/attempts`, {
    headers,
    data: { idempotency_key: "once", choice: "b" },
  });

  const queue = await page.request.get("http://127.0.0.1:8000/api/v1/reviews/due", {
    headers,
  });
  const body = (await queue.json()) as {
    due: { id: string }[];
    scheduled: { id: string }[];
  };
  const reviewId = body.scheduled[0]?.id ?? body.due[0]?.id;
  expect(reviewId).toBeTruthy();
  makeReviewDue(reviewId as string);

  await page.goto("/app/review");
  await expect(page.getByRole("heading", { name: "Due now" })).toBeVisible();
  await expect(page.getByText("Not now")).toBeVisible();
  await expect(page.getByRole("button", { name: "3h" })).toBeVisible();
  await expect(
    page.getByText("Skipping is not study and does not count as remembering"),
  ).toBeVisible();
  await page.getByRole("button", { name: "3h" }).click();
  await expect(page.getByRole("heading", { name: "Nothing is due" })).toBeVisible();
  await expect(page.getByText("Not retention")).toBeVisible();
});
