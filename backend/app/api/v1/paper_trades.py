"""Paper Trading API endpoints with order validation and P&L calculation."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.entities import PaperTrade, utcnow
from app.schemas.entities import (
    PaperTradeCreate,
    PaperTradeUpdate,
    PaperTradeRead,
    PaginatedResponse,
)

router = APIRouter(prefix="/paper-trades", tags=["Paper Trading"])


@router.get("", response_model=PaginatedResponse[PaperTradeRead], summary="List Paper Trades")
def list_paper_trades(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: Open, Closed, Cancelled"),
    market: Optional[str] = Query(None, description="Optional market filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PaperTradeRead]:
    """Retrieve paginated paper trades with optional status and market filters."""
    query = db.query(PaperTrade)
    if status_filter:
        query = query.filter(func.lower(PaperTrade.status) == status_filter.strip().lower())
    if market and market.upper() != "ALL":
        query = query.filter(func.upper(PaperTrade.market) == market.strip().upper())

    total = query.count()
    items = query.order_by(PaperTrade.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=PaperTradeRead, status_code=status.HTTP_201_CREATED, summary="Create Paper Trade")
def create_paper_trade(
    payload: PaperTradeCreate,
    db: Session = Depends(get_db),
) -> PaperTradeRead:
    """Create and record an open paper trade with validated prices and quantity."""
    # Additional domain validation on SL/TP if provided
    if payload.direction == "Long":
        if payload.stop_loss and payload.stop_loss >= payload.entry_price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="For Long positions, stop loss must be lower than the entry price.",
            )
        if payload.take_profit and payload.take_profit <= payload.entry_price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="For Long positions, take profit must be higher than the entry price.",
            )
    elif payload.direction == "Short":
        if payload.stop_loss and payload.stop_loss <= payload.entry_price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="For Short positions, stop loss must be higher than the entry price.",
            )
        if payload.take_profit and payload.take_profit >= payload.entry_price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="For Short positions, take profit must be lower than the entry price.",
            )

    trade = PaperTrade(
        symbol=payload.symbol.strip().upper(),
        market=payload.market.strip().upper(),
        side=payload.direction,
        order_type="MARKET",
        quantity=payload.quantity,
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss,
        take_profit=payload.take_profit,
        status="Open",
        notes=payload.notes.strip() if payload.notes else None,
        created_at=utcnow(),
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


@router.get("/{trade_id}", response_model=PaperTradeRead, summary="Get Paper Trade by ID")
def get_paper_trade(
    trade_id: int,
    db: Session = Depends(get_db),
) -> PaperTradeRead:
    """Get single paper trade by ID."""
    trade = db.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper trade with ID {trade_id} not found.",
        )
    return trade


@router.put("/{trade_id}", response_model=PaperTradeRead, summary="Update / Close Paper Trade")
def update_paper_trade(
    trade_id: int,
    payload: PaperTradeUpdate,
    db: Session = Depends(get_db),
) -> PaperTradeRead:
    """Update paper trade status or close it with an exit price, computing simulated P&L."""
    trade = db.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper trade with ID {trade_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # If exit_price is provided or status is being set to Closed, calculate P&L
    if "exit_price" in update_data and update_data["exit_price"] is not None:
        exit_p = update_data["exit_price"]
        trade.exit_price = exit_p
        trade.closed_at = utcnow()
        trade.status = "Closed"

        # Calculate P&L:
        # Long: (exit_price - entry_price) * quantity
        # Short: (entry_price - exit_price) * quantity
        if trade.side.lower() in {"long", "buy"}:
            trade.pnl = round((exit_p - trade.entry_price) * trade.quantity, 2)
        else:
            trade.pnl = round((trade.entry_price - exit_p) * trade.quantity, 2)

    if "status" in update_data and update_data["status"] is not None:
        new_status = update_data["status"]
        trade.status = new_status
        if new_status in {"Closed", "Cancelled"} and not trade.closed_at:
            trade.closed_at = utcnow()

    if "stop_loss" in update_data:
        trade.stop_loss = update_data["stop_loss"]
    if "take_profit" in update_data:
        trade.take_profit = update_data["take_profit"]
    if "notes" in update_data and update_data["notes"] is not None:
        trade.notes = update_data["notes"]

    db.commit()
    db.refresh(trade)
    return trade


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Paper Trade")
def delete_paper_trade(
    trade_id: int,
    db: Session = Depends(get_db),
):
    """Delete a paper trade record."""
    trade = db.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper trade with ID {trade_id} not found.",
        )
    db.delete(trade)
    db.commit()
    return None
