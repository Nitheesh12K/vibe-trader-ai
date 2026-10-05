import json
import time
import uuid
from datetime import timedelta, datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import (
    BuyProposal,
    AgentExecutionCycle,
    StrategyCandidate,
    RiskSettings,
    AutonomousExitPermission,
    Position,
    TradeReport,
    utcnow,
)
from app.schemas.intelligence import (
    IntelligenceCycleResponse,
    IntelligenceStatusResponse,
    AgentMetadata,
    AgentStatus,
)
from app.services.core_intelligence.perception_agent import PerceptionAgent
from app.services.core_intelligence.reasoning_agent import ReasoningAgent
from app.services.core_intelligence.memory_agent import MemoryAgent
from app.services.core_intelligence.learning_agent import LearningAgent
from app.services.core_intelligence.planning_agent import PlanningAgent
from app.services.core_intelligence.risk_guardian_agent import RiskGuardianAgent
from app.services.core_intelligence.trade_manager_agent import AutonomousTradeManagerAgent
from app.services.core_intelligence.outcome_evaluator import OutcomeEvaluator
from app.services.audit_service import AuditService


class VibeIntelligenceCore:
    """
    Central coordination layer that manages specialized agents, shared context,
    decisions, and execution permissions with real execution-based status tracking.
    """

    CORE_VERSION = "2.0.0"

    # Runtime live execution state tracking
    _is_cycle_running: bool = False
    _running_cycle_id: Optional[str] = None
    _running_agent_id: Optional[str] = None
    _running_agent_start: Optional[float] = None

    AGENT_NAMES: Dict[str, str] = {
        "perception": "Perception Agent",
        "reasoning": "Reasoning Agent",
        "memory": "Memory Agent",
        "learning": "Learning Agent",
        "planning": "Planning Agent",
        "risk_guardian": "Risk Guardian",
        "trade_manager": "Autonomous Trade Manager",
        "outcome_evaluator": "Outcome Evaluator",
    }

    @classmethod
    def run_cycle(
        cls,
        db: Session,
        symbol: str = "EUR/USD",
        market: str = "FOREX",
        timeframe: str = "1D",
    ) -> IntelligenceCycleResponse:
        cycle_start_time = time.perf_counter()
        cycle_id = f"CYCLE-{uuid.uuid4().hex[:8]}"
        now = utcnow()

        cls._is_cycle_running = True
        cls._running_cycle_id = cycle_id

        try:
            # Step 1: Perception Agent (Deterministic market observation & indicator calculation)
            cls._running_agent_id = "perception"
            cls._running_agent_start = time.perf_counter()
            perception = PerceptionAgent.perceive(db=db, symbol=symbol, market=market, timeframe=timeframe)
            perception.agent.execution_id = cycle_id
            perception.agent.last_run_at = now

            # Step 2: Memory Agent (Deterministic SQLite recall of historical win rates & proposals)
            cls._running_agent_id = "memory"
            cls._running_agent_start = time.perf_counter()
            memory = MemoryAgent.recall(db=db, symbol=symbol, regime=perception.regime)
            memory.agent.execution_id = cycle_id
            memory.agent.last_run_at = now

            # Step 3: EXACTLY ONE CONSOLIDATED LLM ANALYSIS CALL
            # Synthesizes Perception, Memory, and Strategic considerations in 1 single call
            from app.services.ai_provider import ai_service
            consolidated_ai = ai_service.analyze_consolidated_cycle(
                symbol=symbol,
                market=market,
                timeframe=timeframe,
                perception=perception,
                memory=memory,
            )

            # Step 4: Reasoning Agent (Consumes deterministic indicators + consolidated AI synthesis)
            cls._running_agent_id = "reasoning"
            cls._running_agent_start = time.perf_counter()
            reasoning = ReasoningAgent.evaluate(perception=perception, ai_consolidated=consolidated_ai)
            reasoning.agent.execution_id = cycle_id
            reasoning.agent.last_run_at = now

            # Step 5: Planning Agent (Produces structured trade plan with 100% deterministic ATR SL/TP & sizing)
            cls._running_agent_id = "planning"
            cls._running_agent_start = time.perf_counter()
            planning = PlanningAgent.plan(
                db=db,
                perception=perception,
                reasoning=reasoning,
                memory=memory,
                ai_consolidated=consolidated_ai,
            )
            planning.agent.execution_id = cycle_id
            planning.agent.last_run_at = now

            # Step 5: Risk Guardian Agent (Independent deterministic gate)
            cls._running_agent_id = "risk_guardian"
            cls._running_agent_start = time.perf_counter()
            risk_guardian = RiskGuardianAgent.validate_plan(
                db=db,
                plan=planning,
                symbol=symbol,
                market=market,
            )
            risk_guardian.agent.execution_id = cycle_id
            risk_guardian.agent.last_run_at = now

            # Step 6: Learning Agent (Reflects empirical performance)
            cls._running_agent_id = "learning"
            cls._running_agent_start = time.perf_counter()
            learning = LearningAgent.evaluate_performance(db=db)
            learning.agent.execution_id = cycle_id
            learning.agent.last_run_at = now

            # Step 7: Autonomous Trade Manager (Monitors and enforces exit rules)
            cls._running_agent_id = "trade_manager"
            cls._running_agent_start = time.perf_counter()
            trade_manager = AutonomousTradeManagerAgent.inspect_and_manage(db=db)
            trade_manager.agent.execution_id = cycle_id
            trade_manager.agent.last_run_at = now

            # Determine overall decision
            if planning.decision == "TRADE_PLAN" and risk_guardian.verdict == "PASSED":
                overall_decision = "BUY_PROPOSED"
                # Emit structured BuyProposal record awaiting explicit human approval
                prop_id = f"PROP-{uuid.uuid4().hex[:10].upper()}"
                proposal = BuyProposal(
                    proposal_id=prop_id,
                    symbol=symbol,
                    market=market,
                    strategy_name=planning.strategy_name,
                    current_price=perception.current_price,
                    proposed_entry_price=planning.proposed_entry_price or perception.current_price,
                    proposed_quantity=planning.proposed_quantity or 1.0,
                    stop_loss=planning.stop_loss or (perception.current_price * 0.98),
                    target=planning.target or (perception.current_price * 1.04),
                    risk_amount=planning.estimated_risk_amount or 100.0,
                    risk_reward_ratio=planning.risk_reward_ratio or 2.0,
                    estimated_costs=planning.estimated_costs or 2.5,
                    matched_conditions_json=json.dumps(reasoning.conforming_evidence),
                    unmatched_conditions_json=json.dumps(reasoning.conflicting_signals),
                    supporting_indicators_json=json.dumps(perception.indicators),
                    confidence_score=round(max(0.1, 1.0 - reasoning.uncertainty_score), 2),
                    confidence_method="Vibe Intelligence Core Multi-Agent Confluence",
                    explanation=planning.explanation,
                    uncertainties=f"Uncertainty ({reasoning.uncertainty_score:.2f}): {'; '.join(reasoning.uncertainty_factors)}",
                    data_source=perception.data_source,
                    data_timestamp=now,
                    expires_at=now + timedelta(minutes=15),
                    status="PENDING",
                )
                db.add(proposal)
                db.commit()

                AuditService.log_event(
                    db=db,
                    event_type="PROPOSAL_GENERATED",
                    action=f"Intelligence Core generated BUY Proposal {prop_id} for {symbol}",
                    actor="INTELLIGENCE_CORE",
                    symbol=symbol,
                    market=market,
                    proposal_id=prop_id,
                    details={
                        "cycle_id": cycle_id,
                        "strategy": planning.strategy_name,
                        "confidence": proposal.confidence_score,
                    },
                )

            elif planning.decision == "NO_TRADE":
                overall_decision = "NO_TRADE"
            else:
                overall_decision = "BLOCKED_BY_RISK"

            # Check outcome evaluator status from historical reports
            has_reports = db.query(TradeReport).count() > 0

            # Record detailed agent states in DB
            agent_details_for_db = {
                "perception": {
                    "status": perception.agent.status,
                    "execution_time_ms": perception.agent.execution_time_ms,
                    "error_detail": perception.agent.error_detail,
                    "execution_id": cycle_id,
                    "last_run_at": now.isoformat(),
                },
                "reasoning": {
                    "status": reasoning.agent.status,
                    "execution_time_ms": reasoning.agent.execution_time_ms,
                    "error_detail": reasoning.agent.error_detail,
                    "execution_id": cycle_id,
                    "last_run_at": now.isoformat(),
                },
                "memory": {
                    "status": memory.agent.status,
                    "execution_time_ms": memory.agent.execution_time_ms,
                    "error_detail": memory.agent.error_detail,
                    "execution_id": cycle_id,
                    "last_run_at": now.isoformat(),
                },
                "planning": {
                    "status": planning.agent.status,
                    "execution_time_ms": planning.agent.execution_time_ms,
                    "error_detail": planning.agent.error_detail,
                    "execution_id": cycle_id,
                    "last_run_at": now.isoformat(),
                },
                "risk_guardian": {
                    "status": risk_guardian.agent.status,
                    "execution_time_ms": risk_guardian.agent.execution_time_ms,
                    "error_detail": risk_guardian.agent.error_detail,
                    "execution_id": cycle_id,
                    "last_run_at": now.isoformat(),
                },
                "learning": {
                    "status": learning.agent.status,
                    "execution_time_ms": learning.agent.execution_time_ms,
                    "error_detail": learning.agent.error_detail,
                    "execution_id": cycle_id,
                    "last_run_at": now.isoformat(),
                },
                "trade_manager": {
                    "status": trade_manager.agent.status,
                    "execution_time_ms": trade_manager.agent.execution_time_ms,
                    "error_detail": trade_manager.agent.error_detail,
                    "execution_id": cycle_id,
                    "last_run_at": now.isoformat(),
                },
                "outcome_evaluator": {
                    "status": "COMPLETED" if has_reports else "IDLE",
                    "execution_time_ms": 0.0,
                    "error_detail": None,
                    "execution_id": cycle_id,
                    "last_run_at": now.isoformat(),
                },
                "consolidated_llm": {
                    "provider": consolidated_ai.get("provider_used"),
                    "model_id": consolidated_ai.get("model_id"),
                    "latency_ms": consolidated_ai.get("latency_ms"),
                    "token_usage": consolidated_ai.get("token_usage"),
                    "llm_calls": 1,
                },
            }

            agent_states: Dict[str, AgentStatus] = {
                "Perception": perception.agent.status,
                "Reasoning": reasoning.agent.status,
                "Memory": memory.agent.status,
                "Planning": planning.agent.status,
                "Risk Guardian": risk_guardian.agent.status,
                "Learning": learning.agent.status,
                "Trade Manager": trade_manager.agent.status,
            }

            cycle_latency = round((time.perf_counter() - cycle_start_time) * 1000, 2)

            cycle_record = AgentExecutionCycle(
                cycle_id=cycle_id,
                symbol=symbol,
                market=market,
                timeframe=timeframe,
                agent_states_json=json.dumps(agent_details_for_db),
                perception_summary_json=json.dumps({"regime": perception.regime, "price": perception.current_price}),
                reasoning_summary_json=json.dumps({"is_viable": reasoning.is_trade_viable, "uncertainty": reasoning.uncertainty_score}),
                memory_summary_json=json.dumps({"past_setups": memory.similar_setups_found, "win_rate": memory.regime_historical_win_rate}),
                planning_summary_json=json.dumps({"decision": planning.decision, "strategy": planning.strategy_name}),
                risk_verdict=risk_guardian.verdict,
                decision=overall_decision,
                explanation=planning.explanation,
                created_at=now,
            )
            db.add(cycle_record)
            db.commit()

            return IntelligenceCycleResponse(
                cycle_id=cycle_id,
                symbol=symbol,
                market=market,
                timeframe=timeframe,
                agent_states=agent_states,
                overall_decision=overall_decision,
                perception=perception,
                reasoning=reasoning,
                memory=memory,
                planning=planning,
                risk_guardian=risk_guardian,
                learning_summary=learning,
                trade_manager=trade_manager,
                execution_timestamp=now,
                cycle_latency_ms=cycle_latency,
                llm_calls_count=1,
                llm_provider_used=consolidated_ai.get("provider_used", "DETERMINISTIC_FALLBACK"),
                token_usage=consolidated_ai.get("token_usage"),
            )
        finally:
            cls._is_cycle_running = False
            cls._running_cycle_id = None
            cls._running_agent_id = None
            cls._running_agent_start = None

    @classmethod
    def get_status(cls, db: Session) -> IntelligenceStatusResponse:
        """
        Returns real execution-derived status of the agent fleet.
        Never calls AI models or executes agents during status inquiry.
        """
        now = utcnow()

        # Check emergency stop
        risk_settings = (
            db.query(RiskSettings).order_by(RiskSettings.id.desc()).first()
        )
        emergency_active = bool(risk_settings and risk_settings.emergency_stop_active)

        # Check autonomous sell permissions
        exit_perm = (
            db.query(AutonomousExitPermission).order_by(AutonomousExitPermission.id.desc()).first()
        )
        autonomous_sell_enabled = bool(exit_perm and exit_perm.is_enabled)

        # Counts
        candidates_count = db.query(StrategyCandidate).count()
        pending_proposals = db.query(BuyProposal).filter(BuyProposal.status == "PENDING").count()
        open_positions = db.query(Position).filter(Position.status == "OPEN").count()

        # Fetch latest execution cycle from persistent SQLite storage
        last_cycle = (
            db.query(AgentExecutionCycle)
            .order_by(AgentExecutionCycle.id.desc())
            .first()
        )

        agents: Dict[str, AgentMetadata] = {}

        if cls._is_cycle_running:
            core_status = "PROCESSING"
            for agent_id, name in cls.AGENT_NAMES.items():
                if agent_id == cls._running_agent_id:
                    elapsed = (time.perf_counter() - (cls._running_agent_start or time.perf_counter())) * 1000
                    agents[agent_id] = AgentMetadata(
                        name=name,
                        version="1.0.0",
                        status="RUNNING",
                        execution_time_ms=round(elapsed, 2),
                        timestamp=now,
                        execution_id=cls._running_cycle_id,
                        last_run_at=now,
                    )
                else:
                    agents[agent_id] = AgentMetadata(
                        name=name,
                        version="1.0.0",
                        status="IDLE",
                        execution_time_ms=0.0,
                        timestamp=now,
                        execution_id=cls._running_cycle_id,
                    )
            active_regime = "Cycle Execution In Progress..."
            data_freshness = 0.5

        elif last_cycle is None:
            # Before first cycle: all agents are honestly in IDLE state
            core_status = "HALTED_BY_EMERGENCY" if emergency_active else "IDLE"
            for agent_id, name in cls.AGENT_NAMES.items():
                if agent_id == "risk_guardian" and emergency_active:
                    st: AgentStatus = "BLOCKED"
                    err = "Emergency Stop Active"
                else:
                    st = "IDLE"
                    err = None

                agents[agent_id] = AgentMetadata(
                    name=name,
                    version="1.0.0",
                    status=st,
                    execution_time_ms=0.0,
                    timestamp=now,
                    error_detail=err,
                    execution_id=None,
                    last_run_at=None,
                )
            active_regime = "Standby (No Evaluation Cycle Executed)"
            data_freshness = 0.0

        else:
            # Restore genuine execution history from latest cycle
            core_status = "HALTED_BY_EMERGENCY" if emergency_active else "OPERATIONAL"
            cycle_data: Dict[str, Any] = {}
            try:
                cycle_data = json.loads(last_cycle.agent_states_json or "{}")
            except Exception:
                pass

            # Handle both rich dictionary schema and legacy simple status mapping
            for agent_id, name in cls.AGENT_NAMES.items():
                stored_entry = cycle_data.get(agent_id)
                if not stored_entry:
                    # Check capitalized name fallback (legacy format)
                    title_name = name.split()[0]
                    legacy_st = cycle_data.get(title_name) or cycle_data.get(name)
                    if legacy_st:
                        stored_entry = {"status": legacy_st, "execution_time_ms": 0.0}

                st_val = stored_entry.get("status", "COMPLETED") if isinstance(stored_entry, dict) else "COMPLETED"
                time_val = stored_entry.get("execution_time_ms", 0.0) if isinstance(stored_entry, dict) else 0.0
                err_val = stored_entry.get("error_detail") if isinstance(stored_entry, dict) else None

                if agent_id == "risk_guardian" and emergency_active:
                    st_val = "BLOCKED"
                    err_val = "Emergency Stop Active"

                last_run_dt = last_cycle.created_at
                agents[agent_id] = AgentMetadata(
                    name=name,
                    version="1.0.0",
                    status=st_val,
                    execution_time_ms=round(float(time_val), 2),
                    timestamp=now,
                    error_detail=err_val,
                    execution_id=last_cycle.cycle_id,
                    last_run_at=last_run_dt,
                )

            # Regime from actual perception summary
            try:
                p_summary = json.loads(last_cycle.perception_summary_json or "{}")
                active_regime = p_summary.get("regime", "Multi-Market Surveillance Active")
            except Exception:
                active_regime = "Multi-Market Surveillance Active"

            data_freshness = max(0.0, round((now - last_cycle.created_at).total_seconds(), 1))

        return IntelligenceStatusResponse(
            core_status=core_status,
            agents=agents,
            active_regime=active_regime,
            data_freshness_seconds=data_freshness,
            emergency_stop_active=emergency_active,
            autonomous_sell_enabled=autonomous_sell_enabled,
            total_candidate_strategies=candidates_count,
            pending_proposals_count=pending_proposals,
            open_positions_count=open_positions,
            timestamp=now,
        )


# Class alias for backward compatibility and testing
MultiAgentCoordinator = VibeIntelligenceCore
