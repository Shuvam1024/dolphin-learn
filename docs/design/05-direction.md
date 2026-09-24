# 05 — Direction

**Product:** Dolphin  
**Document role:** The product we are actually building, the next phase, and the phases after it  
**Last updated:** September 24, 2026

Earlier notes called some choices “locks.” They are not. This file is the current judgment. `03-build-plan.md` (S01–S50) and `06-first-ship-plan.md` (S51–S105) are the only sequential build lists. When they disagree, this file decides the product and the build plan decides the next commit.

---

## The final vision (center of every decision)

The learner can **learn anything they want**, keep their learning **organized in one place**, get **real learning content, technique, and performance**, and have Dolphin **adapt to the task and the time they actually have**. The interface stays **clean and easy to use**; most of the machinery is **behind the scenes** — and that machinery is the **adaptive tutor**: it explains differently and hints, drafts lessons and practice for any subject, normalizes goals, explains plans, and proposes misconception notes; the learner model calibrates effort and selects items. The **deterministic core stays the referee**: grading by key, evidence rows by the evidence writer, plans by the planner; every model output is schema- and feature-validated, labeled, and `provisional` until reviewed. Seeded content works with no key.

Every feature and every screen is judged on three questions: is it appealing, is it useful, is it easy for the learner. Honesty rules do not move (assisted ≠ independent, same-session ≠ retention, no percent, no streak guilt, active minutes not dates). They are expressed through structure — chips, deferred lists, minutes — not through caveats on every line.

## Where we stand after S50 (assessment, September 23, 2026)

The machinery is real and tested: minutes measured, plans fit the budget, help labeled, retention earned from a due review, ownership enforced (53 pytest, 19 Playwright). The learner-facing surface is not yet a product: one sign-in card style on every route; raw keys (`python.names`, `insufficient_minutes`) as visible vocabulary; seven thin competencies with one to three multiple-choice items; a subject picker that refuses anything not seeded; a Learn tab that is a dead end; honesty rules rendered as disclaimers; a priority control that changes nothing; a stored session length that is never read; no accessibility or performance harness; dev-only sign-in.

The gaps, in order: (1) “learn anything” stops at a dropdown, (2) content is demo-thin, (3) time is measured but not felt inside a sitting, (4) the surface leaks the machinery, (5) no place where learning is organized, (6) not shippable to strangers. `06-first-ship-plan.md` spends S51–S105 on exactly those, in that order of dependency, with a verification gate between phases.

---

## Where we stand after Gate 7 / v0.1 RC (September 24, 2026)

Phase 7 is verified through the golden release suite and RC record. Settings, managed auth, export/delete, edge hardening, containers, observability, and the release suite are on `main`. Next is **S105 — tag v0.1.0**.

## Where we stand after Gate 6 (September 24, 2026)

Phase 6 is verified. Effort estimates calibrate from measured active minutes; item selection uses difficulty and history with logged reasons; every prompt has a safety eval suite; product events and dataset views record what future estimators would need — without storing answers or emails.

Next is **Phase 7 — Account, trust, release** (S96) — complete through S104 RC; ship with S105.

## Where we stand after Gate 5 (September 24, 2026)

Phase 5 is verified. The General route accepts any subject with learner-owned outcomes; placement proposes skips the learner confirms; the goal normalizer and wizard v2 guide creation; provisional outlines and item drafts stay under review; checked subjects are deep enough for real sittings; content CI publishes an audit with zero errors.

## The product

Dolphin is one learning home. A person can learn any subject they can describe, at whatever real time they have, and the product keeps a record of what they can do without help.

Personalization changes the route: which topics fit, how a session is presented, how much guidance they asked for. It does not lower the evidence required to say they can do the thing.

Four facts stay separate:

| Fact | Meaning |
|---|---|
| Exposed | They met the material. |
| Practicing | A correct answer came after help. |
| Independently demonstrated | A correct answer on an unseen check, with no help. |
| Retained | A later review, already due, was answered with no help. |

`applied` waits until a task is actually new, not a repeat of the lesson. There is no global mastery percent and no streak.

A tutor, when one exists, may explain. It does not write those rows. If the screen cannot observe a skill — playing an instrument, a clinical procedure, a license — the product says it cannot observe it.

Adults first. A younger audience needs its own privacy and safety design, not a checkbox on this one.

---

## Time is physical

Study time is measured in minutes the learner was actually in an active session.

- The clock runs from the start of a session until pause, and from resume until the next pause or finish.
- Time away is not study. Overnight gaps are not study. A calendar date is not study.
- A budget is a quantity of study minutes. “30 minutes on each of 14 sittings” is 420 minutes. It is not a due date, and it is not 14 × 24 hours.
- A review wait is a duration until the next retrieval. Spacing needs that wait. The wait is not study, and it does not increase the budget.
- There is no goal deadline field. Someone preparing for an exam tells Dolphin how many minutes they can study. The plan includes what fits and names what does not.

---

## Demo content focus (not a learner path)

The end product is for **anything** a person wants to learn. The learner’s order is their goal, their minutes, and their evidence — never a fixed sequence we invent for them.

What we seed first for demos and deep checks is computing-related material, because we can teach and grade it well on a screen right now:

- Computer science and programming (Python lessons already seeded are a start).
- Software engineering habits: reading code, finding a bug, writing a test, finishing a small program.
- AI and machine learning topics, when we can attach real checks and the math those topics need.

That list is a **build and demo priority**. It is not the curriculum every user must walk. Someone can ask for fractions, writing, or another field that already has honest content. Someone can skip straight into a later computing topic if the plan and checks support it.

Mathematics shows up when a goal needs it (the fractions lesson is that kind of support). Other fields use the same goals, minute clock, competency graph, sessions, evidence ledger, and reviews. A new field is more curriculum data and activity types, not a second app.

Do not special-case computing in the planner, the clock, or the ledger. The silent Python default was removed in S47; the next honesty step is the **General route** (S76): any subject the learner names, taught with the technique that works everywhere — read, recall without looking, self-rate, review later — recorded as self-reported evidence that never becomes “independently demonstrated.”

---

## Path to the end

The end is one platform: any subject, any adult learner, any amount of real study time, and a record of what they can do without help.

What we build now is the core every later subject will use. It does not belong to Python or to any one career track.

- Goals, minute budgets, the competency graph, sessions, the evidence ledger, and reviews are the same for every subject.
- A subject is data: a domain, competencies, edges, and activities. A later field is another seed, not another application.
- Demo content may be computing-heavy for a while. The session clock, the ledger, and the planner rules do not special-case it.
- When a skill cannot be observed on screen, the product says so instead of inventing mastery.

The programming lab and the Knowledge Vault, when they arrive, are adapters on this core. The lab is useful for early demos where people write programs. It is not the only activity type the ledger can hold. A later subject brings its own activities and the same evidence facts.

Scale means new subjects and new checks plug in. It does not mean a service per field, and it does not mean rewriting the clock or the ledger when the second subject shows up.

---

## What every step has to be good at

Two things decide whether a step is done. Neither one is a polish pass at the end.

**The learning itself.** Content, technique, and time have to help a person get better at the thing.

- A lesson, a practice item, and a check should teach the skill. A correct endpoint with thin or confusing material is not finished.
- Technique stays visible. The learner tries, help is labeled as help, a later check is a different question, and a review waits long enough to mean something.
- Time adaptivity is felt, not only stored. The plan fits the minutes they actually have. The clock matches time they were studying. A shorter budget changes what fits. It does not lower what “you can do this” means.

**The person using it.** Usability is part of the same step.

- They can tell what to do next, what a result means, and what happens if they pause, ask for help, or leave.
- The words are about their study. Internal names can appear only when a plain sentence is next to them.
- Keyboard use, a phone-width screen, and the path through sign-in stay intact.
- The app should feel quick in a study session. That is responsiveness a person notices, not a made-up benchmark.

A third bar joins those two for the first ship: **the surface itself**. Tokens only; one primary action per screen; no raw keys, ids, reason codes, or version numbers as learner copy; at most one explanatory sentence per screen (definitions live in Help); loading, empty, and error states present. This is the design review checklist created in S51 and applied at every gate.

Phases 0–1D (S01–S50) are finished.

---

## Next: the first-ship plan (build this)

**`06-first-ship-plan.md`, S51–S105.** Six phases, each closed by a verification gate (full test suite green with the tutor off and with the fake provider; axe zero serious/critical on every route; API p95 and page budgets met and recorded; tutor evaluation fixtures pass; design review checklist per screen; design docs updated).

| Phase | Steps | What the learner gets |
|---|---|---|
| 2 — Foundations | S51–S58 | Done — harness, UI kit, names not keys, activity-type model, content files, model gateway, Studio payload contract |
| 3 — The learning session | S59–S70 | **Done (Gate 3)** — Studio for every activity type; feedback; worked examples; unseen pools; typed answers; free recall ceiling; tutor explain/hints; misconception notes and recall compare; sitting size; stop point; summary v2; ai-eval |
| 4 — Organized in one place, adaptive to time | S71–S80 | **Done (Gate 4)** — priority shapes plans; Home v2; Learn shelf; mobile tabs; path + replan preview; plan explainer; Progress by goal; reviews with what fits; wizard preview |
| 5 — Learn anything | S81–S90 | **Done (Gate 5)** — General route; placement; goal normalizer; wizard v2; provisional outlines; item drafts; deep Python/math/software; content audit |
| 6 — Learner model and adaptivity | S91–S95 | **Done (Gate 6)** — effort EMA; difficulty/history item selection; ai-eval safety suite; product events + dataset views |
| 7 — Account, trust, release | S96–S105 | Settings (incl. tutor on/off); managed sign-in for production; export and delete; security headers and rate limits; containers and a runbook; logs and gateway metrics; a golden release suite run with the tutor off and fake; a release-candidate review with a live tutor evaluation; **v0.1.0** |

The earlier working labels “1E scope,” “1F tutor,” “2A lab,” “2B Vault,” “2C transfer” are superseded by this numbering. Scope-by-priority is S71; the tutor that cannot grade begins at S63 inside the learning session, not in a separate phase.

## After first ship

Build order, not a learner’s required path. Write numbered steps only when starting the phase, after v0.1 feedback.

**Phase 8 — A programming lab (first activity adapter).** Learner code runs outside the API process, with no credentials and no path to another user’s data. Passing tests can support an attempt. The model does not award the facet by itself. Other subjects will add their own adapters later; the ledger stays shared.

**Phase 9 — Knowledge Vault.** Private files. Ownership is checked before any retrieval. Answers that come from a file cite a span the learner can open. Uploads are untrusted. Nothing is redistributed to other people. (Until then, the General route accepts pasted notes.)

**Phase 10 — Transfer.** A task that is meaningfully new can set `applied`. Repeating the lesson cannot.

**Phase 11 — Calibrated estimators.** Probabilistic mastery or spacing models only after validity and fairness studies on the v0.1 dataset (`v_attempt_features`, `v_review_outcomes`), and only as advice the deterministic referee can override.

**After that.** More domains and activity types on the same platform — whatever people ask to learn, as soon as we can teach and check it honestly. Deeper accessibility. A community only with moderation and privacy. Younger learners only as a separate reviewed product. A fancier review scheduler only after these plain durations have real data.

---

## What this product will not do

- Invent scale, latency, or coverage numbers to sound finished.
- Treat streaks, messages, or time-on-page as learning.
- Diagnose learning styles.
- Claim every subject is fully assessed.
- Split into a microservice fleet before the learning loop needs it.
- Let a model both teach and record proficiency. The tutor explains, hints, and drafts; the deterministic referee grades and writes evidence.
