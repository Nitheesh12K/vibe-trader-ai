"""Autonomous Trade Manager Agent: Manages positions, enforces approval gates, and oversees pre-authorized exits."""
import time
from sqlalchemy.orm import Session
from app.models.entities import Position, AutonomousExitPermission, utcnow
from app.schemas.intelligence import TradeManagerOutput, AgentMetadata
from app.services.position_monitor import PositionMonitorService
from app.services.audit_service import AuditService


class AutonomousTradeManagerAgent:
    """Logical agent executing paper trades strictly within granted permissions."""

    NAME = "Autonomous Trade Manager"
    VERSION = "1.0.0"

    @classmethod
    def inspect_and_manage(
        cls,
        db: Session,
    ) -> TradeManagerOutput:
        start_time = time.perf_counter()
        now = utcnow()

        # Check user pre-authorization settings
        perm = (
            db.query(AutonomousExitPermission)
            .order_by(AutonomousExitPermission.id.desc())
            .first()
        )
        is_enabled = bool(perm and perm.is_enabled)

        open_positions = db.query(Position).filter(Position.status == "OPEN").all()

        # Trade Manager runs active surveillance ONLY when open paper positions exist
        if not open_positions:
            meta = AgentMetadata(
                name=cls.NAME,
                version=cls.VERSION,
                status="IDLE",
                execution_time_ms=0.0,
                timestamp=now,
            )
            return TradeManagerOutput(
                agent=meta,
                monitored_positions_count=0,
                autonomous_exit_enabled=is_enabled,
                exit_triggers_checked=0,
                autonomous_exits_executed=0,
                status_message="No active open paper positions requiring exit surveillance. Trade Manager is IDLE.",
                timestamp=now,
            )

        # Run position checks
        exits_executed = 0
        triggers_checked = len(open_positions)

        for pos in open_positions:
            # Check if position crossed SL or TP
            crossed_sl = pos.current_price <= pos.stop_loss
            crossed_tp = pos.current_price >= pos.target

            if crossed_sl or crossed_tp:
                reason = "STOP_LOSS" if crossed_sl else "TAKE_PROFIT"
                if is_enabled:
                    # Pre-authorized autonomous exit
                    try:
                        PositionMonitorService.close_position(
                            db=db,
                            position_id=pos.position_id,
                            exit_price=pos.current_price,
                            reason=f"AUTONOMOUS_{reason}",
                            autonomous_exit=True,
                        )
                        exits_executed += 1
                        AuditService.log_event(
                            db=db,
                            event_type="AUTONOMOUS_EXIT_TRIGGERED",
                            action=f"Trade Manager executed autonomous SELL on {pos.symbol} ({reason})",
                            actor="TRADE_MANAGER",
                            symbol=pos.symbol,
                            market=pos.market,
                            position_id=pos.position_id,
                            details={"reason": reason, "exit_price": pos.current_price},
                        )
                    except Exception as e:
                        AuditService.log_event(
                            db=db,
                            event_type="EXECUTION_ERROR",
                            action=f"Trade Manager error closing {pos.position_id}: {str(e)}",
                            actor="TRADE_MANAGER",
                            symbol=pos.symbol,
                            position_id=pos.position_id,
                        )
                else:
                    # User permission disabled: Log manual alert notification
                    AuditService.log_event(
                        db=db,
                        event_type="EXIT_TRIGGER_ALERT",
                        action=f"Price crossed {reason} on {pos.symbol} at ${pos.current_price:.4f}. Autonomous SELL is DISABLED — Manual intervention required.",
                        actor="TRADE_MANAGER",
                        symbol=pos.symbol,
                        market=pos.market,
                        position_id=pos.position_id,
                        details={"reason": reason, "current_price": pos.current_price},
                    )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        meta = AgentMetadata(
            name=cls.NAME,
            version=cls.VERSION,
            status="COMPLETED",
            execution_time_ms=round(elapsed_ms, 2),
            timestamp=now,
        )

        status_msg = (
            f"Active surveillance over {len(open_positions)} open position(s). "
            f"Autonomous exit permission is {'ENABLED' if is_enabled else 'DISABLED (Manual Fallback)'}. "
            f"{exits_executed} exit order(s) processed."
        )

        return TradeManagerOutput(
            agent=meta,
            monitored_positions_count=len(open_positions),
            autonomous_exit_enabled=is_enabled,
            exit_triggers_checked=triggers_checked,
            autonomous_exits_executed=exits_executed,
            status_message=status_msg,
            timestamp=now,
        )
