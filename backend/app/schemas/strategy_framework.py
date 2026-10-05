"""Pydantic schemas for Rule-Based Strategy Framework."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

SignalState = Literal["BUY_CANDIDATE", "SELL_CANDIDATE", "HOLD", "NO_TRADE", "INVALID_DATA"]

class StrategyDefinition(BaseModel):
    strategy_id: str
    name: str
    version: str = "1.0.0"
    description: str
    market_compatibility: List[str] = ["NSE", "FOREX", "MCX"]
    timeframe_compatibility: List[str] = ["1m", "5m", "15m", "1h", "1D"]
    required_indicators: List[str]
    entry_conditions: List[str]
    exit_conditions: List[str]
    stop_loss_logic: str
    target_logic: str
    trailing_stop_enabled: bool = False
    max_holding_period_candles: int = 50
    required_candle_history: int = 20
    risk_config_reference: str = "Standard 0.5% virtual equity risk"

class StrategySignalOutput(BaseModel):
    strategy_id: str
    strategy_name: str
    symbol: str
    market: str
    timeframe: str
    signal_state: SignalState
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    suggested_entry: Optional[float] = None
    suggested_stop_loss: Optional[float] = None
    suggested_target: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    matched_conditions: List[str] = []
    unmatched_conditions: List[str] = []
    reasons: List[str] = []
    conflicts: List[str] = []
    timestamp: datetime
    is_trade_authorization: bool = False

    model_config = ConfigDict(from_attributes=True)
