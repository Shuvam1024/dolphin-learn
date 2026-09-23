"""Versioned API surface. Feature routers are included as steps add them."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/version")
def version() -> dict[str, str]:
    """Confirms the process is serving the v1 contract."""
    return {"api": "v1"}
