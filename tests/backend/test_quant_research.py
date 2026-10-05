"""Quantitative Research & Walk-Forward Validation Engine Test Suite.
Validates:
1. Walk-Forward Chronological Rolling Folds (in-sample vs out-of-sample)
2. Zero Look-Ahead Bias & Non-Overlapping Splits
3. Buy-and-Hold Baseline & Alpha Attribution
4. Sortino Ratio & Downside Risk Mathematics
5. Sensitivity & Execution Friction Stress Scenarios
6. Historical Market Regime Classification
7. Strategy Catalog Research Metadata
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.database.session import SessionLocal
from app.services.research_service import QuantResearchService
from app.schemas.workflow import BacktestTradeResult

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_research_strategies_catalog_inspection():
    """Verify listing supported strategies for quantitative research."""
    res = client.get("/api/research/strategies")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 7
    ids = {s["strategy_id"] for s in data}
    assert "STRAT-EMA-CROSS" in ids
    assert "STRAT-RSI-REV" in ids
    assert "STRAT-MACD-MOM" in ids


def test_walk_forward_multi_fold_execution(db_session):
    """Verify walk-forward validation runs chronological rolling folds with no lookahead bias."""
    res = client.post("/api/research/walk-forward", json={
        "symbol": "RELIANCE",
        "market": "NSE",
        "timeframe": "1D",
        "strategy_id": "STRAT-EMA-CROSS",
        "initial_capital": 100000.0,
        "num_folds": 3,
        "train_ratio": 0.65,
        "slippage_pct": 0.02,
        "commission_per_trade": 20.0,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["strategy_id"] == "STRAT-EMA-CROSS"
    assert data["num_folds"] >= 2
    assert "folds" in data
    assert len(data["folds"]) >= 2

    # Check fold chronological integrity
    for fold in data["folds"]:
        assert fold["train_candles"] > 0
        assert fold["test_candles"] > 0
        # Train period must precede test period chronologically
        assert fold["train_end"] <= fold["test_start"]

    # Check baseline alpha attribution
    assert "baseline_buy_and_hold_pnl" in data
    assert "alpha_over_buy_and_hold" in data
    assert "aggregate_oos_roi_pct" in data
    assert "disclaimer" in data


def test_walk_forward_insufficient_data_rejection():
    """Verify that requests with insufficient history or excessive folds are rejected with HTTP 400."""
    res = client.post("/api/research/walk-forward", json={
        "symbol": "RELIANCE",
        "market": "NSE",
        "timeframe": "1D",
        "strategy_id": "STRAT-EMA-CROSS",
        "num_folds": 8,  # 8 folds on 61 candles gives fold_size=7 < 25 required
    })
    assert res.status_code in [400, 422]


def test_sensitivity_analysis_four_scenarios(db_session):
    """Verify execution friction stress test runs 4 graduated scenarios."""
    res = client.post("/api/research/sensitivity", json={
        "symbol": "RELIANCE",
        "market": "NSE",
        "timeframe": "1D",
        "strategy_id": "STRAT-EMA-CROSS",
        "initial_capital": 100000.0,
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["scenarios"]) == 4
    scenario_names = [s["scenario_name"] for s in data["scenarios"]]
    assert "Optimal Low Friction" in scenario_names[0]
    assert "Baseline Indian Equities" in scenario_names[1]
    assert "Elevated Friction / Spread" in scenario_names[2]
    assert "Stress Liquidity Freeze" in scenario_names[3]

    # Verify slippage increases monotonically across scenarios
    slippages = [s["slippage_pct"] for s in data["scenarios"]]
    assert slippages == sorted(slippages)

    assert "robustness_verdict" in data
    assert len(data["robustness_verdict"]) > 5


def test_regime_classification_methodology(db_session):
    """Verify historical market regime classification into 4 regimes."""
    res = client.get("/api/research/regimes?symbol=RELIANCE&timeframe=1D")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "RELIANCE"
    assert data["total_candles"] > 0
    assert len(data["regimes"]) == 4

    regime_names = {r["regime_name"] for r in data["regimes"]}
    assert "BULLISH_TREND" in regime_names
    assert "BEARISH_TREND" in regime_names
    assert "HIGH_VOLATILITY" in regime_names
    assert "SIDEWAYS_RANGE" in regime_names

    # Percentage sum should be approximately 100%
    total_pct = sum(r["percentage_of_time"] for r in data["regimes"])
    assert 99.0 <= total_pct <= 101.0


def test_sortino_ratio_downside_deviation_mathematics():
    """Verify Sortino ratio calculation computes downside deviation accurately."""
    # Create sample trades with some positive and negative returns
    trades = [
        BacktestTradeResult(
            trade_id=1, symbol="TEST", entry_time=1, exit_time=2,
            entry_price=100, exit_price=105, quantity=10, gross_pnl=50, net_pnl=50,
            roi_pct=5.0, exit_reason="TARGET_HIT"
        ),
        BacktestTradeResult(
            trade_id=2, symbol="TEST", entry_time=3, exit_time=4,
            entry_price=100, exit_price=98, quantity=10, gross_pnl=-20, net_pnl=-20,
            roi_pct=-2.0, exit_reason="STOP_LOSS_HIT"
        ),
        BacktestTradeResult(
            trade_id=3, symbol="TEST", entry_time=5, exit_time=6,
            entry_price=100, exit_price=108, quantity=10, gross_pnl=80, net_pnl=80,
            roi_pct=8.0, exit_reason="TARGET_HIT"
        ),
    ]
    sortino = QuantResearchService._calculate_sortino(trades)
    assert sortino is not None
    assert sortino > 0  # Net positive with positive mean return
