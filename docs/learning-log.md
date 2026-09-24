# Dolphin learning log

Teach notes for each sequential build step (what / how / why). The product is **Dolphin**.

**Status of this file:** S01–S57 notes live in the long-form log kept with the team store. This in-repo log holds **S58 onward**. The step index, test results, and “next step” line live only in [`design/04-implementation-status.md`](design/04-implementation-status.md).

Do not duplicate the first-ship plan here.

---

## How to append

After each completed step, add a heading `## Snn — <title>` with commit hash, what/how/why, and the named tests that passed.

## Next incomplete step

**S66 — Size the sitting** in [`design/06-first-ship-plan.md`](design/06-first-ship-plan.md).

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

**Commit:** `b2599e3` — feat(assess): unseen item selection; provisional items never graded

**What:** Fresh checks and reviews serve items the learner has not seen yet. Provisional graded items are never selected for grading. Exhausted pools mark `repeat`; a correct answer on an item whose solution was revealed stays practicing.

**How:** Added `item_pool.pick_unseen` (never-attempted first, then least-recent; filters `provisional=false` when graded). Wired into `move_to_unseen_question` and `reviews._objective`; studio `state.repeat` from fresh-check events; evidence caps revealed items at practicing.

**Why:** A fresh check only proves something if it is actually new — and AI drafts must not grade until reviewed.

**Acceptance:** passed — pytest 93 passed, 6 skipped (`test_item_pools.py`: avoid seen, repeat, provisional excluded, reviews rotate, ownership 404).

**Push:** `b2599e3` is on origin/main

## S63 — Tutor: explain differently and validated hints

**Commit:** `c4c7819` — feat(tutor): explain differently and validated generated hints with seeded fallback

**What:** The tutor can explain a lesson differently and give a hint. Generated hints are checked against the key; a leak falls back to the seeded hint. Explain and hints count as help for the current item. With AI off, explain is 404 and the panel stays hidden.

**How:** Added `tutor.py` with `hint_validator`, `request_hint`, and `request_explain`; prompts `hint.v1` and `explain_differently.v1`; `POST /sessions/{id}/explain`; studio fills `hint_text`/`alt_explanation` from session events; FakeProvider defaults for those prompts; web help route forwards explain; `e2e/tutor.spec.ts`.

**Why:** A second explanation and a safe hint are real teaching work — the validator keeps the referee honest.

**Acceptance:** passed — pytest 98 passed, 6 skipped (`test_tutor.py`: leak→seeded, clean AI hint, explain assistance, AI-off 404).

**Push:** `c4c7819` is on origin/main

## S64 — Typed grading and AI misconception notes

**Commit:** `c09e19f` — feat(assess): short answer and numeric grading; ai misconception note for typed mistakes

**What:** Short-answer and numeric items grade deterministically (normalize text; parse decimals/fractions with tolerance). A wrong typed answer can get an AI misconception note labeled AI — the grade is decided first and never changed by the model.

**How:** Extended `grading.py`; `submit_attempt` accepts choice/text/value; Alembic `0012_evaluation_feedback_json`; `misconception_note.v1` + validator; seed numeric + short_answer items; studio shows AI chip on the note.

**Why:** Typed practice needs a referee that is not a model; the note is advice only.

**Acceptance:** passed — pytest 102 passed, 6 skipped (`test_grading_types`, `test_ai_misconception`).

**Push:** `c09e19f` is on origin/main

## S65 — Free recall with a self-report ceiling

**Commit:** `7e69baa` — feat(assess): free recall with self-rating capped at practicing

**What:** Free recall: write from memory (lesson hidden), then see the lesson and self-rate. Evidence never exceeds practicing. AI recall comparison is advisory only.

**How:** `free_recall.py` + `POST /sessions/{id}/self-rate`; `recall_compare.v1`; studio hides body until text submit; Self-reported chip; reviews skip retained for free-recall items.

**Why:** Honest engine for any subject — self-check with a hard ceiling.

**Acceptance:** passed — pytest 104 passed, 6 skipped (`test_free_recall_ceiling`).

**Push:** `7e69baa` is on origin/main

## S66 — Size the sitting

**Commit:** `5f28ddf` — feat(sessions): target minutes per sitting from the learner

**What:** Before a new sitting, the learner picks how long they have (10–60 or their usual). The session stores that target and sizes the remaining-minutes estimate to it. Resume never asks again.

**How:** Alembic `0013_sessions_target_minutes`; `POST /sessions` accepts `target_minutes` (default preferred, bounds 5–180); SittingChooser at `/app/goals/[goalId]/start`; `_sized_remaining` stops once cumulative low exceeds the target (≥ 1 activity); header shows "About N minutes".

**Why:** Dolphin should adapt to the time the learner actually has right now.

**Acceptance:** passed — pytest 106 passed, 6 skipped (`test_session_sizing`).

**Push:** `5f28ddf` is on origin/main

## S67 — Remaining estimate and a good stopping point

**Commit:** `acf9ed7` — feat(studio): remaining estimate and good stopping point without a countdown

**What:** Studio quietly shows how many minutes are left in this sitting. When active minutes reach the target and the current activity is complete, it offers a good place to stop — Finish primary, Keep going secondary. Nothing is forced; there is no countdown.

**How:** `actions.stop_point` when active ≥ target and current complete; header remaining range + stop notice; ActionBar Keep going advances; `DOLPHIN_E2E_FAST_CLOCK=1` for e2e; grep gate bans countdown/timer/time's up copy.

**Why:** Respect the learner's time without guilt or a ticking clock.

**Acceptance:** passed — pytest 107 passed, 6 skipped (`test_stop_point`).

**Push:** `acf9ed7` is on origin/main

## S68 — Session summary v2

**Commit:** `1991706` — feat(sessions): summary v2 with what you showed, what to watch, and what is next

**What:** End-of-session summary lists what you showed on your own, practiced with help, and self-reported, plus watch-outs, next review, minutes studied, and a next step — without celebration copy.

**How:** `summary.py` fills the v2 buckets; finish screen renders them on the kit; forbidden-words checks keep streaks and praise out.

**Why:** The close of a sitting should be honest and useful, not a cheer.

**Acceptance:** passed — pytest 109 passed, 6 skipped (`test_summary_v2`).

**Push:** `1991706` is on origin/main

## S69 — Learning-session AI evaluation fixtures

**Commit:** `fbf3c20` — test(ai): tutor prompt evaluation fixtures and regression suite

**What:** Scripted evaluation cases for tutor prompts (hint, explain differently, misconception note, recall compare) — leaks, overlong, injection, wrong language — all must pass validators.

**How:** `tests/ai_eval/` JSON fixtures (≥20 per prompt) + validators; `make ai-eval` runs them and writes `docs/evaluations/ai-eval-<date>.md`.

**Why:** Tutors stay useful only if adversarial outputs are rejected before learners see them.

**Acceptance:** passed — pytest 112 passed, 6 skipped; make ai-eval green; report recorded.

**Push:** `fbf3c20` is on origin/main

## S70 — Gate 3: the learning session

**Commit:** `9dabf8f` — docs: phase 3 learning session verified; studio, tutor, and activity types in ux spec

**What:** Phase 3 is verified: Studio v2, feedback, worked examples, unseen pools, typed grading, free recall, tutor, sitting size, stop point, summary v2, and ai-eval. UX and architecture docs name what shipped.

**How:** Full pytest with AI off and FakeProvider; `make ai-eval`; gate Playwright set; updates to `01-product-and-ux`, `02-architecture`, `05-direction`, and `prove-loop-demo` (typed answer, free recall, tutor explain, sized sitting).

**Why:** A phase gate locks what is true before Home/Learn organization builds on it.

**Acceptance:** passed — pytest 112 passed, 6 skipped (off + fake); ai-eval green; e2e 13 passed, 1 skipped.

**Push:** `9dabf8f` is on origin/main

## S71 — Priority that shapes the plan

**Commit:** `349a187` — feat(plan): priority enum shapes breadth, depth, and review reserve

**What:** Goals store a focus priority. Understand packs by low effort (breadth). Apply packs by high effort (deeper practice). Make it stick keeps about one fifth of minutes for review.

**How:** Alembic `0014_goal_priority`; `propose_plan(..., priority)`; POST/PATCH and plan-proposals accept priority; rationale uses plain labels, never raw enums.

**Why:** The same minutes should mean different plans when the learner wants breadth, depth, or stickiness.

**Acceptance:** passed — pytest 116 passed, 6 skipped (`test_priority_planner`).

**Push:** `349a187` is on origin/main

## S72 — Home v2

**Commit:** `237a6e7` — feat(home): home v2 with one next action, goal cards, reviews, and evidence chips

**What:** Home centers one next action with subtitle and minutes, goal cards with subject and next lesson, due-review count, and evidence chips. Log out moved off Home.

**How:** Expanded `GET /home`; Promise.all for me+home; Retry on load error; e2e home-v2.

**Why:** One clear next step beats a dashboard of equal-weight widgets.

**Acceptance:** passed — pytest 117 passed, 6 skipped.

**Push:** `237a6e7` is on origin/main

## S73 — Learn: every goal, organized

**Commit:** `a14d13b` — feat(learn): goal list with continue, pause, and archive

**What:** Learn lists Active / Paused / Archived goals with Continue, Pause, Resume, and Archive. Home next action skips paused and archived goals.

**How:** Alembic `0015_goal_status`; PATCH status; GET /goals card fields; `/app/learn` sections.

**Why:** Learners need one shelf for every goal, not only the current sitting.

**Acceptance:** passed — pytest 118 passed, 6 skipped.

**Push:** `a14d13b` is on origin/main

## S74 — Shell, landing, sign-in, Help

**Commit:** `4074358` — feat(web): responsive shell, landing page, and help

**What:** Mobile bottom tabs under 768px; desktop top bar. Landing states the product in five lines without a placeholder. Help explains evidence, minutes, reviews, and that the tutor never grades. More links Settings, Help, Privacy, Sign out.

**How:** `nav.tsx` dual chrome; `/app/help`; `/app/settings` stub; e2e/shell.spec.ts.

**Why:** Organization needs a calm shell and honest Help before path and review deepen.

**Acceptance:** passed — shell e2e added; pytest 118 passed, 6 skipped.

**Push:** `4074358` is on origin/main

## S75 — Goal path v2 with replan preview → accept

**Commit:** `6a2d945` — feat(goals): path v2 with chips and minutes; replan preview then accept

**What:** The goal path shows remaining minutes, lesson chips with effort ranges, Not in this plan, and plan history. Update plan previews first; Accept writes the next version. A stale preview hash is rejected.

**How:** `POST /replan-proposals` (no write) and `POST /replan/accept {proposal_hash}` (409 on stale); overview adds effort, facet labels, remaining_minutes, plan_history; ReplanPanel + e2e goal-path-v2.

**Why:** Learners should see the change before the plan moves, and minutes should stay honest against the original budget.

**Acceptance:** passed — pytest 121 passed, 6 skipped (`test_replan_preview`).

**Push:** `6a2d945` is on origin/main
