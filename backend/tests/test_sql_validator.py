"""Tests for deterministic SQLGlot AST validation, schema allowlisting, and safety checks."""

import pytest
from app.guardrails.sql_validator import validate_sql

SAMPLE_ALLOWLIST = {
    "customers": ["id", "customer_name", "region", "city", "created_at"],
    "products": ["id", "product_name", "category", "unit_price"],
    "orders": ["id", "customer_id", "order_date", "status"],
    "order_items": ["id", "order_id", "product_id", "quantity", "unit_price", "discount_amount"],
}


def test_valid_select_query():
    """Verify that a safe read-only SELECT passes and injects default LIMIT."""
    sql = "SELECT product_name, unit_price FROM products WHERE category = 'Electronics';"
    result = validate_sql(sql, schema_allowlist=SAMPLE_ALLOWLIST, max_rows=500)

    assert result.is_valid
    assert result.status == "passed"
    assert "LIMIT 500" in result.sanitized_sql
    assert "products" in result.tables_used
    assert "product_name" in result.columns_used
    assert "unit_price" in result.columns_used


def test_valid_query_preserves_smaller_limit():
    """Verify that an existing LIMIT smaller than max_rows is preserved."""
    sql = "SELECT product_name FROM products LIMIT 5;"
    result = validate_sql(sql, schema_allowlist=SAMPLE_ALLOWLIST, max_rows=500)

    assert result.is_valid
    assert "LIMIT 5" in result.sanitized_sql


def test_valid_query_caps_oversized_limit():
    """Verify that an existing LIMIT larger than max_rows is capped."""
    sql = "SELECT product_name FROM products LIMIT 5000;"
    result = validate_sql(sql, schema_allowlist=SAMPLE_ALLOWLIST, max_rows=500)

    assert result.is_valid
    assert "LIMIT 500" in result.sanitized_sql


def test_valid_join_and_revenue_calculation():
    """Verify complex JOIN with aggregation and canonical revenue calculation."""
    sql = """
    SELECT 
        p.product_name,
        SUM(oi.quantity * oi.unit_price - oi.discount_amount) AS revenue
    FROM products p
    JOIN order_items oi ON p.id = oi.product_id
    GROUP BY p.product_name
    ORDER BY revenue DESC
    LIMIT 10;
    """
    result = validate_sql(sql, schema_allowlist=SAMPLE_ALLOWLIST)

    assert result.is_valid
    assert result.status == "passed"
    assert set(result.tables_used) == {"products", "order_items"}


def test_valid_cte_query():
    """Verify that safe CTE queries (WITH ... SELECT) pass validation."""
    sql = """
    WITH regional_customers AS (
        SELECT id, customer_name, region
        FROM customers
        WHERE region = 'North'
    )
    SELECT rc.customer_name, COUNT(o.id) AS total_orders
    FROM regional_customers rc
    LEFT JOIN orders o ON rc.id = o.customer_id
    GROUP BY rc.customer_name;
    """
    result = validate_sql(sql, schema_allowlist=SAMPLE_ALLOWLIST)

    assert result.is_valid
    assert result.status == "passed"
    assert "customers" in result.tables_used
    assert "orders" in result.tables_used


@pytest.mark.parametrize(
    "destructive_sql,operation",
    [
        ("DROP TABLE products;", "DROP"),
        ("DELETE FROM customers WHERE id = 1;", "DELETE"),
        ("INSERT INTO products (product_name, unit_price) VALUES ('Hacked', 0);", "INSERT"),
        ("UPDATE customers SET customer_name = 'Attacker';", "UPDATE"),
        ("ALTER TABLE orders ADD COLUMN hacked TEXT;", "ALTER"),
        ("TRUNCATE TABLE order_items;", "TRUNCATE"),
        ("CREATE TABLE evil_table (id INT);", "CREATE"),
        ("GRANT ALL ON customers TO public;", "GRANT"),
    ],
)
def test_reject_destructive_sql(destructive_sql, operation):
    """Verify that destructive/DDL operations are blocked by AST analysis."""
    result = validate_sql(destructive_sql, schema_allowlist=SAMPLE_ALLOWLIST)

    assert not result.is_valid
    assert result.status == "rejected_unsafe_sql"
    assert any(operation in err.upper() for err in result.errors)


def test_reject_multi_statement_stacked_query():
    """Verify rejection of stacked queries / multiple statements."""
    sql = "SELECT * FROM customers; DROP TABLE products;"
    result = validate_sql(sql, schema_allowlist=SAMPLE_ALLOWLIST)

    assert not result.is_valid
    assert result.status == "rejected_unsafe_sql"
    assert "Multi-statement" in result.errors[0]


def test_reject_unapproved_table():
    """Verify rejection of queries referencing unapproved or internal tables."""
    sql = "SELECT id, password_hash FROM user_credentials;"
    result = validate_sql(sql, schema_allowlist=SAMPLE_ALLOWLIST)

    assert not result.is_valid
    assert result.status == "rejected_unknown_schema_reference"
    assert "unapproved table" in result.errors[0].lower()
    assert "user_credentials" in result.errors[0]


def test_reject_unapproved_column():
    """Verify rejection of queries referencing non-existent columns (e.g. hallucinated revenue column)."""
    sql = "SELECT id, revenue FROM orders;"
    result = validate_sql(sql, schema_allowlist=SAMPLE_ALLOWLIST)

    assert not result.is_valid
    assert result.status == "rejected_unknown_schema_reference"
    assert "unapproved column" in result.errors[0].lower()
    assert "revenue" in result.errors[0]


def test_reject_syntax_error():
    """Verify rejection of malformed or invalid SQL syntax."""
    sql = "SELECT FROM WHERE GROUP HAVING;"
    result = validate_sql(sql, schema_allowlist=SAMPLE_ALLOWLIST)

    assert not result.is_valid
    assert result.status == "rejected_invalid_sql"
    assert "parsing error" in result.errors[0].lower()
