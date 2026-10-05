"""Risk Guardian Agent: Independent, deterministic safety and limit enforcement gate."""
import time
from sqlalchemy.orm import Session
from app.models.entities import Position, RiskSettings, utcnow
from app.schemas.intelligence import RiskGuardianOutput, PlanningOutput, AgentMetadata
from app.services.risk_service import RiskService
from app.services.audit_service import AuditService


class RiskGuardianAgent:
    """Independent deterministic risk-validation gate with absolute veto power."""

    NAME = "Risk Guardian"
    VERSION = "1.0.0"

    @classmethod
    def validate_plan(
        cls,
        db: Session,
        plan: PlanningOutput,
        symbol: str,
        market: str,
    ) -> RiskGuardianOutput:
        start_time = time.perf_counter()
        now = utcnow()

        # If planning produced NO_TRADE, Risk Guardian confirms NO_TRADE
        if plan.decision == "NO_TRADE":
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            meta = AgentMetadata(
                name=cls.NAME,
                version=cls.VERSION,
                status="COMPLETED",
                execution_time_ms=round(elapsed_ms, 2),
                timestamp=now,
            )
            return RiskGuardianOutput(
                agent=meta,
                verdict="NO_TRADE",
                checks_summary={"no_trade_input": True},
                blocking_reasons=[],
                emergency_stop_active=False,
                veto_power_active=True,
                timestamp=now,
            )

        settings = RiskService.get_or_create_settings(db)
        checks = {}
        blocking_reasons = []

        # 1. Global Emergency Stop Check (Instant Veto)
        if settings.emergency_stop_active:
            checks["emergency_stop_clear"] = False
            blocking_reasons.append("Global Emergency Stop is ACTIVE. All order submissions are frozen.")
        else:
            checks["emergency_stop_clear"] = True

        # 2. Daily Loss Limit Check
        # Calculate closed losses today
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        from app.models.entities import TradeReport
        today_reports = (
            db.query(TradeReport)
            .filter(TradeReport.exit_time >= start_of_day)
            .all()
        )
        realized_today = sum(r.net_pnl for r in today_reports)
        if realized_today <= -abs(settings.max_daily_loss):
            checks["daily_loss_ok"] = False
            blocking_reasons.append(
                f"Cumulative daily loss (${abs(realized_today):,.2f}) exceeds limit of ${settings.max_daily_loss:,.2f}."
            )
        else:
            checks["daily_loss_ok"] = True

        # 3. Maximum Concurrent Open Positions Check
        open_positions = db.query(Position).filter(Position.status == "OPEN").all()
        if len(open_positions) >= settings.max_open_positions:
            checks["open_positions_cap_ok"] = False
            blocking_reasons.append(
                f"Open position count ({len(open_positions)}) has reached maximum ceiling ({settings.max_open_positions})."
            )
        else:
            checks["open_positions_cap_ok"] = True

        # 4. Duplicate Order / Single Position Cap Per Symbol
        existing_for_symbol = [p for p in open_positions if p.symbol == symbol]
        if len(existing_for_symbol) >= 1:
            checks["single_position_per_symbol_ok"] = False
            blocking_reasons.append(f"Position already open for {symbol}. Duplicate entry disallowed.")
        else:
            checks["single_position_per_symbol_ok"] = True

        # 5. Position Sizing & Max Risk Per Trade Check
        sim_balance = settings.simulated_balance
        max_allowed_risk = sim_balance * (settings.max_risk_per_trade_pct / 100.0)
        proposed_risk = plan.estimated_risk_amount or 0.0

        if proposed_risk > max_allowed_risk * 1.05:  # allow 5% rounding tolerance
            checks["risk_per_trade_ok"] = False
            blocking_reasons.append(
                f"Proposed risk (${proposed_risk:,.2f}) exceeds policy limit of ${max_allowed_risk:,.2f} ({settings.max_risk_per_trade_pct}%)."
            )
        else:
            checks["risk_per_trade_ok"] = True

        # 6. Stop Loss & Parameter Integrity
        if plan.proposed_entry_price is not None and plan.stop_loss is not None:
            if plan.stop_loss >= plan.proposed_entry_price or plan.stop_loss <= 0:
                checks["stop_loss_integrity_ok"] = False
                blocking_reasons.append(
                    f"Stop loss ({plan.stop_loss}) must be strictly positive and lower than proposed entry price ({plan.proposed_entry_price})."
                )
            else:
                checks["stop_loss_integrity_ok"] = True
        elif plan.stop_loss is None:
            checks["stop_loss_integrity_ok"] = False
            blocking_reasons.append("Stop loss is missing from trade plan.")

        # 7. Quantity Integrity
        if plan.proposed_quantity is None or plan.proposed_quantity <= 0:
            checks["quantity_integrity_ok"] = False
            blocking_reasons.append(f"Proposed quantity ({plan.proposed_quantity}) must be greater than zero.")
        else:
            checks["quantity_integrity_ok"] = True

        # 8. Available Virtual Balance & Capital Allocation Check
        open_capital_used = sum(p.entry_price * p.quantity for p in open_positions)
        available_balance = max(0.0, sim_balance - open_capital_used)
        required_capital = (plan.proposed_entry_price or 0.0) * (plan.proposed_quantity or 0.0)
        if required_capital > available_balance:
            checks["available_balance_ok"] = False
            blocking_reasons.append(
                f"Insufficient capital: Required (${required_capital:,.2f}) exceeds available simulated balance (${available_balance:,.2f})."
            )
        else:
            checks["available_balance_ok"] = True

        # 9. Maximum Single-Position Size Check
        max_allowed_position = sim_balance * (settings.max_position_size_pct / 100.0)
        if required_capital > max_allowed_position:
            checks["max_position_size_ok"] = False
            blocking_reasons.append(
                f"Position size violation: Required capital (${required_capital:,.2f}) exceeds max allowed single-position size ({settings.max_position_size_pct}% = ${max_allowed_position:,.2f})."
            )
        else:
            checks["max_position_size_ok"] = True

        # 10. Instrument & Market Eligibility
        eligible_markets = {"FOREX", "NSE", "MCX"}
        if market not in eligible_markets:
            checks["market_eligible"] = False
            blocking_reasons.append(f"Market '{market}' is not eligible for virtual execution.")
        else:
            checks["market_eligible"] = True

        # Verdict
        passed = len(blocking_reasons) == 0
        verdict = "PASSED" if passed else "REJECTED"

        if not passed:
            AuditService.log_event(
                db=db,
                event_type="RISK_CHECK_FAILED",
                action=f"Risk Guardian vetoed trade plan for {symbol}: {'; '.join(blocking_reasons)}",
                actor="RISK_GUARDIAN",
                symbol=symbol,
                market=market,
                details={"blocking_reasons": blocking_reasons, "checks": checks},
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        meta = AgentMetadata(
            name=cls.NAME,
            version=cls.VERSION,
            status="COMPLETED" if passed else "BLOCKED",
            execution_time_ms=round(elapsed_ms, 2),
            timestamp=now,
            error_detail="; ".join(blocking_reasons) if not passed else None,
        )

        return RiskGuardianOutput(
            agent=meta,
            verdict=verdict,
            checks_summary=checks,
            blocking_reasons=blocking_reasons,
            emergency_stop_active=settings.emergency_stop_active,
            veto_power_active=True,
            timestamp=now,
        )
