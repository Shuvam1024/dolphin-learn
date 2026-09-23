# AGENTS.md — Dolphin

Guidance for maintainers working in this repository.

## Source of truth

- Design package index: `docs/design/README.md`
- Vision / UX / architecture: `docs/design/00`–`02`
- Sequential build steps: `docs/design/03-build-plan.md` (`S01`–`S50`, complete) then `docs/design/06-first-ship-plan.md` (`S51`–`S96`, in order, one phase gate at a time)
- Product judgment and final vision: `docs/design/05-direction.md`
- Progress tracker: `docs/design/04-implementation-status.md` (update after every completed step)
- Locks / constraints: `docs/design/project-context.md`
- Brand: `docs/design/brand.md`

## Working rules

1. One build-plan step per commit; do not skip ahead of the current phase exit.
2. Explain **what / how / why** from each step’s teach note while implementing.
3. Prefer the modular monolith layout under `apps/web`, `services/api`, `packages/contracts`, `infra`.
4. Do not start Vault/RAG/sandbox before v0.1 ships (`06-first-ship-plan.md`, S105). The adaptive tutor is the engine behind the learning (model gateway from S56, tutor from S63); every model call goes through `ai_gateway`, is schema- and feature-validated, labeled in the UI, and never grades or writes evidence. Seeded content and every screen still work with no key.
4a. A step is done only when its acceptance holds — tests named in the step, plus the phase gate's accessibility, performance-budget, and design-review checks.
5. Seeded Prove Loop content must work without an LLM API key.
6. Server-side ownership checks on every nested resource id; no cross-user retrieval by similarity.
7. Never execute untrusted learner code in the API process.
8. Product name is **Dolphin** only — see `docs/design/brand.md` retired appendix; do not revive old working names in titles or active specs.

## Stack (target)

Next.js (web) + FastAPI (API) + Postgres — Clear Depth visual identity on the client.
