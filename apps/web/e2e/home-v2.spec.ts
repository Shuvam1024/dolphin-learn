import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

test("home v2: one primary, lesson names, no Log out", async ({ page }) => {
  await signIn(page, `s72-home-${Date.now()}@example.com`);
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
        preferred_session_minutes: 25,
      },
    },
  });
  const goalId = (await created.json()).id as string;
  await page.request.post(`http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`, {
    headers,
  });

  await page.goto("/app");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const primaries = page.getByRole("link", { name: /Continue Learn Python|Create a goal/i });
  await expect(primaries.first()).toBeVisible();
  await expect(page.getByText(/next:/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Log out" })).toHaveCount(0);
  await expect(page.getByText(/streak|mastery %/i)).toHaveCount(0);

  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter(
    (item) => item.impact === "serious" || item.impact === "critical",
  );
  expect(serious).toEqual([]);
});
