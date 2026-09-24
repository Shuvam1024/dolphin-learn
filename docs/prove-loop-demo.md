# Prove Loop demo (through Gate 4)

**Scope:** Click path for the seeded Prove Loop plus Phase 3 learning-session features on `main`. Next incomplete first-ship step is **S71** in `docs/design/06-first-ship-plan.md`.

This path shows Dolphin with seeded lessons. Vault, retrieval, and the code sandbox are not part of this demo. Learner-facing screens show competency **names**; machine keys such as `python.names` remain in the API.

## Before you start

Postgres is up (`docker compose up -d`). The API is on `http://127.0.0.1:8000` and the web app is on `http://127.0.0.1:3000`. For the seeded path, leave `OPENAI_API_KEY` unset. For tutor explain/hints in CI-style mode, set `AI_PROVIDER=fake`.

## What to click

1. Open `/sign-in`, enter an email, and continue. There is no password.
2. On Home, confirm you are 18 or older. Until you do, goal and studio routes stay on that gate.
3. Choose **Quick Learn**. Title the goal `Quick Learn Python` and ask to learn names and calls. Keep **120** total minutes and a preferred session of **30**. Save, then **Accept plan**.
4. From the goal path, choose **Continue**. The sitting chooser asks how long you have — pick **15 minutes** (or your usual). Resume later never asks again.
5. Session Studio shows the names reading, “About 15 minutes,” and minutes left in this sitting — not a countdown. Continue through the **worked example** (“Now you try”), then the objective question.
6. Answer the names question with the choice that says the name is bound to 3. Feedback shows the explanation. If you ask for a hint or **Explain differently** (with AI fake on), the Tutor chip labels the text; the next answer is Assisted.
7. Optional typed check: on a short-answer or numeric item, type the answer. A wrong typed answer may show an AI misconception note labeled AI — the grade was already decided.
8. Optional free recall: write from memory while the lesson is hidden, submit, then self-rate. The chip reads Self-reported; evidence never claims independently demonstrated from this alone.
9. When active minutes reach your sitting target, Studio offers a **good place to stop** with Finish and Keep going. Finish for an honest summary: what you showed, practiced with help, self-reported, watch-outs, minutes studied, and a next step — no celebration copy.
10. Open Home and Progress for evidence facets by name. Open Review for scheduled checks (nothing due the same day from today’s independent answer).

Optional second journey: create a goal whose title or request says fractions, choose 30 minutes a day for 14 days, and accept. Usable minutes are **420** (14 × 30).

## What this does not show

- No Knowledge Vault upload, embeddings, or RAG answers.
- No code sandbox or project workspace.
- The model never grades and never writes an evidence row.
- A review scheduled from today’s independent answer is not due until tomorrow.
- Sign-in is the dev email token. There is no password store.

## Re-run the Gate 3 checks

From `services/api`:

```bash
AI_PROVIDER= .venv/bin/pytest --tb=no
AI_PROVIDER=fake AI_GATEWAY_ENABLED=1 .venv/bin/pytest --tb=no
make -C ../.. ai-eval
```

From `apps/web` (API on :8000 with current code; set `DOLPHIN_E2E_FAST_CLOCK=1` on the API for sitting stop-point e2e):

```bash
npx playwright test \
  e2e/quick-learn.spec.ts \
  e2e/math-windows.spec.ts \
  e2e/studio-v2.spec.ts \
  e2e/review.spec.ts \
  e2e/tutor.spec.ts \
  e2e/refresh-resume.spec.ts \
  e2e/free-recall.spec.ts \
  e2e/session-sizing.spec.ts \
  --reporter=line
```

Recorded on September 24, 2026: pytest **112 passed, 6 skipped** (AI off and fake); `make ai-eval` green; gate Playwright **13 passed, 1 skipped**.

Phase 4 (Gate 4) is verified. Next is **Phase 5 — S81** (General route).
