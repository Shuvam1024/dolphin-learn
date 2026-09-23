# Dolphin — First-ship plan (S51–S96)

**Document status:** Sequential build plan to a shippable first release (v0.1) — not a claim of shipped code  
**Last updated:** September 23, 2026  
**Continues:** `03-build-plan.md` (S01–S50 done: Phase 0, 1A Prove Loop, 1B retention, 1C study time, 1D honest demo content)  
**Assessment behind this plan:** product and design assessment after S50 (project store `docs/product-design-assessment.md`; summary in `05-direction.md`)  
**Companion docs:** `00`/`01`/`02` (spec), `03-build-plan.md` (S01–S50), `04-implementation-status.md` (tracker), `05-direction.md` (judgment)

---

## The vision this plan serves

The learner can **learn anything they want**, keep learning **organized in one place**, get **real learning content, technique, and performance**, and have Dolphin **adapt to the task and the time they actually have**. The UI stays **clean and easy to use**; most of the machinery is **behind the scenes**. Every step below is judged on appeal, usefulness, and ease for the learner.

Rules that do not move: assisted ≠ independent; same-session ≠ retention; no mastery percent; no streak guilt; active study minutes, not calendar dates; seeded content works with no AI key; a model may explain but never writes an evidence row; computing content is demo focus, not a learner sequence; the core stays subject-agnostic.

## How to use this plan

1. One step at a time, in ID order. Commit after each step with the suggested message.
2. A step is done only when its **Acceptance** holds — including the tests it names — and the teach note has been written into `docs/learning-log.md` (and reported in chat).
3. A **gate** step closes each phase. Do not begin the next phase until the gate passes and the design docs named in the gate are updated.
4. Keep `docs/design/04-implementation-status.md` current after every step.
5. Do not start Vault uploads, RAG, or a code sandbox in this plan. Those are Phase 7+ (after first ship).

## Phase map

| Phase | Steps | Outcome |
|---|---|---|
| **2 — Clean surface** | S51–S61 | Verification harness; UI kit; names not keys; Home, Learn, shell, Studio, path, Progress redesigned; replan preview→accept |
| **3 — Time you can feel** | S62–S68 | Presets; real priority; session sizing; quiet remaining estimate; good stopping point; minutes on the path and Home |
| **4 — Real content and technique** | S69–S80 | Content as validated files; item pools; explanations; short-answer/numeric; free recall; deep Python; deeper math and software; General route for anything; placement diagnostic; worked examples |
| **5 — Optional AI behind the scenes** | S81–S86 | Gateway; explain-differently/hints with seeded fallback; goal intake suggestion; provisional outlines for General; safety tests. Flagged; ship may go dark |
| **6 — Account, trust, release** | S87–S96 | Settings; managed auth; export/delete; security headers; deploy; observability; golden E2E; release candidate; v0.1 tag |

## Verification standard used in every gate

- **Full suite green:** `ruff`, `mypy`, `pytest`; `eslint`, `tsc --noEmit`, `vitest`; `playwright test` (all specs). CI green on `main`.
- **Accessibility:** `@axe-core/playwright` reports **zero serious or critical** violations on every `/app` route in both empty and populated states; keyboard-only golden journey passes; focus visible; 390px width has no horizontal scroll; `prefers-reduced-motion` honored.
- **Performance budget (local, reproducible):** API deterministic endpoints (`/home`, `/progress`, `/reviews/due`, `/goals/{id}/overview`, `/sessions/{id}`, `/goals/{id}/plan-proposals`) **p95 ≤ 250 ms** in-process against local Postgres for a seeded learner with 5 goals, 3 plan versions, 60 attempts, 20 review items. Web pages via `next build && next start`: **TTFB ≤ 800 ms, DOMContentLoaded ≤ 1.5 s, LCP ≤ 2.5 s** on the harness machine; first-load JS per route ≤ 130 kB (Next build output). Numbers are recorded in `04-implementation-status.md` with the machine noted. Budgets are floors to keep, not marketing.
- **Design review checklist** (`docs/design/design-review-checklist.md`, created in S51): tokens only; no raw keys, ids, reason codes, or version numbers as learner copy; one primary action per screen; button hierarchy (primary / secondary / quiet); at most one explanatory sentence per screen (definitions live in Help); loading/empty/error states present; no streak, percent, or celebration copy; copy is about the learner's study.
- **Docs:** `04-implementation-status.md`, `docs/learning-log.md`, and the design docs the gate names are updated in the gate commit.

---

## Phase 2 — Clean surface (S51–S61)

Make what already works look and read like a product. Nothing in the ledger or clock changes here.

### S51 — Verification harness

| Field | Value |
|---|---|
| **Title** | Add accessibility, performance-budget, and design-checklist harness |
| **Commit** | `test: add axe, perf budget, and design review checklist harness` |
| **Files/areas** | `apps/web/e2e/a11y.spec.ts` (`@axe-core/playwright` over every `/app` route, empty and populated fixtures); `apps/web/e2e/perf.spec.ts` (Navigation Timing + LCP via `PerformanceObserver`, budgets as constants, runs against `next start`); `services/api/tests/perf/test_latency_budget.py` (seeded heavy learner fixture; 50 calls per endpoint; asserts p95 ≤ 250 ms; skipped unless `DOLPHIN_PERF=1`); `docs/design/design-review-checklist.md`; `Makefile` targets `a11y`, `perf`, `check` (everything); CI job `perf-a11y` |
| **Acceptance** | `make check` runs every suite; axe reports current violations as a baseline file (failures allowed only in this step, recorded); perf test prints p95 per endpoint and page; checklist exists with the items listed under "Verification standard"; CI runs the new jobs |

**Teach note:**  
**What:** Before changing screens, we build the ruler we will measure them with.  
**How:** Axe checks the DOM for WCAG failures; Navigation Timing gives TTFB/DCL/LCP; the API perf test uses the same TestClient as other tests, with a heavy fixture so numbers mean something.  
**Why:** The user asked that intensive verification precede "done." A budget that exists only in a doc is not a budget.

### S52 — UI kit on Clear Depth

| Field | Value |
|---|---|
| **Title** | Add shared UI components and verified contrast pairs |
| **Commit** | `feat(web): add clear depth ui kit with verified contrast` |
| **Files/areas** | `apps/web/components/ui/`: `Page` (header with kicker/title/subtitle, content grid), `Surface`, `Button` (`primary` ink, `secondary` seafoam outline, `quiet` text), `Chip` (facet variants: exposed / practicing / demonstrated / retained / unassessed / deferred), `Field` (label + input + help + error), `Stack`, `InlineNotice` (info / success / warning), `Markdown` (react-markdown, no raw HTML, code styled in Plex Mono); `globals.css` type scale (display 28–40px in app, not 52px); `brand.md` contrast table |
| **Acceptance** | Vitest renders each component; contrast pairs recorded in `brand.md` with measured ratios (all text ≥ 4.5:1, large text ≥ 3:1; kicker moved to ink-on-foam if seafoam fails); Storybook is **not** added; sign-in and gate migrated to the kit as the first consumers; axe on `/sign-in` and gate: zero serious/critical; design checklist passes for both |

**Teach note:**  
**What:** One set of parts every screen will use.  
**How:** Small server-friendly React components with CSS modules on the existing tokens. Button variants encode hierarchy so screens stop stacking identical black pills.  
**Why:** Every route currently borrows the sign-in card. A kit is how "clean and easy" becomes repeatable instead of hand-tuned.

### S53 — Names, not keys

| Field | Value |
|---|---|
| **Title** | Return display names and plain reasons from every learner-facing endpoint |
| **Commit** | `feat(api): expose competency names and plain reasons in learner payloads` |
| **Files/areas** | `home.py`, `progress_router.py`, `overview.py`, `reviews.py`, `proposals.py`, `summary.py`: add `competency_name`, `lesson_title`, `reason_text` beside existing keys; `app/modules/learning/copy.py` maps `insufficient_minutes` → "Not enough minutes this time", `prerequisite_deferred` → "Comes after a topic that did not fit", facets → learner words; contracts types updated |
| **Acceptance** | Pytest: every payload item with a `competency_key` also has a non-empty `competency_name`; reason codes always have `reason_text`; existing tests unchanged; Playwright `no-raw-keys.spec.ts` asserts no text matching `/\b[a-z]+\.[a-z_]+\b/` (competency keys) or `_minutes|_deferred` appears on Home, Progress, Review, goal path, or wizard preview |

**Teach note:**  
**What:** The API keeps keys for machines and adds words for people.  
**How:** A single copy module owns the mapping so wording changes in one place. Keys stay in payloads for tests and links.  
**Why:** "Machinery behind the scenes" starts with the vocabulary. `python.names` is a database identifier, not a lesson.

### S54 — Home as a hub

| Field | Value |
|---|---|
| **Title** | Redesign Home around one next action, goal cards, reviews, and evidence chips |
| **Commit** | `feat(web): redesign home around the next action` |
| **Files/areas** | `apps/web/app/app/page.tsx` + `home.module.css` on the kit; hero next action (verb + lesson name + goal + "about N minutes" from activity effort when known); goal cards (title, subject, "N of M minutes studied", one Continue); due reviews as a count and one Review button; evidence as named chips; Quick Learn as secondary; **Log out removed** (lives in More); loading skeleton + error notice instead of redirect-on-error |
| **Acceptance** | Playwright `home.spec.ts` updated: empty state shows one Create a goal primary; populated state shows exactly one primary button; the next action text names the lesson, not the key; no "Log out" on Home; a 500 from the API shows an inline error with Retry, not a sign-in redirect; axe zero serious/critical; design checklist pass; perf: Home TTFB within budget (single API call — `loadMe` and `loadHome` merged server-side or fetched in parallel) |

**Teach note:**  
**What:** Home answers "what now?" with one thing, then context.  
**How:** The hero reads the existing `next_action`; cards read `goals`; chips read `recent_evidence`. Parallel fetches keep TTFB down.  
**Why:** The hub is a product lock. Today it is three bullet lists and a Log out button.

### S55 — Learn lists goals; pause and archive

| Field | Value |
|---|---|
| **Title** | Make Learn the organized list of goals with continue, pause, and archive |
| **Commit** | `feat(learn): list goals with continue pause and archive` |
| **Files/areas** | `GET /api/v1/goals` returns subject name, minutes usable/studied, next activity title, open session, status; `PATCH /goals/{id}` accepts `status` in `active | paused | archived`; Home hides archived and does not pick paused goals as the next action; `/app/learn/page.tsx` lists active, then paused, then an archived disclosure; empty state only when no goals exist |
| **Acceptance** | Pytest: pause removes a goal from Home's next-action candidates but keeps its evidence and reviews; archive hides it from Learn's active list; another user gets 404; Playwright: with two goals, Learn shows both with Continue; pausing one changes Home's next action; axe and design checklist pass |

**Teach note:**  
**What:** Learn becomes the shelf where every goal lives.  
**How:** The goal `status` column already exists. We expose it and read it in Home's ranking.  
**Why:** "Organized in one place" needs a place. A static "No session yet" page is a dead end.

### S56 — Shell, landing, and sign-in

| Field | Value |
|---|---|
| **Title** | Responsive app shell with bottom tabs on small screens; real landing page |
| **Commit** | `feat(web): responsive shell with mobile tabs and a real landing page` |
| **Files/areas** | `nav.tsx` → top bar on ≥ 768px, bottom tab bar under 768px (Learn / Review / Library / Progress, More in the bar); `aria-current` and safe-area padding; landing `/` explains what Dolphin does and does not promise in five short lines, one Sign in; `/sign-in` on the kit with the dev-mode note shown only when `ENVIRONMENT=development` |
| **Acceptance** | Playwright at 390px: tab bar visible, no horizontal scroll, tab order reachable by keyboard; at 1280px: top bar; landing contains the tagline and no "placeholder" text; axe zero serious/critical on `/`, `/sign-in`, and shell; perf: landing LCP within budget |

**Teach note:**  
**What:** The frame around every screen, on a phone and a laptop.  
**How:** One `Nav` component with a media query; the landing page uses the kit's `Page`.  
**Why:** The first sentence a visitor reads should not be a build note; the nav should work with a thumb.

### S57 — Studio layout and rendered content

| Field | Value |
|---|---|
| **Title** | Rebuild Session Studio layout: header, rendered markdown, action bar |
| **Commit** | `feat(studio): studio layout with rendered content and action hierarchy` |
| **Files/areas** | `/app/learn/[sessionId]/page.tsx` + module CSS on the kit; header: goal › lesson, "Activity n of m", minutes studied (quiet), Pause as a quiet icon-button; content: `Markdown` renderer for reading body and prompt; action bar: one primary (Submit answer, or Continue after a reading), Show a hint secondary, Show the solution / Finish session quiet; **Next activity hidden until** the reading is marked read or the answer is recorded; `GET /sessions/{id}` adds `position`, `total`, `lesson_title`, `goal_title`; mobile: action bar sticks to the bottom |
| **Acceptance** | Pytest: session payload includes position/total/titles; Playwright `studio.spec.ts`: reading shows rendered `<code>` (no literal backticks), exactly one primary button, Next absent before an answer and present after; pause persists across reload (existing); at 390px the action bar is visible without scrolling; axe zero serious/critical; design checklist pass |

**Teach note:**  
**What:** The lesson surface becomes a lesson surface.  
**How:** The same server-rendered forms, arranged by importance; markdown rendered safely (no raw HTML).  
**Why:** Session Studio is a pillar. Seven identical buttons and literal backticks read as a prototype.

### S58 — Feedback after an answer

| Field | Value |
|---|---|
| **Title** | Show inline feedback with an explanation, then offer the honest next step |
| **Commit** | `feat(studio): inline feedback with explanation and next-step offer` |
| **Files/areas** | Alembic: `activity_versions.explanation` (nullable text); seed adds a one- or two-sentence explanation to every objective item; `GET /sessions/{id}` returns `explanation` only after an attempt exists or the solution was revealed; Studio: `InlineNotice` success/warning with the explanation; primary becomes **Continue**; after an assisted answer the primary becomes **Try a fresh question** (existing independent-check route); the "Marked independent/assisted" label becomes a chip |
| **Acceptance** | Pytest: explanation absent before an attempt, present after; challenge mode still hides it; Playwright: wrong answer shows the explanation and Continue; after Show the solution the primary is Try a fresh question and the chip reads Assisted; no celebration copy; axe and checklist pass |

**Teach note:**  
**What:** Right or wrong, the learner learns why.  
**How:** One new column and one payload rule: explanations are visible only after the learner has committed an answer.  
**Why:** Feedback is where teaching happens. "Outcome: correct" teaches nothing.

### S59 — Goal path redesign and replan preview

| Field | Value |
|---|---|
| **Title** | Redesign the goal path; replan shows a preview and requires Accept |
| **Commit** | `feat(goals): path with facet chips and replan preview before accept` |
| **Files/areas** | `POST /goals/{id}/replan` becomes `POST /goals/{id}/replan-proposals` (preview from remaining minutes and demonstrated facets, no write) + `POST /goals/{id}/replan/accept` (writes version N+1); `/app/goals/[goalId]` on the kit: lesson list with facet chips and minute ranges, "Why this next?" as subtitle under the next item, "Not in this plan" section with plain reasons, Update plan → preview panel → Accept; version number moves to a quiet "Plan history" disclosure |
| **Acceptance** | Pytest: replan proposal writes no version; accept writes N+1 with the S45 semantics (remaining minutes, demonstrated excluded, evidence unchanged); Playwright `replan.spec.ts` updated to preview → Accept; no raw reason codes; axe and checklist pass; overview p95 within budget |

**Teach note:**  
**What:** The path reads as lessons, and changing it is a two-step choice.  
**How:** Split the replan route the same way S24/S25 split propose and accept.  
**Why:** S36 wrote the new version on click. The product rule is that the learner accepts plans; the path should also read like a plan, not a table of labels.

### S60 — Progress grouped by goal

| Field | Value |
|---|---|
| **Title** | Redesign Progress as an evidence ledger grouped by goal |
| **Commit** | `feat(progress): group evidence by goal with chips and upcoming reviews` |
| **Files/areas** | `GET /progress` adds `goals[]` each with competencies (name, facet, last independent result date), `upcoming_reviews[]`, `unassessed` per goal; `/app/progress` on the kit: per-goal groups, facet chips, a collapsed legend ("What these words mean"), upcoming reviews; still no percent |
| **Acceptance** | Pytest: grouping matches accepted plans; a learner with two goals sees two groups; no `percent`/`mastery` fields; Playwright `progress.spec.ts`: legend collapsed by default and readable when expanded; no raw keys; axe and checklist pass |

**Teach note:**  
**What:** Progress tells the truth per goal instead of as one flat list.  
**How:** Project the same `competency_state` rows through the goal's accepted activities.  
**Why:** A learner with two goals wants to know where each stands. Definitions belong in a legend, not a lede paragraph.

### S61 — Gate 2: clean surface

| Field | Value |
|---|---|
| **Title** | Verify Phase 2 and update the design docs |
| **Commit** | `docs: phase 2 clean surface verified; update ux spec and status` |
| **Files/areas** | `04-implementation-status.md` (results with numbers), `docs/learning-log.md`, `01-product-and-ux.md` (Home, Learn, Studio, path, Progress as built; button hierarchy; copy rules), `brand.md` (contrast table), `README.md` screenshots section optional |
| **Acceptance** | Verification standard fully met: full suite green; axe zero serious/critical on every `/app` route (baseline file from S51 deleted); perf budgets met and recorded; design checklist signed per screen; `docs/prove-loop-demo.md` click path re-run by hand and updated |

**Teach note:**  
**What:** Stop and check the whole surface before changing behavior.  
**How:** Run the harness, walk the demo script, write the numbers down.  
**Why:** A gate is where "intensive testing and verification" is not a slogan.

---

## Phase 3 — Time you can feel (S62–S68)

The clock and budget are honest. Now the learner feels them inside a sitting.

### S62 — Budget presets and a plain summary

| Field | Value |
|---|---|
| **Title** | Add minute presets and a spelled-out total to the wizard |
| **Commit** | `feat(web): budget presets with a plain total in the goal wizard` |
| **Files/areas** | Wizard step 2: preset chips (10, 15, 30, 60, 120 minutes; 15×7, 30×14, 45×10 sittings) + Custom; live summary "30 minutes × 14 sittings = 7 hours of study"; preferred session length defaults to the per-sitting minutes when weekly; no deadline field anywhere |
| **Acceptance** | Vitest for the summary formatter (singular/plural, hours rounding); Playwright `goal-wizard.spec.ts`: choosing 30×14 shows "7 hours" and saves 420 usable; custom entry still validates as before; keyboard reachable; axe and checklist pass |

**Teach note:**  
**What:** Numbers with meaning attached.  
**How:** Presets fill the same fields; the summary is computed client-side from the payload.  
**Why:** "120" in a box is not a decision. "Two hours in one sitting" is.

### S63 — A priority that changes the plan

| Field | Value |
|---|---|
| **Title** | Store priority as an enum and make the planner use it |
| **Commit** | `feat(plan): priority enum shapes breadth depth and review reserve` |
| **Files/areas** | Alembic `goals.priority` in `understand | apply | make_it_stick` (learner labels: "Understand the basics", "Get good at doing it", "Make it stick"); migrate existing `Priority: …` strings; planner: `understand` fits competencies by `effort_low` (breadth); `apply` allocates `effort_high` and includes all practice items for fewer competencies (depth); `make_it_stick` reserves 20% of usable minutes for review before fitting; rationale names the effect in plain words; wizard step 3 updates the preview live |
| **Acceptance** | Pytest planner invariants: prerequisites never violated under any priority; `understand` includes ≥ as many competencies as `apply` at equal minutes; `make_it_stick` reports `reserved_review_minutes` = 20% and fits the rest; changing priority on an accepted goal only affects the next replan; Playwright: switching priority changes the preview's included list |

**Teach note:**  
**What:** The one control that did nothing now does something the learner can see.  
**How:** Three deterministic strategies over the same closure and effort ranges.  
**Why:** A stored string that never changes behavior is a dead control; the design bans those.

### S64 — Size the sitting

| Field | Value |
|---|---|
| **Title** | Ask how long the learner has right now and size the session to it |
| **Commit** | `feat(sessions): target minutes for this sitting from the learner` |
| **Files/areas** | `POST /sessions` accepts `target_minutes` (default `preferred_session_minutes`); session stores it; the session's activity list is the plan's next activities whose summed `effort_low` fits the target (at least one); Home's Continue and the path's Continue open a small "How long do you have?" chooser (presets 10/15/30/45/60, default preferred) before starting; resuming does not ask again |
| **Acceptance** | Pytest: a 15-minute target on a plan whose next activities are 5–8, 3–5, 20–40 includes the first two and not the third; a target below the first activity still includes one; another user 404; Playwright `session-sizing.spec.ts`: choose 15, Studio header shows "about 15 minutes"; axe and checklist pass |

**Teach note:**  
**What:** "I have 20 minutes now" becomes a real input.  
**How:** The session reads a target and takes activities from the plan until they no longer fit.  
**Why:** Adapting to the time they actually have is the pillar; the stored preference was never read.

### S65 — Quiet remaining estimate and a good stopping point

| Field | Value |
|---|---|
| **Title** | Show a quiet remaining estimate; offer a stopping point at the target |
| **Commit** | `feat(studio): remaining estimate and good stopping point without a countdown` |
| **Files/areas** | Studio header: "About N minutes left in this sitting" computed from remaining activities' `effort_low`–`effort_high` and `active_minutes` (range, never a timer); when `active_minutes ≥ target_minutes` and the current activity is complete, an `InlineNotice`: "Good place to stop" with **Finish** primary and **Keep going** secondary; nothing is forced |
| **Acceptance** | Pytest for the estimate helper (ranges, clamping at zero); Playwright: with a 1-minute target (test-only preset) the notice appears after an answer and Keep going continues; no `countdown`, `timer`, or `time's up` text anywhere; the estimate never shows seconds; axe and checklist pass |

**Teach note:**  
**What:** The learner knows roughly how much is left and when it is fine to stop.  
**How:** Sum ranges of remaining activities; compare active minutes to the target.  
**Why:** Time-adaptive means guidance, not pressure. A countdown is the thing we refuse.

### S66 — Minutes on the path

| Field | Value |
|---|---|
| **Title** | Show minute ranges per lesson and minutes left on the goal path |
| **Commit** | `feat(goals): lesson minute ranges and minutes left on the path` |
| **Files/areas** | Overview adds per-activity `effort_low/high` and goal-level `remaining_minutes = max(0, usable − studied)`; path shows "~5–8 min" per lesson and "About 390 of 420 minutes left" in the header; Learn cards show the same |
| **Acceptance** | Pytest: remaining matches S45's arithmetic; Playwright `studied-budget.spec.ts` updated to the new sentence; no percent bar; axe and checklist pass |

**Teach note:**  
**What:** The plan shows its own cost.  
**How:** Effort ranges already exist on `activity_versions`; we expose and sum them.  
**Why:** A learner deciding whether to start should see "about 8 minutes," not guess.

### S67 — Review minutes and Home fit

| Field | Value |
|---|---|
| **Title** | Estimate review minutes and say what fits on Home |
| **Commit** | `feat(home): review estimates and what fits in the next sitting` |
| **Files/areas** | `GET /reviews/due` adds `estimated_minutes` per item (item effort range low); Home hero adds "Fits in about N minutes" for the next action; if due reviews total more than the preferred session, Home says "Start with N reviews (about M minutes)" and offers the rest later — never "catch up on everything" |
| **Acceptance** | Pytest: with 8 due items at 3 minutes and a 15-minute preference, Home proposes 5 and names the remainder as later; Playwright `review.spec.ts`: due card shows "about N minutes"; no "overdue", "missed", or "streak" copy; axe and checklist pass |

**Teach note:**  
**What:** Even reviews respect the time the learner has.  
**How:** Sum item estimates against the preferred session length.  
**Why:** Dumping every due item onto one day is the classic spaced-repetition guilt trap. We refuse it.

### S68 — Gate 3: time you can feel

| Field | Value |
|---|---|
| **Title** | Verify Phase 3 and update the design docs |
| **Commit** | `docs: phase 3 time you can feel verified; update time rules and status` |
| **Files/areas** | `04-implementation-status.md`, `docs/learning-log.md`, `01-product-and-ux.md` (Time Intelligence UX rules: presets, sizing, stopping point, review fit), `05-direction.md` (priority semantics), `00-vision-and-principles.md` if wording changes |
| **Acceptance** | Verification standard met (suite, axe, perf, checklist, docs); golden E2E-01 and E2E-02 still pass with the new wizard and Studio; demo script updated to include sizing a sitting |

**Teach note:** Same as S61 — measure, walk the path, write it down.

---

## Phase 4 — Real content and technique (S69–S80)

Content becomes a first-class, validated asset; technique (example → attempt → feedback → fresh check → later recall) is built into every path; and the learner can bring any subject.

### S69 — Content as validated files

| Field | Value |
|---|---|
| **Title** | Move curricula to content files with a validating loader |
| **Commit** | `feat(content): curricula as validated markdown and yaml files` |
| **Files/areas** | `content/<domain>/<competency>.md` with YAML frontmatter (key, name, requires, effort ranges) and body sections: `## Reading`, `## Worked example`, `## Items` (typed items with id, prompt, choices/answer, explanation, misconception tag); `services/api/app/content/loader.py` parses and validates: unique ids, referenced keys exist, ≥ 3 items per competency, explanation present, no prerequisite cycles; `seed.py` reads the loader; `tests/test_content_validation.py`; CI runs the validator |
| **Acceptance** | Pytest: current seeded content round-trips into files with identical keys and versions; a fixture file missing an explanation fails validation with a line number; seed twice is still idempotent; all existing tests pass |

**Teach note:**  
**What:** Lessons become files a person can read, review, and diff.  
**How:** Frontmatter for structure, markdown for prose, a loader that refuses bad content.  
**Why:** "Real learning content" needs authoring and review to be cheap and checked. Python tuples in `seed.py` are neither.

### S70 — Item pools and unseen selection

| Field | Value |
|---|---|
| **Title** | Pick unseen items for independent checks and reviews |
| **Commit** | `feat(assess): item pools with unseen selection for checks and reviews` |
| **Files/areas** | `independent-check` chooses an item of the same competency the learner has **not** attempted (fallback: least-recently seen, labeled "repeat" in the payload and never eligible for `independently_demonstrated` if it was the item whose solution was revealed); review attempts rotate items the same way; `attempts` queries by `activity_version_id` |
| **Acceptance** | Pytest: after answering item A, the check serves B or C, never A; after all items are seen, the payload says `repeat: true` and a correct answer on the revealed item stays `practicing`; review after review serves a different item when one exists; Playwright quick-learn journey still passes |

**Teach note:**  
**What:** A fresh check is genuinely fresh.  
**How:** Track seen item versions per learner and select from what is left.  
**Why:** The honesty rule says the independent check is a different question. With one item per competency, that rule was only barely true.

### S71 — Explanations and misconception notes everywhere

| Field | Value |
|---|---|
| **Title** | Require explanations and misconception tags on every item; show them in feedback |
| **Commit** | `feat(content): explanations and misconception notes on all items` |
| **Files/areas** | Loader requires `explanation` and optional `misconceptions: {choice: note}`; Studio and Review feedback show the note matching the learner's wrong choice when present; summary lists "Watch out for" notes from the session's incorrect attempts |
| **Acceptance** | Validator fails on a missing explanation; Playwright: a specific wrong choice shows its misconception note; session summary lists it under Unresolved; axe and checklist pass |

**Teach note:**  
**What:** Wrong answers get specific help.  
**How:** Content carries a note per distractor; the UI shows the one that matches.  
**Why:** Feedback targeted at the mistake is the technique that moves learners; generic "incorrect" does not.

### S72 — Short-answer and numeric items

| Field | Value |
|---|---|
| **Title** | Add short-answer and numeric activity types with deterministic grading |
| **Commit** | `feat(assess): short answer and numeric items graded deterministically` |
| **Files/areas** | Activity types `short_answer` (normalized exact/alternates: trim, case, whitespace, optional punctuation) and `numeric` (value ± tolerance, fraction forms like `3/4`); grader module with unit tests; Studio and Review renderers; content loader validates keys per type; at least one item of each type in Python, math, and software |
| **Acceptance** | Pytest grading: `" B "`/`"b"` equal for short answer alternates; `0.75` and `3/4` both correct within tolerance; a free-text item with no key is rejected by the validator; Playwright: numeric item accepted from the keyboard at 390px; ownership and idempotency tests cover the new types |

**Teach note:**  
**What:** Recall instead of recognition.  
**How:** Normalization rules and tolerances, no model in the loop.  
**Why:** Multiple choice can be guessed. Typing the answer is closer to what "I can do this" means.

### S73 — Free recall (self-reported evidence)

| Field | Value |
|---|---|
| **Title** | Add a free-recall activity with self-rating recorded as self-report |
| **Commit** | `feat(assess): free recall activity recorded as self-reported evidence` |
| **Files/areas** | Activity type `free_recall`: prompt → learner writes from memory (textarea, no source visible) → reveals the reading → self-rates "Got it / Partly / Not yet"; evaluator `self_report`; evidence kind `self_report`; **facet ceiling `practicing`** (never `independently_demonstrated` or `retained`); reviews may be scheduled from a "Got it" but the review itself is another free recall with the same ceiling; Progress shows a distinct "Self-reported" chip |
| **Acceptance** | Pytest: a "Got it" self-rating writes evidence with `evaluator=self_report` and the facet is at most `practicing`; a due review on a free-recall item does not write `retained`; Playwright: the reading is hidden until the learner submits their recall; Progress shows the chip; checklist pass |

**Teach note:**  
**What:** The one technique that works for any subject — recall, then check yourself.  
**How:** New activity type, a self-report evaluator, and a hard ceiling in the evidence writer.  
**Why:** This is what makes the General route possible without lying about what a screen can verify.

### S74 — Deep Python path

| Field | Value |
|---|---|
| **Title** | Grow Python to a two-week-capable path with real depth |
| **Commit** | `feat(content): python fundamentals path with eight competencies` |
| **Files/areas** | `content/python/`: names, calls, conditionals, loops, lists, defining functions, strings, reading an error message; each with reading (150–300 words), worked example, ≥ 4 items mixing objective / short answer / numeric, explanations, misconception notes, effort ranges summing to roughly 6–8 hours at `effort_low`; edges form a DAG |
| **Acceptance** | Validator passes; planner test: 420 minutes with `understand` includes ≥ 6 competencies; 120 minutes includes names, calls, conditionals and defers the rest with plain reasons; a short content review checklist (`docs/design/content-review-checklist.md`) is filled for each file; Playwright quick-learn and math-windows still pass |

**Teach note:**  
**What:** A path a learner can actually spend two weeks on.  
**How:** Author files against the loader's rules; keep every item checkable on a screen (reading code, predicting output, naming errors).  
**Why:** Demo content must be deep enough to be real, while the core stays subject-agnostic.

### S75 — Deeper math and software

| Field | Value |
|---|---|
| **Title** | Grow math and software paths to four competencies each |
| **Commit** | `feat(content): deeper fractions and software practice paths` |
| **Files/areas** | `content/math/`: parts of a whole, add same denominator, equivalent fractions, compare fractions (numeric items with fraction forms); `content/software/`: read a failing test, name the mismatch, choose the smallest fix, describe a test for a bug; same quality bar as S74 |
| **Acceptance** | Validator passes; each domain plans four competencies at 240 minutes and defers with plain reasons at 30; math-windows E2E shows a numeric item; software E2E shows a fresh check from the pool |

**Teach note:**  
**What:** The two other seeded subjects earn the same depth.  
**How:** Same file format, same checks.  
**Why:** The point of the shared core is that a second subject is more files, not more code.

### S76 — The General route: learn anything

| Field | Value |
|---|---|
| **Title** | Accept any subject with a learner-supplied General route |
| **Commit** | `feat(goals): general route for any subject from the learner's own material` |
| **Files/areas** | Domain `general` (system) with per-goal competencies created from the learner's input: wizard step 1 becomes "What do you want to learn?" + subject chips (Python, Foundational math, Software practice, **Something else**); Something else asks for the topic and optional pasted notes (plain text/markdown, size-limited, sanitized) and 1–5 "things I want to be able to do" which become goal-scoped competencies; planner fits them by declared minutes per item; Studio activities: reading (their notes or the topic prompt), free recall, reflection; evidence is self-report only; Progress and Home say "Self-reported" and Help explains why; Library remains honest empty |
| **Acceptance** | Pytest: a "Spanish greetings" goal saves, proposes, and accepts with no seeded content; competencies are owned by the goal and invisible to other users (404); evidence never exceeds `practicing`; a 60-minute budget with five outcomes defers some with plain reasons; Playwright `general-route.spec.ts`: full journey to a scheduled free-recall review; validator rejects pasted content over the size limit; axe and checklist pass |

**Teach note:**  
**What:** The first screen finally says yes to anything.  
**How:** Goal-scoped competencies on the same graph, the free-recall technique from S73, and honest self-report labeling.  
**Why:** "Learn anything" is the vision. Honesty is preserved by what the ledger is allowed to write, not by refusing the subject.

### S77 — Placement diagnostic in the wizard

| Field | Value |
|---|---|
| **Title** | Offer a short placement and let the learner confirm skips |
| **Commit** | `feat(goals): placement diagnostic proposes skips the learner confirms` |
| **Files/areas** | Wizard step 4 (skippable): 3–5 items from the chosen subject via existing `POST /goals/{id}/diagnostic`; proposal marks competencies answered correctly as "You may already know this — skip?" with a checkbox per item, default unchecked; skipped competencies are recorded `skipped_by_learner` and shown as unassessed on Progress; no facet is written from the diagnostic |
| **Acceptance** | Pytest: diagnostic still writes no evidence; a confirmed skip removes the competency from the accepted plan and lists it as skipped/unassessed; unchecked leaves it in; Playwright `goal-wizard.spec.ts`: skip the diagnostic path and the confirm path both accept plans; checklist pass |

**Teach note:**  
**What:** Returning learners are not forced through basics, and nobody is told they "passed."  
**How:** The diagnostic API from S23 feeds a checkbox list; the learner decides.  
**Why:** Confidence is not proof; agency is explicit.

### S78 — Worked examples before attempts

| Field | Value |
|---|---|
| **Title** | Render worked examples as a step between reading and first attempt |
| **Commit** | `feat(studio): worked example step between reading and practice` |
| **Files/areas** | Content `## Worked example` becomes an activity of type `worked_example` inserted after the reading when present; Studio renders it with a "Now you try" primary; evidence: exposure only; planner counts its effort |
| **Acceptance** | Pytest: worked example writes no attempt and no facet above `exposed`; planner sums include it; Playwright: Python names shows reading → example → question; checklist pass |

**Teach note:**  
**What:** Show one, then do one.  
**How:** A new activity type with no grading.  
**Why:** Technique is part of content. Worked examples reduce floundering on the first attempt without inflating evidence.

### S79 — Content quality in CI

| Field | Value |
|---|---|
| **Title** | Enforce the content checklist and item validation in CI |
| **Commit** | `test(content): validate curricula and enforce the content checklist in ci` |
| **Files/areas** | CI job `content` runs the validator over `content/`; `content-review-checklist.md` fields (reading length, example present, ≥ 3 items, explanation, misconception notes, effort realistic, no answer leakage in prompt, plain language) become machine checks where possible and a required frontmatter `reviewed_by`/`reviewed_on` otherwise; a `docs/evaluations/content-audit.md` lists every competency and its check status |
| **Acceptance** | CI fails on an unreviewed or invalid file; audit lists every competency in Python, math, software as reviewed; no item prompt contains its own answer text (heuristic test) |

**Teach note:**  
**What:** Content gets the same discipline as code.  
**How:** Validation on every push, human review recorded in the file.  
**Why:** AI-drafted or hurried items are the fastest way to teach something wrong.

### S80 — Gate 4: real content and technique

| Field | Value |
|---|---|
| **Title** | Verify Phase 4 and update vision, UX, and architecture docs |
| **Commit** | `docs: phase 4 content and technique verified; general route in vision and architecture` |
| **Files/areas** | `04-implementation-status.md`, `docs/learning-log.md`, `00-vision-and-principles.md` (V1 wedge: any subject via General route + checked subjects), `01-product-and-ux.md` (wizard steps as built, activity types, self-report chip), `02-architecture.md` (content files, loader, activity types, evidence ceilings), `05-direction.md` |
| **Acceptance** | Verification standard met; golden scenarios E2E-01, E2E-02, E2E-05, E2E-06, E2E-08, E2E-12, E2E-16-spirit (Quick → longer budget keeps evidence), E2E-20 (General route) automated and green; perf re-baselined with the larger content set; demo script v2 includes a General-route goal |

---

## Phase 5 — Optional AI behind the scenes (S81–S86)

Everything here is behind a feature flag and a configured key. With no key, every screen behaves exactly as after S80. The model explains and drafts; the deterministic grader and the evidence writer stay the only writers.

### S81 — AI gateway module

| Field | Value |
|---|---|
| **Title** | Add a provider-agnostic AI gateway with typed outputs and a disabled state |
| **Commit** | `feat(ai): provider-agnostic gateway with typed outputs and disabled fallback` |
| **Files/areas** | `services/api/app/modules/ai_gateway/`: `Provider` protocol, one HTTP provider behind `AI_PROVIDER`/`AI_API_KEY`, versioned prompt files, pydantic output schemas, timeout/retry/cancel, per-user daily cap, audit row (model, prompt version, tokens; no raw private prompt retained), `is_enabled()`; `GET /api/v1/me` adds `ai_enabled`; `.env.example` documents the flag |
| **Acceptance** | Pytest with a fake provider: schema violations raise a typed error and the caller falls back; timeouts return `unavailable` within the limit; cap returns 429 in the envelope; with no key `is_enabled()` is false and no network call is attempted (socket-blocking test); mypy clean |

**Teach note:**  
**What:** One door for every model call.  
**How:** Protocol + one implementation + schemas + limits.  
**Why:** The design says AI proposes, the app validates. A gateway is where that rule is enforced once.

### S82 — Explain differently and generated hints

| Field | Value |
|---|---|
| **Title** | Offer "Explain this differently" and a generated hint with seeded fallback |
| **Commit** | `feat(studio): explain differently and generated hints behind the ai flag` |
| **Files/areas** | Studio secondary action "Explain this differently" (visible only when `ai_enabled`); hint route uses the model to produce a hint that must not contain the answer (validator: no choice letter, no answer string, length cap) else falls back to the seeded hint; both are recorded as assistance events exactly like the seeded hint; a small "AI" chip marks generated text; streaming optional, cancel supported |
| **Acceptance** | Pytest: a generated hint containing the answer text is rejected and the seeded hint served; assistance is recorded either way; with the flag off the button is absent; Playwright (fake provider): the chip appears and a later answer is marked assisted; E2E-08 (no key) still passes |

**Teach note:**  
**What:** A tutor that helps and is labeled.  
**How:** Validate every hint against the answer key before showing it.  
**Why:** Help is allowed; unlabeled help is not. The model never touches the evidence writer.

### S83 — Goal intake suggestion

| Field | Value |
|---|---|
| **Title** | Suggest a title, subject, and outcomes from the learner's free text |
| **Commit** | `feat(goals): ai goal normalizer suggests title subject and outcomes` |
| **Files/areas** | With the flag on, the wizard's first field calls `POST /goals/normalize` → suggested title, best matching seeded subject or General, 3–5 outcome statements for the General route; all editable; without the flag the learner types them as in S76 |
| **Acceptance** | Pytest with fake provider: suggestions validate against the schema and only reference real domain keys; nothing is saved until the learner submits; Playwright: suggestion appears, learner edits the title, saved goal uses the edited title; flag off shows the manual fields |

**Teach note:**  
**What:** Less typing to start.  
**How:** A schema-gated suggestion; the learner remains the author.  
**Why:** "Behind the scenes" means the model does the drudgery, not the deciding.

### S84 — Provisional outlines and recall prompts for General

| Field | Value |
|---|---|
| **Title** | Draft a provisional outline and recall prompts for General-route goals |
| **Commit** | `feat(general): provisional outline and recall prompts behind the ai flag` |
| **Files/areas** | With the flag on, a General goal may request an outline (ordered outcomes with short readings) and recall prompts; each item is marked `provisional` and `unreviewed`; used only for reading, free recall, and reflection (self-report ceiling); never for objective/short-answer grading; learner can delete or edit any item |
| **Acceptance** | Pytest: provisional items cannot carry an answer key (validator) and cannot be selected by the independent check; evidence from them stays ≤ `practicing`; content safety validator rejects instructions embedded in pasted notes (injection fixture); Playwright: a General goal gains an outline, learner deletes one item, plan updates via preview → Accept |

**Teach note:**  
**What:** For any subject, a starting structure appears — labeled as a draft.  
**How:** Provisional items are a separate class the grader cannot use.  
**Why:** This is how "learn anything" gets content without pretending the model can certify it.

### S85 — AI safety and failure tests

| Field | Value |
|---|---|
| **Title** | Test injection, timeouts, caps, and no-grading paths for AI features |
| **Commit** | `test(ai): injection timeout cap and no-grading coverage` |
| **Files/areas** | Fixtures for prompt injection in pasted notes and in model output; mid-stream timeout; daily cap; assertion that no code path from `ai_gateway` writes `competency_evidence`, `evaluations`, or `review_items` (import-graph test); E2E-10 and E2E-17 automated with the fake provider |
| **Acceptance** | All fixtures pass; import-graph test fails if a future change imports the evidence writer from the gateway; CI green with the flag on (fake provider) and off |

### S86 — Gate 5: optional AI

| Field | Value |
|---|---|
| **Title** | Verify Phase 5 and update the architecture and UX docs |
| **Commit** | `docs: phase 5 optional ai verified; gateway rules in architecture` |
| **Files/areas** | `04-implementation-status.md`, `docs/learning-log.md`, `02-architecture.md` (gateway, flags, validators, what the model may and may not do), `01-product-and-ux.md` (AI chip, explain differently, disabled state), `05-direction.md` |
| **Acceptance** | Verification standard met with the flag off **and** on (fake provider); perf budgets hold with the flag off (AI paths are excluded from the deterministic budget and reported separately) |

---

## Phase 6 — Account, trust, release (S87–S96)

What a stranger needs before we hand them a URL.

### S87 — Settings

| Field | Value |
|---|---|
| **Title** | Add Settings for name, timezone, reduced motion, larger text, and default session length |
| **Commit** | `feat(settings): preferences page wired to the profile api` |
| **Files/areas** | `/app/settings` (linked from More) on the kit; uses `PATCH /me/preferences`; adds `default_session_minutes` to the profile; `larger_text` applies a root class that scales the type ramp; `reduced_motion` forces the reduced-motion CSS path even when the OS does not |
| **Acceptance** | Pytest: new field validates (5–180); Playwright: change timezone and larger text, reload, both persist and the page is visibly larger; another user's profile unaffected; axe and checklist pass |

### S88 — Managed auth for production

| Field | Value |
|---|---|
| **Title** | Add a managed sign-in provider for production; dev token only in development |
| **Commit** | `feat(auth): managed provider sign-in for production with dev token gated` |
| **Files/areas** | One provider path (email magic link or OIDC via a managed service) issuing RS256 tokens verified by the existing `AUTH_JWKS_URL` path; web `/sign-in` renders the provider flow when `ENVIRONMENT=production`; `POST /api/v1/dev/token` returns 404 in production (already) and the web dev form is not rendered; session cookie flags `Secure`, `HttpOnly`, `SameSite=Lax`; logout revokes |
| **Acceptance** | Pytest: production config rejects HS256 dev tokens and accepts a JWKS-signed fixture; Playwright (dev) unchanged; a manual production-mode run against the provider sandbox is recorded in the status doc; no password field exists anywhere |

### S89 — Export my data

| Field | Value |
|---|---|
| **Title** | Let the learner download everything Dolphin holds about them |
| **Commit** | `feat(privacy): export my data as json` |
| **Files/areas** | `GET /api/v1/me/export` → JSON of profile, goals, budgets, plan versions, sessions, attempts, evaluations, evidence, reviews, General-route content; Settings → Privacy → Download my data |
| **Acceptance** | Pytest: export contains the learner's rows and none of another user's; large exports stream; Playwright: the download completes and parses; documented in `/privacy` |

### S90 — Delete my account

| Field | Value |
|---|---|
| **Title** | Delete account and data with confirmation and a stated retention window |
| **Commit** | `feat(privacy): delete account with confirmation and retention disclosure` |
| **Files/areas** | `DELETE /api/v1/me` requires typed confirmation; sets `users.deleted_at`, cascades or tombstones owned rows, invalidates sessions; a scheduled purge job (`make purge`) removes tombstoned rows after the stated window; `/privacy` states the window |
| **Acceptance** | Pytest: after delete every owned route returns 401/404, export is unavailable, and the purge removes rows; another user unaffected; Playwright: the confirmation flow and sign-out |

### S91 — Security headers, rate limits, error pages

| Field | Value |
|---|---|
| **Title** | Harden the edge: CSP, headers, rate limits, and honest error pages |
| **Commit** | `feat(security): csp headers rate limits and error pages` |
| **Files/areas** | Next middleware sets CSP (self + fonts), `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS in production; API rate limits on sign-in, attempts, and AI routes (envelope 429); web `error.tsx`/`not-found.tsx` on the kit; API never returns stack traces (existing) |
| **Acceptance** | Pytest: 429 envelope after the limit; a raised exception returns the envelope without a trace; Playwright: response headers present; a forced error renders the error page with Retry; `npm audit` and `pip-audit` clean or documented |

### S92 — Deployment

| Field | Value |
|---|---|
| **Title** | Containerize web and API; document a one-command deploy with migrations |
| **Commit** | `chore(deploy): dockerfiles compose and runbook with migrations on release` |
| **Files/areas** | `apps/web/Dockerfile` (standalone Next), `services/api/Dockerfile`, `infra/compose.prod.yml` (web, api, postgres, migrate-then-start), `infra/RUNBOOK.md` (env, secrets, backup, restore, rollback), health and readiness endpoints |
| **Acceptance** | `docker compose -f infra/compose.prod.yml up` on a clean machine serves the app over the configured host; migrations run before the API accepts traffic; the Prove Loop demo passes against the containers; image sizes recorded |

### S93 — Observability

| Field | Value |
|---|---|
| **Title** | Structured request logs, product events, and readiness |
| **Commit** | `feat(observability): structured logs product events and readiness` |
| **Files/areas** | JSON request logs with `request_id`, route, status, duration; product events from the design (goal_created, plan_accepted, session_started, activity_submitted, independent_check_completed, review_completed, …) with opaque ids only; `GET /ready` checks DB; a `docs/evaluations/funnel.md` explaining how to read the honest funnel |
| **Acceptance** | Pytest: events contain no raw answers or notes; logs redact tokens; `/ready` fails when the DB is down; perf budget unchanged |

### S94 — Golden scenarios end to end

| Field | Value |
|---|---|
| **Title** | Automate the applicable golden scenarios as one release suite |
| **Commit** | `test(e2e): golden release suite covering the applicable e2e scenarios` |
| **Files/areas** | `apps/web/e2e/release/*.spec.ts`: E2E-01, 02, 03 (same subject, larger budget replans wider and keeps versions), 05, 06, 07, 08, 09, 12, 14, 15 (keyboard-only journey), 16-spirit, 18 (accept retry idempotent), 20; tagged `@release`; runs in CI on `main` |
| **Acceptance** | All release specs green three runs in a row locally and once in CI; flake list empty |

### S95 — Release candidate review

| Field | Value |
|---|---|
| **Title** | Run the full verification standard and a manual design review on the candidate |
| **Commit** | `docs: v0.1 release candidate verification and design review record` |
| **Files/areas** | `docs/evaluations/v0.1-rc.md` with perf numbers per endpoint/page, axe results per route, checklist per screen with screenshots at 390px and 1280px, keyboard journey notes, known limitations |
| **Acceptance** | Verification standard met in production mode with the flag off and on; no P0 findings open; the demo can be completed by someone who has not seen the code, following `docs/prove-loop-demo.md` v2 |

### S96 — Ship v0.1

| Field | Value |
|---|---|
| **Title** | Tag v0.1.0 with release notes, updated docs, and the next-phase pointer |
| **Commit** | `release: v0.1.0 first ship` |
| **Files/areas** | `CHANGELOG.md`; `README.md` (what it does, how to run, limits); `docs/design/README.md` index; `04-implementation-status.md` (Phase 6 done; next = Phase 7 programming lab or Vault, decided after ship); `05-direction.md`; git tag `v0.1.0` |
| **Acceptance** | Tag exists on `main`; CI green on the tag; docs name what shipped and what did not (no Vault, no sandbox, no `applied`); the learning log has an entry for every step S51–S96 |

---

## After first ship (not in this plan)

Phase 7 — Programming lab (isolated runner; passing tests support an attempt; the model never awards the facet). Phase 8 — Knowledge Vault (private files, ownership before retrieval, cited spans, deletion races). Phase 9 — Transfer and `applied`. Then more subjects and activity types on the same core, deeper accessibility, and a review scheduler with real data. Decide the order after v0.1 feedback.

## Step index

| ID | Phase | Title |
|---|---|---|
| S51 | 2 | Add accessibility, performance-budget, and design-checklist harness |
| S52 | 2 | Add shared UI components and verified contrast pairs |
| S53 | 2 | Return display names and plain reasons from every learner-facing endpoint |
| S54 | 2 | Redesign Home around one next action, goal cards, reviews, and evidence chips |
| S55 | 2 | Make Learn the organized list of goals with continue, pause, and archive |
| S56 | 2 | Responsive app shell with bottom tabs on small screens; real landing page |
| S57 | 2 | Rebuild Session Studio layout: header, rendered markdown, action bar |
| S58 | 2 | Show inline feedback with an explanation, then offer the honest next step |
| S59 | 2 | Redesign the goal path; replan shows a preview and requires Accept |
| S60 | 2 | Redesign Progress as an evidence ledger grouped by goal |
| S61 | 2 | Gate 2: verify Phase 2 and update the design docs |
| S62 | 3 | Add minute presets and a spelled-out total to the wizard |
| S63 | 3 | Store priority as an enum and make the planner use it |
| S64 | 3 | Ask how long the learner has right now and size the session to it |
| S65 | 3 | Show a quiet remaining estimate; offer a stopping point at the target |
| S66 | 3 | Show minute ranges per lesson and minutes left on the goal path |
| S67 | 3 | Estimate review minutes and say what fits on Home |
| S68 | 3 | Gate 3: verify Phase 3 and update the design docs |
| S69 | 4 | Move curricula to content files with a validating loader |
| S70 | 4 | Pick unseen items for independent checks and reviews |
| S71 | 4 | Require explanations and misconception tags on every item; show them in feedback |
| S72 | 4 | Add short-answer and numeric activity types with deterministic grading |
| S73 | 4 | Add a free-recall activity with self-rating recorded as self-report |
| S74 | 4 | Grow Python to a two-week-capable path with real depth |
| S75 | 4 | Grow math and software paths to four competencies each |
| S76 | 4 | Accept any subject with a learner-supplied General route |
| S77 | 4 | Offer a short placement and let the learner confirm skips |
| S78 | 4 | Render worked examples as a step between reading and first attempt |
| S79 | 4 | Enforce the content checklist and item validation in CI |
| S80 | 4 | Gate 4: verify Phase 4 and update vision, UX, and architecture docs |
| S81 | 5 | Add a provider-agnostic AI gateway with typed outputs and a disabled state |
| S82 | 5 | Offer "Explain this differently" and a generated hint with seeded fallback |
| S83 | 5 | Suggest a title, subject, and outcomes from the learner's free text |
| S84 | 5 | Draft a provisional outline and recall prompts for General-route goals |
| S85 | 5 | Test injection, timeouts, caps, and no-grading paths for AI features |
| S86 | 5 | Gate 5: verify Phase 5 and update the architecture and UX docs |
| S87 | 6 | Add Settings for name, timezone, reduced motion, larger text, and default session length |
| S88 | 6 | Add a managed sign-in provider for production; dev token only in development |
| S89 | 6 | Let the learner download everything Dolphin holds about them |
| S90 | 6 | Delete account and data with confirmation and a stated retention window |
| S91 | 6 | Harden the edge: CSP, headers, rate limits, and honest error pages |
| S92 | 6 | Containerize web and API; document a one-command deploy with migrations |
| S93 | 6 | Structured request logs, product events, and readiness |
| S94 | 6 | Automate the applicable golden scenarios as one release suite |
| S95 | 6 | Run the full verification standard and a manual design review on the candidate |
| S96 | 6 | Tag v0.1.0 with release notes, updated docs, and the next-phase pointer |
