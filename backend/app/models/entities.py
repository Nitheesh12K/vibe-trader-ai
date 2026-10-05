"""SQLAlchemy data models for Vibe Trader AI."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.database.base import Base


def utcnow() -> datetime:
    """Return naive current UTC datetime for SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserSettings(Base):
    """User preferences and configuration."""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    theme = Column(String(50), default="dark")
    default_market = Column(String(50), default="ALL")
    default_timeframe = Column(String(20), default="1D")
    risk_percentage = Column(Float, default=1.0)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class WatchlistGroup(Base):
    """User-created watchlist groups."""
    __tablename__ = "watchlist_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class WatchlistInstrument(Base):
    """Instruments tracked on the user watchlist."""
    __tablename__ = "watchlist_instruments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    market = Column(String(50), nullable=False)  # FOREX, NSE, MCX
    category = Column(String(50), default="General")  # Currencies, Equities, Commodities, Indices
    exchange = Column(String(50), nullable=True)  # e.g., NSE, MCX, FX_CM, etc.
    order_index = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    group_name = Column(String(100), default="Default Watchlist")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint("market", "symbol", name="uq_watchlist_market_symbol"),
    )


class Strategy(Base):
    """Configured trading or analysis strategies."""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    market = Column(String(50), default="ALL")
    timeframe = Column(String(20), default="1D")
    parameters_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)  # Enabled status
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class PaperTrade(Base):
    """Simulated virtual paper trades for research and testing."""
    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    market = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # Long or Short (also supports BUY / SELL)
    order_type = Column(String(20), default="MARKET")
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)
    status = Column(String(20), default="Open")  # Open, Closed, Cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)  # Entry timestamp
    closed_at = Column(DateTime, nullable=True)   # Exit timestamp

    journal_entries = relationship("TradeJournalEntry", back_populates="trade", cascade="all, delete-orphan")


class TradeJournalEntry(Base):
    """Journal notes and reflections tied to trades or general market sessions."""
    __tablename__ = "trade_journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("paper_trades.id", ondelete="SET NULL"), nullable=True)
    symbol = Column(String(50), nullable=True)
    title = Column(String(200), nullable=False)
    notes = Column(Text, nullable=False)  # Trade notes
    lessons_learned = Column(Text, nullable=True)  # Lessons learned
    tags = Column(String(200), default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    trade = relationship("PaperTrade", back_populates="journal_entries")


class BuyProposal(Base):
    """AI-detected BUY proposals awaiting explicit user approval."""
    __tablename__ = "buy_proposals"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(String(64), unique=True, index=True, nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    market = Column(String(50), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True)
    strategy_name = Column(String(100), nullable=False)
    current_price = Column(Float, nullable=False)
    proposed_entry_price = Column(Float, nullable=False)
    proposed_quantity = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target = Column(Float, nullable=False)
    risk_amount = Column(Float, nullable=False)
    risk_reward_ratio = Column(Float, nullable=False)
    estimated_costs = Column(Float, default=0.0)
    matched_conditions_json = Column(Text, default="[]")
    unmatched_conditions_json = Column(Text, default="[]")
    supporting_indicators_json = Column(Text, default="{}")
    confidence_score = Column(Float, default=0.0)
    confidence_method = Column(String(100), default="Multi-Factor Indicator Confluence")
    explanation = Column(Text, nullable=False)
    uncertainties = Column(Text, default="")
    data_source = Column(String(50), default="DEMO_DATA")
    data_timestamp = Column(DateTime, default=utcnow)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(30), default="PENDING")  # PENDING, APPROVED, REJECTED, EXPIRED, EXECUTED, BLOCKED_BY_RISK
    rejection_reason = Column(Text, nullable=True)
    risk_check_details = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Position(Base):
    """Active positions tracked by the background monitoring engine."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(String(64), unique=True, index=True, nullable=False)
    proposal_id = Column(Integer, ForeignKey("buy_proposals.id", ondelete="SET NULL"), nullable=True)
    symbol = Column(String(50), nullable=False, index=True)
    market = Column(String(50), nullable=False)
    side = Column(String(10), default="LONG")
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)
    highest_price = Column(Float, nullable=True)
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED
    exit_price = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True)
    exit_reason = Column(String(100), nullable=True)
    exit_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class AutonomousExitPermission(Base):
    """User pre-authorization settings for autonomous SELL execution."""
    __tablename__ = "autonomous_exit_permissions"

    id = Column(Integer, primary_key=True, index=True)
    is_enabled = Column(Boolean, default=True)
    allow_stop_loss = Column(Boolean, default=True)
    allow_take_profit = Column(Boolean, default=True)
    allow_strategy_exit = Column(Boolean, default=True)
    allow_max_drawdown = Column(Boolean, default=True)
    max_position_scope = Column(String(50), default="ALL")
    emergency_risk_limit_pct = Column(Float, default=5.0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class RiskSettings(Base):
    """System-wide risk management limits and Emergency Stop."""
    __tablename__ = "risk_settings"

    id = Column(Integer, primary_key=True, index=True)
    simulated_balance = Column(Float, default=100000.0)
    max_risk_per_trade_pct = Column(Float, default=2.0)
    max_daily_loss = Column(Float, default=5000.0)
    max_open_positions = Column(Integer, default=5)
    max_position_size_pct = Column(Float, default=20.0)
    emergency_stop_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class TradeReport(Base):
    """Comprehensive post-trade analytics and performance reports."""
    __tablename__ = "trade_reports"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    proposal_id = Column(Integer, ForeignKey("buy_proposals.id", ondelete="SET NULL"), nullable=True)
    symbol = Column(String(50), nullable=False)
    market = Column(String(50), nullable=False)
    strategy_name = Column(String(100), nullable=False)
    side = Column(String(10), default="LONG")
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=False)
    gross_pnl = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    net_pnl = Column(Float, nullable=False)
    roi_pct = Column(Float, nullable=False)
    exit_reason = Column(String(100), nullable=False)
    autonomous_exit = Column(Boolean, default=False)
    buy_approval_timestamp = Column(DateTime, nullable=True)
    risk_check_passed = Column(Boolean, default=True)
    strategy_rationale = Column(Text, nullable=True)
    data_source = Column(String(50), default="DEMO_DATA")
    created_at = Column(DateTime, default=utcnow)


class AuditLog(Base):
    """Append-only audit trail capturing all system events."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    actor = Column(String(50), default="SYSTEM")
    symbol = Column(String(50), nullable=True)
    market = Column(String(50), nullable=True)
    proposal_id = Column(String(64), nullable=True)
    position_id = Column(String(64), nullable=True)
    details_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=utcnow, index=True)


class StrategyCandidate(Base):
    """
    Candidate strategy adaptations proposed by the Learning Agent.
    Strict Lifecycle: CANDIDATE -> SANDBOX -> BACKTESTED -> OUT_OF_SAMPLE_VALIDATED -> PAPER_TRADING -> REVIEW -> ACTIVATED (or REJECTED/ARCHIVED).
    """
    __tablename__ = "strategy_candidates"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(String(64), unique=True, index=True, nullable=False)
    base_strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    version = Column(String(20), default="v1.0.0")
    market = Column(String(50), default="FOREX")
    timeframe = Column(String(20), default="1D")
    parameters_json = Column(Text, default="{}")
    rationale = Column(Text, nullable=False)
    lifecycle_stage = Column(String(40), default="CANDIDATE")
    validation_metrics_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class AgentExecutionCycle(Base):
    """Structured record of multi-agent intelligence evaluation cycles."""
    __tablename__ = "agent_execution_cycles"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(String(64), unique=True, index=True, nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    market = Column(String(50), nullable=False)
    timeframe = Column(String(20), default="1D")
    agent_states_json = Column(Text, default="{}")
    perception_summary_json = Column(Text, default="{}")
    reasoning_summary_json = Column(Text, default="{}")
    memory_summary_json = Column(Text, default="{}")
    planning_summary_json = Column(Text, default="{}")
    risk_verdict = Column(String(30), default="PASSED")  # PASSED, REJECTED, NO_TRADE
    decision = Column(String(50), default="NO_TRADE")     # BUY_PROPOSED, NO_TRADE, EXIT_TRIGGERED, BLOCKED_BY_RISK
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)


class CustomDataset(Base):
    """Uploaded and validated historical CSV dataset for backtesting and analysis."""
    __tablename__ = "custom_datasets"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(64), unique=True, index=True, nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    market = Column(String(50), default="CUSTOM")
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=True)
    timeframe = Column(String(20), default="1D")
    row_count = Column(Integer, nullable=False, default=0)
    start_timestamp = Column(Integer, nullable=True)
    end_timestamp = Column(Integer, nullable=True)
    is_valid = Column(Boolean, default=True)
    candles_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class AlertRule(Base):
    """User-configured price, indicator, strategy, and risk alerts."""
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, index=True, nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    market = Column(String(50), default="NSE")
    alert_type = Column(String(50), nullable=False)  # PRICE_ABOVE, PRICE_BELOW, RSI_THRESHOLD, EMA_CROSSOVER, STRATEGY_SIGNAL, MARKET_SESSION_OPEN, MARKET_SESSION_CLOSE, RISK_BLOCK, DATA_STALE, AI_UNAVAILABLE, TRADE_EXECUTED, POSITION_CLOSED, DAILY_LOSS_LIMIT
    condition = Column(String(20), default="TRIGGERED")
    threshold = Column(Float, nullable=True)
    threshold_str = Column(String(100), nullable=True)
    is_enabled = Column(Boolean, default=True)
    cooldown_seconds = Column(Integer, default=60)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class AlertEvent(Base):
    """Triggered notifications and audit history for alerts."""
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True)
    alert_type = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=True)
    market = Column(String(50), nullable=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="INFO")  # INFO, WARNING, ERROR, CRITICAL
    details_json = Column(Text, default="{}")
    is_read = Column(Boolean, default=False)
    triggered_at = Column(DateTime, default=utcnow, index=True)


class ReplaySession(Base):
    """Historical market replay simulation state."""
    __tablename__ = "replay_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    symbol = Column(String(50), nullable=False)
    market = Column(String(50), default="NSE")
    dataset_id = Column(String(64), nullable=True)
    timeframe = Column(String(20), default="1D")
    initial_capital = Column(Float, default=100000.0)
    virtual_balance = Column(Float, default=100000.0)
    realized_pnl = Column(Float, default=0.0)
    total_candles = Column(Integer, default=0)
    current_index = Column(Integer, default=0)
    status = Column(String(20), default="PAUSED")  # PLAYING, PAUSED, COMPLETED
    speed_ms = Column(Integer, default=1000)
    state_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class PerformanceSnapshot(Base):
    """Persisted performance metrics for paper trading and backtest portfolios."""
    __tablename__ = "performance_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_type = Column(String(20), default="PAPER")  # PAPER or BACKTEST
    reference_id = Column(String(64), nullable=True)
    total_equity = Column(Float, default=100000.0)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    metrics_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utcnow, index=True)


class XGBoostExperiment(Base):
    """XGBoost Quantitative Machine Learning Experiments and Model Artifact Metadata."""
    __tablename__ = "xgboost_experiments"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(64), unique=True, index=True, nullable=False)
    experiment_name = Column(String(100), nullable=False)
    model_version = Column(String(20), default="1.0.0")
    model_type = Column(String(50), default="XGBClassifier")
    symbol = Column(String(50), index=True, nullable=False)
    market = Column(String(50), default="NSE")
    timeframe = Column(String(20), default="1D")
    target_definition = Column(String(100), default="NEXT_BAR_DIRECTION (Close[t+1] > Close[t])")
    feature_version = Column(String(20), default="v1.0")

    training_start_timestamp = Column(Integer, nullable=True)
    training_end_timestamp = Column(Integer, nullable=True)
    validation_start_timestamp = Column(Integer, nullable=True)
    validation_end_timestamp = Column(Integer, nullable=True)
    test_start_timestamp = Column(Integer, nullable=True)
    test_end_timestamp = Column(Integer, nullable=True)

    training_row_count = Column(Integer, default=0)
    validation_row_count = Column(Integer, default=0)
    test_row_count = Column(Integer, default=0)

    class_distribution = Column(Text, default="{}")
    hyperparameters = Column(Text, default="{}")
    random_seed = Column(Integer, default=42)

    baseline_metrics = Column(Text, default="{}")
    out_of_sample_metrics = Column(Text, default="{}")
    walk_forward_metrics = Column(Text, default="[]")
    confusion_matrix = Column(Text, default="{}")
    feature_importance = Column(Text, default="{}")
    calibration_metrics = Column(Text, default="{}")

    artifact_path = Column(String(255), nullable=True)
    artifact_checksum = Column(String(64), nullable=True)
    status = Column(String(30), default="COMPLETED")  # QUEUED, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)


class XGBoostPredictionRecord(Base):
    """Inference predictions generated by XGBoost models with advisory-only labeling."""
    __tablename__ = "xgboost_prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String(64), unique=True, index=True, nullable=False)
    experiment_id = Column(String(64), index=True, nullable=False)
    model_version = Column(String(20), default="1.0.0")
    symbol = Column(String(50), index=True, nullable=False)
    market = Column(String(50), default="NSE")
    timeframe = Column(String(20), default="1D")

    feature_timestamp = Column(Integer, index=True, nullable=False)
    prediction_timestamp = Column(DateTime, default=utcnow, index=True)
    target_timestamp = Column(Integer, nullable=True)

    predicted_class = Column(Integer, nullable=False)  # 1 (Bullish/Up), 0 (Bearish/Down)
    predicted_probability = Column(Float, nullable=False)
    bearish_probability = Column(Float, nullable=False)
    bullish_probability = Column(Float, nullable=False)

    features_snapshot = Column(Text, default="{}")
    data_freshness_status = Column(String(30), default="FRESH")
    advisory_only = Column(Boolean, default=True)

    actual_future_close = Column(Float, nullable=True)
    actual_future_direction = Column(Integer, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    outcome_status = Column(String(30), default="UNVERIFIED_PENDING_BAR")  # UNVERIFIED_PENDING_BAR, CORRECT, INCORRECT

    created_at = Column(DateTime, default=utcnow)


class AIStrategyComparisonRecordModel(Base):
    """Historical concurrence and divergence tracking between deterministic strategies and AI/ML advisory systems."""
    __tablename__ = "ai_strategy_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(Integer, index=True, nullable=False)
    symbol = Column(String(50), index=True, nullable=False)
    market = Column(String(50), default="NSE")
    timeframe = Column(String(20), default="1D")

    deterministic_strategy_name = Column(String(100), nullable=False)
    deterministic_signal = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    deterministic_confidence = Column(Float, default=0.0)

    xgboost_predicted_direction = Column(String(20), nullable=True)  # UP, DOWN, ABSTAIN
    xgboost_probability = Column(Float, nullable=True)
    qwen_synthesized_recommendation = Column(String(20), nullable=True)  # BUY, SELL, HOLD

    concurrence_status = Column(String(20), nullable=False, index=True)  # AGREE, DIVERGE, CAUTIONARY
    divergence_reason = Column(Text, nullable=True)

    human_approval_status = Column(String(30), default="NOT_REQUIRED")  # NOT_REQUIRED, PENDING, APPROVED, REJECTED
    paper_trade_execution_status = Column(String(30), default="NOT_EXECUTED")  # NOT_EXECUTED, EXECUTED, BLOCKED_BY_RISK
    realized_outcome = Column(String(20), nullable=True)  # WIN, LOSS, BREAKEVEN, PENDING
    realized_pnl = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow, index=True)


class ChatMessageRecord(Base):
    """Interactive AI Market Assistant conversation messages and retrieved data citations."""
    __tablename__ = "chat_message_records"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(64), unique=True, index=True, nullable=False)
    session_id = Column(String(64), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    symbol_context = Column(String(50), nullable=True)
    market_context = Column(String(50), nullable=True)
    timeframe_context = Column(String(20), nullable=True)
    sources_json = Column(Text, default="[]")  # Retrieved tool citations with timestamps
    model_name = Column(String(100), nullable=True)
    is_fallback = Column(Boolean, default=False)
    detected_language = Column(String(20), default="english", nullable=True)
    detected_intent = Column(String(50), default="GENERAL_CHAT", nullable=True)
    routing_time_ms = Column(Float, default=0.0, nullable=True)
    tool_latency_ms = Column(Float, default=0.0, nullable=True)
    inference_latency_ms = Column(Float, default=0.0, nullable=True)
    total_latency_ms = Column(Float, default=0.0, nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)

