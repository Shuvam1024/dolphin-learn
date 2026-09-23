import { expect, test } from "@playwright/test";

test("reading studio shows the explanation and pause survives refresh", async ({ page }) => {
  const email = `s27-${Date.now()}@example.com`;
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
      raw_request: "Names and calls.",
      time_budget: {
        mode: "one_off",
        one_off_minutes: 120,
        preferred_session_minutes: 30,
      },
    },
  });
  expect(created.status()).toBe(201);
  const goalId = (await created.json()).id as string;
  const accepted = await page.request.post(
    `http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`,
    { headers },
  );
  expect(accepted.status()).toBe(201);
  const started = await page.request.post("http://127.0.0.1:8000/api/v1/sessions", {
    headers,
    data: { goal_id: goalId },
  });
  expect(started.status()).toBe(201);
  const sessionId = (await started.json()).id as string;

  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByRole("heading", { name: "Names point at values" })).toBeVisible();
  await expect(page.getByText("binds the name")).toBeVisible();
  await expect(page.getByText("Mode: Guided")).toBeVisible();
  await expect(page.getByText("No countdown")).toBeVisible();
  await expect(page.getByText("time remaining")).toHaveCount(0);

  await page.getByRole("button", { name: "Pause" }).click();
  await expect(page.getByText("Paused.")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Paused.")).toBeVisible();
  await expect(page.getByText("binds the name")).toBeVisible();
  await expect(page.getByRole("button", { name: "Resume" })).toBeVisible();
});
