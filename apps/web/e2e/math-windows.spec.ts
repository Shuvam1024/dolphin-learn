import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

test("two-week math plan counts 30-minute days, not 14 times 24 hours", async ({ page }) => {
  expect(process.env.OPENAI_API_KEY ?? "").toBe("");
  await signIn(page, `s38-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();

  await page.getByLabel("Goal title").fill("Fractions");
  await page.getByLabel("What do you want to learn?").fill("Add fractions with the same denominator.");
  await page.getByLabel("Subject").selectOption("math");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByLabel("Minutes each day for a set number of days").check();
  await page.getByLabel("Minutes per day").fill("30");
  await page.getByRole("textbox", { name: "Number of days", exact: true }).fill("14");
  await page.getByLabel("Preferred session length (minutes)").fill("30");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "Save goal" }).click();
  await expect(page.getByText("30 minutes a day for 14 days")).toBeVisible();
  await expect(page.getByText("A fraction as parts of a whole")).toBeVisible();
  await expect(page.getByRole("button", { name: "Accept plan" })).toBeEnabled();
  await page.getByRole("button", { name: "Accept plan" }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();

  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const headers = { Authorization: `Bearer ${token}` };
  const listed = await page.request.get("http://127.0.0.1:8000/api/v1/goals", { headers });
  const goals = (await listed.json()) as Array<{ id: string; title: string }>;
  const goal = goals.find((item) => item.title === "Fractions");
  const plan = await page.request.get(`http://127.0.0.1:8000/api/v1/goals/${goal?.id}/plan`, {
    headers,
  });
  expect(plan.ok()).toBeTruthy();
  const accepted = (await plan.json()) as {
    usable_minutes: number;
    rationale: string;
    activities: Array<{ title: string; estimated_minutes_low: number }>;
  };
  expect(accepted.usable_minutes).toBe(30 * 14);
  expect(accepted.usable_minutes).not.toBe(14 * 24 * 60);
  expect(accepted.rationale).toContain("Usable minutes: 420.");
  expect(accepted.rationale).not.toContain("20160");
  const checkpoint = accepted.activities.find((item) => item.title.endsWith("objective"));
  expect(checkpoint).toBeTruthy();

  await page.getByRole("link", { name: "Back to home" }).click();
  await page.getByRole("button", { name: "Start a session for Fractions" }).click();
  await expect(page.getByText("three equal parts out of four")).toBeVisible();
  await page.getByRole("button", { name: "Next activity" }).click();
  await expect(page.getByRole("button", { name: "Now you try" })).toBeVisible();
  await page.getByRole("button", { name: "Now you try" }).click();
  await expect(page.getByText("In 3/4, what does the 4 name?")).toBeVisible();
  await expect(page.getByRole("radio", { name: /equal parts make the whole/ })).toBeVisible();
});
