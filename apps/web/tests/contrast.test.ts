import { describe, expect, it } from "vitest";

/** WCAG relative luminance for sRGB hex. */
export function luminance(hex: string): number {
  const cleaned = hex.replace("#", "");
  const value = Number.parseInt(cleaned, 16);
  const channels = [(value >> 16) & 255, (value >> 8) & 255, value & 255].map((channel) => {
    const c = channel / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

export function contrastRatio(foreground: string, background: string): number {
  const a = luminance(foreground);
  const b = luminance(background);
  const lighter = Math.max(a, b);
  const darker = Math.min(a, b);
  return (lighter + 0.05) / (darker + 0.05);
}

const INK = "#0B1F2A";
const SEAFOAM = "#1FA7A0";
const FOAM = "#F4F8F9";
const ELEVATED = "#E8F1F3";
const MIST = "#5A6B73";

describe("Clear Depth contrast pairs", () => {
  it("keeps body text at least 4.5:1", () => {
    expect(contrastRatio(INK, FOAM)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(INK, ELEVATED)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(MIST, FOAM)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(FOAM, INK)).toBeGreaterThanOrEqual(4.5);
  });

  it("rejects seafoam-on-foam for body text and uses ink kickers instead", () => {
    expect(contrastRatio(SEAFOAM, FOAM)).toBeLessThan(4.5);
    expect(contrastRatio(INK, ELEVATED)).toBeGreaterThanOrEqual(4.5);
  });
});
