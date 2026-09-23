# Dolphin Implementation Status

- **Last updated:** September 23, 2026
- **Milestone completed:** S01–S19 (Phase 0 foundation); S20–S40 Prove Loop (Phase 1A exit); S41–S42 delayed retention; S43–S46 physical study time (Phase 1C exit)
- **Verified working user journey:** Study minutes are active session time. Home and the goal path show usable minutes beside studied minutes. Replan uses what remains. A due review can wait 24 hours with Not now, without retention or a longer interval.
- **Implemented modules/features:** Layout; env template; Postgres; API health; Next.js shell; Clear Depth; error envelope; Alembic; checks; auth mapping; protected `/app`; learner preferences; adult acknowledgment; curriculum graph; goals and time budgets; plans, sessions, attempts, evidence, review tables, an honest session-finish summary, a review due queue with 1/3/7/14-day intervals, a Home snapshot of the next action, a Progress ledger of facets plus unassessed plan gaps, a goal path overview, replan that writes the next plan version, and a Studio control to move to the next activity or a different question; seeded Python and math lessons (reading + objective); `POST/GET /api/v1/goals`, `GET/PATCH /api/v1/goals/{id}` with one-off XOR weekly time budgets
- **Stubbed or unavailable features:** Library discloses that the Knowledge Vault is later and has no file control. Dev sign-in is email-only (no password store). Vault, RAG, the tutor, and the sandbox are not built. Phase 1D is done. Next is Phase 2 of `06-first-ship-plan.md` (foundations incl. the AI gateway, S51–S58). Computing seeds may lead demos; the product is for any subject.
- **Schema/API changes:** Alembic through `0009_goal_domain_key`; goals require `domain_key`; `GET /api/v1/domains`; `POST /api/v1/goals/{id}/replan` writes accepted plan version N+1 from remaining study minutes and demonstrated competencies and leaves older versions in place; `GET /api/v1/goals/{id}/overview` returns the path, deferred topics, usable and studied minutes, and the session to continue; `POST /api/v1/reviews/{id}/snooze` moves `due_at` by hours without retention
- **Tests run and exact results:**
  - S01: `tree` shows `apps/web`, `services/api`, `packages/contracts`, `infra`, `docs/`
  - S02: README lists Next.js + FastAPI + Postgres; `.env.example` placeholders; AI keys optional
  - S03: `docker compose up -d` → `dolphin-postgres` healthy; `psql` `SELECT 1` returned `ok` (exit 0) against `postgresql://dolphin:dolphin@127.0.0.1:5432/dolphin`
  - S04: `uvicorn app.main:app` then `curl http://127.0.0.1:8000/health` → `HTTP/1.1 200 OK` body `{"status":"ok"}` (fastapi 0.115.6, uvicorn 0.34.0)
  - S05: `npx tsc --noEmit` exit 0; `next dev` `GET /` → HTTP 200 and the page contains “Dolphin” (Next.js 15.5.26)
  - S06: `npx tsc --noEmit` exit 0; `GET /` HTTP 200; HTML classes load Syne, Manrope, and IBM Plex Mono; served CSS contains `#0B1F2A`, `#1FA7A0`, `#F4F8F9`, `#E8F1F3`, `#E6A817`, `#5A6B73`; no dark-mode color scheme
  - S07: TestClient `GET /health` 200; `GET /api/v1/version` 200 `{"api":"v1"}`; unknown route 404 envelope `code=not_found` with `X-Request-ID`; invalid body 422 envelope `code=validation_error` and a `details` list
  - S08: `alembic upgrade head` applied `0001_baseline`; `alembic current` → `0001_baseline (head)`; `check_connection()` returned `1` against `postgresql+psycopg://dolphin:dolphin@localhost:5432/dolphin` (Postgres 16)
  - S09: `make web-lint web-type web-test` exit 0 (eslint, tsc, vitest 1 passed); `make api-lint api-type api-test` exit 0 (ruff, mypy, pytest 3 passed)
  - S10: `alembic upgrade head` applied `0002_users`; `GET /api/v1/me` without a token → 401 `code=unauthorized`; `POST /api/v1/dev/token` then `GET /api/v1/me` → 200 with `auth_subject=dev|s10-learner@example.com` and one `users` row; repeat call keeps the same id; `ruff`, `mypy` clean; `pytest` 5 passed
  - S11: `tsc --noEmit` exit 0; vitest 2 passed; eslint clean; anonymous `GET /app` → 307 `/sign-in`; `POST /api/session` with email → 303 `/app` and HttpOnly cookie; `GET /app` with cookie → 200 containing the email and “Log out”; `POST /api/session/logout` clears the cookie; following `GET /app` → 307 `/sign-in`
  - S12: `alembic upgrade head` applied `0003_learner_profiles`; `GET /api/v1/me` profile defaults `timezone=UTC`, `locale=en`; `PATCH /api/v1/me/preferences` stores display name, `America/New_York`, `en-US`, and `reduced_motion`; a second user's body `user_id` → 422 and does not change the first timezone; invalid timezone → 422 `validation_error`; `pytest` 8 passed; ruff and mypy clean
  - S13: `alembic upgrade head` applied `0004_adult_acknowledgment`; new user `adult_acknowledged_at` is null; `POST /api/v1/me/adult-acknowledgment` sets a timestamp that stays the same on repeat and on `GET /me`; anonymous-to-signed-in `GET /app/goals/new` → 307 `/app` until acknowledgment; gate page shows the 18+ copy and privacy link; `GET /privacy` 200; after acknowledge, `GET /app/goals/new` 200 “Create a goal” and refresh of `/app` shows “You are in”; `tsc` exit 0; pytest 9 passed
  - S14: `alembic upgrade head` applied `0005_curriculum_graph`; pytest duplicate domain key, duplicate competency key, self-loop, bad edge type, and duplicate edge each raise `IntegrityError`; a valid `REQUIRES` edge commits; pytest 11 passed; ruff and mypy clean
  - S15: `alembic upgrade head` applied `0006_goals_time_budgets`; validator rejects negative one-off and weekly minutes and accepts 120-minute one-off plus 14×30 weekly; inserting a goal with no `user_id` raises `IntegrityError`; a negative `one_off_minutes` row raises `IntegrityError`; a valid 120-minute budget commits; pytest 14 passed; ruff and mypy clean
  - S16: `alembic upgrade head` applied `98b0fc485c6b`; models import; ownership foreign keys present on paths, sessions, attempts, evidence, state, and review items; attempts and review events have no `updated_at`; pytest 15 passed; ruff and mypy clean
  - S17: `python -m app.seed` twice; pytest confirms domains `python` and `math`, activity types `reading` and `objective`, and at least two answer keys; pytest 16 passed; ruff and mypy clean; no LLM key used
  - S18: `tsc` and eslint exit 0; signed-in acknowledged `GET /app` 200 contains Learn, Review, Library, Progress, More, and “Create a goal”; `/app/library` 200 “Coming later” and “Knowledge Vault” with no file input; `/app/learn`, `/app/review`, `/app/progress`, `/app/more` each 200
  - S19: pytest `test_phase0_smoke` health 200 and unauthenticated `GET /api/v1/me` 401; full pytest 18 passed; `npx playwright test` 1 passed — anonymous `/app` lands on `/sign-in`, email sign-in shows “Before you start”, adult acknowledgment shows “You are in”, primary nav, and “Create a goal”
  - S20: User A `POST /api/v1/goals` 201 with stripped title, `raw_request`, and `normalized_objective`; list and get return that goal; User B `GET` of A’s id → 404 `not_found` and B’s list omits it; empty title and empty request → 422 `validation_error` and no row; pytest 21 passed; ruff and mypy clean
  - S21: negative one-off minutes and a one-off body that also sets a weekly window → 422 `validation_error` and no goal row; 120-minute Quick Learn stores `one_off`; PATCH to 14 days × 30 min/day stores `weekly` and clears one-off minutes; GET returns the same budget; pytest 23 passed; ruff and mypy clean
  - S22: `tsc` and eslint clean; Playwright keyboard-only wizard: back keeps title and request, Save stores title “Names and values”, objective `Priority: Focus one topic`, and a 120-minute one-off budget (API list confirms); 390px width shows the weekly fields without horizontal overflow; phase 0 smoke still 1 passed
  - S23: `alembic upgrade head` applied `0007_diagnostic_runs`; start returns 3–8 items and no answer key; a one-answer submit then the rest both record attempts; skip returns `skipped`; a later start still works; `mastery_claimed` is false and no competency evidence row is written; another user gets 404; pytest 25 passed; ruff and mypy clean
  - S24: 15 usable minutes includes only `python.names` and defers `python.calls` with `insufficient_minutes`; 120 minutes includes both and `scope_conflict` is false; a 5-minute budget has `estimated_required_low > usable`, empty included, and a scope-conflict payload; `POST …/plan-proposals` does not insert `plan_versions`; pytest 27 passed; ruff and mypy clean; no LLM
  - S25: before accept, `GET …/plan` is 404; accept of a 15-minute Python goal returns version 1 with rationale listing `python.calls` and `insufficient_minutes`; a second GET returns the same version; pytest 28 passed; Playwright keyboard wizard accepts a 120-minute plan (`Deferred: none.`, version 1) and phase 0 smoke still passes
  - S26: start from an accepted 120-minute plan lands on the first activity; a progress event moves to the next; GET returns that same activity; the same `client_event_id` does not move it back and does not add a second event; pause survives GET; another user gets 404; pytest 29 passed; ruff and mypy clean
  - S27: session GET includes the reading body “binds the name”, mode `guided`, and no `answer_key`; Playwright opens `/app/learn/:sessionId`, shows the explanation and “No countdown”, Pause then reload still says Paused; phase 0 smoke passed; no AI key
  - S28: `alembic upgrade head` applied `0008_attempt_idempotency`; submit choice `b` returns `created` true and assistance `independent`; the same key with choice `a` returns the same attempt id and choice `b`; another user gets 404; one attempt row; Playwright records “Answer recorded: b” and reload keeps it; pytest 30 passed
  - S29: correct choice `b` with no help is `independent` / `correct` and eligible; challenge mode refuses the solution and does not reveal it; after an explicit solution the next attempt is `assisted` and not eligible; hint text does not reveal the letter; studio browser tests still passed; no LLM
  - S30: solution then a correct answer stays `practicing` and Progress does not show `independently_demonstrated`; `POST …/independent-check` moves to a different question with no revealed letter; an unassisted correct answer on that item sets `independently_demonstrated`; no evidence facet is `retained` or `applied`; pytest 33 passed; ruff and mypy clean
  - S31: pause before finish leaves status `paused` and summary null; `POST …/finish` returns stored independent attempts and the note that the summary is not retention; a second finish returns the same attempts and does not add a row; pause after finish is 422; Playwright shows “Session finished” with no celebration copy; pytest 34 passed; ruff, mypy, tsc, and eslint clean
  - S32: independent correct schedules `interval_days` 1 with `due_at` in the future; after that item is due, `GET /reviews/due` includes `python.names` and “Not retention” and no answer key; completing it sets interval 3; a second same-session success does not move the due time; assisted session success creates no review; challenge mode is 403; an assisted review stays at interval 1; another user gets 404; Playwright shows “Nothing is due” and “Not retention”; pytest 36 passed; ruff, mypy, tsc, and eslint clean
  - S33: empty Home is `create_goal`; after a 120-minute accept, the next action is `start_session` and the note includes “Usable minutes: 120”; with an open session and a due review, the next action is `review` and recent evidence is `independently_demonstrated` for `python.names`; another user sees no goals; the payload has no streak or mastered field; Playwright shows “You are in” then “Resume your session” and “Usable minutes: 120”, with no “% mastered”; phase 0 smoke passed; pytest 37 passed; ruff, mypy, tsc, and eslint clean
  - S34: empty progress has no facets and no unassessed keys; a 120-minute plan with no attempts lists `python.names` and `python.calls` as unassessed; assisted success sets `python.names` to `practicing` and leaves `python.calls` unassessed; the payload has no mastery percent; Playwright shows the facet, the unassessed gap, and not “% mastered”; pytest 38 passed; ruff, mypy, tsc, and eslint clean
  - S35: a 15-minute plan overview is version 1, orders activities from position 1, labels the first names activity `prereq`, defers `python.calls` with `insufficient_minutes`, and says why that activity is next; before a session, continue is `start`; after start, continue href is that session; another user gets 404; Playwright shows the deferred line and Continue opens the names reading; pytest 39 passed; ruff, mypy, tsc, and eslint clean
  - S36: after an independent names answer and a budget change to 15 minutes, `POST …/replan` returns version 2 with `insufficient_minutes` and “Already demonstrated: python.names”; version 1 remains; attempt count stays 1; `POST …/plan-proposals` does not create version 3; another user gets 404; Playwright shows “Plan version 2” and the deferred calls line; pytest 40 passed; ruff, mypy, tsc, and eslint clean
  - S37: Playwright signs in, saves a 120-minute Python goal, accepts a plan with `usable_minutes` 120 and allocated activity minutes ≤ 120, reads the names note, answers one question independently, checks a different question, and sees `python.names: independently_demonstrated` on Home and Progress with no “% mastered”; `OPENAI_API_KEY` was empty; ruff, mypy, tsc, and eslint clean
  - S38: Playwright saves Fractions as 30 minutes a day for 14 days; accepted plan `usable_minutes` is 420 and the rationale is not 20160; Studio shows “three parts out of four” and the seeded question “What is 1/4 + 2/4?”; `OPENAI_API_KEY` was empty
  - S39: User B receives 404 `not_found` on A’s goal, plan, overview, replan, accept, session, pause, attempt, advance, independent check, and finish; B’s Home, Progress, and review queue are empty; A still has one attempt and `independently_demonstrated`; a repeated idempotency key returns the original choice `b`; Playwright reload keeps the reading, then keeps “Answer recorded: b” with no second submit button; pytest 41 passed; ruff clean
  - S41: same-session correct stays `independently_demonstrated`; a review that is not yet due can extend the interval and stays that facet; a due independent review returns `retained` true and Progress shows `retained`; a due assisted review stays `independently_demonstrated`; pytest 44 passed; ruff and mypy clean
  - S42: after that due review, Home `recent_evidence` is `python.names` / `retained` and the payload has no mastery percent; Progress explains retained as a later due review and not a permanent promise; Playwright shows that sentence and not “% mastered”; ruff, mypy, tsc, and eslint clean
  - S46: snooze for 24 hours moves due_at, keeps interval_days, writes a snooze event, adds no retained evidence, removes the item from due; hours 0 is 422; another user is 404; Playwright clicks Not now and returns to “Nothing is due”
  - S45: after 30 studied minutes on a 420 budget, replan returns version 2 with usable 390, rationale names studied and remaining, the weekly budget row stays 30×14, evidence and attempts are unchanged; a 30-minute budget fully spent replans at 0 with a scope conflict
  - S44: a 14×30 accept keeps usable minutes 420; after a 30-minute finished session, overview and Home both show studied 30; payloads have no mastery percent and no deadline; Playwright shows “Usable minutes: 420. Studied: 0 minutes”; pytest 50 passed after S46
  - S40 exit, September 23, 2026: `cd services/api && .venv/bin/ruff check app tests` → `All checks passed!`; `.venv/bin/mypy app` → `Success: no issues found in 40 source files`; `.venv/bin/pytest --tb=no` → `41 passed, 1 warning in 2.41s`. `cd apps/web && npx playwright test e2e/phase0.spec.ts e2e/quick-learn.spec.ts e2e/math-windows.spec.ts e2e/refresh-resume.spec.ts --reporter=line` → `4 passed (10.4s)`. Demo script `docs/prove-loop-demo.md`. Next phase is 1B, not Vault
- **Known bugs/security/accessibility concerns:** None in the shell. Light theme only until a later contrast pass.
- **Build plan:** `docs/design/03-build-plan.md` (S01–S50, complete); `docs/design/06-first-ship-plan.md` (S51–S105)
- **Completed steps:** **S01–S50**
- **Next step:** **S51 — verification harness (axe, perf budget, design review checklist)**, Phase 2 of the first-ship plan

Design package SoT: `docs/design/`. This file is the live tracker; `docs/implementation-status.md` mirrors it.

---

## Milestone checklist

| Phase | Milestone | Status |
|---|---|---|
| 0 | Foundation (S01–S19) | Done (S01–S19) |
| 1A | Prove Loop (S20–S40) | Done (S20–S40) |
| 1B | Delayed retention (S41–S42) | Done (S42) |
| 1C | Physical study time (S43–S46) | Done (S46) |
| 1D | Honest demo content (S47–S50) | Done (S50) |
| 2 | Foundations incl. AI gateway (S51–S58) | Next |
| 3 | The learning session incl. tutor (S59–S70) | Planned |
| 4 | Organized in one place, adaptive to time (S71–S80) | Planned |
| 5 | Learn anything incl. AI drafting under review (S81–S90) | Planned |
| 6 | Learner model and adaptivity (S91–S95) | Planned |
| 7 | Account, trust, release → v0.1 (S96–S105) | Planned |
| 8+ | Programming lab, Vault, transfer, calibrated estimators | After first ship |

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
| **Quality** | `docs: judge each step by learning quality and usability` | Content, technique, time fit, and plain use are part of done, not a later polish pass |
| **S43** | `feat(sessions): measure active study minutes excluding pauses` | Pause gaps are excluded; finish freezes the total; Studio says the clock stops when you pause |
| **S44** | `feat(progress): show studied minutes beside the usable budget` | 14×30 stays 420 usable; studied minutes match the clock; no percent and no date |
| **S45** | `feat(plan): replan from minutes remaining after study` | 30 studied on 420 replans at 390; budget row stays; evidence untouched |
| **S46** | `feat(review): snooze a due item for a duration without retention` | Hours move due time only; interval and evidence stay; Not now is not memory |
| **S47** | `feat(goals): require an explicit domain for plans` | Domain stored on goal; GET /domains; cooking is not Python; wizard picks a subject |
| **S48** | `feat(seed): add python conditionals with real checks` | Conditionals lesson with reading + graded items; short plans defer it |
| **S49** | `feat(seed): add software practice mini curriculum` | software domain on shared ledger; plans only software competencies |
| **S50** | `feat(web): pick a domain in the goal wizard` | Subject required; software e2e is not Python; copy says more subjects come later |
