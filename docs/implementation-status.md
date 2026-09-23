# Dolphin Implementation Status

- **Last updated:** September 23, 2026
- **Milestone completed:** S01–S19 (Phase 0 foundation); S20–S28 of the Prove Loop
- **Verified working user journey:** Read an explanation or submit an objective answer; the same idempotency key does not create a second attempt
- **Implemented modules/features:** Layout; env template; Postgres; API health; Next.js shell; Clear Depth; error envelope; Alembic; checks; auth mapping; protected `/app`; learner preferences; adult acknowledgment; curriculum graph; goals and time budgets; plans, sessions, attempts, evidence, and review tables; seeded Python and math lessons (reading + objective); `POST/GET /api/v1/goals`, `GET/PATCH /api/v1/goals/{id}` with one-off XOR weekly time budgets
- **Stubbed or unavailable features:** Library discloses that the Knowledge Vault is later and has no file control. Dev sign-in is email-only (no password store). Attempts are stored but not graded yet
- **Schema/API changes:** Alembic through `0008_attempt_idempotency`; `POST /api/v1/sessions/{id}/attempts` stores an immutable answer snapshot keyed by `idempotency_key`
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
- **Known bugs/security/accessibility concerns:** None in the shell. Light theme only until a later contrast pass.
- **Build plan:** `docs/design/03-build-plan.md`
- **Completed steps:** **S01–S28**
- **Next step:** **S29 — Grade closed-form items and label assisted vs independent**

Design package SoT: `docs/design/`. This file is the live tracker; `docs/implementation-status.md` mirrors it.

---

## Milestone checklist

| Phase | Milestone | Status |
|---|---|---|
| 0 | Foundation (S01–S19) | Done (S01–S19) |
| 1A | Prove Loop (S20–S40) | In progress (S28) |
| Later | Vault / labs / community | Not started |

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
