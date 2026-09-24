import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
}

test("120-minute python quick learn proves evidence without an AI key", async ({ page }) => {
  expect(process.env.OPENAI_API_KEY ?? "").toBe("");
  await signIn(page, `s37-${Date.now()}@example.com`);
  await page.getByLabel("What do you want to learn?").fill("Names and calls.");
  await page.getByRole("radio", { name: "Quick Learn" }).check();
  await page.getByRole("button", { name: "Start" }).click();
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await expect(page.getByRole("listitem").filter({ hasText: "Names and values" })).toBeVisible();
  await expect(page.getByRole("listitem").filter({ hasText: "Calling a function" })).toBeVisible();
  await expect(page.getByText("Not in this plan").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Accept", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();

  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const headers = { Authorization: `Bearer ${token}` };
  const listed = await page.request.get("http://127.0.0.1:8000/api/v1/goals", { headers });
  const goals = (await listed.json()) as Array<{ id: string; title: string }>;
  const goal = goals.find((item) => item.title === "Names and calls");
  const plan = await page.request.get(`http://127.0.0.1:8000/api/v1/goals/${goal?.id}/plan`, {
    headers,
  });
  expect(plan.status()).toBe(200);
  const accepted = (await plan.json()) as {
    usable_minutes: number;
    activities: Array<{ estimated_minutes_low: number }>;
  };
  const allocated = accepted.activities.reduce((sum, item) => sum + item.estimated_minutes_low, 0);
  expect(accepted.usable_minutes).toBe(120);
  expect(allocated).toBeLessThanOrEqual(120);

  await page.getByRole("link", { name: "Back to home" }).click();
  await page.goto(`/app/goals/${goal?.id}/start`);
  await page.getByLabel("30 minutes").check();
  await page.getByRole("button", { name: "Start sitting" }).click();
  await expect(page).toHaveURL(/\/app\/learn\//);
  await expect(page.getByText("binds the name")).toBeVisible();
  await expect(page.getByText("The clock stops when you pause")).toBeVisible();

  await page.getByRole("button", { name: "Next activity" }).click();
  await expect(page.getByRole("button", { name: "Now you try" })).toBeVisible();
  await page.getByRole("button", { name: "Now you try" }).click();
  await expect(page.getByRole("group", { name: "Choose one answer" })).toBeVisible();
  await page.getByRole("radio", { name: /bound to the value 3/ }).check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText("Answer recorded: b")).toBeVisible();
  await expect(page.getByText("Marked independent")).toBeVisible();

  await page.getByRole("button", { name: "Check a different question" }).click();
  await expect(page.getByText("Answer recorded")).toHaveCount(0);
  await expect(page.getByRole("group", { name: "Choose one answer" })).toBeVisible();
  // Item pool may serve objective-3 (rebinds) or objective-4 (print lookup).
  const rebinds = page.getByRole("radio", { name: /rebinds/ });
  const printLookup = page.getByRole("radio", { name: /print\(n\)/ });
  if (await rebinds.count()) {
    await rebinds.check();
    await page.getByRole("button", { name: "Submit answer" }).click();
    await expect(page.getByText("Answer recorded: a")).toBeVisible();
  } else {
    await printLookup.check();
    await page.getByRole("button", { name: "Submit answer" }).click();
    await expect(page.getByText("Answer recorded: b")).toBeVisible();
  }

  await page.goto("/app");
  await expect(page.getByText("Names and values: Shown on your own")).toBeVisible();
  await page.goto("/app/progress");
  await expect(page.getByText("Names and values: Shown on your own")).toBeVisible();
  await expect(page.getByText("% mastered")).toHaveCount(0);
});
