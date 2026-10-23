"""Conditional routing functions for the QueryPilot LangGraph workflow."""

import logging
from app.config import get_settings
from app.graph.state import SQLState

logger = logging.getLogger("querypilot.graph.routing")


def route_after_classification(state: SQLState) -> str:
    """Route based on question classification."""
    is_data = state.get("is_data_question", True)
    if not is_data:
        logger.info("Routing to finalize_response (out of scope question)")
        return "finalize_response"
    return "get_schema"


def route_after_validation(state: SQLState) -> str:
    """Route after deterministic SQLGlot validation."""
    status = state.get("validation_status")
    retry_count = state.get("retry_count", 0)
    settings = get_settings()
    max_retries = state.get("max_retries", settings.max_sql_repair_attempts)

    if status == "passed":
        logger.info("Validation passed; routing to execute_sql")
        return "execute_sql"

    if retry_count < max_retries:
        logger.info("Validation failed (%s); routing to repair_sql (attempt %d of %d)", status, retry_count + 1, max_retries)
        return "repair_sql"

    logger.warning("Max repair retries reached (%d); routing to finalize_response", retry_count)
    return "finalize_response"


def route_after_execution(state: SQLState) -> str:
    """Route after SQL execution."""
    status = state.get("validation_status")
    retry_count = state.get("retry_count", 0)
    settings = get_settings()
    max_retries = state.get("max_retries", settings.max_sql_repair_attempts)

    if status == "passed":
        return "analyze_results"

    if retry_count < max_retries:
        logger.info("Execution failed; routing to repair_sql (attempt %d)", retry_count + 1)
        return "repair_sql"

    return "finalize_response"
