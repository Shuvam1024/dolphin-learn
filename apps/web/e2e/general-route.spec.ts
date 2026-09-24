import { expect, test } from "@playwright/test";

async function signIn(page: import("@playwright/test").Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/app$/);
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

test("general route outline appears and plan accepts", async ({ page }) => {
  await signIn(page, `s85-e2e-${Date.now()}@example.com`);
  await page.getByRole("link", { name: "Create a goal" }).click();
  await page.getByLabel("What do you want to learn?").fill("Spanish greetings");
  await page.getByLabel("Goal title").fill("Spanish greetings");
  await page.getByRole("button", { name: "Something else" }).click();
  await page.getByLabel("Outcome 1").fill("I can say hello");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "60 min" }).click();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "See plan" }).click();
  await expect(page.getByText("Step 5 of 5")).toBeVisible();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();
});
