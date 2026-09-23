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

`GET http://localhost:8000/health` → `200` `{"status":"ok"}`.
