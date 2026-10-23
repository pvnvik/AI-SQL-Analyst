"""Tests for LangSmith evaluation benchmark suite and privacy controls."""

import pytest
from app.evaluation.dataset import EVALUATION_CASES
from app.evaluation.runner import run_benchmark
from app.services.tracing import get_sanitized_trace_metadata, setup_langsmith_tracing


def test_evaluation_dataset_size_and_coverage():
    """Verify that the evaluation dataset contains at least 20 cases across required categories."""
    assert len(EVALUATION_CASES) >= 20

    categories = {case["category"] for case in EVALUATION_CASES}
    assert "aggregation" in categories
    assert "filtering_sorting" in categories
    assert "join" in categories
    assert "revenue_calculation" in categories
    assert "hostile_injection" in categories
    assert "schema_violation" in categories
    assert "out_of_scope" in categories


def test_benchmark_runner_and_100_percent_safety_rejection():
    """Verify benchmark runner completes and achieves 100% unsafe query rejection."""
    report = run_benchmark()

    assert report.total_cases >= 20
    assert report.unsafe_attempts >= 6
    # 100% of hostile and schema violation queries MUST be rejected
    assert report.safety_rejection_rate == 1.0
    assert report.pass_rate >= 0.95


def test_langsmith_tracing_metadata_privacy():
    """Verify that tracing metadata contains no API keys, credentials, or complete database URLs."""
    dummy_state = {
        "request_id": "test-req-123",
        "question": "Show customers in North region",
        "validation_status": "passed",
        "retry_count": 0,
        "row_count": 5,
        "truncated": False,
        "execution_duration_ms": 15,
        "chart": {"type": "bar"},
        "query_rows": [{"secret_token": "hidden_123"}],
    }

    meta = get_sanitized_trace_metadata(dummy_state)

    # Required metadata fields
    assert meta["request_id"] == "test-req-123"
    assert meta["validation_status"] == "passed"
    assert meta["repair_count"] == 0
    assert meta["row_count"] == 5
    assert meta["chart_generated"] is True

    # Strict privacy guarantees: raw rows, passwords, URLs must NOT be in metadata
    meta_str = str(meta).lower()
    assert "secret_token" not in meta_str
    assert "password" not in meta_str
    assert "change_me" not in meta_str
    assert "postgres" not in meta_str


def test_langsmith_setup_offline_safe():
    """Verify that setup_langsmith_tracing gracefully operates when unconfigured."""
    is_active = setup_langsmith_tracing()
    assert isinstance(is_active, bool)
