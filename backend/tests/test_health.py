"""Tests for the health check and root endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client: TestClient):
    """Test that GET / returns 200 with service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["app"] == "QueryPilot API"
    assert "health_check" in data


def test_health_endpoint_contract(client: TestClient):
    """Test GET /api/health response format and contract compliance."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    # Core top-level contract
    assert data["status"] == "ok"
    assert "app_env" in data
    assert "version" in data
    assert "checks" in data

    # Checks structure
    checks = data["checks"]
    assert isinstance(checks["gemini_configured"], bool)
    assert isinstance(checks["database_configured"], bool)
    assert isinstance(checks["langsmith_configured"], bool)
    assert isinstance(checks["gemini_model"], str)
    assert isinstance(checks["database_dialect"], str)


def test_health_endpoint_no_secret_leakage(client: TestClient):
    """Verify that no sensitive API keys or full database credentials leak."""
    response = client.get("/api/health")
    raw_text = response.text
    settings = get_settings()

    # If an actual key is set in the environment, ensure it is NOT in the response
    if settings.google_api_key:
        assert settings.google_api_key not in raw_text
    if settings.langsmith_api_key:
        assert settings.langsmith_api_key not in raw_text

    # Ensure passwords or complete raw database connection strings are never leaked
    assert "password" not in raw_text.lower()
    assert "change_me" not in raw_text
