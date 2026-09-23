# services/api

FastAPI modular monolith — authenticated brain for goals, sessions, assessment, review, and later adapters.

Domain modules live under `app/modules/` and are created when implemented (identity, goals, curriculum, sessions, assessment, review, vault, labs, ai_gateway).

## Run locally (S04+)

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Checks (from the repo root, after `pip install -r requirements-dev.txt` inside this virtualenv):

```bash
make api-lint api-type api-test
```

Apply schema changes against the Compose (or local) Postgres URL:

```bash
alembic upgrade head
```

`GET http://localhost:8000/health` → `200` `{"status":"ok"}` (outside the version prefix).

Versioned routes live at `/api/v1`. Failures use one envelope:

```json
{"error": {"code": "not_found", "message": "Not Found", "details": null, "request_id": "…"}}
```
