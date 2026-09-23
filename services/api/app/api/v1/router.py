"""Versioned API surface. Feature routers are included as steps add them."""

from fastapi import APIRouter

from app.modules.identity.router import router as identity_router

router = APIRouter()
router.include_router(identity_router)


@router.get("/version")
def version() -> dict[str, str]:
    """Confirms the process is serving the v1 contract."""
    return {"api": "v1"}
