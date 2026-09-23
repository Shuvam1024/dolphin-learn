# AGENTS.md — Dolphin

Guidance for humans and coding agents working in this repository.

## Source of truth

- Design package index: `docs/design/README.md`
- Vision / UX / architecture: `docs/design/00`–`02`
- Sequential build steps: `docs/design/03-build-plan.md` (execute `S01` → `S40` in order)
- Progress tracker: `docs/design/04-implementation-status.md` (update after every completed step)
- Locks / constraints: `docs/design/project-context.md`
- Brand: `docs/design/brand.md`

## Working rules

1. One build-plan step per commit; do not skip ahead of the current phase exit.
2. Explain **what / how / why** from each step’s teach note while implementing.
3. Prefer the modular monolith layout under `apps/web`, `services/api`, `packages/contracts`, `infra`.
4. Do not start Vault/RAG/sandbox until Phase 1A (through S40) is demonstrated.
5. Seeded Prove Loop content must work without an LLM API key.
6. Server-side ownership checks on every nested resource id; no cross-user retrieval by similarity.
7. Never execute untrusted learner code in the API process.
8. Product name is **Dolphin** only — see `docs/design/brand.md` retired appendix; do not revive old working names in titles or active specs.

## Stack (target)

Next.js (web) + FastAPI (API) + Postgres — Clear Depth visual identity on the client.
