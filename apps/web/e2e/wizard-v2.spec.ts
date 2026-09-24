import { expect, test } from "@playwright/test";

async function signIn(page: import("@playwright/test").Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
}

test("wizard v2 keyboard python path with 30x14 hours", async ({ page }) => {
  await signIn(page, `s84-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Message").fill("I want to learn Python names. 30 minutes a day for 14 days.");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText(/30 minutes a day for 14 days/)).toBeVisible();
  await expect(page.getByText("Not in this plan")).toBeVisible();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();
});

test("wizard v2 general route to accept", async ({ page }) => {
  await signIn(page, `s84-gen-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Message").fill("Spanish greetings for travel.");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("What should you be able to do")).toBeVisible();
  await page.getByLabel("Message").fill("I can say hello and goodbye");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("How much time do you have?")).toBeVisible();
  await page.getByLabel("Message").fill("60 minutes");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText(/60 minutes in one sitting/)).toBeVisible();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();
});

test("wizard v2 reload keeps draft", async ({ page }) => {
  await signIn(page, `s84-draft-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Message").fill("Keep this draft text about Python.");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Keep this draft text about Python.")).toBeVisible();
});
