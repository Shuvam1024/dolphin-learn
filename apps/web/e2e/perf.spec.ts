import { expect, test, type Page } from "@playwright/test";

import { budgets } from "./budgets";

type PageTiming = {
  route: string;
  ttfbMs: number;
  dclMs: number;
  lcpMs: number;
};

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I am 18 or older and I understand" }).click();
  await expect(page.getByRole("heading", { name: "You are in" })).toBeVisible();
}

async function measure(page: Page, route: string): Promise<PageTiming> {
  await page.addInitScript(() => {
    (window as unknown as { __dolphinLcp?: number }).__dolphinLcp = 0;
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === "largest-contentful-paint") {
          (window as unknown as { __dolphinLcp?: number }).__dolphinLcp = entry.startTime;
        }
      }
    });
    observer.observe({ type: "largest-contentful-paint", buffered: true });
  });

  const response = await page.goto(route, { waitUntil: "load" });
  expect(response?.ok()).toBeTruthy();
  await page.waitForTimeout(500);

  const timing = await page.evaluate(() => {
    const nav = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming;
    const lcp = (window as unknown as { __dolphinLcp?: number }).__dolphinLcp ?? 0;
    return {
      ttfbMs: nav.responseStart,
      dclMs: nav.domContentLoadedEventEnd,
      lcpMs: lcp || nav.domContentLoadedEventEnd,
    };
  });

  return { route, ...timing };
}

test("page budgets against next start", async ({ page }) => {
  const email = `s51-perf-${Date.now()}@example.com`;
  await signIn(page, email);

  const routes = ["/app", "/app/goals/new", "/app/progress", "/app/review", "/app/learn"];
  const rows: PageTiming[] = [];
  for (const route of routes) {
    rows.push(await measure(page, route));
  }

  for (const row of rows) {
    console.log(
      `perf page ${row.route}: ttfb=${row.ttfbMs.toFixed(0)}ms dcl=${row.dclMs.toFixed(0)}ms lcp=${row.lcpMs.toFixed(0)}ms`,
    );
    expect(row.ttfbMs).toBeLessThanOrEqual(budgets.ttfbMs);
    expect(row.dclMs).toBeLessThanOrEqual(budgets.dclMs);
    expect(row.lcpMs).toBeLessThanOrEqual(budgets.lcpMs);
  }
});
