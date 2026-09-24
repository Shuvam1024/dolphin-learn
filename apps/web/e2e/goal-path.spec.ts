import { expect, test } from "@playwright/test";

test("goal path shows deferred work and continue opens the session", async ({ page }) => {
  const email = `s35-${Date.now()}@example.com`;
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
        one_off_minutes: 15,
        preferred_session_minutes: 15,
      },
    },
  });
  const goalId = (await created.json()).id as string;
  await page.request.post(`http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`, {
    headers,
  });

  await page.goto(`/app/goals/${goalId}`);
  await expect(page.getByRole("heading", { name: "Learn Python" })).toBeVisible();
  await expect(page.getByText("Why this next?")).toBeVisible();
  await expect(page.getByText("Calling a function. Not enough minutes this time")).toBeVisible();
  await expect(page.getByText(/About \d+ of \d+ minutes left/)).toBeVisible();
  await page.getByRole("link", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/app\/learn\//);
  await expect(page.getByRole("heading", { name: "Names point at values" })).toBeVisible();
});
