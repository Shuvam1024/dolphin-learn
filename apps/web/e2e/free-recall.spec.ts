import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
}

test("free recall hides lesson until submit and shows Self-reported", async ({ page }) => {
  await signIn(page, `s65-recall-${Date.now()}@example.com`);
  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "dolphin_access_token",
  )?.value;
  const headers = { Authorization: `Bearer ${token}` };
  const created = await page.request.post("http://127.0.0.1:8000/api/v1/goals", {
    headers,
    data: {
      title: "Learn Python",
      domain_key: "python",
      raw_request: "Names.",
      time_budget: {
        mode: "one_off",
        one_off_minutes: 180,
        preferred_session_minutes: 30,
      },
    },
  });
  const goalId = (await created.json()).id as string;
  const accepted = await page.request.post(
    `http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`,
    { headers },
  );
  const recalls = ((await accepted.json()).activities as { id: string; title: string }[]).filter(
    (item) => item.title.endsWith("free_recall"),
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
        client_event_id: "to-recall",
        event_type: "progress",
        payload: { plan_activity_id: recalls[0].id },
      },
    },
  });
  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByLabel("Write from memory")).toBeVisible();
  await expect(page.getByText(/sticky note|binding/i)).toHaveCount(0);
  await page.getByLabel("Write from memory").fill("A name is bound to a value.");
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText(/How did that go/i)).toBeVisible();
  await page.getByLabel("Got it").check();
  await page.getByRole("button", { name: "Save self-rating" }).click();
  await expect(page.getByText("Self-reported")).toBeVisible();
});
