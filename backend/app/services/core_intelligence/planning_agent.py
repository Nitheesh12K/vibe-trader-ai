import time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import Strategy, RiskSettings, Position, utcnow
from app.schemas.intelligence import (
    PlanningOutput,
    PerceptionOutput,
    ReasoningOutput,
    MemoryContextOutput,
    AgentMetadata,
)
from app.services.risk_service import RiskService


class PlanningAgent:
    """Logical agent selecting validated strategies to synthesize structured trade plans."""

    NAME = "Planning Agent"
    VERSION = "1.0.0"

    @classmethod
    def plan(
        cls,
        db: Session,
        perception: PerceptionOutput,
        reasoning: ReasoningOutput,
        memory: MemoryContextOutput,
        ai_consolidated: Optional[Dict[str, Any]] = None,
    ) -> PlanningOutput:
        start_time = time.perf_counter()
        now = utcnow()

        # 1. Check if Reasoning determined trade is NOT viable
        if not reasoning.is_trade_viable:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            meta = AgentMetadata(
                name=cls.NAME,
                version=cls.VERSION,
                status="COMPLETED",
                execution_time_ms=round(elapsed_ms, 2),
                timestamp=now,
            )
            return PlanningOutput(
                agent=meta,
                strategy_name="None (Grounded in No-Trade Assessment)",
                strategy_version="1.0.0",
                decision="NO_TRADE",
                direction="NONE",
                contingency_conditions=["Maintain flat position until signal conflicts resolve."],
                explanation=f"No trade planned: Reasoning Agent reported non-viable setup ({reasoning.rationale}).",
                uncertainties=f"Uncertainty Score: {reasoning.uncertainty_score:.2f}",
                timestamp=now,
            )

        # 2. Query active validated strategies matching market
        active_strategies = (
            db.query(Strategy)
            .filter(
                Strategy.is_active == True,
                (Strategy.market == perception.market) | (Strategy.market == "ALL"),
            )
            .all()
        )

        if not active_strategies:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            meta = AgentMetadata(
                name=cls.NAME,
                version=cls.VERSION,
                status="BLOCKED",
                execution_time_ms=round(elapsed_ms, 2),
                timestamp=now,
                error_detail="No active validated strategy found matching market.",
            )
            return PlanningOutput(
                agent=meta,
                strategy_name="None",
                strategy_version="1.0.0",
                decision="NO_TRADE",
                direction="NONE",
                contingency_conditions=["Activate a validated strategy matching this market."],
                explanation=f"No trade planned: No active strategy configuration exists for {perception.market}.",
                uncertainties="Missing active strategy profile",
                timestamp=now,
            )

        selected_strategy = active_strategies[0]
        price = perception.current_price
        atr = perception.indicators.get("atr_14") or (price * 0.01)

        # Calculate Stop Loss and Target
        # Stop loss placed at 1.5 * ATR below current price or nearest support
        sl_distance = max(atr * 1.5, price * 0.005)
        stop_loss = round(price - sl_distance, 4)

        # Target placed for at least 2.0x Risk-Reward
        risk_per_unit = max(price - stop_loss, 0.0001)
        target = round(price + (risk_per_unit * 2.0), 4)
        rr_ratio = round((target - price) / risk_per_unit, 2)

        # Position Sizing based on Risk Settings
        risk_settings = RiskService.get_or_create_settings(db)
        account_balance = risk_settings.simulated_balance
        max_risk_pct = risk_settings.max_risk_per_trade_pct
        max_risk_dollars = account_balance * (max_risk_pct / 100.0)

        quantity = round(max_risk_dollars / risk_per_unit, 2)
        total_risk = round(quantity * risk_per_unit, 2)
        estimated_costs = round(quantity * price * 0.0003 + 2.0, 2)

        contingencies = [
            f"If price invalidates below stop loss ${stop_loss:.4f}, trigger immediate exit.",
            f"If profit target ${target:.4f} is hit, execute full take-profit liquidation.",
            "If market regime shifts to Bearish Downtrend before stop, evaluate early invalidation exit.",
        ]

        ai_thesis_note = f" AI Thesis: {ai_consolidated.get('planning_thesis')}" if (ai_consolidated and ai_consolidated.get("planning_thesis")) else ""
        explanation = (
            f"Validated Plan created via '{selected_strategy.name}'. "
            f"Entry: ${price:.4f} | SL: ${stop_loss:.4f} | TP: ${target:.4f} (R:R {rr_ratio}:1). "
            f"Position size: {quantity} units with estimated risk of ${total_risk:.2f} ({max_risk_pct}% of capital). "
            f"Aligned with {perception.regime} market structure.{ai_thesis_note}"
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        meta = AgentMetadata(
            name=cls.NAME,
            version=cls.VERSION,
            status="COMPLETED",
            execution_time_ms=round(elapsed_ms, 2),
            timestamp=now,
        )

        return PlanningOutput(
            agent=meta,
            strategy_name=selected_strategy.name,
            strategy_version="1.0.0",
            decision="TRADE_PLAN",
            direction="BUY",
            proposed_entry_price=price,
            stop_loss=stop_loss,
            target=target,
            risk_reward_ratio=rr_ratio,
            proposed_quantity=quantity,
            estimated_risk_amount=total_risk,
            estimated_costs=estimated_costs,
            contingency_conditions=contingencies,
            explanation=explanation,
            uncertainties="Plan subject to human authorization and independent Risk Guardian clearance.",
            timestamp=now,
        )
