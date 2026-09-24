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

Primary: **Learn / Review / Library / Progress** + **More** (Settings, Help, Privacy, Sign out).

Under 768px the shell uses **bottom tabs** for Learn / Review / Library / Progress / More. From 768px up it uses a top bar with the same destinations. Landing (`/`) states what Dolphin is in five lines; Help explains evidence words, minutes, reviews, and that the tutor never grades.

| Surface | Role |
|---|---|
| **Home** (`/app`) | One next action with subtitle and minutes; goal cards; due-review count; evidence chips |
| **Learn** | Every goal organized: Active / Paused / Archived with Continue, Pause, Resume, Archive |
| **Review** | Due queue with estimates and what fits this sitting; snooze 3h / 24h / 72h |
| **Library** | Knowledge Vault (honest empty/coming-later until later phase) |
| **Progress** | Evidence by goal with facet chips, collapsed legend → Help, upcoming reviews |
| **More** | Settings, Help, Privacy, Sign out |

Within Session Studio, use a contextual workspace — do not bounce the learner across many top-level pages.

### Routes

```text
/                       landing (what Dolphin is)
/sign-in                managed authentication
/app                    Home
/app/goals/new          goal wizard (text → minutes → priority → preview → accept)
/app/goals/:goalId      path v2: minutes left, lesson chips, Not in this plan, replan preview → accept
/app/goals/:goalId/start sitting chooser
/app/learn              goal shelf (active / paused / archived)
/app/learn/:sessionId   Session Studio
/app/review             due items + fit + snooze presets
/app/library            files and linked sources (later)
/app/progress           Evidence by goal + upcoming reviews
/app/help               evidence, minutes, reviews, tutor limits
/app/settings           stub → privacy / export later
/app/more               Settings, Help, Privacy, Sign out
```

---

## Core screens

### Home

One primary next action with subtitle and minutes; goal cards with subject and next lesson; due-review count; recent evidence chips. Empty-state → create first goal. Log out lives under More. **No** streak counters, leaderboards, or punitive missed-day shame.

### Goal wizard

1. Goal text + subject → 2. Study minutes → 3. Priority (Cover more ground / Focus one topic / Leave room for review) → preview with lesson names and minutes, total vs budget, Not in this plan, plan explanation (AI chip when on) → Accept. Live priority re-fetches the proposal. Keyboard-friendly; mobile usable. There is no deadline date.

### Learning path

Header “About N of M minutes left”; lessons with facet chips and `~low–high min`; why-next; Not in this plan with plain reasons; Update plan → preview → Accept (stale hash rejected); Plan history disclosure. Priority shapes breadth, depth, and review reserve.

### Session Studio

Studio v2 is the learning session for every activity type. Header shows goal › lesson, activity position, **about N minutes** for this sitting, and a quiet remaining estimate (**not** a countdown). When active minutes reach the sitting target and the current activity is complete, Studio offers a **good place to stop** — Finish primary, Keep going secondary; nothing is forced.

**Activity types in the body:** reading, worked example, objective, short answer, numeric, free recall, reflection. Markdown renders real code. One sticky primary action. Worked examples use “Now you try.” Free recall hides the lesson until the learner writes from memory, then self-rates.

**Feedback:** after a graded attempt or reveal, the explanation and the note for *this* mistake appear (seeded choice notes; AI misconception notes for typed wrong answers, labeled). Assisted answers make the primary “Try a fresh question.”

**Tutor panel:** explain differently and hint when AI is on for the learner; always labeled with the Tutor/AI chip. With AI off, the panel stays hidden and `/explain` is unavailable. Generated hints that leak the answer fall back to the seeded hint.

**Sitting chooser:** new sittings start at `/app/goals/[goalId]/start` (10/15/30/45/60 or “use my usual”). Resume never asks again.

**Modes:** `guided` (shipped), with slots for `independent_challenge`, `direct_explanation`, `explore`. Seeded path when AI unavailable. Pause/resume persists; the clock stops when you pause.

### Session summary

End-of-session summary lists what you showed on your own, practiced with help, and self-reported; watch-outs (seed and AI notes, labeled); next review; minutes studied; and a next step. No celebration, streak, or mastery-percent copy.

### Review

“N due · start with M (about K minutes)” against preferred session length; one item at a time; estimated minutes per item; snooze presets 3h / 24h / 72h. Copy never says overdue, missed, or streak.

### Progress (Evidence Ledger)

Grouped by goal: competency name, facet chip, last independent time, self-reported flag, unassessed count. Collapsed legend links to Help. Upcoming reviews listed. **Never** a single global “% mastered.”

### Settings / Help / More

Help owns evidence words, how minutes are counted, reviews, and tutor limits (never grades). More links Settings, Help, Privacy, Sign out.

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
