# Dolphin

Adaptive learning platform (adults 18+). Design package is in `docs/`; application scaffold follows `docs/build-plan.md`.

## Layout

```text
dolphin-learn/
├── apps/web/           # Next.js client
├── services/api/       # FastAPI modular monolith
├── packages/contracts/ # Shared OpenAPI / DTO contracts
├── infra/              # Infra helpers
├── docs/               # Design SoT + build tracker
└── AGENTS.md           # Agent / contributor pointers
```

Install and run instructions land in S02; local Postgres via Compose in S03.
