"""Pytest test suite for Vibe Trader AI Backend."""
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.database.session import engine, init_db


@pytest.fixture(scope="module")
def client():
    # Ensure database is initialized
    init_db()
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    """Test that GET /api/health returns 200 and reports database connected."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database_connected"] is True
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


def test_market_demo_endpoint(client):
    """Test GET /api/market/demo returns required demo structures."""
    response = client.get("/api/market/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["is_demo"] is True

    # Check portfolio
    portfolio = data["portfolio"]
    assert "total_value" in portfolio
    assert "available_cash" in portfolio
    assert "daily_pnl" in portfolio
    assert portfolio["is_mock"] is True

    # Check market statuses for Forex, NSE, MCX
    statuses = data["market_statuses"]
    market_names = [s["market"] for s in statuses]
    assert "FOREX" in market_names
    assert "NSE" in market_names
    assert "MCX" in market_names

    # Check instruments
    instruments = data["instruments"]
    assert len(instruments) > 0
    categories = {i["market"] for i in instruments}
    assert "FOREX" in categories
    assert "NSE" in categories
    assert "MCX" in categories

    # Check AI insight
    insight = data["ai_insight"]
    assert "DEMO" in insight["disclaimer"].upper()
    assert "sentiment" in insight


def test_market_instruments_filtering(client):
    """Test GET /api/market/instruments with market filtering."""
    for market in ["FOREX", "NSE", "MCX"]:
        response = client.get(f"/api/market/instruments?market={market}")
        assert response.status_code == 200
        items = response.json()
        assert len(items) > 0
        for item in items:
            assert item["market"] == market


def test_ohlc_endpoint(client):
    """Test GET /api/market/ohlc/{symbol} returns valid candlestick data."""
    test_symbols = ["EUR/USD", "RELIANCE", "GOLD"]
    for sym in test_symbols:
        response = client.get(f"/api/market/ohlc/{sym}")
        assert response.status_code == 200
        data = response.json()
        assert "is_mock" in data
        assert isinstance(data["is_mock"], bool)
        assert len(data["candles"]) > 0
        candle = data["candles"][0]
        assert "time" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        assert candle["high"] >= candle["low"]


def test_database_tables_exist():
    """Verify all requested models are registered and tables exist in SQLite."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    expected = [
        "user_settings",
        "watchlist_instruments",
        "strategies",
        "paper_trades",
        "trade_journal_entries",
    ]
    for exp in expected:
        assert exp in tables, f"Expected table '{exp}' to exist in database"
