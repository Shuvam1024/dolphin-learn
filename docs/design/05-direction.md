# 05 — Direction

**Product:** Dolphin  
**Document role:** The product we are actually building, the next phase, and the phases after it  
**Last updated:** September 23, 2026

Earlier notes called some choices “locks.” They are not. This file is the current judgment. `03-build-plan.md` is the only sequential build list. When they disagree, this file decides the product and the build plan decides the next commit.

---

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

Do not special-case computing in the planner, the clock, or the ledger. Known seam: a goal that names neither the seeded Python domain nor math is still planned as Python. Remove that silent default as soon as domain selection is honest.

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

Phase 1C is finished. The next numbered steps deepen honest demo content without turning Dolphin into a computing-only school.

---

## Next phase (build this)

**Phase 1D — Honest demo content on the shared core.** Done (S47–S50).

**Next: Phase 1E — Scope, same evidence** (write numbered steps when starting).

| Step | Commit | Done when |
|---|---|---|
| S47 | `feat(goals): require an explicit domain for plans` | No silent Python; goal stores `domain_key`; unknown domain is 422 |
| S48 | `feat(seed): add python conditionals with real checks` | New competency with reading + graded items; planner can include or defer it |
| S49 | `feat(seed): add software practice mini curriculum` | `software` domain plans its own competencies on the shared ledger |
| S50 | `feat(web): pick a domain in the goal wizard` | Learner chooses a seeded domain; software e2e is not Python |

Phase 1C (S43–S46) is done.

## Later phases

These are build order, not a learner’s required path. Write numbered steps only when starting the phase.

**Phase 1E — Scope, same evidence.** A priority (understand, apply, or go deeper) may drop topics from the plan. It must not change what “retained” means. “How close” is a count of unassessed topics, deferred topics, and due reviews. Never a percent.

**Phase 1F — A tutor that cannot grade.** Optional model for hints and explanations. Seeded lessons still run with no key. The evidence writer stays the deterministic grader.

**Phase 2A — A programming lab (first activity adapter).** Learner code runs outside the API process, with no credentials and no path to another user’s data. Passing tests can support an attempt. The model does not award the facet by itself. Other subjects will add their own adapters later; the ledger stays shared.

**Phase 2B — Knowledge Vault.** Private files. Ownership is checked before any retrieval. Answers that come from a file cite a span the learner can open. Uploads are untrusted. Nothing is redistributed to other people.

**Phase 2C — Transfer.** A task that is meaningfully new can set `applied`. Repeating the lesson cannot.

**After that.** More domains and activity types on the same platform — whatever people ask to learn, as soon as we can teach and check it honestly. Deeper accessibility. A community only with moderation and privacy. Younger learners only as a separate reviewed product. A fancier review scheduler only after these plain durations have real data.

---

## What this product will not do

- Invent scale, latency, or coverage numbers to sound finished.
- Treat streaks, messages, or time-on-page as learning.
- Diagnose learning styles.
- Claim every subject is fully assessed.
- Split into a microservice fleet before the learning loop needs it.
- Let a model both teach and record proficiency.
