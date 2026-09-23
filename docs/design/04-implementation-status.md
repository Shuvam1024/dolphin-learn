# Dolphin Implementation Status

- **Last updated:** September 23, 2026
- **Milestone completed:** S01–S50; **S51** verification harness (Phase 2 foundations started)
- **Verified working user journey:** Study minutes, evidence facets, domain picker, and prove loop remain. S51 adds axe baseline, API/page perf budgets, and the design review checklist.
- **Implemented modules/features:** Prior S01–S50 surface plus harness: `@axe-core/playwright` baseline, Playwright perf project on `next start :3100`, API p95 budget tests (`DOLPHIN_PERF=1`), `docs/design/design-review-checklist.md`, Makefile `a11y`/`perf`/`check`, CI job `perf-a11y`.
- **Stubbed or unavailable features:** Vault, RAG, tutor gateway, sandbox. AI FakeProvider arrives in S56. Axe still records contrast findings (baseline only until later gates require zero).
- **Schema/API changes:** Alembic through `0009_goal_domain_key` (unchanged in S51)
- **Tests run and exact results (S51):**
  - `DOLPHIN_PERF=1 pytest tests/perf -s` → 6 passed; p95 home 55.8ms, progress 5.6ms, reviews/due 42.0ms, overview 24.8ms, session 8.8ms, plan-proposals 8.2ms (budget 250ms)
  - `pytest -q` (AI off) → 53 passed, 6 skipped (perf without flag)
  - `playwright test e2e/a11y.spec.ts` → 1 passed; wrote `e2e/a11y-baseline.json` with 13 serious/critical (mostly color-contrast)
  - `playwright test -c playwright.perf.config.ts` → 1 passed; sample TTFB/DCL/LCP well under 800/1500/2500ms
  - `ruff` / `mypy` / `tsc` / `vitest` clean
- **Known bugs/security/accessibility concerns:** Axe baseline lists color-contrast on kickers (seafoam) — cleared in S52 contrast pass.
- **Build plan:** `docs/design/06-first-ship-plan.md` (S51–S105)
- **Completed steps:** **S01–S51**
- **Next step:** **S52 — UI kit on Clear Depth**

Design package SoT: `docs/design/`. This file is the live tracker; `docs/implementation-status.md` mirrors it.

---

## Milestone checklist

| Phase | Milestone | Status |
|---|---|---|
| 0 | Foundation (S01–S19) | Done |
| 1A | Prove Loop (S20–S40) | Done |
| 1B | Delayed retention (S41–S42) | Done |
| 1C | Physical study time (S43–S46) | Done |
| 1D | Honest demo content (S47–S50) | Done |
| 2 | Foundations (S51–S58) | In progress (S51) |
| Later | Phases 3–7 per first-ship plan | Later |

---

## Step log

| Step | Commit | Acceptance |
|---|---|---|
| **S01** | `chore: scaffold dolphin monorepo layout` | Layout present |
| **S02** | `docs: add README and env example for local setup` | README + env template |
| **S03** | `chore: add docker-compose postgres for local infra` | Compose healthy + psql ping |
| **S04** | `feat(api): add fastapi app with health check` | `GET /health` → 200 JSON |
| **S05** | `feat(web): scaffold next.js typescript app shell` | `tsc` clean; placeholder HTTP 200 |
| **S06** | `feat(web): add clear depth tokens and brand fonts` | Tokens + Syne/Manrope/Plex; light theme |
| **S07** | `feat(api): standardize v1 prefix and error envelope` | Unknown route and validation errors use the envelope |
| **S08** | `feat(api): bootstrap sqlalchemy and alembic` | `alembic upgrade head`; session `SELECT 1` |
| **S09** | `chore: add lint typecheck and test runners` | `make` web + API lint/type/test exit 0 |
| **S10** | `feat(api): integrate managed auth and user subject mapping` | Valid test token resolves one user; missing token → 401 |
| **S11** | `feat(web): add sign-in and protect app shell routes` | Anonymous `/app` redirects; sign-in loads `/app`; logout clears the session |
| **S12** | `feat(identity): add learner profile and preferences endpoints` | Owner can read/update prefs; another user's id cannot be patched |
| **S13** | `feat(web): add adult age-gate and privacy notice` | Goal page blocked until acknowledgment; acknowledgment survives refresh |
| **S14** | `feat(db): migrate domains competencies and edges` | Unique keys; self-loop and bad edge type fail |
| **S15** | `feat(db): migrate goals and time budgets` | Goal requires user; negative minutes rejected |
| **S16** | `feat(db): migrate plans sessions attempts evidence review` | Upgrade head; models import; ownership FKs present |
| **S17** | `feat(seed): add python and math mini curricula` | Python and math paths; reading and objective items |
| **S18** | `feat(web): add p0 nav shell with honest empty states` | Four primary nav items; Library has no upload; Home asks for a goal |
| **S19** | `test: add phase 0 auth and health smoke tests` | Health 200; anonymous `/app` blocked; signed-in shell loads |
| **S20** | `feat(goals): add create list and get goal endpoints` | Owner creates, lists, and reads a goal; another user gets 404; empty title or request is 422 |
| **S21** | `feat(goals): validate and store time budgets` | Negative minutes and double-counted modes rejected; 120-minute and 14×30 budgets stored |
| **S22** | `feat(web): add accessible goal and availability wizard` | Keyboard-only save persists goal and budget; back keeps fields; phone width usable |
| **S23** | `feat(goals): add optional diagnostic start and attempts` | Skip or answer 3–8 items; incomplete sample can be continued; no mastery claim |
| **S24** | `feat(plan): add deterministic feasibility plan proposal` | 15- and 120-minute Python budgets differ; over-budget returns a scope conflict; no plan row yet |
| **S25** | `feat(plan): add plan preview and explicit accept` | Preview is not active; accept creates version 1; refresh returns it; rationale lists deferred items |
| **S26** | `feat(sessions): create and resume persisted sessions` | Start from an accepted plan; refresh keeps progress; duplicate client event id does not double-apply |
| **S27** | `feat(studio): render session studio reading activity` | Seeded explanation shows; pause persists; no countdown; no AI |
| **S28** | `feat(studio): add question activity and attempt submit` | Immutable attempt; same idempotency key returns the same result; other user denied |
| **S29** | `feat(assess): deterministic grading and assistance labels` | Unassisted correct is eligible; after show-solution the next attempt is assisted |
| **S30** | `feat(assess): independent check and evidence ledger updates` | Assisted success is not independent demonstration; an unseen item can be; Progress shows facets |
| **S31** | `feat(sessions): add finish endpoint and summary ui` | Finish is idempotent; summary matches stored attempts; pause does not finish |
| **S32** | `feat(review): due queue and review attempt flow` | Independent success schedules a future due; due list shows a reason; assisted review does not extend the interval |
| **S33** | `feat(home): next action goals reviews and evidence snapshot` | Home shows the real next session or review; empty state still asks for a goal; no streak counter |
| **S34** | `feat(progress): evidence ledger progress view` | Facets match stored evidence; unassessed gaps stay visible; no global mastery percent |
| **S35** | `feat(goals): path overview with feasibility and sessions` | Accepted plan renders; deferred competencies stay visible; continue opens the right session |
| **S36** | `feat(plan): add replan endpoint creating new plan version` | Budget edit then replan writes version N+1; older versions and attempts stay; proposals still do not write a version |
| **S37** | `test(e2e): cover 120-minute python quick learn prove loop` | Browser journey accepts a plan whose activities fit in 120 minutes, then shows independent evidence on Home and Progress |
| **S38** | `test(e2e): cover two-week math thirty-minute days` | Usable minutes are 14×30, not 14×24h; the seeded fraction question appears in Studio |
| **S39** | `test: add ownership isolation and session refresh coverage` | Another user gets 404; refresh keeps the lesson; the same idempotency key does not add an attempt |
| **S40** | `docs: record phase 1a prove loop demo and status` | Demo script plus exact Phase 1A test results; next phase is 1B, not Vault |
| **S41** | `feat(assess): award retained only after a due review` | Due independent review sets retained; same-session, early, and assisted reviews do not |
| **S42** | `feat(progress): show retained facet from delayed review` | Home and Progress name retained; neither shows a mastery percent |
| **Plan** | `docs: plan physical study time as phase 1c` | S43–S46 measure active minutes, show them beside the budget, replan the remainder, snooze by hours |
| **Subjects** | `docs: prioritize computing subjects first` | Early demos may use computing seeds; not a required CS→SE→ML learner path |
| **Path** | `docs: keep the core subject-agnostic on the way to any field` | The clock, ledger, and graph stay shared for any subject |
| **Focus** | `docs: treat computing as demo focus not a learner path` | Product stays for anything; CS/SE/ML are build priority for demos only |
| **1D plan** | `docs: plan phase 1d honest demo content on shared core` | S47–S50: explicit domain, deeper Python check, software domain, wizard picker |
| **Quality** | `docs: judge each step by learning quality and usability` | Content, technique, time fit, and plain use are part of done, not a later polish pass |
| **S43** | `feat(sessions): measure active study minutes excluding pauses` | Pause gaps are excluded; finish freezes the total; Studio says the clock stops when you pause |
| **S44** | `feat(progress): show studied minutes beside the usable budget` | 14×30 stays 420 usable; studied minutes match the clock; no percent and no date |
| **S45** | `feat(plan): replan from minutes remaining after study` | 30 studied on 420 replans at 390; budget row stays; evidence untouched |
| **S46** | `feat(review): snooze a due item for a duration without retention` | Hours move due time only; interval and evidence stay; Not now is not memory |
| **S47** | `feat(goals): require an explicit domain for plans` | Domain stored on goal; GET /domains; cooking is not Python; wizard picks a subject |
| **S48** | `feat(seed): add python conditionals with real checks` | Conditionals lesson with reading + graded items; short plans defer it |
| **S49** | `feat(seed): add software practice mini curriculum` | software domain on shared ledger; plans only software competencies |
| **S50** | `feat(web): pick a domain in the goal wizard` | Subject required; software e2e is not Python; copy says more subjects come later |
| **S51** | `test: add axe, perf budget, and design review checklist harness` | Axe baseline, API/page budgets, checklist, Makefile a11y/perf/check, CI perf-a11y |
