# Project context — locked decisions

Stable goals, constraints, and decisions for Dolphin.  
**Last updated:** September 23, 2026

---

## Product

| Decision | Value |
|---|---|
| Product name | **Dolphin** (locked) |
| GitHub repo | public **`shuvam1024/dolphin-learn`** (also Cursor Cloud Agent project repo) |
| Design SoT | `docs/design/` |
| Build tracker | `docs/design/04-implementation-status.md` |
| Sequential build plan | `docs/design/03-build-plan.md` (S01–S50, complete) → `docs/design/06-first-ship-plan.md` (S51–S105, to v0.1) |
| Product judgment | `docs/design/05-direction.md` (final vision at the center; time is active minutes, not dates) |
| Brand | `docs/design/brand.md` |

---

## Vision (user-locked)

Dolphin is an **all-in omega learning platform**: for **anyone**, for **anything**, in **any time**, **personalized for each user**.

Architecture welcomes every domain; marketing never claims full mastery coverage before it exists.

**Final product vision (user emphasis, 2026-09-23):** the learner can learn **anything they want**, keep learning **organized in one place**, get **real learning content, technique, and performance**, and have Dolphin **adapt to the task and the time they actually have**. The interface stays **clean and easy to use**; most of the machinery is **behind the scenes** — AI/ML is that machinery (tutor, drafting, normalizing, plan explanation, learner model), with the deterministic core as referee for grades, evidence, and plans. Every feature and design decision is judged on appeal, usefulness, and ease for the learner; intensive testing and verification (tests, accessibility, performance, design review) precede each step's "done"; design docs are updated when the product changes.

**Curriculum focus vs learning order:** computer science → software engineering → AI/ML is the current focus for demos and seeded content only. It is not a learning order the product imposes. The shared core (goals, minute budgets, competency graph, sessions, Evidence Ledger, reviews, study clock) stays subject-agnostic.

---

## First-class pillars (non-negotiable)

1. **Centralized learning dashboard (Home)**
2. **Time-adaptive planning** from real available minutes
3. **Honest capability evidence** (Evidence Ledger)

---

## V1 wedge

| Dimension | V1 |
|---|---|
| Audience | Adults **18+** |
| Subjects | Any subject on one platform. Early demos may prefer computing content we can grade well; that is not a required learner path |
| Client | Accessible responsive web |
| Loop | Prove Loop |
| AI | Optional; seeded content works without keys |
| Stack | Next.js + FastAPI + Postgres modular monolith |

---

## UX / brand locks

- P0 nav: **Learn / Review / Library / Progress** (+ **More**)
- **Session Studio** is the lesson surface — not a chat-shell product
- **No streak guilt**
- Visual identity: **Clear Depth** (see `brand.md` and `01-product-and-ux.md`)

---

## Engineering constraints

- Phase **0 → 1A Prove Loop** before Vault/RAG, code sandbox, or community
- Follow `03-build-plan.md` step IDs; **commit after each step**
- Explain **what / how / why** from each teach note while developing
- Server-side ownership checks; no cross-user retrieval by similarity
- Never execute untrusted learner code in the API process
- Assisted practice ≠ independent mastery; same-session ≠ retention
- No dead controls; no cosmetic progress

---

## Near-term non-goals

Accredited credentials; replacing human teachers; training a foundation model; social feed; child/school accounts; “all subjects fully assessed” marketing; microservice fleet; punitive gamification.

---

## Implementation stance

Follow `docs/design/`. S01–S50 are complete; execute S51–S105 from `06-first-ship-plan.md`, passing each phase gate before the next. Mega-tickets (`DOLPHIN-BOOT-001` …) are orientation only — execute via sequential step IDs.
