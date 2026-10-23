"""Chart configuration builder for QueryPilot analytical visualizations."""

from datetime import date, datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
from app.api.schemas import ChartConfig

logger = logging.getLogger("querypilot.agents.chart_builder")


def _is_numeric(val: Any) -> bool:
    """Check if value is an int, float, or Decimal."""
    return isinstance(val, (int, float, Decimal)) and not isinstance(val, bool)


def _is_date_like(val: Any, col_name: str) -> bool:
    """Check if value or column name represents a date or temporal series."""
    if isinstance(val, (datetime, date)):
        return True
    lower = col_name.lower()
    return any(k in lower for k in ("date", "month", "year", "quarter", "day", "week"))


def build_chart_config(
    question: str,
    columns: List[str],
    rows: List[Dict[str, Any]],
) -> Optional[ChartConfig]:
    """Deterministically determine if a chart is suitable and produce valid ChartConfig.

    Rules:
    - At least 2 data rows required for meaningful visualization.
    - Exactly or at least 1 numeric column and 1 categorical/label column.
    - Verified that selected x and y exist in columns.
    - If temporal x -> line chart. Otherwise -> bar chart.

    Args:
        question: User's question.
        columns: List of returned column names.
        rows: List of returned data rows.

    Returns:
        ChartConfig if suitable, or None if no suitable chart can be built.
    """
    if not rows or len(rows) < 2 or not columns or len(columns) < 2:
        return None

    # Inspect first row to classify column data types
    first_row = rows[0]
    numeric_cols: List[str] = []
    categorical_cols: List[str] = []
    temporal_cols: List[str] = []

    for col in columns:
        val = first_row.get(col)
        if _is_numeric(val):
            numeric_cols.append(col)
        elif _is_date_like(val, col):
            temporal_cols.append(col)
        else:
            categorical_cols.append(col)

    # Need at least one numeric column for the Y axis
    if not numeric_cols:
        return None

    # Determine X and Y columns
    y_col = numeric_cols[0]
    # Prefer temporal for line chart, then categorical
    if temporal_cols:
        x_col = temporal_cols[0]
        chart_type = "line"
    elif categorical_cols:
        x_col = categorical_cols[0]
        chart_type = "bar"
    elif len(numeric_cols) >= 2:
        # 2 numeric columns: first can be X
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]
        chart_type = "bar"
    else:
        return None

    # Format human-friendly chart title
    title = f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}"

    return ChartConfig(
        type=chart_type,
        title=title,
        x=x_col,
        y=y_col,
    )
