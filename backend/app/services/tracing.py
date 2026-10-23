"""LangSmith tracing configuration, privacy filtering, and trace metadata service."""

import logging
import os
from typing import Any, Dict, Optional
from app.config import get_settings

logger = logging.getLogger("querypilot.services.tracing")


def setup_langsmith_tracing() -> bool:
    """Configure LangChain / LangSmith environment variables if credentials exist.

    Returns:
        True if LangSmith tracing is active, False otherwise.
    """
    settings = get_settings()

    if settings.is_langsmith_configured:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key or ""
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
        logger.info(
            "LangSmith tracing enabled for project '%s' at '%s'",
            settings.langsmith_project,
            settings.langsmith_endpoint,
        )
        return True
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.info("LangSmith tracing is disabled (offline/unconfigured).")
        return False


def get_sanitized_trace_metadata(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata for LangSmith runs while strictly adhering to privacy policies.

    Never logs:
    - Passwords, database URLs, or API keys
    - Unbounded raw row dumps
    """
    settings = get_settings()
    return {
        "request_id": state.get("request_id"),
        "question_length": len(state.get("question", "")),
        "validation_status": state.get("validation_status"),
        "repair_count": state.get("retry_count", 0),
        "row_count": state.get("row_count", 0),
        "truncated": state.get("truncated", False),
        "execution_duration_ms": state.get("execution_duration_ms", 0),
        "model_name": settings.gemini_model,
        "chart_generated": state.get("chart") is not None,
    }


def get_langsmith_trace_url(run_id: Optional[str]) -> Optional[str]:
    """Generate a valid LangSmith trace URL if client is available.

    Never fabricates a URL if tracing is disabled or unavailable.
    """
    if not run_id:
        return None

    settings = get_settings()
    if not settings.is_langsmith_configured:
        return None

    try:
        from langsmith import Client
        client = Client()
        # Retrieve real run URL
        url = client.get_run_url(run_id=run_id, project_name=settings.langsmith_project)
        return url
    except Exception as exc:
        logger.debug("Could not resolve LangSmith trace URL for run %s: %s", run_id, exc)
        return None
