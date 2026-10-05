/**
 * Centralized API Service for Vibe Trader AI
 * Handles typed communication with the FastAPI backend.
 */
import {
  HealthResponse,
  DashboardSummaryResponse,
  InstrumentItem,
  OHLCResponse,
  UserSettings,
  UserSettingsUpdate,
  WatchlistItem,
  WatchlistCreate,
  StrategyItem,
  StrategyCreate,
  StrategyUpdate,
  PaperTradeItem,
  PaperTradeCreate,
  PaperTradeUpdate,
  JournalItem,
  JournalCreate,
  JournalUpdate,
  PaginatedResponse,
  IndicatorsResponse,
  PatternsResponse,
  SupportResistanceResponse,
  AnalysisSummaryResponse,
  TechnicalAnalysisFullBundle,
  BuyProposalRead,
  PositionRead,
  AutonomousExitPermissionRead,
  AutonomousExitPermissionUpdate,
  RiskSettingsRead,
  RiskSettingsUpdate,
  TradeReportRead,
  AuditLogRead,
  BacktestRequest,
  BacktestSummaryResponse,
  MonitoringStatusResponse,
  IntelligenceStatusResponse,
  IntelligenceCycleResponse,
  LearningSummaryOutput,
  OutcomeEvaluationOutput,
  StrategyCandidateRead,
  StrategyCandidateCreate,
  StrategyDefinition,
  StrategySignalOutput,
  AIAnalysisResponse,
  AIProviderStatus,
  ZerodhaStatusResponse,
  CSVDatasetInfo,
  CSVUploadResult,
  WatchlistInstrumentItem,
  WatchlistGroupItem,
  WatchlistCreatePayload,
  WatchlistUpdatePayload,
  AlertRuleItem,
  AlertEventItem,
  AlertRuleCreatePayload,
  StrategyCompareRequestPayload,
  StrategyCompareResponseData,
  ReplaySessionItem,
  ReplayCreatePayload,
  PerformanceSummaryData,
  PerformanceByStrategyData,
  PerformanceBySymbolData,
  DatasetItemData,
  DatasetDetailData,
  SystemHealthFullResponse,
  ConsolidatedSettingsData,
  XGBoostTrainRequestPayload,
  XGBoostTrainResponse,
  XGBoostModelSummary,
  XGBoostModelDetail,
  XGBoostPredictRequestPayload,
  XGBoostPredictResponse,
  XGBoostPredictionRecordItem,
  XGBoostSynthesizeRequestPayload,
  XGBoostSynthesizeResponse,
  XGBoostSplitMetrics,
  XGBoostBaselineMetrics,
  XGBoostFeatureImportance,
  XGBoostWalkForwardFold,
  AIStrategyComparisonRecordItem,
  AIComparisonSummaryData,
  ChatMessageRequest,
  ChatMessageResponse,
  ChatHistoryItem,
  AssistantStatusResponse,
} from '../types/market';

// Read API base URL from Vite environment or default to local FastAPI host
const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/+$/, '') ||
  'http://127.0.0.1:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Helper request wrapper with standard error handling and headers
   */
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...(options.headers || {}),
        },
      });

      if (!response.ok) {
        let errorDetail = `Request failed with status ${response.status}`;
        try {
          const errorJson = await response.json();
          if (errorJson.message || errorJson.detail) {
            errorDetail = errorJson.message || errorJson.detail;
          }
        } catch {
          // ignore json parse error on non-json error responses
        }
        throw new Error(errorDetail);
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return null as unknown as T;
      }

      return (await response.json()) as T;
    } catch (error: any) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(
          `Unable to connect to backend server at ${this.baseUrl}. Please verify the FastAPI backend is running.`
        );
      }
      throw error;
    }
  }

  // ==========================================================================
  // Health & Market Demo APIs
  // ==========================================================================

  public async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/health');
  }

  public async getDemoDashboard(): Promise<DashboardSummaryResponse> {
    return this.request<DashboardSummaryResponse>('/api/market/demo');
  }

  public async getInstruments(market?: string): Promise<InstrumentItem[]> {
    const query = market && market !== 'ALL' ? `?market=${encodeURIComponent(market)}` : '';
    return this.request<InstrumentItem[]>(`/api/market/instruments${query}`);
  }

  public async getOHLC(symbol: string, timeframe: string = '1D'): Promise<OHLCResponse> {
    const encodedSymbol = encodeURIComponent(symbol);
    return this.request<OHLCResponse>(
      `/api/market/ohlc/${encodedSymbol}?timeframe=${encodeURIComponent(timeframe)}`
    );
  }

  // ==========================================================================
  // User Settings APIs
  // ==========================================================================

  public async getSettings(): Promise<UserSettings> {
    return this.request<UserSettings>('/api/settings');
  }

  public async updateSettings(payload: UserSettingsUpdate): Promise<UserSettings> {
    return this.request<UserSettings>('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  // ==========================================================================
  // Watchlist APIs
  // ==========================================================================

  public async getWatchlist(market?: string): Promise<WatchlistItem[]> {
    const query = market && market !== 'ALL' ? `?market=${encodeURIComponent(market)}` : '';
    return this.request<WatchlistItem[]>(`/api/watchlist${query}`);
  }

  public async addWatchlist(payload: WatchlistCreate): Promise<WatchlistItem> {
    return this.request<WatchlistItem>('/api/watchlist', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async deleteWatchlist(id: number): Promise<void> {
    return this.request<void>(`/api/watchlist/${id}`, {
      method: 'DELETE',
    });
  }

  // ==========================================================================
  // Strategies APIs
  // ==========================================================================

  public async getStrategies(
    market?: string,
    isActive?: boolean,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<StrategyItem>> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (market && market !== 'ALL') params.append('market', market);
    if (isActive !== undefined) params.append('is_active', String(isActive));
    return this.request<PaginatedResponse<StrategyItem>>(`/api/strategies?${params.toString()}`);
  }

  public async getStrategy(id: number): Promise<StrategyItem> {
    return this.request<StrategyItem>(`/api/strategies/${id}`);
  }

  public async createStrategy(payload: StrategyCreate): Promise<StrategyItem> {
    return this.request<StrategyItem>('/api/strategies', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async updateStrategy(id: number, payload: StrategyUpdate): Promise<StrategyItem> {
    return this.request<StrategyItem>(`/api/strategies/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  public async deleteStrategy(id: number): Promise<void> {
    return this.request<void>(`/api/strategies/${id}`, {
      method: 'DELETE',
    });
  }

  // ==========================================================================
  // Paper Trading APIs
  // ==========================================================================

  public async getPaperTrades(
    status?: string,
    market?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<PaperTradeItem>> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (status) params.append('status', status);
    if (market && market !== 'ALL') params.append('market', market);
    return this.request<PaginatedResponse<PaperTradeItem>>(`/api/paper-trades?${params.toString()}`);
  }

  public async getPaperTrade(id: number): Promise<PaperTradeItem> {
    return this.request<PaperTradeItem>(`/api/paper-trades/${id}`);
  }

  public async createPaperTrade(payload: PaperTradeCreate): Promise<PaperTradeItem> {
    return this.request<PaperTradeItem>('/api/paper-trades', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async updatePaperTrade(id: number, payload: PaperTradeUpdate): Promise<PaperTradeItem> {
    return this.request<PaperTradeItem>(`/api/paper-trades/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  public async deletePaperTrade(id: number): Promise<void> {
    return this.request<void>(`/api/paper-trades/${id}`, {
      method: 'DELETE',
    });
  }

  // ==========================================================================
  // Trade Journal APIs
  // ==========================================================================

  public async getJournal(
    symbol?: string,
    tradeId?: number,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<JournalItem>> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (symbol) params.append('symbol', symbol);
    if (tradeId !== undefined) params.append('trade_id', String(tradeId));
    return this.request<PaginatedResponse<JournalItem>>(`/api/journal?${params.toString()}`);
  }

  public async createJournal(payload: JournalCreate): Promise<JournalItem> {
    return this.request<JournalItem>('/api/journal', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async updateJournal(id: number, payload: JournalUpdate): Promise<JournalItem> {
    return this.request<JournalItem>(`/api/journal/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  public async deleteJournal(id: number): Promise<void> {
    return this.request<void>(`/api/journal/${id}`, {
      method: 'DELETE',
    });
  }

  // ==========================================================================
  // Technical Analysis APIs
  // ==========================================================================

  public async getTechnicalAnalysisBundle(
    symbol: string,
    timeframe: string = '1D',
    market: string = 'FOREX',
    options?: {
      rsiPeriod?: number;
      macdFast?: number;
      macdSlow?: number;
      macdSignal?: number;
      tolerance?: number;
    }
  ): Promise<TechnicalAnalysisFullBundle> {
    const params = new URLSearchParams({
      symbol,
      timeframe,
      market,
    });
    if (options?.rsiPeriod) params.append('rsi_period', String(options.rsiPeriod));
    if (options?.macdFast) params.append('macd_fast', String(options.macdFast));
    if (options?.macdSlow) params.append('macd_slow', String(options.macdSlow));
    if (options?.macdSignal) params.append('macd_signal', String(options.macdSignal));
    if (options?.tolerance) params.append('tolerance', String(options.tolerance));

    return this.request<TechnicalAnalysisFullBundle>(`/api/analysis/full?${params.toString()}`);
  }

  public async getIndicators(
    symbol: string,
    timeframe: string = '1D',
    market?: string,
    options?: {
      rsiPeriod?: number;
      macdFast?: number;
      macdSlow?: number;
      macdSignal?: number;
    }
  ): Promise<IndicatorsResponse> {
    const params = new URLSearchParams({ symbol, timeframe });
    if (market) params.append('market', market);
    if (options?.rsiPeriod) params.append('rsi_period', String(options.rsiPeriod));
    if (options?.macdFast) params.append('macd_fast', String(options.macdFast));
    if (options?.macdSlow) params.append('macd_slow', String(options.macdSlow));
    if (options?.macdSignal) params.append('macd_signal', String(options.macdSignal));

    return this.request<IndicatorsResponse>(`/api/analysis/indicators?${params.toString()}`);
  }

  public async getPatterns(
    symbol: string,
    timeframe: string = '1D',
    market?: string
  ): Promise<PatternsResponse> {
    const params = new URLSearchParams({ symbol, timeframe });
    if (market) params.append('market', market);
    return this.request<PatternsResponse>(`/api/analysis/patterns?${params.toString()}`);
  }

  public async getSupportResistance(
    symbol: string,
    timeframe: string = '1D',
    tolerance: number = 0.008
  ): Promise<SupportResistanceResponse> {
    const params = new URLSearchParams({
      symbol,
      timeframe,
      tolerance: String(tolerance),
    });
    return this.request<SupportResistanceResponse>(`/api/analysis/support-resistance?${params.toString()}`);
  }

  public async getAnalysisSummary(
    symbol: string,
    timeframe: string = '1D',
    market: string = 'FOREX'
  ): Promise<AnalysisSummaryResponse> {
    const params = new URLSearchParams({ symbol, timeframe, market });
    return this.request<AnalysisSummaryResponse>(`/api/analysis/summary?${params.toString()}`);
  }

  // ==========================================================================
  // Autonomous Workflow APIs: Proposals, Positions, Risk, Reports, Backtesting
  // ==========================================================================

  // --- 1. BUY Proposals & Approval Center ---
  public async getProposals(status?: string, symbol?: string): Promise<BuyProposalRead[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (symbol) params.append('symbol', symbol);
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<BuyProposalRead[]>(`/api/proposals${query}`);
  }

  public async getProposal(proposalId: string): Promise<BuyProposalRead> {
    return this.request<BuyProposalRead>(`/api/proposals/${proposalId}`);
  }

  public async approveProposal(
    proposalId: string,
    notes?: string
  ): Promise<{ status: string; proposal_id: string; position_id: string; fill_price: number; quantity: number; message: string }> {
    return this.request(`/api/proposals/${proposalId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ notes: notes || '' }),
    });
  }

  public async rejectProposal(
    proposalId: string,
    reason: string
  ): Promise<{ status: string; proposal_id: string; rejection_reason: string; message: string }> {
    return this.request(`/api/proposals/${proposalId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  public async scanAndGenerateProposal(
    symbol: string = 'EUR/USD',
    timeframe: string = '1D',
    market: string = 'FOREX'
  ): Promise<{ opportunity_detected: boolean; proposal?: BuyProposalRead; message?: string }> {
    const params = new URLSearchParams({ symbol, timeframe, market });
    return this.request(`/api/proposals/scan-and-generate?${params.toString()}`, {
      method: 'POST',
    });
  }

  // --- 2. Open Positions & Exit Monitoring ---
  public async getPositions(status?: 'OPEN' | 'CLOSED', symbol?: string): Promise<PositionRead[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (symbol) params.append('symbol', symbol);
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<PositionRead[]>(`/api/positions${query}`);
  }

  public async getPosition(positionId: string): Promise<PositionRead> {
    return this.request<PositionRead>(`/api/positions/${positionId}`);
  }

  public async closePosition(
    positionId: string,
    reason: string = 'MANUAL_CLOSE',
    exitPrice?: number
  ): Promise<{ status: string; position_id: string; realized_pnl: number; message: string }> {
    return this.request(`/api/positions/${positionId}/close`, {
      method: 'POST',
      body: JSON.stringify({ reason, exit_price: exitPrice }),
    });
  }

  // --- 3. Autonomous Exit Permissions ---
  public async getAutonomousExitPermissions(): Promise<AutonomousExitPermissionRead> {
    return this.request<AutonomousExitPermissionRead>('/api/autonomous-exit/permissions');
  }

  public async updateAutonomousExitPermissions(
    data: AutonomousExitPermissionUpdate
  ): Promise<AutonomousExitPermissionRead> {
    return this.request<AutonomousExitPermissionRead>('/api/autonomous-exit/permissions', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // --- 4. Risk Management & Emergency Stop ---
  public async getRiskSettings(): Promise<RiskSettingsRead> {
    return this.request<RiskSettingsRead>('/api/risk/settings');
  }

  public async updateRiskSettings(data: RiskSettingsUpdate): Promise<RiskSettingsRead> {
    return this.request<RiskSettingsRead>('/api/risk/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  public async toggleEmergencyStop(
    active: boolean,
    reason: string = 'User manual emergency intervention'
  ): Promise<RiskSettingsRead> {
    return this.request<RiskSettingsRead>('/api/risk/emergency-stop', {
      method: 'POST',
      body: JSON.stringify({ emergency_stop_active: active, reason }),
    });
  }

  // --- 5. Post-Trade Reports ---
  public async getTradeReports(limit: number = 50): Promise<TradeReportRead[]> {
    return this.request<TradeReportRead[]>(`/api/reports?limit=${limit}`);
  }

  public async getTradeReport(reportId: number): Promise<TradeReportRead> {
    return this.request<TradeReportRead>(`/api/reports/${reportId}`);
  }

  // --- 6. Append-Only Audit Trail ---
  public async getAuditLogs(
    eventType?: string,
    symbol?: string,
    limit: number = 100
  ): Promise<AuditLogRead[]> {
    const params = new URLSearchParams();
    if (eventType) params.append('event_type', eventType);
    if (symbol) params.append('symbol', symbol);
    params.append('limit', String(limit));
    return this.request<AuditLogRead[]>(`/api/audit-logs?${params.toString()}`);
  }

  // --- 7. Quantitative Backtesting ---
  public async runBacktest(req: BacktestRequest): Promise<BacktestSummaryResponse> {
    return this.request<BacktestSummaryResponse>('/api/backtesting/run', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  // --- 8. Continuous Market Monitoring ---
  public async getMonitoringStatus(): Promise<MonitoringStatusResponse> {
    return this.request<MonitoringStatusResponse>('/api/monitoring/status');
  }

  public async triggerMonitoringScan(): Promise<{ status: string; scanned_symbols: number; new_proposals: number; updated_positions: number }> {
    return this.request('/api/monitoring/scan', {
      method: 'POST',
    });
  }

  // --- 9. Vibe Intelligence Core Multi-Agent Platform ---
  public async getIntelligenceStatus(): Promise<IntelligenceStatusResponse> {
    return this.request<IntelligenceStatusResponse>('/api/intelligence/status');
  }

  public async runIntelligenceCycle(
    symbol: string = 'EUR/USD',
    timeframe: string = '1D',
    market: string = 'FOREX'
  ): Promise<IntelligenceCycleResponse> {
    return this.request<IntelligenceCycleResponse>('/api/intelligence/cycle', {
      method: 'POST',
      body: JSON.stringify({ symbol, timeframe, market }),
    });
  }

  public async getLearningSummary(): Promise<LearningSummaryOutput> {
    return this.request<LearningSummaryOutput>('/api/intelligence/learning/summary');
  }

  public async evaluateOutcome(reportId: number): Promise<OutcomeEvaluationOutput> {
    return this.request<OutcomeEvaluationOutput>(`/api/intelligence/evaluate-outcome/${reportId}`, {
      method: 'POST',
    });
  }

  public async getStrategyCandidates(): Promise<StrategyCandidateRead[]> {
    return this.request<StrategyCandidateRead[]>('/api/intelligence/strategies/candidates');
  }

  public async createStrategyCandidate(candidate: StrategyCandidateCreate): Promise<StrategyCandidateRead> {
    return this.request<StrategyCandidateRead>('/api/intelligence/strategies/candidates', {
      method: 'POST',
      body: JSON.stringify(candidate),
    });
  }

  public async advanceStrategyCandidate(
    candidateId: number,
    targetStage: string,
    validationNotes?: string
  ): Promise<StrategyCandidateRead> {
    return this.request<StrategyCandidateRead>(`/api/intelligence/strategies/candidates/${candidateId}/advance`, {
      method: 'POST',
      body: JSON.stringify({ target_stage: targetStage, validation_notes: validationNotes }),
    });
  }

  public async activateStrategyCandidate(candidateId: number): Promise<StrategyCandidateRead> {
    return this.request<StrategyCandidateRead>(`/api/intelligence/strategies/candidates/${candidateId}/activate`, {
      method: 'POST',
    });
  }

  // --- 10. Strategy Catalogue & Signal Evaluation ---
  public async getStrategyCatalogue(): Promise<{ strategies: StrategyDefinition[]; total_strategies: number }> {
    return this.request('/api/strategies/catalogue/all');
  }

  public async evaluateStrategySignal(
    strategyCode: string,
    payload: { symbol: string; timeframe?: string; custom_params?: Record<string, any> }
  ): Promise<StrategySignalOutput> {
    return this.request<StrategySignalOutput>(`/api/strategies/${strategyCode}/evaluate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // --- 11. AI Analysis & Hallucination Defense ---
  public async getAIStatus(): Promise<AIProviderStatus> {
    return this.request<AIProviderStatus>('/api/analysis/ai/status');
  }

  public async evaluateAIAnalysis(payload: {
    symbol: string;
    timeframe?: string;
    market?: string;
    include_patterns?: boolean;
  }): Promise<AIAnalysisResponse> {
    return this.request<AIAnalysisResponse>('/api/analysis/ai/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // --- 12. Zerodha Kite Connect Free Integration ---
  public async getZerodhaStatus(): Promise<ZerodhaStatusResponse> {
    return this.request<ZerodhaStatusResponse>('/api/broker/zerodha/status');
  }

  public async getZerodhaLoginUrl(): Promise<{ login_url: string; status: string; instructions: string }> {
    return this.request('/api/broker/zerodha/login-url');
  }

  public async disconnectZerodha(): Promise<{ status: string; message: string }> {
    return this.request('/api/broker/zerodha/disconnect', {
      method: 'POST',
    });
  }

  public async submitZerodhaLiveOrder(order: { symbol: string; quantity: number; transaction_type?: string }): Promise<any> {
    return this.request('/api/broker/zerodha/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    });
  }

  // --- 13. CSV Market Data Provider ---
  public async uploadCSV(csvContent: string, symbol?: string, market?: string): Promise<CSVUploadResult> {
    return this.request<CSVUploadResult>('/api/market/csv/upload', {
      method: 'POST',
      body: JSON.stringify({ csv_content: csvContent, symbol, market }),
    });
  }

  public async getCSVDatasets(): Promise<{ datasets: CSVDatasetInfo[] }> {
    return this.request('/api/market/csv/datasets');
  }

  // --- 14. Risk Defaults Demo Reset (₹2,000 / 0.5% max risk) ---
  public async resetRiskDefaults(): Promise<RiskSettingsRead> {
    return this.request<RiskSettingsRead>('/api/risk/reset-defaults', {
      method: 'POST',
    });
  }

  // --- 15. Watchlist Management ---
  public async getWatchlists(params?: { market?: string; group?: string }): Promise<WatchlistInstrumentItem[]> {
    const q = new URLSearchParams();
    if (params?.market) q.append('market', params.market);
    if (params?.group) q.append('group', params.group);
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return this.request<WatchlistInstrumentItem[]>(`/api/watchlists${queryStr}`);
  }

  public async getWatchlistGroups(): Promise<WatchlistGroupItem[]> {
    return this.request<WatchlistGroupItem[]>('/api/watchlists/groups');
  }

  public async addToWatchlist(payload: WatchlistCreatePayload): Promise<WatchlistInstrumentItem> {
    return this.request<WatchlistInstrumentItem>('/api/watchlist', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async updateWatchlistItem(id: number, payload: WatchlistUpdatePayload): Promise<WatchlistInstrumentItem> {
    return this.request<WatchlistInstrumentItem>(`/api/watchlist/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  public async deleteWatchlistItem(id: number): Promise<void> {
    return this.request<void>(`/api/watchlist/${id}`, {
      method: 'DELETE',
    });
  }

  // --- 16. Alert & Notification System ---
  public async getAlertRules(symbol?: string): Promise<AlertRuleItem[]> {
    const query = symbol ? `?symbol=${encodeURIComponent(symbol)}` : '';
    return this.request<AlertRuleItem[]>(`/api/alerts${query}`);
  }

  public async createAlertRule(payload: AlertRuleCreatePayload): Promise<AlertRuleItem> {
    return this.request<AlertRuleItem>('/api/alerts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async deleteAlertRule(id: string | number): Promise<void> {
    return this.request<void>(`/api/alerts/${id}`, {
      method: 'DELETE',
    });
  }

  public async toggleAlertRule(id: string | number): Promise<AlertRuleItem> {
    return this.request<AlertRuleItem>(`/api/alerts/${id}/toggle`, {
      method: 'PATCH',
    });
  }

  public async checkAlerts(): Promise<AlertEventItem[]> {
    return this.request<AlertEventItem[]>('/api/alerts/check', {
      method: 'POST',
    });
  }

  public async getAlertEvents(unreadOnly = false): Promise<AlertEventItem[]> {
    const query = unreadOnly ? '?unread_only=true' : '';
    return this.request<AlertEventItem[]>(`/api/alerts/events${query}`);
  }

  public async markAlertEventRead(eventId: string): Promise<void> {
    return this.request<void>(`/api/alerts/events/${eventId}/read`, {
      method: 'POST',
    });
  }

  public async clearAlertEvents(): Promise<{ message: string }> {
    return this.request('/api/alerts/events/clear', {
      method: 'POST',
    });
  }

  // --- 17. Multi-Strategy Comparison ---
  public async compareStrategies(payload: StrategyCompareRequestPayload): Promise<StrategyCompareResponseData> {
    return this.request<StrategyCompareResponseData>('/api/strategies/compare', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // --- 18. Market Replay Mode ---
  public async getReplaySessions(): Promise<ReplaySessionItem[]> {
    return this.request<ReplaySessionItem[]>('/api/replay/sessions');
  }

  public async createReplaySession(payload: ReplayCreatePayload): Promise<ReplaySessionItem> {
    return this.request<ReplaySessionItem>('/api/replay/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async getReplaySession(sessionId: string): Promise<ReplaySessionItem> {
    return this.request<ReplaySessionItem>(`/api/replay/sessions/${sessionId}`);
  }

  public async stepReplaySession(sessionId: string, stepCount = 1): Promise<ReplaySessionItem> {
    return this.request<ReplaySessionItem>(`/api/replay/sessions/${sessionId}/step`, {
      method: 'POST',
      body: JSON.stringify({ step_count: stepCount }),
    });
  }

  public async playReplaySession(sessionId: string): Promise<{ status: string; session_id: string }> {
    return this.request(`/api/replay/sessions/${sessionId}/play`, {
      method: 'POST',
    });
  }

  public async pauseReplaySession(sessionId: string): Promise<{ status: string; session_id: string }> {
    return this.request(`/api/replay/sessions/${sessionId}/pause`, {
      method: 'POST',
    });
  }

  public async resetReplaySession(sessionId: string): Promise<ReplaySessionItem> {
    return this.request<ReplaySessionItem>(`/api/replay/sessions/${sessionId}/reset`, {
      method: 'POST',
    });
  }

  public async approveReplayProposal(sessionId: string, proposalId: string): Promise<any> {
    return this.request(`/api/replay/sessions/${sessionId}/approve?proposal_id=${encodeURIComponent(proposalId)}`, {
      method: 'POST',
    });
  }

  public async closeReplayPosition(sessionId: string, positionId: string): Promise<any> {
    return this.request(`/api/replay/sessions/${sessionId}/close-position?position_id=${encodeURIComponent(positionId)}`, {
      method: 'POST',
    });
  }

  // --- 19. Performance Analytics ---
  public async getPerformanceSummary(): Promise<PerformanceSummaryData> {
    return this.request<PerformanceSummaryData>('/api/performance/summary');
  }

  public async getPerformanceByStrategy(): Promise<PerformanceByStrategyData[]> {
    return this.request<PerformanceByStrategyData[]>('/api/performance/by-strategy');
  }

  public async getPerformanceBySymbol(): Promise<PerformanceBySymbolData[]> {
    return this.request<PerformanceBySymbolData[]>('/api/performance/by-symbol');
  }

  // --- 20. Data Manager ---
  public async getDatasets(): Promise<{ datasets: DatasetItemData[]; total_datasets: number }> {
    return this.request('/api/datasets');
  }

  public async getDatasetDetail(datasetId: string): Promise<DatasetDetailData> {
    return this.request<DatasetDetailData>(`/api/datasets/${datasetId}`);
  }

  public async deleteDataset(datasetId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/datasets/${datasetId}`, {
      method: 'DELETE',
    });
  }

  public async uploadDatasetFile(formData: FormData): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/datasets/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to upload dataset.');
    }
    return res.json();
  }

  // --- 21. Report Exports ---
  public getExportUrl(reportType: string, format: 'csv' | 'json'): string {
    return `${this.baseUrl}/api/exports/${reportType}?format=${format}`;
  }

  public async exportReport(reportType: string, format: 'csv' | 'json'): Promise<any> {
    const url = this.getExportUrl(reportType, format);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Export failed: ${res.statusText}`);
    if (format === 'json') return res.json();
    return res.text();
  }

  // --- 22. System Health Diagnostics ---
  public async getSystemHealth(): Promise<SystemHealthFullResponse> {
    return this.request<SystemHealthFullResponse>('/api/system/health');
  }

  // --- 23. Consolidated Settings Center ---
  public async getConsolidatedSettings(): Promise<ConsolidatedSettingsData> {
    return this.request<ConsolidatedSettingsData>('/api/settings/all');
  }

  public async updateConsolidatedSettings(payload: Record<string, any>): Promise<ConsolidatedSettingsData> {
    return this.request<ConsolidatedSettingsData>('/api/settings/all', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  // --- 24. XGBoost Quantitative Research Engine ---
  public async trainXGBoost(payload: XGBoostTrainRequestPayload): Promise<XGBoostTrainResponse> {
    return this.request<XGBoostTrainResponse>('/api/xgboost/train', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async getXGBoostModels(symbol?: string): Promise<XGBoostModelSummary[]> {
    const q = symbol ? `?symbol=${encodeURIComponent(symbol)}` : '';
    const res = await this.request<any[]>(`/api/xgboost/models${q}`);
    const items = Array.isArray(res) ? res : [];
    return items.map((m: any) => ({
      ...m,
      model_id: m.model_id,
      experiment_id: m.experiment_id || m.model_id,
      symbol: m.symbol,
      timeframe: m.timeframe,
      created_at: m.created_at,
      status: m.status || 'COMPLETED',
      test_accuracy: m.test_accuracy ?? m.out_of_sample_accuracy ?? 0,
      test_f1: m.test_f1 ?? m.out_of_sample_f1 ?? 0,
      test_roc_auc: m.test_roc_auc ?? null,
      n_samples: m.n_samples ?? m.test_row_count ?? 0,
    }));
  }

  public async getXGBoostModelDetail(modelId: string): Promise<XGBoostModelDetail> {
    const raw: any = await this.request(`/api/xgboost/models/${encodeURIComponent(modelId)}`);

    const testMetrics = raw.test_metrics || raw.out_of_sample_metrics || {};

    let cm = testMetrics.confusion_matrix || raw.confusion_matrix;
    if (cm && !Array.isArray(cm) && typeof cm === 'object') {
      cm = [
        [cm.true_negatives ?? 0, cm.false_positives ?? 0],
        [cm.false_negatives ?? 0, cm.true_positives ?? 0],
      ];
    }
    if (!Array.isArray(cm)) {
      cm = [[0, 0], [0, 0]];
    }

    const normalizedTestMetrics: XGBoostSplitMetrics = {
      accuracy: testMetrics.accuracy ?? raw.out_of_sample_accuracy ?? 0,
      precision: testMetrics.precision ?? 0,
      recall: testMetrics.recall ?? 0,
      f1: testMetrics.f1 ?? raw.out_of_sample_f1 ?? 0,
      roc_auc: testMetrics.roc_auc ?? null,
      pr_auc: testMetrics.pr_auc ?? null,
      balanced_accuracy: testMetrics.balanced_accuracy ?? testMetrics.accuracy ?? 0,
      log_loss: testMetrics.log_loss ?? 0,
      brier_score: testMetrics.brier_score ?? raw.calibration_metrics?.brier_score ?? 0,
      confusion_matrix: cm,
    };

    const rawBase = raw.baseline_metrics || {};
    const normalizedBaselines: XGBoostBaselineMetrics = {
      majority_class: {
        predicted_class: rawBase.majority_class?.predicted_class ?? rawBase.majority_class_baseline?.predicted_class ?? 1,
        accuracy: rawBase.majority_class?.accuracy ?? rawBase.majority_class_baseline?.accuracy ?? raw.baseline_majority_accuracy ?? 0,
        brier_score: rawBase.majority_class?.brier_score ?? rawBase.majority_class_baseline?.brier_score ?? 0.25,
      },
      momentum: {
        accuracy: rawBase.momentum?.accuracy ?? rawBase.momentum_direction_baseline?.accuracy ?? raw.baseline_momentum_accuracy ?? 0,
        brier_score: rawBase.momentum?.brier_score ?? rawBase.momentum_direction_baseline?.brier_score ?? 0.25,
      },
    };

    let featList = raw.feature_importances;
    if (!Array.isArray(featList) && raw.feature_importance && typeof raw.feature_importance === 'object') {
      featList = Object.entries(raw.feature_importance).map(([name, v]: [string, any]) => ({
        feature_name: name,
        gain: typeof v === 'object' ? (v?.gain ?? 0) : (Number(v) || 0),
        weight: typeof v === 'object' ? (v?.weight ?? 0) : 0,
      }));
    }
    if (!Array.isArray(featList)) {
      featList = [];
    }

    let wfList = raw.walk_forward_results;
    if (!Array.isArray(wfList) && Array.isArray(raw.walk_forward_metrics)) {
      wfList = raw.walk_forward_metrics.map((m: any) => ({
        fold: m.fold_index ?? m.fold ?? 1,
        train_start: m.train_start ? String(m.train_start) : '',
        train_end: m.train_end ? String(m.train_end) : '',
        test_start: m.test_start ? String(m.test_start) : '',
        test_end: m.test_end ? String(m.test_end) : '',
        train_samples: m.train_count ?? m.train_samples ?? 0,
        test_samples: m.test_count ?? m.test_samples ?? 0,
        test_accuracy: m.accuracy ?? m.test_accuracy ?? 0,
        test_f1: m.test_f1 ?? m.f1 ?? (m.accuracy ?? 0),
      }));
    }
    if (!Array.isArray(wfList)) {
      wfList = [];
    }

    return {
      ...raw,
      model_id: raw.model_id,
      experiment_id: raw.experiment_id || raw.model_id,
      symbol: raw.symbol,
      timeframe: raw.timeframe,
      created_at: raw.created_at,
      hyperparameters: raw.hyperparameters || {},
      train_metrics: raw.train_metrics || normalizedTestMetrics,
      val_metrics: raw.val_metrics || normalizedTestMetrics,
      test_metrics: normalizedTestMetrics,
      baseline_metrics: normalizedBaselines,
      feature_importances: featList,
      walk_forward_results: wfList,
      dataset_info: raw.dataset_info || {
        symbol: raw.symbol,
        timeframe: raw.timeframe,
        total_raw_bars: (raw.training_row_count || 0) + (raw.test_row_count || 0),
        usable_bars: (raw.training_row_count || 0) + (raw.test_row_count || 0),
        features_count: featList.length || 9,
      },
      status: raw.status || 'COMPLETED',
    };
  }

  public async predictXGBoost(payload: XGBoostPredictRequestPayload): Promise<XGBoostPredictResponse> {
    const raw: any = await this.request('/api/xgboost/predict', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    const isBull = raw.predicted_direction?.includes('BULL') || raw.predicted_class === 1;
    const isBear = raw.predicted_direction?.includes('BEAR') || raw.predicted_class === 0;
    const direction = isBull ? 'BULLISH' : isBear ? 'BEARISH' : 'NEUTRAL';
    const probUp = raw.probability_up ?? raw.bullish_probability ?? (isBull ? (raw.predicted_probability || 0.5) : (1 - (raw.predicted_probability || 0.5)));
    const probDown = raw.probability_down ?? raw.bearish_probability ?? (1 - probUp);
    const conf = raw.confidence ?? Math.max(probUp, probDown);

    let topFeats = raw.top_contributing_features;
    if (!Array.isArray(topFeats) && raw.features_snapshot && typeof raw.features_snapshot === 'object') {
      topFeats = Object.entries(raw.features_snapshot).slice(0, 4).map(([name, val]: [string, any]) => ({
        feature_name: name,
        value: Number(val) || 0,
        contribution_score: Math.abs(Number(val) || 0) * 0.1,
      }));
    }
    if (!Array.isArray(topFeats)) {
      topFeats = [];
    }

    return {
      ...raw,
      model_id: raw.model_id || raw.experiment_id || '',
      symbol: raw.symbol,
      prediction_timestamp: raw.prediction_timestamp,
      predicted_direction: direction,
      probability_up: probUp,
      probability_down: probDown,
      confidence: conf,
      features_used: raw.features_snapshot || raw.features_used || {},
      top_contributing_features: topFeats,
      warning: raw.warning || undefined,
    };
  }

  public async getXGBoostPredictions(symbol?: string, limit: number = 20): Promise<XGBoostPredictionRecordItem[]> {
    const params = new URLSearchParams();
    if (symbol) params.append('symbol', symbol);
    if (limit) params.append('limit', limit.toString());
    const q = params.toString() ? `?${params.toString()}` : '';
    const raw: any = await this.request(`/api/xgboost/predictions${q}`);
    const list = Array.isArray(raw) ? raw : (raw?.items || []);

    return list.map((item: any, idx: number) => {
      const isBull = item.predicted_direction?.includes('BULL') || item.predicted_class === 1;
      const isBear = item.predicted_direction?.includes('BEAR') || item.predicted_class === 0;
      const dir = isBull ? 'BULLISH' : isBear ? 'BEARISH' : 'NEUTRAL';
      const pUp = item.probability_up ?? item.bullish_probability ?? (isBull ? (item.predicted_probability || 0.5) : (1 - (item.predicted_probability || 0.5)));
      const conf = item.confidence ?? item.predicted_probability ?? Math.max(pUp, 1 - pUp);

      return {
        id: item.id ?? item.prediction_id ?? idx + 1,
        model_id: item.model_id ?? item.experiment_id ?? '',
        symbol: item.symbol,
        prediction_timestamp: item.prediction_timestamp,
        predicted_direction: dir,
        probability_up: pUp,
        confidence: conf,
        actual_direction: item.actual_direction || null,
        is_correct: item.is_correct ?? (item.outcome_status === 'CORRECT' ? true : item.outcome_status === 'INCORRECT' ? false : null),
        verified_at: item.verified_at || null,
      };
    });
  }

  public async synthesizeXGBoost(payload: XGBoostSynthesizeRequestPayload): Promise<XGBoostSynthesizeResponse> {
    const raw: any = await this.request('/api/xgboost/synthesize', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    const synthesis = raw.synthesis || {};
    const pred = raw.xgboost_prediction || {};
    const probUp = pred.bullish_probability ?? 0.5;

    return {
      ...raw,
      symbol: raw.symbol,
      timeframe: raw.timeframe,
      provider_used: raw.provider_used || 'DETERMINISTIC_FALLBACK',
      rule_signal: raw.rule_signal,
      xgboost_prediction: pred.predicted_direction || 'BEARISH_DOWN',
      probability_up: probUp,
      divergence_detected: raw.divergence_detected ?? false,
      divergence_warning: synthesis.divergence_or_uncertainty || (raw.divergence_detected ? 'Divergence detected between rule signal and XGBoost.' : undefined),
      synthesized_recommendation: synthesis.synthesis_verdict || (raw.divergence_detected ? 'CAUTION_HOLD' : raw.rule_signal),
      unified_confidence: synthesis.unified_confidence ?? 0.75,
      qwen_advisory_text: synthesis.ai_explanation || synthesis.advisory_caveat || 'Advisory synthesis evaluated.',
      timestamp: raw.timestamp || new Date().toISOString(),
    };
  }

  public async getAIComparisonSummary(params?: {
    symbol?: string;
    timeframe?: string;
    concurrence_status?: string;
    limit?: number;
    offset?: number;
  }): Promise<AIComparisonSummaryData> {
    const qp = new URLSearchParams();
    if (params?.symbol) qp.append('symbol', params.symbol);
    if (params?.timeframe) qp.append('timeframe', params.timeframe);
    if (params?.concurrence_status) qp.append('concurrence_status', params.concurrence_status);
    if (params?.limit) qp.append('limit', params.limit.toString());
    if (params?.offset) qp.append('offset', params.offset.toString());
    const q = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<AIComparisonSummaryData>(`/api/research/ai-comparison${q}`);
  }

  public async evaluateAIComparison(payload: {
    symbol: string;
    market?: string;
    timeframe?: string;
    deterministic_strategy_name: string;
    deterministic_signal: 'BUY' | 'SELL' | 'HOLD';
    deterministic_confidence: number;
    xgboost_predicted_direction?: string;
    xgboost_probability?: number;
    qwen_synthesized_recommendation?: string;
    buy_divergence_prob_threshold?: number;
    sell_divergence_prob_threshold?: number;
    notes?: string;
  }): Promise<AIStrategyComparisonRecordItem> {
    return this.request<AIStrategyComparisonRecordItem>('/api/research/ai-comparison/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // --- 19. Interactive AI Market Assistant ---
  public async getAssistantStatus(): Promise<AssistantStatusResponse> {
    return this.request<AssistantStatusResponse>('/api/assistant/status');
  }

  public async sendAssistantChat(payload: ChatMessageRequest): Promise<ChatMessageResponse> {
    return this.request<ChatMessageResponse>('/api/assistant/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async getAssistantChatHistory(sessionId: string): Promise<ChatHistoryItem[]> {
    return this.request<ChatHistoryItem[]>(`/api/assistant/history/${sessionId}`);
  }

  public async clearAssistantChatHistory(sessionId: string): Promise<{ status: string; session_id: string; deleted_count: number }> {
    return this.request<{ status: string; session_id: string; deleted_count: number }>(`/api/assistant/history/${sessionId}`, {
      method: 'DELETE',
    });
  }
}




export const api = new ApiService(API_BASE_URL);
