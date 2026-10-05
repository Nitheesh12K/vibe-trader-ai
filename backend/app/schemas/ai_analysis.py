"""Strict Pydantic schemas for AI Analysis & Quality Transparency."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


MarketState = Literal["TRENDING_BULLISH", "TRENDING_BEARISH", "RANGING", "HIGH_VOLATILITY", "COMPRESSION", "UNCERTAIN"]
AlgorithmSignal = Literal["BUY_CANDIDATE", "SELL_CANDIDATE", "HOLD", "NO_TRADE", "INVALID_DATA"]
SuggestedAction = Literal["EXECUTE_BUY_PROPOSAL", "WAIT", "AVOID", "CONSIDER_EXIT", "NO_ACTION"]
ProviderStatus = Literal["OLLAMA_ONLINE", "DETERMINISTIC_FALLBACK", "OFFLINE"]


class AIAnalysisQualityMetrics(BaseModel):
    input_completeness_pct: float = Field(..., ge=0.0, le=100.0, description="Completeness of input market observations")
    data_freshness_seconds: float = Field(..., ge=0.0, description="Freshness of underlying candle observations")
    structured_output_validity: bool = Field(True, description="Whether model output strictly conformed to Pydantic schema")
    unsupported_claims_rejected: int = Field(0, description="Count of hallucinated claims purged by defense layer")
    ai_provider_status: ProviderStatus
    model_id: str
    analysis_latency_ms: float
    disclaimer: str = (
        "AI EXPLANATION NOTICE: Generated for educational and analytical context only. "
        "AI model cannot authorize or execute live trades. All factual values originate from validated deterministic data."
    )


class AIAnalysisResponse(BaseModel):
    analysis_id: str
    symbol: str
    timeframe: str
    market: str
    market_state: MarketState
    algorithm_signal: AlgorithmSignal
    ai_interpretation: str
    supporting_evidence: List[str] = []
    conflicting_evidence: List[str] = []
    risk_factors: List[str] = []
    missing_information: List[str] = []
    suggested_action: SuggestedAction
    reasoning_summary: str
    data_timestamp: datetime
    model_id: str
    is_trade_authorization: bool = False
    quality_metrics: AIAnalysisQualityMetrics

    model_config = ConfigDict(from_attributes=True)


class AIAnalysisRequest(BaseModel):
    symbol: str = Field("RELIANCE", description="Symbol to analyze")
    market: str = Field("NSE", description="Market category: NSE, FOREX, MCX")
    timeframe: str = Field("1D", description="Candle timeframe: 1m, 5m, 15m, 1h, 1D")
    strategy_id: Optional[str] = Field("STRAT-MULTI-CONF", description="Optional strategy ID to analyze")
