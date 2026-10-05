"""Pydantic schemas for Deterministic Strategy vs AI/XGBoost Advisory Comparison."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AIStrategyComparisonRecord(BaseModel):
    """Common comparison record between deterministic rule signal and AI/ML advisory."""
    record_id: str = Field(..., description="Unique record identifier")
    timestamp: int = Field(..., description="Candle unix timestamp in seconds")
    symbol: str = Field(..., description="Instrument symbol (e.g. RELIANCE, NIFTY 50)")
    market: str = Field("NSE", description="Market identifier")
    timeframe: str = Field("1D", description="Timeframe")

    deterministic_strategy_name: str = Field(..., description="Name of rule-based strategy evaluated")
    deterministic_signal: str = Field(..., description="Signal from deterministic engine: BUY, SELL, or HOLD")
    deterministic_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence of deterministic rule")

    xgboost_predicted_direction: Optional[str] = Field(None, description="XGBoost direction: UP, DOWN, or ABSTAIN")
    xgboost_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="XGBoost predicted probability")
    qwen_synthesized_recommendation: Optional[str] = Field(None, description="Qwen synthesized verdict: BUY, SELL, HOLD")

    concurrence_status: str = Field(..., description="Concurrence verdict: AGREE, DIVERGE, or CAUTIONARY")
    divergence_reason: Optional[str] = Field(None, description="Detailed explanation if signals diverge")

    human_approval_status: Optional[str] = Field(
        "NOT_REQUIRED",
        description="Human approval stage: NOT_REQUIRED, PENDING, APPROVED, REJECTED"
    )
    paper_trade_execution_status: Optional[str] = Field(
        "NOT_EXECUTED",
        description="Execution outcome: NOT_EXECUTED, EXECUTED, BLOCKED_BY_RISK"
    )
    realized_outcome: Optional[str] = Field(
        None,
        description="Final trade outcome: WIN, LOSS, BREAKEVEN, PENDING"
    )
    realized_pnl: Optional[float] = Field(None, description="Realized PnL in currency units")
    notes: Optional[str] = Field(None, description="Additional context or audit observations")
    created_at: Optional[str] = Field(None, description="ISO timestamp of record creation")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("deterministic_signal")
    @classmethod
    def validate_deterministic_signal(cls, v: str) -> str:
        upper = v.upper()
        if upper not in {"BUY", "SELL", "HOLD"}:
            raise ValueError(f"deterministic_signal must be BUY, SELL, or HOLD, got '{v}'")
        return upper

    @field_validator("concurrence_status")
    @classmethod
    def validate_concurrence_status(cls, v: str) -> str:
        upper = v.upper()
        if upper not in {"AGREE", "DIVERGE", "CAUTIONARY"}:
            raise ValueError(f"concurrence_status must be AGREE, DIVERGE, or CAUTIONARY, got '{v}'")
        return upper


class AIComparisonEvaluationRequest(BaseModel):
    """Request to evaluate and store a new comparison between deterministic and AI signals."""
    symbol: str = Field("RELIANCE", description="Symbol to evaluate")
    market: str = Field("NSE", description="Market identifier")
    timeframe: str = Field("1D", description="Timeframe")
    timestamp: Optional[int] = Field(None, description="Candle timestamp; if omitted, latest candle is used")
    deterministic_strategy_name: str = Field("STRAT-EMA-CROSS", description="Strategy identifier")
    deterministic_signal: str = Field("BUY", description="Deterministic signal: BUY, SELL, or HOLD")
    deterministic_confidence: float = Field(0.75, ge=0.0, le=1.0)
    xgboost_predicted_direction: Optional[str] = Field(None, description="UP, DOWN, or ABSTAIN")
    xgboost_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    qwen_synthesized_recommendation: Optional[str] = Field(None, description="BUY, SELL, or HOLD")
    buy_divergence_prob_threshold: float = Field(0.40, ge=0.0, le=1.0, description="Divergence threshold when deterministic is BUY")
    sell_divergence_prob_threshold: float = Field(0.60, ge=0.0, le=1.0, description="Divergence threshold when deterministic is SELL")
    notes: Optional[str] = Field(None)


class AIComparisonFilter(BaseModel):
    """Query filters for retrieving comparison history."""
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    concurrence_status: Optional[str] = None
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


class AIComparisonSummary(BaseModel):
    """Aggregate metrics and list of comparison records."""
    total_records: int
    agreement_count: int
    divergence_count: int
    cautionary_count: int
    agreement_rate: float
    divergence_rate: float
    cautionary_rate: float
    agreement_trade_win_rate: Optional[float] = None
    divergence_trade_win_rate: Optional[float] = None
    records: List[AIStrategyComparisonRecord]
