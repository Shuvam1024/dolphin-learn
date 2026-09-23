"""Dolphin API entrypoint.

S04 only proves the process boots. Business routes arrive in later steps.
"""

from fastapi import FastAPI

app = FastAPI(title="Dolphin API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Returns 200 when the process is serving."""
    return {"status": "ok"}
