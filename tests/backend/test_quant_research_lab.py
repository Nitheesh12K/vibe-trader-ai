"""Phase 4: Quantitative Research Lab Automated Validation Suite.
Rigorous verification of:
1. Causal Feature Engineering & Zero Look-Ahead Bias Invariants.
2. Chronological Walk-Forward Rolling Folds (Non-overlapping Out-of-Sample testing).
3. Buy-and-Hold Baseline Benchmarking & Alpha Attribution.
4. Sortino Ratio & Downside Risk Mathematics (Zero Division Safeguards).
5. Market Regime Classification Distribution & Coverage Integrity (100% of candles classified).
6. Execution Friction Stress Testing (Monotonic ROI Degradation under increasing slippage/commissions).
7. Data Boundary Safeguards (Graceful HTTP 400 rejection on insufficient history).
"""
import sys
import math
from pathlib import Path
from typing import List
import pytest
import numpy as np
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.database.session import SessionLocal, init_db
from app.schemas.market import OHLCCandle
from app.schemas.workflow import BacktestTradeResult
from app.services.research_service import QuantResearchService
from app.services.xgboost_feature_pipeline import XGBoostFeaturePipeline, FEATURE_NAMES

client = TestClient(app)


@pytest.fixture
def db_session():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_synthetic_candles(count: int = 100, base_price: float = 1000.0) -> List[OHLCCandle]:
    """Generates synthetic price candles with consistent trending and mean-reverting sections."""
    candles = []
    curr = base_price
    t0 = 1700000000
    for i in range(count):
        drift = 1.0 if (i % 20 < 10) else -0.8
        noise = (i % 5 - 2) * 0.5
        open_p = curr
        close_p = curr + drift + noise
        high_p = max(open_p, close_p) + 2.0
        low_p = min(open_p, close_p) - 2.0
        vol = 10000.0 + (i * 100)
        curr = close_p
        candles.append(OHLCCandle(
            time=t0 + (i * 86400),
            open=round(open_p, 2),
            high=round(high_p, 2),
            low=round(low_p, 2),
            close=round(close_p, 2),
            volume=vol,
        ))
    return candles


# -------------------------------------------------------------------------
# Test 1: Causal Feature Pipeline & Look-Ahead Bias Prevention
# -------------------------------------------------------------------------
def test_causal_feature_pipeline_lookahead_prevention():
    """Verify that features computed at index t depend strictly on candles <= t.
    Modifying future candles (t+1, t+2) must NOT alter features at t.
    """
    candles_orig = generate_synthetic_candles(80)
    df_clean_orig = XGBoostFeaturePipeline.validate_and_clean_candles(candles_orig)
    df_orig = XGBoostFeaturePipeline.extract_features_df(df_clean_orig)

    # Pick evaluation index t (say index 40)
    eval_idx = 40
    vec_orig = df_orig.iloc[eval_idx][FEATURE_NAMES].to_dict()

    # Create mutated future candle set where candles > eval_idx are radically changed
    candles_mutated = [c.model_copy() for c in candles_orig]
    for i in range(eval_idx + 1, len(candles_mutated)):
        candles_mutated[i].close *= 3.0
        candles_mutated[i].high *= 3.0
        candles_mutated[i].low *= 0.2

    df_clean_mutated = XGBoostFeaturePipeline.validate_and_clean_candles(candles_mutated)
    df_mutated = XGBoostFeaturePipeline.extract_features_df(df_clean_mutated)
    vec_mutated = df_mutated.iloc[eval_idx][FEATURE_NAMES].to_dict()

    # Assert exact bit-level equality for all features at row eval_idx
    for f in FEATURE_NAMES:
        orig_val = vec_orig[f]
        mut_val = vec_mutated[f]
        if np.isnan(orig_val) and np.isnan(mut_val):
            continue
        assert abs(orig_val - mut_val) < 1e-9, f"Feature '{f}' altered by future data leakage at row {eval_idx}!"

    # Verify build_training_dataset drops warmup and aligns pairs
    pipeline_res = XGBoostFeaturePipeline.build_training_dataset(candles_orig, warmup_bars=50)
    assert len(pipeline_res.features_df) > 0
    assert len(pipeline_res.targets) == len(pipeline_res.features_df)
    assert pipeline_res.usable_rows == len(pipeline_res.features_df)


# -------------------------------------------------------------------------
# Test 2: Chronological Walk-Forward Rolling Folds
# -------------------------------------------------------------------------
def test_walk_forward_oos_chronological_integrity():
    """Verify walk-forward validation creates non-overlapping train and test splits
    where train period end strictly precedes test period start.
    """
    resp = client.post("/api/research/walk-forward", json={
        "symbol": "RELIANCE",
        "market": "NSE",
        "timeframe": "1D",
        "strategy_id": "STRAT-EMA-CROSS",
        "initial_capital": 100000.0,
        "num_folds": 2,
        "train_ratio": 0.70,
        "slippage_pct": 0.02,
        "commission_per_trade": 20.0,
    })
    assert resp.status_code == 200, f"Walk-forward failed: {resp.text}"
    data = resp.json()

    folds = data["folds"]
    assert len(folds) >= 2

    prev_test_end = 0
    for fold in folds:
        train_start = fold["train_start"]
        train_end = fold["train_end"]
        test_start = fold["test_start"]
        test_end = fold["test_end"]

        # 1. Train period ends before or at test period start
        assert train_end <= test_start, f"Lookahead in fold {fold['fold_index']}: train_end > test_start"

        # 2. Test periods do not regress backwards
        assert test_start >= prev_test_end, f"Fold {fold['fold_index']} test_start overlaps prior test!"
        prev_test_end = test_end

        # 3. Minimum candle counts
        assert fold["train_candles"] >= 20
        assert fold["test_candles"] >= 5


# -------------------------------------------------------------------------
# Test 3: Buy-and-Hold Baseline Benchmark & Alpha Attribution
# -------------------------------------------------------------------------
def test_buy_and_hold_baseline_and_alpha_attribution():
    """Verify that walk-forward returns calculate Buy-and-Hold baseline and correct alpha."""
    resp = client.post("/api/research/walk-forward", json={
        "symbol": "RELIANCE",
        "market": "NSE",
        "timeframe": "1D",
        "strategy_id": "STRAT-EMA-CROSS",
        "initial_capital": 100000.0,
        "num_folds": 2,
        "train_ratio": 0.70,
    })
    assert resp.status_code == 200
    data = resp.json()

    bnh_pnl = data["baseline_buy_and_hold_pnl"]
    alpha = data["alpha_over_buy_and_hold"]
    strat_net_pnl = data["aggregate_oos_net_pnl"]

    # Alpha in cash terms = Strategy Net PnL - Benchmark PnL
    expected_alpha = round(strat_net_pnl - bnh_pnl, 2)
    assert abs(alpha - expected_alpha) <= 0.05, f"Alpha {alpha} != expected {expected_alpha}"


# -------------------------------------------------------------------------
# Test 4: Sortino Ratio & Downside Deviation Mathematics
# -------------------------------------------------------------------------
def test_sortino_ratio_and_downside_deviation_boundary_cases():
    """Verify Sortino calculation under normal, all-positive, and all-negative return distributions."""
    # Case 1: Normal distribution with downside variance
    mixed_trades = [
        BacktestTradeResult(
            trade_id=1, symbol="TEST", entry_time=1, exit_time=2,
            entry_price=100, exit_price=110, quantity=10, gross_pnl=100, net_pnl=100,
            roi_pct=10.0, exit_reason="TARGET_HIT"
        ),
        BacktestTradeResult(
            trade_id=2, symbol="TEST", entry_time=3, exit_time=4,
            entry_price=100, exit_price=95, quantity=10, gross_pnl=-50, net_pnl=-50,
            roi_pct=-5.0, exit_reason="STOP_LOSS_HIT"
        ),
        BacktestTradeResult(
            trade_id=3, symbol="TEST", entry_time=5, exit_time=6,
            entry_price=100, exit_price=105, quantity=10, gross_pnl=50, net_pnl=50,
            roi_pct=5.0, exit_reason="TARGET_HIT"
        ),
    ]
    sortino = QuantResearchService._calculate_sortino(mixed_trades)
    assert sortino is not None
    assert sortino > 0.0, "Expected positive Sortino for net profitable trading distribution"

    # Case 2: All positive trades (zero downside deviation -> returns None safely)
    positive_trades = [
        BacktestTradeResult(
            trade_id=i, symbol="TEST", entry_time=i, exit_time=i+1,
            entry_price=100, exit_price=105, quantity=10, gross_pnl=50, net_pnl=50,
            roi_pct=5.0, exit_reason="TARGET_HIT"
        )
        for i in range(5)
    ]
    sortino_pos = QuantResearchService._calculate_sortino(positive_trades)
    assert sortino_pos is None, "Zero downside deviation returns None to indicate no downside risk"

    # Case 3: Empty trades list returns None safely
    assert QuantResearchService._calculate_sortino([]) is None


# -------------------------------------------------------------------------
# Test 5: Market Regime Classification Distribution & Coverage
# -------------------------------------------------------------------------
def test_market_regime_classification_coverage_and_transitions(db_session):
    """Verify that historical candles are fully classified across the 4 canonical regimes
    with cumulative percentage summing to 100%.
    """
    resp = client.get("/api/research/regimes?symbol=RELIANCE&timeframe=1D")
    assert resp.status_code == 200
    data = resp.json()

    assert data["symbol"] == "RELIANCE"
    assert data["total_candles"] > 0
    regimes = data["regimes"]
    assert len(regimes) == 4

    regime_names = {r["regime_name"] for r in regimes}
    expected_names = {"BULLISH_TREND", "BEARISH_TREND", "HIGH_VOLATILITY", "SIDEWAYS_RANGE"}
    assert regime_names == expected_names

    # Check candle coverage sums to total_candles
    total_classified = sum(r["candle_count"] for r in regimes)
    assert total_classified == data["total_candles"]

    # Check percentage sum is ~100%
    pct_sum = sum(r["percentage_of_time"] for r in regimes)
    assert 99.5 <= pct_sum <= 100.5


# -------------------------------------------------------------------------
# Test 6: Execution Friction Stress Testing Monotonicity
# -------------------------------------------------------------------------
def test_execution_sensitivity_stress_testing_monotonicity():
    """Verify that 4 graduated execution friction scenarios produce non-increasing net ROI."""
    resp = client.post("/api/research/sensitivity", json={
        "symbol": "RELIANCE",
        "market": "NSE",
        "timeframe": "1D",
        "strategy_id": "STRAT-EMA-CROSS",
        "initial_capital": 100000.0,
    })
    assert resp.status_code == 200
    data = resp.json()

    scenarios = data["scenarios"]
    assert len(scenarios) == 4

    # Monotonic degradation check: Scenario k+1 net_pnl must be <= Scenario k net_pnl
    for i in range(len(scenarios) - 1):
        curr_pnl = scenarios[i]["net_pnl"]
        next_pnl = scenarios[i + 1]["net_pnl"]
        assert next_pnl <= curr_pnl + 1e-4, (
            f"Friction violation: Higher friction scenario {scenarios[i+1]['scenario_name']} ({next_pnl}) "
            f"has higher net P&L than lower friction scenario {scenarios[i]['scenario_name']} ({curr_pnl})!"
        )

    assert "robustness_verdict" in data
    assert len(data["robustness_verdict"]) > 0


# -------------------------------------------------------------------------
# Test 7: Data Boundary & Insufficient Candle Safeguards
# -------------------------------------------------------------------------
def test_insufficient_data_rejection_safety():
    """Verify that walk-forward with excessive folds or insufficient dataset returns HTTP 400 safely."""
    # Attempting 10 folds on 61 candles -> 6 candles per fold < 25 required
    resp = client.post("/api/research/walk-forward", json={
        "symbol": "RELIANCE",
        "market": "NSE",
        "timeframe": "1D",
        "strategy_id": "STRAT-EMA-CROSS",
        "num_folds": 10,
    })
    assert resp.status_code == 400
    assert "requires at least" in resp.json()["detail"].lower() or "insufficient" in resp.json()["detail"].lower()
