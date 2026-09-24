import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
}

test("software subject plans software competencies, not python", async ({ page }) => {
  await signIn(page, `s50-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Message").fill("I want to read what a failing test expected.");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("How much time do you have?")).toBeVisible();
  await page.getByLabel("Message").fill("60 minutes");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Software practice")).toBeVisible();
  await expect(page.getByText("Read a failing test", { exact: true })).toBeVisible();
  await expect(page.getByText("Names and values", { exact: true })).toHaveCount(0);
  await expect(page.getByText("python.names")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Accept", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();
});

test("wizard cannot continue without choosing a subject", async ({ page }) => {
  await signIn(page, `s50-empty-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Message").fill("Anything honest.");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Which subject is this?")).toBeVisible();
});
