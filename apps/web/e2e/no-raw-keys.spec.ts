/**
 * S53 baseline: learner-facing screens must not show raw competency keys,
 * reason codes, or underscored facet machine names. Gate 4 requires green.
 */
import { expect, test, type Page } from "@playwright/test";

const KEY_DOT = /\b[a-z]+\.[a-z_]+\b/;
const MACHINE = /_minutes|_deferred|_demonstrated/;

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

async function assertNoRawKeys(page: Page) {
  const text = await page.locator("main").innerText();
  expect(text).not.toMatch(KEY_DOT);
  expect(text).not.toMatch(MACHINE);
}

test("home progress review path and wizard preview hide raw keys", async ({ page }) => {
  await signIn(page, `s53-${Date.now()}@example.com`);
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
        preferred_session_minutes: 25,
      },
    },
  });
  const goalId = (await created.json()).id as string;
  const accepted = await page.request.post(
    `http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`,
    { headers },
  );
  const question = (
    (await accepted.json()).activities as Array<{ id: string; title: string }>
  ).find((item) => item.title.endsWith("objective"));
  const started = await page.request.post("http://127.0.0.1:8000/api/v1/sessions", {
    headers,
    data: { goal_id: goalId },
  });
  const sessionId = (await started.json()).id as string;
  await page.request.patch(`http://127.0.0.1:8000/api/v1/sessions/${sessionId}`, {
    headers,
    data: {
      event: {
        client_event_id: "to-q",
        event_type: "progress",
        payload: { plan_activity_id: question?.id },
      },
    },
  });
  await page.request.post(`http://127.0.0.1:8000/api/v1/sessions/${sessionId}/attempts`, {
    headers,
    data: { idempotency_key: "once", choice: "b" },
  });

  await page.goto("/app");
  await expect(page.getByText("Names and values")).toBeVisible();
  await expect(page.getByText("Shown on your own")).toBeVisible();
  await assertNoRawKeys(page);

  await page.goto("/app/progress");
  await expect(page.getByText("Names and values: Shown on your own")).toBeVisible();
  await expect(page.getByText("Calling a function: Not tried yet")).toBeVisible();
  await assertNoRawKeys(page);

  await page.goto("/app/review");
  await assertNoRawKeys(page);

  const short = await page.request.post("http://127.0.0.1:8000/api/v1/goals", {
    headers,
    data: {
      title: "Short Python",
      domain_key: "python",
      raw_request: "Names only.",
      time_budget: {
        mode: "one_off",
        one_off_minutes: 15,
        preferred_session_minutes: 15,
      },
    },
  });
  const shortId = (await short.json()).id as string;
  await page.request.post(`http://127.0.0.1:8000/api/v1/goals/${shortId}/plans/accept`, {
    headers,
  });
  await page.goto(`/app/goals/${shortId}`);
  await expect(
    page.getByText("Calling a function. Not enough minutes this time"),
  ).toBeVisible();
  await assertNoRawKeys(page);

  await page.goto("/app/goals/new");
  await expect(page.locator("[data-hydrated='true']")).toBeVisible();
  await page.getByLabel("Goal title").fill("Preview names");
  await page.getByLabel("What do you want to learn?").fill("Names only.");
  await page.getByLabel("Subject").selectOption("python");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByLabel("Total minutes").fill("15");
  await page.getByLabel("Preferred session length (minutes)").fill("15");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "Save goal" }).click();
  await expect(page.getByRole("heading", { name: "Goal saved" })).toBeVisible();
  await expect(page.getByText("Not in this plan").first()).toBeVisible();
  await expect(page.getByText(/Names and values/).first()).toBeVisible();
  await expect(page.getByText(/Calling a function/).first()).toBeVisible();
  await assertNoRawKeys(page);
});
