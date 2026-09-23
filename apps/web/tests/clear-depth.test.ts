import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const css = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "../app/globals.css"),
  "utf8",
);

it("defines the Clear Depth light-theme tokens", () => {
  for (const hex of ["#0B1F2A", "#1FA7A0", "#F4F8F9", "#E8F1F3", "#E6A817", "#5A6B73"]) {
    expect(css).toContain(hex);
  }
  expect(css).toContain("color-scheme: light");
  expect(css).not.toMatch(/prefers-color-scheme:\s*dark/);
});
