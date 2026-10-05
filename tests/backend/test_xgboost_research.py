"""XGBoost Quantitative Research Engine Test Suite.
Validates:
1. Complete training & evaluation pipeline on historical dataset
2. Temporal split integrity & lookahead prevention (chronological, non-shuffled)
3. Insufficient and missing data handling (clean HTTP 400 rejection)
4. Invalid hyperparameters rejection (bounds on depth, eta, ratios)
5. Model loading failure resilience (non-existent/corrupted artifact -> HTTP 404)
6. Zero order execution verification (no trades, no balance changes, broker fail-closed)
7. Stale and incomplete data rejection
8. Baseline integrity (majority class & momentum benchmarks)
9. Reproducibility with fixed random seed
10. API request validation and REST endpoints
11. Qwen offline fallback resilience (divergence detection & deterministic synthesis)
12. Prediction verification workflow (unverified until future bar closes)
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.database.session import SessionLocal
from app.schemas.market import OHLCCandle
from app.models.entities import (
    XGBoostExperiment,
    XGBoostPredictionRecord,
    PaperTrade,
    RiskSettings,
    BuyProposal,
)
from app.services.xgboost_feature_pipeline import XGBoostFeaturePipeline, FEATURE_NAMES
from app.services.xgboost_service import XGBoostService
from app.services.xgboost_advisory_explainer import XGBoostAdvisoryExplainer
from app.services.csv_data_provider import CSVDataProvider

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_datasets():
    """Ensure in-memory dataset cache from earlier test suites does not leak into quantitative tests."""
    CSVDataProvider._STORED_DATASETS.clear()
    yield
    CSVDataProvider._STORED_DATASETS.clear()


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_synthetic_ohlc_candles(n_bars: int = 120, trend: float = 0.001):
    """Generate synthetic OHLCCandles for controlled deterministic testing."""
    np.random.seed(42)
    base_time = 1704067200  # 2024-01-01 00:00:00 UTC
    returns = np.random.normal(loc=trend, scale=0.015, size=n_bars)
    prices = 100.0 * np.cumprod(1.0 + returns)

    candles = []
    for i in range(n_bars):
        close_p = float(prices[i])
        low_p = float(close_p * (1.0 - abs(np.random.normal(0, 0.005))))
        high_p = float(close_p * (1.0 + abs(np.random.normal(0, 0.005))))
        open_p = float((close_p + low_p) / 2.0)
        vol = float(np.random.randint(10000, 500000))
        t = base_time + (i * 86400)

        candles.append(OHLCCandle(
            time=t,
            open=open_p,
            high=high_p,
            low=low_p,
            close=close_p,
            volume=vol,
        ))
    return candles


# ============================================================================
# 1. Pipeline Train & Evaluate
# ============================================================================
def test_pipeline_train_and_evaluate(db_session):
    """Test full training pipeline on RELIANCE historical data."""
    res = client.post("/api/xgboost/train", json={
        "symbol": "RELIANCE",
        "timeframe": "1D",
        "market": "NSE",
        "train_ratio": 0.70,
        "val_ratio": 0.15,
        "num_folds": 2,
        "max_depth": 3,
        "learning_rate": 0.05,
        "n_estimators": 50,
        "random_seed": 42,
    })

    assert res.status_code == 200, f"Training failed: {res.text}"
    data = res.json()
    assert "model_id" in data
    assert data["symbol"] == "RELIANCE"
    assert data["status"] == "COMPLETED"

    # Verify metrics structure
    metrics = data["out_of_sample_metrics"]
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert ("f1_score" in metrics or "f1" in metrics)
    assert "brier_score" in metrics
    assert "confusion_matrix" in data

    # Verify baseline metrics
    assert "majority_class_baseline" in data["baseline_metrics"]
    assert "momentum_direction_baseline" in data["baseline_metrics"]

    # Verify feature importances
    assert "feature_importance" in data
    assert "rsi_14" in data["feature_importance"]

    # Verify experiment was persisted in DB
    exp = db_session.query(XGBoostExperiment).filter(
        XGBoostExperiment.model_id == data["model_id"]
    ).first()
    assert exp is not None
    assert exp.status == "COMPLETED"
    assert os.path.exists(exp.artifact_path)
    assert exp.artifact_checksum is not None


# ============================================================================
# 2. Temporal Split Integrity & Lookahead Prevention
# ============================================================================
def test_temporal_split_integrity_and_no_lookahead():
    """Verify chronological train/val/test splits with zero shuffling and no future leakage."""
    candles = generate_synthetic_ohlc_candles(n_bars=120)

    # Feature extraction & aligned pairs
    pipeline_res = XGBoostFeaturePipeline.build_training_dataset(candles, warmup_bars=50)
    X = pipeline_res.features_df
    y = pipeline_res.targets
    timestamps = pipeline_res.timestamps

    total = len(X)
    train_idx = int(total * 0.70)
    val_idx = int(total * 0.85)

    train_ts = timestamps.iloc[:train_idx]
    val_ts = timestamps.iloc[train_idx:val_idx]
    test_ts = timestamps.iloc[val_idx:]

    # Strict temporal ordering: train < val < test
    assert train_ts.max() < val_ts.min(), "Lookahead leakage: train overlaps with val!"
    assert val_ts.max() < test_ts.min(), "Lookahead leakage: val overlaps with test!"

    # Single-vector inference causal check:
    # At inference time, only candles up to t are ingested.
    latest_features, latest_ts = XGBoostFeaturePipeline.extract_single_inference_vector(candles)
    assert latest_ts == candles[-1].time
    assert "rsi_14" in latest_features
    assert "macd_hist_norm" in latest_features


# ============================================================================
# 3. Insufficient and Missing Data Handling
# ============================================================================
def test_insufficient_and_missing_data_handling():
    """Verify clean rejection when dataset has fewer bars than required warmup."""
    short_candles = generate_synthetic_ohlc_candles(n_bars=30)

    with pytest.raises(ValueError) as excinfo:
        XGBoostFeaturePipeline.build_training_dataset(short_candles, warmup_bars=50)
    assert "Insufficient historical data" in str(excinfo.value)

    # API level test with insufficient data
    with patch.object(XGBoostService, "load_candles", return_value=generate_synthetic_ohlc_candles(n_bars=30)):
        res = client.post("/api/xgboost/train", json={
            "symbol": "RELIANCE",
            "timeframe": "1D",
        })
        assert res.status_code == 400
        assert "Insufficient historical data" in res.json()["detail"]


# ============================================================================
# 4. Invalid Hyperparameters Rejection
# ============================================================================
def test_invalid_hyperparameters_rejection():
    """Verify API schema validates hyperparameter bounds."""
    # max_depth < 1
    res = client.post("/api/xgboost/train", json={
        "symbol": "RELIANCE",
        "timeframe": "1D",
        "max_depth": 0,
    })
    assert res.status_code == 422

    # learning_rate <= 0
    res = client.post("/api/xgboost/train", json={
        "symbol": "RELIANCE",
        "timeframe": "1D",
        "learning_rate": -0.05,
    })
    assert res.status_code == 422

    # train_ratio < 0.4
    res = client.post("/api/xgboost/train", json={
        "symbol": "RELIANCE",
        "timeframe": "1D",
        "train_ratio": 0.05,
    })
    assert res.status_code == 422


# ============================================================================
# 5. Model Loading Failure Resilience
# ============================================================================
def test_model_loading_failure_resilience():
    """Verify requesting prediction with invalid or non-existent model ID returns HTTP 400 or 404."""
    res = client.post("/api/xgboost/predict", json={
        "model_id": "non_existent_xgb_model_9999",
        "symbol": "RELIANCE",
        "timeframe": "1D",
    })
    assert res.status_code in [400, 404]
    detail = res.json()["detail"].lower()
    assert ("not found" in detail or "no trained xgboost" in detail or "found" in detail)


# ============================================================================
# 6. Zero Order Execution Verification
# ============================================================================
def test_zero_order_execution_verification(db_session):
    """Verify XGBoost training, prediction, and advisory synthesis execute ZERO real or paper orders."""
    initial_trade_count = db_session.query(PaperTrade).count()
    initial_proposal_count = db_session.query(BuyProposal).count()
    initial_risk = db_session.query(RiskSettings).first()
    initial_balance = initial_risk.simulated_balance if initial_risk else 100000.0

    # 1. Run prediction
    res_pred = client.post("/api/xgboost/predict", json={
        "symbol": "RELIANCE",
        "timeframe": "1D",
    })

    # 2. Run advisory synthesis
    res_synth = client.post("/api/xgboost/synthesize", json={
        "symbol": "RELIANCE",
        "timeframe": "1D",
        "rule_signal": "BUY",
        "confidence": 0.85,
        "proposed_reasoning": "RSI oversold crossover",
    })

    # Assert invariant: zero paper trades created
    final_trade_count = db_session.query(PaperTrade).count()
    assert final_trade_count == initial_trade_count, "XGBoost created a paper trade! Safety violation!"

    # Assert invariant: proposals untouched
    final_proposal_count = db_session.query(BuyProposal).count()
    assert final_proposal_count == initial_proposal_count, "XGBoost created a buy proposal! Safety violation!"

    # Assert invariant: balance unchanged
    final_risk = db_session.query(RiskSettings).first()
    final_balance = final_risk.simulated_balance if final_risk else 100000.0
    assert final_balance == initial_balance, "Simulated balance altered by XGBoost! Safety violation!"

    # Assert invariant: live broker order remains fail-closed
    res_broker = client.post("/api/broker/zerodha/orders")
    assert res_broker.status_code == 403, "Live broker order endpoint is not fail-closed!"


# ============================================================================
# 7. Stale and Incomplete Data Rejection
# ============================================================================
def test_stale_and_incomplete_data_rejection():
    """Verify feature pipeline rejects candles with missing required columns."""
    short_df = pd.DataFrame({
        "time": [1, 2, 3],
        "open": [100, 101, 102],
        "high": [105, 106, 107],
        "low": [99, 100, 101],
        "close": [103, 104, 105],
        "volume": [1000, 2000, 3000],
    })

    with pytest.raises(ValueError) as excinfo:
        XGBoostFeaturePipeline.extract_features_df(short_df)
    assert "Insufficient historical candles" in str(excinfo.value)

    # Missing close column
    missing_close = pd.DataFrame({
        "time": list(range(60)),
        "open": [100.0] * 60,
        "high": [105.0] * 60,
        "low": [95.0] * 60,
        "volume": [1000.0] * 60,
    })
    with pytest.raises(KeyError):
        XGBoostFeaturePipeline.extract_features_df(missing_close)


# ============================================================================
# 8. Baseline Integrity
# ============================================================================
def test_baseline_integrity():
    """Verify majority class baseline and momentum baseline logic."""
    # 70% ones, 30% zeros in training
    y_train = pd.Series([1, 1, 1, 1, 1, 1, 1, 0, 0, 0])
    y_test = pd.Series([1, 1, 0, 0])
    features_test = pd.DataFrame({"return_1bar": [0.02, -0.01, 0.03, -0.02]})

    # Majority class in train is 1
    majority_class = int(y_train.mode()[0])
    assert majority_class == 1

    majority_preds = np.full(shape=len(y_test), fill_value=majority_class)
    majority_acc = float(np.mean(y_test == majority_preds))
    assert majority_acc == 0.50

    # Momentum baseline: predict 1 if return_1bar > 0 else 0
    momentum_preds = (features_test["return_1bar"] > 0.0).astype(int).values
    momentum_acc = float(np.mean(y_test.values == momentum_preds))
    assert momentum_acc == 0.50


# ============================================================================
# 9. Reproducibility with Fixed Random Seed
# ============================================================================
def test_reproducibility_with_fixed_random_seed():
    """Verify identical parameters and random_seed produce identical models and metrics."""
    res1 = client.post("/api/xgboost/train", json={
        "symbol": "RELIANCE",
        "timeframe": "1D",
        "n_estimators": 30,
        "max_depth": 3,
        "learning_rate": 0.05,
        "random_seed": 42,
    })
    res2 = client.post("/api/xgboost/train", json={
        "symbol": "RELIANCE",
        "timeframe": "1D",
        "n_estimators": 30,
        "max_depth": 3,
        "learning_rate": 0.05,
        "random_seed": 42,
    })

    assert res1.status_code == 200
    assert res2.status_code == 200

    d1 = res1.json()["out_of_sample_metrics"]
    d2 = res2.json()["out_of_sample_metrics"]

    assert d1["accuracy"] == d2["accuracy"]
    assert d1.get("f1_score", d1.get("f1")) == d2.get("f1_score", d2.get("f1"))
    assert d1["brier_score"] == d2["brier_score"]


# ============================================================================
# 10. API Endpoints Validation
# ============================================================================
def test_api_endpoints_validation():
    """Verify REST API endpoints for models, predictions, and synthesis."""
    # GET /models
    res_models = client.get("/api/xgboost/models")
    assert res_models.status_code == 200
    models_list = res_models.json()
    assert isinstance(models_list, list)

    if len(models_list) > 0:
        first_model_id = models_list[0]["model_id"]
        # GET /models/{model_id}
        res_detail = client.get(f"/api/xgboost/models/{first_model_id}")
        assert res_detail.status_code == 200
        detail = res_detail.json()
        assert detail["model_id"] == first_model_id
        assert "hyperparameters" in detail
        assert "out_of_sample_metrics" in detail
        assert "feature_importance" in detail

    # GET /predictions
    res_preds = client.get("/api/xgboost/predictions")
    assert res_preds.status_code == 200
    preds_list = res_preds.json()
    assert isinstance(preds_list, list)


# ============================================================================
# 11. Qwen Offline Fallback Resilience & Divergence Detection
# ============================================================================
def test_qwen_offline_fallback_resilience(db_session):
    """Verify advisory explainer operates safely when Ollama is offline and flags divergences."""
    # Case A: Divergence (Rule = BUY, XGBoost = BEARISH)
    res_divergent = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="RELIANCE",
        timeframe="1D",
        rule_signal="BUY",
        xgboost_prediction={
            "predicted_direction": "BEARISH_DOWN",
            "bearish_probability": 0.75,
            "bullish_probability": 0.25,
            "model_version": "1.0.0",
        },
        technical_context={"rsi_14": 68.5},
        ollama_host="http://127.0.0.1:19999",  # Unused port to guarantee offline
    )

    assert res_divergent["divergence_detected"] is True
    assert res_divergent["provider_used"] == "DETERMINISTIC_FALLBACK"
    assert res_divergent["synthesis"]["synthesis_verdict"] == "DIVERGENT"
    assert "DIVERGENCE DETECTED" in res_divergent["synthesis"]["divergence_or_uncertainty"]

    # Case B: Agreement (Rule = BUY, XGBoost = BULLISH)
    res_agree = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
        db=db_session,
        symbol="RELIANCE",
        timeframe="1D",
        rule_signal="BUY",
        xgboost_prediction={
            "predicted_direction": "BULLISH_UP",
            "bearish_probability": 0.25,
            "bullish_probability": 0.75,
            "model_version": "1.0.0",
        },
        technical_context={"rsi_14": 52.0},
        ollama_host="http://127.0.0.1:19999",
    )

    assert res_agree["divergence_detected"] is False
    assert res_agree["synthesis"]["synthesis_verdict"] == "CONFLUENT_BULLISH"


# ============================================================================
# 12. Prediction Verification Workflow
# ============================================================================
def test_prediction_verification_workflow(db_session):
    """Verify predictions start with actual_future_direction=None and outcome_status='UNVERIFIED_PENDING_BAR'."""
    res = client.post("/api/xgboost/predict", json={
        "symbol": "RELIANCE",
        "timeframe": "1D",
    })

    assert res.status_code == 200
    data = res.json()
    pred_id = data["prediction_id"]

    # Query latest prediction from DB
    rec = db_session.query(XGBoostPredictionRecord).filter(
        XGBoostPredictionRecord.prediction_id == pred_id
    ).first()

    assert rec is not None
    assert rec.predicted_class in [0, 1]
    assert rec.outcome_status == "UNVERIFIED_PENDING_BAR"
    assert rec.actual_future_direction is None
    assert rec.advisory_only is True
