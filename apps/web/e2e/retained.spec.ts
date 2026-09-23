import { expect, test } from "@playwright/test";

test("progress explains retained and does not show a mastery percent", async ({ page }) => {
  const email = `s42-${Date.now()}@example.com`;
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();

  await page.goto("/app/progress");
  await expect(page.getByText("Retained means a later review")).toBeVisible();
  await expect(page.getByText("% mastered")).toHaveCount(0);
  await expect(page.getByText("permanent promise")).toBeVisible();
});
