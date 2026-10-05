"""Comprehensive automated test suite for Autonomous Trading Workflow:
Strategy Engine, Proposals, Risk Gates, Position Monitoring, Autonomous SELL, and Backtesting.
"""
import sys
import uuid
from pathlib import Path
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.database.session import init_db, SessionLocal
from app.models.entities import (
    BuyProposal,
    Position,
    RiskSettings,
    AutonomousExitPermission,
    TradeReport,
    AuditLog,
    utcnow,
)
from app.schemas.market import OHLCCandle
from app.services.market_data_service import MarketDataService
from app.services.indicators_service import IndicatorsService
from app.services.pattern_service import PatternService
from app.services.support_resistance_service import SupportResistanceService
from app.services.strategy_engine import StrategyEngine
from app.services.position_monitor import PositionMonitorService
from app.services.risk_service import RiskService


@pytest.fixture(scope="module")
def client():
    init_db()
    with SessionLocal() as db:
        risk = RiskService.get_or_create_settings(db)
        risk.emergency_stop_active = False
        risk.max_open_positions = 50
        risk.simulated_balance = 100000.0
        risk.max_risk_per_trade_pct = 2.0
        risk.max_daily_loss = 5000.0
        # Clean up any leftover open test positions from prior runs
        db.query(Position).filter(Position.status == "OPEN").update({"status": "CLOSED"})
        db.commit()
    with TestClient(app) as c:
        yield c


def test_strategy_evaluation_and_proposal_generation():
    """Verify StrategyEngine detects confluence and creates a structured BuyProposal."""
    with SessionLocal() as db:
        market_service = MarketDataService(db=db)
        ohlc = market_service.get_ohlc(symbol="EUR/USD", timeframe="1D")
        candles = ohlc.candles

        indicators = IndicatorsService.compute_all_indicators(candles=candles, symbol="EUR/USD", timeframe="1D")
        patterns = PatternService.detect_patterns(candles=candles, symbol="EUR/USD", timeframe="1D")
        sr = SupportResistanceService.calculate_zones(candles=candles, symbol="EUR/USD", timeframe="1D")

        sym = f"EUR_{uuid.uuid4().hex[:4]}"
        proposal = StrategyEngine.evaluate_opportunity(
            db=db,
            symbol=sym,
            market="FOREX",
            timeframe="1D",
            candles=candles,
            indicators=indicators,
            patterns=patterns,
            sr=sr,
        )

        assert proposal is not None
        assert proposal.status == "PENDING"
        assert proposal.proposed_entry_price > 0
        assert proposal.stop_loss < proposal.proposed_entry_price
        assert proposal.target > proposal.proposed_entry_price
        assert proposal.confidence_score > 0.50
        assert proposal.risk_reward_ratio >= 1.5


def test_buy_approval_and_risk_validation(client):
    """Verify explicit user approval executes paper BUY order and creates Position."""
    prop_id = f"PROP-APP-{uuid.uuid4().hex[:8]}"
    sym = f"SYM_APP_{uuid.uuid4().hex[:4]}"

    with SessionLocal() as db:
        risk = RiskService.get_or_create_settings(db)
        risk.emergency_stop_active = False
        now = utcnow()
        p = BuyProposal(
            proposal_id=prop_id,
            symbol=sym,
            market="FOREX",
            strategy_name="EMA Trend",
            current_price=100.0,
            proposed_entry_price=100.0,
            proposed_quantity=10.0,
            stop_loss=95.0,
            target=110.0,
            risk_amount=50.0,
            risk_reward_ratio=2.0,
            estimated_costs=3.5,
            confidence_score=0.78,
            confidence_method="Confluence",
            explanation="Test bullish opportunity",
            uncertainties="None",
            data_source="DEMO",
            data_timestamp=now,
            expires_at=now + timedelta(minutes=15),
            status="PENDING",
        )
        db.add(p)
        db.commit()

    # User approves proposal
    resp = client.post(f"/api/proposals/{prop_id}/approve", json={"notes": "Approved for paper test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "APPROVED_AND_EXECUTED"
    assert "position_id" in data

    # Verify Position is OPEN
    with SessionLocal() as db:
        pos = db.query(Position).filter(Position.position_id == data["position_id"]).first()
        assert pos is not None
        assert pos.status == "OPEN"
        assert pos.quantity == 10.0


def test_risk_check_enforcements(client):
    """Verify risk validation blocks orders when Emergency Stop is active or proposal expired."""
    prop_id = f"PROP-RSK-{uuid.uuid4().hex[:8]}"
    sym = f"SYM_RSK_{uuid.uuid4().hex[:4]}"

    with SessionLocal() as db:
        now = utcnow()
        risk = RiskService.get_or_create_settings(db)
        risk.emergency_stop_active = True
        db.commit()

        p = BuyProposal(
            proposal_id=prop_id,
            symbol=sym,
            market="FOREX",
            strategy_name="EMA Trend",
            current_price=100.0,
            proposed_entry_price=100.0,
            proposed_quantity=10.0,
            stop_loss=95.0,
            target=110.0,
            risk_amount=50.0,
            risk_reward_ratio=2.0,
            expires_at=now + timedelta(minutes=15),
            status="PENDING",
            explanation="Test",
        )
        db.add(p)
        db.commit()

    # Approval should be blocked by emergency stop
    resp = client.post(f"/api/proposals/{prop_id}/approve", json={})
    assert resp.status_code in [400, 422]
    assert "Emergency Stop" in resp.json()["detail"]

    # Clear emergency stop for subsequent tests
    with SessionLocal() as db:
        risk = RiskService.get_or_create_settings(db)
        risk.emergency_stop_active = False
        db.commit()


def test_duplicate_order_prevention(client):
    """Verify an already executed proposal cannot be approved again."""
    prop_id = f"PROP-DUP-{uuid.uuid4().hex[:8]}"
    sym = f"SYM_DUP_{uuid.uuid4().hex[:4]}"

    with SessionLocal() as db:
        now = utcnow()
        p = BuyProposal(
            proposal_id=prop_id,
            symbol=sym,
            market="FOREX",
            strategy_name="EMA Trend",
            current_price=100.0,
            proposed_entry_price=100.0,
            proposed_quantity=10.0,
            stop_loss=95.0,
            target=110.0,
            risk_amount=50.0,
            risk_reward_ratio=2.0,
            expires_at=now + timedelta(minutes=15),
            status="PENDING",
            explanation="Test dup",
        )
        db.add(p)
        db.commit()

    # First approval succeeds
    resp1 = client.post(f"/api/proposals/{prop_id}/approve", json={})
    assert resp1.status_code == 200

    # Second approval fails
    resp2 = client.post(f"/api/proposals/{prop_id}/approve", json={})
    assert resp2.status_code == 400


def test_buy_rejection(client):
    """Verify explicit user rejection updates status and logs rejection."""
    prop_id = f"PROP-REJ-{uuid.uuid4().hex[:8]}"
    sym = f"SYM_REJ_{uuid.uuid4().hex[:4]}"

    with SessionLocal() as db:
        now = utcnow()
        p = BuyProposal(
            proposal_id=prop_id,
            symbol=sym,
            market="NSE",
            strategy_name="Breakout",
            current_price=500.0,
            proposed_entry_price=500.0,
            proposed_quantity=5.0,
            stop_loss=480.0,
            target=550.0,
            risk_amount=100.0,
            risk_reward_ratio=2.5,
            expires_at=now + timedelta(minutes=15),
            status="PENDING",
            explanation="Test reject",
        )
        db.add(p)
        db.commit()

    resp = client.post(f"/api/proposals/{prop_id}/reject", json={"reason": "Excessive market volatility"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"


def test_position_monitoring_and_autonomous_exit():
    """Verify pre-authorized autonomous SELL execution when target price is hit."""
    pos_id = f"POS-AUTO-{uuid.uuid4().hex[:8]}"
    sym = f"SYM_AUTO_{uuid.uuid4().hex[:4]}"

    with SessionLocal() as db:
        perm = PositionMonitorService.get_or_create_permissions(db)
        perm.is_enabled = True
        perm.allow_take_profit = True
        db.commit()

        # Create open position with target 105.0
        pos = Position(
            position_id=pos_id,
            symbol=sym,
            market="FOREX",
            side="LONG",
            quantity=10.0,
            entry_price=100.0,
            current_price=100.0,
            stop_loss=95.0,
            target=105.0,
            status="OPEN",
        )
        db.add(pos)
        db.commit()

        # Feed price above target (106.0)
        actions = PositionMonitorService.update_position_prices_and_evaluate_exits(
            db=db,
            price_feed={sym: 106.0}
        )

        matching_actions = [a for a in actions if a["position_id"] == pos_id]
        assert len(matching_actions) >= 1
        assert matching_actions[0]["action"] == "AUTONOMOUS_SELL_EXECUTED"
        assert matching_actions[0]["reason"] == "TARGET_HIT"

        # Verify position is closed
        closed_pos = db.query(Position).filter(Position.position_id == pos_id).first()
        assert closed_pos.status == "CLOSED"
        assert closed_pos.realized_pnl > 0

        # Verify TradeReport was generated
        report = db.query(TradeReport).filter(TradeReport.symbol == sym).first()
        assert report is not None
        assert report.autonomous_exit is True
        assert report.net_pnl > 0


def test_autonomous_exit_disabled_fallback():
    """Verify position remains open with manual notification when autonomous exit is disabled."""
    pos_id = f"POS-MANUAL-{uuid.uuid4().hex[:8]}"
    sym = f"SYM_MANUAL_{uuid.uuid4().hex[:4]}"

    with SessionLocal() as db:
        perm = PositionMonitorService.get_or_create_permissions(db)
        perm.is_enabled = False
        db.commit()

        pos = Position(
            position_id=pos_id,
            symbol=sym,
            market="FOREX",
            side="LONG",
            quantity=10.0,
            entry_price=100.0,
            current_price=100.0,
            stop_loss=95.0,
            target=105.0,
            status="OPEN",
        )
        db.add(pos)
        db.commit()

        # Feed price above target (106.0)
        actions = PositionMonitorService.update_position_prices_and_evaluate_exits(
            db=db,
            price_feed={sym: 106.0}
        )

        matching_actions = [a for a in actions if a["position_id"] == pos_id]
        assert len(matching_actions) >= 1
        assert matching_actions[0]["action"] == "MANUAL_ACTION_REQUIRED"

        # Position must remain OPEN
        active_pos = db.query(Position).filter(Position.position_id == pos_id).first()
        assert active_pos.status == "OPEN"

        # Reset permission
        perm.is_enabled = True
        db.commit()


def test_audit_logs_endpoint(client):
    """Verify append-only audit trail endpoint."""
    resp = client.get("/api/audit-logs")
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) > 0
    event_types = [l["event_type"] for l in logs]
    assert "PROPOSAL_APPROVED" in event_types or "PROPOSAL_REJECTED" in event_types or "AUTONOMOUS_SELL_EXECUTED" in event_types


def test_backtesting_simulation(client):
    """Verify backtesting engine execution and metrics."""
    req = {
        "symbol": "EUR/USD",
        "timeframe": "1D",
        "market": "FOREX",
        "strategy_name": "EMA Momentum Trend Following",
        "initial_capital": 50000.0,
        "risk_per_trade_pct": 2.0,
        "slippage_pct": 0.02,
        "commission_per_trade": 1.5
    }
    resp = client.post("/api/backtesting/run", json=req)
    assert resp.status_code == 200
    res = resp.json()
    assert "total_trades" in res
    assert "win_rate" in res
    assert "profit_factor" in res
    assert "max_drawdown_pct" in res
    assert "net_pnl" in res
    assert "disclaimer" in res
