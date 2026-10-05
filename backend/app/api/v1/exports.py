"""Report Export API router supporting CSV and JSON formats."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.export_service import export_service

router = APIRouter(prefix="/exports", tags=["Report Export"])


@router.get("/{report_type}", summary="Export Verified Report as CSV or JSON")
def export_report(
    report_type: str,
    format: str = Query("csv", description="Export format: csv or json"),
    db: Session = Depends(get_db),
):
    """
    Generate downloadable CSV or JSON export for:
    - trades (paper trades)
    - journal (trade journal reflections)
    - portfolio (portfolio summary & open positions)
    - audit (audit trail events)
    """
    fmt = format.lower().strip()
    if fmt not in {"csv", "json"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Only 'csv' and 'json' are supported."
        )

    r_type = report_type.lower().strip()

    if r_type in {"trades", "paper_trades", "papertrades"}:
        res = export_service.export_paper_trades(db, format=fmt)
    elif r_type in {"journal", "trade_journal", "tradejournal"}:
        res = export_service.export_trade_journal(db, format=fmt)
    elif r_type in {"portfolio", "summary", "portfolio_summary"}:
        res = export_service.export_portfolio_summary(db, format=fmt)
    elif r_type in {"audit", "audit_trail", "audits", "audit_logs"}:
        res = export_service.export_audit_logs(db, format=fmt)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown report type '{report_type}'. Available: trades, journal, portfolio, audit."
        )

    return Response(
        content=res["content"],
        media_type=res["media_type"],
        headers={
            "Content-Disposition": f"attachment; filename=\"{res['filename']}\"",
            "Cache-Control": "no-cache",
        },
    )
