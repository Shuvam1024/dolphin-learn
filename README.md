# Dolphin

**Learn anything. Fit the time you have. Prove you can do it.**

Dolphin is an adaptive learning platform for adults (18+): a Home hub, time-adaptive plans from real available minutes, Session Studio lessons, and an honest Evidence Ledger. **v0.1** ships checked subjects (Python, foundational math, software practice), a General route for any subject you name, an optional adaptive tutor, settings, export/delete, and a deployable container path.

Design source of truth: [`docs/design/`](docs/design/)  
Build sequence: [`docs/design/03-build-plan.md`](docs/design/03-build-plan.md) (S01–S50) then [`docs/design/06-first-ship-plan.md`](docs/design/06-first-ship-plan.md) (S51–S105)  
Status: [`docs/design/04-implementation-status.md`](docs/design/04-implementation-status.md)  
Release notes: [`CHANGELOG.md`](CHANGELOG.md) · RC record: [`docs/evaluations/v0.1-rc.md`](docs/evaluations/v0.1-rc.md)  
Prove Loop demo: [`docs/prove-loop-demo.md`](docs/prove-loop-demo.md)

## What v0.1 does

- Sign in (dev email locally; managed OIDC in production — no passwords)
- Create a goal that fits the minutes you have; accept a plan; sit and study
- Deterministic grading and evidence; tutor explains when enabled, never grades
- Review due items; snooze 3h / 24h / 72h without claiming retention
- Settings for comfort and tutor on/off; download or delete your data

## What v0.1 does not do

- Vault / RAG, code sandbox, `applied` facet, mastery percentages, or streaks
- Ship AI-drafted graded items without human review (`provisional` until then)

## Stack

| Layer | Choice |
|---|---|
| Web | Next.js (TypeScript) — `apps/web` |
| API | FastAPI (Python) — `services/api` |
| Database | PostgreSQL |
| Local infra | Docker Compose (Postgres only; app processes run on the host) |

Model gateway API keys are **optional**. Seeded Prove Loop content must work without them.

## Layout

```text
dolphin-learn/
├── apps/web/           # Next.js client
├── services/api/       # FastAPI modular monolith
├── packages/contracts/ # Shared OpenAPI / DTO contracts
├── infra/              # Infra helpers
├── docs/               # Design SoT (`docs/design/`) + pointers and demo script
├── docker-compose.yml  # Local Postgres (S03)
├── .env.example        # Named placeholders only — no secrets
└── AGENTS.md           # Maintainer pointers
```

## Local setup (Phase 0)

1. **Copy environment template** (never commit a real `.env`):

   ```bash
   cp .env.example .env
   ```

2. **Start Postgres** (Compose file at repo root):

   ```bash
   docker compose up -d
   ```

3. **API** (FastAPI health):

   ```bash
   cd services/api
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

   `GET http://localhost:8000/health` returns `{"status":"ok"}` and stays outside the version prefix.

   Versioned routes are `/api/v1/...`. Errors share one shape: `{ "error": { "code", "message", "details", "request_id" } }`.

4. **Web** (Next.js shell):

   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

   Or from the repo root: `npm run dev:web`. The public placeholder is at `http://localhost:3000`. `/app` redirects to `/sign-in` until you submit an email. Log out from the shell. The API must be running so sign-in can mint a dev token.

   Phase 0 smoke (API health plus a Chromium sign-in): `make smoke` from the repo root after `npx playwright install chromium` inside `apps/web`. Postgres and the API virtualenv must already be available.

5. **Migrations** (from `services/api`, with the virtualenv active):

   ```bash
   alembic upgrade head
   ```

   `DATABASE_URL` in `.env` is what Alembic uses. The chain includes `users`, keyed by the managed auth subject (`auth_subject`). Local development can mint a bearer token with `POST /api/v1/dev/token` (`{"email":"you@example.com"}`) and call `GET /api/v1/me`. That path is off when `ENVIRONMENT=production` (use `AUTH_JWKS_URL` instead). There is no password store.

Exact package pins live in `services/api/requirements.txt`. Model gateway keys stay optional.

## Environment variables

All names are listed in [`.env.example`](.env.example). Placeholders only — put real values in a local `.env` that git ignores.

| Area | Examples | Notes |
|---|---|---|
| Database | `DATABASE_URL`, `POSTGRES_*` | Compose defaults match `.env.example` |
| API | `API_HOST`, `API_PORT`, `CORS_ORIGINS` | Local defaults for FastAPI |
| Web | `NEXT_PUBLIC_API_BASE_URL` | Browser → API base |
| Auth | `AUTH_*` / OIDC placeholders | Managed auth (S10+) |
| Model gateway (optional) | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. | Leave empty; seeded content must still work |

## Checks

From the repo root, after web `npm install` and `pip install -r services/api/requirements-dev.txt` inside `services/api/.venv`:

```bash
make web-lint web-type web-test
make api-lint api-type api-test
make release-suite   # golden e2e, AI off then fake (API must be restartable on :8000)
```

Production-style bring-up: see [`infra/RUNBOOK.md`](infra/RUNBOOK.md) and `infra/compose.prod.yml`.

## Product locks (short)

- Adults **18+** until a child product is designed and reviewed.
- No Vault / RAG / code sandbox until Phase 1A Prove Loop is demonstrated.
- No fake `% mastered` or streak-as-learning guilt.
- Clear Depth visual identity (not generic indigo-purple chrome).

## License

No `LICENSE` file yet. SPDX / OSI terms are **not chosen**. Treat the repository as source-available until a license is added. Intended public location: `shuvam1024/dolphin-learn`.
