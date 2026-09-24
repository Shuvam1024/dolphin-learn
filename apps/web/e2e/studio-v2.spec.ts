import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

async function startPythonSession(page: Page) {
  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const headers = { Authorization: `Bearer ${token}` };
  const created = await page.request.post("http://127.0.0.1:8000/api/v1/goals", {
    headers,
    data: {
      title: "Learn Python",
      domain_key: "python",
      raw_request: "Names and calls.",
      time_budget: {
        mode: "one_off",
        one_off_minutes: 120,
        preferred_session_minutes: 30,
      },
    },
  });
  const goalId = (await created.json()).id as string;
  await page.request.post(`http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`, {
    headers,
  });
  const started = await page.request.post("http://127.0.0.1:8000/api/v1/sessions", {
    headers,
    data: { goal_id: goalId },
  });
  const sessionId = (await started.json()).id as string;
  return { sessionId, headers, goalId };
}

test("studio v2 renders markdown code, one primary, pause, and hides tutor when AI is off", async ({
  page,
}) => {
  expect(process.env.OPENAI_API_KEY ?? "").toBe("");
  await signIn(page, `s59-${Date.now()}@example.com`);
  const { sessionId } = await startPythonSession(page);

  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByText("Learn Python › Names point at values")).toBeVisible();
  await expect(page.getByText(/Activity 1 of /)).toBeVisible();
  await expect(page.locator("code").filter({ hasText: "n = 3" })).toBeVisible();

  const primaries = page.getByRole("button").filter({ hasText: /^(Next activity|Submit answer|Try a fresh question|Finish session|Now you try)$/ });
  // Action bar primary plus quiet Finish session — count buttons with primary styling via name list
  await expect(page.getByRole("button", { name: "Next activity" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Submit answer" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Tutor help" })).toHaveCount(0);
  await expect(page.getByText("Explain this differently")).toHaveCount(0);

  await page.getByRole("button", { name: "Pause" }).click();
  await expect(page.getByText("Paused.")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Paused.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Resume" })).toBeVisible();
  await page.getByRole("button", { name: "Resume" }).click();

  await page.getByRole("button", { name: "Next activity" }).click();
  await expect(page.getByRole("button", { name: "Now you try" })).toBeVisible();
  await page.getByRole("button", { name: "Now you try" }).click();
  await expect(page.getByRole("group", { name: "Choose one answer" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Submit answer" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Next activity" })).toHaveCount(0);

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator("[data-studio-action-bar]")).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth <= window.innerWidth + 1,
  );
  expect(overflow).toBe(true);

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
    .analyze();
  const serious = results.violations.filter(
    (item) => item.impact === "serious" || item.impact === "critical",
  );
  expect(serious).toEqual([]);

  void primaries;
});

test("reading then worked example then question with Now you try", async ({ page }) => {
  await signIn(page, `s61-${Date.now()}@example.com`);
  const { sessionId } = await startPythonSession(page);
  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByText(/Activity 1 of /)).toBeVisible();
  await expect(page.locator("code").filter({ hasText: "n = 3" })).toBeVisible();
  await page.getByRole("button", { name: "Next activity" }).click();
  await expect(page.getByRole("button", { name: "Now you try" })).toBeVisible();
  await expect(page.getByText(/Start with|rebind|binds/i)).toBeVisible();
  await page.getByRole("button", { name: "Now you try" }).click();
  await expect(page.getByRole("group", { name: "Choose one answer" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Submit answer" })).toBeVisible();
});

test("wrong choice shows misconception note; solution then answer offers a fresh question", async ({
  page,
}) => {
  await signIn(page, `s60-${Date.now()}@example.com`);
  const { sessionId, headers, goalId } = await startPythonSession(page);
  const listed = await page.request.get(`http://127.0.0.1:8000/api/v1/goals/${goalId}/plan`, {
    headers,
  });
  const activities = (await listed.json()).activities as Array<{ id: string; title: string }>;
  const question = activities.find((item) => item.title.endsWith("objective"));
  await page.request.patch(`http://127.0.0.1:8000/api/v1/sessions/${sessionId}`, {
    headers,
    data: {
      event: {
        client_event_id: "to-obj",
        event_type: "progress",
        payload: { plan_activity_id: question?.id },
      },
    },
  });

  await page.goto(`/app/learn/${sessionId}`);
  await page.getByRole("radio", { name: /permanent box/ }).check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText(/A name can be rebound/i)).toBeVisible();
  await expect(page.getByText(/congratulat|great job|streak/i)).toHaveCount(0);

  await page.getByRole("button", { name: "Check a different question" }).click();
  await expect(page.getByRole("button", { name: "Show the solution" })).toBeVisible();
  await page.getByRole("button", { name: "Show the solution" }).click();
  await expect(page.getByText(/You asked for the solution/)).toBeVisible();
  await page.getByRole("radio").first().check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByRole("button", { name: "Try a fresh question" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Next activity" })).toHaveCount(0);
  await expect(page.getByText(/congratulat|great job|well done/i)).toHaveCount(0);
});
