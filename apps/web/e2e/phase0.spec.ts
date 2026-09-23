import { expect, test } from "@playwright/test";

test("health, blocked shell, then signed-in home", async ({ page, request }) => {
  const health = await request.get("http://127.0.0.1:8000/health");
  expect(health.status()).toBe(200);
  expect(await health.json()).toEqual({ status: "ok" });

  await page.goto("/app");
  await expect(page).toHaveURL(/\/sign-in$/);
  await expect(page.getByRole("heading", { name: "Dolphin" })).toBeVisible();

  const email = `s19-${Date.now()}@example.com`;
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByRole("heading", { name: "Before you start" })).toBeVisible();

  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Learn", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Create a goal" })).toBeVisible();
});
