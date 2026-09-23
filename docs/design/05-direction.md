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

## First subjects

The product can hold any subject. The first ones we actually build are computing:

1. Computer science and programming. The Python lessons already seeded are the start, not a toy on the side.
2. Software engineering: reading code, finding a bug, writing a test, finishing a small program.
3. AI and machine learning, only after the computing and mathematics those topics require.

Mathematics is included when a computing topic needs it. The fractions lesson is that kind of support. It is not a decision to build a general math, language, music, or trades product next.

Other subjects use this same ledger and this same minute clock when they come. They do not skip ahead of the computing path.

---

## Next phase (build this)

**Phase 1C — Physical study time. S43, then S44, then S45, then S46.**

| Step | Commit | Done when |
|---|---|---|
| S43 | `feat(sessions): measure active study minutes excluding pauses` | A pause gap is excluded; finish freezes the total |
| S44 | `feat(progress): show studied minutes beside the usable budget` | 14×30 still shows 420 usable; studied minutes are the measured sum; no percent and no date |
| S45 | `feat(plan): replan from minutes remaining after study` | 30 studied on a 420 budget replans at 390; the budget row stays 420; evidence is untouched |
| S46 | `feat(review): snooze a due item for a duration without retention` | Hours move the next check only; interval and evidence stay |

Do not start Vault, RAG, a tutor, or a sandbox in this phase. Do not add a deadline date.

---

## Later phases (do not start until 1C is finished)

These are the order, not a ticket list. Write numbered steps only when the previous phase is done.

**Phase 1D — Computing curriculum.** More computer science, then software engineering, then machine learning. Each topic is a competency with a real check. Math is added only as a prerequisite. No second app, and no claim that every field is covered.

**Phase 1E — Scope, same evidence.** A priority (understand, apply, or go deeper) may drop topics from the plan. It must not change what “retained” means. “How close” is a count of unassessed topics, deferred topics, and due reviews. Never a percent.

**Phase 1F — A tutor that cannot grade.** Optional model for hints and explanations. Seeded lessons still run with no key. The evidence writer stays the deterministic grader.

**Phase 2A — A programming lab.** Learner code runs outside the API process, with no credentials and no path to another user’s data. Passing tests can support an attempt. The model does not award the facet by itself. This comes before a general file vault because the first learners are writing programs.

**Phase 2B — Knowledge Vault.** Private files. Ownership is checked before any retrieval. Answers that come from a file cite a span the learner can open. Uploads are untrusted. Nothing is redistributed to other people.

**Phase 2C — Transfer.** A task that is meaningfully new can set `applied`. Repeating the lesson cannot.

**After that.** Subjects outside computing, on the same ledger, not new apps. Deeper accessibility. A community only with moderation and privacy. Younger learners only as a separate reviewed product. A fancier review scheduler only after these plain durations have real data.

---

## What this product will not do

- Invent scale, latency, or coverage numbers to sound finished.
- Treat streaks, messages, or time-on-page as learning.
- Diagnose learning styles.
- Claim every subject is fully assessed.
- Split into a microservice fleet before the learning loop needs it.
- Let a model both teach and record proficiency.
