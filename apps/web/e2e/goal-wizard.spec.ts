import { expect, test } from "@playwright/test";

async function signIn(page: import("@playwright/test").Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/app$/);
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

test("keyboard-only wizard saves a goal and keeps fields on back", async ({ page }) => {
  await signIn(page, `s22-${Date.now()}@example.com`);
  await page.getByRole("link", { name: "Create a goal" }).click();
  await expect(page.getByRole("heading", { name: "Create a goal" })).toBeVisible();
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();

  await page.getByLabel("What do you want to learn?").fill("I want to bind names to values in Python.");
  await page.getByLabel("Goal title").fill("Names and values");
  await page.getByLabel("Subject").selectOption("python");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Step 2 of 5")).toBeVisible();

  await page.getByRole("button", { name: "Back" }).click();
  await expect(page.getByLabel("Goal title")).toHaveValue("Names and values");
  await expect(page.getByLabel("What do you want to learn?")).toHaveValue(
    "I want to bind names to values in Python.",
  );
  await expect(page.getByLabel("Subject")).toHaveValue("python");

  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByLabel("Total minutes").fill("120");
  await page.getByLabel("Preferred sitting length").fill("30");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Step 3 of 5")).toBeVisible();

  await page.getByText("Focus one topic").click();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "Skip placement" }).click();
  await expect(page.getByText("Step 5 of 5")).toBeVisible();
  await expect(page.getByText(/Plan uses \d+ of your minutes/)).toBeVisible();
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
  expect(saved?.priority).toBe("apply");
  expect(saved?.time_budget?.mode).toBe("one_off");
  expect(saved?.time_budget?.one_off_minutes).toBe(120);
});
