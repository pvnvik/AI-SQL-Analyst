"""QueryPilot FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import __version__
from app.api.routes import health
from app.config import get_settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("querypilot")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan events for application startup and shutdown."""
    settings = get_settings()
    logger.info("Initializing QueryPilot API v%s (env: %s)", __version__, settings.app_env)
    logger.info(
        "Readiness check: Gemini API=%s, Database URL=%s, LangSmith Tracing=%s",
        "Configured" if settings.is_gemini_configured else "Missing/Unconfigured",
        "Configured" if settings.is_database_configured else "Default/Placeholder",
        "Enabled" if settings.is_langsmith_configured else "Disabled/Unconfigured",
    )
    yield
    logger.info("Shutting down QueryPilot API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="QueryPilot API",
        description="Agentic AI SQL Analyst Backend API",
        version=__version__,
        lifespan=lifespan,
    )

    # Configure CORS for frontend access
    allowed_origins = {
        settings.frontend_origin.rstrip("/"),
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(health.router, prefix="/api")

    @app.get("/")
    async def root():
        """Root endpoint redirecting awareness to API health."""
        return {
            "app": "QueryPilot API",
            "version": __version__,
            "status": "running",
            "documentation": "/docs",
            "health_check": "/api/health",
        }

    return app


app = create_app()
