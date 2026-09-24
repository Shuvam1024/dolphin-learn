# Changelog

## [0.1.0] — 2026-09-24

First ship. Adults (18+) can sign in, set preferences, create time-fit goals for checked subjects (Python, foundational math, software practice) or a General route, study in Session Studio, review with honest snooze, export or delete their data, and run with or without an AI key.

### Shipped

- Prove Loop: reading → worked example → objective → evidence facets (exposed / practicing / independently demonstrated / retained)
- Time-fit plans from real available minutes; sitting chooser; pause/resume
- Adaptive tutor behind a gateway (explains and hints; never grades); FakeProvider for CI; works with AI off
- Settings: name, timezone, sitting length, larger text, reduced motion, tutor on/off
- Privacy: JSON export (rate limited); account delete with 30-day retention purge
- Managed auth for production (RS256 / JWKS); dev email token only in development
- CSP, security headers, rate limits, structured logs, `/metrics`, `/ready`
- Dockerfiles, prod compose, runbook
- Golden release suite (AI off + fake)

### Not in v0.1

- Knowledge Vault / RAG
- Code sandbox or project workspace
- `applied` evidence facet
- Calibrated mastery estimators
- Child / under-18 product
- Claimed live-provider cost or latency without a recorded live run

### Upgrade notes

- Run Alembic to head (through `0023_users_deleted_at`).
- Production requires `AUTH_JWKS_URL` and `ENVIRONMENT=production` (dev token disabled).
- Optional: `AI_PROVIDER` / gateway flags and model API keys.
