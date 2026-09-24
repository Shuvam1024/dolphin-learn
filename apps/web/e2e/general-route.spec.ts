import { expect, test } from "@playwright/test";

async function signIn(page: import("@playwright/test").Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
}

test("general route outline appears and plan accepts", async ({ page }) => {
  await signIn(page, `s85-e2e-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Message").fill("Spanish greetings");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("What should you be able to do")).toBeVisible();
  await page.getByLabel("Message").fill("I can say hello");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("How much time do you have?")).toBeVisible();
  await page.getByLabel("Message").fill("60 minutes");
  await page.getByRole("button", { name: "Send" }).click();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();
});
