import { expect, test } from "@playwright/test";

test("update plan previews then accepts the next version after a budget change", async ({
  page,
}) => {
  const email = `s36-${Date.now()}@example.com`;
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
  await page.goto(`/app/goals/${goalId}`);
  await expect(page.getByText("Plan version 1")).toBeVisible();

  const patched = await page.request.patch(`http://127.0.0.1:8000/api/v1/goals/${goalId}`, {
    headers,
    data: {
      time_budget: {
        mode: "one_off",
        one_off_minutes: 15,
        preferred_session_minutes: 15,
      },
    },
  });
  expect(patched.ok()).toBeTruthy();
  await page.getByRole("button", { name: "Update plan" }).click();
  await expect(page.getByRole("heading", { name: "Proposed plan" })).toBeVisible();
  await page.getByRole("button", { name: "Accept" }).click();
  await expect(page.getByText("Plan version 2")).toBeVisible();
  await expect(page.getByText("Calling a function. Not enough minutes this time")).toBeVisible();
});
