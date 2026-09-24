# Dolphin learning log

Teach notes for each sequential build step (what / how / why). The product is **Dolphin**.

**Status of this file:** S01–S57 notes live in the long-form log kept with the team store. This in-repo log holds **S58 onward**. The step index, test results, and “next step” line live only in [`design/04-implementation-status.md`](design/04-implementation-status.md).

Do not duplicate the first-ship plan here.

---

## How to append

After each completed step, add a heading `## Snn — <title>` with commit hash, what/how/why, and the named tests that passed.

## Next incomplete step

**S59 — Studio v2 renderer** in [`design/06-first-ship-plan.md`](design/06-first-ship-plan.md).

---

## S58 — Gate 2: foundations

**Commit:** PENDING — docs: phase 2 foundations verified; content model, ai gateway, and studio contract in architecture

**What:** Phase 2 foundations are verified end-to-end: harness, UI kit, copy, activity types, content files, AI gateway, and Studio payload. Architecture and brand docs now describe those pieces.

**How:** Ran the full suite with AI off and with FakeProvider; validated content; recorded axe baseline by route and API/page perf budgets; updated e2e specs that still expected raw keys or pre-S55 lesson wording; updated `02-architecture.md` (content files/rules, activity provenance, gateway hygiene, studio contract) and `brand.md` (kit + copy notes).

**Why:** A phase gate locks what is true before Studio v2 builds on it.

**Acceptance:** passed — AI off/fake 81 passed + 6 skipped; content ok; smoke 22 passed; axe baseline 13 by route; API p95 under 250ms; page LCP under budget; docs updated.

**Push:** PENDING
