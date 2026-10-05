"""Performance Analytics API router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.entities import (
    PerformanceSummaryResponse,
    PerformanceByStrategyItem,
    PerformanceBySymbolItem,
)
from app.services.performance_service import performance_service

router = APIRouter(prefix="/performance", tags=["Performance Analytics"])


@router.get("/summary", response_model=PerformanceSummaryResponse, summary="Get Performance Analytics Summary")
def get_performance_summary(
    mode: str = Query("PAPER_TRADING", description="PAPER_TRADING or BACKTEST"),
    symbol: Optional[str] = Query(None, description="Optional symbol filter"),
    strategy: Optional[str] = Query(None, description="Optional strategy name filter"),
    market: Optional[str] = Query("ALL", description="Optional market filter"),
    db: Session = Depends(get_db),
) -> PerformanceSummaryResponse:
    """Retrieve detailed verified performance analytics and curves."""
    res = performance_service.get_paper_performance(
        db=db,
        symbol=symbol,
        strategy=strategy,
        market=market,
    )
    return PerformanceSummaryResponse(**res)


@router.get("/by-strategy", response_model=List[PerformanceByStrategyItem], summary="Get Performance Grouped by Strategy")
def get_performance_by_strategy(
    db: Session = Depends(get_db),
) -> List[PerformanceByStrategyItem]:
    """Retrieve performance grouped across executed strategies."""
    items = performance_service.get_performance_by_strategy(db)
    return [PerformanceByStrategyItem(**i) for i in items]


@router.get("/by-symbol", response_model=List[PerformanceBySymbolItem], summary="Get Performance Grouped by Symbol")
def get_performance_by_symbol(
    db: Session = Depends(get_db),
) -> List[PerformanceBySymbolItem]:
    """Retrieve performance grouped across traded symbols."""
    items = performance_service.get_performance_by_symbol(db)
    return [PerformanceBySymbolItem(**i) for i in items]
