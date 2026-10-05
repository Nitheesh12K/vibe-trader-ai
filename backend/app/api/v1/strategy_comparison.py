"""Strategy Comparison API router.

Executes side-by-side quantitative backtests of multiple strategies across the
exact same dataset and configuration, presenting neutral factual performance metrics.
Strictly avoids arbitrary ranking, winner labels, or predictive claims.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.entities import (
    StrategyCompareRequest,
    StrategyComparisonItem,
    StrategyCompareResponse,
)
from app.schemas.workflow import BacktestRequest
from app.services.backtesting_service import BacktestingService
from app.services.strategy_engine import StrategyEngine
from app.models.entities import utcnow

logger = logging.getLogger("vibe-trader-ai.strategy_comparison")
router = APIRouter(prefix="/strategies", tags=["Strategy Comparison"])


@router.post("/compare", response_model=StrategyCompareResponse, summary="Compare Multiple Strategies Side-by-Side")
def compare_strategies(
    payload: StrategyCompareRequest,
    db: Session = Depends(get_db),
) -> StrategyCompareResponse:
    """
    Run identical-parameter backtest simulations for multiple strategies on the same dataset.
    Returns neutral factual metrics: trades, gross/net P&L, win rate, avg win/loss,
    profit factor, max drawdown, expectancy, fees, slippage, trade list, and equity curve.
    """
    if not payload.strategy_codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one strategy code must be provided.")

    if len(payload.strategy_codes) > 7:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 7 strategies can be compared at once.")

    comparison_results: List[StrategyComparisonItem] = []

    for code in payload.strategy_codes:
        try:
            resolved_code = BacktestingService.resolve_strategy_id(code)
            strat_def = StrategyEngine.STRATEGY_CATALOG[resolved_code]
            strat_name = strat_def.name
            strat_version = getattr(strat_def, "version", "1.0.0")

            bt_req = BacktestRequest(
                strategy_name=resolved_code,
                symbol=payload.symbol,
                timeframe=payload.timeframe,
                initial_capital=payload.initial_capital,
                dataset_id=payload.dataset_id,
                commission_per_trade=2.0,
                slippage_pct=payload.slippage_pct,
            )

            bt_res = BacktestingService.run_backtest(db=db, req=bt_req)

            # Build equity curve points
            equity_curve = [{"timestamp": 0, "equity": payload.initial_capital, "drawdown_pct": 0.0}]
            curr_equity = payload.initial_capital
            peak_equity = payload.initial_capital
            for t in bt_res.trades:
                curr_equity += t.net_pnl
                if curr_equity > peak_equity:
                    peak_equity = curr_equity
                dd_pct = round(((peak_equity - curr_equity) / peak_equity) * 100, 2) if peak_equity > 0 else 0.0
                equity_curve.append({
                    "timestamp": t.exit_time,
                    "equity": round(curr_equity, 2),
                    "drawdown_pct": dd_pct,
                })

            # Build trade list
            trade_list = [
                {
                    "trade_id": t.trade_id,
                    "entry_time": t.entry_time,
                    "exit_time": t.exit_time,
                    "side": "LONG",
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "quantity": t.quantity,
                    "gross_pnl": t.gross_pnl,
                    "net_pnl": t.net_pnl,
                    "exit_reason": t.exit_reason,
                    "holding_period_candles": 1,
                }
                for t in bt_res.trades
            ]

            comparison_results.append(
                StrategyComparisonItem(
                    strategy_code=resolved_code,
                    strategy_name=strat_name,
                    strategy_version=strat_version,
                    dataset_id=payload.dataset_id,
                    total_trades=bt_res.total_trades,
                    winning_trades=bt_res.winning_trades,
                    losing_trades=bt_res.losing_trades,
                    win_rate=bt_res.win_rate,
                    gross_pnl=round(bt_res.net_pnl + (bt_res.total_trades * 2.0), 2),
                    net_pnl=bt_res.net_pnl,
                    roi_pct=bt_res.net_roi_pct,
                    average_win=bt_res.average_win,
                    average_loss=bt_res.average_loss,
                    profit_factor=bt_res.profit_factor,
                    max_drawdown=round(payload.initial_capital * (bt_res.max_drawdown_pct / 100.0), 2),
                    max_drawdown_pct=bt_res.max_drawdown_pct,
                    expectancy=bt_res.expectancy,
                    average_holding_time="N/A",
                    total_fees=round(bt_res.total_trades * 2.0, 2),
                    total_slippage=round(bt_res.total_trades * payload.initial_capital * payload.slippage_pct * 0.05, 2),
                    equity_curve=equity_curve,
                    trade_list=trade_list,
                    disclaimer="NEUTRAL FACTUAL METRICS: Historical performance does not guarantee future results.",
                )
            )
        except Exception as e:
            logger.warning(f"Strategy comparison error for {code}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to evaluate strategy '{code}': {str(e)}"
            )

    return StrategyCompareResponse(
        symbol=payload.symbol,
        market=payload.market,
        timeframe=payload.timeframe,
        initial_capital=payload.initial_capital,
        compared_at=utcnow(),
        strategies=comparison_results,
    )
