# 02 — Architecture

**Product:** Dolphin  
**Document role:** Stack, modules, data model highlights, API / AI / security boundaries

---

## Recommended stack

| Layer | Choice |
|---|---|
| Web | Next.js (React + TypeScript) — `apps/web` |
| API | FastAPI (Python) — `services/api` |
| Database | PostgreSQL + SQLAlchemy 2 + Alembic |
| Local infra | Docker Compose for **Postgres only** (app processes on host) |
| Auth | Managed OIDC / email auth — no custom password crypto |
| Tests | Pytest (API), Vitest/RTL + Playwright (web) |
| Later | pgvector + object storage (Vault); isolated code sandbox (Labs) |

**Pattern:** modular monolith + async workers when needed. AI calls are server-side; credentials never in the browser. Prefer deterministic services over agent autonomy.

---

## Repository tree

```text
dolphin-learn/
├── README.md
├── .env.example
├── docker-compose.yml
├── AGENTS.md
├── docs/
│   ├── design/                   # ← this package (SoT)
│   ├── dolphin-master-design.md  # slim pointer into design/
│   ├── implementation-status.md  # slim pointer into design/04
│   ├── learning-log.md           # teach notes from S58 onward
│   ├── prove-loop-demo.md
│   ├── architecture-decisions/   # reserved (empty)
│   ├── api/                      # reserved (empty)
│   └── evaluations/              # reserved until later first-ship steps
├── apps/web/
├── services/api/
│   └── app/modules/{identity,goals,curriculum,sessions,assessment,review,vault,labs,ai_gateway}/
├── packages/contracts/
└── infra/
```

Create domain modules when implementing them. OpenAPI from the API is the contract source of truth.

---

## Logical flow

```text
Accessible Web Client
        │
        ▼
Authenticated API ──► Goals & Time Planner ──► PostgreSQL
                 ├──► Session Studio / Tutor ──► PostgreSQL (+ optional model gateway)
                 ├──► Evidence Ledger ──► PostgreSQL
                 ├──► Home / Progress / Review
                 └──► Knowledge Vault (later) ──► DB + private object storage + jobs
```

---

## Module boundaries

| Module | Owns | Must not own |
|---|---|---|
| `identity` | auth mapping, preferences, access policies | prompts or score changes |
| `goals` | goals, timeframes, plan revisions | historic attempt mutation |
| `curriculum` | domains, competencies, graph, approved items | private resource visibility |
| `sessions` | Session Studio progress, messages, assistance | declaring verified retention alone |
| `assessment` | attempts, evaluator provenance, evidence derivation | LLM direct SQL writes |
| `review` | due schedule, outcomes | erasing missed history |
| `vault` | file ownership, extraction, index, retrieval permissions | sharing without authorization |
| `ai_gateway` | providers, limits, validated structured responses | raw ownership decisions |
| `labs` | activity renderers/evaluators | in-process code execution |
| `analytics` | privacy-respecting metrics | causal claims from engagement alone |

Communicate via typed services / domain events — not direct cross-module table writes.

---

## Data model highlights

Ownership enforced **server-side** on every nested id.

| Area | Tables (essentials) | Invariants |
|---|---|---|
| Identity | `users`, `learner_profiles` | Unique `auth_subject`; 1:1 profile |
| Goals | `goals`, `time_budgets`, `goal_competencies` | Owner index; one budget mode; nonnegative minutes |
| Curriculum | `domains`, `competencies`, `competency_edges` | Unique keys; no self-loops; DAG where required |
| Plans | `learning_paths`, `plan_versions`, `plan_activities` | Immutable after accept; versioned |
| Content | `lessons`, `activity_versions` | Versioned keys/rubrics; keys withheld in challenge mode |
| Sessions | `sessions`, `session_events` | Resumable; idempotent client event ids |
| Evidence | `attempts`, `evaluations`, `competency_evidence`, `competency_state` | Append-only attempts; state recomputable |
| Review | `review_items`, `review_events` | Transparent intervals; append-only history |

**Status facets (not a fake mastery %):** `not_started | exposed | practicing | independently_demonstrated | retained | applied`.

Never award `retained` / `applied` from same-session success alone.

---

## API conventions

- Version under `/api/v1`.
- Error envelope: `{ error: { code, message, details, request_id } }`.
- Proposing a plan does **not** replace the active plan until explicit acceptance.
- Idempotency keys on attempt submit and other high-impact mutations.
- Health may live at `GET /health` (documented consistently).

### Target route map (Phase 0 / 1A first)

| Area | Routes |
|---|---|
| Profile | `GET /me`, `PATCH /me/preferences` |
| Goals | `POST/GET/PATCH /goals…`, diagnostic, plan-proposals, plans/accept, replan |
| Sessions | `POST/GET/PATCH /sessions…`, attempts, finish |
| Review | `GET /reviews/due`, `POST /reviews/{id}/attempts` |
| Progress | `GET /progress` |
| Later | tutor, Vault upload/process, labs runner, export/delete |

---

## AI architecture (boundaries)

- Runtime-configured providers; typed I/O validation; per-user caps.
- AI **proposes**; the app validates and persists.
- Tutor receives only authorized profile/learning-state/source context for the current session.
- Tutor does **not** write mastery or receive unrelated account history.
- Deterministic seeded content works with AI disabled.
- Vault/RAG (later): owner filter **before** retrieval; cite verified spans only; treat uploads as untrusted.

---

## Security, privacy, safety

- Managed auth; object-level authorization; TLS; least privilege.
- **Never** give a model direct SQL, arbitrary internal URL fetch, or ownership bypass.
- **Never** execute untrusted learner code in the API process (sandbox is a later, isolated service).
- Private-by-default learning data; export/delete before calling production-ready.
- Adult-only until child/school product is designed and compliance-reviewed.
- Distinguish education from medical/legal/financial advice.

---

## Time-budget algorithm (invariants)

1. Normalize to UTC + IANA timezone; materialize local windows; handle DST.
2. Compute `usable_budget` from real windows — not “14 × 24h.”
3. Prerequisite closure; effort **ranges**; topo + greedy selection.
4. If `estimated_required_low > usable` → scope conflict payload (included vs deferred).
5. Versioned plan with rationale; on edit/miss → **new** plan version; keep evidence.

---

## Quality and tests (targets)

- Unit: budget/DST, planner invariants, grading, review, schemas.
- Integration: migrations, ownership, idempotency, Prove Loop.
- E2E golden: 120-min Python Quick Learn; 2-week math × 30 min/day; refresh resume; cross-user IDOR denial.
- Degraded-AI mode keeps seeded lessons, reviews, grading, and progress usable.

### Definition of done (per milestone)

Usable UI; real persistence; server authz; loading/empty/error; real control behavior; tests pass; docs/`.env.example` updated; privacy considered; no fake progress.
