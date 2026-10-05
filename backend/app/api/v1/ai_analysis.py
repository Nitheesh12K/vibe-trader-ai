"""API Router for Structured AI Analysis & Quality Transparency."""
from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.ai_analysis import AIAnalysisResponse, AIAnalysisRequest
from app.services.ai_provider import ai_service
from app.services.market_data_service import MarketDataService
from app.services.indicators_service import IndicatorsService
from app.services.pattern_service import PatternService
from app.services.support_resistance_service import SupportResistanceService
from app.services.strategy_engine import StrategyEngine

router = APIRouter(prefix="/analysis", tags=["AI Analysis Engine"])


@router.get("/status", summary="Check AI Provider and Hallucination Defense Status")
def get_ai_status():
    """Returns connectivity status for local Ollama and the deterministic fallback engine."""
    return ai_service.get_provider_status()


@router.post("/evaluate", response_model=AIAnalysisResponse, summary="Generate Structured AI Analysis")
def generate_ai_analysis(payload: AIAnalysisRequest):
    """
    Generates a structured, evidence-grounded AI analysis of market data and algorithmic signals.
    Employs Hallucination Defense to verify that output values strictly conform to factual data.
    """
    ohlc = MarketDataService.get_ohlc(symbol=payload.symbol, timeframe=payload.timeframe, market=payload.market)
    candles = ohlc.candles
    if not candles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No candlestick data available for {payload.symbol} ({payload.market})",
        )

    indicators_res = IndicatorsService.compute_all_indicators(candles, symbol=payload.symbol, timeframe=payload.timeframe)
    patterns_res = PatternService.detect_patterns(candles, symbol=payload.symbol, timeframe=payload.timeframe)
    sr_res = SupportResistanceService.calculate_levels(candles, symbol=payload.symbol, timeframe=payload.timeframe)

    strat_id = payload.strategy_id or "STRAT-MULTI-CONF"
    strat_signal = StrategyEngine.evaluate_strategy_signal(
        strategy_id=strat_id,
        symbol=payload.symbol,
        market=payload.market,
        timeframe=payload.timeframe,
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
        symbol=payload.symbol,
        market=payload.market,
        timeframe=payload.timeframe,
        current_price=current_price,
        indicators=indicator_dict,
        patterns=pattern_names,
        sr_zones=sr_levels,
        strategy_signal=strat_signal.signal_state,
        data_freshness_seconds=1.2,
    )

    return analysis
