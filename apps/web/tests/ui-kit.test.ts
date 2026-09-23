import { createElement as h } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import {
  Button,
  Chip,
  Field,
  InlineNotice,
  Markdown,
  Page,
  PageHeader,
  Pending,
  Stack,
  Surface,
} from "@/components/ui";

describe("Clear Depth UI kit", () => {
  it("renders Page, Surface, and PageHeader", () => {
    const html = renderToStaticMarkup(
      h(
        Page,
        null,
        h(
          Surface,
          null,
          h(PageHeader, {
            kicker: "Sign in",
            title: "Dolphin",
            subtitle: "Learn anything.",
          }),
        ),
      ),
    );
    expect(html).toContain("Sign in");
    expect(html).toContain("Dolphin");
    expect(html).toContain("Learn anything.");
  });

  it("renders button variants", () => {
    for (const variant of ["primary", "secondary", "quiet"] as const) {
      const html = renderToStaticMarkup(h(Button, { variant, type: "button" }, "Continue"));
      expect(html).toContain("Continue");
    }
  });

  it("renders chips, field, notice, stack, pending, markdown", () => {
    expect(renderToStaticMarkup(h(Chip, { tone: "ai" }, "AI"))).toContain("AI");
    expect(
      renderToStaticMarkup(
        h(Field, { id: "email", label: "Email", name: "email", type: "email" }),
      ),
    ).toContain("Email");
    expect(renderToStaticMarkup(h(InlineNotice, { tone: "warning" }, "Check this"))).toContain(
      "Check this",
    );
    expect(renderToStaticMarkup(h(Stack, { gap: "sm" }, h("span", null, "a")))).toContain("a");
    expect(renderToStaticMarkup(h(Pending, { label: "Thinking…" }))).toContain("Thinking…");
    expect(
      renderToStaticMarkup(h(Markdown, { children: "Use `n = 3` to bind a name." })),
    ).toContain("code");
  });
});
