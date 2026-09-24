# Learner-model roadmap (post-ship)

Calibrated estimators (mastery probability, spacing predictions) are **not** in v0.1. Phase 6 records the dataset they would need and keeps adaptivity transparent and deterministic.

## What a calibrated estimator would need

From `v_attempt_features`:

- item difficulty
- assistance level
- delay since first exposure
- outcome
- active minutes
- selection reason

From `v_review_outcomes`:

- scheduled interval
- outcome
- delay relative to due time

Plus opaque product-event sequencing for session and review context.

## Why it is post-ship

1. Validity and fairness studies need enough longitudinal data.
2. The referee must stay deterministic; any model output is advice it can override.
3. Shipping opaque ML scores as “mastery” would violate honest evidence principles.

Until then, effort EMA (S91) and difficulty/history item selection (S92) are the only adaptivity in product.
