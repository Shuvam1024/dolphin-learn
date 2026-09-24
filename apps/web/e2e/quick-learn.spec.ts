import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

test("120-minute python quick learn proves evidence without an AI key", async ({ page }) => {
  expect(process.env.OPENAI_API_KEY ?? "").toBe("");
  await signIn(page, `s37-${Date.now()}@example.com`);
  await page.getByRole("link", { name: "Quick Learn" }).click();
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();

  await page.getByLabel("Goal title").fill("Quick Learn Python");
  await page.getByLabel("What do you want to learn?").fill("Names and calls.");
  await page.getByLabel("Subject").selectOption("python");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByLabel("Total minutes").fill("120");
  await page.getByLabel("Preferred session length (minutes)").fill("30");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "Save goal" }).click();
  await expect(page.getByText("Names and values")).toBeVisible();
  await expect(page.getByText("Calling a function")).toBeVisible();
  await expect(page.getByText("Nothing is deferred.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Accept plan" })).toBeEnabled();
  await page.getByRole("button", { name: "Accept plan" }).click();
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();

  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const headers = { Authorization: `Bearer ${token}` };
  const listed = await page.request.get("http://127.0.0.1:8000/api/v1/goals", { headers });
  const goals = (await listed.json()) as Array<{ id: string; title: string }>;
  const goal = goals.find((item) => item.title === "Quick Learn Python");
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
  await page.getByRole("button", { name: "Start a session for Quick Learn Python" }).click();
  await expect(page).toHaveURL(/\/app\/learn\//);
  await expect(page.getByText("binds the name")).toBeVisible();
  await expect(page.getByText("No countdown")).toBeVisible();

  await page.getByRole("button", { name: "Next activity" }).click();
  await expect(page.getByRole("button", { name: "Now you try" })).toBeVisible();
  await page.getByRole("button", { name: "Now you try" }).click();
  await expect(page.getByRole("group", { name: "Choose one answer" })).toBeVisible();
  await page.getByRole("radio", { name: /bound to the value 3/ }).check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText("Answer recorded: b")).toBeVisible();
  await expect(page.getByText("Marked independent")).toBeVisible();

  await page.getByRole("button", { name: "Check a different question" }).click();
  await expect(page.getByText(/What does/)).toBeVisible();
  await expect(page.getByText("Answer recorded")).toHaveCount(0);
  await page.getByRole("radio", { name: /rebinds/ }).check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText("Answer recorded: a")).toBeVisible();

  await page.goto("/app");
  await expect(page.getByText("Names and values: Shown on your own")).toBeVisible();
  await page.goto("/app/progress");
  await expect(page.getByText("Names and values: Shown on your own")).toBeVisible();
  await expect(page.getByText("% mastered")).toHaveCount(0);
});
