"""Versioned API surface. Feature routers are included as steps add them."""

from fastapi import APIRouter

from app.modules.curriculum.router import router as domains_router
from app.modules.goals.router import router as goals_router
from app.modules.identity.router import router as identity_router
from app.modules.learning.home_router import router as home_router
from app.modules.learning.progress_router import router as progress_router
from app.modules.learning.review_router import router as reviews_router
from app.modules.learning.session_router import router as sessions_router

router = APIRouter()
router.include_router(identity_router)
router.include_router(domains_router)
router.include_router(goals_router)
router.include_router(sessions_router)
router.include_router(progress_router)
router.include_router(reviews_router)
router.include_router(home_router)


@router.get("/version")
def version() -> dict[str, str]:
    """Confirms the process is serving the v1 contract."""
    return {"api": "v1"}
