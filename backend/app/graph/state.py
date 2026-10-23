"""Typed state definitions for the QueryPilot LangGraph workflow."""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class SQLState(TypedDict, total=False):
    """Complete state passed between LangGraph nodes during query processing."""

    request_id: str
    question: str
    is_data_question: bool
    schema_context: str
    sql: str
    validation_status: str  # passed, rejected_unsafe_sql, rejected_invalid_sql, rejected_unknown_schema_reference, repair_limit_reached
    validation_errors: List[str]
    retry_count: int
    max_retries: int
    query_rows: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_duration_ms: int
    truncated: bool
    insight: str
    chart: Optional[Dict[str, Any]]
    fatal_error: Optional[str]
    trace_project: str
    trace_url: Optional[str]
