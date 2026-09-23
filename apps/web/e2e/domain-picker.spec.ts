import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

test("software subject plans software competencies, not python", async ({ page }) => {
  await signIn(page, `s50-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();

  await page.getByLabel("Goal title").fill("Read failing tests");
  await page
    .getByLabel("What do you want to learn?")
    .fill("I want to read what a failing test expected.");
  await page.getByLabel("Subject").selectOption("software");
  await expect(
    page.getByText("These are subjects we can check today. More come later on the same platform."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByLabel("Total minutes").fill("60");
  await page.getByLabel("Preferred session length (minutes)").fill("25");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "Save goal" }).click();

  await expect(page.getByRole("heading", { name: "Goal saved" })).toBeVisible();
  await expect(page.getByText("Subject: software")).toBeVisible();
  await expect(page.getByText("Read a failing test", { exact: true })).toBeVisible();
  await expect(page.getByText("Names and values", { exact: true })).toHaveCount(0);
  await expect(page.getByText("python.names")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Accept plan" })).toBeEnabled();
  await page.getByRole("button", { name: "Accept plan" }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();
});

test("wizard cannot continue without choosing a subject", async ({ page }) => {
  await signIn(page, `s50-empty-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Goal title").fill("Something");
  await page.getByLabel("What do you want to learn?").fill("Anything honest.");
  await expect(page.getByLabel("Subject")).toHaveValue("");
  await expect(page.getByRole("button", { name: "Next", exact: true })).toBeDisabled();
});
