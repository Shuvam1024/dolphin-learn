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
  await page.getByRole("link", { name: "Create a goal" }).click();
  await expect(page.getByRole("heading", { name: "Create a goal" })).toBeVisible();
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await expect(page.getByText("Step 1 of 5")).toBeVisible();

  await page.getByLabel("What do you want to learn?").fill("I want to learn Python names.");
  await page.getByLabel("Goal title").fill("Names and values");
  await page.getByLabel("Subject").selectOption("python");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Step 2 of 5")).toBeVisible();

  await page.getByRole("button", { name: "30 × 14" }).click();
  await expect(page.getByText(/30 minutes × 14 sittings = 7 hours of study/)).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Step 3 of 5")).toBeVisible();

  await page.getByText("Focus one topic").click();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Step 4 of 5")).toBeVisible();

  await page.getByRole("button", { name: "Skip placement" }).click();
  await expect(page.getByText("Step 5 of 5")).toBeVisible();
  await expect(page.getByText(/Plan uses \d+ of your minutes/)).toBeVisible();
  await expect(page.getByText("Not in this plan")).toBeVisible();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();
});

test("wizard v2 general route to accept", async ({ page }) => {
  await signIn(page, `s84-gen-${Date.now()}@example.com`);
  await page.getByRole("link", { name: "Create a goal" }).click();
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("What do you want to learn?").fill("Spanish greetings for travel.");
  await page.getByLabel("Goal title").fill("Spanish greetings");
  await page.getByRole("button", { name: "Something else" }).click();
  await page.getByLabel("Outcome 1").fill("I can say hello and goodbye");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "60 min" }).click();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "See plan" }).click();
  await expect(page.getByText("Step 5 of 5")).toBeVisible();
  await expect(page.getByText(/Plan uses \d+ of your minutes/)).toBeVisible();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();
});

test("wizard v2 reload keeps draft", async ({ page }) => {
  await signIn(page, `s84-draft-${Date.now()}@example.com`);
  await page.getByRole("link", { name: "Create a goal" }).click();
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("What do you want to learn?").fill("Keep this draft text.");
  await page.getByLabel("Goal title").fill("Draft goal");
  await page.getByLabel("Subject").selectOption("python");
  await page.reload();
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await expect(page.getByLabel("Goal title")).toHaveValue("Draft goal");
  await expect(page.getByLabel("What do you want to learn?")).toHaveValue("Keep this draft text.");
});
