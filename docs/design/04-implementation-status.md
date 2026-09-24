# Dolphin Implementation Status

- **Last updated:** September 24, 2026
- **Milestone completed:** S01–S72; Home v2
- **Schema/API changes:** Alembic through `0014_goal_priority`
- **Tests run and exact results (S72):**
  - `pytest -q` → 117 passed, 6 skipped (`test_home_v2`)
- **Tests run and exact results (S71):**
  - `alembic upgrade head` → `0014_goal_priority`
  - `pytest -q` → 116 passed, 6 skipped (`test_priority_planner`)
- **Tests run and exact results (S70 Gate 3):**
  - `AI_PROVIDER=` pytest → 112 passed, 6 skipped
  - `AI_PROVIDER=fake` pytest → 112 passed, 6 skipped
  - `make ai-eval` → green; `docs/evaluations/ai-eval-2026-09-24.md`
  - Playwright gate (quick-learn, math-windows, studio-v2, review, tutor, refresh-resume, free-recall, session-sizing) → 13 passed, 1 skipped
  - Docs: `01-product-and-ux`, `02-architecture`, `05-direction`, `prove-loop-demo` updated for Studio v2 / tutor / sizing / summary
- **Tests run and exact results (S69):**
  - `make ai-eval` → hint/explain/misconception/recall 20+ cases each, all pass; wrote `docs/evaluations/ai-eval-2026-09-24.md`
  - `pytest -q` → 112 passed, 6 skipped (`tests/ai_eval`)
- **Tests run and exact results (S68):**
  - `pytest -q` → 109 passed, 6 skipped (`test_summary_v2`)
- **Tests run and exact results (S67):**
  - `pytest -q` → 107 passed, 6 skipped (`test_stop_point`)
- **Tests run and exact results (S66):**
  - `alembic upgrade head` → `0013_sessions_target_minutes`
  - `pytest -q` → 106 passed, 6 skipped (`test_session_sizing`)
- **Tests run and exact results (S65):**
  - `pytest -q` → 104 passed, 6 skipped (`test_free_recall_ceiling`)
  - content validate ok
- **Tests run and exact results (S64):**
  - `alembic upgrade head` → `0012_evaluation_feedback_json`
  - `pytest -q` → 102 passed, 6 skipped (`test_grading_types`, `test_ai_misconception`)
  - content validate ok (numeric + short_answer seeded)
- **Tests run and exact results (S63):**
  - `pytest -q` → 98 passed, 6 skipped (`test_tutor.py`: leak→seeded, AI hint, explain assistance, AI-off 404)
  - ruff clean on changed modules
- **Tests run and exact results (S62):**
  - `pytest -q` → 93 passed, 6 skipped (`test_item_pools.py`: A→B/C never A, exhausted marks repeat, provisional excluded, reviews rotate, ownership 404; revealed item stays practicing)
  - ruff clean on changed modules
- **Tests run and exact results (S61):**
  - `pytest -q` → 88 passed, 6 skipped (`test_worked_example.py`)
  - `python -m app.content.validate` → content ok
  - playwright smoke 25 passed (reading → Now you try → question)
- **Tests run and exact results (S60):**
  - `pytest -q` → 84 passed, 6 skipped (`test_feedback_view.py`: wrong-choice note, assisted→fresh_check, watch_out_for summary)
  - `python -m app.content.validate` → content ok (objective misconception required)
  - `e2e/studio-v2.spec.ts` extended: wrong note + Try a fresh question after solution; no celebration copy
  - ruff clean
- **Tests run and exact results (S59):**
  - `tsc` / eslint clean; vitest 7 passed
  - `playwright` smoke 23 passed (incl. `e2e/studio-v2.spec.ts`: markdown `<code>`, one primary, Next absent before answer, pause survives reload, 390px action bar, tutor absent with AI off, axe zero on Studio)
  - `pytest -q` → 81 passed, 6 skipped
- **Tests run and exact results (S58 Gate 2):**
  - `AI_PROVIDER=` pytest → 81 passed, 6 skipped; ruff/mypy clean; `python -m app.content.validate` → content ok
  - `AI_PROVIDER=fake` pytest → 81 passed, 6 skipped
  - web: tsc/eslint clean; vitest 7 passed; playwright smoke 22 passed
  - `make a11y` → 1 passed; `e2e/a11y-baseline.json` 13 serious/critical by route (contrast)
  - `make perf` → API 6 passed (p95 home 62.5ms, progress 6.2ms, reviews/due 45.4ms, overview 33.8ms, session 16.7ms, plan-proposals 9.1ms; budget 250ms); page budgets 1 passed (LCP under 2500ms)
  - contracts: StudioActions/Tutor/State present in `packages/contracts`
- **Tests run and exact results (S57):**
  - `pytest -q` → 81 passed, 6 skipped (incl. studio_view action table + ownership)
  - `ruff` / `mypy` clean; contracts include StudioActions/Tutor/State
- **Tests run and exact results (S56):**
  - `alembic upgrade head` → `0011_ai_calls`
  - `pytest -q` → 73 passed, 6 skipped (AI gateway + import graph)
  - `AI_PROVIDER=fake` suite green; ruff/mypy clean
- **Tests run and exact results (S55):**
  - `python -m app.content.validate` → content ok
  - `pytest -q` → 67 passed, 6 skipped (incl. content loader rule fixtures)
  - `ruff` / `mypy` clean; CI job `content` added
- **Tests run and exact results (S54):**
  - `alembic upgrade head` → `0010_activity_content_fields`
  - `pytest -q` → 56 passed, 6 skipped (incl. `test_activity_types_schema.py`)
  - `ruff` / `mypy` clean
- **Tests run and exact results (S53):**
  - `pytest -q` → 54 passed, 6 skipped
  - `playwright test e2e/no-raw-keys.spec.ts` (+ progress/path/wizard/replan/quick-learn/home/domain-picker) → green
  - `ruff` / `mypy` / `tsc` clean
- **Tests run and exact results (S52):**
  - vitest 7 passed (ui-kit + contrast); `e2e/sign-in-a11y.spec.ts` 1 passed (zero serious/critical); tsc/eslint clean; pytest 53 passed + 6 skipped
- **Tests run and exact results (S51):**
  - `DOLPHIN_PERF=1 pytest tests/perf -s` → 6 passed; p95 home 55.8ms, progress 5.6ms, reviews/due 42.0ms, overview 24.8ms, session 8.8ms, plan-proposals 8.2ms (budget 250ms)
  - `pytest -q` (AI off) → 53 passed, 6 skipped (perf without flag)
  - `playwright test e2e/a11y.spec.ts` → 1 passed; wrote `e2e/a11y-baseline.json` with 13 serious/critical (mostly color-contrast)
  - `playwright test -c playwright.perf.config.ts` → 1 passed; sample TTFB/DCL/LCP well under 800/1500/2500ms
  - `ruff` / `mypy` / `tsc` / `vitest` clean
- **Known bugs/security/accessibility concerns:** Axe baseline lists remaining contrast findings on older screens until later kit migration.
- **Build plan:** `docs/design/06-first-ship-plan.md` (S51–S105)
- **Completed steps:** **S01–S72**
- **Next step:** **S73 — Learn: every goal, organized**

Design package SoT: `docs/design/`. This file is the only live tracker. `docs/implementation-status.md` is a pointer here. Teach notes from S58 onward go in `docs/learning-log.md`.

---

## Milestone checklist

| Phase | Milestone | Status |
|---|---|---|
| 0 | Foundation (S01–S19) | Done |
| 1A | Prove Loop (S20–S40) | Done |
| 1B | Delayed retention (S41–S42) | Done |
| 1C | Physical study time (S43–S46) | Done |
| 1D | Honest demo content (S47–S50) | Done |
| 2 | Foundations (S51–S58) | Done |
| 3 | The learning session (S59–S70) | Done (Gate 3) |
| 4 | Organized / adaptive (S71–S80) | In progress (next: S73) |
| Later | Phases 4–7 per first-ship plan | Later |

---

## Step log

| Step | Commit | Acceptance |
|---|---|---|
| **S01** | `chore: scaffold dolphin monorepo layout` | Layout present |
| **S02** | `docs: add README and env example for local setup` | README + env template |
| **S03** | `chore: add docker-compose postgres for local infra` | Compose healthy + psql ping |
| **S04** | `feat(api): add fastapi app with health check` | `GET /health` → 200 JSON |
| **S05** | `feat(web): scaffold next.js typescript app shell` | `tsc` clean; placeholder HTTP 200 |
| **S06** | `feat(web): add clear depth tokens and brand fonts` | Tokens + Syne/Manrope/Plex; light theme |
| **S07** | `feat(api): standardize v1 prefix and error envelope` | Unknown route and validation errors use the envelope |
| **S08** | `feat(api): bootstrap sqlalchemy and alembic` | `alembic upgrade head`; session `SELECT 1` |
| **S09** | `chore: add lint typecheck and test runners` | `make` web + API lint/type/test exit 0 |
| **S10** | `feat(api): integrate managed auth and user subject mapping` | Valid test token resolves one user; missing token → 401 |
| **S11** | `feat(web): add sign-in and protect app shell routes` | Anonymous `/app` redirects; sign-in loads `/app`; logout clears the session |
| **S12** | `feat(identity): add learner profile and preferences endpoints` | Owner can read/update prefs; another user's id cannot be patched |
| **S13** | `feat(web): add adult age-gate and privacy notice` | Goal page blocked until acknowledgment; acknowledgment survives refresh |
| **S14** | `feat(db): migrate domains competencies and edges` | Unique keys; self-loop and bad edge type fail |
| **S15** | `feat(db): migrate goals and time budgets` | Goal requires user; negative minutes rejected |
| **S16** | `feat(db): migrate plans sessions attempts evidence review` | Upgrade head; models import; ownership FKs present |
| **S17** | `feat(seed): add python and math mini curricula` | Python and math paths; reading and objective items |
| **S18** | `feat(web): add p0 nav shell with honest empty states` | Four primary nav items; Library has no upload; Home asks for a goal |
| **S19** | `test: add phase 0 auth and health smoke tests` | Health 200; anonymous `/app` blocked; signed-in shell loads |
| **S20** | `feat(goals): add create list and get goal endpoints` | Owner creates, lists, and reads a goal; another user gets 404; empty title or request is 422 |
| **S21** | `feat(goals): validate and store time budgets` | Negative minutes and double-counted modes rejected; 120-minute and 14×30 budgets stored |
| **S22** | `feat(web): add accessible goal and availability wizard` | Keyboard-only save persists goal and budget; back keeps fields; phone width usable |
| **S23** | `feat(goals): add optional diagnostic start and attempts` | Skip or answer 3–8 items; incomplete sample can be continued; no mastery claim |
| **S24** | `feat(plan): add deterministic feasibility plan proposal` | 15- and 120-minute Python budgets differ; over-budget returns a scope conflict; no plan row yet |
| **S25** | `feat(plan): add plan preview and explicit accept` | Preview is not active; accept creates version 1; refresh returns it; rationale lists deferred items |
| **S26** | `feat(sessions): create and resume persisted sessions` | Start from an accepted plan; refresh keeps progress; duplicate client event id does not double-apply |
| **S27** | `feat(studio): render session studio reading activity` | Seeded explanation shows; pause persists; no countdown; no AI |
| **S28** | `feat(studio): add question activity and attempt submit` | Immutable attempt; same idempotency key returns the same result; other user denied |
| **S29** | `feat(assess): deterministic grading and assistance labels` | Unassisted correct is eligible; after show-solution the next attempt is assisted |
| **S30** | `feat(assess): independent check and evidence ledger updates` | Assisted success is not independent demonstration; an unseen item can be; Progress shows facets |
| **S31** | `feat(sessions): add finish endpoint and summary ui` | Finish is idempotent; summary matches stored attempts; pause does not finish |
| **S32** | `feat(review): due queue and review attempt flow` | Independent success schedules a future due; due list shows a reason; assisted review does not extend the interval |
| **S33** | `feat(home): next action goals reviews and evidence snapshot` | Home shows the real next session or review; empty state still asks for a goal; no streak counter |
| **S34** | `feat(progress): evidence ledger progress view` | Facets match stored evidence; unassessed gaps stay visible; no global mastery percent |
| **S35** | `feat(goals): path overview with feasibility and sessions` | Accepted plan renders; deferred competencies stay visible; continue opens the right session |
| **S36** | `feat(plan): add replan endpoint creating new plan version` | Budget edit then replan writes version N+1; older versions and attempts stay; proposals still do not write a version |
| **S37** | `test(e2e): cover 120-minute python quick learn prove loop` | Browser journey accepts a plan whose activities fit in 120 minutes, then shows independent evidence on Home and Progress |
| **S38** | `test(e2e): cover two-week math thirty-minute days` | Usable minutes are 14×30, not 14×24h; the seeded fraction question appears in Studio |
| **S39** | `test: add ownership isolation and session refresh coverage` | Another user gets 404; refresh keeps the lesson; the same idempotency key does not add an attempt |
| **S40** | `docs: record phase 1a prove loop demo and status` | Demo script plus exact Phase 1A test results; next phase is 1B, not Vault |
| **S41** | `feat(assess): award retained only after a due review` | Due independent review sets retained; same-session, early, and assisted reviews do not |
| **S42** | `feat(progress): show retained facet from delayed review` | Home and Progress name retained; neither shows a mastery percent |
| **Plan** | `docs: plan physical study time as phase 1c` | S43–S46 measure active minutes, show them beside the budget, replan the remainder, snooze by hours |
| **Subjects** | `docs: prioritize computing subjects first` | Early demos may use computing seeds; not a required CS→SE→ML learner path |
| **Path** | `docs: keep the core subject-agnostic on the way to any field` | The clock, ledger, and graph stay shared for any subject |
| **Focus** | `docs: treat computing as demo focus not a learner path` | Product stays for anything; CS/SE/ML are build priority for demos only |
| **1D plan** | `docs: plan phase 1d honest demo content on shared core` | S47–S50: explicit domain, deeper Python check, software domain, wizard picker |
| **Quality** | `docs: judge each step by learning quality and usability` | Content, technique, time fit, and plain use are part of done, not a later polish pass |
| **S43** | `feat(sessions): measure active study minutes excluding pauses` | Pause gaps are excluded; finish freezes the total; Studio says the clock stops when you pause |
| **S44** | `feat(progress): show studied minutes beside the usable budget` | 14×30 stays 420 usable; studied minutes match the clock; no percent and no date |
| **S45** | `feat(plan): replan from minutes remaining after study` | 30 studied on 420 replans at 390; budget row stays; evidence untouched |
| **S46** | `feat(review): snooze a due item for a duration without retention` | Hours move due time only; interval and evidence stay; Not now is not memory |
| **S47** | `feat(goals): require an explicit domain for plans` | Domain stored on goal; GET /domains; cooking is not Python; wizard picks a subject |
| **S48** | `feat(seed): add python conditionals with real checks` | Conditionals lesson with reading + graded items; short plans defer it |
| **S49** | `feat(seed): add software practice mini curriculum` | software domain on shared ledger; plans only software competencies |
| **S50** | `feat(web): pick a domain in the goal wizard` | Subject required; software e2e is not Python; copy says more subjects come later |
| **S51** | `test: add axe, perf budget, and design review checklist harness` | Axe baseline, API/page budgets, checklist, Makefile a11y/perf/check, CI perf-a11y |
| **S52** | `feat(web): add clear depth ui kit with verified contrast` | Kit primitives; contrast tests; sign-in and gate migrated; axe zero on both |
| **S53** | `feat(api): copy module with competency names and plain reasons in payloads` | Names and plain reasons on payloads; web shows labels; no-raw-keys baseline green |
| **S54** | `feat(db): activity item ids, explanations, misconceptions, typed payloads, provisional flag` | Seven activity types; item_id; payload; provisional/source/reviewed_at; downgrade ok |
| **S55** | `feat(content): curricula as validated markdown and yaml with a loader` | content/ files; loader+rules; seed from files; CI content job |
| **S56** | `feat(ai): provider-agnostic gateway with typed outputs, limits, audit, and fake provider` | Gateway+FakeProvider; ai_calls; ai_enabled on /me; CI ai-fake |
| **S57** | `feat(sessions): studio payload with position, estimate, state, actions, and tutor slots` | studio_view actions; explanation hidden pre-attempt; contracts |
| **S58** | `docs: phase 2 foundations verified; content model, ai gateway, and studio contract in architecture` | Gate 2 green; architecture + brand updated |
| **S59** | `feat(studio): studio v2 renderer for every activity type with tutor panel` | StudioHeader/Body/AnswerInput/FeedbackNotice/TutorPanel/ActionBar; studio-v2 e2e green |
| **S60** | `feat(studio): feedback with explanation and the note for your mistake` | FeedbackNotice; watch_out_for summary; misconception rule |
| **S61** | `feat(content): worked example activity between reading and practice` | ## Worked example → activity; Now you try; warning rule |
| **S62** | `feat(assess): unseen item selection; provisional items never graded` | pick_unseen; provisional excluded; repeat flag; reviews rotate |
| **S63** | `feat(tutor): explain differently and validated generated hints with seeded fallback` | explain route; hint validator; seeded fallback; panel AI chip |
| **S64** | `feat(assess): short answer and numeric grading; ai misconception note for typed mistakes` | typed graders; feedback_json; AI note cannot change outcome |
| **S65** | `feat(assess): free recall with self-rating capped at practicing` | self-rate; practicing ceiling; recall_compare advisory |
| **S66** | `feat(sessions): target minutes per sitting from the learner` | SittingChooser; target_minutes; remaining sized to target |
| **S67** | `feat(studio): remaining estimate and good stopping point without a countdown` | stop_point; Keep going; no countdown copy |
| **S68** | `feat(sessions): summary v2 with what you showed, what to watch, and what is next` | showed/practiced/self_reported; next_step; no celebration |
| **S69** | `test(ai): tutor prompt evaluation fixtures and regression suite` | 20+ cases/prompt; make ai-eval; recorded report |
| **S70** | `docs: phase 3 learning session verified; studio, tutor, and activity types in ux spec` | Gate 3; UX + architecture + demo updated |
| **S71** | `feat(plan): priority enum shapes breadth, depth, and review reserve` | understand/apply/make_it_stick; 0014; rationale labels |
| **S72** | `feat(home): home v2 with one next action, goal cards, reviews, and evidence chips` | next_action shape; cards; due_reviews object; no Log out |
