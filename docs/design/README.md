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
| [`03-build-plan.md`](03-build-plan.md) | Sequential steps **S01–S40** (Phase 0 → Phase 1A Prove Loop) |
| [`04-implementation-status.md`](04-implementation-status.md) | What is done, next step, test results |
| [`project-context.md`](project-context.md) | Locked decisions (name, repo, stack, non-goals) |
| [`brand.md`](brand.md) | Locked name, tagline, Clear Depth tokens; retired names appendix |

## How to use (agents and humans)

1. Read `project-context.md` locks first.
2. Implement one step at a time from `03-build-plan.md`.
3. Update `04-implementation-status.md` after every completed step.
4. Explain **what / how / why** from each step’s teach note while building.
5. Stop before Vault/RAG/sandbox until Phase 1A (through S40) is demonstrated.

## Slim pointer

Root [`../dolphin-master-design.md`](../dolphin-master-design.md) only redirects here — do not maintain a second conflicting master spec.
