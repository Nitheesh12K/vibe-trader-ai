"""Memory Agent: Retrieves structured historical context and past regime outcomes from SQLite."""
import time
from sqlalchemy.orm import Session
from app.models.entities import (
    BuyProposal,
    PaperTrade,
    TradeReport,
    AuditLog,
    Strategy,
    utcnow,
)
from app.schemas.intelligence import MemoryContextOutput, AgentMetadata


class MemoryAgent:
    """Logical agent recalling past proposals, approvals, rejections, and trade reports."""

    NAME = "Memory Agent"
    VERSION = "1.0.0"

    @classmethod
    def recall(
        cls,
        db: Session,
        symbol: str,
        regime: str,
    ) -> MemoryContextOutput:
        start_time = time.perf_counter()
        now = utcnow()

        # 1. Past proposals for this symbol
        past_proposals = db.query(BuyProposal).filter(BuyProposal.symbol == symbol).all()
        pending_count = sum(1 for p in past_proposals if p.status == "PENDING")
        approved_count = sum(1 for p in past_proposals if p.status in ["APPROVED", "APPROVED_AND_EXECUTED"])
        rejected_count = sum(1 for p in past_proposals if p.status == "REJECTED")
        expired_count = sum(1 for p in past_proposals if p.status == "EXPIRED")

        proposals_summary = {
            "total": len(past_proposals),
            "approved": approved_count,
            "rejected": rejected_count,
            "expired": expired_count,
            "pending": pending_count,
        }

        # 2. Historical completed trade reports for this symbol / regime
        reports = db.query(TradeReport).filter(TradeReport.symbol == symbol).all()
        similar_setups_found = len(reports)
        wins = sum(1 for r in reports if r.net_pnl > 0)
        win_rate = (wins / len(reports) * 100.0) if reports else 50.0  # default uninformative baseline

        # 3. Contextual notes & audit reflections
        relevant_notes = []
        if rejected_count > 0:
            relevant_notes.append(f"User previously rejected {rejected_count} proposal(s) on {symbol}.")
        if approved_count > 0:
            relevant_notes.append(f"User approved {approved_count} historical proposal(s) on {symbol}.")

        # Check recent audit logs for risk rejections
        risk_blocks = (
            db.query(AuditLog)
            .filter(AuditLog.symbol == symbol, AuditLog.event_type.ilike("%RISK%"))
            .order_by(AuditLog.id.desc())
            .limit(3)
            .all()
        )
        for rb in risk_blocks:
            relevant_notes.append(f"Prior risk note: {rb.action}")

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        meta = AgentMetadata(
            name=cls.NAME,
            version=cls.VERSION,
            status="COMPLETED",
            execution_time_ms=round(elapsed_ms, 2),
            timestamp=now,
        )

        return MemoryContextOutput(
            agent=meta,
            symbol=symbol,
            similar_setups_found=similar_setups_found,
            regime_historical_win_rate=round(win_rate, 1),
            past_proposals_summary=proposals_summary,
            relevant_notes=relevant_notes[:4],
            timestamp=now,
        )
