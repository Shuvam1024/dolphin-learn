# 01 — Product and UX

**Product:** Dolphin  
**Document role:** Information architecture, core screens, Prove Loop, Clear Depth visual system

---

## Prove Loop (Phase 1A exit journey)

Sign in → create goal → feasible plan → Session Studio → independent check → Evidence Ledger → review → Home — works with seeded content and **no** LLM API key.

Detailed first-launch steps:

1. Landing explains Dolphin as a complete personal learning system, not a proficiency guarantee.
2. Sign in (managed auth).
3. Natural-language goal → Quick Learn or Journey → a budget of **actual study minutes**.
4. Backend normalizes → proposed objective, prerequisite estimate, feasibility range.
5. User confirms; optional short diagnostic or “start from basics.”
6. Persist goal, time budget, path, plan version, session; show included vs deferred outcomes.
7. Session Studio: seeded content + practice; answers become attempt records.
8. Hint/solution/pause/mode change; assistance history persists.
9. Feedback + different independent check + next step.
10. Session summary: topics, independent attempts, unresolved items, review recommendation.

**Critical:** refresh mid-flow without data loss; no cross-user access to goals, files, or attempts.

---

## Global navigation (P0 lock)

Primary: **Learn / Review / Library / Progress** + **More** (Settings, Projects when present, account).

| Surface | Role |
|---|---|
| **Home** (`/app`) | Product hub — next action, goals, feasibility, due reviews, evidence snapshot, Quick Learn |
| **Learn** | Goals, path overview, Session Studio entry |
| **Review** | Due queue |
| **Library** | Knowledge Vault (honest empty/coming-later until Phase 2A) |
| **Progress** | Evidence Ledger–oriented view |
| **More** | Settings, privacy, help |

Within Session Studio, use a contextual workspace — do not bounce the learner across many top-level pages.

### Routes

```text
/                       marketing or auth redirect
/sign-in                managed authentication
/onboarding             optional preferences + first goal
/app                    Home (learning dashboard hub)
/app/goals/new          goal + study-minute budget wizard
/app/goals/:goalId      objectives, plan, feasibility
/app/goals/:goalId/edit timeframe, scope, preferences
/app/learn/:sessionId   Session Studio
/app/review             due items + history
/app/library            files and linked sources (later)
/app/progress           Evidence Ledger analytics
/app/settings           profile, access, privacy, export/delete
```

---

## Core screens

### Home

One primary next action (“Continue: solving equations — 20 min”); due reviews; active goals with feasibility note; Quick Learn; recent independent evidence; empty-state → create first goal. **No** streak counters, leaderboards, or punitive missed-day shame.

### Goal wizard

1. Goal text → 2. Study minutes (one sitting, or minutes per sitting × number of sittings) → 3. Priority/preferences → 4. Optional diagnostic → 5. Plan preview + disposition rationale. Always allow back/edit. Keyboard-friendly; mobile usable. There is no deadline date.

### Learning path

Accessible ordered list; labels: prereq / needs-practice / demonstrated / deferred; session cards with minutes + evidence objectives; “Why this next?”; usable minutes and measured study minutes.

### Session Studio

Title + competency; quiet progress + remaining estimated effort (**not** a punishing countdown); main content; context panel (tutor, notes, citations, lab); hint / show solution / submit / pause. Modes: `guided`, `independent_challenge`, `direct_explanation`, `explore`. Seeded path when AI unavailable. Pause/resume persists.

### Review

Due by competency, why due, estimated minutes, snooze, independent question, schedule update.

### Progress (Evidence Ledger)

Facets: exposed / practicing / independently_demonstrated / retained / applied / unassessed. Distinguish assisted vs independent. **Never** a single global “% mastered.”

### Settings

Language, density, reduced motion, default session length, optional non-punitive notifications, privacy/export/delete.

---

## Time Intelligence (UX-facing rules)

Study time is physical. It is the minutes a session was active, not a date.

- Ask for real minutes (one sitting, **or** minutes per sitting times a number of sittings — never both, and never 24 hours per day).
- If estimated required low > usable budget → **scope conflict**: show what fits and what does not. Offer a smaller goal or more minutes. Do not invent a deadline date.
- Plans are versioned; accept is explicit; replan creates a new version without mutating evidence. After Phase 1C, replan uses minutes still remaining.
- Misses change future planning only — never dump everything onto one catch-up day. Time away is not study.

### Same subject, different budgets (Python examples)

| Input | Appropriate scope |
|---|---|
| 15 min | Variables + basic output; no mastery claim |
| 2 h | I/O, conditions/loops, tiny program, independent challenge |
| 2 wk × 30 min/day | Selected fundamentals + mini-project + review |
| 6 mo × 5 h/wk | Foundations, testing, projects, revisits + portfolio evidence |

---

## Evidence honesty (UX copy rules)

| Observation | May say | Must not say |
|---|---|---|
| Watched lesson | Exposed / encountered | Mastered |
| Solved after hints | Assisted practice | Independent demonstration |
| Unseen validated task unassisted | Independently demonstrated (scoped) | Retained forever / all related skills |
| Delayed check passed | Retention for task/horizon | Permanent knowledge promise |

Full solution on request is allowed — then label evidence assisted and issue a **different** independent check.

---

## Clear Depth visual direction

- **Brand signal:** calm depth, fluid adaptation, trustworthy clarity. Adult, contemporary, curious.
- **Avoid:** indigo–purple AI cliché; warm cream + terracotta serif cliché; streak/leaderboard chrome; neon glow stacks; childlike mascot spam.

### Tokens (verify contrast on real pairings)

| Token | Value | Use |
|---|---|---|
| Deep water ink | `#0B1F2A` | Primary text / chrome |
| Seafoam action | `#1FA7A0` | Primary actions |
| Foam surface | `#F4F8F9` / elevated `#E8F1F3` | Backgrounds |
| Signal amber | `#E6A817` | CTAs / alerts (not terracotta) |
| Mist secondary | `#5A6B73` | Secondary text |

Light theme first; dark mode only if contrast-validated later.

### Typography

- **Syne** — display  
- **Manrope** — UI  
- **IBM Plex Mono** — code / math plaintext  

Avoid Inter / Roboto / Arial / system as the design voice.

### Atmosphere and motion

Subtle depth gradients / soft water-grain; real learning imagery where used. Default: no cards in marketing hero. Motion: 2–3 intentional moments (Home next-action entrance, Studio activity crossfade, plan feasibility reveal). Respect `prefers-reduced-motion`.

---

## Accessibility and agency

- WCAG 2.2 AA target; keyboard, focus, contrast, zoom, reduced motion.
- Explicit user choice can override recommendations; AI never silently deletes or rewrites learner history.
- Adult enrollment acknowledgment before learning flows.
- Every async feature needs idle/loading/success/empty/error/retry. No dead buttons; no cosmetic progress.
