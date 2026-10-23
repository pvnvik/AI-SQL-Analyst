"""Gemini Result Analyst Agent for grounded natural-language explanations."""

import json
import logging
from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.sql_generator import get_gemini_llm

logger = logging.getLogger("querypilot.agents.result_analyst")

ANALYST_SYSTEM_PROMPT = """You are an expert data analyst for QueryPilot.
Your task is to provide a clear, concise, and accurate natural-language answer to the user's question based strictly on the query execution results provided.

Strict Rules:
1. Ground your explanation ONLY in the returned data rows.
2. DO NOT invent, extrapolate, or hallucinate facts or numbers not present in the results.
3. If no rows were returned, clearly state that no records matched the query criteria.
4. Keep the explanation concise and direct (1 to 3 sentences maximum).
5. If results were truncated, mention that only the top results are shown.
"""

ANALYST_USER_PROMPT = """User Question:
{question}

Executed SQL Query:
{sql}

Total Rows Returned: {row_count} (Truncated: {truncated})
Columns: {columns}

Data Rows (Sample):
{sample_rows}

Provide a concise, grounded explanation of these results answering the question.
"""


def analyze_results(
    question: str,
    sql: str,
    columns: List[str],
    rows: List[Dict[str, Any]],
    row_count: int,
    truncated: bool = False,
    llm: Optional[BaseChatModel] = None,
) -> str:
    """Generate a grounded natural language insight for query results.

    Args:
        question: User's question.
        sql: The SQL query that was executed.
        columns: List of returned column names.
        rows: List of returned row dictionaries.
        row_count: Total row count.
        truncated: Whether results were capped.
        llm: Optional chat model.

    Returns:
        Concise natural-language insight string.
    """
    if not rows or row_count == 0:
        return "The query executed successfully, but no records matched the requested criteria."

    # Cap sample rows to first 20 to avoid exceeding context tokens
    sample_rows = rows[:20]
    sample_json = json.dumps(sample_rows, default=str, indent=2)

    user_prompt = ANALYST_USER_PROMPT.format(
        question=question,
        sql=sql,
        row_count=row_count,
        truncated="Yes" if truncated else "No",
        columns=", ".join(columns),
        sample_rows=sample_json,
    )

    messages = [
        SystemMessage(content=ANALYST_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    try:
        active_llm = llm or get_gemini_llm()
        response = active_llm.invoke(messages)
        insight = response.content if hasattr(response, "content") else str(response)
        return insight.strip()
    except Exception as exc:
        logger.warning("Result analysis LLM failed (%s). Generating deterministic summary.", exc)
        # Deterministic grounded fallback
        first_row = rows[0]
        preview = ", ".join(f"{k}: {v}" for k, v in list(first_row.items())[:3])
        return (
            f"Retrieved {row_count} record(s). "
            f"Top result: [{preview}]."
        )
