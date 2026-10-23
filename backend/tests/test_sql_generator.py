"""Tests for Gemini SQL generation agent and structured output validation."""

import json
from unittest.mock import MagicMock
import pytest
from langchain_core.messages import AIMessage
from app.agents.sql_generator import SQL_SYSTEM_PROMPT, generate_sql
from app.guardrails.guardrail_service import validate_structured_sql_output
from app.guardrails.output_models import GeneratedSQLOutput


def test_generated_sql_output_model():
    """Test model validation and markdown fence stripping."""
    raw_sql = "```sql\nSELECT * FROM customers;\n```"
    model = GeneratedSQLOutput(
        sql=raw_sql,
        explanation="Selects all customers",
        assumptions=["None"],
        confidence=0.95,
    )

    # Markdown fences should be cleanly stripped
    assert model.sql == "SELECT * FROM customers;"
    assert model.confidence == 0.95
    assert len(model.assumptions) == 1


def test_generated_sql_output_empty_sql_rejected():
    """Test that empty SQL strings raise validation errors."""
    with pytest.raises(ValueError):
        GeneratedSQLOutput(
            sql="   ",
            explanation="Empty query",
            confidence=0.5,
        )


def test_validate_structured_sql_output_json_string():
    """Test validating JSON string matching schema."""
    json_payload = json.dumps({
        "sql": "SELECT product_name, unit_price FROM products ORDER BY unit_price DESC LIMIT 5;",
        "explanation": "Retrieves top 5 most expensive products",
        "assumptions": ["Sorted descending by price"],
        "confidence": 0.98,
    })

    result, err = validate_structured_sql_output(json_payload)
    assert err is None
    assert result is not None
    assert "products" in result.sql
    assert result.confidence == 0.98


def test_validate_structured_sql_output_markdown_fence():
    """Test validating output wrapped in markdown ```json code blocks."""
    fenced = """```json
    {
        "sql": "SELECT region, COUNT(*) AS count FROM customers GROUP BY region;",
        "explanation": "Counts customers grouped by geographical region",
        "assumptions": [],
        "confidence": 0.9
    }
    ```"""

    result, err = validate_structured_sql_output(fenced)
    assert err is None
    assert result is not None
    assert "GROUP BY region" in result.sql


def test_validate_structured_sql_output_invalid_json():
    """Test handling of invalid or non-JSON output gracefully."""
    bad_output = "I am an AI and here is your query: SELECT * FROM products"
    result, err = validate_structured_sql_output(bad_output)
    assert result is None
    assert err is not None
    assert "validation failed" in err.lower()


def test_generate_sql_with_mock_llm():
    """Test generate_sql execution with mocked LLM ensuring prompt composition and output parsing."""
    mock_llm = MagicMock()
    fake_response_json = json.dumps({
        "sql": "SELECT p.product_name, SUM(oi.quantity * oi.unit_price - oi.discount_amount) AS revenue FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.product_name ORDER BY revenue DESC LIMIT 5;",
        "explanation": "Calculates revenue per product using the canonical revenue formula and returns top 5.",
        "assumptions": ["Revenue includes discounts"],
        "confidence": 0.96,
    })

    mock_llm.with_structured_output.return_value.invoke.return_value = GeneratedSQLOutput(
        sql="SELECT p.product_name, SUM(oi.quantity * oi.unit_price - oi.discount_amount) AS revenue FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.product_name ORDER BY revenue DESC LIMIT 5;",
        explanation="Calculates revenue per product using the canonical revenue formula and returns top 5.",
        assumptions=["Revenue includes discounts"],
        confidence=0.96,
    )

    schema_sample = "Table: products\nColumns:\n- id: INTEGER\n- product_name: VARCHAR\nTable: order_items\nColumns:\n- quantity: INTEGER\n- unit_price: NUMERIC\n- discount_amount: NUMERIC"

    output = generate_sql(
        question="Which five products generated the most revenue?",
        schema_context=schema_sample,
        dialect="postgres",
        llm=mock_llm,
    )

    assert isinstance(output, GeneratedSQLOutput)
    assert "revenue" in output.sql.lower()
    assert "SUM" in output.sql
    assert output.confidence == 0.96
    assert len(output.assumptions) == 1
