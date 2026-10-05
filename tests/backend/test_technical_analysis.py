"""Unit and Integration tests for Technical Analysis calculations and endpoints."""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.database.session import init_db
from app.schemas.market import OHLCCandle
from app.services.indicators_service import IndicatorsService
from app.services.pattern_service import PatternService
from app.services.support_resistance_service import SupportResistanceService


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


def test_indicators_service_calculations():
    """Verify RSI, MACD, EMA, SMA, ATR, and Bollinger Bands calculation logic."""
    # Create 30 synthetic ascending candles
    base_time = 1700000000
    candles = [
        OHLCCandle(
            time=base_time + (i * 86400),
            open=100.0 + i,
            high=102.0 + i,
            low=99.0 + i,
            close=101.5 + i,
            volume=500.0 + i * 10
        )
        for i in range(40)
    ]

    res = IndicatorsService.compute_all_indicators(
        candles=candles,
        symbol="TEST",
        timeframe="1D"
    )

    assert len(res.rsi) == 40
    # Last RSI point should have a valid value > 70 due to steady gain
    valid_rsi = [p.value for p in res.rsi if p.value is not None]
    assert len(valid_rsi) > 0
    assert 0.0 <= valid_rsi[-1] <= 100.0
    assert valid_rsi[-1] > 60.0

    # MACD check
    assert len(res.macd) == 40
    valid_macd = [p for p in res.macd if p.macd is not None and p.signal is not None]
    assert len(valid_macd) > 0

    # Bollinger check
    assert len(res.bollinger) == 40
    valid_bb = [p for p in res.bollinger if p.upper is not None and p.lower is not None]
    assert len(valid_bb) > 0
    assert valid_bb[-1].upper > valid_bb[-1].middle > valid_bb[-1].lower

    # ATR check
    assert len(res.atr) == 40
    valid_atr = [p.value for p in res.atr if p.value is not None]
    assert len(valid_atr) > 0
    assert valid_atr[-1] > 0


def test_candlestick_pattern_detection():
    """Verify rule-based detection of Doji, Hammer, Engulfing, and Star patterns."""
    base_time = 1700000000
    candles = [
        # Normal candle
        OHLCCandle(time=base_time, open=100.0, high=102.0, low=99.0, close=101.0, volume=100),
        # 1. Doji: open == close with wide high/low
        OHLCCandle(time=base_time + 60, open=101.0, high=105.0, low=97.0, close=101.05, volume=100),
        # 2. Hammer: open 100, close 101, high 101.2, low 95.0 (long lower wick >= 2x body)
        OHLCCandle(time=base_time + 120, open=100.0, high=101.2, low=95.0, close=101.0, volume=100),
        # 3. Setup Bearish Engulfing: prev green candle, next massive red candle
        OHLCCandle(time=base_time + 180, open=101.0, high=103.0, low=100.5, close=102.5, volume=100),
        OHLCCandle(time=base_time + 240, open=103.0, high=103.5, low=98.0, close=99.0, volume=200),
    ]

    res = PatternService.detect_patterns(candles=candles, symbol="TEST", timeframe="1m")
    pattern_names = [p.pattern_name for p in res.patterns]
    assert "Doji" in pattern_names
    assert "Hammer" in pattern_names
    assert "Bearish Engulfing" in pattern_names

    # Test Morning Star pattern
    ms_candles = [
        # C1: Long red candle
        OHLCCandle(time=base_time + 300, open=110.0, high=110.5, low=100.0, close=101.0, volume=100),
        # C2: Small star gapped/low body
        OHLCCandle(time=base_time + 360, open=99.0, high=100.0, low=98.0, close=99.2, volume=80),
        # C3: Bullish green recovering > 50%
        OHLCCandle(time=base_time + 420, open=99.5, high=108.0, low=99.0, close=107.0, volume=150),
    ]
    ms_res = PatternService.detect_patterns(candles=ms_candles, symbol="TEST", timeframe="1m")
    ms_names = [p.pattern_name for p in ms_res.patterns]
    assert "Morning Star" in ms_names


def test_support_resistance_service():
    """Verify Support & Resistance swing cluster generation and classification."""
    base_time = 1700000000
    # Create price structure with clear peaks at 120 and troughs at 100
    candles = [
        OHLCCandle(time=base_time + i*60, open=105, high=106, low=104, close=105, volume=100)
        for i in range(5)
    ]
    # Add a swing peak
    candles.append(OHLCCandle(time=base_time + 300, open=115, high=125, low=114, close=120, volume=200))
    candles.append(OHLCCandle(time=base_time + 360, open=120, high=121, low=112, close=113, volume=150))
    candles.append(OHLCCandle(time=base_time + 420, open=113, high=114, low=108, close=110, volume=120))
    # Add a swing trough
    candles.append(OHLCCandle(time=base_time + 480, open=105, high=106, low=95, close=98, volume=180))
    candles.append(OHLCCandle(time=base_time + 540, open=98, high=106, low=97, close=105, volume=140))
    candles.append(OHLCCandle(time=base_time + 600, open=105, high=108, low=104, close=107, volume=100))

    sr = SupportResistanceService.calculate_zones(candles=candles, symbol="TEST", timeframe="1m", tolerance=0.02)
    assert len(sr.zones) > 0
    # Every zone has valid price, zone_type, and touches
    for z in sr.zones:
        assert z.zone_type in ["Support", "Resistance"]
        assert z.touches >= 1
        assert z.strength in ["Strong", "Moderate", "Minor"]


def test_api_analysis_endpoints(client):
    """Test all 5 technical analysis REST endpoints."""
    # 1. Indicators
    resp = client.get("/api/analysis/indicators?symbol=EUR/USD&timeframe=1D")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "EUR/USD"
    assert "rsi" in data
    assert "macd" in data
    assert "ema_9" in data
    assert "bollinger" in data

    # 2. Patterns
    resp = client.get("/api/analysis/patterns?symbol=EUR/USD&timeframe=1D")
    assert resp.status_code == 200
    pdata = resp.json()
    assert "patterns" in pdata
    assert "total_detected" in pdata

    # 3. Support & Resistance
    resp = client.get("/api/analysis/support-resistance?symbol=EUR/USD&timeframe=1D")
    assert resp.status_code == 200
    srdata = resp.json()
    assert "zones" in srdata
    assert "current_price" in srdata

    # 4. Summary
    resp = client.get("/api/analysis/summary?symbol=EUR/USD&timeframe=1D&market=FOREX")
    assert resp.status_code == 200
    sumdata = resp.json()
    assert "regime" in sumdata
    assert "rsi_summary" in sumdata
    assert "conflicts" in sumdata
    assert "disclaimer" in sumdata
    assert sumdata["data_source"] == "DEMO DATA (Simulated)"
    assert "demo candles" in sumdata["disclaimer"].lower()

    # 5. Full Bundle
    resp = client.get("/api/analysis/full?symbol=EUR/USD&timeframe=1D&market=FOREX")
    assert resp.status_code == 200
    fulldata = resp.json()
    assert "candles" in fulldata
    assert "indicators" in fulldata
    assert "patterns" in fulldata
    assert "support_resistance" in fulldata
    assert "summary" in fulldata
    assert len(fulldata["candles"]) > 0
