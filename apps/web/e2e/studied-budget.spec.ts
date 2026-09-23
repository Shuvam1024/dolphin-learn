import { expect, test } from "@playwright/test";

test("goal path shows usable and studied minutes without a mastery percent", async ({
  page,
}) => {
  const email = `s44-${Date.now()}@example.com`;
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
      title: "Fractions",
      domain_key: "math",
      raw_request: "Add fractions with the same denominator.",
      time_budget: {
        mode: "weekly",
        weekly_minutes_per_day: 30,
        horizon_days: 14,
        preferred_session_minutes: 30,
      },
    },
  });
  expect(created.status()).toBe(201);
  const goalId = (await created.json()).id as string;
  await page.request.post(`http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`, {
    headers,
  });

  await page.goto(`/app/goals/${goalId}`);
  await expect(page.getByText("Usable minutes: 420. Studied: 0 minutes")).toBeVisible();
  await expect(page.getByText("% mastered")).toHaveCount(0);
  await expect(page.getByText(/deadline/i)).toHaveCount(0);
});
