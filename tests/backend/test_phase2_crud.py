"""Pytest suite for Phase 2: CRUD endpoints and validation using an isolated test database."""
import os
import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup paths
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.base import Base
from app.database.session import get_db, migrate_sqlite_schema, seed_defaults
from main import app


@pytest.fixture(scope="module")
def test_db_setup():
    """Create an isolated temporary SQLite database for testing."""
    tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_path = tmp_file.name
    tmp_file.close()

    test_engine = create_engine(
        f"sqlite:///{tmp_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Initialize tables and seed defaults
    Base.metadata.create_all(bind=test_engine)
    with TestingSessionLocal() as session:
        seed_defaults(session)

    # Override get_db dependency in FastAPI app
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    # Teardown
    app.dependency_overrides.clear()
    try:
        os.remove(tmp_path)
    except Exception:
        pass


# ============================================================================
# Health Endpoint Tests
# ============================================================================

def test_health_check_with_db(test_db_setup):
    """Test GET /api/health confirms backend and database are healthy."""
    response = test_db_setup.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database_connected"] is True


# ============================================================================
# User Settings Tests
# ============================================================================

def test_settings_read_and_update(test_db_setup):
    """Test reading default settings and updating preferences."""
    # 1. Read
    get_res = test_db_setup.get("/api/settings")
    assert get_res.status_code == 200
    curr = get_res.json()
    assert curr["theme"] in {"dark", "light"}
    assert curr["risk_percentage"] == 1.0

    # 2. Update valid
    update_res = test_db_setup.put(
        "/api/settings",
        json={
            "theme": "light",
            "default_market": "NSE",
            "default_timeframe": "15m",
            "risk_percentage": 2.5,
            "notifications_enabled": False,
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["theme"] == "light"
    assert updated["default_market"] == "NSE"
    assert updated["default_timeframe"] == "15m"
    assert updated["risk_percentage"] == 2.5
    assert updated["notifications_enabled"] is False

    # 3. Invalid risk percentage (> 100 or < 0.1)
    inv_res = test_db_setup.put("/api/settings", json={"risk_percentage": 150.0})
    assert inv_res.status_code == 422

    # 4. Invalid theme
    inv_theme = test_db_setup.put("/api/settings", json={"theme": "blue"})
    assert inv_theme.status_code == 422


# ============================================================================
# Watchlist Tests & Duplicate Prevention
# ============================================================================

def test_watchlist_crud_and_duplicate_prevention(test_db_setup):
    """Test watchlist creation, listing, duplicate prevention, and deletion."""
    # 1. Add unique instrument
    create_res = test_db_setup.post(
        "/api/watchlist",
        json={
            "symbol": "BTC/USD",
            "name": "Bitcoin / US Dollar",
            "market": "FOREX",
            "category": "Crypto",
            "exchange": "Spot",
        },
    )
    assert create_res.status_code == 201
    item = create_res.json()
    item_id = item["id"]
    assert item["symbol"] == "BTC/USD"
    assert item["market"] == "FOREX"

    # 2. Duplicate attempt in same market -> 409 Conflict
    dup_res = test_db_setup.post(
        "/api/watchlist",
        json={
            "symbol": "BTC/USD",
            "name": "Bitcoin / US Dollar",
            "market": "FOREX",
        },
    )
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"]

    # 3. List watchlist with market filter
    list_res = test_db_setup.get("/api/watchlist?market=FOREX")
    assert list_res.status_code == 200
    symbols = [x["symbol"] for x in list_res.json()]
    assert "BTC/USD" in symbols

    # 4. Delete instrument
    del_res = test_db_setup.delete(f"/api/watchlist/{item_id}")
    assert del_res.status_code == 204

    # 5. Verify deletion
    del_verify = test_db_setup.delete(f"/api/watchlist/{item_id}")
    assert del_verify.status_code == 404


# ============================================================================
# Strategies Tests
# ============================================================================

def test_strategy_crud_and_json_validation(test_db_setup):
    """Test strategy creation, JSON parameters validation, update, and deletion."""
    # 1. Valid strategy creation
    create_res = test_db_setup.post(
        "/api/strategies",
        json={
            "name": "MACD Divergence Trader",
            "description": "Cross-market MACD histogram divergence with ATR stops.",
            "market": "NSE",
            "timeframe": "1h",
            "parameters_json": '{"fast": 12, "slow": 26, "signal": 9}',
            "is_active": True,
        },
    )
    assert create_res.status_code == 201
    strat = create_res.json()
    strat_id = strat["id"]
    assert strat["name"] == "MACD Divergence Trader"

    # 2. Invalid JSON in parameters -> 422
    bad_json_res = test_db_setup.post(
        "/api/strategies",
        json={
            "name": "Broken Strategy",
            "parameters_json": "{not valid json}",
        },
    )
    assert bad_json_res.status_code == 422

    # 3. Get by ID
    get_res = test_db_setup.get(f"/api/strategies/{strat_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == strat_id

    # 4. Update
    upd_res = test_db_setup.put(
        f"/api/strategies/{strat_id}",
        json={"is_active": False, "description": "Updated description"},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["is_active"] is False

    # 5. Delete
    del_res = test_db_setup.delete(f"/api/strategies/{strat_id}")
    assert del_res.status_code == 204

    # 6. Verify 404
    get_404 = test_db_setup.get(f"/api/strategies/{strat_id}")
    assert get_404.status_code == 404


# ============================================================================
# Paper Trading Tests
# ============================================================================

def test_paper_trade_lifecycle_and_pnl(test_db_setup):
    """Test opening a paper trade, SL/TP validation, closing, and P&L calculation."""
    # 1. Invalid trade (Long with SL >= entry price) -> 422
    inv_sl = test_db_setup.post(
        "/api/paper-trades",
        json={
            "symbol": "RELIANCE",
            "market": "NSE",
            "direction": "Long",
            "entry_price": 2900.0,
            "stop_loss": 2950.0,  # Invalid: SL is above entry for Long
            "quantity": 10.0,
        },
    )
    assert inv_sl.status_code == 422

    # 2. Valid Long trade
    long_res = test_db_setup.post(
        "/api/paper-trades",
        json={
            "symbol": "RELIANCE",
            "market": "NSE",
            "direction": "Long",
            "entry_price": 2900.0,
            "stop_loss": 2850.0,
            "take_profit": 3050.0,
            "quantity": 10.0,
            "notes": "Testing trend breakout on daily chart",
        },
    )
    assert long_res.status_code == 201
    trade = long_res.json()
    trade_id = trade["id"]
    assert trade["status"] == "Open"
    assert trade["pnl"] is None

    # 3. Close the trade at 2980.00 -> Profit should be (2980 - 2900) * 10 = +$800.00
    close_res = test_db_setup.put(
        f"/api/paper-trades/{trade_id}",
        json={"exit_price": 2980.0},
    )
    assert close_res.status_code == 200
    closed_trade = close_res.json()
    assert closed_trade["status"] == "Closed"
    assert closed_trade["pnl"] == 800.0
    assert closed_trade["closed_at"] is not None

    # 4. Valid Short trade
    short_res = test_db_setup.post(
        "/api/paper-trades",
        json={
            "symbol": "EUR/USD",
            "market": "FOREX",
            "direction": "Short",
            "entry_price": 1.0900,
            "stop_loss": 1.0950,
            "take_profit": 1.0800,
            "quantity": 10000.0,
        },
    )
    assert short_res.status_code == 201
    short_id = short_res.json()["id"]

    # Close Short at 1.0850 -> Profit should be (1.0900 - 1.0850) * 10000 = +$50.00
    close_short = test_db_setup.put(
        f"/api/paper-trades/{short_id}",
        json={"exit_price": 1.0850},
    )
    assert close_short.status_code == 200
    assert close_short.json()["pnl"] == 50.0


# ============================================================================
# Trade Journal Tests
# ============================================================================

def test_journal_crud(test_db_setup):
    """Test trade journal note logging and lessons learned."""
    # 1. Create journal entry
    res = test_db_setup.post(
        "/api/journal",
        json={
            "title": "Asian Session Breakout Review",
            "symbol": "USD/JPY",
            "notes": "Entered on strong momentum after Bank of Japan statement.",
            "lessons_learned": "Wait for 15-minute candle close before executing.",
            "tags": "psychology,execution,forex",
        },
    )
    assert res.status_code == 201
    entry = res.json()
    entry_id = entry["id"]
    assert entry["title"] == "Asian Session Breakout Review"
    assert entry["lessons_learned"] is not None

    # 2. List journal entries
    list_res = test_db_setup.get("/api/journal?symbol=USD/JPY")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 3. Update entry
    upd_res = test_db_setup.put(
        f"/api/journal/{entry_id}",
        json={"title": "Updated Session Review"},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["title"] == "Updated Session Review"

    # 4. Delete entry
    del_res = test_db_setup.delete(f"/api/journal/{entry_id}")
    assert del_res.status_code == 204

    # 5. Verify 404
    get_404 = test_db_setup.get(f"/api/journal/{entry_id}")
    assert get_404.status_code == 404
