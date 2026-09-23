# AGENTS.md — Dolphin

Guidance for humans and coding agents working in this repository.

## Source of truth

- Product + architecture: `docs/dolphin-master-design.md`
- Sequential build steps: `docs/build-plan.md` (execute `S01` → `S40` in order)
- Progress tracker: `docs/implementation-status.md` (update after every completed step)
- Locks / constraints: `docs/project-context.md`
- Brand: `docs/brand-shortlist.md`

## Working rules

1. One build-plan step per commit; do not skip ahead of the current phase exit.
2. Explain **what / how / why** from each step’s teach note while implementing.
3. Prefer the modular monolith layout under `apps/web`, `services/api`, `packages/contracts`, `infra`.
4. Do not start Vault/RAG/sandbox until Phase 1A (through S40) is demonstrated.
5. Seeded Prove Loop content must work without an LLM API key.
6. Server-side ownership checks on every nested resource id; no cross-user retrieval by similarity.
7. Never execute untrusted learner code in the API process.

## Stack (target)

Next.js (web) + FastAPI (API) + Postgres — Clear Depth visual identity on the client.
