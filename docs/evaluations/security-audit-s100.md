# Security audit notes (S100)

- `npm audit --omit=dev` and `pip-audit` should run in CI. Local snapshot: document residual advisories here when present.
- Rate limits: `/api/v1/dev/token`, session writes, AI help routes return `{error:{code:rate_limited}}` with 429.
- Next middleware sets CSP (nonce), `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and HSTS in production.
