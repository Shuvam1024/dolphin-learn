# Dolphin — Project context

Stable goals, constraints, and decisions for the Learning Platform project.  
**Last updated:** September 23, 2026

---

## Product

| Decision | Value |
|---|---|
| Product name | **Dolphin** (locked) |
| GitHub repo | public **`shuvam1024/dolphin-learn`** (also Cursor Cloud Agent project repo) |
| Document SoT | `docs/dolphin-master-design.md` |
| Brand notes | `docs/brand-shortlist.md` |
| Build tracker | `docs/implementation-status.md` |
| Sequential build plan | `docs/build-plan.md` (Phase 0 → Phase 1A Prove Loop, S01–S40) |
| Superseded packages | Atlas design package in `internal/atlas-source/` (engineering depth source only); other prior name candidates are retired — do not build from them |

---

## Vision (user-locked)

Dolphin is an **all-in omega learning platform**: for **anyone**, for **anything**, in **any time**, **personalized for each user**.

Long-term ambition is universal domain coverage and deeply personal paths. Shipping honesty requires staged delivery — architecture welcomes every domain; marketing never claims full mastery coverage before it exists.

---

## First-class pillars (non-negotiable)

1. **Centralized learning dashboard (Home)** — product hub: next action, goals, due reviews, evidence snapshot, Quick Learn.
2. **Time-adaptive planning** — plans from **real available minutes**, feasibility/scope conflict, versioned replan; not calendar-horizon fiction.
3. **Honest capability evidence** — Evidence Ledger: assisted vs independent, delayed retention, projects; no fake % mastered or streak-as-learning.

Supporting systems (Session Studio / tutor, curriculum graph, Vault, labs, review, accessibility) remain core platform — not optional side quests.

---

## V1 wedge (honest staging)

| Dimension | V1 |
|---|---|
| Audience | Adults **18+** (age-gate; no child product until designed + reviewed) |
| Subjects | **Python** + **foundational math** + **generic reading path** |
| Client | Accessible responsive **web** |
| Loop | Prove Loop: goal → feasible plan → Session Studio → independent check → Evidence Ledger → review → Home |
| AI | Optional; **seeded content must work without API keys** |
| Stack default | Next.js + FastAPI + Postgres **modular monolith** (unless existing coherent stack) |

---

## UX / brand locks

- P0 nav: **Learn / Review / Library / Progress** (+ **More**).
- **Session Studio** is the lesson surface — not a chat-shell product.
- **No streak guilt**; optional non-punitive reminders only.
- Visual identity: **Clear Depth** (deep water ink / seafoam / foam / signal amber) — avoid indigo-purple AI cliché and cream-serif terracotta cliché; avoid retired mesa/canyon visual directions from prior name explorations.
- Do not ship under Atlas, Planhaven, Tallymark, Planmoor, or other retired names.

---

## Differentiation to preserve

Vs Meridian / Brilliant / Khanmigo / StudyFetch / generic AI tutors:

- Feasible plans from **real available minutes** + honest scope conflict
- **Evidence Ledger** honesty (assisted ≠ independent; same-session ≠ retention)
- **Session Studio** craft (modes, pause, seeded fallback)
- **Home** as hub (not a planner-only shell)
- Domain-adapter architecture with honest V1 scope
- Simplified P0 nav; no streak/leaderboard guilt

---

## Engineering constraints

- Phase **0 → 1A Prove Loop** before Vault/RAG, code sandbox, or community.
- Follow `docs/build-plan.md` step IDs (`S01`…); **commit after each step**.
- While developing each step, explain **what / how / why** (see each step’s teach note) — the user is learning as we build.
- Server-side ownership checks; no cross-user retrieval by similarity.
- Never execute untrusted learner code in the API process.
- Assisted practice ≠ independent mastery; same-session ≠ retention.
- No dead controls; no cosmetic progress.
- Privacy: export/delete before calling production-ready; adult-only until compliance review for minors/schools.
- Do not create the GitHub remote until auth is ready; local commits are fine.

---

## Non-goals (near term)

Accredited credentials; replacing human teachers; training a foundation model; social feed; child/school accounts; “all subjects fully assessed” marketing; microservice fleet; punitive gamification.

---

## Implementation stance

Cursor (and humans) follow `docs/dolphin-master-design.md` Sections 20–22 and the sequential steps in `docs/build-plan.md`: smallest vertical slice, real tests, update `docs/implementation-status.md` each step. Mega-tickets `DOLPHIN-BOOT-001` … `DOLPHIN-E2E-001` are orientation only — execute via S01–S40.
