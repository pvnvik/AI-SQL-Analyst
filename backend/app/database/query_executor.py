"""Safe read-only SQL query executor with timeout, row capping, and timing metrics."""

from dataclasses import dataclass, field
from decimal import Decimal
import logging
import re
import time
from typing import Any, Dict, List, Optional
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError
from app.config import get_settings
from app.database import connection

logger = logging.getLogger("querypilot.executor")


@dataclass
class QueryExecutionResult:
    """Encapsulates the result of executing a SQL query."""
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    duration_ms: int = 0
    truncated: bool = False
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.error is None


def _serialize_value(val: Any) -> Any:
    """Format non-JSON serializable values like Decimal, datetime, etc."""
    if isinstance(val, Decimal):
        return float(val)
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return val


def _sanitize_error_message(err: Exception) -> str:
    """Clean database exception message to avoid leaking internal hostnames or credentials."""
    raw = str(err)
    # Mask connection strings or passwords
    cleaned = re.sub(r":([^:@/]+)@", r":***@", raw)
    # Remove filesystem paths
    cleaned = re.sub(r"[A-Za-z]:\\[\w\\\.-]+", "[internal path]", cleaned)
    # Extract the main error sentence
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    if lines:
        return lines[0]
    return "Database execution failed"


def execute_query(
    sql: str,
    engine: Optional[Engine] = None,
    timeout_seconds: Optional[int] = None,
    max_rows: Optional[int] = None,
) -> QueryExecutionResult:
    """Execute a validated read-only SQL query against the database.

    Enforces:
    - Statement timeout (via DB connection options)
    - Maximum returned row count (MAX_ROWS)
    - Execution timing in milliseconds
    - Value serialization for JSON responses

    Args:
        sql: The SQL string to execute.
        engine: SQLAlchemy engine. Defaults to configured application engine.
        timeout_seconds: Timeout in seconds. Defaults to settings.query_timeout_seconds.
        max_rows: Maximum rows to return. Defaults to settings.max_rows.

    Returns:
        QueryExecutionResult with columns, rows, timing, and truncation status.
    """
    settings = get_settings()
    target_engine = engine or connection.get_engine()
    timeout = timeout_seconds or settings.query_timeout_seconds
    limit = max_rows or settings.max_rows

    start_time = time.perf_counter()

    try:
        with target_engine.connect() as conn:
            # Set Postgres statement timeout if on postgres dialect
            if target_engine.dialect.name == "postgresql":
                conn.execute(text(f"SET LOCAL statement_timeout = {timeout * 1000}"))

            # Execute query
            cursor_result = conn.execute(text(sql))

            # Retrieve columns if returns_rows
            if cursor_result.returns_rows:
                columns = list(cursor_result.keys())
                # Fetch up to limit + 1 to detect truncation
                raw_rows = cursor_result.fetchmany(limit + 1)
                truncated = len(raw_rows) > limit
                display_rows = raw_rows[:limit]

                formatted_rows: List[Dict[str, Any]] = [
                    {col: _serialize_value(row[i]) for i, col in enumerate(columns)}
                    for row in display_rows
                ]
            else:
                columns = []
                formatted_rows = []
                truncated = False

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return QueryExecutionResult(
            columns=columns,
            rows=formatted_rows,
            row_count=len(formatted_rows),
            duration_ms=duration_ms,
            truncated=truncated,
            error=None,
        )

    except (OperationalError, DBAPIError, SQLAlchemyError) as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        sanitized = _sanitize_error_message(exc)
        logger.warning("SQL execution failed: %s (in %d ms)", sanitized, duration_ms)
        return QueryExecutionResult(
            columns=[],
            rows=[],
            row_count=0,
            duration_ms=duration_ms,
            truncated=False,
            error=sanitized,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.exception("Unexpected error executing query")
        return QueryExecutionResult(
            columns=[],
            rows=[],
            row_count=0,
            duration_ms=duration_ms,
            truncated=False,
            error="Unexpected query execution error",
        )


def execute_fixed_safe_query(engine: Optional[Engine] = None) -> QueryExecutionResult:
    """Execute a fixed safe query verifying that the database is readable and populated.

    Runs a standard customer count and product sample query.
    """
    fixed_sql = """
    SELECT 
        c.region,
        COUNT(DISTINCT c.id) AS customer_count,
        COUNT(o.id) AS total_orders
    FROM customers c
    LEFT JOIN orders o ON c.id = o.customer_id
    GROUP BY c.region
    ORDER BY total_orders DESC;
    """
    return execute_query(fixed_sql, engine=engine)
