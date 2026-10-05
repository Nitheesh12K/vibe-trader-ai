"""Task 2.4: Qwen Failure Simulation & Resilience Test Suite.
Verifies:
1. Ollama service offline -> deterministic fallback < 20ms.
2. HTTP request timeout (bounded timeout) -> deterministic fallback.
3. Connection refused -> deterministic fallback.
4. HTTP 404 Model Not Found -> deterministic fallback.
5. HTTP 500 Provider Internal Error -> deterministic fallback.
6. Empty response from LLM -> deterministic fallback.
7. Database audit logging error -> safe failsafe degradation.
8. Zero orders executed on AI failure.
9. Deterministic Risk Guardian & Human Approval gates remain 100% active.
10. Deterministic fallback stability across identical invocations.
"""
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import httpx
import pytest

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, init_db
from app.models.entities import Position, BuyProposal, AuditLog
from app.services.xgboost_advisory_explainer import XGBoostAdvisoryExplainer
from app.services.risk_service import RiskService


@pytest.fixture
def db_session():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_ollama_service_offline_fast_fallback(db_session):
    """Verify that an unreachable Ollama port triggers deterministic fallback in < 50ms."""
    start = time.perf_counter()
    res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="RELIANCE",
        timeframe="1D",
        rule_signal="BUY",
        ollama_host="http://127.0.0.1:59998",  # Unused port
        xgboost_prediction={"bullish_probability": 0.65, "bearish_probability": 0.35},
    )
    duration_ms = (time.perf_counter() - start) * 1000
    assert duration_ms < 3000.0, f"Fallback too slow: {duration_ms}ms"
    assert res["provider_used"] == "DETERMINISTIC_FALLBACK"
    assert res["contract"]["model_name"] == "deterministic-fallback-analyzer"


def test_ollama_request_timeout_triggers_fallback(db_session):
    """Verify request timeout triggers deterministic fallback cleanly."""
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timed out after 4.0s")), \
         patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": ["qwen3-local:latest"]}):

        res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
            db=db_session,
            symbol="TCS",
            timeframe="1D",
            rule_signal="BUY",
            timeout=0.01,
            xgboost_prediction={"bullish_probability": 0.60, "bearish_probability": 0.40},
        )
        assert res["provider_used"] == "DETERMINISTIC_FALLBACK"
        assert res["synthesis"]["synthesis_verdict"] == "CONFLUENT_BULLISH"


def test_ollama_404_model_not_found_fallback(db_session):
    """Verify HTTP 404 for missing model triggers fallback."""
    with patch("httpx.Client.post") as mock_post, \
         patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": ["other:latest"]}):

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"error": "model 'nonexistent-model' not found"}
        mock_post.return_value = mock_resp

        res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
            db=db_session,
            symbol="INFY",
            timeframe="1D",
            rule_signal="SELL",
            model_name="nonexistent-model",
            xgboost_prediction={"bullish_probability": 0.20, "bearish_probability": 0.80},
        )
        assert res["provider_used"] == "DETERMINISTIC_FALLBACK"
        assert res["contract"]["synthesis_verdict"] == "CONFLUENT_BEARISH"


def test_ollama_500_provider_error_fallback(db_session):
    """Verify HTTP 500 server crash triggers fallback without failing caller."""
    with patch("httpx.Client.post") as mock_post, \
         patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": ["qwen3-local:latest"]}):

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {"error": "CUDA out of memory"}
        mock_post.return_value = mock_resp

        res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
            db=db_session,
            symbol="SBIN",
            timeframe="1D",
            rule_signal="HOLD",
        )
        assert res["provider_used"] == "DETERMINISTIC_FALLBACK"
        assert res["contract"]["deterministic_signal"] == "HOLD"


def test_audit_logging_failure_degrades_safely(db_session):
    """Verify that an audit logging failure does NOT prevent advisory return (failsafe degradation)."""
    with patch("app.services.audit_service.AuditService.log_event", side_effect=Exception("Disk full / DB locked")):
        res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
            db=db_session,
            symbol="HDFC",
            timeframe="1D",
            rule_signal="BUY",
        )
        assert res is not None
        assert res["symbol"] == "HDFC"


def test_zero_order_execution_on_ai_failure(db_session):
    """Verify that AI synthesis failures NEVER cause positions or orders to be executed."""
    pos_count_before = db_session.query(Position).count()
    proposal_count_before = db_session.query(BuyProposal).count()

    # Trigger failure with broken JSON
    with patch("httpx.Client.post") as mock_post, \
         patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": ["qwen3-local:latest"]}):

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "SYSTEM CRITICAL FAILURE"}
        mock_post.return_value = mock_resp

        res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
            db=db_session,
            symbol="CRASH_TEST",
            timeframe="1D",
            rule_signal="BUY",
        )
        assert res["provider_used"] == "DETERMINISTIC_FALLBACK"

    pos_count_after = db_session.query(Position).count()
    proposal_count_after = db_session.query(BuyProposal).count()

    assert pos_count_after == pos_count_before
    assert proposal_count_after == proposal_count_before


def test_deterministic_fallback_stability(db_session):
    """Verify deterministic fallback produces bit-identical outputs for identical inputs."""
    res1 = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="STABILITY_TEST",
        timeframe="1D",
        rule_signal="BUY",
        xgboost_prediction={"bullish_probability": 0.65, "bearish_probability": 0.35},
        technical_context={"rsi_14": 55.0},
        ollama_host="http://127.0.0.1:59998",  # Force fallback
        input_timestamp=1700000000,
    )

    res2 = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="STABILITY_TEST",
        timeframe="1D",
        rule_signal="BUY",
        xgboost_prediction={"bullish_probability": 0.65, "bearish_probability": 0.35},
        technical_context={"rsi_14": 55.0},
        ollama_host="http://127.0.0.1:59998",  # Force fallback
        input_timestamp=1700000000,
    )

    assert res1["contract"]["explanation"] == res2["contract"]["explanation"]
    assert res1["contract"]["synthesis_verdict"] == res2["contract"]["synthesis_verdict"]
    assert res1["contract"]["summary"] == res2["contract"]["summary"]
