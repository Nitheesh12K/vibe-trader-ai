"""Pydantic v2 schemas for Vibe Intelligence Core multi-agent architecture."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


AgentStatus = Literal[
    "IDLE",
    "RUNNING",
    "PROCESSING",
    "COMPLETED",
    "BLOCKED",
    "FAILED",
    "TIMED_OUT",
    "UNAVAILABLE",
    "ERROR",
]


class AgentMetadata(BaseModel):
    name: str
    version: str = "1.0.0"
    status: AgentStatus = "IDLE"
    execution_time_ms: float = 0.0
    timestamp: datetime
    error_detail: Optional[str] = None
    execution_id: Optional[str] = None
    last_run_at: Optional[datetime] = None


class PerceptionOutput(BaseModel):
    agent: AgentMetadata
    symbol: str
    market: str
    timeframe: str
    current_price: float
    candle_count: int
    indicators: Dict[str, Any] = {}
    detected_patterns: List[str] = []
    support_zones: List[float] = []
    resistance_zones: List[float] = []
    regime: str
    data_freshness_seconds: float
    missing_data_detected: bool = False
    data_source: str = "DEMO_DATA (Simulated)"
    timestamp: datetime


class ReasoningOutput(BaseModel):
    agent: AgentMetadata
    symbol: str
    conforming_evidence: List[str] = []
    conflicting_signals: List[str] = []
    regime: str
    uncertainty_score: float = 0.0  # 0.0 (certain) to 1.0 (highly uncertain)
    uncertainty_factors: List[str] = []
    rationale: str
    is_trade_viable: bool
    timestamp: datetime


class MemoryContextOutput(BaseModel):
    agent: AgentMetadata
    symbol: str
    similar_setups_found: int = 0
    regime_historical_win_rate: float = 0.0
    past_proposals_summary: Dict[str, int] = {}
    relevant_notes: List[str] = []
    disclaimer: str = (
        "Memory Context: Past outcomes are historical observations and DO NOT guarantee future performance."
    )
    timestamp: datetime


class LearningSummaryOutput(BaseModel):
    agent: AgentMetadata
    total_trades_analyzed: int
    win_rate: float
    profit_factor: float
    expectancy: float
    average_win: float
    average_loss: float
    max_drawdown_pct: float
    average_slippage: float
    performance_by_regime: Dict[str, Dict[str, float]] = {}
    performance_deterioration_detected: bool = False
    deterioration_reasons: List[str] = []
    candidate_strategy_count: int = 0
    timestamp: datetime


class PlanningOutput(BaseModel):
    agent: AgentMetadata
    strategy_name: str
    strategy_version: str
    decision: Literal["TRADE_PLAN", "NO_TRADE"]
    direction: Literal["BUY", "NONE"] = "NONE"
    proposed_entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    proposed_quantity: Optional[float] = None
    estimated_risk_amount: Optional[float] = None
    estimated_costs: Optional[float] = None
    contingency_conditions: List[str] = []
    explanation: str
    uncertainties: str
    timestamp: datetime


class RiskGuardianOutput(BaseModel):
    agent: AgentMetadata
    verdict: Literal["PASSED", "REJECTED", "NO_TRADE"]
    checks_summary: Dict[str, bool] = {}
    blocking_reasons: List[str] = []
    emergency_stop_active: bool = False
    veto_power_active: bool = True
    timestamp: datetime


class TradeManagerOutput(BaseModel):
    agent: AgentMetadata
    monitored_positions_count: int = 0
    autonomous_exit_enabled: bool = False
    exit_triggers_checked: int = 0
    autonomous_exits_executed: int = 0
    status_message: str = "Monitoring active under user permission policy."
    timestamp: datetime


class OutcomeEvaluationOutput(BaseModel):
    report_id: int
    position_id: Optional[str] = None
    symbol: str
    market: str
    strategy_name: str
    planned_entry: float
    actual_entry: float
    entry_slippage: float
    planned_exit: float
    actual_exit: float
    exit_slippage: float
    gross_pnl: float
    fees: float
    net_pnl: float
    realized_vs_expected_behavior: str
    evaluated_at: datetime


class IntelligenceCycleRequest(BaseModel):
    symbol: str = Field("EUR/USD", description="Symbol to evaluate")
    timeframe: str = Field("1D", description="Candle timeframe (1m, 5m, 15m, 1h, 1D)")
    market: str = Field("FOREX", description="Market category: FOREX, NSE, MCX")


class IntelligenceCycleResponse(BaseModel):
    cycle_id: str
    symbol: str
    market: str
    timeframe: str
    agent_states: Dict[str, AgentStatus]
    overall_decision: Literal["BUY_PROPOSED", "NO_TRADE", "BLOCKED_BY_RISK"]
    perception: PerceptionOutput
    reasoning: ReasoningOutput
    memory: MemoryContextOutput
    planning: PlanningOutput
    risk_guardian: RiskGuardianOutput
    learning_summary: LearningSummaryOutput
    trade_manager: TradeManagerOutput
    execution_timestamp: datetime
    # Step 4 Execution & LLM Optimization Metrics
    cycle_latency_ms: Optional[float] = None
    llm_calls_count: Optional[int] = 1
    llm_provider_used: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None


class IntelligenceStatusResponse(BaseModel):
    core_status: str  # OPERATIONAL, DEGRADED, HALTED_BY_EMERGENCY
    agents: Dict[str, AgentMetadata]
    active_regime: str
    data_freshness_seconds: float
    emergency_stop_active: bool
    autonomous_sell_enabled: bool
    total_candidate_strategies: int
    pending_proposals_count: int
    open_positions_count: int
    timestamp: datetime


# ============================================================================
# Controlled Strategy Adaptation Lifecycle Schemas
# ============================================================================

LifecycleStage = Literal[
    "CANDIDATE",
    "SANDBOX",
    "BACKTESTED",
    "OUT_OF_SAMPLE_VALIDATED",
    "PAPER_TRADING",
    "REVIEW",
    "ACTIVATED",
    "REJECTED",
    "ARCHIVED",
]


class StrategyCandidateRead(BaseModel):
    id: int
    candidate_id: str
    base_strategy_id: Optional[int] = None
    name: str
    version: str
    market: str
    timeframe: str
    parameters_json: str
    rationale: str
    lifecycle_stage: LifecycleStage
    validation_metrics: Dict[str, Any] = {}
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrategyCandidateCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    version: str = Field("v1.1.0-rc1", max_length=20)
    base_strategy_id: Optional[int] = None
    market: str = Field("FOREX", max_length=50)
    timeframe: str = Field("1D", max_length=20)
    parameters_json: str = Field("{}", description="Candidate parameter adjustments")
    rationale: str = Field(..., min_length=10, description="Reasoning for candidate adaptation")


class StrategyCandidateAdvanceRequest(BaseModel):
    target_stage: LifecycleStage
    validation_notes: Optional[str] = Field(None, max_length=500)
