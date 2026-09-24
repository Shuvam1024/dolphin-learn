import AxeBuilder from "@axe-core/playwright";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { writeFileSync } from "node:fs";
import path from "node:path";

const APP_ROUTES = [
  "/app",
  "/app/learn",
  "/app/review",
  "/app/library",
  "/app/progress",
  "/app/more",
  "/app/goals/new",
] as const;

type Violation = {
  route: string;
  fixture: "empty" | "populated";
  id: string;
  impact: string | null;
  help: string;
  nodes: number;
};

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

async function tokenFrom(page: Page): Promise<string> {
  const cookie = (await page.context().cookies()).find(
    (item) => item.name === "dolphin_access_token",
  );
  expect(cookie?.value).toBeTruthy();
  return cookie!.value;
}

async function populateLearner(request: APIRequestContext, token: string) {
  const headers = { Authorization: `Bearer ${token}` };
  const created = await request.post("http://127.0.0.1:8000/api/v1/goals", {
    headers,
    data: {
      title: "Learn Python",
      domain_key: "python",
      raw_request: "Names and calls for a11y.",
      time_budget: {
        mode: "one_off",
        one_off_minutes: 120,
        preferred_session_minutes: 30,
      },
    },
  });
  expect(created.ok()).toBeTruthy();
  const goalId = (await created.json()).id as string;
  const accepted = await request.post(
    `http://127.0.0.1:8000/api/v1/goals/${goalId}/plans/accept`,
    { headers },
  );
  expect(accepted.ok()).toBeTruthy();
  const started = await request.post("http://127.0.0.1:8000/api/v1/sessions", {
    headers,
    data: { goal_id: goalId },
  });
  expect(started.ok()).toBeTruthy();
  const sessionId = (await started.json()).id as string;
  return { goalId, sessionId };
}

async function scan(
  page: Page,
  route: string,
  fixture: "empty" | "populated",
): Promise<Violation[]> {
  await page.goto(route);
  await page.waitForLoadState("domcontentloaded");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
    .analyze();
  return results.violations
    .filter((item) => item.impact === "serious" || item.impact === "critical")
    .map((item) => ({
      route,
      fixture,
      id: item.id,
      impact: item.impact ?? null,
      help: item.help,
      nodes: item.nodes.length,
    }));
}

test("axe baseline over empty and populated /app routes", async ({ page, request }) => {
  const email = `s51-a11y-${Date.now()}@example.com`;
  await signIn(page, email);
  const token = await tokenFrom(page);

  const found: Violation[] = [];
  for (const route of APP_ROUTES) {
    found.push(...(await scan(page, route, "empty")));
  }

  const { goalId, sessionId } = await populateLearner(request, token);
  const populatedRoutes = [
    "/app",
    "/app/learn",
    "/app/review",
    "/app/progress",
    `/app/goals/${goalId}`,
    `/app/learn/${sessionId}`,
  ];
  for (const route of populatedRoutes) {
    found.push(...(await scan(page, route, "populated")));
  }

  const byRoute: Record<string, Omit<Violation, "route">[]> = {};
  for (const item of found) {
    const { route, ...rest } = item;
    (byRoute[route] ??= []).push(rest);
  }

  const baselinePath = path.join(__dirname, "a11y-baseline.json");
  writeFileSync(
    baselinePath,
    JSON.stringify(
      {
        recorded_at: new Date().toISOString(),
        note: "S58 Gate 2 baseline: serious/critical by route. Later gates require zero.",
        serious_or_critical: found,
        by_route: byRoute,
        totals: {
          serious_or_critical: found.length,
          routes_with_findings: Object.keys(byRoute).length,
        },
      },
      null,
      2,
    ),
  );

  // S51 records current violations; it does not fail the suite on them.
  expect(baselinePath).toContain("a11y-baseline.json");
  console.log(`a11y baseline: ${found.length} serious/critical finding(s)`);
});
