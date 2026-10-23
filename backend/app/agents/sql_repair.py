"""Gemini SQL Repair Agent for bounded query correction."""

import logging
from typing import List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.sql_generator import get_gemini_llm
from app.config import get_settings
from app.database.schema_introspection import get_schema_prompt_context
from app.guardrails.output_models import SQLRepairOutput

logger = logging.getLogger("querypilot.agents.sql_repair")

REPAIR_SYSTEM_PROMPT = """You are an expert SQL repair agent for QueryPilot.
A candidate SQL query failed validation or execution checks. Your task is to repair the SQL query while preserving strict safety rules.

Strict Rules:
1. Fix the exact errors listed below.
2. ONLY produce a single read-only SQL query (SELECT or WITH ... SELECT).
3. NEVER produce write or DDL commands (no INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE).
4. ONLY use approved tables and columns from the provided schema.
5. REVENUE DEFINITION:
   Revenue MUST always be calculated as: SUM(order_items.quantity * order_items.unit_price - order_items.discount_amount).
   There is NO 'revenue' column in any table.
6. Return your response as a valid JSON object matching the following schema:
   {
     "sql": "SELECT ...",
     "fix_applied": "Description of what was fixed",
     "confidence": 0.90
   }
"""

REPAIR_USER_PROMPT = """Original User Question:
{question}

Database Schema:
{schema_context}

Previous Candidate SQL:
{failed_sql}

Validation / Execution Errors Encountered:
{error_messages}

Target Dialect:
{dialect}

Generate the repaired read-only SQL query as structured JSON.
"""


def repair_sql(
    question: str,
    failed_sql: str,
    error_messages: List[str],
    schema_context: Optional[str] = None,
    dialect: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
) -> SQLRepairOutput:
    """Repair a failed SQL query using Gemini.

    Args:
        question: Original question from user.
        failed_sql: The query that failed validation or execution.
        error_messages: List of errors to correct.
        schema_context: Database schema context string.
        dialect: Target dialect.
        llm: Optional chat model for injection in tests.

    Returns:
        SQLRepairOutput with the repaired SQL query.
    """
    settings = get_settings()
    target_dialect = dialect or settings.database_dialect
    schema_str = schema_context or get_schema_prompt_context()
    formatted_errors = "\n- ".join(error_messages)

    user_prompt = REPAIR_USER_PROMPT.format(
        question=question,
        schema_context=schema_str,
        failed_sql=failed_sql,
        error_messages=f"- {formatted_errors}",
        dialect=target_dialect.upper(),
    )

    messages = [
        SystemMessage(content=REPAIR_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    active_llm = llm or get_gemini_llm()

    logger.info("Attempting SQL repair for question: %s", question[:60])

    try:
        structured_llm = active_llm.with_structured_output(SQLRepairOutput)
        result = structured_llm.invoke(messages)
        if isinstance(result, SQLRepairOutput):
            return result
    except Exception as exc:
        logger.warning("Repair with_structured_output fallback: %s", exc)

    # Fallback to direct invoke and parsing
    response = active_llm.invoke(messages)
    raw_content = response.content if hasattr(response, "content") else str(response)

    # Basic cleanup
    cleaned = raw_content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    import json
    data = json.loads(cleaned.strip())
    return SQLRepairOutput(**data)
