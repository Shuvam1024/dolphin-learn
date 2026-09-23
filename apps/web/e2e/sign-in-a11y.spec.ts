import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("sign-in and adult gate have zero serious or critical axe findings", async ({ page }) => {
  await page.goto("/sign-in");
  await expect(page.getByRole("heading", { name: "Dolphin" })).toBeVisible();
  const signIn = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
    .analyze();
  const signInBad = signIn.violations.filter(
    (item) => item.impact === "serious" || item.impact === "critical",
  );
  expect(signInBad, JSON.stringify(signInBad, null, 2)).toEqual([]);

  await page.getByLabel("Email").fill(`s52-gate-${Date.now()}@example.com`);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Before you start" })).toBeVisible();
  const gate = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
    .analyze();
  const gateBad = gate.violations.filter(
    (item) => item.impact === "serious" || item.impact === "critical",
  );
  expect(gateBad, JSON.stringify(gateBad, null, 2)).toEqual([]);
});
