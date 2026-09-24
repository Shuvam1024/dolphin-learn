import { expect, test } from "@playwright/test";

test("reading studio shows the explanation and pause survives refresh", async ({ page }) => {
  const email = `s27-${Date.now()}@example.com`;
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();

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
  expect(created.status()).toBe(201);
  const goalId = (await created.json()).id as string;
  const accepted = await page.request.post(
    `http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`,
    { headers },
  );
  expect(accepted.status()).toBe(201);
  const started = await page.request.post("http://127.0.0.1:8000/api/v1/sessions", {
    headers,
    data: { goal_id: goalId },
  });
  expect(started.status()).toBe(201);
  const sessionId = (await started.json()).id as string;

  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByRole("heading", { name: "Names point at values" })).toBeVisible();
  await expect(page.getByText("binds the name")).toBeVisible();
  await expect(page.getByText("Mode: Guided")).toBeVisible();
  await expect(page.getByText("The clock stops when you pause")).toBeVisible();
  await expect(page.getByText(/Studied in this session:/)).toBeVisible();
  await expect(page.getByText("time remaining")).toHaveCount(0);

  await page.getByRole("button", { name: "Pause" }).click();
  await expect(page.getByText("Paused.")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Paused.")).toBeVisible();
  await expect(page.getByText("binds the name")).toBeVisible();
  await expect(page.getByRole("button", { name: "Resume" })).toBeVisible();
});

test("objective question records an answer", async ({ page }) => {
  const email = `s28-${Date.now()}@example.com`;
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();

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
        client_event_id: "to-question",
        event_type: "progress",
        payload: { plan_activity_id: question?.id },
      },
    },
  });

  await page.goto(`/app/learn/${sessionId}`);
  await expect(page.getByRole("group", { name: "Choose one answer" })).toBeVisible();
  await page.getByRole("radio", { name: /bound to the value 3/ }).check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText("Answer recorded: b")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Answer recorded: b")).toBeVisible();
  await expect(page.getByRole("button", { name: "Submit answer" })).toHaveCount(0);
});

test("finish shows an honest summary and pause does not finish", async ({ page }) => {
  const email = `s31-${Date.now()}@example.com`;
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();

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

  await page.goto(`/app/learn/${sessionId}`);
  await page.getByRole("button", { name: "Pause" }).click();
  await expect(page.getByText("Paused.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Session finished" })).toHaveCount(0);

  await page.getByRole("button", { name: "Finish session" }).click();
  await expect(page.getByRole("heading", { name: "Session finished" })).toBeVisible();
  await expect(page.getByText("This summary counts stored attempts only")).toBeVisible();
  await expect(page.getByText(/streak|congratulations|great job/i)).toHaveCount(0);
});
