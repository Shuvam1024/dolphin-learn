# 00 — Vision and principles

**Product:** Dolphin  
**Document role:** Vision, pillars, differentiation, pedagogical principles

---

## Omega vision (locked)

Dolphin is an **all-in learning platform** for **anyone**, for **anything**, in **any time**, **personalized for each user**.

Architecture welcomes every domain. Shipping honesty requires staged delivery: V1 is a deep vertical slice (Python + foundational math + generic reading path) without fake “all subjects fully validated” marketing.

**One-sentence vision:** Dolphin turns any appropriately scoped subject, question, personal resource, or skill objective into a guided learning experience that adapts to starting knowledge, goals, **real available minutes**, demonstrated performance, and preferred interaction methods — then helps the learner practice, retain, and independently apply what they learned.

**Preferred tagline:** *Learn anything. Fit the time you have. Prove you can do it.*

---

## Non-negotiable product identity

Dolphin is a comprehensive learning home — **not** a short-course generator, flashcard app, AI chat wrapper, or deadline planner alone.

Time-adaptive planning is one cross-cutting capability inside a broader system: Session Studio tutoring, curricula, concept maps, hands-on activities, Evidence Ledger assessment, retention, projects, and learning analytics. Ship an honest vertical slice first; expand without rewriting foundations.

---

## First-class pillars (product locks)

These three are non-negotiable identity — not optional modules:

1. **Centralized learning dashboard (Home)** — hub: next best action, active goals, available session length, due reviews, recent Evidence Ledger snapshot, Quick Learn / start something new.
2. **Time-adaptive learning** — plans from **real available minutes**, feasibility / scope conflict, versioned replan after misses or constraint changes. Calendar horizon ≠ study effort.
3. **Honest capability evidence (Evidence Ledger)** — assisted vs independent, delayed retention, project/application evidence; no fake global “% mastered”; no streak-as-learning guilt.

---

## Eight permanent platform pillars

Every release preserves a path for each (not every pillar is fully implemented in MVP):

1. Goals & Time Intelligence  
2. Curriculum & Competency Graph  
3. Session Studio & Adaptive Tutor  
4. Knowledge Vault (Phase 2A — not before Prove Loop)  
5. Interactive Learning Labs  
6. Assessment & Evidence Ledger  
7. Retention & Planning  
8. Progress, Agency & Accessibility  

---

## Problems Dolphin solves

Learners patch together courses, videos, notes, AI chat, flashcards, calendars, exercises, and project repos. Context breaks across tools; exposure is confused with competence; plans ignore actual time budgets. General AI chat answers questions but does not provide coherent curriculum, controlled practice, traceable sources, independent assessment, or retention planning.

Dolphin joins those jobs as the **learning home**. It does not replace human teachers, accredited credentials, physical training, or licensed professionals.

---

## Primary jobs to be done

- “I have 20 minutes; explain and let me practice exactly this concept.”
- “I have an exam in 2 weeks and 45 minutes on weekdays; help me prioritize and find gaps.”
- “I want to become capable of building web apps over 6 months; teach, test, and help me ship.”
- “I have a PDF or notes; teach me from this material and cite the source.” (Vault — later phase)
- “I learned something last month; help me remember and apply it without hints.”
- “I need to change my deadline or study time; replan without deleting progress.”

---

## Outcomes, not screen-time

**North-star:** improvement on appropriately designed **independent, delayed, goal-relevant assessments**, plus practical project completion and user-reported usefulness.

**Never** equate streaks, AI messages, time spent, or course completion with learning. No streak guilt. No leaderboard pressure in V1.

---

## Differentiation to preserve

Vs generic AI tutors, flashcard apps, and planner-only tools:

| Dimension | Dolphin stance |
|---|---|
| Planning | Feasible plans from **real available minutes** + honest scope conflict |
| Assessment | Evidence Ledger: assisted ≠ independent; same-session ≠ retention |
| Teaching surface | **Session Studio** craft (modes, pause, seeded fallback) — not a chat shell |
| Hub | **Home** as centralized dashboard, not a planner-only or chat-first shell |
| Scope honesty | Domain-adapter architecture with truthful V1 wedge |
| Motivation | Simplified P0 nav; no streak/leaderboard guilt |

---

## Product boundaries (V1)

| Boundary | Decision |
|---|---|
| Audience | Adults **18+**; age-gate until a child-specific product is designed and reviewed |
| Subjects | Computing first: CS, software engineering, then AI/ML. Math only as a prerequisite |
| Client | Accessible responsive web |
| Loop | Prove Loop: goal → feasible plan → Session Studio → independent check → Evidence Ledger → review → Home |
| AI | Optional; seeded content must work without API keys |
| Stack | Next.js + FastAPI + Postgres modular monolith |

---

## Research-informed principles (design guidance — not efficacy claims)

| Principle | Implementation rule |
|---|---|
| Retrieval practice | Recall/solve without source; independent retry after assistance |
| Distributed practice | Plan revisits after elapsed time; separate from the initial session |
| No fixed “learning styles” | Modality/a11y preferences only — never diagnose VAK types |
| Inclusive instruction | Multiple means of engagement, representation, action (UDL) |
| Accessible UX | WCAG 2.2 AA target |
| Responsible generative AI | Accuracy, harm, privacy, oversight; treat uploads as untrusted |

**Pedagogical constraints:**

- Assistance changes evidence quality (`independent`, `hinted`, `worked_example`, …).
- Never classify a user as “low ability.” Skill estimates are local and uncertain.
- Delayed checks → retention; new-context tasks → transfer. Neither from lesson completion alone.
- A smaller study-minute budget prioritizes what fits. It does not redefine mastery, and a calendar date is not study time.

---

## Direction

`05-direction.md` is the current product judgment, including how time is measured. It is not a second build plan. Sequential steps stay in `03-build-plan.md`.

## Near-term non-goals

Accredited credentials; replacing human teachers; training a foundation model; social feed; child/school accounts; “all subjects fully assessed” marketing; microservice fleet; punitive gamification; Vault/RAG/code sandbox before the written phase in `03-build-plan.md` is finished.
