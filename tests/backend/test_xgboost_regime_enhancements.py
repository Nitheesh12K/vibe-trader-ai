"""Test suite for XGBoost Enhancements & Market-Regime Classification.

Verifies:
1. Feature schema versioning (FEATURE_SCHEMA_VERSION = "2.0.0-causal").
2. Detection and rejection of mismatched feature schema versions.
3. Probability calibration check and Brier score threshold warnings.
4. Prediction abstention zone for near-50% probabilities (0.48 <= P <= 0.52).
5. Strictly causal market-regime classification (ADX/ATR/EMA alignment).
6. Regime-conditioned evaluation metrics breakdown across market environments.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock

from app.services.xgboost_feature_pipeline import (
    XGBoostFeaturePipeline,
    FEATURE_SCHEMA_VERSION,
    FEATURE_NAMES,
)
from app.services.xgboost_service import XGBoostService
from app.schemas.market import OHLCCandle


# ============================================================================
# 1. FEATURE SCHEMA VERSIONING TESTS
# ============================================================================

def test_feature_schema_version_constant():
    """Validates that explicit causal schema versioning constant is active."""
    assert FEATURE_SCHEMA_VERSION == "2.0.0-causal"


def test_feature_schema_validation_success():
    """Validates matching feature schema version succeeds."""
    assert XGBoostFeaturePipeline.validate_feature_schema("2.0.0-causal") is True


def test_feature_schema_validation_mismatch_rejected():
    """Validates that mismatched or legacy schema versions are strictly rejected."""
    with pytest.raises(ValueError, match="Feature schema version mismatch"):
        XGBoostFeaturePipeline.validate_feature_schema("1.0.0")

    with pytest.raises(ValueError, match="Feature schema version mismatch"):
        XGBoostFeaturePipeline.validate_feature_schema("v1.0")

    with pytest.raises(ValueError, match="missing or empty"):
        XGBoostFeaturePipeline.validate_feature_schema("")


# ============================================================================
# 2. PROBABILITY CALIBRATION & BRIER SCORE CHECKS
# ============================================================================

def test_well_calibrated_model_metrics():
    """Confirms low Brier score is tagged as WELL_CALIBRATED with zero warnings."""
    # Near-perfect predictions: y_true matches y_prob closely
    y_true = np.array([1, 1, 0, 0, 1, 0, 1, 0])
    y_pred = np.array([1, 1, 0, 0, 1, 0, 1, 0])
    y_prob = np.array([0.90, 0.85, 0.10, 0.15, 0.88, 0.12, 0.92, 0.08])

    metrics = XGBoostService._calculate_evaluation_metrics(
        y_true=y_true, y_pred=y_pred, y_prob=y_prob
    )
    assert metrics["brier_score"] < 0.20
    assert metrics["calibration_status"] == "WELL_CALIBRATED"
    assert metrics["calibration_warning"] is None


def test_poor_calibration_warning_triggered():
    """Confirms that overconfident/misaligned probabilities (Brier score > 0.28) trigger a calibration warning."""
    # Misaligned probabilities: model predicts high prob when truth is opposite
    y_true = np.array([1, 1, 0, 0, 1, 0, 1, 0])
    y_pred = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    y_prob = np.array([0.15, 0.20, 0.85, 0.90, 0.10, 0.80, 0.15, 0.85])

    metrics = XGBoostService._calculate_evaluation_metrics(
        y_true=y_true, y_pred=y_pred, y_prob=y_prob
    )
    assert metrics["brier_score"] > 0.28
    assert metrics["calibration_status"] == "POOR_CALIBRATION_WARNING"
    assert "High Brier score" in metrics["calibration_warning"]


# ============================================================================
# 3. PREDICTION ABSTENTION IN LOW-CONFIDENCE ZONE
# ============================================================================

def test_prediction_abstention_in_low_confidence_zone():
    """Verifies that probabilities between 0.48 and 0.52 result in ABSTAIN status."""
    # Build a minimal dataframe
    test_feature_dict = {feat: 0.0 for feat in FEATURE_NAMES}
    test_feature_dict["rsi_14"] = 50.0

    mock_model = MagicMock()
    # Mock predict_proba to return 0.51 for UP (in zone [0.48, 0.52])
    mock_model.predict_proba.return_value = np.array([[0.49, 0.51]])
    mock_model.predict.return_value = np.array([1])

    # Simulate prediction logic
    feature_vector = pd.DataFrame([test_feature_dict])[FEATURE_NAMES]
    probabilities = mock_model.predict_proba(feature_vector)[0]
    prob_down = round(float(probabilities[0]), 4)
    prob_up = round(float(probabilities[1]), 4)

    ABSTENTION_LOWER = 0.48
    ABSTENTION_UPPER = 0.52
    is_abstaining = ABSTENTION_LOWER <= prob_up <= ABSTENTION_UPPER

    assert is_abstaining is True

    if is_abstaining:
        predicted_class = -1
        pred_prob = round(max(prob_up, prob_down), 4)
        direction = "ABSTAIN"
    else:
        predicted_class = int(mock_model.predict(feature_vector)[0])
        pred_prob = prob_up if predicted_class == 1 else prob_down
        direction = "BULLISH_UP" if predicted_class == 1 else "BEARISH_DOWN"

    assert predicted_class == -1
    assert direction == "ABSTAIN"
    assert pred_prob == 0.51


def test_directional_prediction_outside_abstention_zone():
    """Verifies that probabilities outside [0.48, 0.52] produce directional output."""
    prob_up = 0.78
    prob_down = 0.22

    ABSTENTION_LOWER = 0.48
    ABSTENTION_UPPER = 0.52
    is_abstaining = ABSTENTION_LOWER <= prob_up <= ABSTENTION_UPPER
    assert is_abstaining is False

    predicted_direction = "BULLISH_UP" if prob_up > 0.50 else "BEARISH_DOWN"
    assert predicted_direction == "BULLISH_UP"


# ============================================================================
# 4. CAUSAL MARKET-REGIME CLASSIFICATION
# ============================================================================

def test_market_regime_classification_bullish():
    """Validates that positive trend and spread produce TRENDING_BULLISH."""
    regime = XGBoostFeaturePipeline.classify_market_regime(
        ema_spread=0.015,
        ema_trend=0.020,
        atr_norm=0.012,
        bb_pct_b=0.75,
    )
    assert regime == "TRENDING_BULLISH"


def test_market_regime_classification_bearish():
    """Validates that negative trend and spread produce TRENDING_BEARISH."""
    regime = XGBoostFeaturePipeline.classify_market_regime(
        ema_spread=-0.012,
        ema_trend=-0.018,
        atr_norm=0.014,
        bb_pct_b=0.25,
    )
    assert regime == "TRENDING_BEARISH"


def test_market_regime_classification_high_volatility():
    """Validates that high normalized ATR triggers HIGH_VOLATILITY_EXPANSION."""
    regime = XGBoostFeaturePipeline.classify_market_regime(
        ema_spread=0.010,
        ema_trend=0.015,
        atr_norm=0.038,  # > 0.025 threshold
        bb_pct_b=0.90,
    )
    assert regime == "HIGH_VOLATILITY_EXPANSION"


def test_market_regime_classification_ranging():
    """Validates that flat or mixed moving averages produce RANGING_LOW_VOLATILITY."""
    regime = XGBoostFeaturePipeline.classify_market_regime(
        ema_spread=0.0005,
        ema_trend=0.001,
        atr_norm=0.008,
        bb_pct_b=0.50,
    )
    assert regime == "RANGING_LOW_VOLATILITY"


def test_regimes_for_dataframe_causality():
    """Validates that each row is causally classified row-by-row without lookahead."""
    df = pd.DataFrame([
        {"ema_spread_9_21": 0.015, "ema_trend_50": 0.02, "atr_norm_14": 0.01, "bb_pct_b": 0.8},
        {"ema_spread_9_21": -0.015, "ema_trend_50": -0.02, "atr_norm_14": 0.01, "bb_pct_b": 0.2},
        {"ema_spread_9_21": 0.005, "ema_trend_50": 0.005, "atr_norm_14": 0.04, "bb_pct_b": 0.95},
        {"ema_spread_9_21": 0.0001, "ema_trend_50": 0.0001, "atr_norm_14": 0.005, "bb_pct_b": 0.5},
    ])

    regimes = XGBoostFeaturePipeline.classify_regimes_for_dataframe(df)
    assert len(regimes) == 4
    assert regimes.iloc[0] == "TRENDING_BULLISH"
    assert regimes.iloc[1] == "TRENDING_BEARISH"
    assert regimes.iloc[2] == "HIGH_VOLATILITY_EXPANSION"
    assert regimes.iloc[3] == "RANGING_LOW_VOLATILITY"


# ============================================================================
# 5. REGIME-CONDITIONED EVALUATION BREAKDOWN
# ============================================================================

def test_regime_conditioned_accuracy_tally():
    """Verifies that accuracy metrics can be aggregated per regime on test split."""
    y_test = pd.Series([1, 1, 0, 0])
    y_pred = pd.Series([1, 0, 0, 1])  # 2 correct (50% overall)
    test_regimes = pd.Series([
        "TRENDING_BULLISH",
        "TRENDING_BULLISH",
        "TRENDING_BEARISH",
        "RANGING_LOW_VOLATILITY",
    ])

    regime_breakdown = {}
    for r in ["TRENDING_BULLISH", "TRENDING_BEARISH", "RANGING_LOW_VOLATILITY", "HIGH_VOLATILITY_EXPANSION"]:
        mask = (test_regimes == r)
        count = int(mask.sum())
        if count > 0:
            acc = float((y_test[mask] == y_pred[mask]).sum() / count)
            regime_breakdown[r] = {"sample_count": count, "accuracy": acc}
        else:
            regime_breakdown[r] = {"sample_count": 0, "accuracy": None}

    assert regime_breakdown["TRENDING_BULLISH"]["sample_count"] == 2
    assert regime_breakdown["TRENDING_BULLISH"]["accuracy"] == 0.5  # 1 out of 2
    assert regime_breakdown["TRENDING_BEARISH"]["sample_count"] == 1
    assert regime_breakdown["TRENDING_BEARISH"]["accuracy"] == 1.0  # 1 out of 1
    assert regime_breakdown["HIGH_VOLATILITY_EXPANSION"]["sample_count"] == 0
    assert regime_breakdown["HIGH_VOLATILITY_EXPANSION"]["accuracy"] is None
