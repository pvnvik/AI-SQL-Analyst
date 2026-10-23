"""Tests for GET /api/schema endpoint."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import connection
from app.database.demo_seed import seed_database
from app.database.schema_introspection import clear_schema_cache


@pytest.fixture
def client_with_db():
    """TestClient fixture with an active seeded database engine."""
    clear_schema_cache()
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    seed_database(engine=test_engine, reset=True)

    # Monkeypatch connection.get_engine to return our test_engine
    orig_get_engine = connection.get_engine
    connection.get_engine = lambda *args, **kwargs: test_engine

    with TestClient(app) as test_client:
        yield test_client

    connection.get_engine = orig_get_engine
    clear_schema_cache()
    test_engine.dispose()


def test_get_schema_contract(client_with_db: TestClient):
    """Test that GET /api/schema returns 200 and adheres to the API schema contract."""
    response = client_with_db.get("/api/schema")
    assert response.status_code == 200
    data = response.json()

    assert "dialect" in data
    assert "tables" in data
    assert "approved_tables_count" in data
    assert "revenue_rule" in data

    assert data["approved_tables_count"] == 4
    table_names = [t["name"] for t in data["tables"]]
    assert set(table_names) == {"customers", "products", "orders", "order_items"}

    # Ensure customers has region, city, customer_name
    customers_table = next(t for t in data["tables"] if t["name"] == "customers")
    col_names = [c["name"] for c in customers_table["columns"]]
    assert "customer_name" in col_names
    assert "region" in col_names

    # Check revenue rule explanation is present
    assert "quantity * unit_price - discount_amount" in data["revenue_rule"]
