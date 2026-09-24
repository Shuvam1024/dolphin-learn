# Dolphin learning log

Teach notes for each sequential build step (what / how / why). The product is **Dolphin**.

**Status of this file:** S01–S57 notes live in the long-form log kept with the team store. This in-repo log holds **S58 onward**. The step index, test results, and “next step” line live only in [`design/04-implementation-status.md`](design/04-implementation-status.md).

Do not duplicate the first-ship plan here.

---

## How to append

After each completed step, add a heading `## Snn — <title>` with commit hash, what/how/why, and the named tests that passed.

## Next incomplete step

**S63 — Tutor: explain differently and validated hints** in [`design/06-first-ship-plan.md`](design/06-first-ship-plan.md).

---

## S58 — Gate 2: foundations

**Commit:** `c032262` — docs: phase 2 foundations verified; content model, ai gateway, and studio contract in architecture

**What:** Phase 2 foundations are verified end-to-end: harness, UI kit, copy, activity types, content files, AI gateway, and Studio payload. Architecture and brand docs now describe those pieces.

**How:** Ran the full suite with AI off and with FakeProvider; validated content; recorded axe baseline by route and API/page perf budgets; updated e2e specs that still expected raw keys or pre-S55 lesson wording; updated `02-architecture.md` (content files/rules, activity provenance, gateway hygiene, studio contract) and `brand.md` (kit + copy notes).

**Why:** A phase gate locks what is true before Studio v2 builds on it.

**Acceptance:** passed — AI off/fake 81 passed + 6 skipped; content ok; smoke 22 passed; axe baseline 13 by route; API p95 under 250ms; page LCP under budget; docs updated.

**Push:** `c032262` is on origin/main.

## S59 — Studio v2 renderer

**Commit:** `010f1ba` — feat(studio): studio v2 renderer for every activity type with tutor panel

**What:** Session Studio is rebuilt from kit pieces: header with goal › lesson and activity position, markdown body with real `<code>`, answer inputs by kind, a tutor panel that stays hidden when AI is off, and one sticky primary action.

**How:** Added `components/studio/*` (StudioHeader, ActivityBody, AnswerInput, FeedbackNotice, TutorPanel, ActionBar) wired to the S57 studio payload (`studio_activity`, `actions`, `tutor`). Pause stays quiet in the header. `e2e/studio-v2.spec.ts` covers markdown, primary rules, pause, 390px bar, axe zero, and no tutor with AI off; quick-learn updated for rendered markdown.

**Why:** Studio v2 is the place learners actually study — one clear action and honest content before tutor and grading deepen in later steps.

**Acceptance:** passed — smoke 23 passed; studio-v2 green; pytest 81 passed, 6 skipped; tsc/eslint/vitest clean.

**Push:** `010f1ba` is on origin/main

## S60 — Feedback with explanation and misconception note

**Commit:** `be1d702` — feat(studio): feedback with explanation and the note for your mistake

**What:** After every graded attempt (or reveal), Studio shows the explanation and — for a wrong objective choice — the seeded note for that mistake. Assisted answers make the primary "Try a fresh question." The session summary collects a "Watch out for" list.

**How:** `studio_view` fills explanation after attempt or reveal and misconception notes by choice; content rules require ≥1 misconception on objectives; `summary.watch_out_for` aggregates incorrect-attempt notes; FeedbackNotice uses success/warning tones without celebration copy.

**Why:** Immediate, specific feedback is the teaching moment — the referee stays deterministic; the note names the mistake.

**Acceptance:** passed — pytest 84 passed, 6 skipped; studio-v2 e2e extended; content ok.

**Push:** `be1d702` is on origin/main

## S61 — Worked examples

**Commit:** `2c06fb2` — feat(content): worked example activity between reading and practice

**What:** Every checked-subject lesson now has a worked example between the reading and the first question. Studio labels the primary "Now you try"; continuing it writes no evidence.

**How:** Loader turns `## Worked example` into a `worked_example` activity (effort 3–5) after reading; seed orders by type; accept keeps that order; validator warns when a checked subject lacks one.

**Why:** Seeing one solved case before the first attempt is basic teaching structure.

**Acceptance:** passed — pytest 88 passed, 6 skipped; smoke 25; content ok.

**Push:** `2c06fb2` is on origin/main

## S62 — Unseen item pools

**Commit:** `e2632e6` — feat(assess): unseen item selection; provisional items never graded

**What:** Fresh checks and reviews serve items the learner has not seen yet. Provisional graded items are never selected for grading. Exhausted pools mark `repeat`; a correct answer on an item whose solution was revealed stays practicing.

**How:** Added `item_pool.pick_unseen` (never-attempted first, then least-recent; filters `provisional=false` when graded). Wired into `move_to_unseen_question` and `reviews._objective`; studio `state.repeat` from fresh-check events; evidence caps revealed items at practicing.

**Why:** A fresh check only proves something if it is actually new — and AI drafts must not grade until reviewed.

**Acceptance:** passed — pytest 93 passed, 6 skipped (`test_item_pools.py`: avoid seen, repeat, provisional excluded, reviews rotate, ownership 404).

**Push:** `e2632e6` is on origin/main

