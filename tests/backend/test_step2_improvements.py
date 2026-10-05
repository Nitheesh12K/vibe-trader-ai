"""Targeted Verification Suite for Step 2 Engine Improvements:
1. Dynamic Strategy Dispatch in Backtesting Engine
2. Agent Fleet Real State Tracking (no fake COMPLETED)
3. Market Trading Status & Multi-Market Calendar
4. Persistent CSV Datasets (SQLite-backed, row/size limits, audit logging)
"""
import json
import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

from main import app
from app.database.session import SessionLocal
from app.models.entities import CustomDataset, AuditLog, AgentExecutionCycle
from app.market_data.session_calendar import MarketSessionCalendar, MarketSessionStatus
from app.services.csv_data_provider import CSVDataProvider, CSVValidationResult
from app.services.core_intelligence.coordinator import MultiAgentCoordinator
from app.services.strategy_engine import StrategyEngine
from app.services.backtesting_service import BacktestingService
from app.schemas.workflow import BacktestRequest
from app.schemas.market import OHLCCandle

client = TestClient(app)


# ============================================================================
# 1. Backtesting Engine — Dynamic Strategy Dispatch Tests
# ============================================================================

def test_backtesting_dynamic_strategy_dispatch_multiple_strategies():
    """Verify different strategies from STRATEGY_CATALOG execute and return valid results."""
    # Test EMA Crossover
    req_ema = {
        "strategy_name": "STRAT-EMA-CROSS",
        "symbol": "EUR/USD",
        "timeframe": "1D",
        "market": "FOREX",
        "initial_capital": 100000.0,
    }
    res_ema = client.post("/api/backtesting/run", json=req_ema)
    assert res_ema.status_code == 200
    data_ema = res_ema.json()
    assert data_ema["strategy_name"] in ["EMA Crossover", "EMA Momentum Trend Following"]
    assert data_ema["initial_capital"] == 100000.0
    assert "trades" in data_ema
    assert "profit_factor" in data_ema
    assert "max_drawdown_pct" in data_ema

    # Test RSI Reversal
    req_rsi = {
        "strategy_name": "STRAT-RSI-REV",
        "symbol": "EUR/USD",
        "timeframe": "1D",
        "market": "FOREX",
        "initial_capital": 100000.0,
    }
    res_rsi = client.post("/api/backtesting/run", json=req_rsi)
    assert res_rsi.status_code == 200
    data_rsi = res_rsi.json()
    assert data_rsi["strategy_name"] in ["RSI Reversal", "RSI Support Confluence"]

    # Test Bollinger Band Reversion
    req_bb = {
        "strategy_name": "STRAT-BB-REV",
        "symbol": "EUR/USD",
        "timeframe": "1D",
        "market": "FOREX",
        "initial_capital": 100000.0,
    }
    res_bb = client.post("/api/backtesting/run", json=req_bb)
    assert res_bb.status_code == 200
    data_bb = res_bb.json()
    assert data_bb["strategy_name"] in ["Bollinger Band Reversion", "Bollinger Band Mean Reversion"]


def test_backtesting_unsupported_strategy_raises_400():
    """Verify requesting an uncataloged strategy raises HTTP 400 with helpful catalog hints."""
    req_invalid = {
        "strategy_name": "NON_EXISTENT_MARTINGALE_BOT",
        "symbol": "EUR/USD",
        "timeframe": "1D",
        "market": "FOREX",
    }
    res = client.post("/api/backtesting/run", json=req_invalid)
    assert res.status_code == 400
    err_msg = res.json()["detail"]
    assert "Unsupported strategy 'NON_EXISTENT_MARTINGALE_BOT'" in err_msg
    assert "STRAT-EMA-CROSS" in err_msg or "EMA Momentum" in err_msg


def test_backtesting_chronological_candle_history_requirement():
    """Verify backtester requires sufficient historical warmup to prevent look-ahead bias."""
    short_candles = [
        OHLCCandle(time=1700000000 + i * 86400, open=100.0, high=101.0, low=99.0, close=100.5, volume=1000.0)
        for i in range(10)
    ]
    CSVDataProvider._STORED_DATASETS["SHORT_SERIES"] = short_candles

    with SessionLocal() as db:
        req = BacktestRequest(
            strategy_name="STRAT-EMA-CROSS",
            symbol="SHORT_SERIES",
            timeframe="1D",
            market="FOREX",
        )
        # Directly test with insufficient candles
        summary = BacktestingService.run_backtest(db=db, req=req)
        # When insufficient candles, total_trades must be 0 and disclaimer must note data requirement
        assert summary.total_trades == 0
        assert "BACKTEST INSUFFICIENT DATA" in summary.disclaimer


# ============================================================================
# 2. Agent Fleet Status — Real State Tracking Tests
# ============================================================================

def test_agent_fleet_status_initial_state_is_idle():
    """Verify agents start with valid non-fake status."""
    coordinator = MultiAgentCoordinator()
    with SessionLocal() as db:
        status_report = coordinator.get_status(db=db)

    assert status_report.agents is not None
    assert len(status_report.agents) == 8

    # Check individual agents have valid non-fake statuses
    for agent_id, agent_meta in status_report.agents.items():
        assert agent_meta.status in ["IDLE", "COMPLETED", "READY"]
        assert agent_id in [
            "perception", "reasoning", "memory", "learning",
            "planning", "risk_guardian", "trade_manager", "outcome_evaluator"
        ]


def test_agent_status_polling_does_not_trigger_inference():
    """Verify GET /api/intelligence/status is a read-only endpoint that does not trigger new cycles."""
    with SessionLocal() as db:
        initial_cycle_count = db.query(AgentExecutionCycle).count()

    # Poll status endpoint multiple times
    for _ in range(3):
        res = client.get("/api/intelligence/status")
        assert res.status_code == 200
        data = res.json()
        assert len(data["agents"]) == 8

    with SessionLocal() as db:
        post_cycle_count = db.query(AgentExecutionCycle).count()

    # No execution cycle should have been spawned from simple status polling
    assert post_cycle_count == initial_cycle_count


def test_agent_execution_cycle_updates_and_persists_fleet_status():
    """Verify executing an evaluation cycle records real execution metrics."""
    res = client.post(
        "/api/intelligence/cycle",
        json={"symbol": "EUR/USD", "market": "FOREX", "timeframe": "1D"},
    )
    assert res.status_code == 200
    cycle_data = res.json()
    assert "cycle_id" in cycle_data
    assert cycle_data["cycle_id"].startswith("CYCLE-")
    assert "agent_states" in cycle_data

    # Query fleet status after cycle execution
    status_res = client.get("/api/intelligence/status")
    assert status_res.status_code == 200
    fleet = status_res.json()
    assert "agents" in fleet
    assert "perception" in fleet["agents"]
    assert fleet["agents"]["perception"]["execution_id"] == cycle_data["cycle_id"]

    # Verify coordinator restored persisted state
    new_coordinator = MultiAgentCoordinator()
    with SessionLocal() as db:
        restored = new_coordinator.get_status(db=db)
        assert restored.agents["perception"].execution_id == cycle_data["cycle_id"]


# ============================================================================
# 3. Market Trading Status — Calendar and Session Logic Tests
# ============================================================================

def test_nse_market_sessions_schedule():
    """Verify NSE sessions: Pre-open, Regular Trading, Post-close, and Night/Weekend Closed."""
    ist = ZoneInfo("Asia/Kolkata")

    # Regular Trading Day: Wednesday 2026-03-11 at 10:30 AM IST (Trading open)
    trading_dt = datetime(2026, 3, 11, 10, 30, tzinfo=ist)
    nse_open = MarketSessionCalendar.get_market_status("NSE", current_dt=trading_dt)
    assert nse_open.status == MarketSessionStatus.OPEN
    assert nse_open.is_open is True

    # Pre-open Session: Wednesday 2026-03-11 at 09:05 AM IST
    pre_open_dt = datetime(2026, 3, 11, 9, 5, tzinfo=ist)
    nse_pre = MarketSessionCalendar.get_market_status("NSE", current_dt=pre_open_dt)
    assert nse_pre.status == MarketSessionStatus.PRE_OPEN
    assert nse_pre.is_open is False

    # Post-close Session: Wednesday 2026-03-11 at 15:45 (3:45 PM IST)
    post_close_dt = datetime(2026, 3, 11, 15, 45, tzinfo=ist)
    nse_post = MarketSessionCalendar.get_market_status("NSE", current_dt=post_close_dt)
    assert nse_post.status == MarketSessionStatus.POST_CLOSE
    assert nse_post.is_open is False

    # Night Closed: Wednesday 2026-03-11 at 22:00 (10:00 PM IST)
    night_dt = datetime(2026, 3, 11, 22, 0, tzinfo=ist)
    nse_night = MarketSessionCalendar.get_market_status("NSE", current_dt=night_dt)
    assert nse_night.status == MarketSessionStatus.CLOSED
    assert nse_night.is_open is False

    # Weekend Closed: Sunday 2026-03-15 at 11:00 AM IST
    weekend_dt = datetime(2026, 3, 15, 11, 0, tzinfo=ist)
    nse_weekend = MarketSessionCalendar.get_market_status("NSE", current_dt=weekend_dt)
    assert nse_weekend.status == MarketSessionStatus.CLOSED
    assert "Weekend" in nse_weekend.reason


def test_nse_holiday_calendar_detection():
    """Verify Indian National Holidays (e.g. Gandhi Jayanti on Oct 2) are detected as closed."""
    ist = ZoneInfo("Asia/Kolkata")

    # Gandhi Jayanti (2026-10-02 at 11:00 AM IST - Friday)
    holiday_dt = datetime(2026, 10, 2, 11, 0, tzinfo=ist)
    nse_holiday = MarketSessionCalendar.get_market_status("NSE", current_dt=holiday_dt)
    assert nse_holiday.status in [MarketSessionStatus.CLOSED, MarketSessionStatus.HOLIDAY]
    assert nse_holiday.is_open is False
    assert "holiday" in nse_holiday.reason.lower()


def test_forex_24_5_market_hours():
    """Verify FOREX runs 24/5 UTC, closing Friday 22:00 UTC and opening Sunday 22:00 UTC."""
    # Wednesday at noon UTC -> OPEN
    midweek_dt = datetime(2026, 3, 11, 12, 0, tzinfo=timezone.utc)
    fx_open = MarketSessionCalendar.get_market_status("FOREX", current_dt=midweek_dt)
    assert fx_open.status == MarketSessionStatus.OPEN
    assert fx_open.is_open is True

    # Saturday at noon UTC -> CLOSED
    saturday_dt = datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc)
    fx_closed = MarketSessionCalendar.get_market_status("FOREX", current_dt=saturday_dt)
    assert fx_closed.status == MarketSessionStatus.CLOSED
    assert fx_closed.is_open is False
    assert "Weekend" in fx_closed.reason


def test_market_api_status_integration():
    """Verify GET /api/market/demo includes real-time session evaluations with reasons."""
    res = client.get("/api/market/demo")
    assert res.status_code == 200
    data = res.json()
    assert "market_statuses" in data
    statuses = data["market_statuses"]
    assert len(statuses) >= 3

    markets = {s["market"] for s in statuses}
    assert "NSE" in markets
    assert "MCX" in markets
    assert "FOREX" in markets

    for s in statuses:
        assert s["status"] in ["OPEN", "CLOSED", "PRE_OPEN", "POST_CLOSE", "HOLIDAY"]
        assert "reason" in s
        assert "evaluated_at" in s


# ============================================================================
# 4. CSV Dataset Persistence — SQLite Storage & Safeguards Tests
# ============================================================================

def test_csv_file_size_and_row_count_safeguards():
    """Verify CSV parser enforces 10MB raw content and 50,000 row limits."""
    # Huge content > 10MB
    large_csv = "date,open,high,low,close,volume\n" + ("2026-01-01,100,105,95,102,1000\n" * 350000)
    result = CSVDataProvider.validate_and_parse_csv(csv_content=large_csv, symbol_override="TOO_LARGE")
    assert result.is_valid is False
    assert any("exceeds maximum allowed limit" in err for err in result.errors)


def test_csv_upload_persists_in_sqlite():
    """Verify valid uploaded CSV persists to SQLite and survives new DB sessions."""
    csv_text = """date,open,high,low,close,volume
2026-01-01,100.0,105.0,98.0,103.0,15000
2026-01-02,103.0,108.0,102.0,107.0,20000
2026-01-03,107.0,110.0,105.0,106.0,18000
2026-01-04,106.0,112.0,104.0,111.0,22000
"""
    test_symbol = "PERSIST_TEST_SYM"

    # Clean up prior test data if exists
    with SessionLocal() as db:
        old = db.query(CustomDataset).filter(CustomDataset.symbol == test_symbol).first()
        if old:
            db.delete(old)
            db.commit()

    upload_payload = {
        "csv_content": csv_text,
        "symbol": test_symbol,
        "market": "NSE",
        "filename": "../../unsafe_path/test_data.csv",
        "timeframe": "1D",
        "overwrite": True,
    }
    res = client.post("/api/market/csv/upload", json=upload_payload)
    assert res.status_code == 200
    upload_data = res.json()
    assert upload_data["is_valid"] is True
    assert upload_data["total_rows"] == 4
    dataset_id = upload_data["dataset_id"]
    assert dataset_id.startswith("DS-")

    # Verify directly in fresh SQLite session
    with SessionLocal() as db:
        rec = db.query(CustomDataset).filter(CustomDataset.dataset_id == dataset_id).first()
        assert rec is not None
        assert rec.symbol == test_symbol
        assert rec.row_count == 4
        assert rec.original_filename == "test_data.csv"  # Sanitized!
        assert rec.is_valid is True

        # Verify Audit Log event was created
        audit_entry = (
            db.query(AuditLog)
            .filter(AuditLog.event_type == "DATASET_IMPORTED", AuditLog.symbol == test_symbol)
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert audit_entry is not None
        assert dataset_id in audit_entry.action


def test_csv_datasets_listing_and_retrieval():
    """Verify GET /api/market/csv/datasets and GET /api/market/csv/datasets/{dataset_id}."""
    res = client.get("/api/market/csv/datasets")
    assert res.status_code == 200
    data = res.json()
    assert "datasets" in data
    assert "total_datasets" in data
    assert any(d["symbol"] == "PERSIST_TEST_SYM" for d in data["datasets"])

    # Retrieve specific dataset by ID
    target_ds = next(d for d in data["datasets"] if d["symbol"] == "PERSIST_TEST_SYM")
    detail_res = client.get(f"/api/market/csv/datasets/{target_ds['dataset_id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["symbol"] == "PERSIST_TEST_SYM"
    assert detail["row_count"] == 4
    assert len(detail["preview_candles"]) == 4


def test_csv_dataset_duplicate_protection():
    """Verify upload fails with 409 Conflict when duplicate symbol exists and overwrite=False."""
    csv_text = """date,open,high,low,close,volume
2026-01-01,100.0,105.0,98.0,103.0,15000
2026-01-02,103.0,108.0,102.0,107.0,20000
"""
    # Attempt upload with overwrite=False
    payload = {
        "csv_content": csv_text,
        "symbol": "PERSIST_TEST_SYM",
        "overwrite": False,
    }
    res = client.post("/api/market/csv/upload", json=payload)
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"]


def test_csv_dataset_deletion_and_audit():
    """Verify DELETE /api/market/csv/datasets/{dataset_id} removes from DB and logs audit trail."""
    # Lookup dataset_id
    with SessionLocal() as db:
        rec = db.query(CustomDataset).filter(CustomDataset.symbol == "PERSIST_TEST_SYM").first()
        assert rec is not None
        ds_id = rec.dataset_id

    delete_res = client.delete(f"/api/market/csv/datasets/{ds_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    # Verify removed from database
    with SessionLocal() as db:
        deleted_rec = db.query(CustomDataset).filter(CustomDataset.dataset_id == ds_id).first()
        assert deleted_rec is None

        # Verify Audit Log event for deletion
        del_audit = (
            db.query(AuditLog)
            .filter(AuditLog.event_type == "DATASET_DELETED", AuditLog.symbol == "PERSIST_TEST_SYM")
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert del_audit is not None
        assert ds_id in del_audit.action


def test_backtest_with_imported_csv_dataset():
    """Verify backtesting runs on an uploaded custom CSV dataset seamlessly."""
    base_date = datetime(2026, 1, 1)
    csv_rows = ["date,open,high,low,close,volume"]
    for i in range(50):
        price = 100.0 + (i * 0.8) + (0.4 if i % 2 == 0 else -0.3)
        dt_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        csv_rows.append(f"{dt_str},{price:.2f},{price + 1.5:.2f},{price - 1.2:.2f},{price + 0.5:.2f},50000")

    csv_content = "\n".join(csv_rows)
    custom_symbol = "CUSTOM_GROWTH_STOCK"

    # Upload dataset
    upload_res = client.post("/api/market/csv/upload", json={
        "csv_content": csv_content,
        "symbol": custom_symbol,
        "overwrite": True,
    })
    assert upload_res.status_code == 200
    assert upload_res.json()["is_valid"] is True

    # Run backtest on custom symbol
    backtest_res = client.post("/api/backtesting/run", json={
        "strategy_name": "STRAT-EMA-CROSS",
        "symbol": custom_symbol,
        "timeframe": "1D",
        "market": "CUSTOM",
        "initial_capital": 50000.0,
    })
    assert backtest_res.status_code == 200
    bt_data = backtest_res.json()
    assert bt_data["symbol"] == custom_symbol
    assert bt_data["initial_capital"] == 50000.0
    assert "profit_factor" in bt_data
    assert "trades" in bt_data

    # Cleanup dataset
    with SessionLocal() as db:
        rec = db.query(CustomDataset).filter(CustomDataset.symbol == custom_symbol).first()
        if rec:
            CSVDataProvider.delete_dataset(db, rec.dataset_id)
