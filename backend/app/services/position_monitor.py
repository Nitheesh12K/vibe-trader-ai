"""Background Open Position Monitoring & Pre-Authorized Autonomous SELL Engine."""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import (
    Position,
    AutonomousExitPermission,
    BuyProposal,
    PaperTrade,
    TradeReport,
    utcnow,
)
from app.services.broker_adapter import paper_broker
from app.services.audit_service import AuditService

logger = logging.getLogger("vibe-trader-ai.position_monitor")


class PositionMonitorService:
    @staticmethod
    def get_or_create_permissions(db: Session) -> AutonomousExitPermission:
        perm = db.query(AutonomousExitPermission).first()
        if not perm:
            perm = AutonomousExitPermission(
                is_enabled=True,
                allow_stop_loss=True,
                allow_take_profit=True,
                allow_strategy_exit=True,
                allow_max_drawdown=True,
                max_position_scope="ALL",
                emergency_risk_limit_pct=5.0,
            )
            db.add(perm)
            db.commit()
            db.refresh(perm)
        return perm

    @classmethod
    def update_position_prices_and_evaluate_exits(
        cls,
        db: Session,
        price_feed: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Scans all open positions, updates current prices and unrealized P&L,
        and triggers autonomous SELL exits if pre-authorized conditions are met.
        """
        open_positions = db.query(Position).filter(Position.status == "OPEN").all()
        permission = cls.get_or_create_permissions(db)
        actions_taken: List[Dict[str, Any]] = []

        for pos in open_positions:
            current_price = price_feed.get(pos.symbol)
            if not current_price or current_price <= 0:
                continue

            # Update position tracking metrics
            pos.current_price = current_price
            gross_unrealized = (current_price - pos.entry_price) * pos.quantity
            pos.unrealized_pnl = round(gross_unrealized, 2)
            cost_basis = pos.entry_price * pos.quantity
            pos.unrealized_pnl_pct = round((gross_unrealized / max(0.01, cost_basis)) * 100, 2)

            if pos.highest_price is None or current_price > pos.highest_price:
                pos.highest_price = current_price

            # Evaluate Exit Conditions
            exit_trigger: Optional[str] = None
            if current_price >= pos.target:
                exit_trigger = "TARGET_HIT"
            elif current_price <= pos.stop_loss:
                exit_trigger = "STOP_LOSS_HIT"
            elif pos.unrealized_pnl_pct <= -abs(permission.emergency_risk_limit_pct):
                exit_trigger = "EMERGENCY_RISK_LIMIT"

            if exit_trigger:
                # Check whether Autonomous Exit Permission is active and covers this condition
                is_pre_authorized = False
                if permission.is_enabled:
                    if exit_trigger == "TARGET_HIT" and permission.allow_take_profit:
                        is_pre_authorized = True
                    elif exit_trigger == "STOP_LOSS_HIT" and permission.allow_stop_loss:
                        is_pre_authorized = True
                    elif exit_trigger == "EMERGENCY_RISK_LIMIT" and permission.allow_max_drawdown:
                        is_pre_authorized = True

                if is_pre_authorized:
                    logger.info(f"Pre-authorized Autonomous SELL triggered for Position {pos.position_id} ({pos.symbol}) — Reason: {exit_trigger}")
                    report = cls._close_position_internal(
                        db=db,
                        position=pos,
                        exit_price=current_price,
                        exit_reason=exit_trigger,
                        is_autonomous=True,
                    )
                    actions_taken.append({
                        "position_id": pos.position_id,
                        "action": "AUTONOMOUS_SELL_EXECUTED",
                        "reason": exit_trigger,
                        "net_pnl": report.net_pnl,
                    })
                else:
                    # Autonomous permission disabled: Flag notification without automatic execution
                    logger.info(f"Exit condition {exit_trigger} met for Position {pos.position_id}, but autonomous permission disabled. Manual action required.")
                    AuditService.log_event(
                        db=db,
                        event_type="EXIT_TRIGGERED_MANUAL_REQUIRED",
                        action=f"Exit trigger {exit_trigger} reached for Position {pos.position_id}. Autonomous permission disabled.",
                        actor="POSITION_MONITOR",
                        symbol=pos.symbol,
                        market=pos.market,
                        position_id=pos.position_id,
                        details={"trigger": exit_trigger, "current_price": current_price, "target": pos.target, "stop_loss": pos.stop_loss},
                    )
                    actions_taken.append({
                        "position_id": pos.position_id,
                        "action": "MANUAL_ACTION_REQUIRED",
                        "reason": exit_trigger,
                    })

        db.commit()
        return actions_taken

    @classmethod
    def close_position(
        cls,
        db: Session,
        position_id: str,
        exit_price: Optional[float] = None,
        reason: str = "AUTONOMOUS_EXIT",
        autonomous_exit: bool = True,
    ) -> TradeReport:
        """Closes an open position with specified reason and autonomy flag."""
        pos = db.query(Position).filter(Position.position_id == position_id, Position.status == "OPEN").first()
        if not pos:
            raise ValueError(f"Open position with ID {position_id} not found.")

        price = exit_price or pos.current_price
        return cls._close_position_internal(
            db=db,
            position=pos,
            exit_price=price,
            exit_reason=reason,
            is_autonomous=autonomous_exit,
        )

    @classmethod
    def close_position_manually(
        cls,
        db: Session,
        position_id: str,
        exit_price_override: Optional[float] = None,
        reason: str = "MANUAL_CLOSE"
    ) -> TradeReport:
        """Explicitly closes an active position upon user command."""
        pos = db.query(Position).filter(Position.position_id == position_id, Position.status == "OPEN").first()
        if not pos:
            raise ValueError(f"Open position with ID {position_id} not found.")

        price = exit_price_override or pos.current_price
        return cls._close_position_internal(
            db=db,
            position=pos,
            exit_price=price,
            exit_reason=reason,
            is_autonomous=False,
        )

    @classmethod
    def _close_position_internal(
        cls,
        db: Session,
        position: Position,
        exit_price: float,
        exit_reason: str,
        is_autonomous: bool,
    ) -> TradeReport:
        """Internal execution of SELL order and generation of comprehensive TradeReport."""
        # Atomic transition to CLOSING to prevent concurrent double-close
        updated = db.query(Position).filter(
            Position.id == position.id,
            Position.status == "OPEN"
        ).update({"status": "CLOSING"}, synchronize_session="fetch")
        db.commit()

        if updated == 0:
            existing_report = db.query(TradeReport).filter(TradeReport.position_id == position.id).first()
            if existing_report:
                return existing_report
            raise ValueError(f"Position {position.position_id} is already being closed or already closed.")

        # Submit paper SELL order
        sell_fill = paper_broker.submit_sell_order(
            symbol=position.symbol,
            market=position.market,
            quantity=position.quantity,
            price=exit_price,
            reason=exit_reason,
        )

        if sell_fill.get("status") in ["FAILED", "REJECTED", "CANCELLED"]:
            position.status = "OPEN"
            db.commit()
            logger.error(f"Paper broker exit order failed for Position {position.position_id}: {sell_fill.get('reason')}")
            AuditService.log_event(
                db=db,
                event_type="EXIT_ORDER_FAILED",
                action=f"Failed to execute exit order for Position {position.position_id}: {sell_fill.get('reason')}",
                actor="PAPER_BROKER",
                symbol=position.symbol,
                market=position.market,
                position_id=position.position_id,
                details=sell_fill,
            )
            raise RuntimeError(f"Paper exit order failed ({sell_fill.get('status')}): {sell_fill.get('reason')}")

        fill_price = sell_fill["fill_price"]
        fees = sell_fill["fees"]
        slippage = sell_fill["slippage"]

        # Calculate P&L metrics
        gross_pnl = round((fill_price - position.entry_price) * position.quantity, 2)
        net_pnl = round(gross_pnl - fees, 2)
        cost_basis = position.entry_price * position.quantity
        roi_pct = round((net_pnl / max(0.01, cost_basis)) * 100, 2)

        # Update position record
        now = utcnow()
        position.status = "CLOSED"
        position.exit_price = fill_price
        position.realized_pnl = net_pnl
        position.exit_reason = exit_reason
        position.exit_timestamp = now
        position.current_price = fill_price

        # Retrieve related proposal for attribution
        proposal = db.query(BuyProposal).filter(BuyProposal.id == position.proposal_id).first() if position.proposal_id else None
        strat_name = proposal.strategy_name if proposal else "Manual / Discretionary"
        approval_time = proposal.updated_at if proposal else None
        rationale = proposal.explanation if proposal else "Direct execution"

        # Generate Comprehensive TradeReport
        report = TradeReport(
            position_id=position.id,
            proposal_id=position.proposal_id,
            symbol=position.symbol,
            market=position.market,
            strategy_name=strat_name,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=fill_price,
            entry_time=position.created_at,
            exit_time=now,
            gross_pnl=gross_pnl,
            fees=fees,
            slippage=slippage,
            net_pnl=net_pnl,
            roi_pct=roi_pct,
            exit_reason=exit_reason,
            autonomous_exit=is_autonomous,
            buy_approval_timestamp=approval_time,
            risk_check_passed=True,
            strategy_rationale=rationale,
            data_source="DEMO_DATA (Simulated)",
            created_at=now,
        )
        db.add(report)

        # Close matching paper trade if exists
        matching_trade = db.query(PaperTrade).filter(
            PaperTrade.symbol == position.symbol,
            PaperTrade.status == "Open"
        ).first()
        if matching_trade:
            matching_trade.status = "Closed"
            matching_trade.exit_price = fill_price
            matching_trade.pnl = net_pnl
            matching_trade.closed_at = now

        # Update simulated portfolio balance in RiskSettings
        from app.models.entities import RiskSettings
        risk_settings = db.query(RiskSettings).first()
        if risk_settings:
            risk_settings.simulated_balance = round(risk_settings.simulated_balance + net_pnl, 2)

        db.commit()
        db.refresh(report)

        # Audit Event
        AuditService.log_event(
            db=db,
            event_type="AUTONOMOUS_SELL_EXECUTED" if is_autonomous else "MANUAL_EXIT_SUBMITTED",
            action=f"Closed Position {position.position_id} ({position.symbol}) via {exit_reason} (Net PnL: ${net_pnl:+,.2f})",
            actor="POSITION_MONITOR" if is_autonomous else "USER",
            symbol=position.symbol,
            market=position.market,
            position_id=position.position_id,
            details={
                "exit_reason": exit_reason,
                "fill_price": fill_price,
                "gross_pnl": gross_pnl,
                "net_pnl": net_pnl,
                "fees": fees,
                "roi_pct": roi_pct,
                "autonomous": is_autonomous,
            },
        )

        # Trigger post-trade Outcome Evaluator for slippage and execution attribution
        from app.services.core_intelligence.outcome_evaluator import OutcomeEvaluator
        try:
            OutcomeEvaluator.evaluate_trade_report(db=db, report_id=report.id)
        except Exception as e:
            logger.warning(f"Outcome evaluation error on Report #{report.id}: {e}")

        return report
