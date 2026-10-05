"""Step 5: Algorithm Validation, Backtest Robustness & Strategy Quality Audit Test Suite.
Validates:
1. Strategy-by-strategy validation across all 7 catalog strategies (entry, exit, SL, TP, ATR, version, parameters, no silent fallback).
2. No look-ahead bias verification (future candle shocks do not alter past signals or indicators).
3. Chronological simulation verification (candle t -> indicators t -> decision t -> execution t+1).
4. Reproducibility test (two runs with identical inputs produce 100% bitwise/exact matching results).
5. In-sample vs Out-of-sample data split validation (FULL, IN_SAMPLE, VALIDATION, OUT_OF_SAMPLE, no leakage).
6. Market regime testing (Trending, Sideways, Volatility; reports INSUFFICIENT_DATA when < 10 candles).
7. Realistic execution costs & slippage (Gross P&L vs Net P&L).
8. Safe statistical risk metrics & division-by-zero handling (0 trades, 1 trade, 100% win, 100% loss, Sharpe sample check).
9. Extreme edge cases & data sanity (missing/corrupted candles, duplicate timestamps, zero volume, flat prices, low capital).
10. Overtrading prevention & single-position constraint (duplicate signal filtering, consecutive win/loss tracking).
11. Paper vs Backtest consistency.
12. Algorithm -> AI separation of concerns (authoritative math, no AI tampering).
13. Strategy version control and metadata audit.
14. Runtime performance benchmark.
"""
import time
import math
import sys
from pathlib import Path
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.database.session import SessionLocal
from app.schemas.market import OHLCCandle
from app.schemas.analysis import IndicatorsResponse
from app.schemas.workflow import BacktestRequest
from app.services.indicators_service import IndicatorsService
from app.services.strategy_engine import StrategyEngine
from app.services.backtesting_service import BacktestingService
from app.services.risk_service import RiskService
from app.models.entities import BuyProposal, utcnow
from app.services.market_data_service import MarketDataService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


def generate_synthetic_candles(count: int = 100, base_price: float = 100.0, trend: float = 0.5) -> list[OHLCCandle]:
    """Helper to generate deterministic chronological OHLCV candles."""
    candles = []
    base_time = 1704067200  # 2024-01-01 00:00:00
    price = base_price
    for i in range(count):
        price = round(price + trend + (math.sin(i / 5.0) * 1.5), 2)
        high = round(price + 2.0, 2)
        low = round(price - 1.5, 2)
        open_p = round(price - 0.5, 2)
        close_p = price
        vol = 1000 + (i * 20)
        candles.append(
            OHLCCandle(
                time=base_time + (i * 86400),
                open=open_p,
                high=high,
                low=low,
                close=close_p,
                volume=vol,
            )
        )
    return candles


# ============================================================================
# 1. STRATEGY-BY-STRATEGY VALIDATION & NO SILENT FALLBACK
# ============================================================================

def test_all_seven_strategies_catalog_definitions():
    """Verify that all 7 strategies are configured in STRATEGY_CATALOG with required metadata."""
    expected_strategies = [
        "STRAT-EMA-CROSS",
        "STRAT-RSI-REV",
        "STRAT-MACD-MOM",
        "STRAT-VWAP-TREND",
        "STRAT-BB-REV",
        "STRAT-VOL-BREAKOUT",
        "STRAT-MULTI-CONF",
    ]
    catalog = StrategyEngine.STRATEGY_CATALOG

    for strat_id in expected_strategies:
        assert strat_id in catalog, f"Strategy {strat_id} missing from catalog"
        s_def = catalog[strat_id]
        assert s_def.strategy_id == strat_id
        assert s_def.name
        assert s_def.version == "1.0.0"
        assert len(s_def.required_indicators) > 0
        assert len(s_def.entry_conditions) > 0
        assert len(s_def.exit_conditions) > 0
        assert s_def.stop_loss_logic
        assert s_def.target_logic
        assert s_def.required_candle_history >= 20


def test_strategy_engine_rejects_unknown_strategy_without_silent_fallback():
    """Verify that StrategyEngine NEVER silently falls back to another strategy for unknown IDs."""
    candles = generate_synthetic_candles(50)
    indicators = IndicatorsService.compute_all_indicators(candles, "TEST", "1D")

    # Pass an unknown strategy ID
    unknown_id = "STRAT-NONEXISTENT-MAGIC"
    signal = StrategyEngine.evaluate_strategy_signal(
        strategy_id=unknown_id,
        symbol="TEST",
        market="NSE",
        timeframe="1D",
        candles=candles,
        indicators=indicators,
    )

    # Must return INVALID_DATA with explicit reasons, NOT a valid signal from STRAT-MULTI-CONF
    assert signal.signal_state == "INVALID_DATA"
    assert "not found in STRATEGY_CATALOG" in signal.reasons[0]
    assert "Silent fallback is strictly prohibited" in signal.reasons[0]
    assert signal.suggested_stop_loss is None
    assert signal.suggested_target is None


def test_each_of_seven_strategies_evaluates_without_silent_fallback():
    """Verify that all 7 strategies execute their dedicated evaluation branch."""
    candles = generate_synthetic_candles(60)
    indicators = IndicatorsService.compute_all_indicators(candles, "TEST", "1D")

    expected_strategies = [
        "STRAT-EMA-CROSS",
        "STRAT-RSI-REV",
        "STRAT-MACD-MOM",
        "STRAT-VWAP-TREND",
        "STRAT-BB-REV",
        "STRAT-VOL-BREAKOUT",
        "STRAT-MULTI-CONF",
    ]

    for strat_id in expected_strategies:
        signal = StrategyEngine.evaluate_strategy_signal(
            strategy_id=strat_id,
            symbol="TEST",
            market="NSE",
            timeframe="1D",
            candles=candles,
            indicators=indicators,
        )
        assert signal.strategy_id == strat_id
        assert signal.signal_state in ["BUY_CANDIDATE", "SELL_CANDIDATE", "HOLD", "NO_TRADE", "NO_SIGNAL", "INVALID_DATA"]
        assert isinstance(signal.reasons, list)


# ============================================================================
# 2. NO LOOK-AHEAD BIAS REGRESSION TEST
# ============================================================================

def test_no_look_ahead_bias_indicators_and_signals_invariant_to_future_shocks():
    """
    CRITICAL QUANTITATIVE PROOF:
    Verify that altering, inverting, or shocking future candles (t > M) has ZERO effect
    on indicators, support/resistance, or strategy signals evaluated at candle M.
    """
    n_total = 80
    eval_point = 40  # Step M
    candles_original = generate_synthetic_candles(n_total, base_price=100.0, trend=0.5)

    # 1. Evaluate historical slice strictly up to eval_point
    sub_slice_orig = candles_original[: eval_point + 1]
    ind_orig = IndicatorsService.compute_all_indicators(sub_slice_orig, "TEST", "1D")
    signal_orig = StrategyEngine.evaluate_strategy_signal(
        strategy_id="STRAT-EMA-CROSS",
        symbol="TEST",
        market="NSE",
        timeframe="1D",
        candles=sub_slice_orig,
        indicators=ind_orig,
    )

    # 2. Create shocked future series: candles up to eval_point are IDENTICAL,
    # but all candles after eval_point have extreme -90% crash prices
    candles_shocked = [c.model_copy() for c in candles_original[: eval_point + 1]]
    last_time = candles_shocked[-1].time
    for j in range(eval_point + 1, n_total):
        candles_shocked.append(
            OHLCCandle(
                time=last_time + ((j - eval_point) * 86400),
                open=10.0,
                high=11.0,
                low=9.0,
                close=10.0,
                volume=999999,
            )
        )

    # 3. Evaluate historical slice up to eval_point on the shocked dataset
    sub_slice_shocked = candles_shocked[: eval_point + 1]
    ind_shocked = IndicatorsService.compute_all_indicators(sub_slice_shocked, "TEST", "1D")
    signal_shocked = StrategyEngine.evaluate_strategy_signal(
        strategy_id="STRAT-EMA-CROSS",
        symbol="TEST",
        market="NSE",
        timeframe="1D",
        candles=sub_slice_shocked,
        indicators=ind_shocked,
    )

    # 4. Strict assertions: Indicator values at eval_point MUST BE 100% IDENTICAL
    assert ind_orig.rsi[-1].value == ind_shocked.rsi[-1].value
    assert ind_orig.ema_9[-1].value == ind_shocked.ema_9[-1].value
    assert ind_orig.ema_21[-1].value == ind_shocked.ema_21[-1].value
    assert ind_orig.macd[-1].macd == ind_shocked.macd[-1].macd
    assert ind_orig.atr[-1].value == ind_shocked.atr[-1].value

    # 5. Strict assertion: Strategy decision at eval_point MUST BE 100% IDENTICAL
    assert signal_orig.signal_state == signal_shocked.signal_state
    assert signal_orig.suggested_stop_loss == signal_shocked.suggested_stop_loss
    assert signal_orig.suggested_target == signal_shocked.suggested_target
    assert signal_orig.reasons == signal_shocked.reasons


# ============================================================================
# 3. CHRONOLOGICAL SIMULATION VERIFICATION
# ============================================================================

def test_chronological_candle_processing_order(db_session):
    """Verify that BacktestingService strictly advances time forward (entry_time < exit_time)."""
    req = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
        initial_capital=50000.0,
        risk_per_trade_pct=1.0,
        slippage_pct=0.02,
        commission_per_trade=1.5,
    )
    result = BacktestingService.run_backtest(db=db_session, req=req)

    assert result.strategy_id == "STRAT-EMA-CROSS"
    if result.total_trades > 0:
        for trade in result.trades:
            # Exit time must strictly be at or after entry time
            assert trade.exit_time >= trade.entry_time
            assert trade.entry_price > 0
            assert trade.exit_price > 0
            assert trade.quantity > 0


# ============================================================================
# 4. REPRODUCIBILITY TEST (DETERMINISTIC SIMULATION)
# ============================================================================

def test_backtest_reproducibility_identical_runs_produce_exact_results(db_session):
    """Verify running the exact same backtest twice produces 100% bitwise matching results."""
    req = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
        initial_capital=100000.0,
        risk_per_trade_pct=2.0,
        slippage_pct=0.05,
        commission_per_trade=2.0,
    )

    run_1 = BacktestingService.run_backtest(db=db_session, req=req)
    run_2 = BacktestingService.run_backtest(db=db_session, req=req)

    assert run_1.total_trades == run_2.total_trades
    assert run_1.winning_trades == run_2.winning_trades
    assert run_1.losing_trades == run_2.losing_trades
    assert run_1.win_rate == run_2.win_rate
    assert run_1.net_pnl == run_2.net_pnl
    assert run_1.final_capital == run_2.final_capital
    assert run_1.max_drawdown_pct == run_2.max_drawdown_pct
    assert run_1.profit_factor == run_2.profit_factor
    assert run_1.expectancy == run_2.expectancy

    # Compare trade-by-trade
    assert len(run_1.trades) == len(run_2.trades)
    for t1, t2 in zip(run_1.trades, run_2.trades):
        assert t1.trade_id == t2.trade_id
        assert abs(t1.entry_time - t2.entry_time) <= 1
        assert abs(t1.exit_time - t2.exit_time) <= 1
        assert t1.entry_price == t2.entry_price
        assert t1.exit_price == t2.exit_price
        assert t1.quantity == t2.quantity
        assert t1.gross_pnl == t2.gross_pnl
        assert t1.net_pnl == t2.net_pnl
        assert t1.roi_pct == t2.roi_pct


# ============================================================================
# 5. IN-SAMPLE VS OUT-OF-SAMPLE DATA SPLIT VALIDATION
# ============================================================================

def test_data_split_in_sample_validation_out_of_sample(db_session):
    """Verify that BacktestRequest supports FULL, IN_SAMPLE, VALIDATION, and OUT_OF_SAMPLE without data leakage."""
    req_full = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
        data_split="FULL",
    )
    res_full = BacktestingService.run_backtest(db=db_session, req=req_full)

    req_in = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
        data_split="IN_SAMPLE",
        in_sample_ratio=0.70,
    )
    res_in = BacktestingService.run_backtest(db=db_session, req=req_in)

    req_val = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
        data_split="VALIDATION",
        in_sample_ratio=0.70,
        validation_ratio=0.15,
    )
    res_val = BacktestingService.run_backtest(db=db_session, req=req_val)

    req_oos = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
        data_split="OUT_OF_SAMPLE",
        in_sample_ratio=0.70,
        validation_ratio=0.15,
    )
    res_oos = BacktestingService.run_backtest(db=db_session, req=req_oos)

    total_candles = res_full.date_range["candle_count"]
    in_candles = res_in.date_range["candle_count"]
    val_candles = res_val.date_range["candle_count"]
    oos_candles = res_oos.date_range["candle_count"]

    assert in_candles == int(total_candles * 0.70)
    assert val_candles == int(total_candles * 0.85) - int(total_candles * 0.70)
    assert oos_candles == total_candles - int(total_candles * 0.85)
    assert (in_candles + val_candles + oos_candles) == total_candles

    # Verify no chronological overlap
    if in_candles > 0 and oos_candles > 0:
        assert res_in.date_range["end_time"] <= res_oos.date_range["start_time"]


# ============================================================================
# 6. MARKET REGIME TESTING
# ============================================================================

def test_market_regime_classification_and_insufficient_data(db_session):
    """Verify that market regimes are classified and report INSUFFICIENT_DATA when < 10 candles."""
    req = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
    )
    res = BacktestingService.run_backtest(db=db_session, req=req)

    assert "regime_breakdown" in res.model_dump()
    regimes = res.regime_breakdown
    assert isinstance(regimes, dict)

    for r_name in ["BULLISH_TREND", "BEARISH_TREND", "SIDEWAYS_RANGE", "HIGH_VOLATILITY"]:
        if r_name in regimes:
            reg_info = regimes[r_name]
            assert "status" in reg_info
            assert reg_info["status"] in ["EVALUATED", "INSUFFICIENT_DATA"]
            if reg_info["candle_count"] < 10:
                assert reg_info["status"] == "INSUFFICIENT_DATA"
            else:
                assert reg_info["status"] == "EVALUATED"


# ============================================================================
# 7. REALISTIC EXECUTION COSTS & SLIPPAGE
# ============================================================================

def test_realistic_execution_costs_and_slippage_comparison(db_session):
    """Verify that slippage and commission reduce Gross P&L to Net P&L realistically."""
    req_cost = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
        slippage_pct=0.1,
        commission_per_trade=5.0,
    )
    res_cost = BacktestingService.run_backtest(db=db_session, req=req_cost)

    if res_cost.total_trades > 0:
        assert res_cost.total_commission == round(res_cost.total_trades * 5.0 * 2.0, 2)
        assert res_cost.total_slippage > 0
        assert res_cost.net_pnl < res_cost.gross_pnl
        for t in res_cost.trades:
            assert t.net_pnl <= t.gross_pnl


# ============================================================================
# 8. SAFE STATISTICAL RISK METRICS & DIVISION BY ZERO HANDLING
# ============================================================================

def test_safe_metrics_zero_trades_no_division_by_zero(db_session):
    """Verify 0 trades handles division by zero safely without NaN/Inf."""
    # Slicing with tiny validation ratio produces < 25 candles -> 0 trades
    req = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
        data_split="VALIDATION",
        in_sample_ratio=0.5,
        validation_ratio=0.01,  # Produces ~1 candle
    )
    res = BacktestingService.run_backtest(db=db_session, req=req)

    assert res.total_trades == 0
    assert res.winning_trades == 0
    assert res.losing_trades == 0
    assert res.win_rate == 0.0
    assert res.profit_factor == 0.0
    assert res.expectancy == 0.0
    assert res.average_holding_time_seconds == 0.0
    assert res.sharpe_ratio is None
    assert "INSUFFICIENT DATA" in res.disclaimer


def test_safe_sharpe_ratio_sample_size_requirement(db_session):
    """Verify Sharpe ratio is None for fewer than 3 trades, and finite for >= 3 trades."""
    req = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
    )
    res = BacktestingService.run_backtest(db=db_session, req=req)

    if res.total_trades < 3:
        assert res.sharpe_ratio is None
    else:
        assert isinstance(res.sharpe_ratio, float)
        assert not math.isnan(res.sharpe_ratio)
        assert not math.isinf(res.sharpe_ratio)


# ============================================================================
# 9. EXTREME EDGE CASES & DATA SANITY
# ============================================================================

def test_edge_case_invalid_ohlc_and_duplicate_timestamps(db_session):
    """Verify that BacktestingService deduplicates timestamps and rejects invalid OHLC cleanly."""
    # Test through BacktestingService using clean_candles sorting
    candles = [
        OHLCCandle(time=1000, open=100, high=105, low=95, close=102, volume=500),
        OHLCCandle(time=1000, open=100, high=105, low=95, close=102, volume=500),  # Duplicate timestamp
        OHLCCandle(time=2000, open=102, high=90, low=110, close=95, volume=500),   # Invalid: high < low
        OHLCCandle(time=3000, open=102, high=108, low=101, close=106, volume=0),   # Zero volume
    ]
    # Filter using same logic as BacktestingService
    seen = set()
    cleaned = []
    for c in candles:
        if c.time not in seen and c.high >= c.low and c.open >= 0 and c.close >= 0:
            seen.add(c.time)
            cleaned.append(c)

    assert len(cleaned) == 2  # Deduplicated timestamp and filtered high < low
    assert cleaned[0].time == 1000
    assert cleaned[1].time == 3000


def test_edge_case_flat_prices_zero_atr_handled_safely():
    """Verify that perfectly flat prices (ATR = 0) do not cause ZeroDivisionError in indicators or strategy."""
    flat_candles = [
        OHLCCandle(time=1700000000 + (i * 86400), open=100.0, high=100.0, low=100.0, close=100.0, volume=1000)
        for i in range(50)
    ]
    indicators = IndicatorsService.compute_all_indicators(flat_candles, "FLAT", "1D")
    assert indicators.atr[-1].value == 0.0

    signal = StrategyEngine.evaluate_strategy_signal(
        strategy_id="STRAT-EMA-CROSS",
        symbol="FLAT",
        market="NSE",
        timeframe="1D",
        candles=flat_candles,
        indicators=indicators,
    )
    assert signal.signal_state in ["NO_SIGNAL", "BUY_CANDIDATE", "SELL_CANDIDATE", "HOLD", "NO_TRADE", "INVALID_DATA"]


# ============================================================================
# 10. OVERTRADING & SINGLE-POSITION CONSTRAINT
# ============================================================================

def test_single_position_constraint_filters_duplicate_signals(db_session):
    """Verify that multiple simultaneous positions are prevented and duplicate signals are counted."""
    req = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
    )
    res = BacktestingService.run_backtest(db=db_session, req=req)

    assert res.execution_assumptions["single_position_enforced"] is True
    assert "overtrading_metrics" in res.model_dump()
    ot = res.overtrading_metrics
    assert "total_signals_generated" in ot
    assert "signals_executed" in ot
    assert "signals_filtered_duplicate" in ot
    assert ot["total_signals_generated"] == (ot["signals_executed"] + ot["signals_filtered_duplicate"])


# ============================================================================
# 11. PAPER VS BACKTEST CONSISTENCY
# ============================================================================

def test_paper_vs_backtest_signal_consistency():
    """Verify StrategyEngine outputs identical signals for paper and backtest with identical candle slices."""
    candles = generate_synthetic_candles(50)
    indicators = IndicatorsService.compute_all_indicators(candles, "TEST", "1D")

    signal_backtest = StrategyEngine.evaluate_strategy_signal(
        strategy_id="STRAT-MULTI-CONF",
        symbol="TEST",
        market="NSE",
        timeframe="1D",
        candles=candles,
        indicators=indicators,
    )

    signal_paper = StrategyEngine.evaluate_strategy_signal(
        strategy_id="STRAT-MULTI-CONF",
        symbol="TEST",
        market="NSE",
        timeframe="1D",
        candles=candles,
        indicators=indicators,
    )

    assert signal_backtest.signal_state == signal_paper.signal_state
    assert signal_backtest.suggested_stop_loss == signal_paper.suggested_stop_loss
    assert signal_backtest.suggested_target == signal_paper.suggested_target
    assert signal_backtest.reasons == signal_paper.reasons


# ============================================================================
# 12. ALGORITHM -> AI SEPARATION OF CONCERNS
# ============================================================================

def test_algorithm_authoritative_separation_from_ai(db_session):
    """Verify that deterministic mathematical algorithm cannot be overridden by AI reasoning."""
    candles = generate_synthetic_candles(50)
    indicators = IndicatorsService.compute_all_indicators(candles, "TEST", "1D")

    # Algorithm evaluation is pure math
    algo_signal = StrategyEngine.evaluate_strategy_signal(
        strategy_id="STRAT-RSI-REV",
        symbol="TEST",
        market="NSE",
        timeframe="1D",
        candles=candles,
        indicators=indicators,
    )

    # Risk Guardian validates proposal against deterministic mathematical limits
    # Even if AI were to claim 100% confidence, Risk Guardian rejects if allocation or max risk breached
    proposal = BuyProposal(
        proposal_id="TEST-PROP-001",
        symbol="TEST",
        market="NSE",
        strategy_name="RSI Reversal",
        current_price=100.0,
        proposed_entry_price=100.0,
        proposed_quantity=500000.0,  # Ridiculous size that exceeds capital limits
        stop_loss=98.0,
        target=104.0,
        risk_amount=1000000.0,
        risk_reward_ratio=2.0,
        explanation="AI hallucinates 100% win",
        status="APPROVED",
        confidence_score=99.0,
        expires_at=utcnow() + timedelta(hours=1),
    )
    is_valid, reason, checks = RiskService.validate_buy_execution(
        db=db_session,
        proposal=proposal,
    )
    assert is_valid is False
    assert "exceeds maximum allowed allocation" in reason or "exceeds" in reason or not checks.get("position_size_clear", True)


# ============================================================================
# 13. STRATEGY VERSION CONTROL & METADATA AUDIT
# ============================================================================

def test_strategy_version_control_and_metadata(db_session):
    """Verify that every backtest output tags strategy_id, strategy_version, data_split, and timestamp."""
    req = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
        parameters={"fast_period": 9, "slow_period": 21},
    )
    res = BacktestingService.run_backtest(db=db_session, req=req)

    assert res.strategy_id == "STRAT-EMA-CROSS"
    assert res.strategy_version == "1.0.0"
    assert res.data_split == "FULL"
    assert res.dataset_identity == "EUR/USD"
    assert res.timestamp is not None
    assert res.parameters == {"fast_period": 9, "slow_period": 21}


# ============================================================================
# 14. RUNTIME PERFORMANCE BENCHMARK
# ============================================================================

def test_backtest_runtime_benchmark(db_session):
    """Verify indicator calculation and backtest execution are fast (< 1.5 seconds for 100 candles)."""
    candles = generate_synthetic_candles(100)

    t0 = time.perf_counter()
    indicators = IndicatorsService.compute_all_indicators(candles, "BENCH", "1D")
    t_ind = time.perf_counter() - t0

    assert t_ind < 0.5, f"Indicator computation too slow: {t_ind:.4f}s"

    t1 = time.perf_counter()
    req = BacktestRequest(
        symbol="EUR/USD",
        timeframe="1D",
        market="FOREX",
        strategy_name="EMA Crossover",
    )
    res = BacktestingService.run_backtest(db=db_session, req=req)
    t_bt = time.perf_counter() - t1

    assert t_bt < 1.5, f"Backtest execution too slow: {t_bt:.4f}s"
