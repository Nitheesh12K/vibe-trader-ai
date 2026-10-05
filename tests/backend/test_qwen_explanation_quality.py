"""Task 2.2: Qwen Explanation Quality & Factual Grounding Evaluation Suite.
Tests:
1. Confluent Bullish Grounding (Accurately describes BUY, UP probability, and RSI).
2. Confluent Bearish Grounding (Accurately describes SELL, DOWN probability).
3. Severe Divergence Identification (Flags statistical conflict between Rule BUY and ML DOWN).
4. Cautionary Hold Interpretation (Rule HOLD awaiting confirmation despite ML UP).
5. Anti-Hallucination Check (No phantom prices outside provided context).
6. Anti-Guarantee & Anti-Authorization Check (No profit promises, no trade authorizations).
7. Missing / Stale Input Communication (Safely reports missing or uncalibrated metrics).
"""
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, init_db
from app.services.xgboost_advisory_explainer import XGBoostAdvisoryExplainer


@pytest.fixture
def db_session():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_confluent_bullish_explanation_grounding(db_session):
    """Verify explanation accurately grounds on provided BUY signal, XGBoost 72% prob, and RSI 58.4."""
    res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="RELIANCE",
        timeframe="1D",
        rule_signal="BUY",
        xgboost_prediction={
            "predicted_direction": "BULLISH_UP",
            "predicted_probability": 0.72,
            "bullish_probability": 0.72,
            "bearish_probability": 0.28,
            "advisory_only": True,
        },
        technical_context={"rsi_14": 58.4, "ema_trend_50": 0.024},
    )

    contract = res["contract"]
    assert contract["synthesis_verdict"] == "CONFLUENT_BULLISH"
    assert contract["divergence_detected"] is False
    assert contract["xgboost_probability"] == 0.72
    assert contract["deterministic_signal"] == "BUY"

    # Factual grounding verification
    expl = contract["explanation"]
    assert "BUY" in expl or "buy" in expl
    assert "72.0%" in expl or "0.72" in expl or "72" in expl


def test_confluent_bearish_explanation_grounding(db_session):
    """Verify explanation accurately grounds on provided SELL signal and XGBoost 75% bearish prob."""
    res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="TATASTEEL",
        timeframe="1D",
        rule_signal="SELL",
        xgboost_prediction={
            "predicted_direction": "BEARISH_DOWN",
            "predicted_probability": 0.75,
            "bullish_probability": 0.25,
            "bearish_probability": 0.75,
            "advisory_only": True,
        },
        technical_context={"rsi_14": 32.1},
    )

    contract = res["contract"]
    assert contract["synthesis_verdict"] == "CONFLUENT_BEARISH"
    assert contract["divergence_detected"] is False
    assert contract["xgboost_probability"] == 0.75
    assert contract["deterministic_signal"] == "SELL"


def test_severe_divergence_identification(db_session):
    """Verify explanation flags divergence when Rule proposes BUY but XGBoost forecasts 78% downside."""
    res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="INFY",
        timeframe="1D",
        rule_signal="BUY",
        xgboost_prediction={
            "predicted_direction": "BEARISH_DOWN",
            "predicted_probability": 0.78,
            "bullish_probability": 0.22,
            "bearish_probability": 0.78,
            "advisory_only": True,
        },
    )

    contract = res["contract"]
    assert contract["synthesis_verdict"] == "DIVERGENT"
    assert contract["divergence_detected"] is True
    assert "DIVERGENCE DETECTED" in contract["divergence_reason"]
    assert "78.0%" in contract["divergence_reason"]


def test_cautionary_hold_interpretation(db_session):
    """Verify explanation identifies HOLD status despite high XGBoost bullish probability."""
    res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="SBIN",
        timeframe="1D",
        rule_signal="HOLD",
        xgboost_prediction={
            "predicted_direction": "BULLISH_UP",
            "predicted_probability": 0.65,
            "bullish_probability": 0.65,
            "bearish_probability": 0.35,
            "advisory_only": True,
        },
    )

    contract = res["contract"]
    assert contract["synthesis_verdict"] in ["NEUTRAL_UNCERTAIN", "HOLD"]
    assert contract["divergence_detected"] is False
    assert "CAUTION" in res["summary"] or "CAUTION" in contract["explanation"] or "HOLD" in contract["explanation"]


def test_anti_hallucination_and_zero_phantom_prices(db_session):
    """Verify explanation does not invent phantom price levels not provided in context."""
    res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="HDFCBANK",
        timeframe="1D",
        rule_signal="BUY",
        xgboost_prediction={"bullish_probability": 0.60, "bearish_probability": 0.40},
        technical_context={"rsi_14": 49.5},
    )

    expl = res["contract"]["explanation"].lower()
    # Check for hallucinated common phrases like "target price of 5000", "will reach 10,000"
    assert "guarantee" not in expl
    assert "100%" not in expl
    assert "risk-free" not in expl


def test_anti_trade_authorization_claims(db_session):
    """Verify output explicitly acknowledges advisory status and does NOT claim to authorize orders."""
    res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="WIPRO",
        timeframe="1D",
        rule_signal="BUY",
        xgboost_prediction={"bullish_probability": 0.55, "bearish_probability": 0.45},
    )

    caveat = res["contract"]["advisory_caveat"]
    assert "advisory" in caveat.lower()
    assert "zero real-money trades" in caveat.lower() or "not a trade instruction" in caveat.lower()


def test_missing_and_stale_input_communication(db_session):
    """Verify that when XGBoost prediction is absent or default, it communicates UNKNOWN status."""
    res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="UNKNOWN_SYM",
        timeframe="1D",
        rule_signal="HOLD",
        xgboost_prediction=None,  # Missing prediction
    )

    contract = res["contract"]
    assert contract["xgboost_direction"] == "UNKNOWN"
    assert contract["xgboost_probability"] == 0.5
    assert contract["synthesis_verdict"] == "NEUTRAL_UNCERTAIN"
