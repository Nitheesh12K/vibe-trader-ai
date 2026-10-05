"""Schemas for Quantitative Research & Walk-Forward Validation Engine."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WalkForwardFoldResult(BaseModel):
    fold_index: int
    train_start: int
    train_end: int
    train_candles: int
    test_start: int
    test_end: int
    test_candles: int
    in_sample_trades: int
    in_sample_win_rate: float
    in_sample_net_pnl: float
    in_sample_sharpe: Optional[float] = None
    in_sample_max_dd: float
    out_of_sample_trades: int
    out_of_sample_win_rate: float
    out_of_sample_net_pnl: float
    out_of_sample_sharpe: Optional[float] = None
    out_of_sample_sortino: Optional[float] = None
    out_of_sample_max_dd: float
    out_of_sample_profit_factor: float


class WalkForwardRequest(BaseModel):
    symbol: str = Field("RELIANCE", description="Symbol to research")
    market: str = Field("NSE", description="Market identifier")
    timeframe: str = Field("1D", description="Timeframe")
    strategy_id: str = Field("STRAT-EMA-CROSS", description="Strategy catalog ID")
    initial_capital: float = Field(100000.0, description="Virtual capital")
    num_folds: int = Field(3, ge=2, le=10, description="Number of chronological walk-forward rolling folds")
    train_ratio: float = Field(0.65, ge=0.4, le=0.85, description="Fraction of each fold allocated to in-sample training")
    slippage_pct: float = Field(0.02, description="Slippage percentage")
    commission_per_trade: float = Field(20.0, description="Commission per trade in INR")


class WalkForwardResponse(BaseModel):
    strategy_id: str
    strategy_name: str
    symbol: str
    timeframe: str
    num_folds: int
    folds: List[WalkForwardFoldResult]
    aggregate_oos_trades: int
    aggregate_oos_win_rate: float
    aggregate_oos_net_pnl: float
    aggregate_oos_roi_pct: float
    aggregate_oos_max_dd: float
    aggregate_oos_sharpe: Optional[float] = None
    aggregate_oos_sortino: Optional[float] = None
    baseline_buy_and_hold_pnl: float
    baseline_buy_and_hold_roi_pct: float
    baseline_no_trade_pnl: float = 0.0
    alpha_over_buy_and_hold: float
    disclaimer: str
    timestamp: str


class SensitivityScenario(BaseModel):
    scenario_name: str
    slippage_pct: float
    commission_per_trade: float
    net_pnl: float
    net_roi_pct: float
    win_rate: float
    total_trades: int
    profit_factor: float
    max_drawdown_pct: float
    sharpe_ratio: Optional[float] = None


class SensitivityAnalysisRequest(BaseModel):
    symbol: str = Field("RELIANCE", description="Symbol")
    market: str = Field("NSE", description="Market identifier")
    timeframe: str = Field("1D", description="Timeframe")
    strategy_id: str = Field("STRAT-EMA-CROSS", description="Strategy catalog ID")
    initial_capital: float = Field(100000.0, description="Virtual capital")


class SensitivityAnalysisResponse(BaseModel):
    strategy_id: str
    strategy_name: str
    symbol: str
    timeframe: str
    scenarios: List[SensitivityScenario]
    robustness_verdict: str
    disclaimer: str
    timestamp: str


class MarketRegimeBreakdown(BaseModel):
    regime_name: str
    candle_count: int
    percentage_of_time: float
    trades_executed: int
    net_pnl: float
    win_rate: float
    profit_factor: float
    description: str


class RegimeAnalysisResponse(BaseModel):
    symbol: str
    timeframe: str
    total_candles: int
    regimes: List[MarketRegimeBreakdown]
    methodology: str
    disclaimer: str
    timestamp: str
