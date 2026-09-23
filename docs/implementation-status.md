# Dolphin Implementation Status

- **Last updated:** September 23, 2026
- **Milestone completed:** S01–S11 (layout through protected web shell)
- **Verified working user journey:** Local sign-in → `/app` → log out (no goals yet)
- **Implemented modules/features:** Layout; README + `.env.example`; local Postgres; FastAPI `GET /health`; Next.js shell; Clear Depth tokens; `/api/v1` plus error envelope; SQLAlchemy 2 and Alembic; lint/type/test; `users.auth_subject`; sign-in page and protected `/app`
- **Stubbed or unavailable features:** No profile preferences, age-gate, or Prove Loop. Dev sign-in is email-only (no password store)
- **Schema/API changes:** `GET /api/v1/version`; error envelope; `GET /health` unversioned; Alembic `0001_baseline`, `0002_users` (`auth_subject` unique, email, id); `POST /api/v1/dev/token`, `GET /api/v1/me`
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
- **Known bugs/security/accessibility concerns:** None in the shell. Light theme only until a later contrast pass.
- **Build plan:** `docs/design/03-build-plan.md`
- **Completed steps:** **S01–S11**
- **Next step:** **S12 — Add profile preferences (`GET/PATCH /me`)**

Design package SoT: `docs/design/`. This file is the live tracker; `docs/implementation-status.md` mirrors it.

---

## Milestone checklist

| Phase | Milestone | Status |
|---|---|---|
| 0 | Foundation (S01–S19) | In progress (S01–S11 done) |
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
