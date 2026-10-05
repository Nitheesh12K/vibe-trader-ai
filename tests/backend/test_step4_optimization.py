"""Step 4 Optimization Tests: Verification of Agent Execution, Consolidated LLM Calling,
Conditional Agent Lifecycle, and Deterministic Code Boundaries.
"""
import uuid
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from app.database.session import SessionLocal
from app.models.entities import (
    Position,
    BuyProposal,
    TradeReport,
    StrategyCandidate,
    RiskSettings,
    AutonomousExitPermission,
    utcnow,
)
from app.services.core_intelligence.coordinator import VibeIntelligenceCore
from app.services.core_intelligence.perception_agent import PerceptionAgent
from app.services.core_intelligence.reasoning_agent import ReasoningAgent
from app.services.core_intelligence.memory_agent import MemoryAgent
from app.services.core_intelligence.planning_agent import PlanningAgent
from app.services.core_intelligence.risk_guardian_agent import RiskGuardianAgent
from app.services.core_intelligence.learning_agent import LearningAgent
from app.services.core_intelligence.trade_manager_agent import AutonomousTradeManagerAgent
from app.services.core_intelligence.outcome_evaluator import OutcomeEvaluator
from app.services.ai_provider import ai_service, AIAnalysisService
from app.services.risk_service import RiskService
from app.services.broker_adapter import paper_broker

client = TestClient(app)


def test_exactly_one_consolidated_llm_call_per_cycle():
    """Verify that exactly ONE consolidated LLM/AI call is made during run_cycle."""
    with SessionLocal() as db:
        # Clear positions to ensure clean state
        db.query(Position).delete()
        db.commit()

        # Spy on ai_service.analyze_consolidated_cycle
        with patch.object(
            ai_service,
            "analyze_consolidated_cycle",
            wraps=ai_service.analyze_consolidated_cycle,
        ) as mock_ai_call:
            res = VibeIntelligenceCore.run_cycle(
                db=db,
                symbol="EUR/USD",
                market="FOREX",
                timeframe="1D",
            )

            # Assert exactly 1 consolidated LLM call was executed
            assert mock_ai_call.call_count == 1

            # Assert response returns optimization metrics
            assert res.llm_calls_count == 1
            assert res.llm_provider_used in ["OLLAMA_ONLINE", "DETERMINISTIC_FALLBACK"]
            assert res.cycle_latency_ms is not None
            assert res.cycle_latency_ms > 0.0
            assert res.token_usage is not None
            assert res.token_usage.get("total_tokens", 0) > 0


def test_trade_manager_is_idle_when_no_open_positions():
    """Verify Trade Manager enters IDLE state with 0ms compute when no open positions exist."""
    with SessionLocal() as db:
        # Ensure 0 open positions
        db.query(Position).filter(Position.status == "OPEN").delete()
        db.commit()

        output = AutonomousTradeManagerAgent.inspect_and_manage(db=db)
        assert output.agent.status == "IDLE"
        assert output.agent.execution_time_ms == 0.0
        assert output.monitored_positions_count == 0
        assert output.exit_triggers_checked == 0
        assert output.autonomous_exits_executed == 0
        assert "IDLE" in output.status_message


def test_trade_manager_activates_only_when_open_position_present():
    """Verify Trade Manager transitions from IDLE to COMPLETED when open positions exist."""
    with SessionLocal() as db:
        pos_id = f"POS-OPT-{uuid.uuid4().hex[:6]}"
        now = utcnow()
        pos = Position(
            position_id=pos_id,
            symbol="EUR/USD",
            market="FOREX",
            side="LONG",
            quantity=100.0,
            entry_price=1.0800,
            current_price=1.0850,
            stop_loss=1.0700,
            target=1.1000,
            status="OPEN",
            created_at=now,
        )
        db.add(pos)
        db.commit()

        try:
            output = AutonomousTradeManagerAgent.inspect_and_manage(db=db)
            assert output.agent.status == "COMPLETED"
            assert output.monitored_positions_count >= 1
            assert output.exit_triggers_checked >= 1
            assert output.autonomous_exits_executed == 0  # not crossed
        finally:
            db.delete(pos)
            db.commit()


def test_learning_agent_event_caching_avoids_repeated_recalculation():
    """Verify Learning Agent returns cached output in 0.0ms when no new trade events occur."""
    with SessionLocal() as db:
        # First execution (computes or populates cache)
        initial = LearningAgent.evaluate_performance(db=db, force_refresh=True)
        assert initial.agent.status == "COMPLETED"

        # Second execution on subsequent cycle tick with no new trades
        cached = LearningAgent.evaluate_performance(db=db, force_refresh=False)
        assert cached.agent.status == "COMPLETED"
        assert cached.agent.execution_time_ms == 0.0
        assert cached.total_trades_analyzed == initial.total_trades_analyzed
        assert cached.win_rate == initial.win_rate


def test_deterministic_code_outside_llm():
    """Verify indicators, risk rules, sizing math, and broker execution remain deterministic outside LLM."""
    with SessionLocal() as db:
        risk_settings = RiskService.get_or_create_settings(db)
        sim_balance = risk_settings.simulated_balance
        max_risk_pct = risk_settings.max_risk_per_trade_pct

        # Deterministic position sizing check
        p = PerceptionAgent.perceive(db=db, symbol="EUR/USD", market="FOREX", timeframe="1D")
        r = ReasoningAgent.evaluate(perception=p)
        mem = MemoryAgent.recall(db=db, symbol=symbol if (symbol := "EUR/USD") else "EUR/USD", regime=p.regime)
        plan = PlanningAgent.plan(db=db, perception=p, reasoning=r, memory=mem)

        if plan.decision == "TRADE_PLAN":
            # Check deterministic ATR stop loss & sizing formula:
            expected_max_risk = sim_balance * (max_risk_pct / 100.0)
            risk_per_unit = max(plan.proposed_entry_price - plan.stop_loss, 0.0001)
            expected_quantity = round(expected_max_risk / risk_per_unit, 2)
            assert abs(plan.proposed_quantity - expected_quantity) <= 0.05

            # Risk Guardian deterministic enforcement
            guard = RiskGuardianAgent.validate_plan(db=db, plan=plan, symbol="EUR/USD", market="FOREX")
            assert guard.veto_power_active is True
            assert isinstance(guard.checks_summary, dict)
            assert "emergency_stop_clear" in guard.checks_summary
            assert "daily_loss_ok" in guard.checks_summary
            assert "open_positions_cap_ok" in guard.checks_summary


def test_trace_one_complete_cycle_end_to_end():
    """
    Trace ONE complete pipeline cycle:
    Market Data -> Indicators -> Strategy -> Perception -> Memory -> Consolidated LLM -> Reasoning -> Planning -> Risk Guardian -> User Approval -> Paper Execution
    """
    with SessionLocal() as db:
        # Reset any blocking state
        risk_settings = RiskService.get_or_create_settings(db)
        risk_settings.emergency_stop_active = False
        db.commit()

        # Step 1: Run cycle with 1 consolidated LLM call
        cycle_res = VibeIntelligenceCore.run_cycle(
            db=db,
            symbol="EUR/USD",
            market="FOREX",
            timeframe="1D",
        )

        assert cycle_res.llm_calls_count == 1
        assert cycle_res.overall_decision in ["BUY_PROPOSED", "NO_TRADE", "BLOCKED_BY_RISK"]
        assert len(cycle_res.agent_states) == 7

        # Step 2: If BUY_PROPOSED, test human user approval gate
        if cycle_res.overall_decision == "BUY_PROPOSED":
            proposal = (
                db.query(BuyProposal)
                .filter(BuyProposal.symbol == "EUR/USD", BuyProposal.status == "PENDING")
                .order_by(BuyProposal.id.desc())
                .first()
            )
            assert proposal is not None
            assert proposal.status == "PENDING"

            # Execute explicit human approval
            resp = client.post(
                f"/api/proposals/{proposal.proposal_id}/approve",
                json={"expected_version": proposal.version, "notes": "Step 4 E2E Test Approval"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "APPROVED_AND_EXECUTED"

            # Verify paper position was opened
            pos = db.query(Position).filter(Position.position_id == data["position_id"]).first()
            assert pos is not None
            assert pos.status == "OPEN"

            # Clean up test position
            db.delete(pos)
            db.commit()


def test_api_cycle_endpoint_returns_optimization_metrics():
    """Verify POST /api/intelligence/cycle returns consolidated LLM metrics."""
    resp = client.post(
        "/api/intelligence/cycle",
        params={"symbol": "EUR/USD", "market": "FOREX", "timeframe": "1D"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["llm_calls_count"] == 1
    assert "cycle_latency_ms" in data
    assert data["cycle_latency_ms"] > 0
    assert "token_usage" in data
    assert "total_tokens" in data["token_usage"]
    assert data["token_usage"]["total_tokens"] > 0
    assert data["llm_provider_used"] in ["OLLAMA_ONLINE", "DETERMINISTIC_FALLBACK"]
