"""Pydantic schemas for Market, Health, and Dashboard endpoints."""
from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    app_name: str = Field(..., examples=["Vibe Trader AI"])
    version: str = Field(..., examples=["0.1.0"])
    timestamp: str = Field(..., examples=["2026-09-30T10:00:00Z"])
    environment: str = Field(..., examples=["development"])
    database_connected: bool = Field(..., examples=[True])


class InstrumentItem(BaseModel):
    symbol: str
    name: str
    market: str  # FOREX, NSE, MCX
    category: str  # Currencies, Equities, Commodities, Indices
    last_price: float
    change: float
    change_percent: float
    high_24h: float
    low_24h: float
    volume: str
    currency_symbol: str
    is_mock: bool = True


class MarketStatusItem(BaseModel):
    market: str  # FOREX, NSE, MCX
    label: str
    status: str  # OPEN, CLOSED, PRE_OPEN, POST_CLOSE, HOLIDAY
    session_hours: str
    timezone: str
    is_demo: bool = True
    evaluated_at: Optional[str] = None
    reason: Optional[str] = None
    source: Optional[str] = None

    @property
    def is_open(self) -> bool:
        return self.status == "OPEN"


class OHLCCandle(BaseModel):
    time: int  # Unix timestamp in seconds (TradingView Lightweight Charts format)
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

    def __getitem__(self, item: str):
        return getattr(self, item)

    def get(self, item: str, default=None):
        return getattr(self, item, default)


class OHLCResponse(BaseModel):
    symbol: str
    market: str
    timeframe: str
    is_mock: bool = True
    candles: List[OHLCCandle]


class PortfolioSummary(BaseModel):
    total_value: float
    available_cash: float
    daily_pnl: float
    daily_pnl_percent: float
    open_positions_count: int
    active_strategies_count: int
    currency: str = "USD"
    is_mock: bool = True


class ActivityItem(BaseModel):
    id: str
    symbol: str
    market: str
    type: str  # PAPER_TRADE, SIGNAL, JOURNAL
    side: str  # BUY, SELL, INFO
    quantity: float
    price: float
    pnl: Optional[float] = None
    status: str
    timestamp: str
    is_mock: bool = True


class AIInsightSummary(BaseModel):
    title: str
    sentiment: str  # Bullish, Bearish, Neutral
    confidence: float
    summary: str
    timestamp: str
    disclaimer: str = "DEMO DATA: Educational & research overview only. Never triggers automated or live trades."


class DashboardSummaryResponse(BaseModel):
    portfolio: PortfolioSummary
    market_statuses: List[MarketStatusItem]
    instruments: List[InstrumentItem]
    recent_activity: List[ActivityItem]
    ai_insight: AIInsightSummary
    is_demo: bool = True
