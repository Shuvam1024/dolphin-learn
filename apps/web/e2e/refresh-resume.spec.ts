import { expect, test } from "@playwright/test";

test("refresh resumes the lesson and a repeated submit stays one attempt", async ({ page }) => {
  const email = `s39-${Date.now()}@example.com`;
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

  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByText("binds the name")).toBeVisible();
  await page.reload();
  await expect(page).toHaveURL(new RegExp(`/app/learn/${sessionId}$`));
  await expect(page.getByText("binds the name")).toBeVisible();
  await expect(page.getByText("In progress.")).toBeVisible();

  await page.getByRole("button", { name: "Next activity" }).click();
  await expect(page.getByRole("button", { name: "Now you try" })).toBeVisible();
  await page.getByRole("button", { name: "Now you try" }).click();
  await expect(page.getByRole("group", { name: "Choose one answer" })).toBeVisible();
  const first = await page.request.post(
    `http://127.0.0.1:8000/api/v1/sessions/${sessionId}/attempts`,
    { headers, data: { idempotency_key: "once", choice: "b" } },
  );
  const second = await page.request.post(
    `http://127.0.0.1:8000/api/v1/sessions/${sessionId}/attempts`,
    { headers, data: { idempotency_key: "once", choice: "a" } },
  );
  expect(first.ok()).toBeTruthy();
  const original = (await first.json()) as { id: string; created: boolean; choice: string };
  const replay = (await second.json()) as { id: string; created: boolean; choice: string };
  expect(replay.id).toBe(original.id);
  expect(replay.created).toBe(false);
  expect(replay.choice).toBe("b");

  await page.reload();
  await expect(page.getByText("Answer recorded: b")).toBeVisible();
  await expect(page.getByRole("button", { name: "Submit answer" })).toHaveCount(0);
});
