# Design review checklist

**Product:** Dolphin  
**Used by:** every phase gate and every screen step that touches UI  
**Created:** S51  

A screen passes only when every item below is true. Sign the screen in the gate commit by naming it and linking the PR/commit that cleared it.

## Visual system

- [ ] Uses only Clear Depth tokens (no one-off hex outside `globals.css` / kit CSS modules)
- [ ] Type ramp is the app scale (display 28–40px, body 16–17px, meta 14px) — not the marketing 52px display
- [ ] Contrast: body text ≥ 4.5:1, large text ≥ 3:1 (see `brand.md` after S52)
- [ ] No glow, purple gradient, or decorative card stack in the hero / primary study surface

## Copy and honesty

- [ ] No raw competency keys, UUIDs, reason codes, or plan version numbers as learner-facing copy
- [ ] Every status shown to the learner uses a plain label (from the copy module after S53)
- [ ] At most one explanatory sentence per screen; definitions live in Help
- [ ] No streak, mastery percent, celebration, or guilt copy
- [ ] Copy is about the learner’s study, not about the product’s internals

## Interaction

- [ ] Exactly one primary action on the screen (button variant `primary`)
- [ ] Secondary and quiet actions use the matching button variants
- [ ] Loading, empty, and error states are present and readable
- [ ] Tutor-generated text (when present) carries the Tutor label/chip; pending tutor waits show a cancelable pending state
- [ ] Dead controls are absent (every control either works or is not shown)

## Accessibility

- [ ] Keyboard-only path reaches the primary action and completes the screen’s job
- [ ] Focus is visible
- [ ] 390px width has no horizontal scroll
- [ ] `prefers-reduced-motion` is honored (no essential motion that cannot be reduced)
- [ ] `@axe-core/playwright` reports zero serious or critical violations on this route (empty and populated where both apply)

## Performance (recorded at the gate)

- [ ] Page meets TTFB ≤ 800 ms, DCL ≤ 1.5 s, LCP ≤ 2.5 s against `next start` on the harness machine
- [ ] First-load JS for the route ≤ 130 kB (Next build output)
- [ ] Deterministic API calls behind the screen stay within p95 ≤ 250 ms on the heavy fixture


## Gate 4 signed screens (S80)

Signed for Phase 4 — organized and adaptive. Tokens, no raw keys, one primary, Help for definitions, no streak/percent/guilt, AI labeled when shown.

| Screen | Route | Notes |
|---|---|---|
| Landing | `/` | Product in five lines; Sign in primary |
| Home v2 | `/app` | One next action; goal cards; due count |
| Learn shelf | `/app/learn` | Active / Paused / Archived |
| Goal path v2 | `/app/goals/:id` | Minutes left; chips; replan preview → accept |
| Wizard preview | `/app/goals/new` | Live priority; minutes; explanation |
| Progress v2 | `/app/progress` | By goal; legend → Help; upcoming reviews |
| Review v2 | `/app/review` | Fit line; snooze 3/24/72h |
| Help / More / Settings | `/app/help`, `/app/more`, `/app/settings` | Honest Help; More links |

API p95 recorded under Gate 4 in `04-implementation-status.md`. Axe baseline deleted; zero serious/critical on `/app` routes.

## Gate 7 / RC signed screens (S104)

Signed for Phase 7 — account, trust, release. Same checklist; Settings privacy and export/delete added.

| Screen | Route | Notes |
|---|---|---|
| Settings | `/app/settings` | Prefs; tutor toggle; export; delete |
| Privacy | `/privacy` | Export rate limit; 30-day retention |
| Sign-in | `/sign-in` | Dev form only in development |

RC record: `docs/evaluations/v0.1-rc.md`.
