# Dolphin design package

**Product:** Dolphin  
**Repo:** [shuvam1024/dolphin-learn](https://github.com/shuvam1024/dolphin-learn)  
**Status:** Build specification — not a claim of shipped features  
**Preferred tagline:** *Learn anything. Fit the time you have. Prove you can do it.*

This folder is the **source of truth** for product vision, UX, architecture, sequential build steps, and implementation tracking. Prefer these files over any older notes outside the repo.

## Index

| Doc | Purpose |
|---|---|
| [`00-vision-and-principles.md`](00-vision-and-principles.md) | Omega vision, first-class pillars, differentiation, principles |
| [`01-product-and-ux.md`](01-product-and-ux.md) | IA, Home, Session Studio, Prove Loop, Clear Depth visual |
| [`02-architecture.md`](02-architecture.md) | Stack, modules, data model, API/AI/security boundaries |
| [`03-build-plan.md`](03-build-plan.md) | Sequential steps S01–S50 (Phases 0, 1A–1D) — complete |
| [`04-implementation-status.md`](04-implementation-status.md) | What is done, next step, test results |
| [`05-direction.md`](05-direction.md) | Final vision at the center, assessment after S50, phase order to v0.1 and after |
| [`06-first-ship-plan.md`](06-first-ship-plan.md) | Sequential steps S51–S105 (Phases 2–7) to a shippable v0.1 — AI/ML integrated as the engine, deterministic core as referee — with verification gates |
| [`project-context.md`](project-context.md) | Locked decisions (name, repo, stack, non-goals) |
| [`brand.md`](brand.md) | Locked name, tagline, Clear Depth tokens; retired names appendix |

## How to use (agents and humans)

1. Read `project-context.md` locks first.
2. Implement one step at a time: `03-build-plan.md` for S01–S50 (done), then `06-first-ship-plan.md` from **S51**.
3. Update `04-implementation-status.md` after every completed step.
4. Explain **what / how / why** from each step’s teach note while building.
5. The current build is Phase 2 (S51–S58, foundations incl. the AI gateway). Read `05-direction.md` first: the final vision is the center of every decision. Each phase ends at a verification gate (suite, a11y, perf budget, design review, docs). No Vault, RAG, or sandbox before v0.1. AI is integrated from S56 through the gateway; it explains and drafts, never grades.

## Slim pointer

Root [`../dolphin-master-design.md`](../dolphin-master-design.md) only redirects here — do not maintain a second conflicting master spec.
