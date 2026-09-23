import { expect, test } from "@playwright/test";

async function signIn(page: import("@playwright/test").Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/app$/);
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

test("keyboard-only wizard saves a goal and keeps fields on back", async ({ page }) => {
  await signIn(page, `s22-${Date.now()}@example.com`);
  await page.getByRole("link", { name: "Create a goal" }).click();
  await expect(page.getByRole("heading", { name: "Create a goal" })).toBeVisible();
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();

  const title = page.getByLabel("Goal title");
  await title.focus();
  await page.keyboard.type("Names and values");
  await page.keyboard.press("Tab");
  await page.keyboard.type("I want to bind names to values in Python.");
  await page.getByRole("button", { name: "Next", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByText("Step 2 of 3")).toBeVisible();

  await page.getByRole("button", { name: "Back" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Goal title")).toHaveValue("Names and values");
  await expect(page.getByLabel("What do you want to learn?")).toHaveValue(
    "I want to bind names to values in Python.",
  );

  await page.getByRole("button", { name: "Next", exact: true }).focus();
  await page.keyboard.press("Enter");
  await page.getByLabel("Total minutes").focus();
  await page.keyboard.press("Control+A");
  await page.keyboard.type("120");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Control+A");
  await page.keyboard.type("30");
  await page.getByRole("button", { name: "Next", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByText("Step 3 of 3")).toBeVisible();

  await page.getByRole("button", { name: "Save goal" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Goal saved" })).toBeVisible();
  await expect(page.getByText("Names and values")).toBeVisible();
  await expect(page.getByText("120 minutes in one sitting")).toBeVisible();
  await expect(page.getByText("Priority: Focus one topic")).toBeVisible();

  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const listed = await page.request.get("http://127.0.0.1:8000/api/v1/goals", {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(listed.status()).toBe(200);
  const goals = (await listed.json()) as Array<{
    id: string;
    title: string;
    normalized_objective: string | null;
    time_budget: { mode: string; one_off_minutes: number | null } | null;
  }>;
  const saved = goals.find((goal) => goal.title === "Names and values");
  expect(saved?.normalized_objective).toBe("Priority: Focus one topic");
  expect(saved?.time_budget?.mode).toBe("one_off");
  expect(saved?.time_budget?.one_off_minutes).toBe(120);

  await expect(page.getByRole("button", { name: "Accept plan" })).toBeEnabled();
  await expect(page.getByText("python.names")).toBeVisible();
  await expect(page.getByText("Nothing is deferred.")).toBeVisible();
  await page.getByRole("button", { name: "Accept plan" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Plan accepted" })).toBeVisible();

  const plan = await page.request.get(`http://127.0.0.1:8000/api/v1/goals/${saved?.id}/plan`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(plan.status()).toBe(200);
  const accepted = (await plan.json()) as { version_number: number; rationale: string };
  expect(accepted.version_number).toBe(1);
  expect(accepted.rationale).toContain("Deferred: none.");
});

test("wizard fits a narrow phone width", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page, `s22-mobile-${Date.now()}@example.com`);
  await page.goto("/app/goals/new");
  await expect(page.getByRole("heading", { name: "Create a goal" })).toBeVisible();
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Goal title").fill("Fractions");
  await page.getByLabel("What do you want to learn?").fill("Add fractions with the same denominator.");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByLabel("Minutes each day for a set number of days").check();
  await expect(page.getByLabel("Minutes per day")).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth <= window.innerWidth + 1,
  );
  expect(overflow).toBe(true);
});
