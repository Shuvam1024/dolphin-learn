import { expect, test } from "@playwright/test";

test("security headers present on app shell", async ({ page }) => {
  const response = await page.goto("/sign-in");
  expect(response).not.toBeNull();
  const headers = response!.headers();
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
  expect(headers["content-security-policy"] || "").toContain("default-src");
});
