"""Tests for safe read-only SQL query executor."""

import pytest
from sqlalchemy import create_engine
from app.database.demo_seed import seed_database
from app.database.query_executor import execute_fixed_safe_query, execute_query


@pytest.fixture
def test_db_engine():
    """Create in-memory SQLite database seeded with retail demo data."""
    engine = create_engine("sqlite:///:memory:")
    seed_database(engine=engine, reset=True)
    yield engine
    engine.dispose()


def test_execute_safe_select_query(test_db_engine):
    """Test executing a valid SELECT query against the seeded database."""
    sql = "SELECT category, COUNT(*) as prod_count FROM products GROUP BY category ORDER BY prod_count DESC;"
    result = execute_query(sql, engine=test_db_engine)

    assert result.is_success
    assert result.error is None
    assert result.columns == ["category", "prod_count"]
    assert len(result.rows) > 0
    assert result.row_count == len(result.rows)
    assert result.duration_ms >= 0
    assert result.truncated is False


def test_execute_fixed_safe_query(test_db_engine):
    """Test execution of the fixed safe query defined in query_executor."""
    result = execute_fixed_safe_query(engine=test_db_engine)

    assert result.is_success
    assert result.error is None
    assert "region" in result.columns
    assert "customer_count" in result.columns
    assert "total_orders" in result.columns
    assert result.row_count > 0


def test_row_capping_and_truncation_flag(test_db_engine):
    """Verify that results exceeding max_rows are capped and flagged as truncated."""
    # 15 products exist, test with max_rows=5
    sql = "SELECT id, product_name, unit_price FROM products ORDER BY id;"
    result = execute_query(sql, engine=test_db_engine, max_rows=5)

    assert result.is_success
    assert result.row_count == 5
    assert len(result.rows) == 5
    assert result.truncated is True


def test_handles_syntax_and_missing_table_gracefully(test_db_engine):
    """Verify that database errors return sanitized error messages without exceptions."""
    sql = "SELECT * FROM non_existent_table_xyz;"
    result = execute_query(sql, engine=test_db_engine)

    assert not result.is_success
    assert result.error is not None
    assert "non_existent_table_xyz" in result.error
    assert result.row_count == 0
    assert result.rows == []
    assert result.columns == []


def test_revenue_calculation_query(test_db_engine):
    """Test query calculating revenue according to the canonical definition."""
    sql = """
    SELECT 
        p.product_name,
        ROUND(SUM(oi.quantity * oi.unit_price - oi.discount_amount), 2) AS total_revenue
    FROM products p
    JOIN order_items oi ON p.id = oi.product_id
    GROUP BY p.product_name
    ORDER BY total_revenue DESC
    LIMIT 5;
    """
    result = execute_query(sql, engine=test_db_engine)

    assert result.is_success
    assert result.columns == ["product_name", "total_revenue"]
    assert len(result.rows) <= 5
    # Revenue should be positive numbers
    for row in result.rows:
        assert float(row["total_revenue"]) > 0
