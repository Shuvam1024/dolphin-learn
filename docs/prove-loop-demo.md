# Prove Loop demo (Phase 1A)

**Scope:** Historical Phase 1A click path. S01–S57 are on `main`; the next incomplete first-ship step is **S58 (Gate 2)** in `docs/design/06-first-ship-plan.md`. Do not treat “next phase is 1B” at the bottom as current build status.

This is the click path that shows Dolphin’s Prove Loop with seeded lessons and no AI key. Vault, retrieval, and the code sandbox are not part of this demo. Learner-facing screens now show competency **names**; machine keys such as `python.names` remain in the API.

## Before you start

Postgres is up (`docker compose up -d`). The API is on `http://127.0.0.1:8000` and the web app is on `http://127.0.0.1:3000`. Do not set `OPENAI_API_KEY`.

## What to click

1. Open `/sign-in`, enter an email, and continue. There is no password.
2. On Home, confirm you are 18 or older. Until you do, goal and studio routes stay on that gate.
3. Choose **Quick Learn**. Title the goal `Quick Learn Python` and ask to learn names and calls. Keep **120** total minutes and a preferred session of **30**. Save, then **Accept plan**. The preview includes `python.names` and `python.calls`, and nothing is deferred. Those activities fit in 120 minutes.
4. Go back to Home and start the session. Session Studio shows the names explanation, Guided mode, and “No countdown”.
5. Choose **Next activity**. Answer the names question with the choice that says the name is bound to 3. The page records `b` as independent.
6. Choose **Check a different question**. The new prompt is about `n = n + 1`. Answer that it rebinds `n` to 4. That second item is the independent check: it is not the question you just finished, and the letter was not shown first.
7. Open Home. Independent evidence lists `python.names: independently_demonstrated`. There is no streak counter.
8. Open Progress. The same facet is listed. `python.calls` stays unassessed until you attempt it. There is no mastery percent.
9. Open Review. Nothing is due today. The page names the scheduled check and says it is not retention. The first interval is one day, then 3, 7, and 14 after an independent review.
10. Optional second journey: create a goal whose title or request says fractions, choose 30 minutes a day for 14 days, and accept. Usable minutes are **420** (14 × 30), not 14 × 24 hours. Next activity shows `What is 1/4 + 2/4?`.

Finish a session from Studio when you want the summary. It lists stored attempts and does not celebrate. Pause before finish leaves the session open.

## What this does not show

- No Knowledge Vault upload, embeddings, or RAG answers.
- No conversational tutor and no model call. Seeded text and a deterministic grader only.
- No code sandbox or project workspace.
- A review scheduled from today’s independent answer is not due until tomorrow, so Home will not pretend it is due now.
- Sign-in is the dev email token. There is no password store.

## Re-run the exit checks

From `services/api`, with the virtualenv:

```bash
.venv/bin/ruff check app tests
.venv/bin/mypy app
.venv/bin/pytest --tb=no
```

Recorded on September 23, 2026: ruff `All checks passed!`; mypy `Success: no issues found in 40 source files`; pytest `41 passed, 1 warning in 2.41s`.

From `apps/web`:

```bash
npx playwright test e2e/phase0.spec.ts e2e/quick-learn.spec.ts e2e/math-windows.spec.ts e2e/refresh-resume.spec.ts --reporter=line
```

Recorded on September 23, 2026: `4 passed (10.4s)`.

Phase 1A stops here. The next phase is **1B**. It is not Vault, RAG, or the sandbox unless that is chosen later.
