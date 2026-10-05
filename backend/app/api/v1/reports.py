"""Trade Reports & Post-Trade Analytics API Router for Vibe Trader AI."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.entities import TradeReport
from app.schemas.workflow import TradeReportRead

router = APIRouter(prefix="/reports", tags=["Trade Reports & Analytics"])


@router.get("", response_model=List[TradeReportRead], summary="List Closed Trade Reports")
def list_reports(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    market: Optional[str] = Query(None, description="Filter by market"),
    db: Session = Depends(get_db),
) -> List[TradeReportRead]:
    query = db.query(TradeReport).order_by(TradeReport.exit_time.desc())
    if symbol:
        query = query.filter(TradeReport.symbol == symbol)
    if market:
        query = query.filter(TradeReport.market == market.upper())
    return query.limit(100).all()


@router.get("/{report_id}", response_model=TradeReportRead, summary="Get Single Trade Report")
def get_report(report_id: int, db: Session = Depends(get_db)) -> TradeReportRead:
    report = db.query(TradeReport).filter(TradeReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Trade report not found")
    return report
