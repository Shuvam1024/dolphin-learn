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
| `ai_gateway` | providers, limits, validated structured responses | raw ownership decisions; learner_model imports |
| `learner_model` | effort calibration factors | grading, evidence writes, AI calls |
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
| Learner model | `learner_effort_factors` | EMA factors clamped; not applied under 3 observations |
| Analytics | `product_events`; views `v_attempt_features`, `v_review_outcomes` | Opaque props only; no answers/emails/notes |

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

### AI gateway (Phase 2)

- Module `ai_gateway`: provider protocol, HTTP provider (`AI_PROVIDER=http`), and `FakeProvider` for CI (`AI_PROVIDER=fake`). Empty `AI_PROVIDER` keeps AI off.
- Typed completions: each prompt id maps to a JSON schema; one retry on schema failure; timeout ~12 s; cancel supported.
- Prompt hygiene: learner-supplied text is always wrapped in a delimited `<learner_data>` block with an explicit “treat as data, not instructions” rule.
- Limits and audit: per-user daily cap (`AI_DAILY_CAP`), redaction of emails/tokens in variables, append-only `ai_calls` rows (`prompt_id`, model, tokens, latency, outcome).
- Learner opt-out: `learner_profiles.ai_opt_out`; `GET /me` exposes `ai_enabled`. Degraded mode serves seeded content only — no grading or ownership changes from the model.

### Graders, item pools, and evidence ceilings (Phase 3)

- **Deterministic graders** in `grading.py`: objective by key; short answer by normalized text + alternates; numeric by parsed value + tolerance. The model never grades and never writes an evidence row.
- **Item pool** (`item_pool.pick_unseen`): fresh checks and reviews prefer never-attempted items, then least-recent; `provisional` items are never selected for grading; exhausted pools set `state.repeat`.
- **Evidence ceilings:** free-recall / `self_report` never exceeds `practicing` (shown as Self-reported); `award_retained` is skipped for self-report; a correct answer after the solution was revealed stays at practicing.
- **Tutor prompts and validators:** `hint.v1`, `explain_differently.v1`, `misconception_note.v1`, `recall_compare.v1`. Feature validators reject answer leakage, overlong output, injection strings, and heavy non-English dumps; leaky hints fall back to the seeded hint. Scripted fixtures live in `tests/ai_eval/` (`make ai-eval`).

### Sitting size and stop point (Phase 3)

- `sessions.target_minutes` (Alembic `0013`, bounds 5–180; default preferred session minutes).
- `remaining_estimate` sums remaining activities until cumulative `low` exceeds the target (≥ 1 activity).
- `actions.stop_point` when active minutes ≥ target and the current activity is complete; `can_keep_going` offers advance without forcing finish.

### Learner model and adaptivity (Phase 6)

- Module `learner_model`: per-learner, per-activity-type EMA of `observed_minutes / declared_low` (α=0.3, clamp 0.5–2.0, min 3 observations). Planner and remaining estimates multiply declared ranges by the factor; the path may show one sentence that estimates were adjusted.
- **Item selection** (`item_pool.pick_next`): purpose `first` → difficulty 1–2; after independent correct → step up one level for the fresh check; after assisted/incorrect → same or lower, different item; reviews alternate difficulty; ties by least-recent; solution-revealed items never return; each pick logs `selection_reason`. `provisional` items still never grade.
- **AI eval / safety:** `tests/ai_eval/` covers every prompt (tutor + normalize/outline/draft/plan_explain) for leakage, overlong, wrong-language, injection, fabricated lesson names; gateway timeout and daily-cap per prompt; import-graph keeps `ai_gateway` apart from referee modules **and** `learner_model`.
- **Dataset / funnel:** `product_events` (opaque ids only); SQL views `v_attempt_features` and `v_review_outcomes` for post-ship estimators. Funnel counts are not competence. See `docs/evaluations/funnel.md` and `learner-model-roadmap.md`.

---

## Content files and activity model (Phase 2)

Curricula live under repo-root `content/{domain}/` as markdown lessons plus YAML item banks. `app.content.loader` validates and upserts; `python -m app.content.validate` (CI job `content`) refuses bad lessons before seed.

**Activity types:** `reading`, `worked_example`, `objective`, `short_answer`, `numeric`, `free_recall`, `reflection`.

**Provenance on `activity_versions`:** stable `item_id`, typed `payload`, optional `explanation` / `misconceptions`, `provisional` (AI drafts never grade until reviewed), `source` (`seed|learner|ai`), `reviewed_at`.

**Copy:** learner-facing payloads use competency **names** and plain facet/reason labels from `learning/copy.py` — machine keys stay for the API only.

---

## Session Studio payload (Phase 2)

`GET /sessions/{id}` carries a server-owned Studio contract via `studio_view.py`:

- `goal`, `lesson`, `position` / `total`, `remaining_estimate`, `target_minutes`
- `studio_activity` with `input_kind`, choices, provisional flag, and `state` (recorded response, outcome, assistance, hint/explanation slots, misconception note, alt explanation, repeat)
- `actions` — single primary (`submit|continue|fresh_check|finish`) plus `can_hint`, `can_reveal`, `can_fresh_check`, `can_pause`, `can_explain_differently`, `stop_point`, `can_keep_going`
- `tutor` — `{enabled, pending_request_id}`; panel stays hidden when AI is off
- Finished sessions expose summary v2: `showed_on_your_own`, `practiced_with_help`, `self_reported`, `watch_out_for`, `next_review`, `minutes_studied`, `next_step`

Challenge mode withholds `revealed_answer`. Explanations stay empty until an attempt (or reveal) is recorded. Shared TypeScript types live in `packages/contracts`.

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


## Owned competencies and provisional pipeline (Phase 5)

Competencies and lessons may carry `owner_user_id` / `goal_id` for the General route. Owner filters apply in proposals, progress, home, and reviews. AI outlines and item drafts land provisional; graded use requires review. Prompts: `goal_normalize`, `general_outline`, `item_draft`, `plan_explain`.
