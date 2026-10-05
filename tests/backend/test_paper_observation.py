"""Paper Trading Observation Test Suite (Step 16).
Validates:
1. Safe observation mode without live broker side-effects
2. 9 canonical observation scenarios (Open, Intraday, High-Vol, Low-Liq, Close, No-Trade, Stale Data, Disconnection, Restart)
3. Execution realism (Slippage, Indian discount brokerage fees, STT, GST)
4. Audit trail logging of all observation events
5. Fail-closed live order shield active at all times
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
from app.services.observation_service import PaperObservationSuite
from app.models.entities import AuditLog

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_run_all_nine_observation_scenarios(db_session):
    """Verify executing all 9 canonical paper trading observation scenarios."""
    results = PaperObservationSuite.run_all_scenarios(db=db_session)
    assert len(results) == 9

    scenario_ids = [r.scenario_id for r in results]
    assert scenario_ids == [f"SCENARIO-0{i}" for i in range(1, 10)]

    for r in results:
        assert r.audit_event_logged is True
        assert r.state_preserved is True
        assert len(r.notes) > 10


def test_observation_market_open_and_warmup(db_session):
    """Verify Scenario 1: Market open price discovery requires indicator warmup."""
    res = PaperObservationSuite._scenario_market_open(db=db_session)
    assert res.market_condition == "OPENING_AUCTION"
    assert res.execution_status == "NO_ORDER_WARMUP"
    assert res.human_approval_required is False


def test_observation_normal_intraday_execution(db_session):
    """Verify Scenario 2: Normal intraday execution applies 2 bps slippage and brokerage."""
    res = PaperObservationSuite._scenario_normal_intraday(db=db_session)
    assert res.market_condition == "LIQUID_INTRADAY"
    assert res.human_approval_required is True
    assert res.execution_status == "PAPER_FILLED"
    assert res.slippage_bps == 2.0
    assert res.brokerage_fees_inr > 0.0


def test_observation_high_volatility_sizing_constraint(db_session):
    """Verify Scenario 3: High volatility scales slippage to 8 bps and constrains size."""
    res = PaperObservationSuite._scenario_high_volatility(db=db_session)
    assert res.market_condition == "HIGH_VOLATILITY"
    assert res.slippage_bps == 8.0
    assert res.risk_guardian_verdict == "SIZE_CONSTRAINED"


def test_observation_low_liquidity_rejection(db_session):
    """Verify Scenario 4: Wide spread / low liquidity leads to risk guardian rejection."""
    res = PaperObservationSuite._scenario_low_liquidity(db=db_session)
    assert res.risk_guardian_verdict == "REJECTED_WIDE_SPREAD"
    assert res.execution_status == "REJECTED_BY_RISK_GUARDIAN"


def test_observation_stale_data_fail_closed(db_session):
    """Verify Scenario 7: Stale data freezes signal evaluation safely."""
    res = PaperObservationSuite._scenario_stale_data(db=db_session)
    assert res.execution_status == "FROZEN_SAFE_STATE"
    assert res.risk_guardian_verdict == "FAIL_CLOSED_STALE"


def test_observation_broker_disconnection_shield(db_session):
    """Verify Scenario 8: Broker timeout keeps system fail-closed and live routes return 403."""
    res = PaperObservationSuite._scenario_broker_disconnection(db=db_session)
    assert res.execution_status == "FAIL_CLOSED_ACTIVE"

    # Verify live order endpoint remains fail-closed
    live_res = client.post("/api/broker/zerodha/orders", json={
        "symbol": "RELIANCE", "quantity": 1, "transaction_type": "BUY"
    })
    assert live_res.status_code == 403
    assert "Live broker order execution is strictly disabled" in live_res.json()["detail"]


def test_observation_audit_logging_and_rehydration(db_session):
    """Verify all observation events create immutable audit records in SQLite."""
    count_before = db_session.query(AuditLog).count()
    PaperObservationSuite.run_all_scenarios(db=db_session)
    count_after = db_session.query(AuditLog).count()
    assert count_after >= count_before + 9
