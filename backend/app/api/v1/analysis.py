"""Technical Analysis API Router for Indicators, Patterns, S/R, and Factual Summary."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.market_data_service import MarketDataService
from app.services.indicators_service import IndicatorsService
from app.services.pattern_service import PatternService
from app.services.support_resistance_service import SupportResistanceService
from app.services.analysis_summary_service import AnalysisSummaryService
from app.schemas.analysis import (
    IndicatorsResponse,
    PatternsResponse,
    SupportResistanceResponse,
    AnalysisSummaryResponse,
    TechnicalAnalysisFullBundle,
)
from app.schemas.ai_analysis import AIAnalysisRequest, AIAnalysisResponse

router = APIRouter(prefix="/analysis", tags=["Technical Analysis"])


@router.get("/indicators", response_model=IndicatorsResponse, summary="Compute Technical Indicators")
def get_indicators(
    symbol: str = Query("EUR/USD", description="Symbol name or ticker"),
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D"),
    market: Optional[str] = Query(None, description="Optional market tag: FOREX, NSE, MCX"),
    rsi_period: int = Query(14, ge=2, le=100, description="RSI lookback period"),
    macd_fast: int = Query(12, ge=2, le=50, description="MACD fast period"),
    macd_slow: int = Query(26, ge=5, le=100, description="MACD slow period"),
    macd_signal: int = Query(9, ge=2, le=50, description="MACD signal smoothing"),
    db: Session = Depends(get_db),
) -> IndicatorsResponse:
    """Calculate RSI, MACD, EMAs (9,21,50,200), SMAs (20,50,200), ATR, and Bollinger Bands using Pandas/NumPy."""
    market_service = MarketDataService(db=db)
    ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
    if not ohlc.candles:
        raise HTTPException(status_code=404, detail=f"No candlestick data available for {symbol}")

    return IndicatorsService.compute_all_indicators(
        candles=ohlc.candles,
        symbol=symbol,
        timeframe=timeframe,
        rsi_period=rsi_period,
        macd_fast=macd_fast,
        macd_slow=macd_slow,
        macd_signal=macd_signal,
    )


@router.get("/patterns", response_model=PatternsResponse, summary="Detect Candlestick Patterns")
def get_patterns(
    symbol: str = Query("EUR/USD", description="Symbol name or ticker"),
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D"),
    market: Optional[str] = Query(None, description="Optional market tag"),
    db: Session = Depends(get_db),
) -> PatternsResponse:
    """Identify Doji, Hammer, Inverted Hammer, Bullish/Bearish Engulfing, Morning/Evening Star, Shooting Star."""
    market_service = MarketDataService(db=db)
    ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
    if not ohlc.candles:
        raise HTTPException(status_code=404, detail=f"No candlestick data available for {symbol}")

    return PatternService.detect_patterns(candles=ohlc.candles, symbol=symbol, timeframe=timeframe)


@router.get("/support-resistance", response_model=SupportResistanceResponse, summary="Calculate Support and Resistance Zones")
def get_support_resistance(
    symbol: str = Query("EUR/USD", description="Symbol name or ticker"),
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D"),
    tolerance: float = Query(0.008, ge=0.001, le=0.05, description="Cluster percentage tolerance (default 0.8%)"),
    market: Optional[str] = Query(None, description="Optional market tag"),
    db: Session = Depends(get_db),
) -> SupportResistanceResponse:
    """Detect swing highs/lows and cluster them into horizontal price zones with touch counts and strength ratings."""
    market_service = MarketDataService(db=db)
    ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
    if not ohlc.candles:
        raise HTTPException(status_code=404, detail=f"No candlestick data available for {symbol}")

    return SupportResistanceService.calculate_zones(
        candles=ohlc.candles,
        symbol=symbol,
        timeframe=timeframe,
        tolerance=tolerance,
    )


@router.get("/summary", response_model=AnalysisSummaryResponse, summary="Factual Technical Summary")
def get_analysis_summary(
    symbol: str = Query("EUR/USD", description="Symbol name or ticker"),
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D"),
    market: Optional[str] = Query("FOREX", description="Market category: FOREX, NSE, MCX"),
    db: Session = Depends(get_db),
) -> AnalysisSummaryResponse:
    """Generate a factual, rule-based summary highlighting market regime, indicators, patterns, S/R, and conflicts."""
    market_service = MarketDataService(db=db)
    ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
    if not ohlc.candles:
        raise HTTPException(status_code=404, detail=f"No candlestick data available for {symbol}")

    indicators = IndicatorsService.compute_all_indicators(candles=ohlc.candles, symbol=symbol, timeframe=timeframe)
    patterns = PatternService.detect_patterns(candles=ohlc.candles, symbol=symbol, timeframe=timeframe)
    sr = SupportResistanceService.calculate_zones(candles=ohlc.candles, symbol=symbol, timeframe=timeframe)

    return AnalysisSummaryService.generate_summary(
        symbol=symbol,
        market=market or "MARKET",
        timeframe=timeframe,
        candles=ohlc.candles,
        indicators=indicators,
        patterns=patterns,
        sr=sr,
    )


@router.get("/full", response_model=TechnicalAnalysisFullBundle, summary="Complete Technical Analysis Bundle")
def get_full_analysis(
    symbol: str = Query("EUR/USD", description="Symbol name or ticker"),
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D"),
    market: Optional[str] = Query("FOREX", description="Market category: FOREX, NSE, MCX"),
    rsi_period: int = Query(14, ge=2, le=100),
    macd_fast: int = Query(12, ge=2, le=50),
    macd_slow: int = Query(26, ge=5, le=100),
    macd_signal: int = Query(9, ge=2, le=50),
    tolerance: float = Query(0.008, ge=0.001, le=0.05),
    db: Session = Depends(get_db),
) -> TechnicalAnalysisFullBundle:
    """Unified endpoint returning candles, computed indicators, detected patterns, S/R levels, and summary in 1 call."""
    market_service = MarketDataService(db=db)
    ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
    if not ohlc.candles:
        raise HTTPException(status_code=404, detail=f"No candlestick data available for {symbol}")

    indicators = IndicatorsService.compute_all_indicators(
        candles=ohlc.candles,
        symbol=symbol,
        timeframe=timeframe,
        rsi_period=rsi_period,
        macd_fast=macd_fast,
        macd_slow=macd_slow,
        macd_signal=macd_signal,
    )
    patterns = PatternService.detect_patterns(candles=ohlc.candles, symbol=symbol, timeframe=timeframe)
    sr = SupportResistanceService.calculate_zones(
        candles=ohlc.candles,
        symbol=symbol,
        timeframe=timeframe,
        tolerance=tolerance,
    )
    summary = AnalysisSummaryService.generate_summary(
        symbol=symbol,
        market=market or "MARKET",
        timeframe=timeframe,
        candles=ohlc.candles,
        indicators=indicators,
        patterns=patterns,
        sr=sr,
    )

    return TechnicalAnalysisFullBundle(
        symbol=symbol,
        market=market or "MARKET",
        timeframe=timeframe,
        candles=ohlc.candles,
        indicators=indicators,
        patterns=patterns,
        support_resistance=sr,
        summary=summary,
        is_mock=True,
    )


@router.get("/ai/status", summary="Check AI Provider and Hallucination Defense Status")
def get_ai_status():
    """Returns connectivity status for local Ollama and the deterministic fallback engine."""
    from app.services.ai_provider import ai_service
    return ai_service.get_provider_status()


@router.post("/ai/evaluate", summary="Generate Structured AI Analysis with Hallucination Defense")
def generate_ai_analysis(payload: AIAnalysisRequest, db: Session = Depends(get_db)):
    """
    Generates a structured, evidence-grounded AI analysis of market data and algorithmic signals.
    Employs Hallucination Defense to verify that output values strictly conform to factual data.
    """
    from app.services.ai_provider import ai_service
    from app.services.strategy_engine import StrategyEngine

    symbol = payload.symbol
    market = payload.market
    timeframe = payload.timeframe
    strat_id = payload.strategy_id or "STRAT-MULTI-CONF"

    market_service = MarketDataService(db=db)
    ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
    candles = ohlc.candles
    if not candles:
        raise HTTPException(
            status_code=400,
            detail=f"No candlestick data available for {symbol} ({market})",
        )

    indicators_res = IndicatorsService.compute_all_indicators(candles, symbol=symbol, timeframe=timeframe)
    patterns_res = PatternService.detect_patterns(candles, symbol=symbol, timeframe=timeframe)
    sr_res = SupportResistanceService.calculate_zones(candles, symbol=symbol, timeframe=timeframe)

    strat_signal = StrategyEngine.evaluate_strategy_signal(
        strategy_id=strat_id,
        symbol=symbol,
        market=market,
        timeframe=timeframe,
        candles=candles,
        indicators=indicators_res,
        patterns=patterns_res,
        sr=sr_res,
    )

    current_price = candles[-1].close
    latest_rsi = next((p.value for p in reversed(indicators_res.rsi) if p.value is not None), None)
    latest_macd = next((p for p in reversed(indicators_res.macd) if p.macd is not None and p.signal is not None), None)
    latest_ema_9 = next((p.value for p in reversed(indicators_res.ema_9) if p.value is not None), None)
    latest_ema_21 = next((p.value for p in reversed(indicators_res.ema_21) if p.value is not None), None)
    latest_ema_50 = next((p.value for p in reversed(indicators_res.ema_50) if p.value is not None), None)
    latest_atr = next((p.value for p in reversed(indicators_res.atr) if p.value is not None), None)
    latest_vwap = next((p.value for p in reversed(indicators_res.vwap) if p.value is not None), None) if hasattr(indicators_res, "vwap") and indicators_res.vwap else None

    indicator_dict = {
        "rsi": latest_rsi,
        "macd_line": latest_macd.macd if latest_macd else None,
        "macd_signal": latest_macd.signal if latest_macd else None,
        "macd_histogram": latest_macd.histogram if latest_macd else None,
        "ema_9": latest_ema_9,
        "ema_21": latest_ema_21,
        "ema_50": latest_ema_50,
        "atr": latest_atr,
        "vwap": latest_vwap,
    }

    pattern_names = [p.pattern_name for p in patterns_res.patterns]
    sr_levels = [z.price for z in sr_res.zones]

    analysis = ai_service.analyze_market_setup(
        symbol=symbol,
        market=market,
        timeframe=timeframe,
        current_price=current_price,
        indicators=indicator_dict,
        patterns=pattern_names,
        sr_zones=sr_levels,
        strategy_signal=strat_signal.signal_state,
        data_freshness_seconds=1.2,
    )

    return analysis

