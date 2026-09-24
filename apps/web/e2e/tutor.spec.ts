import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

async function startOnQuestion(page: Page) {
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
  const accepted = await page.request.post(
    `http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`,
    { headers },
  );
  const questions = ((await accepted.json()).activities as { id: string; title: string }[]).filter(
    (item) => item.title.endsWith("objective"),
  );
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
        payload: { plan_activity_id: questions[0].id },
      },
    },
  });
  return { sessionId, headers };
}

test("tutor explain shows AI chip and marks the next answer Assisted", async ({ page }) => {
  test.skip(
    (process.env.AI_PROVIDER ?? "") !== "fake",
    "Requires AI_PROVIDER=fake for the API webServer",
  );
  await signIn(page, `s63-tutor-${Date.now()}@example.com`);
  const me = await page.request.get("http://127.0.0.1:8000/api/v1/me", {
    headers: {
      Authorization: `Bearer ${(await page.context().cookies()).find((c) => c.name === "dolphin_access_token")?.value}`,
    },
  });
  test.skip(!(await me.json()).ai_enabled, "AI must be enabled for tutor e2e");

  const { sessionId } = await startOnQuestion(page);
  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByRole("button", { name: "Tutor help" })).toBeVisible();
  await page.getByRole("button", { name: "Tutor help" }).click();
  await page.getByRole("button", { name: "Explain this differently" }).click();
  await expect(page.getByText("AI").first()).toBeVisible();
  await expect(page.getByText(/sticky note|label/i).first()).toBeVisible();

  await page.getByRole("radio", { name: /bound to the value/i }).check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText(/Assisted|with help/i).first()).toBeVisible();
});

test("E2E-08: studio works with no AI key", async ({ page }) => {
  expect(process.env.OPENAI_API_KEY ?? "").toBe("");
  await signIn(page, `s63-e08-${Date.now()}@example.com`);
  const { sessionId } = await startOnQuestion(page);
  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByRole("group", { name: "Choose one answer" })).toBeVisible();
  if ((process.env.AI_PROVIDER ?? "") === "" || (process.env.AI_PROVIDER ?? "") === "off") {
    await expect(page.getByRole("button", { name: "Tutor help" })).toHaveCount(0);
  }
  await page.getByRole("button", { name: "Show a hint" }).click();
  await expect(page.getByText(/Compare each choice|Hint/i).first()).toBeVisible();
});
