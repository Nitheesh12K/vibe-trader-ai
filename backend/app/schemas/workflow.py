"""Pydantic schemas for Autonomous Trading Workflow:
Proposals, Positions, Risk, Autonomous Exits, Trade Reports, Audit Logs, and Backtesting.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Buy Proposal Schemas
# ============================================================================

class BuyProposalRead(BaseModel):
    id: int
    proposal_id: str
    symbol: str
    market: str
    strategy_id: Optional[int] = None
    strategy_name: str
    current_price: float
    proposed_entry_price: float
    proposed_quantity: float
    stop_loss: float
    target: float
    risk_amount: float
    risk_reward_ratio: float
    estimated_costs: float
    matched_conditions: List[str] = []
    unmatched_conditions: List[str] = []
    supporting_indicators: Dict[str, Any] = {}
    confidence_score: float
    confidence_method: str
    explanation: str
    uncertainties: str
    data_source: str
    data_timestamp: datetime
    expires_at: datetime
    status: str
    rejection_reason: Optional[str] = None
    risk_check_details: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuyProposalApproveRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=500, description="Optional user approval reflection or notes")
    expected_version: Optional[int] = Field(None, description="Optional proposal version to verify integrity")


class BuyProposalRejectRequest(BaseModel):
    reason: str = Field("User rejected trade proposal", max_length=500, description="Reason for rejecting proposal")


# ============================================================================
# Position Schemas
# ============================================================================

class PositionRead(BaseModel):
    id: int
    position_id: str
    proposal_id: Optional[int] = None
    symbol: str
    market: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    stop_loss: float
    target: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    highest_price: Optional[float] = None
    status: str
    exit_price: Optional[float] = None
    realized_pnl: Optional[float] = None
    exit_reason: Optional[str] = None
    exit_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PositionCloseRequest(BaseModel):
    exit_price: Optional[float] = Field(None, description="Optional manual closing price override")
    reason: str = Field("MANUAL_CLOSE", description="Reason for closing position")


# ============================================================================
# Autonomous Exit Permission Schemas
# ============================================================================

class AutonomousExitPermissionRead(BaseModel):
    id: int
    is_enabled: bool
    allow_stop_loss: bool
    allow_take_profit: bool
    allow_strategy_exit: bool
    allow_max_drawdown: bool
    max_position_scope: str
    emergency_risk_limit_pct: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AutonomousExitPermissionUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    allow_stop_loss: Optional[bool] = None
    allow_take_profit: Optional[bool] = None
    allow_strategy_exit: Optional[bool] = None
    allow_max_drawdown: Optional[bool] = None
    max_position_scope: Optional[str] = None
    emergency_risk_limit_pct: Optional[float] = Field(None, ge=0.5, le=50.0)


# ============================================================================
# Risk Settings Schemas
# ============================================================================

class RiskSettingsRead(BaseModel):
    id: int
    simulated_balance: float
    max_risk_per_trade_pct: float
    max_daily_loss: float
    max_open_positions: int
    max_position_size_pct: float
    emergency_stop_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskSettingsUpdate(BaseModel):
    simulated_balance: Optional[float] = Field(None, ge=100.0)
    max_risk_per_trade_pct: Optional[float] = Field(None, ge=0.1, le=20.0)
    max_daily_loss: Optional[float] = Field(None, ge=10.0)
    max_open_positions: Optional[int] = Field(None, ge=1, le=50)
    max_position_size_pct: Optional[float] = Field(None, ge=1.0, le=100.0)
    emergency_stop_active: Optional[bool] = None


class EmergencyStopToggle(BaseModel):
    emergency_stop_active: bool
    reason: Optional[str] = Field("Operator manual emergency intervention", max_length=200)


# ============================================================================
# Trade Report Schemas
# ============================================================================

class TradeReportRead(BaseModel):
    id: int
    position_id: Optional[int] = None
    proposal_id: Optional[int] = None
    symbol: str
    market: str
    strategy_name: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    gross_pnl: float
    fees: float
    slippage: float
    net_pnl: float
    roi_pct: float
    exit_reason: str
    autonomous_exit: bool
    buy_approval_timestamp: Optional[datetime] = None
    risk_check_passed: bool
    strategy_rationale: Optional[str] = None
    data_source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Audit Log Schemas
# ============================================================================

class AuditLogRead(BaseModel):
    id: int
    event_type: str
    action: str
    actor: str
    symbol: Optional[str] = None
    market: Optional[str] = None
    proposal_id: Optional[str] = None
    position_id: Optional[str] = None
    details: Dict[str, Any] = {}
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Backtesting Schemas
# ============================================================================

class BacktestRequest(BaseModel):
    symbol: str = Field("EUR/USD", description="Symbol to backtest")
    timeframe: str = Field("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D")
    market: str = Field("FOREX", description="Market: FOREX, NSE, MCX")
    strategy_name: str = Field("EMA Momentum Trend Following", description="Strategy to run")
    initial_capital: float = Field(100000.0, ge=1000.0)
    risk_per_trade_pct: float = Field(1.5, ge=0.1, le=10.0)
    slippage_pct: float = Field(0.05, ge=0.0, le=2.0)
    commission_per_trade: float = Field(2.0, ge=0.0)
    # Step 5 Validation & Robustness Additions
    dataset_id: Optional[str] = Field(None, description="Optional ID of imported persistent CSV dataset")
    data_split: Optional[str] = Field("FULL", description="Data split: FULL, IN_SAMPLE, VALIDATION, OUT_OF_SAMPLE")
    in_sample_ratio: Optional[float] = Field(0.70, ge=0.1, le=0.9, description="In-sample data ratio")
    validation_ratio: Optional[float] = Field(0.15, ge=0.0, le=0.5, description="Validation data ratio")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional strategy parameter overrides")


class BacktestTradeResult(BaseModel):
    trade_id: int
    symbol: str
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    net_pnl: float
    roi_pct: float
    exit_reason: str


class BacktestSummaryResponse(BaseModel):
    strategy_name: str
    symbol: str
    timeframe: str
    market: str
    initial_capital: float
    final_capital: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    average_win: float
    average_loss: float
    profit_factor: float
    expectancy: float
    max_drawdown_pct: float
    net_pnl: float
    net_roi_pct: float
    trades: List[BacktestTradeResult] = []
    disclaimer: str = (
        "BACKTEST SIMULATION ONLY: Past performance in a synthetic/historical model does NOT guarantee future market returns."
    )
    # Step 5 Quantitative Validation Attributes
    strategy_id: Optional[str] = None
    strategy_version: Optional[str] = "1.0.0"
    data_split: Optional[str] = "FULL"
    dataset_identity: Optional[str] = None
    date_range: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    execution_assumptions: Optional[Dict[str, Any]] = None
    gross_pnl: Optional[float] = 0.0
    total_commission: Optional[float] = 0.0
    total_slippage: Optional[float] = 0.0
    average_holding_time_seconds: Optional[float] = 0.0
    sharpe_ratio: Optional[float] = None
    regime_breakdown: Optional[Dict[str, Any]] = None
    overtrading_metrics: Optional[Dict[str, Any]] = None
    data_source: Optional[str] = "MARKET_FEED"
    timestamp: Optional[str] = None


# ============================================================================
# Continuous Monitoring Schemas
# ============================================================================

class MonitoringStatusResponse(BaseModel):
    is_active: bool
    monitored_markets: List[str]
    total_instruments: int
    active_strategies_count: int
    last_scan_timestamp: Optional[datetime] = None
    pending_proposals_count: int
    open_positions_count: int
    emergency_stop_active: bool
