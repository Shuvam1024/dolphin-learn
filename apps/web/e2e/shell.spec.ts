import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("landing, sign-in, and help have no placeholder and axe clean", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dolphin" })).toBeVisible();
  await expect(page.getByText("Learn anything.")).toBeVisible();
  await expect(page.getByText(/placeholder/i)).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Sign in" })).toBeVisible();
  let results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter((item) => item.impact === "serious" || item.impact === "critical"),
  ).toEqual([]);

  await page.goto("/sign-in");
  await expect(page.getByLabel("Email")).toBeVisible();
  results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter((item) => item.impact === "serious" || item.impact === "critical"),
  ).toEqual([]);

  await page.getByLabel("Email").fill(`s74-shell-${Date.now()}@example.com`);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();

  await page.goto("/app/help");
  await expect(page.getByRole("heading", { name: /How Dolphin talks/i })).toBeVisible();
  await expect(page.getByText(/never grades/i)).toBeVisible();
  results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter((item) => item.impact === "serious" || item.impact === "critical"),
  ).toEqual([]);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/app");
  await expect(page.getByRole("navigation", { name: "Primary" }).last()).toBeVisible();
  await expect(page.getByRole("link", { name: "More" }).last()).toBeVisible();
});
