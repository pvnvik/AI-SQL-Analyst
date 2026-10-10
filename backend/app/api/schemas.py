"""Pydantic schemas for API endpoints."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthChecks(BaseModel):
    """Component readiness status without secrets."""
    gemini_configured: bool = Field(..., description="Whether Gemini API key is configured")
    gemini_model: str = Field(..., description="Configured Gemini model")
    database_configured: bool = Field(..., description="Whether a non-default database URL is provided")
    database_dialect: str = Field(..., description="Target database dialect")
    langsmith_configured: bool = Field(..., description="Whether LangSmith tracing is active")


class HealthResponse(BaseModel):
    """Response payload for GET /api/health."""
    status: str = Field(default="ok", description="Overall service status")
    app_env: str = Field(..., description="Current environment (development, production, etc.)")
    version: str = Field(..., description="Application version")
    checks: HealthChecks = Field(..., description="Component readiness checks")


class QueryRequest(BaseModel):
    """Request payload for POST /api/query."""
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural language question about the database",
    )


class ValidationInfo(BaseModel):
    """Validation outcome details."""
    status: str = Field(..., description="Validation outcome (passed, rejected_unsafe_sql, etc.)")
    messages: List[str] = Field(default_factory=list, description="Sanitized validation messages")


class ExecutionInfo(BaseModel):
    """Execution statistics."""
    duration_ms: int = Field(0, description="SQL execution time in milliseconds")
    row_count: int = Field(0, description="Number of rows returned")
    truncated: bool = Field(False, description="Whether rows were truncated to MAX_ROWS")


class ChartConfig(BaseModel):
    """Chart specification."""
    type: str = Field("bar", description="Chart type (bar, line, etc.)")
    title: str = Field("", description="Chart title")
    x: str = Field("", description="X-axis column")
    y: str = Field("", description="Y-axis column")


class TraceInfo(BaseModel):
    """LangSmith trace metadata."""
    project: str = Field("querypilot-dev", description="LangSmith project name")
    url: Optional[str] = Field(None, description="LangSmith trace URL if available")


class QueryResponse(BaseModel):
    """Response payload for POST /api/query."""
    request_id: str
    question: str
    sql: str
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    insight: str
    chart: Optional[ChartConfig] = None
    validation: ValidationInfo
    execution: ExecutionInfo
    trace: TraceInfo
