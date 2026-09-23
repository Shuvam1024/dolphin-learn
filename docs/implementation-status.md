# Dolphin Implementation Status

- **Last updated:** September 23, 2026
- **Milestone completed:** S01–S18 (layout through honest navigation)
- **Verified working user journey:** Sign in → adult acknowledgment → Home prompts “Create a goal”; Learn, Review, Library, and Progress are honest empty states
- **Implemented modules/features:** Layout; env template; Postgres; API health; Next.js shell; Clear Depth; error envelope; Alembic; checks; auth mapping; protected `/app`; learner preferences; adult acknowledgment; curriculum graph; goals and time budgets; plans, sessions, attempts, evidence, and review tables; seeded Python and math lessons (reading + objective)
- **Stubbed or unavailable features:** Goal wizard is a placeholder after the gate. Library discloses that the Knowledge Vault is later and has no file control. Dev sign-in is email-only (no password store)
- **Schema/API changes:** Alembic through `98b0fc485c6b` (plans, sessions, append-only attempts, evidence, review) plus `0006_goals_time_budgets` and the curriculum graph; `POST /api/v1/me/adult-acknowledgment`
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
- **Known bugs/security/accessibility concerns:** None in the shell. Light theme only until a later contrast pass.
- **Build plan:** `docs/design/03-build-plan.md`
- **Completed steps:** **S01–S18**
- **Next step:** **S19 — Add API + browser smoke tests for auth shell**

Design package SoT: `docs/design/`. This file is the live tracker; `docs/implementation-status.md` mirrors it.

---

## Milestone checklist

| Phase | Milestone | Status |
|---|---|---|
| 0 | Foundation (S01–S19) | In progress (S01–S18 done) |
| 1A | Prove Loop (S20–S40) | Not started |
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
