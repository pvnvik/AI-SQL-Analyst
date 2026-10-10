"""Health check route."""

from fastapi import APIRouter, Depends
from app import __version__
from app.api.schemas import HealthChecks, HealthResponse
from app.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Returns service health and readiness status.
    Guarantees no secret keys or credentials are leaked.
    """
    checks = HealthChecks(
        gemini_configured=settings.is_gemini_configured,
        gemini_model=settings.gemini_model,
        database_configured=settings.is_database_configured,
        database_dialect=settings.database_dialect,
        langsmith_configured=settings.is_langsmith_configured,
    )
    return HealthResponse(
        status="ok",
        app_env=settings.app_env,
        version=__version__,
        checks=checks,
    )
