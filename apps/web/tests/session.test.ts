import { expect, it } from "vitest";

import { signInRedirect } from "../lib/session";

it("sends anonymous /app visits to sign-in", () => {
  expect(signInRedirect("/app", false)).toBe("/sign-in");
  expect(signInRedirect("/app/goals", false)).toBe("/sign-in");
  expect(signInRedirect("/app", true)).toBeNull();
  expect(signInRedirect("/", false)).toBeNull();
  expect(signInRedirect("/sign-in", false)).toBeNull();
});
