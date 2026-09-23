# Dolphin

**Learn anything. Fit the time you have. Prove you can do it.**

Dolphin is an adaptive learning platform for adults (18+): a Home hub, time-adaptive plans from real available minutes, Session Studio lessons, and an honest Evidence Ledger. V1 wedge: Python + foundational math on an accessible web client.

Design source of truth: [`docs/design/`](docs/design/)  
Build sequence: [`docs/design/03-build-plan.md`](docs/design/03-build-plan.md)  
Status: [`docs/implementation-status.md`](docs/implementation-status.md)

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

3. **API** (after S04 — FastAPI health):

   ```bash
   cd services/api
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt   # added in S04
   uvicorn app.main:app --reload --port 8000
   ```

4. **Web** (after S05 — Next.js shell):

   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

Exact package pins and migrate commands land in later build-plan steps. Until then, this README is the truthful install story: stack, env copy, optional AI keys.

## Environment variables

All names are listed in [`.env.example`](.env.example). Placeholders only — put real values in a local `.env` that git ignores.

| Area | Examples | Notes |
|---|---|---|
| Database | `DATABASE_URL`, `POSTGRES_*` | Compose defaults match `.env.example` |
| API | `API_HOST`, `API_PORT`, `CORS_ORIGINS` | Local defaults for FastAPI |
| Web | `NEXT_PUBLIC_API_BASE_URL` | Browser → API base |
| Auth | `AUTH_*` / OIDC placeholders | Managed auth (S10+) |
| AI (optional) | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. | Leave empty; seeded content must still work |

## Product locks (short)

- Adults **18+** until a child product is designed and reviewed.
- No Vault / RAG / code sandbox until Phase 1A Prove Loop is demonstrated.
- No fake `% mastered` or streak-as-learning guilt.
- Clear Depth visual identity (not generic indigo-purple AI chrome).

## License

To be decided. Repository is intended public under `shuvam1024/dolphin-learn`.
