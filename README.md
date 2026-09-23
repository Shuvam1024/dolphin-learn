# Dolphin

**Learn anything. Fit the time you have. Prove you can do it.**

Dolphin is an adaptive learning platform for adults (18+): a Home hub, time-adaptive plans from real available minutes, Session Studio lessons, and an honest Evidence Ledger. V1 wedge: Python + foundational math on an accessible web client.

Design source of truth: [`docs/design/`](docs/design/)  
Build sequence: [`docs/design/03-build-plan.md`](docs/design/03-build-plan.md)  
Status: [`docs/implementation-status.md`](docs/implementation-status.md)  
Prove Loop demo: [`docs/prove-loop-demo.md`](docs/prove-loop-demo.md)

## Stack

| Layer | Choice |
|---|---|
| Web | Next.js (TypeScript) — `apps/web` |
| API | FastAPI (Python) — `services/api` |
| Database | PostgreSQL |
| Local infra | Docker Compose (Postgres only; app processes run on the host) |

AI / LLM API keys are **optional**. Seeded Prove Loop content must work without them.

## Layout

```text
dolphin-learn/
├── apps/web/           # Next.js client
├── services/api/       # FastAPI modular monolith
├── packages/contracts/ # Shared OpenAPI / DTO contracts
├── infra/              # Infra helpers
├── docs/               # Design SoT + build tracker
├── docker-compose.yml  # Local Postgres (S03)
├── .env.example        # Named placeholders only — no secrets
└── AGENTS.md           # Agent / contributor pointers
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

Exact package pins live in `services/api/requirements.txt`. AI keys stay optional.

## Environment variables

All names are listed in [`.env.example`](.env.example). Placeholders only — put real values in a local `.env` that git ignores.

| Area | Examples | Notes |
|---|---|---|
| Database | `DATABASE_URL`, `POSTGRES_*` | Compose defaults match `.env.example` |
| API | `API_HOST`, `API_PORT`, `CORS_ORIGINS` | Local defaults for FastAPI |
| Web | `NEXT_PUBLIC_API_BASE_URL` | Browser → API base |
| Auth | `AUTH_*` / OIDC placeholders | Managed auth (S10+) |
| AI (optional) | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. | Leave empty; seeded content must still work |

## Checks

From the repo root, after web `npm install` and `pip install -r services/api/requirements-dev.txt` inside `services/api/.venv`:

```bash
make web-lint web-type web-test
make api-lint api-type api-test
```

## Product locks (short)

- Adults **18+** until a child product is designed and reviewed.
- No Vault / RAG / code sandbox until Phase 1A Prove Loop is demonstrated.
- No fake `% mastered` or streak-as-learning guilt.
- Clear Depth visual identity (not generic indigo-purple AI chrome).

## License

To be decided. Repository is intended public under `shuvam1024/dolphin-learn`.
