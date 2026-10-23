"""LangGraph node implementations for QueryPilot query workflow."""

import logging
from typing import Any, Dict
from app.agents.chart_builder import build_chart_config
from app.agents.classifier import classify_question
from app.agents.result_analyst import analyze_results
from app.agents.sql_generator import generate_sql
from app.agents.sql_repair import repair_sql
from app.config import get_settings
from app.database.query_executor import execute_query
from app.database.schema_introspection import get_schema_prompt_context
from app.graph.state import SQLState
from app.guardrails.sql_validator import validate_sql

logger = logging.getLogger("querypilot.graph.nodes")


def classify_question_node(state: SQLState) -> Dict[str, Any]:
    """Node 1: Classify whether the user inquiry is a supported retail data question."""
    question = state.get("question", "")
    classification = classify_question(question)

    if not classification.is_data_question:
        logger.info("Question classified as non-data: '%s'", question)
        return {
            "is_data_question": False,
            "validation_status": "rejected_non_data_question",
            "validation_errors": ["The question does not appear to be related to the retail database."],
            "insight": (
                "QueryPilot only answers questions about retail data (such as customers, products, "
                "orders, sales performance, and revenue). Please ask a question related to your database."
            ),
            "sql": "",
            "columns": [],
            "query_rows": [],
            "row_count": 0,
            "execution_duration_ms": 0,
            "truncated": False,
            "chart": None,
        }

    return {"is_data_question": True}


def get_schema_node(state: SQLState) -> Dict[str, Any]:
    """Node 2: Retrieve approved schema context string for prompt injection."""
    schema_context = state.get("schema_context") or get_schema_prompt_context()
    return {"schema_context": schema_context}


def generate_sql_node(state: SQLState) -> Dict[str, Any]:
    """Node 3: Call Gemini to produce candidate read-only SQL query."""
    question = state["question"]
    schema_context = state.get("schema_context", "")
    settings = get_settings()

    try:
        output = generate_sql(
            question=question,
            schema_context=schema_context,
            dialect=settings.database_dialect,
        )
        return {
            "sql": output.sql,
            "validation_status": "generated",
            "validation_errors": [],
        }
    except Exception as exc:
        logger.error("generate_sql_node failed: %s", exc)
        return {
            "sql": "",
            "validation_status": "rejected_generation_failed",
            "validation_errors": [str(exc)],
        }


def validate_sql_node(state: SQLState) -> Dict[str, Any]:
    """Node 4: Deterministic SQLGlot AST and schema allowlist validation."""
    sql = state.get("sql", "")
    settings = get_settings()

    result = validate_sql(
        sql=sql,
        dialect=settings.database_dialect,
        max_rows=settings.max_rows,
    )

    if result.is_valid:
        return {
            "validation_status": "passed",
            "validation_errors": [],
            "sql": result.sanitized_sql,
        }

    return {
        "validation_status": result.status,
        "validation_errors": result.errors,
    }


def repair_sql_node(state: SQLState) -> Dict[str, Any]:
    """Node 5: Gemini SQL repair agent for bounded error correction."""
    question = state["question"]
    failed_sql = state.get("sql", "")
    errors = state.get("validation_errors", [])
    schema_context = state.get("schema_context", "")
    retry_count = state.get("retry_count", 0) + 1
    settings = get_settings()

    logger.info("Attempting SQL repair (attempt %d): %s", retry_count, errors)

    try:
        repair_output = repair_sql(
            question=question,
            failed_sql=failed_sql,
            error_messages=errors,
            schema_context=schema_context,
            dialect=settings.database_dialect,
        )
        return {
            "sql": repair_output.sql,
            "retry_count": retry_count,
            "validation_status": "repair_attempted",
        }
    except Exception as exc:
        logger.error("repair_sql_node failed: %s", exc)
        return {
            "retry_count": retry_count,
            "validation_status": "repair_failed",
            "validation_errors": errors + [f"Repair invocation failed: {exc}"],
        }


def execute_sql_node(state: SQLState) -> Dict[str, Any]:
    """Node 6: Safe read-only execution with timeout and row limit."""
    sql = state["sql"]
    settings = get_settings()

    exec_result = execute_query(
        sql=sql,
        timeout_seconds=settings.query_timeout_seconds,
        max_rows=settings.max_rows,
    )

    if not exec_result.is_success:
        logger.warning("Execution error: %s", exec_result.error)
        return {
            "validation_status": "rejected_execution_error",
            "validation_errors": [exec_result.error or "Database execution failed"],
            "execution_duration_ms": exec_result.duration_ms,
            "query_rows": [],
            "columns": [],
            "row_count": 0,
            "truncated": False,
        }

    return {
        "query_rows": exec_result.rows,
        "columns": exec_result.columns,
        "row_count": exec_result.row_count,
        "execution_duration_ms": exec_result.duration_ms,
        "truncated": exec_result.truncated,
        "validation_status": "passed",
        "validation_errors": [],
    }


def analyze_results_node(state: SQLState) -> Dict[str, Any]:
    """Node 7: Gemini result analyst generating grounded explanation."""
    question = state["question"]
    sql = state.get("sql", "")
    columns = state.get("columns", [])
    rows = state.get("query_rows", [])
    row_count = state.get("row_count", 0)
    truncated = state.get("truncated", False)

    insight = analyze_results(
        question=question,
        sql=sql,
        columns=columns,
        rows=rows,
        row_count=row_count,
        truncated=truncated,
    )
    return {"insight": insight}


def build_chart_node(state: SQLState) -> Dict[str, Any]:
    """Node 8: Deterministic chart configuration builder."""
    question = state["question"]
    columns = state.get("columns", [])
    rows = state.get("query_rows", [])

    chart_config = build_chart_config(
        question=question,
        columns=columns,
        rows=rows,
    )
    chart_dict = chart_config.model_dump() if chart_config else None
    return {"chart": chart_dict}


def finalize_response_node(state: SQLState) -> Dict[str, Any]:
    """Node 9: Finalize state and ensure all API response guarantees are satisfied."""
    validation_status = state.get("validation_status", "passed")
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    settings = get_settings()

    updates: Dict[str, Any] = {
        "trace_project": settings.langsmith_project,
        "trace_url": None,
    }

    # If query was rejected or failed repair
    if validation_status != "passed" and not state.get("insight"):
        if validation_status == "rejected_non_data_question":
            updates["insight"] = state.get("insight")
        elif retry_count >= settings.max_sql_repair_attempts:
            updates["validation_status"] = "repair_limit_reached"
            updates["insight"] = (
                f"QueryPilot could not generate a safe query after {retry_count} attempts. "
                f"Validation issues: {'; '.join(errors)}"
            )
        else:
            updates["insight"] = (
                f"Query validation failed ({validation_status}). "
                f"Reason: {'; '.join(errors)}"
            )

    # Ensure empty arrays instead of None
    if "columns" not in state:
        updates["columns"] = []
    if "query_rows" not in state:
        updates["query_rows"] = []
    if "chart" not in state:
        updates["chart"] = None

    return updates
