import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

test("settings: persistence, larger font, tutor off hides panel", async ({ page }) => {
  const email = `s96-${Date.now()}@example.com`;
  await signIn(page, email);

  await page.goto("/app/settings");
  await expect(page.getByRole("heading", { name: "Your preferences" })).toBeVisible();

  await page.getByLabel("Name").fill("Sam");
  await page.getByLabel("Usual sitting length (minutes)").fill("45");
  await page.getByLabel("Larger text").check();
  await page.getByLabel("Use the tutor").uncheck();
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Saved.")).toBeVisible();

  await page.reload();
  await expect(page.getByLabel("Name")).toHaveValue("Sam");
  await expect(page.getByLabel("Usual sitting length (minutes)")).toHaveValue("45");
  await expect(page.getByLabel("Larger text")).toBeChecked();
  await expect(page.getByLabel("Use the tutor")).not.toBeChecked();

  const fontSize = await page.evaluate(() => {
    return Number.parseFloat(getComputedStyle(document.body).fontSize);
  });
  expect(fontSize).toBeGreaterThanOrEqual(17);

  const dataText = await page.evaluate(() => document.documentElement.dataset.text);
  expect(dataText).toBe("large");

  // Tutor panel stays hidden when opted out (Studio tutor.enabled false).
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
        one_off_minutes: 60,
        preferred_session_minutes: 25,
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
  await expect(page.getByText("Tutor help")).toHaveCount(0);
});

test("settings: export download parses as json", async ({ page }) => {
  const email = `s98-${Date.now()}@example.com`;
  await signIn(page, email);
  await page.goto("/app/settings");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download my data" }).click();
  const download = await downloadPromise;
  const path = await download.path();
  expect(path).toBeTruthy();
  const fs = await import("node:fs/promises");
  const raw = await fs.readFile(path!, "utf8");
  const parsed = JSON.parse(raw) as { user?: { email?: string }; goals?: unknown[] };
  expect(parsed.user?.email).toContain("@");
  expect(Array.isArray(parsed.goals)).toBeTruthy();
});
