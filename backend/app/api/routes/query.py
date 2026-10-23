"""API route for natural-language database querying via LangGraph."""

import logging
import uuid
from fastapi import APIRouter, HTTPException, status
from app.api.schemas import (
    ChartConfig,
    ExecutionInfo,
    QueryRequest,
    QueryResponse,
    TraceInfo,
    ValidationInfo,
)
from app.config import get_settings
from app.graph.workflow import querypilot_workflow

logger = logging.getLogger("querypilot.api.query")
router = APIRouter(tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest):
    """Process a natural language question through the LangGraph agentic workflow."""
    request_id = str(uuid.uuid4())
    settings = get_settings()

    logger.info("Received query [%s]: '%s'", request_id, request.question)

    initial_state = {
        "request_id": request_id,
        "question": request.question,
        "retry_count": 0,
        "max_retries": settings.max_sql_repair_attempts,
    }

    try:
        final_state = querypilot_workflow.invoke(initial_state)

        # Parse chart if present
        chart_obj = None
        if final_state.get("chart"):
            try:
                chart_obj = ChartConfig(**final_state["chart"])
            except Exception as e:
                logger.warning("Failed to parse chart in response: %s", e)

        return QueryResponse(
            request_id=request_id,
            question=request.question,
            sql=final_state.get("sql", ""),
            columns=final_state.get("columns", []),
            rows=final_state.get("query_rows", []),
            insight=final_state.get("insight", "Analysis complete."),
            chart=chart_obj,
            validation=ValidationInfo(
                status=final_state.get("validation_status", "passed"),
                messages=final_state.get("validation_errors", []),
            ),
            execution=ExecutionInfo(
                duration_ms=final_state.get("execution_duration_ms", 0),
                row_count=final_state.get("row_count", 0),
                truncated=final_state.get("truncated", False),
            ),
            trace=TraceInfo(
                project=final_state.get("trace_project", settings.langsmith_project),
                url=final_state.get("trace_url"),
            ),
        )

    except Exception as exc:
        logger.exception("Error executing workflow for request [%s]: %s", request_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your question. Please try again.",
        )
