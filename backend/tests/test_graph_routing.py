"""Tests for LangGraph routing functions and workflow node behavior."""

import pytest
from app.graph.nodes import (
    build_chart_node,
    classify_question_node,
    finalize_response_node,
)
from app.graph.routing import (
    route_after_classification,
    route_after_execution,
    route_after_validation,
)
from app.graph.state import SQLState


def test_route_after_classification():
    """Verify routing after question classification."""
    state_data: SQLState = {"is_data_question": True, "question": "Show customers"}
    assert route_after_classification(state_data) == "get_schema"

    state_non_data: SQLState = {"is_data_question": False, "question": "Tell me a joke"}
    assert route_after_classification(state_non_data) == "finalize_response"


def test_route_after_validation_success():
    """Verify routing after successful validation."""
    state: SQLState = {
        "validation_status": "passed",
        "retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_validation(state) == "execute_sql"


def test_route_after_validation_repair_loop():
    """Verify routing to repair when validation fails and retries remain."""
    state: SQLState = {
        "validation_status": "rejected_unsafe_sql",
        "retry_count": 1,
        "max_retries": 3,
    }
    assert route_after_validation(state) == "repair_sql"


def test_route_after_validation_max_retries_reached():
    """Verify routing to finalize when max repair retries reached."""
    state: SQLState = {
        "validation_status": "rejected_unsafe_sql",
        "retry_count": 3,
        "max_retries": 3,
    }
    assert route_after_validation(state) == "finalize_response"


def test_route_after_execution():
    """Verify execution routing on success and error."""
    state_ok: SQLState = {"validation_status": "passed", "retry_count": 0}
    assert route_after_execution(state_ok) == "analyze_results"

    state_err: SQLState = {
        "validation_status": "rejected_execution_error",
        "retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_execution(state_err) == "repair_sql"


def test_classify_question_node_non_data():
    """Test classify_question_node handles non-data inquiries."""
    state: SQLState = {"question": "What is the capital of France?"}
    result = classify_question_node(state)

    assert result["is_data_question"] is False
    assert result["validation_status"] == "rejected_non_data_question"
    assert "retail" in result["insight"].lower()


def test_build_chart_node():
    """Test build_chart_node produces valid chart for categorical + numeric."""
    state: SQLState = {
        "question": "Revenue by region",
        "columns": ["region", "revenue"],
        "query_rows": [
            {"region": "North", "revenue": 15000.0},
            {"region": "South", "revenue": 12000.0},
        ],
    }
    result = build_chart_node(state)
    assert result["chart"] is not None
    assert result["chart"]["type"] == "bar"
    assert result["chart"]["x"] == "region"
    assert result["chart"]["y"] == "revenue"


def test_finalize_response_node_repair_limit():
    """Test finalize_response_node produces helpful insight when repair limit reached."""
    state: SQLState = {
        "validation_status": "rejected_unsafe_sql",
        "validation_errors": ["Table 'secret' does not exist"],
        "retry_count": 3,
    }
    result = finalize_response_node(state)
    assert result["validation_status"] == "repair_limit_reached"
    assert "could not generate a safe query" in result["insight"]
