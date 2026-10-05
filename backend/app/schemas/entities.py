"""Pydantic schemas for User Settings, Watchlist, Strategies, Paper Trades, and Trade Journal."""
import json
from datetime import datetime
from typing import Optional, List, Any, Dict, Generic, TypeVar
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# User Settings Schemas
# ============================================================================

class UserSettingsBase(BaseModel):
    theme: str = Field("dark", description="UI theme: dark or light")
    default_market: str = Field("ALL", description="Default market view: ALL, FOREX, NSE, or MCX")
    default_timeframe: str = Field("1D", description="Default charting timeframe: 1m, 5m, 15m, 1h, 1D")
    risk_percentage: float = Field(1.0, ge=0.1, le=100.0, description="Risk tolerance percentage per trade (0.1 to 100%)")
    notifications_enabled: bool = Field(True, description="Enable trading alert notifications")

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in {"dark", "light"}:
            raise ValueError("Theme must be either 'dark' or 'light'")
        return v_clean

    @field_validator("default_market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if v_clean not in {"ALL", "FOREX", "NSE", "MCX"}:
            raise ValueError("Default market must be one of: ALL, FOREX, NSE, MCX")
        return v_clean

    @field_validator("default_timeframe")
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        v_clean = v.strip()
        if v_clean not in {"1m", "5m", "15m", "1h", "1D"}:
            raise ValueError("Default timeframe must be one of: 1m, 5m, 15m, 1h, 1D")
        return v_clean


class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    default_market: Optional[str] = None
    default_timeframe: Optional[str] = None
    risk_percentage: Optional[float] = Field(None, ge=0.1, le=100.0)
    notifications_enabled: Optional[bool] = None

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            if v_clean not in {"dark", "light"}:
                raise ValueError("Theme must be either 'dark' or 'light'")
            return v_clean
        return v

    @field_validator("default_market")
    @classmethod
    def validate_market(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().upper()
            if v_clean not in {"ALL", "FOREX", "NSE", "MCX"}:
                raise ValueError("Default market must be one of: ALL, FOREX, NSE, MCX")
            return v_clean
        return v

    @field_validator("default_timeframe")
    @classmethod
    def validate_timeframe(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip()
            if v_clean not in {"1m", "5m", "15m", "1h", "1D"}:
                raise ValueError("Default timeframe must be one of: 1m, 5m, 15m, 1h, 1D")
            return v_clean
        return v


class UserSettingsRead(UserSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Watchlist Schemas
# ============================================================================

class WatchlistGroupRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_default: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: bool = False


class WatchlistCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50, description="Instrument ticker symbol (e.g. RELIANCE, EUR/USD, GOLD)")
    name: str = Field(..., min_length=1, max_length=100, description="Full instrument name")
    market: str = Field(..., description="Market segment: FOREX, NSE, or MCX")
    category: Optional[str] = Field("General", max_length=50)
    exchange: Optional[str] = Field(None, max_length=50)
    order_index: Optional[int] = Field(0, description="Display order index")
    notes: Optional[str] = Field(None, description="Optional user notes")
    group_name: Optional[str] = Field("Default Watchlist", description="Watchlist group name")

    @field_validator("symbol")
    @classmethod
    def sanitize_symbol(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Symbol cannot be empty")
        return clean

    @field_validator("market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in {"FOREX", "NSE", "MCX"}:
            raise ValueError("Market must be one of: FOREX, NSE, MCX")
        return clean


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    exchange: Optional[str] = None
    order_index: Optional[int] = None
    notes: Optional[str] = None
    group_name: Optional[str] = None
    is_active: Optional[bool] = None


class WatchlistRead(BaseModel):
    id: int
    symbol: str
    name: str
    market: str
    category: str
    exchange: Optional[str] = None
    order_index: int = 0
    notes: Optional[str] = None
    group_name: str = "Default Watchlist"
    is_active: bool
    created_at: datetime
    # Enriched dynamic fields
    latest_price: Optional[float] = None
    change_pct: Optional[float] = None
    market_status: Optional[str] = None
    data_source: Optional[str] = None
    data_freshness: Optional[str] = None
    current_signal: Optional[str] = None
    ai_available: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Strategy Schemas
# ============================================================================

class StrategyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Strategy name")
    description: Optional[str] = None
    market: str = Field("ALL", description="Target market: ALL, FOREX, NSE, MCX")
    timeframe: str = Field("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D")
    parameters_json: str = Field("{}", description="Strategy configuration parameters as JSON string")
    is_active: bool = Field(True, description="Enabled status")

    @field_validator("parameters_json")
    @classmethod
    def validate_json_params(cls, v: str) -> str:
        clean = v.strip()
        try:
            parsed = json.loads(clean)
            if not isinstance(parsed, dict):
                raise ValueError("Parameters must be a JSON object (key-value dictionary)")
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON string format in parameters: {exc}")
        return clean


class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    market: Optional[str] = None
    timeframe: Optional[str] = None
    parameters_json: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("parameters_json")
    @classmethod
    def validate_json_params(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            try:
                parsed = json.loads(clean)
                if not isinstance(parsed, dict):
                    raise ValueError("Parameters must be a JSON object (key-value dictionary)")
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON format: {exc}")
            return clean
        return v


class StrategyRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    market: str
    timeframe: str
    parameters_json: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Paper Trade Schemas
# ============================================================================

class PaperTradeCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    market: str = Field(..., description="FOREX, NSE, MCX")
    direction: str = Field("Long", description="Direction: Long or Short (BUY or SELL)")
    entry_price: float = Field(..., gt=0, description="Virtual entry price")
    quantity: float = Field(..., gt=0, description="Virtual quantity")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
    notes: Optional[str] = Field(None, description="Trade rationale notes")

    @field_validator("symbol")
    @classmethod
    def sanitize_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("direction")
    @classmethod
    def normalize_direction(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean in {"Buy", "Long"}:
            return "Long"
        elif clean in {"Sell", "Short"}:
            return "Short"
        raise ValueError("Direction must be 'Long' (or 'BUY') or 'Short' (or 'SELL')")


class PaperTradeUpdate(BaseModel):
    exit_price: Optional[float] = Field(None, gt=0)
    status: Optional[str] = Field(None, description="Open, Closed, or Cancelled")
    stop_loss: Optional[float] = Field(None, gt=0)
    take_profit: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().capitalize()
            if clean not in {"Open", "Closed", "Cancelled"}:
                raise ValueError("Status must be 'Open', 'Closed', or 'Cancelled'")
            return clean
        return v


class PaperTradeRead(BaseModel):
    id: int
    symbol: str
    market: str
    side: str
    order_type: str
    quantity: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    closed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Trade Journal Schemas
# ============================================================================

class JournalEntryCreate(BaseModel):
    trade_id: Optional[int] = Field(None, description="Related paper trade ID")
    symbol: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., min_length=2, max_length=200, description="Entry title")
    notes: str = Field(..., min_length=2, description="Trade reflections & observations")
    lessons_learned: Optional[str] = Field(None, description="Key takeaways or psychological insights")
    tags: Optional[str] = Field("", max_length=200, description="Comma-separated tags")


class JournalEntryUpdate(BaseModel):
    trade_id: Optional[int] = None
    symbol: Optional[str] = None
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    notes: Optional[str] = Field(None, min_length=2)
    lessons_learned: Optional[str] = None
    tags: Optional[str] = None


class JournalEntryRead(BaseModel):
    id: int
    trade_id: Optional[int] = None
    symbol: Optional[str] = None
    title: str
    notes: str
    lessons_learned: Optional[str] = None
    tags: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Generic Paginated Response Helper
# ============================================================================

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Alert & Notification Schemas
# ============================================================================

class AlertRuleCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    market: str = Field("NSE", max_length=50)
    alert_type: str = Field(..., description="PRICE_ABOVE, PRICE_BELOW, RSI_THRESHOLD, EMA_CROSSOVER, STRATEGY_SIGNAL, MARKET_SESSION_OPEN, MARKET_SESSION_CLOSE, RISK_BLOCK, DATA_STALE, AI_UNAVAILABLE, TRADE_EXECUTED, POSITION_CLOSED, DAILY_LOSS_LIMIT")
    condition: str = Field("TRIGGERED", max_length=20)
    threshold: Optional[float] = None
    threshold_str: Optional[str] = None
    cooldown_seconds: int = Field(60, ge=10, le=86400)
    notes: Optional[str] = None


class AlertRuleUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    threshold: Optional[float] = None
    threshold_str: Optional[str] = None
    cooldown_seconds: Optional[int] = None
    notes: Optional[str] = None


class AlertRuleRead(BaseModel):
    id: int
    alert_id: str
    symbol: str
    market: str
    alert_type: str
    condition: str
    threshold: Optional[float] = None
    threshold_str: Optional[str] = None
    is_enabled: bool
    cooldown_seconds: int
    last_triggered_at: Optional[datetime] = None
    trigger_count: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertEventRead(BaseModel):
    id: int
    event_id: str
    alert_rule_id: Optional[int] = None
    alert_type: str
    symbol: Optional[str] = None
    market: Optional[str] = None
    title: str
    message: str
    severity: str
    details_json: str
    is_read: bool
    triggered_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Strategy Comparison Schemas
# ============================================================================

class StrategyCompareRequest(BaseModel):
    strategy_codes: List[str] = Field(..., min_items=1, description="List of strategy codes (e.g. STRAT-EMA-CROSS, STRAT-RSI-REV)")
    symbol: str = Field("RELIANCE", description="Symbol to run comparison backtests on")
    market: str = Field("NSE", description="Market: NSE, FOREX, MCX, or CUSTOM")
    timeframe: str = Field("1D", description="Candle timeframe")
    dataset_id: Optional[str] = None
    initial_capital: float = Field(100000.0, ge=100.0)
    commission_pct: float = Field(0.0003, ge=0.0)
    slippage_pct: float = Field(0.0005, ge=0.0)


class StrategyComparisonItem(BaseModel):
    strategy_code: str
    strategy_name: str
    strategy_version: str
    dataset_id: Optional[str] = None
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    gross_pnl: float
    net_pnl: float
    roi_pct: float
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_pct: float
    expectancy: float
    average_holding_time: str
    total_fees: float
    total_slippage: float
    equity_curve: List[Dict[str, Any]]
    trade_list: List[Dict[str, Any]]
    disclaimer: str = "NEUTRAL FACTUAL METRICS: Historical performance does not guarantee future results."


class StrategyCompareResponse(BaseModel):
    symbol: str
    market: str
    timeframe: str
    initial_capital: float
    compared_at: datetime
    strategies: List[StrategyComparisonItem]


# ============================================================================
# Market Replay Schemas
# ============================================================================

class ReplaySessionCreate(BaseModel):
    name: str = Field("Replay Session", min_length=1, max_length=100)
    symbol: str = Field("RELIANCE")
    market: str = Field("NSE")
    dataset_id: Optional[str] = None
    timeframe: str = Field("1D")
    initial_capital: float = Field(100000.0, ge=1000.0)


class ReplayStepRequest(BaseModel):
    step_count: int = Field(1, ge=1, le=100, description="Number of candles to advance")


class ReplaySessionRead(BaseModel):
    id: int
    session_id: str
    name: str
    symbol: str
    market: str
    dataset_id: Optional[str] = None
    timeframe: str
    initial_capital: float
    virtual_balance: float
    realized_pnl: float
    unrealized_pnl: float = 0.0
    total_candles: int
    current_index: int
    status: str
    speed_ms: int
    current_candle: Optional[Dict[str, Any]] = None
    current_price: Optional[float] = None
    current_signal: Optional[str] = None
    risk_state: Optional[str] = "NORMAL"
    open_positions: List[Dict[str, Any]] = []
    closed_trades: List[Dict[str, Any]] = []
    pending_proposal: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Performance Analytics Schemas
# ============================================================================

class PerformanceSummaryResponse(BaseModel):
    mode: str = "PAPER_TRADING"
    total_equity: float
    available_cash: float
    realized_pnl: float
    unrealized_pnl: float
    total_fees: float
    total_slippage: float
    max_drawdown: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    average_win: float
    average_loss: float
    profit_factor: float
    expectancy: float
    average_holding_time: str
    consecutive_wins: int
    consecutive_losses: int
    average_risk_per_trade: float
    max_exposure: float
    risk_rejections_count: int
    emergency_stop_count: int
    average_position_size: float
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]
    pnl_distribution: List[Dict[str, Any]]


class PerformanceByStrategyItem(BaseModel):
    strategy_name: str
    total_trades: int
    win_rate: float
    profit_factor: float
    net_pnl: float
    fees: float


class PerformanceBySymbolItem(BaseModel):
    symbol: str
    market: str
    total_trades: int
    win_rate: float
    net_pnl: float


# ============================================================================
# System Health Schemas
# ============================================================================

class ServiceHealthItem(BaseModel):
    name: str
    status: str
    last_check: str
    latency_ms: Optional[float] = None
    version_or_model: Optional[str] = None
    details: Optional[str] = None
    is_critical: bool = True


class SystemHealthResponse(BaseModel):
    overall_status: str
    timestamp: str
    services: List[ServiceHealthItem]
    live_broker_orders: str = "DISABLED (HTTP 403)"
    zerodha_status: str = "NOT CONNECTED (READ-ONLY)"


# ============================================================================
# Consolidated Settings Schemas
# ============================================================================

class SettingsAllRead(BaseModel):
    user_settings: Dict[str, Any]
    risk_settings: Dict[str, Any]
    autonomous_exit: Dict[str, Any]
    ai_status: Dict[str, Any]
    broker_status: Dict[str, Any]


class SettingsAllUpdate(BaseModel):
    theme: Optional[str] = None
    default_market: Optional[str] = None
    default_timeframe: Optional[str] = None
    risk_percentage: Optional[float] = None
    notifications_enabled: Optional[bool] = None
    max_risk_per_trade_pct: Optional[float] = None
    max_daily_loss: Optional[float] = None
    max_open_positions: Optional[int] = None
    max_position_size_pct: Optional[float] = None
    emergency_stop_active: Optional[bool] = None
    allow_stop_loss: Optional[bool] = None
    allow_take_profit: Optional[bool] = None
    allow_strategy_exit: Optional[bool] = None
    allow_max_drawdown: Optional[bool] = None

