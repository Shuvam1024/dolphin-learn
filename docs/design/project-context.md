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
| Sequential build plan | `docs/design/03-build-plan.md` (through Phase 1C, S46) |
| Product judgment | `docs/design/05-direction.md` (time is active minutes, not dates) |
| Brand | `docs/design/brand.md` |

---

## Vision (user-locked)

Dolphin is an **all-in omega learning platform**: for **anyone**, for **anything**, in **any time**, **personalized for each user**.

Architecture welcomes every domain; marketing never claims full mastery coverage before it exists.

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
| Subjects | Python + foundational math + generic reading path |
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

Follow `docs/design/` and execute S01–S40. Mega-tickets (`DOLPHIN-BOOT-001` …) are orientation only — execute via sequential step IDs.
