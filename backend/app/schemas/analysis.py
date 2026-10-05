"""Pydantic schemas for Technical Analysis: Indicators, Patterns, Support/Resistance, and Summary."""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.market import OHLCCandle


class IndicatorValuePoint(BaseModel):
    time: int
    value: Optional[float] = None


class MACDPoint(BaseModel):
    time: int
    macd: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None


class BollingerBandPoint(BaseModel):
    time: int
    upper: Optional[float] = None
    middle: Optional[float] = None
    lower: Optional[float] = None
    bandwidth: Optional[float] = None


class IndicatorsResponse(BaseModel):
    symbol: str
    timeframe: str
    is_mock: bool = True
    rsi: List[IndicatorValuePoint]
    macd: List[MACDPoint]
    ema_9: List[IndicatorValuePoint]
    ema_21: List[IndicatorValuePoint]
    ema_50: List[IndicatorValuePoint]
    ema_200: List[IndicatorValuePoint]
    sma_20: List[IndicatorValuePoint]
    sma_50: List[IndicatorValuePoint]
    sma_200: List[IndicatorValuePoint]
    atr: List[IndicatorValuePoint]
    bollinger: List[BollingerBandPoint]
    vwap: List[IndicatorValuePoint] = []
    volume_sma: List[IndicatorValuePoint] = []

    model_config = ConfigDict(from_attributes=True)


class PatternItem(BaseModel):
    pattern_name: str
    time: int
    candle_index: int
    direction: str  # Bullish, Bearish, Neutral
    reliability: str  # High, Medium, Low
    explanation: str

    model_config = ConfigDict(from_attributes=True)


class PatternsResponse(BaseModel):
    symbol: str
    timeframe: str
    total_detected: int
    patterns: List[PatternItem]

    model_config = ConfigDict(from_attributes=True)


class SupportResistanceZone(BaseModel):
    price: float
    zone_type: str  # Support or Resistance
    touches: int
    strength: str  # Strong, Moderate, Minor
    timeframe: str
    min_price: float
    max_price: float
    calculation_method: str = "Swing High/Low Cluster with Tolerance"

    model_config = ConfigDict(from_attributes=True)


class SupportResistanceResponse(BaseModel):
    symbol: str
    timeframe: str
    current_price: float
    zones: List[SupportResistanceZone]

    model_config = ConfigDict(from_attributes=True)


class AnalysisSummaryResponse(BaseModel):
    symbol: str
    market: str
    timeframe: str
    timestamp: str
    data_source: str = "DEMO DATA (Simulated)"
    current_price: float
    regime: str  # Bullish Momentum, Bearish Trend, Range-Bound, Consolidating
    rsi_summary: str
    macd_summary: str
    ma_summary: str
    volatility_summary: str
    patterns_summary: str
    sr_summary: str
    key_takeaways: List[str]
    conflicts: List[str]
    disclaimer: str = (
        "FACTUAL TECHNICAL SUMMARY: Generated from rule-based calculations on simulated demo candles. "
        "Does not constitute financial advice, buy/sell recommendations, or guaranteed market performance."
    )

    model_config = ConfigDict(from_attributes=True)


class TechnicalAnalysisFullBundle(BaseModel):
    symbol: str
    market: str
    timeframe: str
    candles: List[OHLCCandle]
    indicators: IndicatorsResponse
    patterns: PatternsResponse
    support_resistance: SupportResistanceResponse
    summary: AnalysisSummaryResponse
    is_mock: bool = True

    model_config = ConfigDict(from_attributes=True)
