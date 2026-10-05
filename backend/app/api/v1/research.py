"""API Router for Quantitative Research & Walk-Forward Validation Engine."""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.research import (
    WalkForwardRequest,
    WalkForwardResponse,
    SensitivityAnalysisRequest,
    SensitivityAnalysisResponse,
    RegimeAnalysisResponse,
)
from app.services.research_service import QuantResearchService
from app.services.strategy_engine import StrategyEngine

router = APIRouter(prefix="/research", tags=["Quantitative Research"])


@router.post("/walk-forward", response_model=WalkForwardResponse, summary="Execute Walk-Forward Multi-Fold Validation")
def run_walk_forward(req: WalkForwardRequest, db: Session = Depends(get_db)):
    """Executes multi-fold chronological walk-forward analysis with zero look-ahead bias,
    evaluating in-sample vs out-of-sample performance and Buy-and-Hold benchmark alpha.
    """
    return QuantResearchService.run_walk_forward(db=db, req=req)


@router.post("/sensitivity", response_model=SensitivityAnalysisResponse, summary="Run Sensitivity Stress Test")
def run_sensitivity(req: SensitivityAnalysisRequest, db: Session = Depends(get_db)):
    """Tests strategy resilience across 4 graduated execution friction and slippage scenarios."""
    return QuantResearchService.run_sensitivity_analysis(db=db, req=req)


@router.get("/regimes", response_model=RegimeAnalysisResponse, summary="Analyze Historical Market Regimes")
def get_market_regimes(
    symbol: str = Query("RELIANCE", description="Symbol to classify"),
    timeframe: str = Query("1D", description="Timeframe"),
    db: Session = Depends(get_db),
):
    """Classifies historical candles into Bullish, Bearish, Sideways, and High-Volatility regimes."""
    return QuantResearchService.run_regime_analysis(db=db, symbol=symbol, timeframe=timeframe)


@router.get("/strategies", response_model=List[Dict[str, Any]], summary="List Supported Research Strategies")
def get_research_strategies():
    """Returns available algorithmic strategies with parameter definitions and required candle history."""
    catalog = []
    for s_id, s_def in StrategyEngine.STRATEGY_CATALOG.items():
        catalog.append({
            "strategy_id": s_id,
            "name": s_def.name,
            "description": s_def.description,
            "required_candles": s_def.required_candle_history,
            "timeframes": getattr(s_def, "timeframe_compatibility", ["1D"]),
        })
    return catalog
