"""Outcome Evaluator: Post-trade performance and slippage attribution analysis."""
import time
from typing import Optional
from sqlalchemy.orm import Session
from app.models.entities import TradeReport, BuyProposal, Position, utcnow
from app.schemas.intelligence import OutcomeEvaluationOutput, AgentMetadata
from app.services.audit_service import AuditService


class OutcomeEvaluator:
    """Evaluates completed paper trades comparing planned vs realized execution parameters."""

    NAME = "Outcome Evaluator"
    VERSION = "1.0.0"

    @classmethod
    def evaluate_trade_report(
        cls,
        db: Session,
        report_id: int,
    ) -> Optional[OutcomeEvaluationOutput]:
        report = db.query(TradeReport).filter(TradeReport.id == report_id).first()
        if not report:
            return None

        # Retrieve matching proposal for planned prices if available
        proposal = None
        if report.proposal_id:
            proposal = db.query(BuyProposal).filter(BuyProposal.id == report.proposal_id).first()

        planned_entry = proposal.proposed_entry_price if proposal else report.entry_price
        actual_entry = report.entry_price
        entry_slippage = round(abs(actual_entry - planned_entry), 4)

        planned_exit = (
            (proposal.target if "PROFIT" in report.exit_reason.upper() else proposal.stop_loss)
            if proposal
            else report.exit_price
        )
        actual_exit = report.exit_price
        exit_slippage = round(abs(actual_exit - planned_exit), 4)

        # Evaluate strategy behavior
        if report.net_pnl > 0 and "PROFIT" in report.exit_reason.upper():
            behavior = "Conforming: Strategy reached target boundary with constructive reward capture."
        elif report.net_pnl <= 0 and "STOP" in report.exit_reason.upper():
            behavior = "Protective: Strategy stop loss bounded downside risk as planned."
        elif "AUTONOMOUS" in report.exit_reason.upper():
            behavior = "Automated: Pre-authorized autonomous exit liquidated position per safety trigger."
        else:
            behavior = f"Manual: Operator closed position ({report.exit_reason})."

        now = utcnow()

        AuditService.log_event(
            db=db,
            event_type="OUTCOME_EVALUATED",
            action=f"Outcome Evaluator analyzed Report #{report.id} on {report.symbol}: Net P&L ${report.net_pnl:.2f}, Slip ${report.slippage:.2f}",
            actor="OUTCOME_EVALUATOR",
            symbol=report.symbol,
            market=report.market,
            details={
                "report_id": report.id,
                "net_pnl": report.net_pnl,
                "behavior": behavior,
                "entry_slippage": entry_slippage,
                "exit_slippage": exit_slippage,
            },
        )

        str_pos_id = None
        if report.position_id:
            pos_rec = db.query(Position).filter(Position.id == report.position_id).first()
            str_pos_id = pos_rec.position_id if pos_rec else str(report.position_id)

        return OutcomeEvaluationOutput(
            report_id=report.id,
            position_id=str_pos_id,
            symbol=report.symbol,
            market=report.market,
            strategy_name=report.strategy_name,
            planned_entry=round(planned_entry, 4),
            actual_entry=round(actual_entry, 4),
            entry_slippage=entry_slippage,
            planned_exit=round(planned_exit, 4),
            actual_exit=round(actual_exit, 4),
            exit_slippage=exit_slippage,
            gross_pnl=round(report.gross_pnl, 2),
            fees=round(report.fees, 2),
            net_pnl=round(report.net_pnl, 2),
            realized_vs_expected_behavior=behavior,
            evaluated_at=now,
        )
