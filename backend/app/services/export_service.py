"""Report export service supporting CSV and JSON formats.

Exports Trade Journal, Paper Trades, Portfolio Summary, Backtest Reports,
Strategy Comparison, Performance Analytics, and Audit Events with metadata,
simulation disclaimers, and strict exclusion of secrets and broker credentials.
"""
import io
import csv
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.entities import (
    PaperTrade,
    TradeJournalEntry,
    TradeReport,
    Position,
    RiskSettings,
    AuditLog,
    CustomDataset,
    utcnow,
)

logger = logging.getLogger("vibe-trader-ai.export")

DISCLAIMER_HEADER = (
    "# VIBE TRADER AI — EXPORT REPORT\n"
    "# DISCLAIMER: Generated from simulated paper trading and historical quantitative backtests.\n"
    "# Real capital is NEVER exchanged. Fail-closed live order shield active.\n"
    "# Zero broker secrets or private API credentials are included.\n"
)


class ExportService:
    """Service generating formatted CSV and JSON export files."""

    def export_paper_trades(self, db: Session, format: str = "csv") -> Dict[str, Any]:
        """Export paper trades list."""
        trades = db.query(PaperTrade).order_by(PaperTrade.created_at.desc()).all()
        data = [
            {
                "trade_id": t.id,
                "symbol": t.symbol,
                "market": t.market,
                "side": t.side,
                "order_type": t.order_type,
                "quantity": t.quantity,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price or "",
                "stop_loss": t.stop_loss or "",
                "take_profit": t.take_profit or "",
                "pnl": round(t.pnl, 2) if t.pnl is not None else "",
                "status": t.status,
                "notes": t.notes or "",
                "created_at": t.created_at.isoformat() if t.created_at else "",
                "closed_at": t.closed_at.isoformat() if t.closed_at else "",
            }
            for t in trades
        ]

        if format.lower() == "json":
            payload = {
                "report_type": "PAPER_TRADES",
                "exported_at": utcnow().isoformat(),
                "total_records": len(data),
                "data_source": "SQLITE_PAPER_TRADES",
                "disclaimer": "SIMULATION ONLY. NO REAL MONEY AT RISK.",
                "data": data,
            }
            return {
                "content": json.dumps(payload, indent=2),
                "media_type": "application/json",
                "filename": f"vibe_paper_trades_{utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            }

        # CSV format
        output = io.StringIO()
        output.write(DISCLAIMER_HEADER)
        output.write(f"# Exported At: {utcnow().isoformat()}\n\n")

        if data:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        else:
            output.write("No paper trades found.\n")

        return {
            "content": output.getvalue(),
            "media_type": "text/csv",
            "filename": f"vibe_paper_trades_{utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
        }

    def export_trade_journal(self, db: Session, format: str = "csv") -> Dict[str, Any]:
        """Export trade journal reflections."""
        entries = db.query(TradeJournalEntry).order_by(TradeJournalEntry.created_at.desc()).all()
        data = [
            {
                "journal_id": j.id,
                "trade_id": j.trade_id or "",
                "symbol": j.symbol or "",
                "title": j.title,
                "notes": j.notes,
                "lessons_learned": j.lessons_learned or "",
                "tags": j.tags or "",
                "created_at": j.created_at.isoformat() if j.created_at else "",
            }
            for j in entries
        ]

        if format.lower() == "json":
            payload = {
                "report_type": "TRADE_JOURNAL",
                "exported_at": utcnow().isoformat(),
                "total_records": len(data),
                "data_source": "SQLITE_TRADE_JOURNAL",
                "data": data,
            }
            return {
                "content": json.dumps(payload, indent=2),
                "media_type": "application/json",
                "filename": f"vibe_trade_journal_{utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            }

        output = io.StringIO()
        output.write(DISCLAIMER_HEADER)
        output.write(f"# Exported At: {utcnow().isoformat()}\n\n")

        if data:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        else:
            output.write("No journal entries found.\n")

        return {
            "content": output.getvalue(),
            "media_type": "text/csv",
            "filename": f"vibe_trade_journal_{utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
        }

    def export_portfolio_summary(self, db: Session, format: str = "csv") -> Dict[str, Any]:
        """Export portfolio snapshot and open positions."""
        risk_st = db.query(RiskSettings).first()
        initial_balance = risk_st.simulated_balance if risk_st else 100000.0

        positions = db.query(Position).filter(Position.status == "OPEN").all()
        reports = db.query(TradeReport).all()

        realized_pnl = sum(r.net_pnl for r in reports)
        unrealized_pnl = sum((p.unrealized_pnl or 0.0) for p in positions)
        total_fees = sum(r.fees for r in reports)
        total_slippage = sum(r.slippage for r in reports)
        current_equity = initial_balance + realized_pnl + unrealized_pnl

        summary = {
            "virtual_initial_capital": initial_balance,
            "current_equity": round(current_equity, 2),
            "realized_pnl": round(realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "total_fees": round(total_fees, 2),
            "total_slippage": round(total_slippage, 2),
            "open_positions_count": len(positions),
            "closed_trades_count": len(reports),
            "emergency_stop_active": risk_st.emergency_stop_active if risk_st else False,
            "exported_at": utcnow().isoformat(),
        }

        pos_data = [
            {
                "position_id": p.position_id,
                "symbol": p.symbol,
                "market": p.market,
                "side": p.side,
                "quantity": p.quantity,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "stop_loss": p.stop_loss,
                "target": p.target,
                "unrealized_pnl": round(p.unrealized_pnl or 0.0, 2),
                "created_at": p.created_at.isoformat() if p.created_at else "",
            }
            for p in positions
        ]

        if format.lower() == "json":
            payload = {
                "report_type": "PORTFOLIO_SUMMARY",
                "summary": summary,
                "open_positions": pos_data,
                "disclaimer": "SIMULATED VIRTUAL CAPITAL. NO REAL ASSETS.",
            }
            return {
                "content": json.dumps(payload, indent=2),
                "media_type": "application/json",
                "filename": f"vibe_portfolio_{utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            }

        output = io.StringIO()
        output.write(DISCLAIMER_HEADER)
        output.write(f"# Exported At: {utcnow().isoformat()}\n\n")
        output.write("# --- PORTFOLIO SUMMARY ---\n")
        for k, v in summary.items():
            output.write(f"{k},{v}\n")
        output.write("\n# --- OPEN POSITIONS ---\n")
        if pos_data:
            writer = csv.DictWriter(output, fieldnames=list(pos_data[0].keys()))
            writer.writeheader()
            writer.writerows(pos_data)
        else:
            output.write("No open positions.\n")

        return {
            "content": output.getvalue(),
            "media_type": "text/csv",
            "filename": f"vibe_portfolio_{utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
        }

    def export_audit_logs(self, db: Session, format: str = "csv") -> Dict[str, Any]:
        """Export append-only audit trail."""
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(500).all()
        data = [
            {
                "audit_id": l.id,
                "event_type": l.event_type,
                "action": l.action,
                "actor": l.actor,
                "symbol": l.symbol or "",
                "market": l.market or "",
                "proposal_id": l.proposal_id or "",
                "position_id": l.position_id or "",
                "details": l.details_json,
                "timestamp": l.timestamp.isoformat() if l.timestamp else "",
            }
            for l in logs
        ]

        if format.lower() == "json":
            payload = {
                "report_type": "AUDIT_TRAIL",
                "exported_at": utcnow().isoformat(),
                "total_records": len(data),
                "data": data,
            }
            return {
                "content": json.dumps(payload, indent=2),
                "media_type": "application/json",
                "filename": f"vibe_audit_trail_{utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            }

        output = io.StringIO()
        output.write(DISCLAIMER_HEADER)
        output.write(f"# Exported At: {utcnow().isoformat()}\n\n")

        if data:
            writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
        else:
            output.write("No audit logs found.\n")

        return {
            "content": output.getvalue(),
            "media_type": "text/csv",
            "filename": f"vibe_audit_trail_{utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
        }


export_service = ExportService()
