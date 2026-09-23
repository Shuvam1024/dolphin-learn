# Dolphin — Sequential Build Plan

**Document status:** Learning-oriented implementation sequence — not a claim of shipped code  
**Last updated:** September 23, 2026  
**Audience:** Learner building Dolphin step by step with Cursor  
**Scope:** Phase 0 (foundation) → Phase 1A Prove Loop only. Stop before Vault/RAG/sandbox.

---

## How to use this plan

1. Work **one step at a time** in ID order (`S01` → `S02` → …).
2. **Commit after each step** using the suggested message (or a close variant).
3. Meet the **acceptance check** before starting the next step.
4. While developing, explain **what / how / why** from the teach note — learning is the point.
5. Keep `docs/design/04-implementation-status.md` current after every completed step.
6. Do **not** create a GitHub remote until auth is ready; local git commits are fine.
7. Do **not** start Vault uploads, RAG, or code sandboxes here — only tiny seams if a later step explicitly needs a stub.

**Prove Loop (Phase 1A exit):** sign in → create goal → feasible plan → Session Studio → independent check → Evidence Ledger → review → Home — works with seeded content and **no** LLM API key.

**Companion docs:** `00`/`01`/`02` (spec), `project-context.md` (locks), `04-implementation-status.md` (tracker).

---

## Phase 0 — Foundation

Empty repo → runnable web + API shell, Postgres migrations, managed auth, seeds, honest nav, smoke tests.

---

### S01 — Monorepo skeleton

| Field | Value |
|---|---|
| **Title** | Create Dolphin monorepo folder layout |
| **Commit** | `chore: scaffold dolphin monorepo layout` |
| **Files/areas** | Root `README` stub, `apps/web/`, `services/api/`, `packages/contracts/`, `infra/`, `docs/` (copy or link design docs), `AGENTS.md` pointer |
| **Acceptance** | Empty folders exist with placeholder READMEs; `tree`/`ls` shows the Section 11.4 shape; no app runtime required yet |

**Teach note:**  
**What:** We reserve a clear home for the web app, API, shared contracts, and infra before writing features.  
**How:** Create the directories and short README stubs that name each package’s job.  
**Why:** A modular monolith stays maintainable when module boundaries are visible from day one — later adapters plug in without rewriting the foundation.

---

### S02 — README and environment template

| Field | Value |
|---|---|
| **Title** | Document install story and `.env.example` |
| **Commit** | `docs: add README and env example for local setup` |
| **Files/areas** | `README.md`, `.env.example`, `.gitignore` |
| **Acceptance** | README lists stack (Next.js, FastAPI, Postgres), how to copy `.env.example`, and that AI keys are optional; `.env.example` has named placeholders only (no secrets) |

**Teach note:**  
**What:** Newcomers (including future-you) need a truthful “how do I run this?” story.  
**How:** Write install/run placeholders and list every env var the app will need later, empty or fake.  
**Why:** Secrets never belong in git; documenting variables early prevents hard-coding and makes Phase 1A’s “works without AI key” promise enforceable.

---

### S03 — Docker Compose for Postgres

| Field | Value |
|---|---|
| **Title** | Add local Postgres via Docker Compose |
| **Commit** | `chore: add docker-compose postgres for local infra` |
| **Files/areas** | `docker-compose.yml`, README “infra” section, `.env.example` DB URL |
| **Acceptance** | `docker compose up -d` starts Postgres; connection string from `.env.example` works with `psql` or a ping script |

**Teach note:**  
**What:** Dolphin’s source of truth is relational data — plans, attempts, evidence — so we need a real database early.  
**How:** Compose runs Postgres locally only; app processes stay outside the container for normal development.  
**Why:** Local infra in Compose keeps the modular monolith simple while matching production’s Postgres assumptions (migrations, ownership queries).

---

### S04 — FastAPI health endpoint

| Field | Value |
|---|---|
| **Title** | Boot FastAPI with `/health` |
| **Commit** | `feat(api): add fastapi app with health check` |
| **Files/areas** | `services/api/` (entry, deps, `GET /health`), pin Python deps |
| **Acceptance** | `uvicorn` serves `GET /health` → `200` JSON; deps install cleanly from lock/requirements |

**Teach note:**  
**What:** The API is the authenticated brain for goals, sessions, and evidence.  
**How:** Create a minimal FastAPI app and one health route that proves the process starts.  
**Why:** A tiny green path de-risks tooling (venv, pins, ports) before auth, schemas, or business logic pile on.

---

### S05 — Next.js app shell

| Field | Value |
|---|---|
| **Title** | Boot Next.js TypeScript web shell |
| **Commit** | `feat(web): scaffold next.js typescript app shell` |
| **Files/areas** | `apps/web/` (Next.js + TS), root scripts to run web |
| **Acceptance** | `npm`/`pnpm` install + `dev` shows a placeholder page at localhost; TypeScript compiles |

**Teach note:**  
**What:** Learners interact with Dolphin through an accessible responsive web client.  
**How:** Scaffold Next.js with TypeScript and a single placeholder route.  
**Why:** Establishing the client early lets later steps add real screens without fighting “which framework?” mid-feature.

---

### S06 — Clear Depth design tokens

| Field | Value |
|---|---|
| **Title** | Add Clear Depth CSS variables and fonts |
| **Commit** | `feat(web): add clear depth tokens and brand fonts` |
| **Files/areas** | Global CSS / theme tokens (`#0B1F2A`, `#1FA7A0`, `#F4F8F9`, `#E6A817`, `#5A6B73`), Syne + Manrope (+ IBM Plex Mono reserved), subtle atmosphere background on shell |
| **Acceptance** | Placeholder page uses tokens (not default Inter/purple); fonts load; light theme first |

**Teach note:**  
**What:** Brand is a first-class signal — Dolphin should feel calm depth, not generic AI purple.  
**How:** Define CSS variables and load Syne/Manrope; apply ink/seafoam/foam surfaces on the shell.  
**Why:** Tokens keep every later screen consistent and stop accidental “another indigo chatbot” drift.

---

### S07 — Shared error and API conventions

| Field | Value |
|---|---|
| **Title** | Define shared error envelope and `/api/v1` prefix |
| **Commit** | `feat(api): standardize v1 prefix and error envelope` |
| **Files/areas** | API router mount `/api/v1`, error middleware `{ error: { code, message, details, request_id } }`, optional `packages/contracts` types |
| **Acceptance** | Hitting an unknown route or raising a validation error returns the envelope shape; health may stay outside or under v1 consistently documented |

**Teach note:**  
**What:** Clients and tests need one predictable way to read failures.  
**How:** Mount versioned routes and map exceptions to a small JSON error schema with a request id.  
**Why:** Consistent errors make debugging and OpenAPI clients easier than ad-hoc string messages per endpoint.

---

### S08 — Database session and Alembic bootstrap

| Field | Value |
|---|---|
| **Title** | Wire SQLAlchemy 2 + Alembic empty migration chain |
| **Commit** | `feat(api): bootstrap sqlalchemy and alembic` |
| **Files/areas** | DB engine/session, Alembic config, empty or baseline migration, README migrate commands |
| **Acceptance** | `alembic upgrade head` succeeds against Compose Postgres; app can open a DB session |

**Teach note:**  
**What:** Schema changes must be ordered, repeatable, and reviewable — not “edit prod by hand.”  
**How:** Configure SQLAlchemy 2 models + Alembic and run an initial migration.  
**Why:** Prove Loop data (goals, attempts, evidence) only stays honest if every environment shares the same migration history.

---

### S09 — Lint, typecheck, and test runners

| Field | Value |
|---|---|
| **Title** | Add lint/type/test scripts for web and API |
| **Commit** | `chore: add lint typecheck and test runners` |
| **Files/areas** | ESLint/tsc/Vitest (or RTL) for web; ruff/mypy/pytest for API; root Makefile or npm scripts; CI config stub (local-first OK) |
| **Acceptance** | One command each for web and API lint/type/test exits 0 with at least one trivial passing test |

**Teach note:**  
**What:** Automated checks catch regressions before learners hit them.  
**How:** Install linters and a unit-test runner on both sides; add a hello-world test.  
**Why:** Phase 1A acceptance depends on real tests (ownership, grading, E2E) — runners must exist before those tests matter.

---

### S10 — Managed auth integration (API)

| Field | Value |
|---|---|
| **Title** | Integrate managed OIDC/auth and map `auth_subject` |
| **Commit** | `feat(api): integrate managed auth and user subject mapping` |
| **Files/areas** | Auth middleware/dependency, `users` table migration (`auth_subject`, email), create-on-first-login |
| **Acceptance** | Request with valid test token resolves a user row; unauthenticated protected call → 401 |

**Teach note:**  
**What:** Identity is owned by a managed provider — we do not invent password storage.  
**How:** Verify JWTs/sessions from the provider and upsert a local `users` row keyed by `auth_subject`.  
**Why:** Every goal, attempt, and file must attach to a real owner; custom crypto auth is a security trap.

---

### S11 — Protected web shell and sign-in route

| Field | Value |
|---|---|
| **Title** | Add sign-in page and protect `/app` routes |
| **Commit** | `feat(web): add sign-in and protect app shell routes` |
| **Files/areas** | `/sign-in`, `/app` layout guard, auth SDK/client wiring, logout |
| **Acceptance** | Anonymous visit to `/app` redirects to sign-in; after sign-in, `/app` loads; logout clears session |

**Teach note:**  
**What:** The learning dashboard lives behind authentication.  
**How:** Wire the provider’s web SDK and a server/middleware check on `/app/*`.  
**Why:** Protected routes in the UI are a first line of defense; they complement (not replace) API ownership checks.

---

### S12 — Learner profile and preferences API

| Field | Value |
|---|---|
| **Title** | Add profile preferences (`GET/PATCH /me`) |
| **Commit** | `feat(identity): add learner profile and preferences endpoints` |
| **Files/areas** | `learner_profiles` migration, `GET /api/v1/me`, `PATCH /api/v1/me/preferences` (timezone, locale, display name, a11y prefs) |
| **Acceptance** | Authenticated user reads/updates own profile; another user’s id cannot be patched via the route |

**Teach note:**  
**What:** Timezone and accessibility prefs shape plans and UX without collecting sensitive health traits.  
**How:** 1:1 `learner_profiles` row with JSON/prefs columns and owner-scoped endpoints.  
**Why:** Time Intelligence needs a real IANA timezone; preferences stay editable and skippable for first-use speed.

---

### S13 — Adult age-gate and privacy notice UI

| Field | Value |
|---|---|
| **Title** | Add adult enrollment gate and privacy notice |
| **Commit** | `feat(web): add adult age-gate and privacy notice` |
| **Files/areas** | Onboarding/gate copy, acknowledgment persistence on profile, link to privacy summary |
| **Acceptance** | New user cannot reach goal creation until adult acknowledgment is recorded; acknowledgment survives refresh |

**Teach note:**  
**What:** V1 is adults 18+ until a child-specific product is designed and reviewed.  
**How:** Require an explicit acknowledgment stored on the profile before `/app` learning flows.  
**Why:** Age and privacy boundaries are product locks, not polish — they must precede content and Vault work.

---

### S14 — Core curriculum schema migrations

| Field | Value |
|---|---|
| **Title** | Migrate domains, competencies, and edges |
| **Commit** | `feat(db): migrate domains competencies and edges` |
| **Files/areas** | Tables `domains`, `competencies`, `competency_edges`; unique keys; edge-type constraints |
| **Acceptance** | Migration applies; inserting a self-loop or duplicate key fails; pytest covers uniqueness |

**Teach note:**  
**What:** Learning content hangs on diagnosable competencies and prerequisite edges.  
**How:** Create normalized tables for domains, competencies, and typed edges (`REQUIRES`, etc.).  
**Why:** The planner’s prerequisite closure and seeds need a real graph — not hard-coded lesson lists in UI.

---

### S15 — Goals and time-budget schema

| Field | Value |
|---|---|
| **Title** | Migrate goals and time_budgets |
| **Commit** | `feat(db): migrate goals and time budgets` |
| **Files/areas** | `goals`, `time_budgets`, `goal_competencies`; owner indexes; budget mode invariants |
| **Acceptance** | Migration applies; goal requires `user_id`; budget rejects negative minutes in model/validator tests |

**Teach note:**  
**What:** A goal captures what the learner wants; a time budget captures real available minutes.  
**How:** Separate tables so plan versions can snapshot budgets without mutating history carelessly.  
**Why:** Calendar horizon ≠ study effort — the schema forces that distinction from the start.

---

### S16 — Plans, sessions, activities, attempts schema

| Field | Value |
|---|---|
| **Title** | Migrate plans sessions activities attempts evidence review |
| **Commit** | `feat(db): migrate plans sessions attempts evidence review` |
| **Files/areas** | `learning_paths`, `plan_versions`, `plan_activities`, `lessons`, `activity_versions`, `sessions`, `session_events`, `attempts`, `evaluations`, `competency_evidence`, `competency_state`, `review_items`, `review_events` |
| **Acceptance** | `alembic upgrade head` clean; models import; ownership FKs present; attempt immutability noted in comments/constraints where practical |

**Teach note:**  
**What:** The Prove Loop needs durable plans, resumable sessions, append-only attempts, and review dues.  
**How:** Add the remaining P0 tables in one migration (or a tight pair) with FKs to users/goals/competencies.  
**Why:** Evidence honesty depends on immutable attempt snapshots and recomputable competency state — schema first, UI second.

---

### S17 — Seed Python and math mini-curricula

| Field | Value |
|---|---|
| **Title** | Seed reviewed Python and math competencies + activities |
| **Commit** | `feat(seed): add python and math mini curricula` |
| **Files/areas** | Seed script/data for domains, competencies, edges, lessons, activity_versions with answer keys, effort ranges |
| **Acceptance** | Fresh DB + seed loads ≥1 Python path and ≥1 math path; activities include reading + objective question types; no LLM required |

**Teach note:**  
**What:** Dolphin must teach something useful before AI is configured.  
**How:** Load curated, versioned items with deterministic keys into the curriculum tables.  
**Why:** Seeded content unlocks planner, Session Studio, and E2E demos while keeping “AI optional” honest.

---

### S18 — Honest P0 navigation shell

| Field | Value |
|---|---|
| **Title** | Ship Learn / Review / Library / Progress nav with honest empty states |
| **Commit** | `feat(web): add p0 nav shell with honest empty states` |
| **Files/areas** | App chrome nav, routes for Home/Learn/Review/Library/Progress/More; Library “coming later” or seeded-only disclosure; feature flags if needed |
| **Acceptance** | Signed-in user sees four primary nav items; Library does not fake upload controls; empty Home prompts creating a goal |

**Teach note:**  
**What:** Navigation is a product lock — Home is the hub, not a chat shell.  
**How:** Implement the P0 IA with real routes and truthful empty/coming-later copy where features are absent.  
**Why:** Dead buttons destroy trust; honest disclosure lets us ship the Prove Loop without pretending Vault exists.

---

### S19 — Phase 0 smoke tests

| Field | Value |
|---|---|
| **Title** | Add API + browser smoke tests for auth shell |
| **Commit** | `test: add phase 0 auth and health smoke tests` |
| **Files/areas** | Pytest health/auth; Playwright (or equivalent) sign-in → `/app` smoke |
| **Acceptance** | CI/local commands pass: health 200, unauthenticated `/app` blocked, authenticated shell loads |

**Teach note:**  
**What:** Phase 0 exits when foundation is demonstrably runnable, not merely scaffolded.  
**How:** Automate the smallest browser and API checks around health and auth.  
**Why:** Smoke tests freeze the floor under later Prove Loop work so boot regressions show up immediately.

**Phase 0 exit checklist:** clean install docs, Compose Postgres, migrations + seed, managed auth + protected `/app`, honest nav, lint/test runners green.

---

## Phase 1A — Prove Loop

Goal → plan → Session Studio → independent check → Evidence Ledger → review → Home.

---

### S20 — Goal create API

| Field | Value |
|---|---|
| **Title** | Implement create/list/get goals API |
| **Commit** | `feat(goals): add create list and get goal endpoints` |
| **Files/areas** | `POST/GET /api/v1/goals`, ownership filters, raw_request + normalized_objective fields |
| **Acceptance** | User A creates a goal and lists it; User B cannot GET A’s goal (403/404); validation rejects empty title/request |

**Teach note:**  
**What:** Everything in the Prove Loop hangs off an owned goal.  
**How:** CRUD-lite endpoints that always filter by the authenticated user id.  
**Why:** Server-side ownership is the real security boundary — the UI alone cannot protect private learning data.

---

### S21 — Time budget validation API

| Field | Value |
|---|---|
| **Title** | Attach and validate time budgets on goals |
| **Commit** | `feat(goals): validate and store time budgets` |
| **Files/areas** | Budget write/read on goal create/update; one-off minutes XOR weekly windows; preferred session length; contradiction checks |
| **Acceptance** | API rejects negative minutes and double-counted modes; accepts 120-minute Quick Learn and 2-week × 30 min/day shapes |

**Teach note:**  
**What:** Plans are only as honest as the minutes the learner actually has.  
**How:** Persist `time_budgets` with explicit mode rules and clear 422 errors on contradictions.  
**Why:** Silently inventing a budget would fake feasibility — the product must ask for correction instead.

---

### S22 — Accessible goal wizard UI (steps 1–3)

| Field | Value |
|---|---|
| **Title** | Build goal wizard: objective, availability, priority |
| **Commit** | `feat(web): add accessible goal and availability wizard` |
| **Files/areas** | `/app/goals/new` multi-step form (goal text → deadline/availability → priority); keyboard-friendly; calls goal/budget APIs |
| **Acceptance** | Keyboard-only completion creates a persisted goal+budget; back navigation preserves fields; mobile layout usable |

**Teach note:**  
**What:** First-use should create a goal quickly without drowning in preferences.  
**How:** Progressive wizard steps with real API saves and accessible labels/focus.  
**Why:** ID-04 and WCAG targets say agency and access matter as much as the planner algorithm.

---

### S23 — Optional diagnostic flow

| Field | Value |
|---|---|
| **Title** | Add skippable diagnostic sample for a goal |
| **Commit** | `feat(goals): add optional diagnostic start and attempts` |
| **Files/areas** | `POST /goals/{id}/diagnostic`, diagnostic items from seed, attempt recording, “start from basics” skip |
| **Acceptance** | User can skip or answer 3–8 items; incomplete diagnostic is retriable; results store without claiming mastery |

**Teach note:**  
**What:** A short diagnostic samples starting knowledge; confidence is not proof.  
**How:** Create owner-scoped diagnostics from seeded items; allow skip without blocking plan proposal.  
**Why:** Personalization should use evidence when present — and remain provisional when the sample is tiny or skipped.

---

### S24 — Deterministic plan proposal engine

| Field | Value |
|---|---|
| **Title** | Propose plans from budget, prereqs, and effort ranges |
| **Commit** | `feat(plan): add deterministic feasibility plan proposal` |
| **Files/areas** | Planner service: usable minutes, prereq closure, topo + greedy selection, included vs deferred competencies, reason codes; `POST …/plan-proposals` |
| **Acceptance** | 15-min vs 120-min Python budgets yield different scopes; `estimated_required_low > usable` → scope conflict payload; unit tests for invariants |

**Teach note:**  
**What:** The planner turns goals + real minutes into a feasible (or partially feasible) proposal.  
**How:** Deterministic code over seeded competencies — no LLM required — returning ranges and deferred topics.  
**Why:** Time-adaptive learning is a pillar; inventing mastery to fit a deadline is forbidden.

---

### S25 — Plan preview and accept UI

| Field | Value |
|---|---|
| **Title** | Show plan preview with accept creating a plan version |
| **Commit** | `feat(plan): add plan preview and explicit accept` |
| **Files/areas** | Wizard step / goal detail preview; `POST …/plans/accept`; immutable `plan_versions` + activities |
| **Acceptance** | Proposal alone does not become active; accept creates version 1; refresh shows accepted plan; rationale lists deferred items |

**Teach note:**  
**What:** AI/services propose; the learner accepts — agency is explicit.  
**How:** Separate propose vs accept endpoints; UI shows included/deferred before commit.  
**Why:** Silent plan replacement would erase trust and break the “versioned replan” promise later.

---

### S26 — Session create and resume API

| Field | Value |
|---|---|
| **Title** | Create and resume Session Studio sessions |
| **Commit** | `feat(sessions): create and resume persisted sessions` |
| **Files/areas** | `POST/GET/PATCH /sessions`, link to plan activities, pause/resume fields, append-only `session_events` with client event ids |
| **Acceptance** | Start session from accepted plan; refresh returns same progress; duplicate client_event_id does not double-apply |

**Teach note:**  
**What:** Session Studio is a resumable workspace, not a disposable chat.  
**How:** Persist session state and idempotent events so refresh never loses work.  
**Why:** Forced countdowns and lost progress punish learners; crash-safe writes are a quality attribute.

---

### S27 — Session Studio UI shell (reading activity)

| Field | Value |
|---|---|
| **Title** | Render Session Studio with reading/explanation activity |
| **Commit** | `feat(studio): render session studio reading activity` |
| **Files/areas** | `/app/learn/:sessionId`, activity renderer for reading/demo, modes stub (`guided` default), pause control |
| **Acceptance** | Opening a session shows seeded explanation content; pause persists; no punishing countdown; works offline of AI |

**Teach note:**  
**What:** Teaching starts with grounded explanation before graded claims.  
**How:** Build the Studio chrome and a reading activity type fed by `activity_versions`.  
**Why:** Session Studio is a first-class pillar — if this surface feels like a chat wrapper, the product identity slipped.

---

### S28 — Practice question activity + submit attempt

| Field | Value |
|---|---|
| **Title** | Add objective question activity and attempt submit |
| **Commit** | `feat(studio): add question activity and attempt submit` |
| **Files/areas** | MCQ or short-answer renderer; `POST /sessions/{id}/attempts` with idempotency key; store answer snapshot |
| **Acceptance** | Submitting an answer creates an immutable attempt; retry with same idempotency key returns same result; wrong user session → denied |

**Teach note:**  
**What:** Practice without recorded attempts cannot feed the Evidence Ledger.  
**How:** Typed activity UI posts attempts with assistance level defaulting to independent unless hints were used.  
**Why:** Append-only attempts with provenance are how Dolphin refuses to confuse exposure with competence.

---

### S29 — Deterministic grading and assistance labeling

| Field | Value |
|---|---|
| **Title** | Grade closed-form items and label assisted vs independent |
| **Commit** | `feat(assess): deterministic grading and assistance labels` |
| **Files/areas** | Evaluator for MCQ/numeric/short closed-form; hint/solution endpoints that set assistance; never auto-reveal in challenge mode |
| **Acceptance** | Correct unassisted → eligible independent evidence path; after “show solution,” attempt marked assisted; unit tests for both |

**Teach note:**  
**What:** Closed-form items get deterministic eval; help changes evidence quality.  
**How:** Compare against versioned keys; record `assistanceLevel` when hints or full solutions are used.  
**Why:** Requesting a solution is allowed — but it must not silently count as independent demonstration.

---

### S30 — Independent check and Evidence Ledger update

| Field | Value |
|---|---|
| **Title** | Issue independent check and update competency evidence |
| **Commit** | `feat(assess): independent check and evidence ledger updates` |
| **Files/areas** | After assisted help, generate/select a different seeded item; write `competency_evidence` + recompute `competency_state` facets; block retained/applied from same-session alone |
| **Acceptance** | Assisted success does not set `independently_demonstrated`; unassisted unseen item success does; Progress API reflects facets |

**Teach note:**  
**What:** Independent checks are a different item after assistance — not the same lucky MCQ twice.  
**How:** Policy code derives status facets from eligible evidence only.  
**Why:** Honest capability evidence is a non-negotiable pillar; fake % mastered is banned.

---

### S31 — Session finish summary

| Field | Value |
|---|---|
| **Title** | Finish session with honest summary payload |
| **Commit** | `feat(sessions): add finish endpoint and summary ui` |
| **Files/areas** | `POST /sessions/{id}/finish`, summary of topics, independent attempts, unresolved items, suggested review; Studio summary screen |
| **Acceptance** | Finish is idempotent; summary matches persisted attempts; incomplete session can still pause without finish |

**Teach note:**  
**What:** Ending a session should tell the truth about what was demonstrated.  
**How:** Aggregate attempts/evidence into a summary DTO and render it without celebration spam.  
**Why:** Outcomes beat screen-time metrics — the summary is where that product promise becomes visible.

---

### S32 — Review due queue API and UI

| Field | Value |
|---|---|
| **Title** | Schedule reviews and show due queue |
| **Commit** | `feat(review): due queue and review attempt flow` |
| **Files/areas** | Create `review_items` after independent success (transparent intervals); `GET /reviews/due`; Review page; `POST /reviews/{id}/attempts` |
| **Acceptance** | Independent success schedules a future due; due list shows reason; completing review updates next due; assisted path does not falsely extend intervals |

**Teach note:**  
**What:** Distributed practice needs a due queue separate from the initial session.  
**How:** Transparent staged intervals (not branded FSRS unless truly integrated) plus review attempts.  
**Why:** Same-session success is not retention — delayed checks are how we earn the `retained` facet later.

---

### S33 — Home dashboard from real data

| Field | Value |
|---|---|
| **Title** | Build Home next-action dashboard from live data |
| **Commit** | `feat(home): next action goals reviews and evidence snapshot` |
| **Files/areas** | `/app` Home: primary next action, active goals + feasibility note, due reviews, recent independent evidence, Quick Learn entry; empty state → create goal |
| **Acceptance** | After Prove Loop data exists, Home shows real next session/review — not placeholders; no streak counters |

**Teach note:**  
**What:** Home is the centralized learning hub — the default “what now?” surface.  
**How:** Query goals, plans, due reviews, and recent evidence for the signed-in user.  
**Why:** Without a truthful hub, Dolphin collapses into a planner or a chat toy; Home holds the three pillars together.

---

### S34 — Progress (Evidence Ledger) view

| Field | Value |
|---|---|
| **Title** | Show Progress facets without fake mastery percent |
| **Commit** | `feat(progress): evidence ledger progress view` |
| **Files/areas** | `/app/progress`, `GET /progress` projection: exposed / practicing / independently_demonstrated / unassessed; assistance distinction |
| **Acceptance** | UI never shows a single global “% mastered”; facets match DB evidence; empty state explains unassessed gaps |

**Teach note:**  
**What:** Progress is an Evidence Ledger view, not a gamified scoreboard.  
**How:** Project competency facets and recent independent results into an accessible page.  
**Why:** Fake precision trains the wrong instincts; honest gaps keep agency and trust.

---

### S35 — Goal detail path overview

| Field | Value |
|---|---|
| **Title** | Show goal path with session cards and deferred topics |
| **Commit** | `feat(goals): path overview with feasibility and sessions` |
| **Files/areas** | `/app/goals/:goalId` ordered activities, labels (prereq / demonstrated / deferred), “Why this next?”, link into Studio |
| **Acceptance** | Accepted plan renders; deferred competencies visible; continue CTA opens/resumes correct session |

**Teach note:**  
**What:** Learners need to see the path and what was cut for time.  
**How:** Render plan activities with status labels from evidence + plan version.  
**Why:** Scope conflict only builds trust when deferred work stays visible beside what fits.

---

### S36 — Replan seam (tiny prep, no Vault)

| Field | Value |
|---|---|
| **Title** | Add explicit replan endpoint stub wired to new plan version |
| **Commit** | `feat(plan): add replan endpoint creating new plan version` |
| **Files/areas** | `POST /goals/{id}/replan` using current budget + evidence; keeps old versions; UI entry “update plan” on goal detail |
| **Acceptance** | Replan after budget edit creates version N+1; prior attempts untouched; accept still required if using proposal flow |

**Teach note:**  
**What:** Availability changes must produce a new plan version, not silent mutation.  
**How:** Re-run the deterministic planner; retain history; optional preview/accept if already built.  
**Why:** This is a tiny Phase 1A seam for Time Intelligence — not Vault/RAG — so later deadline edits do not rewrite evidence.

---

### S37 — E2E: 120-minute Python Quick Learn

| Field | Value |
|---|---|
| **Title** | Automate E2E-01 beginner Python Quick Learn |
| **Commit** | `test(e2e): cover 120-minute python quick learn prove loop` |
| **Files/areas** | Playwright (or equiv) journey: auth → goal → plan ≤ 120 min → Studio → independent check → evidence visible on Home/Progress |
| **Acceptance** | Test passes against seeded DB without AI key; activities allocated ≤ 120 minutes |

**Teach note:**  
**What:** Golden scenario E2E-01 proves the vertical slice for a short Python goal.  
**How:** Drive the browser through the real UI and assert evidence side effects.  
**Why:** Unit tests cannot catch broken wiring between wizard, planner, Studio, and Home.

---

### S38 — E2E: two-week math × 30 minutes/day

| Field | Value |
|---|---|
| **Title** | Automate E2E-02 math availability windows |
| **Commit** | `test(e2e): cover two-week math thirty-minute days` |
| **Files/areas** | E2E using weekly windows; asserts usable minutes counting; review/checkpoint appears where seeded |
| **Acceptance** | Plan uses eligible windows only (not “14×24h”); test passes without AI key |

**Teach note:**  
**What:** Journey budgets must count real windows, not calendar folklore.  
**How:** Automate the 2-week × 30 min/day math path from the design’s golden table.  
**Why:** This locks Time Intelligence behavior before we add richer replanning or Vault.

---

### S39 — Cross-user isolation and refresh resilience tests

| Field | Value |
|---|---|
| **Title** | Test IDOR denial and mid-session refresh resume |
| **Commit** | `test: add ownership isolation and session refresh coverage` |
| **Files/areas** | API tests User B vs A goals/sessions/attempts; E2E refresh mid-lesson without duplicate attempts |
| **Acceptance** | Cross-user fetches denied; refresh resumes; duplicate submit prevented (E2E-09 / E2E-12 spirit) |

**Teach note:**  
**What:** Privacy and durability are part of Done, not stretch goals.  
**How:** Explicitly attack IDOR paths in tests and refresh Studio mid-flow.  
**Why:** Learning data is sensitive; Prove Loop exit requires no private route leaks and no lost work on refresh.

---

### S40 — Phase 1A demo checklist + status update

| Field | Value |
|---|---|
| **Title** | Document Prove Loop demo script and mark Phase 1A exit |
| **Commit** | `docs: record phase 1a prove loop demo and status` |
| **Files/areas** | `docs/design/04-implementation-status.md`, short demo script in README or `docs/`; known limitations (no Vault/AI/sandbox) |
| **Acceptance** | Status file lists Phase 1A working journey, exact test commands/results, and next phase = 1B (not Vault unless chosen later) |

**Teach note:**  
**What:** Stop and demonstrate before boiling the ocean.  
**How:** Write the demo path and paste real test output into the status tracker.  
**Why:** The master design forbids starting RAG, conversational spectacle, or code execution until the Prove Loop is real.

**Phase 1A exit checklist:** sign in → goal → feasible plan → Session Studio → independent check → Evidence Ledger → review due → Home/Progress; seeded path works with AI disabled; E2E-01 and E2E-02 green; ownership tests green.

---

## Stop line

Do **not** continue into Phase 1B / 2A (Vault, RAG, tutor gateway spectacle, code sandbox, projects) until Phase 1A is demonstrated and `implementation-status.md` says so.

Tiny seams allowed only as listed (e.g. S36 replan, honest Library empty state). No upload pipelines, embeddings, or in-process code execution in this plan.

---

## Step index

| ID | Phase | Title |
|---|---|---|
| S01 | 0 | Create Dolphin monorepo folder layout |
| S02 | 0 | Document install story and `.env.example` |
| S03 | 0 | Add local Postgres via Docker Compose |
| S04 | 0 | Boot FastAPI with `/health` |
| S05 | 0 | Boot Next.js TypeScript web shell |
| S06 | 0 | Add Clear Depth CSS variables and fonts |
| S07 | 0 | Define shared error envelope and `/api/v1` prefix |
| S08 | 0 | Wire SQLAlchemy 2 + Alembic empty migration chain |
| S09 | 0 | Add lint/type/test scripts for web and API |
| S10 | 0 | Integrate managed OIDC/auth and map `auth_subject` |
| S11 | 0 | Add sign-in page and protect `/app` routes |
| S12 | 0 | Add profile preferences (`GET/PATCH /me`) |
| S13 | 0 | Add adult enrollment gate and privacy notice |
| S14 | 0 | Migrate domains, competencies, and edges |
| S15 | 0 | Migrate goals and time_budgets |
| S16 | 0 | Migrate plans sessions activities attempts evidence review |
| S17 | 0 | Seed reviewed Python and math competencies + activities |
| S18 | 0 | Ship Learn / Review / Library / Progress nav with honest empty states |
| S19 | 0 | Add API + browser smoke tests for auth shell |
| S20 | 1A | Implement create/list/get goals API |
| S21 | 1A | Attach and validate time budgets on goals |
| S22 | 1A | Build goal wizard: objective, availability, priority |
| S23 | 1A | Add skippable diagnostic sample for a goal |
| S24 | 1A | Propose plans from budget, prereqs, and effort ranges |
| S25 | 1A | Show plan preview with accept creating a plan version |
| S26 | 1A | Create and resume Session Studio sessions |
| S27 | 1A | Render Session Studio with reading/explanation activity |
| S28 | 1A | Add objective question activity and attempt submit |
| S29 | 1A | Grade closed-form items and label assisted vs independent |
| S30 | 1A | Issue independent check and update competency evidence |
| S31 | 1A | Finish session with honest summary payload |
| S32 | 1A | Schedule reviews and show due queue |
| S33 | 1A | Build Home next-action dashboard from live data |
| S34 | 1A | Show Progress facets without fake mastery percent |
| S35 | 1A | Show goal path with session cards and deferred topics |
| S36 | 1A | Add explicit replan endpoint stub wired to new plan version |
| S37 | 1A | Automate E2E-01 beginner Python Quick Learn |
| S38 | 1A | Automate E2E-02 math availability windows |
| S39 | 1A | Test IDOR denial and mid-session refresh resume |
| S40 | 1A | Document Prove Loop demo script and mark Phase 1A exit |
