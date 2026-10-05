"""API router for Deterministic Strategy vs AI Advisory Comparison."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.ai_comparison import (
    AIStrategyComparisonRecord,
    AIComparisonEvaluationRequest,
    AIComparisonFilter,
    AIComparisonSummary,
)
from app.services.ai_comparison_service import AIComparisonService

router = APIRouter(prefix="/research/ai-comparison", tags=["AI Strategy Comparison"])


@router.get("", response_model=AIComparisonSummary, summary="Retrieve AI vs Strategy Comparison History & Metrics")
def get_ai_comparisons(
    symbol: Optional[str] = Query(None, description="Filter by instrument symbol"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe (1D, 1H, 15m)"),
    concurrence_status: Optional[str] = Query(None, description="Filter by AGREE, DIVERGE, or CAUTIONARY"),
    start_timestamp: Optional[int] = Query(None, description="Start unix timestamp"),
    end_timestamp: Optional[int] = Query(None, description="End unix timestamp"),
    limit: int = Query(50, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db),
):
    """Returns historical concurrence and divergence metrics between rule-based strategies and local AI/ML advisory."""
    filter_params = AIComparisonFilter(
        symbol=symbol,
        timeframe=timeframe,
        concurrence_status=concurrence_status,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        limit=limit,
        offset=offset,
    )
    return AIComparisonService.get_summary(db=db, filter_params=filter_params)


@router.post("/evaluate", response_model=AIStrategyComparisonRecord, summary="Evaluate & Record AI vs Deterministic Concurrence")
def evaluate_ai_comparison(
    payload: AIComparisonEvaluationRequest,
    db: Session = Depends(get_db),
):
    """Evaluates alignment between a deterministic strategy signal and XGBoost / Qwen advisories,
    logs deduplicated divergence alerts, and stores the comparison record.
    """
    try:
        return AIComparisonService.record_comparison(db=db, req=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
