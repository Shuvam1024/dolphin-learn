import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

test("sitting chooser sets about 15 minutes; resume skips chooser", async ({ page }) => {
  await signIn(page, `s66-size-${Date.now()}@example.com`);
  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const headers = { Authorization: `Bearer ${token}` };
  const created = await page.request.post("http://127.0.0.1:8000/api/v1/goals", {
    headers,
    data: {
      title: "Learn Python",
      domain_key: "python",
      raw_request: "Names.",
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

  await page.goto(`/app/goals/${goalId}/start`);
  await expect(page.getByText("How long do you have right now?")).toBeVisible();
  await page.getByLabel("15 minutes").check();
  await page.getByRole("button", { name: "Start sitting" }).click();
  await expect(page.getByText(/About 15 minutes/i)).toBeVisible();
  await expect(page.getByText(/minutes left in this sitting/i)).toBeVisible();

  const sessionUrl = page.url();
  await page.getByRole("button", { name: "Pause" }).click();
  await page.goto(`/app/goals/${goalId}`);
  await page.getByRole("link", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/app\/learn\//);
  await expect(page.getByText("How long do you have right now?")).toHaveCount(0);
  expect(page.url()).toContain("/app/learn/");
  void sessionUrl;
});
