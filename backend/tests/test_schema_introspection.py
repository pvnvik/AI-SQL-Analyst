"""Tests for schema introspection and LLM prompt context formatting."""

import pytest
from sqlalchemy import Column, Integer, String, create_engine
from app.database.models import Base
from app.database.demo_seed import seed_database
from app.database.schema_introspection import (
    APPROVED_TABLES,
    clear_schema_cache,
    get_approved_schema_dict,
    get_schema_prompt_context,
    introspect_schema,
)


@pytest.fixture
def test_db_engine():
    """Create a clean in-memory SQLite database seeded with demo data."""
    clear_schema_cache()
    engine = create_engine("sqlite:///:memory:")
    seed_database(engine=engine, reset=True)
    yield engine
    clear_schema_cache()
    engine.dispose()


def test_schema_introspection_approved_tables(test_db_engine):
    """Test that all approved tables are introspected and have correct structure."""
    schema = introspect_schema(engine=test_db_engine, force_refresh=True)

    assert schema.dialect == "sqlite"
    assert set(schema.tables.keys()) == APPROVED_TABLES

    # Check customers table
    customers_tbl = schema.tables["customers"]
    col_names = [c.name for c in customers_tbl.columns]
    assert "id" in col_names
    assert "customer_name" in col_names
    assert "region" in col_names
    assert "city" in col_names
    assert "created_at" in col_names
    assert "id" in customers_tbl.primary_keys

    # Check products table
    products_tbl = schema.tables["products"]
    prod_cols = [c.name for c in products_tbl.columns]
    assert "product_name" in prod_cols
    assert "category" in prod_cols
    assert "unit_price" in prod_cols

    # Check orders table
    orders_tbl = schema.tables["orders"]
    order_cols = [c.name for c in orders_tbl.columns]
    assert "customer_id" in order_cols
    assert "order_date" in order_cols
    assert "status" in order_cols

    # Check order_items table
    items_tbl = schema.tables["order_items"]
    item_cols = [c.name for c in items_tbl.columns]
    assert "order_id" in item_cols
    assert "product_id" in item_cols
    assert "quantity" in item_cols
    assert "unit_price" in item_cols
    assert "discount_amount" in item_cols


def test_schema_filters_unapproved_tables(test_db_engine):
    """Ensure internal or unapproved tables are excluded from introspection."""
    # Create an unapproved table in the database
    class SecretConfig(Base):
        __tablename__ = "internal_secrets"
        id = Column(Integer, primary_key=True)
        secret_key = Column(String(50))

    SecretConfig.__table__.create(test_db_engine)

    schema = introspect_schema(engine=test_db_engine, force_refresh=True)
    assert "internal_secrets" not in schema.tables
    assert set(schema.tables.keys()) == APPROVED_TABLES


def test_schema_prompt_context_includes_revenue_definition(test_db_engine):
    """Test that LLM schema context prompt contains exact revenue rules and table details."""
    context = get_schema_prompt_context(engine=test_db_engine, force_refresh=True)

    assert "REVENUE DEFINITION" in context
    assert "quantity * unit_price - discount_amount" in context
    assert "There is NO 'revenue' or 'total_amount' column" in context
    assert "customers" in context
    assert "products" in context
    assert "orders" in context
    assert "order_items" in context


def test_approved_schema_dict(test_db_engine):
    """Verify dictionary mapping table names to column lists for SQL AST validation."""
    schema_dict = get_approved_schema_dict(engine=test_db_engine)
    assert "customers" in schema_dict
    assert "region" in schema_dict["customers"]
    assert "unit_price" in schema_dict["order_items"]
    assert "discount_amount" in schema_dict["order_items"]
