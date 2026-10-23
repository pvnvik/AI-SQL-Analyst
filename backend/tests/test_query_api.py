"""Integration tests for POST /api/query endpoint."""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from app.api.schemas import ChartConfig
from app.database import connection
from app.database.demo_seed import seed_database
from app.database.schema_introspection import clear_schema_cache
from app.guardrails.output_models import GeneratedSQLOutput
from app.main import app


@pytest.fixture
def client_with_db():
    """TestClient fixture with an active seeded SQLite database."""
    clear_schema_cache()
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    seed_database(engine=test_engine, reset=True)

    orig_get_engine = connection.get_engine
    connection.get_engine = lambda *args, **kwargs: test_engine

    with TestClient(app) as test_client:
        yield test_client

    connection.get_engine = orig_get_engine
    clear_schema_cache()
    test_engine.dispose()


def test_query_input_validation(client_with_db: TestClient):
    """Test that requests with too short or invalid question return 422."""
    response = client_with_db.post("/api/query", json={"question": "hi"})
    assert response.status_code == 422


def test_query_non_data_question(client_with_db: TestClient):
    """Test that a non-data question is safely intercepted without running SQL."""
    response = client_with_db.post(
        "/api/query", json={"question": "What is the capital of France?"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["validation"]["status"] == "rejected_non_data_question"
    assert data["sql"] == ""
    assert data["rows"] == []
    assert "retail" in data["insight"].lower()


@patch("app.graph.nodes.generate_sql")
@patch("app.graph.nodes.analyze_results")
def test_query_valid_data_question(mock_analyze, mock_generate, client_with_db: TestClient):
    """Test end-to-end processing of a valid retail data question with mocked LLM."""
    mock_generate.return_value = GeneratedSQLOutput(
        sql="SELECT category, COUNT(*) AS total_products FROM products GROUP BY category ORDER BY total_products DESC;",
        explanation="Counts products by category",
        assumptions=[],
        confidence=0.97,
    )
    mock_analyze.return_value = "Retrieved product counts across retail categories."

    response = client_with_db.post(
        "/api/query",
        json={"question": "How many products do we have in each category?"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["request_id"] != ""
    assert data["validation"]["status"] == "passed"
    assert "products" in data["sql"]
    assert "category" in data["columns"]
    assert "total_products" in data["columns"]
    assert len(data["rows"]) > 0
    assert data["execution"]["row_count"] == len(data["rows"])
    assert data["execution"]["duration_ms"] >= 0
    assert data["insight"] == "Retrieved product counts across retail categories."
    assert data["chart"] is not None
    assert data["chart"]["type"] == "bar"
