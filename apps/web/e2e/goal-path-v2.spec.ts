import { expect, test } from "@playwright/test";

test("goal path v2 shows minutes chips and replan preview then accept", async ({ page }) => {
  const email = `s75-${Date.now()}@example.com`;
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
  await page.request.post(`http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`, {
    headers,
  });

  await page.goto(`/app/goals/${goalId}`);
  await expect(page.getByRole("heading", { name: "Learn Python" })).toBeVisible();
  await expect(page.getByText(/About \d+ of \d+ minutes left/)).toBeVisible();
  await expect(page.getByText("Why this next?")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Lessons" })).toBeVisible();
  await expect(page.getByText(/~\d+–\d+ min/).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Not in this plan" })).toBeVisible();
  await expect(page.getByText("Plan history")).toBeVisible();

  await page.request.patch(`http://127.0.0.1:8000/api/v1/goals/${goalId}`, {
    headers,
    data: {
      time_budget: {
        mode: "one_off",
        one_off_minutes: 15,
        preferred_session_minutes: 15,
      },
    },
  });

  await page.getByRole("button", { name: "Update plan" }).click();
  await expect(page.getByRole("heading", { name: "Proposed plan" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Why this plan/ })).toBeVisible();
  if ((process.env.AI_PROVIDER ?? "") === "fake") {
    await expect(page.getByText("AI", { exact: true })).toBeVisible();
  }
  await expect(page.getByRole("button", { name: "Accept" })).toBeVisible();
  await page.getByRole("button", { name: "Accept" }).click();
  await expect(page.getByText("Plan version 2")).toBeVisible();
  await expect(page.getByText(/Not enough minutes this time/).first()).toBeVisible();
});
