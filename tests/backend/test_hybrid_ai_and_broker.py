"""Comprehensive tests for Hybrid AI Engine, Strategy Catalogue, Zerodha Fail-Closed Safety, and CSV Data Provider."""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.indicators_service import IndicatorsService
from app.services.strategy_engine import StrategyEngine
from app.services.ai_provider import ai_service, DeterministicFallbackProvider, OllamaProvider
from app.services.zerodha_service import zerodha_service
from app.services.csv_data_provider import CSVDataProvider
from app.schemas.market import OHLCCandle
from app.database.session import SessionLocal
from app.models.entities import Position, RiskSettings

client = TestClient(app)


def generate_sample_candles(count: int = 50, base_price: float = 100.0, trend: float = 0.5):
    candles = []
    price = base_price
    for i in range(count):
        price += trend + (0.2 if i % 2 == 0 else -0.1)
        o = price - 0.2
        c = price + 0.2
        h = max(o, c) + 0.5
        l = min(o, c) - 0.5
        candles.append(OHLCCandle(
            time=1700000000 + (i * 86400),
            open=round(o, 2),
            high=round(h, 2),
            low=round(l, 2),
            close=round(c, 2),
            volume=round(1000.0 + (i * 50), 2),
        ))
    return candles


# 1. Indicators: VWAP & Volume SMA Tests
def test_indicators_vwap_and_volume_sma():
    candles = generate_sample_candles(count=30, base_price=2500.0, trend=1.5)
    indicators = IndicatorsService.compute_all_indicators(candles, symbol="RELIANCE", timeframe="1D")

    assert len(indicators.vwap) == 30
    assert indicators.vwap[-1].value is not None
    assert indicators.vwap[-1].value > 2000.0

    assert len(indicators.volume_sma) == 30
    # First 19 points should be None due to 20-period lookback
    assert indicators.volume_sma[0].value is None
    assert indicators.volume_sma[-1].value is not None
    assert indicators.volume_sma[-1].value > 0.0


# 2. Strategy Catalogue & 7 Strategies Evaluation Tests
def test_strategy_catalogue_contains_all_seven_strategies():
    catalogue = StrategyEngine.get_strategy_catalogue()
    strategy_ids = [s.strategy_id for s in catalogue]

    expected_ids = [
        "STRAT-EMA-CROSS",
        "STRAT-RSI-REV",
        "STRAT-MACD-MOM",
        "STRAT-VWAP-TREND",
        "STRAT-BB-REV",
        "STRAT-VOL-BREAKOUT",
        "STRAT-MULTI-CONF",
    ]
    for s_id in expected_ids:
        assert s_id in strategy_ids, f"Strategy {s_id} missing from catalogue"

    res = client.get("/api/strategies/catalogue/all")
    assert res.status_code == 200
    assert len(res.json()) >= 7


def test_strategy_signal_evaluation_states():
    candles = generate_sample_candles(count=40, base_price=100.0, trend=1.0)
    indicators = IndicatorsService.compute_all_indicators(candles, symbol="TATAMOTORS", timeframe="1D")
    from app.services.pattern_service import PatternService
    from app.services.support_resistance_service import SupportResistanceService

    patterns = PatternService.detect_patterns(candles, symbol="TATAMOTORS", timeframe="1D")
    sr = SupportResistanceService.calculate_zones(candles, symbol="TATAMOTORS", timeframe="1D")

    # Evaluate each of the 7 strategies
    for s_def in StrategyEngine.get_strategy_catalogue():
        signal_out = StrategyEngine.evaluate_strategy_signal(
            strategy_id=s_def.strategy_id,
            symbol="TATAMOTORS",
            market="NSE",
            timeframe="1D",
            candles=candles,
            indicators=indicators,
            patterns=patterns,
            sr=sr,
        )
        assert signal_out.signal_state in ["BUY_CANDIDATE", "SELL_CANDIDATE", "HOLD", "NO_TRADE", "INVALID_DATA"]
        assert 0.0 <= signal_out.confidence_score <= 1.0
        assert signal_out.is_trade_authorization is False


# 3. AI Analysis & Provider Abstraction Tests
def test_ai_provider_status_and_fallback():
    status_data = ai_service.get_provider_status()
    assert "ollama" in status_data
    assert "active_provider" in status_data
    assert status_data["hallucination_defense_active"] is True

    res = client.get("/api/analysis/ai/status")
    assert res.status_code == 200
    assert res.json()["hallucination_defense_active"] is True


def test_deterministic_ai_analysis_schema_validity():
    candles = generate_sample_candles(count=35, base_price=500.0, trend=0.8)
    indicators = IndicatorsService.compute_all_indicators(candles, symbol="INFY", timeframe="1D")

    indicator_dict = {
        "rsi": indicators.rsi[-1].value,
        "macd_histogram": indicators.macd[-1].histogram,
        "ema_9": indicators.ema_9[-1].value,
        "ema_21": indicators.ema_21[-1].value,
        "ema_50": indicators.ema_50[-1].value,
        "atr": indicators.atr[-1].value,
        "vwap": indicators.vwap[-1].value,
    }

    analysis = ai_service.analyze_market_setup(
        symbol="INFY",
        market="NSE",
        timeframe="1D",
        current_price=candles[-1].close,
        indicators=indicator_dict,
        patterns=["Bullish Hammer"],
        sr_zones=[480.0, 520.0],
        strategy_signal="BUY_CANDIDATE",
    )

    assert analysis.analysis_id.startswith("AI-ANA-")
    assert analysis.symbol == "INFY"
    assert analysis.market_state in ["TRENDING_BULLISH", "TRENDING_BEARISH", "RANGING", "HIGH_VOLATILITY", "COMPRESSION", "UNCERTAIN"]
    assert analysis.is_trade_authorization is False
    assert analysis.quality_metrics.structured_output_validity is True
    assert analysis.quality_metrics.input_completeness_pct > 0


def test_ai_analysis_api_endpoint():
    res = client.post(
        "/api/analysis/ai/evaluate",
        json={"symbol": "NIFTY 50", "market": "NSE", "timeframe": "1D", "strategy_id": "STRAT-MULTI-CONF"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "NIFTY 50"
    assert "quality_metrics" in data
    assert data["is_trade_authorization"] is False


# 4. Zerodha Kite Connect Fail-Closed Safety Tests
def test_zerodha_status_and_login_url():
    status_res = client.get("/api/broker/zerodha/status")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["broker_name"] == "Zerodha Kite Connect Personal (Free)"
    assert data["live_execution_mode"] == "STRICTLY_DISABLED (FAIL_CLOSED)"
    assert "disclaimer" in data

    url_res = client.get("/api/broker/zerodha/login-url")
    assert url_res.status_code == 200
    assert "kite.zerodha.com" in url_res.json()["login_url"]


def test_zerodha_live_order_strictly_blocked():
    """Security check: live broker order placement must return 403 Forbidden under fail-closed policy."""
    order_res = client.post("/api/broker/zerodha/orders", json={"symbol": "RELIANCE", "quantity": 10})
    assert order_res.status_code == 403
    assert "Live broker order execution is strictly disabled" in order_res.json()["detail"]


# 5. CSV Data Provider Consistency Tests
def test_csv_data_provider_valid_file():
    valid_csv = """time,open,high,low,close,volume
1700000000,100.0,105.0,99.0,104.0,1500
1700086400,104.0,108.0,103.0,107.0,2000
1700172800,107.0,110.0,106.0,109.0,2500
"""
    result = CSVDataProvider.validate_and_parse_csv(valid_csv, symbol_override="TEST_CSV")
    assert result.is_valid is True
    assert result.total_rows == 3
    assert len(result.candles) == 3
    assert result.candles[0].high == 105.0


def test_csv_data_provider_detects_inconsistencies():
    # Inconsistent high < low and negative price
    invalid_csv = """time,open,high,low,close,volume
1700000000,100.0,95.0,99.0,98.0,1500
1700086400,104.0,108.0,103.0,-5.0,2000
"""
    result = CSVDataProvider.validate_and_parse_csv(invalid_csv, symbol_override="BAD_CSV")
    assert result.is_valid is False
    assert len(result.errors) >= 2


def test_csv_upload_api_endpoint():
    valid_csv = """date,open,high,low,close,volume
2026-01-01,2500.0,2550.0,2480.0,2530.0,50000
2026-01-02,2530.0,2580.0,2510.0,2570.0,60000
"""
    res = client.post("/api/market/csv/upload", json={"csv_content": valid_csv, "symbol": "RELIANCE_CSV"})
    assert res.status_code == 200
    assert res.json()["is_valid"] is True
    assert res.json()["total_rows"] == 2


# 6. Risk Settings Demo Reset Tests
def test_risk_settings_reset_to_demo_defaults():
    res = client.post("/api/risk/reset-defaults")
    assert res.status_code == 200
    data = res.json()
    assert data["simulated_balance"] == 2000.0
    assert data["max_risk_per_trade_pct"] == 0.5
    assert data["max_daily_loss"] == 40.0
    assert data["max_open_positions"] == 1
    assert data["emergency_stop_active"] is False

    # Restore settings for remaining tests
    with SessionLocal() as db:
        risk = db.query(RiskSettings).first()
        if risk:
            risk.simulated_balance = 100000.0
            risk.max_risk_per_trade_pct = 2.0
            risk.max_daily_loss = 5000.0
            risk.max_open_positions = 50
            db.commit()
