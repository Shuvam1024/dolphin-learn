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
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Learn", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start" })).toBeVisible();
});
