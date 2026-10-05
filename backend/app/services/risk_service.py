"""Server-Side Risk Validation Engine for Vibe Trader AI."""
import logging
from typing import Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import BuyProposal, Position, RiskSettings, TradeReport, utcnow
from app.services.audit_service import AuditService

logger = logging.getLogger("vibe-trader-ai.risk")


class RiskService:
    @staticmethod
    def get_or_create_settings(db: Session) -> RiskSettings:
        settings = db.query(RiskSettings).first()
        if not settings:
            settings = RiskSettings(
                simulated_balance=100000.0,
                max_risk_per_trade_pct=2.0,
                max_daily_loss=5000.0,
                max_open_positions=5,
                max_position_size_pct=20.0,
                emergency_stop_active=False,
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @classmethod
    def validate_buy_execution(cls, db: Session, proposal: BuyProposal) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Independently validates risk, account limits, proposal integrity, and emergency stops
        before executing an approved BUY order.
        """
        risk_settings = cls.get_or_create_settings(db)
        now = utcnow()

        # 1. Emergency Stop Check
        if risk_settings.emergency_stop_active:
            reason = "Global Emergency Stop is currently ACTIVE. Order submission halted."
            cls._record_failure(db, proposal, reason, "EMERGENCY_STOP_ACTIVE")
            return False, reason, {"emergency_stop": True}

        # 2. Daily Loss Limit Check
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_reports = (
            db.query(TradeReport)
            .filter(TradeReport.exit_time >= start_of_day)
            .all()
        )
        realized_today = sum(r.net_pnl for r in today_reports)
        if realized_today <= -abs(risk_settings.max_daily_loss):
            reason = f"Daily loss limit exceeded: Cumulative loss (${abs(realized_today):,.2f}) has reached limit of ${risk_settings.max_daily_loss:,.2f}."
            cls._record_failure(db, proposal, reason, "DAILY_LOSS_EXCEEDED")
            return False, reason, {"daily_loss": realized_today, "limit": risk_settings.max_daily_loss}

        # 2. Expiry Check
        p_exp = proposal.expires_at.replace(tzinfo=None) if proposal.expires_at.tzinfo else proposal.expires_at
        if now > p_exp or proposal.status == "EXPIRED":
            proposal.status = "EXPIRED"
            db.commit()
            reason = f"Proposal {proposal.proposal_id} expired at {proposal.expires_at.isoformat()}."
            cls._record_failure(db, proposal, reason, "PROPOSAL_EXPIRED")
            return False, reason, {"expired": True}

        # 3. Status Integrity Check (Prevent Duplicate / Re-execution)
        if proposal.status in ["EXECUTED", "BLOCKED_BY_RISK", "REJECTED"]:
            reason = f"Proposal {proposal.proposal_id} cannot be executed (Current status: {proposal.status})."
            cls._record_failure(db, proposal, reason, "INVALID_PROPOSAL_STATUS")
            return False, reason, {"status": proposal.status}

        # 4. Price & Parameter Integrity Check
        if proposal.stop_loss >= proposal.proposed_entry_price:
            reason = f"Integrity failure: Stop loss ({proposal.stop_loss}) must be lower than entry price ({proposal.proposed_entry_price})."
            cls._record_failure(db, proposal, reason, "PRICE_INTEGRITY_FAIL")
            return False, reason, {"price_integrity": False}

        if proposal.target <= proposal.proposed_entry_price:
            reason = f"Integrity failure: Target ({proposal.target}) must be higher than entry price ({proposal.proposed_entry_price})."
            cls._record_failure(db, proposal, reason, "PRICE_INTEGRITY_FAIL")
            return False, reason, {"price_integrity": False}

        if proposal.proposed_quantity <= 0:
            reason = "Quantity must be greater than zero."
            cls._record_failure(db, proposal, reason, "ZERO_QUANTITY")
            return False, reason, {"quantity": proposal.proposed_quantity}

        # 5. Max Open Positions Limit Check
        open_positions = db.query(Position).filter(Position.status == "OPEN").all()
        if len(open_positions) >= risk_settings.max_open_positions:
            reason = f"Limit reached: Max concurrent open positions ({risk_settings.max_open_positions}) already open."
            cls._record_failure(db, proposal, reason, "MAX_OPEN_POSITIONS_EXCEEDED")
            return False, reason, {"open_count": len(open_positions), "limit": risk_settings.max_open_positions}

        # 6. Existing Exposure Check (Prevent duplicate position on same symbol)
        same_symbol_open = [p for p in open_positions if p.symbol == proposal.symbol]
        if same_symbol_open:
            reason = f"Exposure conflict: An active position already exists for {proposal.symbol}."
            cls._record_failure(db, proposal, reason, "EXISTING_EXPOSURE_CONFLICT")
            return False, reason, {"symbol": proposal.symbol, "existing_position_id": same_symbol_open[0].position_id}

        # 7. Portfolio Balance & Capital Allocation Check
        total_balance = risk_settings.simulated_balance
        open_capital_used = sum(p.entry_price * p.quantity for p in open_positions)
        available_balance = max(0.0, total_balance - open_capital_used)
        required_capital = proposal.proposed_entry_price * proposal.proposed_quantity

        if required_capital > available_balance:
            reason = (
                f"Insufficient funds: Required capital (${required_capital:,.2f}) exceeds "
                f"available simulated cash (${available_balance:,.2f})."
            )
            cls._record_failure(db, proposal, reason, "INSUFFICIENT_FUNDS")
            return False, reason, {"required": required_capital, "available": available_balance}

        # 8. Single Position Maximum Allocation Check
        max_allowed_position_capital = total_balance * (risk_settings.max_position_size_pct / 100.0)
        if required_capital > max_allowed_position_capital:
            reason = (
                f"Position size violation: Required capital (${required_capital:,.2f}) exceeds maximum allowed "
                f"single-position size of {risk_settings.max_position_size_pct}% (${max_allowed_position_capital:,.2f})."
            )
            cls._record_failure(db, proposal, reason, "MAX_POSITION_SIZE_VIOLATION")
            return False, reason, {"required": required_capital, "max_allowed": max_allowed_position_capital}

        # 9. Maximum Risk Budget Check
        max_allowed_risk_amount = total_balance * (risk_settings.max_risk_per_trade_pct / 100.0)
        if proposal.risk_amount > max_allowed_risk_amount:
            reason = (
                f"Risk tolerance violation: Trade risk (${proposal.risk_amount:,.2f}) exceeds maximum allowable "
                f"risk of {risk_settings.max_risk_per_trade_pct}% per trade (${max_allowed_risk_amount:,.2f})."
            )
            cls._record_failure(db, proposal, reason, "MAX_RISK_PER_TRADE_VIOLATION")
            return False, reason, {"risk": proposal.risk_amount, "max_risk": max_allowed_risk_amount}

        # All checks passed!
        details = {
            "checks_passed": [
                "Emergency stop inactive",
                "Proposal unexpired & status valid",
                "Price and parameter integrity verified",
                "Open position capacity available",
                "Zero exposure conflict on symbol",
                "Sufficient available cash verified",
                "Single position size allocation compliant",
                "Risk-per-trade within threshold",
            ],
            "required_capital": required_capital,
            "trade_risk": proposal.risk_amount,
            "max_allowed_risk": max_allowed_risk_amount,
        }

        AuditService.log_event(
            db=db,
            event_type="RISK_CHECK_PASSED",
            action=f"Risk validation passed for Proposal {proposal.proposal_id}",
            actor="RISK_ENGINE",
            symbol=proposal.symbol,
            market=proposal.market,
            proposal_id=proposal.proposal_id,
            details=details,
        )

        return True, "All server-side risk validations passed successfully.", details

    @staticmethod
    def _record_failure(db: Session, proposal: BuyProposal, reason: str, code: str):
        proposal.status = "BLOCKED_BY_RISK"
        proposal.risk_check_details = reason
        db.commit()

        AuditService.log_event(
            db=db,
            event_type="RISK_CHECK_FAILED",
            action=f"Risk check failed ({code}) for Proposal {proposal.proposal_id}: {reason}",
            actor="RISK_ENGINE",
            symbol=proposal.symbol,
            market=proposal.market,
            proposal_id=proposal.proposal_id,
            details={"reason": reason, "code": code},
        )
        logger.warning(f"Risk check blocked Proposal {proposal.proposal_id}: {reason}")

    @classmethod
    def get_risk_settings(cls, db: Session) -> RiskSettings:
        return cls.get_or_create_settings(db)


risk_service = RiskService()
