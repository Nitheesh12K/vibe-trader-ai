"""Open Positions API Router for Vibe Trader AI."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.entities import Position
from app.schemas.workflow import PositionRead, PositionCloseRequest, TradeReportRead
from app.services.position_monitor import PositionMonitorService

router = APIRouter(prefix="/positions", tags=["Open Positions & Monitoring"])


@router.get("", response_model=List[PositionRead], summary="List Tracked Positions")
def list_positions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter: OPEN or CLOSED"),
    symbol: Optional[str] = Query(None, description="Filter by instrument symbol"),
    db: Session = Depends(get_db),
) -> List[PositionRead]:
    """Retrieve all tracked positions with live calculated unrealized P&L."""
    query = db.query(Position).order_by(Position.created_at.desc())
    if status_filter:
        query = query.filter(Position.status == status_filter.upper())
    if symbol:
        query = query.filter(Position.symbol == symbol)
    return query.limit(100).all()


@router.get("/{position_id}", response_model=PositionRead, summary="Get Single Position")
def get_position(position_id: str, db: Session = Depends(get_db)) -> PositionRead:
    pos = db.query(Position).filter(
        (Position.position_id == position_id) | (Position.id == int(position_id) if position_id.isdigit() else False)
    ).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")
    return pos


@router.post("/{position_id}/close", response_model=TradeReportRead, summary="Manually Close Position")
def close_position(
    position_id: str,
    req: PositionCloseRequest,
    db: Session = Depends(get_db),
) -> TradeReportRead:
    """Manually exit an active position, triggering virtual SELL order and generating a trade report."""
    try:
        report = PositionMonitorService.close_position_manually(
            db=db,
            position_id=position_id,
            exit_price_override=req.exit_price,
            reason=req.reason,
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
