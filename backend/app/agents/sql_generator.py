"""Gemini SQL Generation Agent with structured output parsing and domain grounding."""

import json
import logging
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import get_settings
from app.database.schema_introspection import get_schema_prompt_context
from app.guardrails.guardrail_service import validate_structured_sql_output
from app.guardrails.output_models import GeneratedSQLOutput

logger = logging.getLogger("querypilot.agents.sql_generator")

SQL_SYSTEM_PROMPT = """You are an expert SQL analyst for QueryPilot.
Your sole job is to translate user natural-language questions into safe, accurate, read-only SQL queries.

Strict Rules:
1. ONLY produce a single read-only SQL query (SELECT or WITH ... SELECT).
2. NEVER produce or suggest write/DDL operations: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE are strictly forbidden.
3. ONLY use approved tables and columns explicitly defined in the database schema below.
4. NEVER hallucinate or assume non-existent columns (e.g. there is NO 'revenue', 'total', 'sales_amount', or 'price' column in the orders table).
5. REVENUE DEFINITION:
   Revenue MUST always be calculated from order_items:
   Revenue per item = (order_items.quantity * order_items.unit_price - order_items.discount_amount)
   Total revenue = SUM(order_items.quantity * order_items.unit_price - order_items.discount_amount)
6. When answering "last quarter" or specific timeframes, reference the order_date column in orders.
7. Return your response as a valid JSON object matching the following schema:
   {
     "sql": "SELECT ...",
     "explanation": "Brief explanation of query logic",
     "assumptions": ["Assumption 1", "Assumption 2"],
     "confidence": 0.95
   }
"""

SQL_USER_PROMPT = """Database Schema & Domain Context:
{schema_context}

User Question:
{question}

Target SQL Dialect:
{dialect}

Generate the candidate read-only SQL query as structured JSON.
"""


def get_gemini_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Initialize the configured Gemini chat model."""
    settings = get_settings()
    if not settings.is_gemini_configured:
        raise ValueError(
            "GOOGLE_API_KEY is not configured or contains placeholder. "
            "Please configure your Gemini API key in backend/.env"
        )

    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
    )


def generate_sql(
    question: str,
    schema_context: Optional[str] = None,
    dialect: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
) -> GeneratedSQLOutput:
    """Generate a structured SQL candidate from a natural-language question.

    Args:
        question: User's question about the database.
        schema_context: Formatted schema string. If None, fetched from database.
        dialect: SQL dialect (default 'postgres').
        llm: Optional LLM instance for testing/dependency injection.

    Returns:
        Validated GeneratedSQLOutput instance.

    Raises:
        ValueError: If question is invalid, API key is missing, or output fails validation.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    settings = get_settings()
    target_dialect = dialect or settings.database_dialect
    schema_str = schema_context or get_schema_prompt_context()

    # Format prompts
    user_prompt = SQL_USER_PROMPT.format(
        schema_context=schema_str,
        question=question.strip(),
        dialect=target_dialect.upper(),
    )

    messages = [
        SystemMessage(content=SQL_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    active_llm = llm or get_gemini_llm()

    logger.info("Invoking Gemini for question: %s", question[:80])

    try:
        # Attempt structured output first
        structured_llm = active_llm.with_structured_output(GeneratedSQLOutput)
        result = structured_llm.invoke(messages)
        if isinstance(result, GeneratedSQLOutput):
            validated, err = validate_structured_sql_output(result)
            if validated:
                return validated
    except Exception as exc:
        logger.warning(
            "with_structured_output failed or unsupported (%s). Falling back to direct prompt invocation.",
            exc,
        )

    # Fallback: direct invoke and parse JSON response
    response = active_llm.invoke(messages)
    raw_content = response.content if hasattr(response, "content") else str(response)

    validated, err = validate_structured_sql_output(raw_content)
    if not validated:
        logger.error("Failed to parse structured SQL output: %s", err)
        raise ValueError(f"Model generated invalid SQL output structure: {err}")

    return validated