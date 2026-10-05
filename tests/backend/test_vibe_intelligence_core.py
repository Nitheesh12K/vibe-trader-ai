"""Comprehensive automated test suite for Vibe Intelligence Core multi-agent architecture:
Perception, Reasoning, Memory, Learning, Planning, Risk Guardian, Trade Manager, Outcome Evaluator, and Strategy Adaptation Lifecycle.
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
    StrategyCandidate,
    Strategy,
    utcnow,
)
from app.services.core_intelligence.perception_agent import PerceptionAgent
from app.services.core_intelligence.reasoning_agent import ReasoningAgent
from app.services.core_intelligence.memory_agent import MemoryAgent
from app.services.core_intelligence.learning_agent import LearningAgent
from app.services.core_intelligence.planning_agent import PlanningAgent
from app.services.core_intelligence.risk_guardian_agent import RiskGuardianAgent
from app.services.core_intelligence.trade_manager_agent import AutonomousTradeManagerAgent
from app.services.core_intelligence.outcome_evaluator import OutcomeEvaluator
from app.services.core_intelligence.coordinator import VibeIntelligenceCore
from app.services.risk_service import RiskService


@pytest.fixture(scope="module")
def client():
    init_db()
    with SessionLocal() as db:
        risk = RiskService.get_or_create_settings(db)
        risk.emergency_stop_active = False
        risk.max_open_positions = 50
        db.query(Position).filter(Position.status == "OPEN").update({"status": "CLOSED"})
        db.commit()
    with TestClient(app) as c:
        yield c


def test_perception_agent_data_collection_and_freshness():
    """Verify Perception Agent collects real observations and computes regime deterministically."""
    with SessionLocal() as db:
        p = PerceptionAgent.perceive(db=db, symbol="EUR/USD", market="FOREX", timeframe="1D")
        assert p.agent.name == "Perception Agent"
        assert p.agent.status == "COMPLETED"
        assert p.candle_count >= 20
        assert p.current_price > 0.0
        assert not p.missing_data_detected
        assert p.regime in [
            "Bullish Momentum Trend",
            "Bearish Downtrend",
            "Consolidation / Low Volatility Squeeze",
            "Range-Bound Mean Reversion",
            "Range-Bound",
        ]
        assert "rsi_14" in p.indicators
        assert p.data_freshness_seconds >= 0.0


def test_reasoning_agent_confluence_and_conflict_detection():
    """Verify Reasoning Agent identifies conforming evidence and calculates uncertainty."""
    with SessionLocal() as db:
        p = PerceptionAgent.perceive(db=db, symbol="EUR/USD", market="FOREX", timeframe="1D")
        r = ReasoningAgent.evaluate(perception=p)

        assert r.agent.name == "Reasoning Agent"
        assert r.agent.status == "COMPLETED"
        assert isinstance(r.conforming_evidence, list)
        assert isinstance(r.conflicting_signals, list)
        assert 0.0 <= r.uncertainty_score <= 1.0
        assert len(r.rationale) > 10


def test_reasoning_agent_no_trade_on_missing_data():
    """Verify Reasoning Agent produces a deterministic No-Trade decision if perception has missing data."""
    with SessionLocal() as db:
        p = PerceptionAgent.perceive(db=db, symbol="EUR/USD", market="FOREX", timeframe="1D")
        # Simulate missing observation anomaly
        p.missing_data_detected = True
        r = ReasoningAgent.evaluate(perception=p)

        assert r.agent.status == "BLOCKED"
        assert r.is_trade_viable is False
        assert "No-trade" in r.rationale


def test_memory_agent_sqlite_recall():
    """Verify Memory Agent queries SQLite history without claiming guarantees."""
    with SessionLocal() as db:
        mem = MemoryAgent.recall(db=db, symbol="EUR/USD", regime="Bullish Momentum Trend")
        assert mem.agent.name == "Memory Agent"
        assert mem.agent.status == "COMPLETED"
        assert "DO NOT guarantee" in mem.disclaimer
        assert "total" in mem.past_proposals_summary


def test_learning_agent_metrics_and_deterioration_detection():
    """Verify Learning Agent quantifies expectancy, profit factor, drawdown, and decay alerts."""
    with SessionLocal() as db:
        learn = LearningAgent.evaluate_performance(db=db)
        assert learn.agent.name == "Learning Agent"
        assert learn.agent.status == "COMPLETED"
        assert learn.win_rate >= 0.0
        assert learn.profit_factor >= 0.0
        assert isinstance(learn.performance_deterioration_detected, bool)
        assert isinstance(learn.deterioration_reasons, list)


def test_planning_agent_strategy_selection_and_no_trade():
    """Verify Planning Agent generates structured plan or NO_TRADE."""
    with SessionLocal() as db:
        p = PerceptionAgent.perceive(db=db, symbol="EUR/USD", market="FOREX", timeframe="1D")
        r = ReasoningAgent.evaluate(perception=p)
        mem = MemoryAgent.recall(db=db, symbol="EUR/USD", regime=p.regime)

        # 1. When reasoning is viable
        plan = PlanningAgent.plan(db=db, perception=p, reasoning=r, memory=mem)
        assert plan.agent.name == "Planning Agent"
        assert plan.decision in ["TRADE_PLAN", "NO_TRADE"]

        # 2. When reasoning is NOT viable, plan MUST be NO_TRADE
        r_not_viable = ReasoningAgent.evaluate(perception=p)
        r_not_viable.is_trade_viable = False
        plan_no_trade = PlanningAgent.plan(db=db, perception=p, reasoning=r_not_viable, memory=mem)
        assert plan_no_trade.decision == "NO_TRADE"
        assert plan_no_trade.direction == "NONE"


def test_risk_guardian_deterministic_veto():
    """Verify Risk Guardian vetoes trade plan when emergency stop is active."""
    with SessionLocal() as db:
        risk = RiskService.get_or_create_settings(db)
        risk.emergency_stop_active = True
        db.commit()

        p = PerceptionAgent.perceive(db=db, symbol="EUR/USD", market="FOREX", timeframe="1D")
        r = ReasoningAgent.evaluate(perception=p)
        mem = MemoryAgent.recall(db=db, symbol="EUR/USD", regime=p.regime)
        plan = PlanningAgent.plan(db=db, perception=p, reasoning=r, memory=mem)
        plan.decision = "TRADE_PLAN"
        plan.estimated_risk_amount = 50.0

        guard = RiskGuardianAgent.validate_plan(db=db, plan=plan, symbol="EUR/USD", market="FOREX")
        assert guard.verdict == "REJECTED"
        assert any("Emergency Stop" in reason for reason in guard.blocking_reasons)

        # Clear emergency stop
        risk.emergency_stop_active = False
        db.commit()


def test_autonomous_trade_manager_execution():
    """Verify Trade Manager inspects open positions and executes autonomous exits under permission."""
    with SessionLocal() as db:
        # Create test position with stop-loss crossed
        pos_id = f"POS-TM-{uuid.uuid4().hex[:8]}"
        pos = Position(
            position_id=pos_id,
            symbol="EUR/USD",
            market="FOREX",
            side="LONG",
            quantity=100.0,
            entry_price=1.1000,
            current_price=1.0500,  # Below stop loss
            stop_loss=1.0700,
            target=1.1500,
            unrealized_pnl=-50.0,
            unrealized_pnl_pct=-4.5,
            status="OPEN",
        )
        db.add(pos)
        db.commit()

        tm_output = AutonomousTradeManagerAgent.inspect_and_manage(db=db)
        assert tm_output.agent.name == "Autonomous Trade Manager"
        assert tm_output.autonomous_exits_executed >= 1

        # Verify position was closed
        closed_pos = db.query(Position).filter(Position.position_id == pos_id).first()
        assert closed_pos.status == "CLOSED"
        assert "AUTONOMOUS_STOP_LOSS" in closed_pos.exit_reason


def test_outcome_evaluator_attribution():
    """Verify Outcome Evaluator computes entry/exit slippage and logs attribution."""
    with SessionLocal() as db:
        report = TradeReport(
            symbol="EUR/USD",
            market="FOREX",
            strategy_name="EMA Trend",
            side="LONG",
            quantity=10.0,
            entry_price=1.0850,
            exit_price=1.0950,
            entry_time=utcnow() - timedelta(hours=2),
            exit_time=utcnow(),
            gross_pnl=100.0,
            fees=2.0,
            slippage=1.5,
            net_pnl=96.5,
            roi_pct=8.9,
            exit_reason="TAKE_PROFIT",
            autonomous_exit=True,
            risk_check_passed=True,
            strategy_rationale="Confluence test",
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        outcome = OutcomeEvaluator.evaluate_trade_report(db=db, report_id=report.id)
        assert outcome is not None
        assert outcome.symbol == "EUR/USD"
        assert outcome.net_pnl == 96.5
        assert "Conforming" in outcome.realized_vs_expected_behavior


def test_strategy_adaptation_lifecycle_progression(client):
    """Verify Strategy Candidate lifecycle: Candidate -> Sandbox -> Backtested -> Review -> Activate."""
    cand_name = f"Test Adaptive EMA {uuid.uuid4().hex[:4]}"
    # 1. Propose candidate
    resp = client.post(
        "/api/intelligence/strategies/candidates",
        json={
            "name": cand_name,
            "version": "v1.2.0-rc1",
            "market": "FOREX",
            "timeframe": "1D",
            "parameters_json": '{"fast_ema": 15}',
            "rationale": "Proposed parameter optimization to capture early trends.",
        },
    )
    assert resp.status_code == 201
    cand = resp.json()
    assert cand["lifecycle_stage"] == "CANDIDATE"
    cand_id = cand["candidate_id"]

    # 2. Advance to Sandbox
    resp = client.post(
        f"/api/intelligence/strategies/candidates/{cand_id}/advance",
        json={"target_stage": "SANDBOX", "validation_notes": "Passed initial parameter stress check"},
    )
    assert resp.status_code == 200
    assert resp.json()["lifecycle_stage"] == "SANDBOX"

    # 3. Advance to Backtested
    resp = client.post(
        f"/api/intelligence/strategies/candidates/{cand_id}/advance",
        json={"target_stage": "BACKTESTED", "validation_notes": "Backtested across 2023-2024 demo data"},
    )
    assert resp.status_code == 200
    assert resp.json()["lifecycle_stage"] == "BACKTESTED"

    # 4. Explicit user activation
    resp = client.post(f"/api/intelligence/strategies/candidates/{cand_id}/activate")
    assert resp.status_code == 200
    assert resp.json()["lifecycle_stage"] == "ACTIVATED"
    assert resp.json()["is_active"] is True

    # Verify strategy was added to active Strategy table
    with SessionLocal() as db:
        active_strat = db.query(Strategy).filter(Strategy.name.like(f"%{cand_name}%")).first()
        assert active_strat is not None
        assert active_strat.is_active is True


def test_vibe_intelligence_core_api_endpoints(client):
    """Verify GET /api/intelligence/status and POST /api/intelligence/cycle endpoints."""
    # 1. Status endpoint
    resp = client.get("/api/intelligence/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "core_status" in data
    assert "agents" in data
    assert "perception" in data["agents"]
    assert "risk_guardian" in data["agents"]

    # 2. Multi-agent evaluation cycle
    resp = client.post("/api/intelligence/cycle?symbol=EUR/USD&market=FOREX&timeframe=1D")
    assert resp.status_code == 200
    cycle = resp.json()
    assert "cycle_id" in cycle
    assert cycle["symbol"] == "EUR/USD"
    assert "perception" in cycle
    assert "reasoning" in cycle
    assert "planning" in cycle
    assert "risk_guardian" in cycle
    assert cycle["overall_decision"] in ["BUY_PROPOSED", "NO_TRADE", "BLOCKED_BY_RISK"]
