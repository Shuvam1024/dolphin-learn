# Dolphin Implementation Status

- **Last updated:** September 23, 2026
- **Milestone completed:** S01–S10 (layout through managed auth subject mapping)
- **Verified working user journey:** None yet (branded placeholder home; API can resolve a dev token to a user)
- **Implemented modules/features:** Layout; README + `.env.example`; local Postgres; FastAPI `GET /health`; Next.js placeholder at `/`; Clear Depth tokens; `/api/v1` plus error envelope; SQLAlchemy 2 session and Alembic; ruff/mypy/pytest and ESLint/tsc/Vitest; `users.auth_subject` and bearer-token `GET /api/v1/me`
- **Stubbed or unavailable features:** No web sign-in yet; no domain schema or Prove Loop. Dev tokens are local-only (not a password store)
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
- **Known bugs/security/accessibility concerns:** None in the shell. Light theme only until a later contrast pass.
- **Build plan:** `docs/design/03-build-plan.md`
- **Completed steps:** **S01–S10**
- **Next step:** **S11 — Add sign-in page and protect `/app` routes**

Design package SoT: `docs/design/`. This file is the live tracker; `docs/implementation-status.md` mirrors it.

---

## Milestone checklist

| Phase | Milestone | Status |
|---|---|---|
| 0 | Foundation (S01–S19) | In progress (S01–S10 done) |
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
