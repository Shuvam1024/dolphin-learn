# Dolphin production runbook (S101)

## Bring-up

```bash
cp .env.example .env   # fill AUTH_JWKS_URL, secrets, AI flags
docker compose -f infra/compose.prod.yml up -d --build
```

Migrations run as the `migrate` one-shot service **before** `api` becomes healthy. `GET /ready` fails until the DB answers.

## Environment

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres |
| `ENVIRONMENT` | `production` gates the email form and requires JWKS |
| `AUTH_JWKS_URL` / `AUTH_ISSUER_URL` / `AUTH_AUDIENCE` | Managed OIDC |
| `AUTH_CLIENT_ID` / `AUTH_CLIENT_SECRET` / `AUTH_TOKEN_URL` | Callback exchange |
| `AI_GATEWAY_ENABLED` / `AI_PROVIDER` / `AI_API_KEY` | Tutor (optional) |
| `METRICS_USER` / `METRICS_PASSWORD` | Basic auth for `/metrics` |
| `RETENTION_DAYS` | Account purge window (default 30) |

## Backup / restore

```bash
docker compose -f infra/compose.prod.yml exec db pg_dump -U dolphin dolphin > backup.sql
docker compose -f infra/compose.prod.yml exec -T db psql -U dolphin dolphin < backup.sql
```

## Rollback

Redeploy the previous image tags and run `alembic downgrade -1` only when a migration is unsafe forward. Prefer forward fixes.

## Purge schedule

```bash
docker compose -f infra/compose.prod.yml exec api python -m app.jobs.purge
```

Run daily. AI audit rows for purged users are anonymized.

## AI key rotation

Rotate `AI_API_KEY` in the environment and restart `api`. No learner secrets live in the key.
