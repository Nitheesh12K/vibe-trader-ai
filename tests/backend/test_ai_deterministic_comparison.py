"""Test suite for AI vs Deterministic Strategy Comparison & Divergence Detection.

Verifies:
1. Concurrence agreement heuristics across BUY, SELL, HOLD.
2. Divergence detection thresholds and warning reasons.
3. Deduplicated divergence alert dispatching.
4. Robust error handling for invalid/missing signals and stale timestamps.
5. Absolute safety invariants:
   - AI agreement NEVER bypasses human approval.
   - AI agreement NEVER overrides Risk Guardian rejection.
   - Divergence NEVER triggers order execution.
6. API endpoint querying, filtering, and summary statistics.
"""
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.models.entities import (
    AIStrategyComparisonRecordModel,
    AlertEvent,
    AuditLog,
)
from app.schemas.ai_comparison import (
    AIComparisonEvaluationRequest,
    AIComparisonFilter,
)
from app.services.ai_comparison_service import AIComparisonService
from main import app


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ============================================================================
# 1. CONCURRENCE & DIVERGENCE HEURISTICS
# ============================================================================

def test_concurrence_agreement_cases():
    """Confirms AGREE verdict when deterministic and AI signals align."""
    # BUY alignment
    status, reason = AIComparisonService.evaluate_concurrence(
        deterministic_signal="BUY",
        deterministic_confidence=0.80,
        xgboost_direction="UP",
        xgboost_probability=0.78,
        qwen_recommendation="BUY",
    )
    assert status == "AGREE"
    assert reason is None

    # SELL alignment
    status, reason = AIComparisonService.evaluate_concurrence(
        deterministic_signal="SELL",
        deterministic_confidence=0.85,
        xgboost_direction="DOWN",
        xgboost_probability=0.25,
        qwen_recommendation="SELL",
    )
    assert status == "AGREE"
    assert reason is None

    # HOLD alignment
    status, reason = AIComparisonService.evaluate_concurrence(
        deterministic_signal="HOLD",
        deterministic_confidence=0.50,
        xgboost_direction="ABSTAIN",
        xgboost_probability=0.50,
        qwen_recommendation="HOLD",
    )
    assert status == "AGREE"
    assert reason is None


def test_divergence_detection_cases():
    """Confirms DIVERGE verdict when deterministic signal is contradicted."""
    # Deterministic BUY contradicted by low XGBoost probability (<0.40)
    status, reason = AIComparisonService.evaluate_concurrence(
        deterministic_signal="BUY",
        deterministic_confidence=0.75,
        xgboost_direction="DOWN",
        xgboost_probability=0.32,
        qwen_recommendation="BUY",
    )
    assert status == "DIVERGE"
    assert "low XGBoost probability" in reason

    # Deterministic BUY contradicted by Qwen SELL
    status, reason = AIComparisonService.evaluate_concurrence(
        deterministic_signal="BUY",
        deterministic_confidence=0.75,
        xgboost_direction="UP",
        xgboost_probability=0.65,
        qwen_recommendation="SELL",
    )
    assert status == "DIVERGE"
    assert "Qwen advisory recommendation" in reason

    # Deterministic SELL contradicted by bullish XGBoost (>0.60)
    status, reason = AIComparisonService.evaluate_concurrence(
        deterministic_signal="SELL",
        deterministic_confidence=0.80,
        xgboost_direction="UP",
        xgboost_probability=0.72,
        qwen_recommendation="SELL",
    )
    assert status == "DIVERGE"
    assert "high bullish XGBoost probability" in reason

    # Deterministic SELL contradicted by Qwen BUY
    status, reason = AIComparisonService.evaluate_concurrence(
        deterministic_signal="SELL",
        deterministic_confidence=0.70,
        xgboost_direction="DOWN",
        xgboost_probability=0.40,
        qwen_recommendation="BUY",
    )
    assert status == "DIVERGE"
    assert "Qwen BUY recommendation" in reason


def test_cautionary_states():
    """Confirms CAUTIONARY status when signals show weak confidence or abstention."""
    # BUY with weak probability (0.45 in zone 0.40-0.55)
    status, reason = AIComparisonService.evaluate_concurrence(
        deterministic_signal="BUY",
        deterministic_confidence=0.70,
        xgboost_direction="UP",
        xgboost_probability=0.48,
        qwen_recommendation="BUY",
    )
    assert status == "CAUTIONARY"
    assert "cautionary zone" in reason

    # HOLD while XGBoost is strongly directional
    status, reason = AIComparisonService.evaluate_concurrence(
        deterministic_signal="HOLD",
        deterministic_confidence=0.40,
        xgboost_direction="UP",
        xgboost_probability=0.88,
        qwen_recommendation="HOLD",
    )
    assert status == "CAUTIONARY"
    assert "strong directional probability" in reason


def test_missing_or_invalid_signals():
    """Confirms rejection and exceptions on missing or malformed signals."""
    with pytest.raises(ValueError, match="Deterministic signal must be provided"):
        AIComparisonService.evaluate_concurrence(
            deterministic_signal="",
            deterministic_confidence=0.5,
        )

    with pytest.raises(ValueError, match="Invalid deterministic signal 'INVALID_SIG'"):
        AIComparisonService.evaluate_concurrence(
            deterministic_signal="INVALID_SIG",
            deterministic_confidence=0.5,
        )


# ============================================================================
# 2. DEDUPLICATED DIVERGENCE ALERTS
# ============================================================================

def test_divergence_alert_dispatching_and_deduplication(test_db):
    """Verifies divergence creates an AlertEvent and suppresses subsequent duplicates within cooldown."""
    AIComparisonService._alert_cooldown_cache.clear()

    req = AIComparisonEvaluationRequest(
        symbol="TATASTEEL",
        market="NSE",
        timeframe="1D",
        deterministic_strategy_name="STRAT-EMA-CROSS",
        deterministic_signal="BUY",
        deterministic_confidence=0.80,
        xgboost_predicted_direction="DOWN",
        xgboost_probability=0.25,
        qwen_synthesized_recommendation="SELL",
    )

    # First divergence evaluation
    rec1 = AIComparisonService.record_comparison(test_db, req)
    assert rec1.concurrence_status == "DIVERGE"

    alerts = test_db.query(AlertEvent).filter(AlertEvent.symbol == "TATASTEEL").all()
    assert len(alerts) == 1
    assert alerts[0].alert_type == "AI_DIVERGENCE"
    assert "AI Divergence Alert: TATASTEEL" in alerts[0].title

    # Second evaluation immediately afterwards (within 300s cooldown)
    rec2 = AIComparisonService.record_comparison(test_db, req)
    assert rec2.concurrence_status == "DIVERGE"

    # Count of alerts must still be 1 due to deduplication
    alerts_after = test_db.query(AlertEvent).filter(AlertEvent.symbol == "TATASTEEL").all()
    assert len(alerts_after) == 1


# ============================================================================
# 3. STALE TIMESTAMP DETECTION
# ============================================================================

def test_stale_timestamp_handling(test_db):
    """Verifies that candle timestamps > 24 hours stale are flagged in notes."""
    ancient_timestamp = int(time.time()) - 150000  # ~41 hours ago

    req = AIComparisonEvaluationRequest(
        symbol="INFY",
        market="NSE",
        timeframe="1D",
        timestamp=ancient_timestamp,
        deterministic_strategy_name="STRAT-RSI-REV",
        deterministic_signal="BUY",
        deterministic_confidence=0.75,
        xgboost_predicted_direction="UP",
        xgboost_probability=0.80,
        qwen_synthesized_recommendation="BUY",
    )

    rec = AIComparisonService.record_comparison(test_db, req)
    assert rec.concurrence_status == "AGREE"
    assert "Stale input timestamp" in (rec.notes or "")


# ============================================================================
# 4. SAFETY INVARIANTS: ZERO BYPASS, RISK GUARDIAN SUPREMACY, ZERO AUTONOMY
# ============================================================================

def test_safety_invariants_human_approval_never_bypassed():
    """Guarantees that even with 100% agreement, human approval is strictly required."""
    check = AIComparisonService.verify_safety_invariants(
        concurrence_status="AGREE",
        human_approval_given=False,
        risk_guardian_verdict="PASSED",
    )
    assert check["allowed_to_execute"] is False
    assert any("Explicit human approval has not been granted" in r for r in check["block_reasons"])
    assert check["human_approval_required"] is True


def test_safety_invariants_risk_guardian_overrides_ai():
    """Guarantees that Risk Guardian rejection halts execution even if AI and Strategy agree."""
    check = AIComparisonService.verify_safety_invariants(
        concurrence_status="AGREE",
        human_approval_given=True,
        risk_guardian_verdict="REJECTED",
    )
    assert check["allowed_to_execute"] is False
    assert any("Risk Guardian rejected" in r for r in check["block_reasons"])
    assert check["risk_guardian_authoritative"] is True


def test_safety_invariants_divergence_never_triggers_trade():
    """Guarantees that divergence blocks order execution unconditionally."""
    check = AIComparisonService.verify_safety_invariants(
        concurrence_status="DIVERGE",
        human_approval_given=True,
        risk_guardian_verdict="PASSED",
    )
    assert check["allowed_to_execute"] is False
    assert any("Divergence between strategy and AI cannot execute" in r for r in check["block_reasons"])


# ============================================================================
# 5. API ENDPOINTS & SUMMARY METRICS
# ============================================================================

def test_ai_comparison_api_flow(client, test_db):
    """Tests POST evaluate and GET history summary via FastAPI test client."""
    now_ts = int(time.time())

    # Seed 3 records: 1 AGREE, 1 DIVERGE, 1 CAUTIONARY
    eval_payloads = [
        {
            "symbol": "RELIANCE",
            "market": "NSE",
            "timeframe": "1D",
            "timestamp": now_ts - 200,
            "deterministic_strategy_name": "STRAT-EMA-CROSS",
            "deterministic_signal": "BUY",
            "deterministic_confidence": 0.85,
            "xgboost_predicted_direction": "UP",
            "xgboost_probability": 0.82,
            "qwen_synthesized_recommendation": "BUY",
        },
        {
            "symbol": "RELIANCE",
            "market": "NSE",
            "timeframe": "1D",
            "timestamp": now_ts - 100,
            "deterministic_strategy_name": "STRAT-EMA-CROSS",
            "deterministic_signal": "BUY",
            "deterministic_confidence": 0.70,
            "xgboost_predicted_direction": "DOWN",
            "xgboost_probability": 0.30,
            "qwen_synthesized_recommendation": "SELL",
        },
        {
            "symbol": "TCS",
            "market": "NSE",
            "timeframe": "1D",
            "timestamp": now_ts,
            "deterministic_strategy_name": "STRAT-RSI-REV",
            "deterministic_signal": "HOLD",
            "deterministic_confidence": 0.50,
            "xgboost_predicted_direction": "UP",
            "xgboost_probability": 0.85,
            "qwen_synthesized_recommendation": "BUY",
        },
    ]

    for p in eval_payloads:
        resp = client.post("/api/research/ai-comparison/evaluate", json=p)
        assert resp.status_code == 200
        data = resp.json()
        assert "record_id" in data
        assert data["symbol"] == p["symbol"]

    # Query all records
    resp_all = client.get("/api/research/ai-comparison")
    assert resp_all.status_code == 200
    summary = resp_all.json()

    assert summary["total_records"] == 3
    assert summary["agreement_count"] == 1
    assert summary["divergence_count"] == 1
    assert summary["cautionary_count"] == 1
    assert abs(summary["agreement_rate"] - (1 / 3)) < 0.01
    assert abs(summary["divergence_rate"] - (1 / 3)) < 0.01
    assert len(summary["records"]) == 3

    # Query filtered by symbol=RELIANCE
    resp_rel = client.get("/api/research/ai-comparison?symbol=RELIANCE")
    assert resp_rel.status_code == 200
    rel_summary = resp_rel.json()
    assert rel_summary["total_records"] == 2
    assert rel_summary["agreement_count"] == 1
    assert rel_summary["divergence_count"] == 1

    # Query filtered by concurrence_status=DIVERGE
    resp_div = client.get("/api/research/ai-comparison?concurrence_status=DIVERGE")
    assert resp_div.status_code == 200
    div_summary = resp_div.json()
    assert div_summary["total_records"] == 1
    assert div_summary["divergence_count"] == 1
    assert div_summary["records"][0]["concurrence_status"] == "DIVERGE"
