# Evaluations

Tutor prompt evaluation fixtures live under `services/api/tests/ai_eval/`.

- `make ai-eval` runs the scripted suite and writes `docs/evaluations/ai-eval-<date>.md` (pass rates, no learner data).
- Optional `AI_EVAL_LIVE=1` annotates a live-provider pass; scripted FakeProvider cases stay the CI gate.

Prove Loop click path: `docs/prove-loop-demo.md`. Step results: `docs/design/04-implementation-status.md`.
