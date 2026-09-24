# Dolphin learning log

Teach notes for each sequential build step (what / how / why). The product is **Dolphin**.

**Status of this file:** S01–S57 notes live in the long-form log kept with the team store. This in-repo log holds **S58 onward**. The step index, test results, and “next step” line live only in [`design/04-implementation-status.md`](design/04-implementation-status.md).

Do not duplicate the first-ship plan here.

---

## How to append

After each completed step, add a heading `## Snn — <title>` with commit hash, what/how/why, and the named tests that passed.

## Next incomplete step

**None in the first-ship plan.** S51–S105 complete; tag **v0.1.0**. Post-v0.1 work is outside `06-first-ship-plan.md` (see `05-direction.md`).

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

## S76 — AI plan explainer

**Commit:** `070adf1` — feat(plan): ai plan explainer over deterministic planner output

**What:** Plan and replan previews explain the plan in plain words. When AI is on, a validated explanation appears with an AI chip. Invented lesson names or numbers fall back to the deterministic rationale. Results cache on the proposal hash.

**How:** `prompts/plan_explain.v1`; `plan_explain.py` validator + cache; wired into plan-proposals and replan-proposals; ReplanPanel shows Why this plan.

**Why:** The planner stays deterministic; the explainer only narrates what was already decided.

**Acceptance:** passed — pytest 125 passed, 6 skipped (`test_plan_explain`).

**Push:** `070adf1` is on origin/main

## S77 — Progress v2

**Commit:** `4cee800` — feat(progress): progress v2 grouped by goal with legend and upcoming reviews

**What:** Progress groups evidence by goal with facet chips, unassessed counts, a collapsed legend linking to Help, and upcoming reviews. Still no percent.

**How:** Expanded `GET /progress` with `goals[]` and `upcoming_reviews[]`; progress page redesigned; e2e progress-v2.

**Why:** Evidence belongs to a goal shelf, not a flat global list.

**Acceptance:** passed — pytest 126 passed, 6 skipped (`test_progress_v2`).

**Push:** `4cee800` is on origin/main

## S78 — Review v2 with fit

**Commit:** `12f839a` — feat(review): review v2 with estimates and what fits

**What:** Due reviews show estimated minutes and what fits this sitting against preferred session length. Snooze presets are 3h / 24h / 72h. Copy avoids overdue, missed, and streak.

**How:** `GET /reviews/due` adds `estimated_minutes`, `fits{count,minutes}`, `preferred_session_minutes`; review page fit line + presets; `test_review_fit`.

**Why:** A sitting should start with what fits, not a guilt list.

**Acceptance:** passed — pytest 129 passed, 6 skipped (`test_review_fit`).

**Push:** `12f839a` is on origin/main

## S79 — Wizard preview on the kit (interim)

**Commit:** `b506ed6` — feat(web): wizard preview with lesson names, minutes, live priority, and plan explanation

**What:** Goal wizard preview lists lesson names with minutes, total vs budget, Not in this plan, and the plan explanation. Priority uses three plain labels and live-refetches the proposal.

**How:** Priority maps to understand/apply/make_it_stick; PATCH + plan-proposals on change; e2e goal-wizard updated for minutes and no raw keys.

**Why:** Accept should follow a clear preview, not a surprise plan.

**Acceptance:** passed — pytest 129 passed, 6 skipped; e2e goal-wizard updated.

**Push:** `b506ed6` is on origin/main

## S80 — Gate 4: organized and adaptive

**Commit:** `521352b` — docs: phase 4 organized and adaptive verified; every screen in ux spec

**What:** Phase 4 is verified: priority plans, Home v2, Learn shelf, shell/Help, path + replan preview, plan explainer, Progress by goal, review fit, wizard preview. UX docs name every screen as built.

**How:** Pytest AI off and fake; API perf recorded; axe zero and baseline deleted; no-raw-keys; E2E-03; checklist signed for Phase 4 screens; updates to `01-product-and-ux`, `05-direction`, `04-implementation-status`, `prove-loop-demo`.

**Why:** Organization and time adaptivity must be true before General-route learning expands the subject set.

**Acceptance:** passed — pytest 129 passed, 6 skipped (off + fake); axe zero; E2E-03 green; no-raw-keys green; API p95 under 250ms.

**Push:** `521352b` is on origin/main

## S81 — General route: goal-scoped competencies

**Commit:** `3f79959` — feat(goals): general route with goal-scoped competencies from the learner

**What:** Something else accepts any topic with learner outcomes. Each outcome becomes an owned competency with reading, free recall, and reflection. Notes are sanitized. Evidence from free recall stays at practicing; a got_it schedules a later recall review.

**How:** Alembic `0016_owned_competencies`; `general` payload on POST /goals; owner filters in proposals/progress/home/reviews; domain `general`.

**Why:** Checked subjects are not the ceiling — any subject can start from the learner's own outcomes.

**Acceptance:** passed — pytest 132 passed, 6 skipped (`test_general_route`).

**Push:** `3f79959` is on origin/main

## S82 — Placement API: confirmed skips

**Commit:** `0a63610` — feat(goals): placement diagnostic proposes skips confirmed by the learner

**What:** Placement suggests competencies to skip; nothing is skipped until the learner sends `skip_competency_keys`. Replan clears skips. General route has no placement.

**How:** Diagnostic starts with 3–5 unseen items; `goal_competencies.requirement=skipped`; plan-proposals accept skip keys; replan clears them.

**Why:** The learner decides what to skip — the sample never claims mastery.

**Acceptance:** passed — pytest 134 passed, 6 skipped (`test_placement_skips`).

**Push:** `0a63610` is on origin/main

## S83 — AI goal normalizer

**Commit:** `35f16d5` — feat(goals): ai goal normalizer suggests title, subject, and outcomes

**What:** Free text becomes a suggested title, subject, and "I can …" outcomes. Nothing is saved. When AI is off, the endpoint returns 404 so the wizard falls back to manual fields.

**How:** `POST /goals/normalize` → `goal_normalize.v1`; unknown domains rejected; web proxy included.

**Why:** The learner still edits every field — AI only drafts the first pass.

**Acceptance:** passed — pytest 137 passed, 6 skipped (`test_goal_normalize`).

**Push:** `35f16d5` is on origin/main

## S84 — Wizard v2

**Commit:** `d50cafe` — feat(web): wizard v2 with ai suggestions, subject chips, presets, focus, placement, and preview

**What:** Five steps — Learn, Time, Focus, Placement, Plan. Presets include 30×14 = 7 hours. Draft survives reload. Something else skips placement.

**How:** sessionStorage draft; subject chips; AI suggest via normalize; placement confirm skips; Accept primary.

**Why:** One guided path from wish to accepted plan without losing the learner's edits.

**Acceptance:** `e2e/wizard-v2.spec.ts` and updated `goal-wizard.spec.ts`.

**Push:** `d50cafe` is on origin/main

## S85 — AI provisional outlines for General

**Commit:** `e7949df` — feat(general): ai provisional outlines, readings, and recall prompts

**What:** Something else goals can request a provisional outline with short readings and recall prompts. Drafts are never graded and never carry answer keys.

**How:** `POST /goals/{id}/outline-proposals` → `general_outline.v1`; accept replaces gather-material prompts; `pick_unseen(graded=True)` returns none.

**Why:** AI drafts material; the learner edits or removes before trust.

**Acceptance:** passed — pytest 139 passed, 6 skipped (`test_provisional_outline`).

**Push:** `e7949df` is on origin/main

## S86 — AI item drafting → human review

**Commit:** `c1c646b` — feat(content): ai item drafting with reviewer approval before graded use

**What:** A CLI drafts graded items into provisional `.drafts.yaml` files. Near-duplicates are rejected. Nothing provisional is seeded as graded.

**How:** `python -m app.content.draft_items --competency …`; Jaccard ≥ 0.8 reject; content-review checklist AI steps.

**Why:** Speed without teaching something wrong — a person still stamps review.

**Acceptance:** passed — pytest 142 passed, 6 skipped (`test_item_drafts`).

**Push:** `c1c646b` is on origin/main

## S87 — Deep Python path

**Commit:** `5f9c09a` — feat(content): python fundamentals with eight competencies

**What:** Python now has eight competencies (names through errors) deep enough for about two weeks.

**How:** New lessons and items; DAG edges; validator green; plan at 420 minutes covers ≥ 6.

**Why:** Checked subjects need enough depth that a real plan feels usable.

**Acceptance:** passed — pytest 144 passed, 6 skipped (`test_python_path`).

**Push:** `5f9c09a` is on origin/main

## S88 — Deeper math and software

**Commit:** `a0fbbb2` — feat(content): deeper fractions and software practice paths

**What:** Fractions gain equivalent and compare; software gains smallest fix and describe a test.

**How:** Four competencies each; numeric items in math; validator green.

**Why:** Every checked subject needs a path that can fill a real sitting budget.

**Acceptance:** passed — pytest 146 passed, 6 skipped (`test_math_software_path`).

**Push:** `a0fbbb2` is on origin/main

## S89 — Content quality in CI and audit

**Commit:** `f9c4cfc` — test(content): enforce content checklist in ci and publish the audit

**What:** Content CI fails on missing review stamps. The audit lists every competency with types, sources, difficulty, and AI-reviewed items.

**How:** `python -m app.content.audit` → `docs/evaluations/content-audit.md`; CI content job validates and rejects unreviewed fixtures.

**Why:** Depth without drift — every graded item stays reviewable.

**Acceptance:** passed — pytest 148 passed, 6 skipped (`test_content_audit`); audit errors 0.

**Push:** `f9c4cfc` is on origin/main

## S90 — Gate 5: learn anything

**Commit:** `80e789f` — docs: phase 5 learn anything verified; general route and ai drafting in vision, ux, and architecture

**What:** Phase 5 is gated. General route, placement skips, normalizer, wizard v2, provisional outlines, item drafting, deep content, and content audit are verified with AI off and fake.

**How:** Pytest green both modes (148 passed, 6 skipped); ai-eval extended to goal_normalize, general_outline, item_draft, plan_explain; vision/UX/architecture/direction and prove-loop demo updated.

**Why:** Learning anything must be real before the learner model starts adapting estimates.

**Acceptance:** Gate 5 met.

**Push:** `80e789f` is on origin/main

## S91 — Effort calibration from active minutes

**Commit:** `f1e9e74` — feat(learner-model): effort calibration from measured active minutes

**What:** Per learner and activity type, an EMA of observed/declared minutes scales plan estimates after three observations. Clamped 0.5–2.0. The path can show one sentence that estimates were adjusted.

**How:** Alembic `0018_learner_effort_factors`; `learner_model.effort`; session progress/finish records observations; proposals scale effort.

**Why:** Plans should fit how long this learner actually takes — without inventing competence.

**Acceptance:** passed — pytest 151 passed, 6 skipped (`test_effort_calibration`).

**Push:** `f1e9e74` is on origin/main

## S92 — Difficulty- and history-aware item selection

**Commit:** `1d249a0` — feat(learner-model): difficulty and history aware item selection

**What:** Next graded item is chosen by purpose and history: first attempts stay easy (1–2); after an independent correct, the fresh check steps up one level; after assisted or incorrect, same or lower with a different item. Reviews alternate difficulty. Solution-revealed items never return. Each pick logs a `selection_reason`.

**How:** Alembic `0019_activity_difficulty`; `item_pool.pick_next`; evidence fresh-check uses it; seed writes difficulty 1–3.

**Why:** Practice should match what the learner just showed — without recycling revealed solutions.

**Acceptance:** passed — pytest 153 passed, 6 skipped (`test_item_selection`).

**Push:** `1d249a0` is on origin/main

## S93 — AI evaluation harness and safety suite

**Commit:** `9e1ae7d` — test(ai): evaluation harness and safety suite for all prompts

**What:** Every prompt (tutor + normalize/outline/draft/plan_explain) has scripted cases for leakage, overlong, wrong-language, and injection. Plan/outline reject fabricated lesson names. Gateway timeout and daily-cap are asserted per prompt. Import-graph keeps `ai_gateway` and `learner_model` apart from the referee.

**How:** Expanded `tests/ai_eval/` fixtures and validators; `test_safety_limits.py`; `test_ai_import_graph` covers `learner_model`; `make ai-eval` rewrote `docs/evaluations/ai-eval-2026-09-24.md`.

**Why:** One safety bar for every model call before adaptivity and release.

**Acceptance:** passed — pytest 170 passed, 6 skipped; make ai-eval green; live/scripted pass rates recorded with no known failures.

**Push:** `9e1ae7d` is on origin/main

## S94 — Learning dataset and honest funnel events

**Commit:** `4f72e00` — feat(analytics): learning dataset views and product events

**What:** Product events record funnel steps with opaque ids only. SQL views `v_attempt_features` and `v_review_outcomes` expose the columns a future estimator would need. Docs describe the funnel and why calibrated models stay post-ship.

**How:** Alembic `0020_product_events_views`; `app/analytics/events.py` wired into goal/plan/session/tutor/review paths; `docs/evaluations/funnel.md` and `learner-model-roadmap.md`.

**Why:** Adaptivity now stays transparent; tomorrow's estimators need a clean dataset without PII or raw answers.

**Acceptance:** passed — pytest 173 passed, 6 skipped (`test_events`); views queryable; no raw answers/notes/emails in props.

**Push:** `4f72e00` is on origin/main

## S95 — Gate 6: learner model

**Commit:** `86352dd` — docs: phase 6 learner model verified; adaptivity rules and dataset in architecture

**What:** Phase 6 is verified: effort calibration, difficulty/history item selection, AI safety suite, and the learning dataset/funnel. Architecture and direction name the learner model and what stays post-ship.

**How:** Pytest green AI off and fake; make ai-eval; E2E-07 delayed check with a test clock; updates to `02-architecture`, `05-direction`, `prove-loop-demo`.

**Why:** Close the adaptivity phase before account/trust/release.

**Acceptance:** passed — pytest 174 passed, 6 skipped (off + fake); ai-eval green; E2E-07 green.

**Push:** `86352dd` is on origin/main

## S96 — Settings

**Commit:** `13d176c` — feat(settings): preferences page wired to the profile api

**What:** Settings covers name, timezone, usual sitting length, larger text, reduced motion, and Use the tutor. Larger text sets data-text=large; reduced motion sets data-motion=reduce. Tutor off writes ai_opt_out and hides the Studio tutor panel. Privacy section points ahead to download/delete.

**How:** Alembic 0021_profile_session_minutes; preferences PATCH; /app/settings form; PrefsBootstrap on the app shell.

**Why:** Learners need control of comfort and AI before strangers use the product.

**Acceptance:** passed — pytest 176 passed, 6 skipped (test_settings); e2e/settings.spec.ts green.

**Push:** `13d176c` is on origin/main

## S97 — Managed auth for production

**Commit:** `8d7b2d9` — feat(auth): managed provider sign-in for production with dev token gated

**What:** Production verifies RS256 via AUTH_JWKS_URL; the email form and /dev/token exist only in development. Logout revokes the token jti. OIDC callback sets a Secure HttpOnly SameSite=Lax cookie. No password field.

**How:** auth_revocations table; /auth/revoke; session/callback; NEXT_PUBLIC_ENVIRONMENT gate; docs/evaluations/auth-sandbox-s97.md.

**Why:** Strangers need a real managed sign-in; the local form must not ship.

**Acceptance:** passed — pytest 181 passed, 6 skipped (test_auth_production).

**Push:** `8d7b2d9` is on origin/main

## S98 — Export my data

**Commit:** `78f85f7` — feat(privacy): export my data as json

**What:** Learners can download a JSON export of profile, goals, owned content, AI call metadata (no prompts), effort factors, attempts, and evidence. Rate limit 3/hour.

**How:** GET /me/export; Settings Download; /privacy documents it.

**Why:** People should see and take what Dolphin holds about them.

**Acceptance:** passed — test_export two-user isolation and rate limit.

**Push:** `78f85f7` is on origin/main

## S99 — Delete my account

**Commit:** `4e4872c` — feat(privacy): delete account with confirmation and retention disclosure

**What:** DELETE /me with confirm DELETE tombstones the account, revokes the session, and schedules purge after 30 days. AI audit rows are anonymized on purge.

**How:** users.deleted_at; app.jobs.purge; Settings delete control; /privacy states the window.

**Why:** Leaving must be possible without a support ticket.

**Acceptance:** passed — test_delete_account.

**Push:** `4e4872c` is on origin/main

## S100 — Edge hardening

**Commit:** `0945acc` — feat(security): csp, headers, rate limits, and error pages

**What:** CSP with nonce, security headers, API rate limits, honest error and not-found pages.

**How:** Next middleware; rate_limit on sensitive routes; error.tsx / not-found.tsx; security-audit note.

**Why:** Strangers need a hardened edge before first ship.

**Acceptance:** passed — test_rate_limits; e2e/security.spec.ts.

**Push:** `0945acc` is on origin/main

## S101 — Containers and runbook

**Commit:** `c3f44e2` — chore(deploy): dockerfiles, prod compose, and runbook with migrations on release

**What:** API and web Dockerfiles, prod compose with migrate one-shot, runbook for env backup rollback and purge.

**How:** infra/compose.prod.yml; infra/RUNBOOK.md; Next standalone output.

**Why:** First ship needs a one-command deploy path.

**Acceptance:** passed — compose and runbook present; /ready used for health after migrate.

**Push:** `c3f44e2` is on origin/main

## S102 — Observability

**Commit:** `6cf2f52` — feat(observability): structured logs, ai metrics, and readiness

**What:** JSON request logs, AI metrics at /metrics, /ready checks DB, AI usage CLI.

**How:** observability middleware; metrics basic auth; test_observability.

**Why:** Operators need cost latency and readiness signals.

**Acceptance:** passed — test_observability.

**Push:** `6cf2f52` is on origin/main

## S103 — Golden release suite

**Commit:** 7832c1f — test(e2e): golden release suite

**What:** Curated Playwright release suite (E2E catalog) runs AI off and FakeProvider; CI job release-suite; wizard and Studio e2e aligned to v2.

**How:** playwright.release.config.ts; make release-suite; e2e/release/; CI matrix off/fake.

**Why:** First ship needs one golden path that stays green in both tutor modes.

**Acceptance:** passed — AI off 21 passed 1 skipped; AI fake 22 passed; flake list empty.

**Push:** 7832c1f is on origin/main


## S104 — Release-candidate review

**Commit:** `80c1ab9` — docs: v0.1 release candidate verification, ai evaluation, and design review record

**What:** RC record covers golden suite both modes, API p95 under budget, axe zero serious/critical, design-review screens, known limitations, no P0s.

**How:** docs/evaluations/v0.1-rc.md; checklist Gate 7 screens; direction and prove-loop demo updated.

**Why:** First ship needs an honest verification gate before the tag.

**Acceptance:** passed — gate met with AI off and fake; no P0 findings.

**Push:** `80c1ab9` is on origin/main

## S105 — Ship v0.1.0

**Commit:** `d128805` — release: v0.1.0 first ship

**What:** Tag v0.1.0 with CHANGELOG, README limits, design status, and learning log through S105.

**How:** CHANGELOG.md; README what shipped / what did not; tag v0.1.0 on main.

**Why:** Close the first-ship plan with an honest, runnable release.

**Acceptance:** passed — tag on main; learning log S51–S105 present; pytest 189 passed 6 skipped; golden suite green both modes.

**Push:** `d128805` is on origin/main
