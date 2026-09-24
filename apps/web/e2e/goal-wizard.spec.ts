import { expect, test } from "@playwright/test";

async function signIn(page: import("@playwright/test").Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
}

test("keyboard-only wizard saves a goal and keeps fields on back", async ({ page }) => {
  await signIn(page, `s22-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Message").fill("Names and values. I want to bind names to values in Python. 120 minutes.");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Not in this plan")).toBeVisible();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();

  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const listed = await page.request.get("http://127.0.0.1:8000/api/v1/goals", {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(listed.status()).toBe(200);
  const goals = (await listed.json()) as Array<{
    id: string;
    title: string;
    priority?: string;
    time_budget: { mode: string; one_off_minutes: number | null } | null;
  }>;
  const saved = goals.find((goal) => goal.title === "Names and values");
  expect(saved?.priority).toBe("understand");
  expect(saved?.time_budget?.mode).toBe("one_off");
  expect(saved?.time_budget?.one_off_minutes).toBe(120);
});
