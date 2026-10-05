"""Strategies API endpoints with JSON validation and pagination."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.entities import Strategy, utcnow
from app.schemas.entities import (
    StrategyCreate,
    StrategyUpdate,
    StrategyRead,
    PaginatedResponse,
)

router = APIRouter(prefix="/strategies", tags=["Strategies"])


@router.get("", response_model=PaginatedResponse[StrategyRead], summary="List Strategies")
def list_strategies(
    market: Optional[str] = Query(None, description="Optional market filter"),
    is_active: Optional[bool] = Query(None, description="Filter by enabled status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[StrategyRead]:
    """Retrieve paginated strategies with optional market or active status filter."""
    query = db.query(Strategy)
    if market and market.upper() != "ALL":
        query = query.filter(func.upper(Strategy.market) == market.upper())
    if is_active is not None:
        query = query.filter(Strategy.is_active == is_active)

    total = query.count()
    items = query.order_by(Strategy.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=StrategyRead, status_code=status.HTTP_201_CREATED, summary="Create Strategy")
def create_strategy(
    payload: StrategyCreate,
    db: Session = Depends(get_db),
) -> StrategyRead:
    """Create a new strategy with validated JSON configuration."""
    strategy = Strategy(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        market=payload.market.strip().upper(),
        timeframe=payload.timeframe.strip(),
        parameters_json=payload.parameters_json,
        is_active=payload.is_active,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


@router.get("/{strategy_id}", response_model=StrategyRead, summary="Get Strategy by ID")
def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> StrategyRead:
    """Get single strategy details."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found.",
        )
    return strategy


@router.put("/{strategy_id}", response_model=StrategyRead, summary="Update Strategy")
def update_strategy(
    strategy_id: int,
    payload: StrategyUpdate,
    db: Session = Depends(get_db),
) -> StrategyRead:
    """Update strategy parameters, enabled status, or descriptive metadata."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(strategy, field, val)

    strategy.updated_at = utcnow()
    db.commit()
    db.refresh(strategy)
    return strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Strategy")
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
):
    """Delete a strategy by ID."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found.",
        )
    db.delete(strategy)
    db.commit()
    return None


@router.get("/catalogue/all", response_model=list, summary="List Pre-configured Strategy Catalogue")
def get_strategy_catalogue():
    """Retrieve pre-configured rule-based strategy definitions."""
    from app.services.strategy_engine import StrategyEngine
    return StrategyEngine.get_strategy_catalogue()


@router.post("/{strategy_code}/evaluate", summary="Evaluate Strategy Signals")
def evaluate_strategy_signal_endpoint(
    strategy_code: str,
    symbol: str = Query("RELIANCE", description="Symbol to evaluate"),
    market: str = Query("NSE", description="Market category: NSE, FOREX, MCX"),
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D"),
):
    """Evaluates a strategy from the catalogue against live/simulated market data."""
    from app.services.market_data_service import MarketDataService
    from app.services.indicators_service import IndicatorsService
    from app.services.pattern_service import PatternService
    from app.services.support_resistance_service import SupportResistanceService
    from app.services.strategy_engine import StrategyEngine

    ohlc = MarketDataService.get_ohlc(symbol=symbol, timeframe=timeframe, market=market)
    candles = ohlc.candles
    indicators = IndicatorsService.compute_all_indicators(candles, symbol=symbol, timeframe=timeframe)
    patterns = PatternService.detect_patterns(candles, symbol=symbol, timeframe=timeframe)
    sr = SupportResistanceService.calculate_zones(candles, symbol=symbol, timeframe=timeframe)

    signal_output = StrategyEngine.evaluate_strategy_signal(
        strategy_id=strategy_code,
        symbol=symbol,
        market=market,
        timeframe=timeframe,
        candles=candles,
        indicators=indicators,
        patterns=patterns,
        sr=sr,
    )
    return signal_output

