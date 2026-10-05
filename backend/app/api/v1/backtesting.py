"""Quantitative Backtesting API Router for Vibe Trader AI."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.workflow import BacktestRequest, BacktestSummaryResponse
from app.services.backtesting_service import BacktestingService

router = APIRouter(prefix="/backtesting", tags=["Quantitative Backtesting"])


@router.post("/run", response_model=BacktestSummaryResponse, summary="Execute Strategy Backtest Simulation")
def run_backtest(
    req: BacktestRequest,
    db: Session = Depends(get_db),
) -> BacktestSummaryResponse:
    """Simulates historical strategy execution including slippage, commissions, and performance metrics."""
    return BacktestingService.run_backtest(db=db, req=req)
