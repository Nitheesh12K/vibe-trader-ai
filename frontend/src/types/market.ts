/**
 * Core type definitions for Vibe Trader AI
 */

export type MarketType = 'FOREX' | 'NSE' | 'MCX';

export interface InstrumentItem {
  symbol: string;
  name: string;
  market: MarketType;
  category: string;
  last_price: number;
  change: number;
  change_percent: number;
  high_24h: number;
  low_24h: number;
  volume: string;
  currency_symbol: string;
  is_mock: boolean;
}

export interface MarketStatusItem {
  market: MarketType;
  label: string;
  status: 'OPEN' | 'CLOSED';
  session_hours: string;
  timezone: string;
  is_demo: boolean;
}

export interface OHLCCandle {
  time: number; // Unix timestamp in seconds for lightweight-charts
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface OHLCResponse {
  symbol: string;
  market: string;
  timeframe: string;
  is_mock: boolean;
  candles: OHLCCandle[];
}

export interface PortfolioSummary {
  total_value: number;
  available_cash: number;
  daily_pnl: number;
  daily_pnl_percent: number;
  open_positions_count: number;
  active_strategies_count: number;
  currency: string;
  is_mock: boolean;
}

export interface ActivityItem {
  id: string;
  symbol: string;
  market: string;
  type: 'PAPER_TRADE' | 'SIGNAL' | 'JOURNAL';
  side: 'BUY' | 'SELL' | 'INFO';
  quantity: number;
  price: number;
  pnl?: number | null;
  status: string;
  timestamp: string;
  is_mock: boolean;
}

export interface AIInsightSummary {
  title: string;
  sentiment: 'Bullish' | 'Bearish' | 'Neutral';
  confidence: number;
  summary: string;
  timestamp: string;
  disclaimer: string;
}

export interface DashboardSummaryResponse {
  portfolio: PortfolioSummary;
  market_statuses: MarketStatusItem[];
  instruments: InstrumentItem[];
  recent_activity: ActivityItem[];
  ai_insight: AIInsightSummary;
  is_demo: boolean;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  timestamp: string;
  environment: string;
  database_connected: boolean;
}

export type NavTabId =
  | 'overview'
  | 'market_watch'
  | 'watchlist'
  | 'technical_analysis'
  | 'buy_approval'
  | 'positions'
  | 'ai_insights'
  | 'strategies'
  | 'strategy_comparison'
  | 'market_replay'
  | 'backtesting'
  | 'paper_trading'
  | 'portfolio'
  | 'performance'
  | 'trade_journal'
  | 'reports'
  | 'data_manager'
  | 'exports'
  | 'alerts'
  | 'audit_trail'
  | 'vibe_intelligence'
  | 'market_data'
  | 'broker_connection'
  | 'system_health'
  | 'risk_management'
  | 'xgboost_research'
  | 'settings';

// ============================================================================
// Phase 2 Database Entity Types
// ============================================================================

export interface UserSettings {
  id: number;
  theme: 'dark' | 'light';
  default_market: 'ALL' | 'FOREX' | 'NSE' | 'MCX';
  default_timeframe: string;
  risk_percentage: number;
  notifications_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserSettingsUpdate {
  theme?: 'dark' | 'light';
  default_market?: 'ALL' | 'FOREX' | 'NSE' | 'MCX';
  default_timeframe?: string;
  risk_percentage?: number;
  notifications_enabled?: boolean;
}

export interface WatchlistItem {
  id: number;
  symbol: string;
  name: string;
  market: MarketType;
  category: string;
  exchange?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface WatchlistCreate {
  symbol: string;
  name: string;
  market: MarketType;
  category?: string;
  exchange?: string;
}

export interface StrategyItem {
  id: number;
  name: string;
  description?: string | null;
  market: string;
  timeframe: string;
  parameters_json: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StrategyCreate {
  name: string;
  description?: string;
  market: string;
  timeframe: string;
  parameters_json: string;
  is_active?: boolean;
}

export interface StrategyUpdate {
  name?: string;
  description?: string;
  market?: string;
  timeframe?: string;
  parameters_json?: string;
  is_active?: boolean;
}

export interface PaperTradeItem {
  id: number;
  symbol: string;
  market: string;
  side: string; // Long or Short
  order_type: string;
  quantity: number;
  entry_price: number;
  stop_loss?: number | null;
  take_profit?: number | null;
  exit_price?: number | null;
  pnl?: number | null;
  status: 'Open' | 'Closed' | 'Cancelled';
  notes?: string | null;
  created_at: string;
  closed_at?: string | null;
}

export interface PaperTradeCreate {
  symbol: string;
  market: string;
  direction: 'Long' | 'Short' | 'BUY' | 'SELL';
  entry_price: number;
  quantity: number;
  stop_loss?: number;
  take_profit?: number;
  notes?: string;
}

export interface PaperTradeUpdate {
  exit_price?: number;
  status?: 'Open' | 'Closed' | 'Cancelled';
  stop_loss?: number;
  take_profit?: number;
  notes?: string;
}

export interface JournalItem {
  id: number;
  trade_id?: number | null;
  symbol?: string | null;
  title: string;
  notes: string;
  lessons_learned?: string | null;
  tags: string;
  created_at: string;
  updated_at: string;
}

export interface JournalCreate {
  trade_id?: number;
  symbol?: string;
  title: string;
  notes: string;
  lessons_learned?: string;
  tags?: string;
}

export interface JournalUpdate {
  trade_id?: number;
  symbol?: string;
  title?: string;
  notes?: string;
  lessons_learned?: string;
  tags?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface IndicatorValuePoint {
  time: number;
  value: number | null;
}

export interface MACDPoint {
  time: number;
  macd: number | null;
  signal: number | null;
  histogram: number | null;
}

export interface BollingerBandPoint {
  time: number;
  upper: number | null;
  middle: number | null;
  lower: number | null;
  bandwidth: number | null;
}

export interface IndicatorsResponse {
  symbol: string;
  timeframe: string;
  is_mock: boolean;
  rsi: IndicatorValuePoint[];
  macd: MACDPoint[];
  ema_9: IndicatorValuePoint[];
  ema_21: IndicatorValuePoint[];
  ema_50: IndicatorValuePoint[];
  ema_200: IndicatorValuePoint[];
  sma_20: IndicatorValuePoint[];
  sma_50: IndicatorValuePoint[];
  sma_200: IndicatorValuePoint[];
  atr: IndicatorValuePoint[];
  bollinger: BollingerBandPoint[];
}

export interface PatternItem {
  pattern_name: string;
  time: number;
  candle_index: number;
  direction: 'Bullish' | 'Bearish' | 'Neutral';
  reliability: 'High' | 'Medium' | 'Low';
  explanation: string;
}

export interface PatternsResponse {
  symbol: string;
  timeframe: string;
  total_detected: number;
  patterns: PatternItem[];
}

export interface SupportResistanceZone {
  price: number;
  zone_type: 'Support' | 'Resistance';
  touches: number;
  strength: 'Strong' | 'Moderate' | 'Minor';
  timeframe: string;
  min_price: number;
  max_price: number;
  calculation_method: string;
}

export interface SupportResistanceResponse {
  symbol: string;
  timeframe: string;
  current_price: number;
  zones: SupportResistanceZone[];
}

export interface AnalysisSummaryResponse {
  symbol: string;
  market: string;
  timeframe: string;
  timestamp: string;
  data_source: string;
  current_price: number;
  regime: string;
  rsi_summary: string;
  macd_summary: string;
  ma_summary: string;
  volatility_summary: string;
  patterns_summary: string;
  sr_summary: string;
  key_takeaways: string[];
  conflicts: string[];
  disclaimer: string;
}

export interface TechnicalAnalysisFullBundle {
  symbol: string;
  market: string;
  timeframe: string;
  candles: OHLCCandle[];
  indicators: IndicatorsResponse;
  patterns: PatternsResponse;
  support_resistance: SupportResistanceResponse;
  summary: AnalysisSummaryResponse;
  is_mock: boolean;
}

// ============================================================================
// Autonomous Trading Workflow Types
// ============================================================================

export interface BuyProposalRead {
  id: number;
  proposal_id: string;
  symbol: string;
  market: string;
  strategy_id?: number | null;
  strategy_name: string;
  current_price: number;
  proposed_entry_price: number;
  proposed_quantity: number;
  stop_loss: number;
  target: number;
  risk_amount: number;
  risk_reward_ratio: number;
  estimated_costs: number;
  matched_conditions: string[];
  unmatched_conditions: string[];
  supporting_indicators: Record<string, any>;
  confidence_score: number;
  confidence_method: string;
  explanation: string;
  uncertainties: string;
  data_source: string;
  data_timestamp: string;
  expires_at: string;
  status: 'PENDING' | 'APPROVED_AND_EXECUTED' | 'REJECTED' | 'EXPIRED' | 'CANCELLED';
  rejection_reason?: string | null;
  risk_check_details?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface BuyProposalApproveRequest {
  notes?: string;
}

export interface BuyProposalRejectRequest {
  reason: string;
}

export interface PositionRead {
  id: number;
  position_id: string;
  proposal_id?: number | null;
  symbol: string;
  market: string;
  side: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  stop_loss: number;
  target: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  highest_price?: number | null;
  status: 'OPEN' | 'CLOSED';
  exit_price?: number | null;
  realized_pnl?: number | null;
  exit_reason?: string | null;
  exit_timestamp?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PositionCloseRequest {
  exit_price?: number;
  reason: string;
}

export interface AutonomousExitPermissionRead {
  id: number;
  is_enabled: boolean;
  allow_stop_loss: boolean;
  allow_take_profit: boolean;
  allow_strategy_exit: boolean;
  allow_max_drawdown: boolean;
  max_position_scope: string;
  emergency_risk_limit_pct: number;
  created_at: string;
  updated_at: string;
}

export interface AutonomousExitPermissionUpdate {
  is_enabled?: boolean;
  allow_stop_loss?: boolean;
  allow_take_profit?: boolean;
  allow_strategy_exit?: boolean;
  allow_max_drawdown?: boolean;
  max_position_scope?: string;
  emergency_risk_limit_pct?: number;
}

export interface RiskSettingsRead {
  id: number;
  simulated_balance: number;
  max_risk_per_trade_pct: number;
  max_daily_loss: number;
  max_open_positions: number;
  max_position_size_pct: number;
  emergency_stop_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RiskSettingsUpdate {
  simulated_balance?: number;
  max_risk_per_trade_pct?: number;
  max_daily_loss?: number;
  max_open_positions?: number;
  max_position_size_pct?: number;
  emergency_stop_active?: boolean;
}

export interface EmergencyStopToggle {
  emergency_stop_active: boolean;
  reason?: string;
}

export interface TradeReportRead {
  id: number;
  position_id?: number | null;
  proposal_id?: number | null;
  symbol: string;
  market: string;
  strategy_name: string;
  side: string;
  quantity: number;
  entry_price: number;
  exit_price: number;
  entry_time: string;
  exit_time: string;
  gross_pnl: number;
  fees: number;
  slippage: number;
  net_pnl: number;
  roi_pct: number;
  exit_reason: string;
  autonomous_exit: boolean;
  buy_approval_timestamp?: string | null;
  risk_check_passed: boolean;
  strategy_rationale?: string | null;
  data_source: string;
  created_at: string;
}

export interface AuditLogRead {
  id: number;
  event_type: string;
  action: string;
  actor: string;
  symbol?: string | null;
  market?: string | null;
  proposal_id?: string | null;
  position_id?: string | null;
  details: Record<string, any>;
  timestamp: string;
}

export interface BacktestRequest {
  symbol: string;
  timeframe: string;
  market: string;
  strategy_name: string;
  initial_capital: number;
  risk_per_trade_pct: number;
  slippage_pct: number;
  commission_per_trade: number;
  dataset_id?: string;
  data_split?: string;
  in_sample_ratio?: number;
  validation_ratio?: number;
  parameters?: Record<string, any>;
}

export interface BacktestTradeResult {
  trade_id: number;
  symbol: string;
  entry_time: number;
  exit_time: number;
  entry_price: number;
  exit_price: number;
  quantity: number;
  gross_pnl: number;
  net_pnl: number;
  roi_pct: number;
  exit_reason: string;
}

export interface BacktestSummaryResponse {
  strategy_name: string;
  symbol: string;
  timeframe: string;
  market: string;
  initial_capital: number;
  final_capital: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  average_win: number;
  average_loss: number;
  profit_factor: number;
  expectancy: number;
  max_drawdown_pct: number;
  net_pnl: number;
  net_roi_pct: number;
  trades: BacktestTradeResult[];
  disclaimer: string;
  strategy_id?: string;
  strategy_version?: string;
  data_split?: string;
  dataset_identity?: string;
  date_range?: Record<string, any>;
  parameters?: Record<string, any>;
  execution_assumptions?: Record<string, any>;
  gross_pnl?: number;
  total_commission?: number;
  total_slippage?: number;
  average_holding_time_seconds?: number;
  sharpe_ratio?: number | null;
  regime_breakdown?: Record<string, any>;
  overtrading_metrics?: Record<string, any>;
  data_source?: string;
  timestamp?: string;
}

export interface MonitoringStatusResponse {
  is_active: boolean;
  monitored_markets: string[];
  total_instruments: number;
  active_strategies_count: number;
  last_scan_timestamp?: string | null;
  pending_proposals_count: number;
  open_positions_count: number;
  emergency_stop_active: boolean;
}

// ============================================================================
// Vibe Intelligence Core Multi-Agent Types
// ============================================================================

export type AgentStatus = 'IDLE' | 'RUNNING' | 'PROCESSING' | 'COMPLETED' | 'BLOCKED' | 'FAILED' | 'TIMED_OUT' | 'UNAVAILABLE' | 'ERROR';

export interface AgentMetadata {
  name: string;
  version: string;
  status: AgentStatus;
  execution_time_ms: number;
  timestamp: string;
  error_detail?: string | null;
  execution_id?: string | null;
  last_run_at?: string | null;
}

export interface PerceptionOutput {
  agent: AgentMetadata;
  symbol: string;
  market: string;
  timeframe: string;
  current_price: number;
  candle_count: number;
  indicators: Record<string, any>;
  detected_patterns: string[];
  support_zones: number[];
  resistance_zones: number[];
  regime: string;
  data_freshness_seconds: number;
  missing_data_detected: boolean;
  data_source: string;
  timestamp: string;
}

export interface ReasoningOutput {
  agent: AgentMetadata;
  symbol: string;
  conforming_evidence: string[];
  conflicting_signals: string[];
  regime: string;
  uncertainty_score: number;
  uncertainty_factors: string[];
  rationale: string;
  is_trade_viable: boolean;
  timestamp: string;
}

export interface MemoryContextOutput {
  agent: AgentMetadata;
  symbol: string;
  similar_setups_found: number;
  regime_historical_win_rate: number;
  past_proposals_summary: Record<string, number>;
  relevant_notes: string[];
  disclaimer: string;
  timestamp: string;
}

export interface LearningSummaryOutput {
  agent: AgentMetadata;
  total_trades_analyzed: int_or_number;
  win_rate: number;
  profit_factor: number;
  expectancy: number;
  average_win: number;
  average_loss: number;
  max_drawdown_pct: number;
  average_slippage: number;
  performance_by_regime: Record<string, Record<string, number>>;
  performance_deterioration_detected: boolean;
  deterioration_reasons: string[];
  candidate_strategy_count: number;
  timestamp: string;
}

type int_or_number = number;

export interface PlanningOutput {
  agent: AgentMetadata;
  strategy_name: string;
  strategy_version: string;
  decision: 'TRADE_PLAN' | 'NO_TRADE';
  direction: 'BUY' | 'NONE';
  proposed_entry_price?: number | null;
  stop_loss?: number | null;
  target?: number | null;
  risk_reward_ratio?: number | null;
  proposed_quantity?: number | null;
  estimated_risk_amount?: number | null;
  estimated_costs?: number | null;
  contingency_conditions: string[];
  explanation: string;
  uncertainties: string;
  timestamp: string;
}

export interface RiskGuardianOutput {
  agent: AgentMetadata;
  verdict: 'PASSED' | 'REJECTED' | 'NO_TRADE';
  checks_summary: Record<string, boolean>;
  blocking_reasons: string[];
  emergency_stop_active: boolean;
  veto_power_active: boolean;
  timestamp: string;
}

export interface TradeManagerOutput {
  agent: AgentMetadata;
  monitored_positions_count: number;
  autonomous_exit_enabled: boolean;
  exit_triggers_checked: number;
  autonomous_exits_executed: number;
  status_message: string;
  timestamp: string;
}

export interface OutcomeEvaluationOutput {
  report_id: number;
  position_id?: string | null;
  symbol: string;
  market: string;
  strategy_name: string;
  planned_entry: number;
  actual_entry: number;
  entry_slippage: number;
  planned_exit: number;
  actual_exit: number;
  exit_slippage: number;
  gross_pnl: number;
  fees: number;
  net_pnl: number;
  realized_vs_expected_behavior: string;
  evaluated_at: string;
}

export interface IntelligenceCycleResponse {
  cycle_id: string;
  symbol: string;
  market: string;
  timeframe: string;
  agent_states: Record<string, AgentStatus>;
  overall_decision: 'BUY_PROPOSED' | 'NO_TRADE' | 'BLOCKED_BY_RISK';
  perception: PerceptionOutput;
  reasoning: ReasoningOutput;
  memory: MemoryContextOutput;
  planning: PlanningOutput;
  risk_guardian: RiskGuardianOutput;
  learning_summary: LearningSummaryOutput;
  trade_manager: TradeManagerOutput;
  execution_timestamp: string;
  cycle_latency_ms?: number;
  llm_calls_count?: number;
  llm_provider_used?: string;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface IntelligenceStatusResponse {
  core_status: 'OPERATIONAL' | 'DEGRADED' | 'HALTED_BY_EMERGENCY';
  agents: Record<string, AgentMetadata>;
  active_regime: string;
  data_freshness_seconds: number;
  emergency_stop_active: boolean;
  autonomous_sell_enabled: boolean;
  total_candidate_strategies: number;
  pending_proposals_count: number;
  open_positions_count: number;
  timestamp: string;
}

export type LifecycleStage =
  | 'CANDIDATE'
  | 'SANDBOX'
  | 'BACKTESTED'
  | 'OUT_OF_SAMPLE_VALIDATED'
  | 'PAPER_TRADING'
  | 'REVIEW'
  | 'ACTIVATED'
  | 'REJECTED'
  | 'ARCHIVED';

export interface StrategyCandidateRead {
  id: number;
  candidate_id: string;
  base_strategy_id?: number | null;
  name: string;
  version: string;
  market: string;
  timeframe: string;
  parameters_json: string;
  rationale: string;
  lifecycle_stage: LifecycleStage;
  validation_metrics: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StrategyCandidateCreate {
  name: string;
  version?: string;
  base_strategy_id?: number | null;
  market: string;
  timeframe: string;
  parameters_json?: string;
  rationale: string;
}

// ============================================================================
// Strategy Framework Types
// ============================================================================

export type SignalState = 'BUY_CANDIDATE' | 'SELL_CANDIDATE' | 'HOLD' | 'NO_TRADE' | 'INVALID_DATA';

export interface StrategyDefinition {
  strategy_code: string;
  name: string;
  family: string;
  description: string;
  indicators_used: string[];
  parameters: Record<string, any>;
  entry_rule_summary: string;
  exit_rule_summary: string;
  lifecycle_status: string;
}

export interface StrategySignalOutput {
  strategy_code: string;
  strategy_name: string;
  signal_state: SignalState;
  symbol: string;
  timeframe: string;
  confidence: number;
  trigger_price: number;
  entry_level?: number | null;
  stop_loss_level?: number | null;
  target_level?: number | null;
  risk_reward_ratio?: number | null;
  reasons: string[];
  caveats: string[];
  generated_at: string;
}

// ============================================================================
// AI Analysis & Hallucination Defense Types
// ============================================================================

export interface AIQualityMetrics {
  input_completeness_pct: number;
  data_freshness_seconds: number;
  structured_schema_valid: boolean;
  model_latency_ms: number;
  unsupported_claims_rejected: number;
  provider_type: 'OLLAMA' | 'FALLBACK_DETERMINISTIC';
}

export interface AIAnalysisResponse {
  symbol: string;
  timeframe: string;
  sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence_score: number;
  market_regime: string;
  primary_rationale: string;
  key_evidence: string[];
  conflicting_signals: string[];
  uncertainty_factors: string[];
  recommended_action: string;
  risk_caveats: string[];
  hallucination_defense_passed: boolean;
  quality_metrics: AIQualityMetrics;
  model_name: string;
  timestamp: string;
}

export interface AIProviderStatus {
  provider_name: string;
  model_name: string;
  host: string;
  is_online: boolean;
  fallback_available: boolean;
  latency_ms: number;
}

// ============================================================================
// Zerodha Kite Broker Types
// ============================================================================

export interface ZerodhaStatusResponse {
  is_connected: boolean;
  broker_name: string;
  user_id?: string | null;
  user_name?: string | null;
  email?: string | null;
  broker_mode: string;
  live_orders_allowed: boolean;
  safety_policy: string;
  auth_time?: string | null;
  available_margin: number;
}

// ============================================================================
// CSV Market Data Types
// ============================================================================

export interface CSVDatasetInfo {
  dataset_id: string;
  symbol: string;
  market: string;
  total_rows: number;
  start_time: string;
  end_time: string;
  is_valid: boolean;
}

export interface CSVUploadResult {
  is_valid: boolean;
  total_rows: number;
  symbol: string;
  errors: string[];
  warnings: string[];
  candles: OHLCCandle[];
}

// ============================================================================
// Product Completion Upgrade Types
// ============================================================================

export interface WatchlistInstrumentItem {
  id: number;
  symbol: string;
  name: string;
  market: MarketType;
  category: string;
  exchange: string;
  order_index: number;
  notes?: string | null;
  group_name: string;
  is_active: boolean;
  created_at: string;
  latest_price?: number | null;
  change_pct?: number | null;
  market_status: string;
  data_source: string;
  data_freshness: string;
  current_signal: string;
  ai_available: boolean;
}

export interface WatchlistGroupItem {
  id: number;
  name: string;
  description?: string | null;
  order_index: number;
  created_at: string;
}

export interface WatchlistCreatePayload {
  symbol: string;
  name: string;
  market: string;
  category?: string;
  exchange?: string;
  order_index?: number;
  notes?: string;
  group_name?: string;
}

export interface WatchlistUpdatePayload {
  name?: string;
  category?: string;
  exchange?: string;
  order_index?: number;
  notes?: string;
  group_name?: string;
  is_active?: boolean;
}

export interface AlertRuleItem {
  id: number;
  alert_id: string;
  symbol: string;
  market: string;
  alert_type: string;
  condition: string;
  threshold?: number | null;
  threshold_str?: string | null;
  cooldown_seconds: number;
  notes?: string | null;
  is_enabled: boolean;
  last_triggered_at?: string | null;
  trigger_count: number;
  created_at: string;
  updated_at: string;
}

export interface AlertEventItem {
  id: number;
  event_id: string;
  alert_rule_id?: number | null;
  alert_type: string;
  symbol?: string | null;
  market: string;
  title: string;
  message: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  details?: Record<string, any>;
  is_read: boolean;
  triggered_at: string;
}

export interface AlertRuleCreatePayload {
  symbol: string;
  market: string;
  alert_type: string;
  condition?: string;
  threshold?: number;
  threshold_str?: string;
  cooldown_seconds?: number;
  notes?: string;
}

export interface StrategyCompareRequestPayload {
  strategy_codes: string[];
  symbol: string;
  market?: string;
  timeframe?: string;
  dataset_id?: string;
  initial_capital?: number;
  commission_pct?: number;
  slippage_pct?: number;
}

export interface StrategyComparisonResultItem {
  strategy_code: string;
  strategy_name: string;
  strategy_version: string;
  dataset_id?: string | null;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  gross_pnl: number;
  net_pnl: number;
  roi_pct: number;
  average_win: number;
  average_loss: number;
  profit_factor: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  expectancy: number;
  average_holding_time: string;
  total_fees: number;
  total_slippage: number;
  equity_curve: Array<{ timestamp: number; equity: number; drawdown_pct: number }>;
  trade_list: Array<Record<string, any>>;
  disclaimer: string;
}

export interface StrategyCompareResponseData {
  symbol: string;
  market: string;
  timeframe: string;
  initial_capital: number;
  compared_at: string;
  strategies: StrategyComparisonResultItem[];
}

export interface ReplaySessionItem {
  id: number;
  session_id: string;
  name: string;
  symbol: string;
  market: string;
  dataset_id?: string | null;
  timeframe: string;
  initial_capital: number;
  virtual_balance: number;
  realized_pnl: number;
  current_index: number;
  total_candles: number;
  status: 'INITIALIZED' | 'PLAYING' | 'PAUSED' | 'COMPLETED';
  created_at: string;
  current_candle?: OHLCCandle | null;
  current_price?: number | null;
  current_signal?: string | null;
  pending_proposal?: Record<string, any> | null;
  open_positions?: Array<Record<string, any>>;
  closed_trades?: Array<Record<string, any>>;
  equity_history?: Array<{ index: number; equity: number; pnl: number }>;
}

export interface ReplayCreatePayload {
  name?: string;
  symbol: string;
  market?: string;
  dataset_id?: string;
  timeframe?: string;
  initial_capital?: number;
}

export interface PerformanceSummaryData {
  mode: string;
  total_equity: number;
  available_cash: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown_pct: number;
  equity_curve: Array<{ time: string; equity: number; pnl: number }>;
  drawdown_curve: Array<{ time: string; drawdown_pct: number }>;
}

export interface PerformanceByStrategyData {
  strategy_name: string;
  total_trades: number;
  win_rate: number;
  realized_pnl: number;
  profit_factor: number;
}

export interface PerformanceBySymbolData {
  symbol: string;
  market: string;
  total_trades: number;
  realized_pnl: number;
  win_rate: number;
}

export interface DatasetItemData {
  dataset_id: string;
  symbol: string;
  market: string;
  timeframe: string;
  total_rows: number;
  row_count?: number;
  start_time?: string | null;
  end_time?: string | null;
  is_valid: boolean;
  source: string;
  created_at?: string | null;
}

export interface DatasetDetailData extends DatasetItemData {
  preview_candles: OHLCCandle[];
}

export interface SubsystemHealth {
  name: string;
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  last_check: string;
  latency_ms: number;
  details: Record<string, any>;
}

export interface SystemHealthFullResponse {
  overall_status: string;
  timestamp: string;
  services: SubsystemHealth[];
  live_broker_orders: string;
  safety_shield: string;
}

export interface ConsolidatedSettingsData {
  user_settings: {
    id: number;
    theme: string;
    default_market: string;
    default_timeframe: string;
    risk_percentage: number;
    notifications_enabled: boolean;
  };
  risk_settings: {
    id: number;
    simulated_balance: number;
    max_risk_per_trade_pct: number;
    max_daily_loss: number;
    max_open_positions: number;
    max_position_size_pct: number;
    emergency_stop_active: boolean;
  };
  autonomous_exit: {
    id: number;
    is_enabled: boolean;
    allow_stop_loss: boolean;
    allow_take_profit: boolean;
    allow_strategy_exit: boolean;
    allow_max_drawdown: boolean;
  };
  ai_status: {
    provider_name: string;
    model_name: string;
    host: string;
    is_online: boolean;
    fallback_available: boolean;
    latency_ms: number;
  };
  broker_status: {
    broker_name: string;
    is_connected: boolean;
    api_key_configured: boolean;
    api_key_masked: string;
    user_id?: string | null;
    user_name?: string | null;
    live_execution_mode: string;
    disclaimer: string;
  };
}

// ============================================================================
// XGBoost Research Engine Interfaces
// ============================================================================

export interface XGBoostHyperparameters {
  n_estimators: number;
  max_depth: number;
  learning_rate: number;
  early_stopping_rounds: number;
  eval_metric: string;
  random_state: number;
}

export interface XGBoostSplitMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc?: number | null;
  pr_auc?: number | null;
  balanced_accuracy: number;
  log_loss: number;
  brier_score: number;
  confusion_matrix: number[][];
}

export interface XGBoostBaselineMetrics {
  majority_class: {
    predicted_class: number;
    accuracy: number;
    brier_score: number;
  };
  momentum: {
    accuracy: number;
    brier_score: number;
  };
}

export interface XGBoostWalkForwardFold {
  fold: number;
  train_start: string;
  train_end: string;
  test_start: string;
  test_end: string;
  train_samples: number;
  test_samples: number;
  test_accuracy: number;
  test_f1: number;
  test_roc_auc?: number | null;
  brier_score: number;
}

export interface XGBoostFeatureImportance {
  feature_name: string;
  gain: number;
  weight: number;
}

export interface XGBoostTrainRequestPayload {
  symbol: string;
  timeframe: string;
  train_ratio?: number;
  val_ratio?: number;
  test_ratio?: number;
  n_estimators?: number;
  max_depth?: number;
  learning_rate?: number;
  early_stopping_rounds?: number;
  cv_folds?: number;
  random_state?: number;
}

export interface XGBoostTrainResponse {
  success: boolean;
  model_id: string;
  experiment_id: string;
  symbol: string;
  timeframe: string;
  metrics: {
    train: XGBoostSplitMetrics;
    val: XGBoostSplitMetrics;
    test: XGBoostSplitMetrics;
  };
  feature_importances: XGBoostFeatureImportance[];
  walk_forward_results: XGBoostWalkForwardFold[];
  baseline_metrics: XGBoostBaselineMetrics;
  message: string;
}

export interface XGBoostModelSummary {
  model_id: string;
  experiment_id: string;
  symbol: string;
  timeframe: string;
  created_at: string;
  status: string;
  test_accuracy: number;
  test_f1: number;
  test_roc_auc?: number | null;
  n_samples: number;
}

export interface XGBoostModelDetail {
  model_id: string;
  experiment_id: string;
  symbol: string;
  timeframe: string;
  created_at: string;
  hyperparameters: XGBoostHyperparameters;
  train_metrics: XGBoostSplitMetrics;
  val_metrics: XGBoostSplitMetrics;
  test_metrics: XGBoostSplitMetrics;
  baseline_metrics: XGBoostBaselineMetrics;
  feature_importances: XGBoostFeatureImportance[];
  walk_forward_results: XGBoostWalkForwardFold[];
  dataset_info: {
    symbol: string;
    timeframe: string;
    total_raw_bars: number;
    usable_bars: number;
    features_count: number;
  };
  status: string;
}

export interface XGBoostPredictRequestPayload {
  model_id?: string;
  symbol: string;
  timeframe?: string;
}

export interface XGBoostPredictResponse {
  model_id: string;
  symbol: string;
  prediction_timestamp: string;
  predicted_direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  probability_up: number;
  probability_down: number;
  confidence: number;
  features_used: Record<string, number>;
  top_contributing_features: {
    feature_name: string;
    value: number;
    contribution_score: number;
  }[];
  rule_agreement?: string | null;
  warning?: string;
}

export interface XGBoostPredictionRecordItem {
  id: number;
  model_id: string;
  symbol: string;
  prediction_timestamp: string;
  predicted_direction: string;
  probability_up: number;
  confidence: number;
  actual_direction?: string | null;
  is_correct?: boolean | null;
  created_at: string;
}

export interface XGBoostSynthesizeRequestPayload {
  symbol: string;
  timeframe?: string;
  model_id?: string;
  rule_signal: 'BUY' | 'SELL' | 'HOLD';
  confidence?: number;
  proposed_reasoning?: string;
}

export interface XGBoostSynthesizeResponse {
  symbol: string;
  timestamp: string;
  rule_signal: string;
  xgboost_prediction: string;
  xgboost_confidence: number;
  probability_up: number;
  divergence_detected: boolean;
  divergence_warning?: string | null;
  unified_confidence: number;
  synthesized_recommendation: string;
  qwen_advisory_text: string;
  risk_disclaimer: string;
}

export interface AIStrategyComparisonRecordItem {
  record_id: string;
  timestamp: number;
  symbol: string;
  market: string;
  timeframe: string;
  deterministic_strategy_name: string;
  deterministic_signal: 'BUY' | 'SELL' | 'HOLD';
  deterministic_confidence: number;
  xgboost_predicted_direction?: 'UP' | 'DOWN' | 'ABSTAIN' | null;
  xgboost_probability?: number | null;
  qwen_synthesized_recommendation?: 'BUY' | 'SELL' | 'HOLD' | null;
  concurrence_status: 'AGREE' | 'DIVERGE' | 'CAUTIONARY';
  divergence_reason?: string | null;
  human_approval_status?: string | null;
  paper_trade_execution_status?: string | null;
  realized_outcome?: string | null;
  realized_pnl?: number | null;
  notes?: string | null;
  created_at?: string | null;
}

export interface AIComparisonSummaryData {
  total_records: number;
  agreement_count: number;
  divergence_count: number;
  cautionary_count: number;
  agreement_rate: number;
  divergence_rate: number;
  cautionary_rate: number;
  agreement_trade_win_rate?: number | null;
  divergence_trade_win_rate?: number | null;
  records: AIStrategyComparisonRecordItem[];
}

export interface ChatSourceItem {
  tool_name: string;
  symbol?: string;
  market?: string;
  timeframe?: string;
  timestamp?: string;
  summary: string;
  data_points: Record<string, any>;
}

export interface ChatMessageRequest {
  session_id: string;
  message: string;
  symbol?: string;
  market?: string;
  timeframe?: string;
}

export interface NewsArticle {
  title: string;
  publisher: string;
  url: string;
  published_at: string;
  retrieved_at: string;
  snippet: string;
  provider: string;
  evidence_type: 'SEARCH_EXCERPT';
}

export interface NewsResult {
  status: 'OK' | 'NO_RECENT_NEWS' | 'PROVIDER_ERROR' | 'CLARIFICATION';
  error_code?: 'RATE_LIMITED' | 'AUTH_REQUIRED' | 'TIMEOUT' | 'CONFIGURATION_ERROR' | 'BAD_RESPONSE' | 'UNAVAILABLE' | null;
  provider: string;
  query: string;
  articles: NewsArticle[];
  checked_at: string;
  cache_hit: boolean;
  context_reused: boolean;
  retrieval_ms: number;
  max_age_hours: number;
  rejected_results: number;
  notice: string;
  summary: string;
  possible_market_implications: string;
  model_metrics?: Record<string, number>;
}

export interface ChatMessageResponse {
  message_id: string;
  session_id: string;
  role: string;
  content: string;
  sources: ChatSourceItem[];
  news?: NewsResult | null;
  symbol_context?: string;
  market_context?: string;
  timeframe_context?: string;
  model_name: string;
  is_fallback: boolean;
  detected_language?: string;
  detected_intent?: string;
  routing_time_ms?: number;
  tool_latency_ms?: number;
  inference_latency_ms?: number;
  total_latency_ms?: number;
  disclaimer: string;
  created_at: string;
}

export interface ChatHistoryItem {
  message_id: string;
  session_id: string;
  role: string;
  content: string;
  sources: ChatSourceItem[];
  news?: NewsResult | null;
  symbol_context?: string;
  market_context?: string;
  timeframe_context?: string;
  model_name?: string;
  is_fallback: boolean;
  detected_language?: string;
  detected_intent?: string;
  routing_time_ms?: number;
  tool_latency_ms?: number;
  inference_latency_ms?: number;
  total_latency_ms?: number;
  created_at: string;
}

export interface AssistantStatusResponse {
  status: 'ONLINE' | 'OFFLINE';
  active_model: string;
  available_models: string[];
  host: string;
  available_tools: string[];
  paper_trading_mode: boolean;
  disclaimer: string;
}

