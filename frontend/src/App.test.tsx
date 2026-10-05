import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import { api } from './services/api';
import { PositionRead, BuyProposalRead } from './types/market';

// Mock the API client
vi.mock('./services/api', () => ({
  api: {
    getBaseUrl: vi.fn(() => 'http://127.0.0.1:8000'),
    getHealth: vi.fn(),
    getDemoDashboard: vi.fn(),
    getInstruments: vi.fn(),
    getOHLC: vi.fn(),
    getSettings: vi.fn(),
    updateSettings: vi.fn(),
    getWatchlist: vi.fn(),
    addWatchlist: vi.fn(),
    deleteWatchlist: vi.fn(),
    getStrategies: vi.fn(),
    getStrategy: vi.fn(),
    createStrategy: vi.fn(),
    updateStrategy: vi.fn(),
    deleteStrategy: vi.fn(),
    getPaperTrades: vi.fn(),
    getPaperTrade: vi.fn(),
    createPaperTrade: vi.fn(),
    updatePaperTrade: vi.fn(),
    deletePaperTrade: vi.fn(),
    getJournal: vi.fn(),
    createJournal: vi.fn(),
    updateJournal: vi.fn(),
    deleteJournal: vi.fn(),
    getTechnicalAnalysisBundle: vi.fn(),
    getIndicators: vi.fn(),
    getPatterns: vi.fn(),
    getSupportResistance: vi.fn(),
    getAnalysisSummary: vi.fn(),
    getProposals: vi.fn(),
    getProposal: vi.fn(),
    approveProposal: vi.fn(),
    rejectProposal: vi.fn(),
    scanAndGenerateProposal: vi.fn(),
    getPositions: vi.fn(),
    getPosition: vi.fn(),
    closePosition: vi.fn(),
    getAutonomousExitPermissions: vi.fn(),
    updateAutonomousExitPermissions: vi.fn(),
    getRiskSettings: vi.fn(),
    updateRiskSettings: vi.fn(),
    toggleEmergencyStop: vi.fn(),
    getTradeReports: vi.fn(),
    getTradeReport: vi.fn(),
    getAuditLogs: vi.fn(),
    runBacktest: vi.fn(),
    getMonitoringStatus: vi.fn(),
    triggerMonitoringScan: vi.fn(),
    getIntelligenceStatus: vi.fn(),
    runIntelligenceCycle: vi.fn(),
    getLearningSummary: vi.fn(),
    evaluateOutcome: vi.fn(),
    getStrategyCandidates: vi.fn(),
    createStrategyCandidate: vi.fn(),
    advanceStrategyCandidate: vi.fn(),
    activateStrategyCandidate: vi.fn(),
    getStrategyCatalogue: vi.fn(),
    evaluateStrategySignal: vi.fn(),
    getAIStatus: vi.fn(),
    evaluateAIAnalysis: vi.fn(),
    getZerodhaStatus: vi.fn(),
    getZerodhaLoginUrl: vi.fn(),
    disconnectZerodha: vi.fn(),
    submitZerodhaLiveOrder: vi.fn(),
    uploadCSV: vi.fn(),
    getCSVDatasets: vi.fn().mockResolvedValue([]),
    resetRiskDefaults: vi.fn(),
    getAssistantStatus: vi.fn().mockResolvedValue({
      status: 'ONLINE',
      active_model: 'qwen3-local:latest',
      available_models: ['qwen3-local:latest'],
      host: 'http://127.0.0.1:11434',
      available_tools: ['MarketDataTool', 'TechnicalIndicatorsTool', 'PaperPortfolioTool'],
      paper_trading_mode: true,
      disclaimer: 'Advisory-only. Zero real order execution.',
    }),
    getAssistantChatHistory: vi.fn().mockResolvedValue([]),
    sendAssistantChat: vi.fn(),
    clearAssistantChatHistory: vi.fn(),
  },
}));

// Mock TradingView lightweight-charts
vi.mock('lightweight-charts', () => ({
  createChart: vi.fn(() => ({
    addCandlestickSeries: vi.fn(() => ({
      setData: vi.fn(),
      createPriceLine: vi.fn(() => ({})),
      removePriceLine: vi.fn(),
    })),
    addHistogramSeries: vi.fn(() => ({
      setData: vi.fn(),
      priceScale: vi.fn(() => ({
        applyOptions: vi.fn(),
      })),
    })),
    addLineSeries: vi.fn(() => ({
      setData: vi.fn(),
      createPriceLine: vi.fn(() => ({})),
    })),
    timeScale: vi.fn(() => ({
      fitContent: vi.fn(),
      subscribeVisibleLogicalRangeChange: vi.fn(),
      setVisibleLogicalRange: vi.fn(),
      getVisibleLogicalRange: vi.fn(() => ({ from: 0, to: 100 })),
    })),
    applyOptions: vi.fn(),
    remove: vi.fn(),
  })),
  ColorType: { Solid: 'solid' },
  LineStyle: { Solid: 0, Dotted: 1, Dashed: 2 },
}));

const mockHealthResponse = {
  status: 'ok',
  app_name: 'Vibe Trader AI',
  version: '0.1.0',
  timestamp: '2026-09-30T10:00:00Z',
  environment: 'development',
  database_connected: true,
};

const mockDashboardResponse = {
  is_demo: true,
  portfolio: {
    total_value: 28450.0,
    available_cash: 11200.0,
    daily_pnl: 420.5,
    daily_pnl_percent: 1.5,
    open_positions_count: 4,
    active_strategies_count: 3,
    currency: 'USD',
    is_mock: true,
  },
  market_statuses: [
    {
      market: 'FOREX' as const,
      label: 'Forex Global',
      status: 'OPEN' as const,
      session_hours: '24 Hours',
      timezone: 'UTC',
      is_demo: true,
    },
    {
      market: 'NSE' as const,
      label: 'NSE India',
      status: 'OPEN' as const,
      session_hours: '09:15 - 15:30 IST',
      timezone: 'IST',
      is_demo: true,
    },
  ],
  instruments: [
    {
      symbol: 'NIFTY 50',
      name: 'Nifty 50 Index',
      market: 'NSE' as const,
      category: 'Indices',
      last_price: 24850.2,
      change: 142.5,
      change_percent: 0.58,
      high_24h: 24900.0,
      low_24h: 24700.0,
      volume: '150.2K',
      currency_symbol: '₹',
      is_mock: true,
    },
    {
      symbol: 'EUR/USD',
      name: 'Euro / US Dollar',
      market: 'FOREX' as const,
      category: 'Currencies',
      last_price: 1.085,
      change: 0.0024,
      change_percent: 0.22,
      high_24h: 1.088,
      low_24h: 1.081,
      volume: '85.4K',
      currency_symbol: '$',
      is_mock: true,
    },
  ],
  recent_activity: [
    {
      id: 'act-1',
      symbol: 'EUR/USD',
      market: 'FOREX',
      type: 'PAPER_TRADE' as const,
      side: 'BUY' as const,
      quantity: 10000.0,
      price: 1.0825,
      pnl: 25.0,
      status: 'OPEN',
      timestamp: '2026-09-30 14:15',
      is_mock: true,
    },
  ],
  ai_insight: {
    title: 'Multi-Market Liquidity & Momentum Overview',
    sentiment: 'Bullish' as const,
    confidence: 0.78,
    summary: 'Demo AI Analysis: Asian sessions steady.',
    timestamp: '2026-09-30 15:00 UTC',
    disclaimer: 'DEMO DATA: Educational overview only.',
  },
};

const mockSettings = {
  id: 1,
  theme: 'dark' as const,
  default_market: 'ALL' as const,
  default_timeframe: '1D',
  risk_percentage: 1.5,
  notifications_enabled: true,
  created_at: '2026-09-30T10:00:00Z',
  updated_at: '2026-09-30T10:00:00Z',
};

const mockStrategies = {
  items: [
    {
      id: 1,
      name: 'EMA Momentum Trend',
      description: 'EMA cross strategy',
      market: 'ALL',
      timeframe: '1D',
      parameters_json: '{"fast": 20, "slow": 50}',
      is_active: true,
      created_at: '2026-09-30T10:00:00Z',
      updated_at: '2026-09-30T10:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

const mockPaperTrades = {
  items: [
    {
      id: 1,
      symbol: 'RELIANCE',
      market: 'NSE',
      side: 'Long',
      order_type: 'MARKET',
      quantity: 10,
      entry_price: 2950.0,
      stop_loss: 2900.0,
      take_profit: 3100.0,
      status: 'Open' as const,
      notes: 'Testing breakout',
      created_at: '2026-09-30T10:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

const mockJournal = {
  items: [
    {
      id: 1,
      symbol: 'NIFTY 50',
      title: 'Morning Rally Review',
      notes: 'Captured opening candle breakout',
      lessons_learned: 'Stick to stop loss strictly',
      tags: 'breakout,discipline',
      created_at: '2026-09-30T10:00:00Z',
      updated_at: '2026-09-30T10:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

const mockTechnicalAnalysisBundle = {
  symbol: 'EUR/USD',
  market: 'FOREX',
  timeframe: '1D',
  candles: [
    { time: 1700000000, open: 1.08, high: 1.09, low: 1.075, close: 1.085, volume: 1000 },
  ],
  indicators: {
    symbol: 'EUR/USD',
    timeframe: '1D',
    is_mock: true,
    rsi: [{ time: 1700000000, value: 58.2 }],
    macd: [{ time: 1700000000, macd: 0.0012, signal: 0.0008, histogram: 0.0004 }],
    ema_9: [{ time: 1700000000, value: 1.082 }],
    ema_21: [{ time: 1700000000, value: 1.08 }],
    ema_50: [{ time: 1700000000, value: 1.078 }],
    ema_200: [{ time: 1700000000, value: 1.07 }],
    sma_20: [{ time: 1700000000, value: 1.081 }],
    sma_50: [{ time: 1700000000, value: 1.078 }],
    sma_200: [{ time: 1700000000, value: 1.07 }],
    atr: [{ time: 1700000000, value: 0.0045 }],
    bollinger: [{ time: 1700000000, upper: 1.092, middle: 1.081, lower: 1.07, bandwidth: 0.02 }],
  },
  patterns: {
    symbol: 'EUR/USD',
    timeframe: '1D',
    total_detected: 1,
    patterns: [
      {
        pattern_name: 'Hammer',
        time: 1700000000,
        candle_index: 0,
        direction: 'Bullish',
        reliability: 'High',
        explanation: 'Hammer pattern rejecting lower prices.',
      },
    ],
  },
  support_resistance: {
    symbol: 'EUR/USD',
    timeframe: '1D',
    current_price: 1.085,
    zones: [
      {
        price: 1.09,
        zone_type: 'Resistance',
        touches: 4,
        strength: 'Moderate',
        timeframe: '1D',
        min_price: 1.089,
        max_price: 1.091,
        calculation_method: 'Swing High/Low Cluster',
      },
      {
        price: 1.075,
        zone_type: 'Support',
        touches: 6,
        strength: 'Strong',
        timeframe: '1D',
        min_price: 1.074,
        max_price: 1.076,
        calculation_method: 'Swing High/Low Cluster',
      },
    ],
  },
  summary: {
    symbol: 'EUR/USD',
    market: 'FOREX',
    timeframe: '1D',
    timestamp: '2026-09-30T10:00:00Z',
    data_source: 'DEMO DATA (Simulated)',
    current_price: 1.085,
    regime: 'Bullish Momentum',
    rsi_summary: 'RSI(14) stands at 58.2 above midline, indicating healthy bullish momentum.',
    macd_summary: 'MACD line is above Signal line with positive histogram.',
    ma_summary: 'EMA 9 is above EMA 21. Price is above EMA 200.',
    volatility_summary: 'ATR(14) is 0.0045.',
    patterns_summary: '1 pattern identified: Hammer (Bullish).',
    sr_summary: 'Nearest resistance at 1.09 (+0.46%). Nearest support at 1.075 (-0.92%).',
    key_takeaways: [
      "Overall technical regime evaluated as 'Bullish Momentum'.",
      'Current market price is within S/R corridor.',
    ],
    conflicts: [],
    disclaimer: 'FACTUAL TECHNICAL SUMMARY: Generated from rule-based calculations on simulated demo candles.',
  },
  is_mock: true,
};

const mockPositions: PositionRead[] = [
  {
    id: 1,
    position_id: 'POS-TEST-001',
    symbol: 'RELIANCE',
    market: 'NSE',
    side: 'Long',
    quantity: 10,
    entry_price: 2950.0,
    current_price: 2980.0,
    stop_loss: 2900.0,
    target: 3100.0,
    unrealized_pnl: 300.0,
    unrealized_pnl_pct: 1.02,
    status: 'OPEN',
    created_at: '2026-09-30T10:00:00Z',
    updated_at: '2026-09-30T10:00:00Z',
  },
];

const mockProposals: BuyProposalRead[] = [
  {
    id: 1,
    proposal_id: 'PROP-TEST-001',
    symbol: 'RELIANCE',
    market: 'NSE',
    strategy_id: 1,
    strategy_name: 'Fast/Slow EMA Trend Follower',
    current_price: 2950.0,
    proposed_entry_price: 2950.0,
    proposed_quantity: 10,
    stop_loss: 2900.0,
    target: 3100.0,
    risk_amount: 500.0,
    risk_reward_ratio: 3.0,
    estimated_costs: 20.0,
    matched_conditions: ['EMA 9 > EMA 21 Bullish Crossover', 'RSI > 50'],
    unmatched_conditions: [],
    supporting_indicators: { 'EMA 9': 2960, 'EMA 21': 2940, RSI: 58.2 },
    confidence_score: 0.85,
    confidence_method: 'Rule Engine + Multi-Agent Consensus',
    explanation: 'Bullish breakout confirmed by technical momentum and AI verification.',
    uncertainties: 'Upcoming RBI policy announcement',
    data_source: 'DEMO / HISTORICAL',
    data_timestamp: '2026-10-02T10:00:00Z',
    expires_at: '2026-10-02T11:00:00Z',
    status: 'PENDING',
    version: 1,
    created_at: '2026-10-02T10:00:00Z',
    updated_at: '2026-10-02T10:00:00Z',
  },
];

describe('Vibe Trader AI App — Phase 2 & Technical Analysis Views', () => {
  beforeEach(() => {
    localStorage.setItem('vibe_onboarding_dismissed', 'true');
    vi.clearAllMocks();
    (api.getHealth as any).mockResolvedValue(mockHealthResponse);
    (api.getDemoDashboard as any).mockResolvedValue(mockDashboardResponse);
    (api.getOHLC as any).mockResolvedValue({ candles: [] });
    (api.getSettings as any).mockResolvedValue(mockSettings);
    (api.getStrategies as any).mockResolvedValue(mockStrategies);
    (api.getPaperTrades as any).mockResolvedValue(mockPaperTrades);
    (api.getJournal as any).mockResolvedValue(mockJournal);
    (api.getTechnicalAnalysisBundle as any).mockResolvedValue(mockTechnicalAnalysisBundle);
    (api.getWatchlist as any).mockResolvedValue([
      { id: 1, symbol: 'TATAMOTORS', name: 'Tata Motors', market: 'NSE', category: 'Equities', is_active: true, created_at: '' },
    ]);
    (api.getInstruments as any).mockResolvedValue([]);
    if (api.getProposals) (api.getProposals as any).mockResolvedValue(mockProposals);
    if (api.getPositions) (api.getPositions as any).mockResolvedValue(mockPositions);
    if (api.getRiskSettings) (api.getRiskSettings as any).mockResolvedValue({
      id: 1,
      simulated_balance: 100000,
      max_risk_per_trade_pct: 2,
      max_daily_loss: 5000,
      max_open_positions: 5,
      max_position_size_pct: 20,
      emergency_stop_active: false,
      created_at: '',
      updated_at: '',
    });
    if (api.getAutonomousExitPermissions) (api.getAutonomousExitPermissions as any).mockResolvedValue({
      id: 1,
      is_enabled: true,
      allow_stop_loss: true,
      allow_take_profit: true,
      allow_strategy_exit: false,
      allow_max_drawdown: true,
      max_position_scope: 'ALL_POSITIONS',
      emergency_risk_limit_pct: 10,
      created_at: '',
      updated_at: '',
    });
    if (api.getTradeReports) (api.getTradeReports as any).mockResolvedValue([]);
    if (api.getAuditLogs) (api.getAuditLogs as any).mockResolvedValue([]);
    if (api.getIntelligenceStatus) {
      (api.getIntelligenceStatus as any).mockResolvedValue({
        core_status: 'OPERATIONAL',
        agents: {},
        active_regime: 'Multi-Market Surveillance Active',
        data_freshness_seconds: 1.2,
        emergency_stop_active: false,
        autonomous_sell_enabled: true,
        total_candidate_strategies: 2,
        pending_proposals_count: 0,
        open_positions_count: 0,
        timestamp: '2026-09-30T10:00:00Z',
      });
    }
    if (api.getLearningSummary) {
      (api.getLearningSummary as any).mockResolvedValue({
        agent: { name: 'Learning Agent', version: '1.0.0', status: 'COMPLETED', execution_time_ms: 5.0, timestamp: '2026-09-30T10:00:00Z' },
        total_trades_analyzed: 12,
        win_rate: 0.65,
        profit_factor: 1.85,
        expectancy: 120.5,
        average_win: 250.0,
        average_loss: -110.0,
        max_drawdown_pct: 4.2,
        average_slippage: 0.0005,
        performance_by_regime: {},
        performance_deterioration_detected: false,
        deterioration_reasons: [],
        candidate_strategy_count: 2,
        timestamp: '2026-09-30T10:00:00Z',
      });
    }
    if (api.getStrategyCandidates) {
      (api.getStrategyCandidates as any).mockResolvedValue([
        {
          id: 1,
          candidate_id: 'CAND-EMA-ADAPT-01',
          name: 'Adaptive EMA Regime Crossover',
          version: 'v1.1.0-rc1',
          market: 'FOREX',
          timeframe: '1D',
          parameters_json: '{}',
          rationale: 'Volatility scaling tests',
          lifecycle_stage: 'SANDBOX',
          validation_metrics: { win_rate: 0.62, profit_factor: 1.7 },
          is_active: false,
          created_at: '2026-09-30T10:00:00Z',
          updated_at: '2026-09-30T10:00:00Z',
        },
      ]);
    }
    if (api.getStrategyCatalogue) {
      (api.getStrategyCatalogue as any).mockResolvedValue({
        strategies: [
          {
            strategy_code: 'STRAT-EMA-CROSS',
            name: 'Fast/Slow EMA Trend Follower',
            family: 'Trend Following',
            description: 'EMA 9 cross over EMA 21 trend following system.',
            indicators_used: ['EMA_9', 'EMA_21'],
            parameters: { fast_period: 9, slow_period: 21 },
            entry_rule_summary: 'Bullish EMA 9 > EMA 21 cross',
            exit_rule_summary: 'Bearish EMA 9 < EMA 21 cross',
            lifecycle_status: 'PRODUCTION',
          },
        ],
        total_strategies: 1,
      });
    }
    if (api.getAIStatus) {
      (api.getAIStatus as any).mockResolvedValue({
        provider_name: 'OllamaProvider',
        model_name: 'deepseek-r1:1.5b',
        host: 'http://127.0.0.1:11434',
        is_online: true,
        fallback_available: true,
        latency_ms: 120.0,
      });
    }
    if (api.evaluateAIAnalysis) {
      (api.evaluateAIAnalysis as any).mockResolvedValue({
        symbol: 'RELIANCE',
        timeframe: '1D',
        sentiment: 'BULLISH',
        confidence_score: 0.85,
        market_regime: 'Trend Continuation',
        primary_rationale: 'Strong institutional buying along 20-day SMA.',
        key_evidence: ['EMA 9 > EMA 21', 'RSI healthy at 58.2'],
        conflicting_signals: [],
        uncertainty_factors: ['Earnings release in 3 weeks'],
        recommended_action: 'BUY_CANDIDATE',
        risk_caveats: ['Strict stop loss required below 2850'],
        hallucination_defense_passed: true,
        quality_metrics: {
          input_completeness_pct: 100,
          data_freshness_seconds: 15,
          structured_schema_valid: true,
          model_latency_ms: 145.2,
          unsupported_claims_rejected: 0,
          provider_type: 'OLLAMA',
        },
        model_name: 'deepseek-r1:1.5b',
        timestamp: '2026-10-02T10:00:00Z',
      });
    }
    if (api.getZerodhaStatus) {
      (api.getZerodhaStatus as any).mockResolvedValue({
        is_connected: true,
        broker_name: 'Zerodha Kite Connect',
        user_id: 'DEMO_USER_01',
        user_name: 'Vibe Trader Demo Account',
        broker_mode: 'READ_ONLY_AUTH',
        live_orders_allowed: false,
        safety_policy: 'FAIL_CLOSED_NO_LIVE_ORDERS',
        available_margin: 2000.0,
      });
    }
    if (api.getZerodhaLoginUrl) {
      (api.getZerodhaLoginUrl as any).mockResolvedValue({
        login_url: 'https://kite.zerodha.com/connect/login',
        status: 'configured',
        instructions: 'Authenticate via Kite',
      });
    }
    if (api.getCSVDatasets) {
      (api.getCSVDatasets as any).mockResolvedValue({
        datasets: [
          {
            dataset_id: 'DS-01',
            symbol: 'RELIANCE_CUSTOM',
            market: 'NSE',
            total_rows: 100,
            start_time: '2026-01-01',
            end_time: '2026-04-10',
            is_valid: true,
          },
        ],
      });
    }
  });

  it('renders overview dashboard with live status and metrics', async () => {
    render(<App />);

    expect(await screen.findByText(/DEMO DATA ONLY/i)).toBeInTheDocument();
    expect(await screen.findByText(/API ONLINE/i)).toBeInTheDocument();
    expect(screen.getAllByText('NIFTY 50').length).toBeGreaterThanOrEqual(1);
  });

  it('navigates to Settings view and loads user preferences', async () => {
    render(<App />);

    const settingsBtn = screen.getByText('Settings');
    fireEvent.click(settingsBtn);

    expect(await screen.findByText(/Terminal & Risk Settings/i)).toBeInTheDocument();
    expect(screen.getByText(/Max Risk Tolerance Per Trade/i)).toBeInTheDocument();
  });

  it('navigates to Strategy Lab view and renders strategy cards', async () => {
    render(<App />);

    const stratBtn = screen.getByText('Strategy Lab');
    fireEvent.click(stratBtn);

    expect(await screen.findByText(/Strategy Lab & Algorithmic Engine/i)).toBeInTheDocument();
    expect((await screen.findAllByText('Fast/Slow EMA Trend Follower')).length).toBeGreaterThanOrEqual(1);
  });

  it('navigates to Paper Trading view and displays active orders', async () => {
    render(<App />);

    const ptBtn = screen.getByText('Paper Trading');
    fireEvent.click(ptBtn);

    expect(await screen.findByText(/Paper Trading Terminal/i)).toBeInTheDocument();
    expect((await screen.findAllByText('RELIANCE')).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Close Trade')).toBeInTheDocument();
  });

  it('navigates to Trade Journal view and renders entries', async () => {
    render(<App />);

    const journalBtn = screen.getByText('Trade Journal');
    fireEvent.click(journalBtn);

    expect(await screen.findByText(/Trader Journal & Reflection/i)).toBeInTheDocument();
    expect(await screen.findByText('Morning Rally Review')).toBeInTheDocument();
  });

  it('navigates to Technical Analysis Studio and displays indicators and patterns', async () => {
    render(<App />);

    const taBtn = screen.getByText('Technical Analysis');
    fireEvent.click(taBtn);

    expect(await screen.findByText(/Technical Analysis Studio/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Factual Technical Summary/i).length).toBeGreaterThanOrEqual(1);
    expect(await screen.findByText(/S\/R Price Zones/i)).toBeInTheDocument();
    expect(await screen.findByText('Hammer')).toBeInTheDocument();
  });

  it('navigates to BUY Approval Center and renders human approval gates', async () => {
    render(<App />);

    const buyBtn = screen.getByText('BUY Approval');
    fireEvent.click(buyBtn);

    expect(await screen.findByText(/BUY Approval Center/i)).toBeInTheDocument();
    expect(await screen.findByText(/HUMAN-IN-THE-LOOP/i)).toBeInTheDocument();
    expect(screen.getByText('Scan for Opportunities')).toBeInTheDocument();
  });

  it('navigates to Open Positions and renders autonomous exit status', async () => {
    render(<App />);

    const posBtn = screen.getAllByText('Open Positions')[0];
    fireEvent.click(posBtn);

    expect(await screen.findByText(/Positions & Autonomous Exit Monitor/i)).toBeInTheDocument();
    expect(await screen.findByText(/STEPS 6 & 7/i)).toBeInTheDocument();
  });

  it('navigates to Risk & Safety controls and shows Emergency Stop status', async () => {
    render(<App />);

    const riskBtn = screen.getByText('Risk & Safety');
    fireEvent.click(riskBtn);

    expect(await screen.findByText(/Risk Management & Emergency Controls/i)).toBeInTheDocument();
    expect(await screen.findByText(/ACTIVATE EMERGENCY STOP/i)).toBeInTheDocument();
  });

  it('navigates to Trade Reports view and displays post-mortem table', async () => {
    render(<App />);

    const reportsBtn = screen.getByText('Trade Reports');
    fireEvent.click(reportsBtn);

    expect(await screen.findByText(/Trade Reports & Post-Mortem Analytics/i)).toBeInTheDocument();
    expect(await screen.findByText(/AUDITED PERFORMANCE/i)).toBeInTheDocument();
  });

  it('navigates to Backtesting view and displays simulation runner', async () => {
    render(<App />);

    const btBtn = screen.getByText('Backtesting');
    fireEvent.click(btBtn);

    expect(await screen.findByText(/Quantitative Backtesting Engine/i)).toBeInTheDocument();
    expect(await screen.findByText(/Run Quantitative Simulation/i)).toBeInTheDocument();
  });

  it('navigates to Vibe Intelligence Core view and renders multi-agent architecture', async () => {
    render(<App />);

    const intelBtn = screen.getByText('Vibe Intelligence');
    fireEvent.click(intelBtn);

    expect(await screen.findByText(/Vibe Intelligence Core/i)).toBeInTheDocument();
    expect(await screen.findByText(/Agent Fleet Status/i)).toBeInTheDocument();
    expect(await screen.findByText(/Controlled Strategy Adaptation Lifecycle/i)).toBeInTheDocument();
    expect(screen.getByText('Evaluate Instrument')).toBeInTheDocument();
  });

  it('navigates to Market Data & CSV view and renders datasets table', async () => {
    render(<App />);

    const mdBtn = screen.getByText('Market Data & CSV');
    fireEvent.click(mdBtn);

    expect(await screen.findByText(/Market Data Sources & CSV Provider/i)).toBeInTheDocument();
    expect(await screen.findByText(/Available Pre-calibrated Demo Datasets/i)).toBeInTheDocument();
  });

  it('navigates to Broker connection view and verifies fail-closed live order shield', async () => {
    render(<App />);

    const brokerBtn = screen.getByText('Broker (Zerodha)');
    fireEvent.click(brokerBtn);

    expect(await screen.findByText(/Broker Integration — Zerodha Kite Connect Personal/i)).toBeInTheDocument();
    expect(await screen.findByText(/Fail-Closed Live Order Shield: ACTIVE & ENFORCED/i)).toBeInTheDocument();
  });

  it('navigates to AI Reasoning view and verifies hallucination defense panel', async () => {
    render(<App />);

    const aiBtn = screen.getByText('AI Reasoning');
    fireEvent.click(aiBtn);

    expect(await screen.findByText(/AI Market Reasoning & Hallucination Defense/i)).toBeInTheDocument();
    expect(await screen.findByText(/Run Market AI Reasoning/i)).toBeInTheDocument();
  });

  it('displays WelcomeOnboardingModal on first visit when not dismissed and dismisses on start paper trading', async () => {
    localStorage.removeItem('vibe_onboarding_dismissed');
    render(<App />);

    expect(await screen.findByText(/WELCOME TO VIBE TRADER AI/i)).toBeInTheDocument();
    expect(screen.getAllByText(/PAPER TRADING — NO REAL MONEY/i).length).toBeGreaterThanOrEqual(1);

    const startBtn = screen.getByRole('button', { name: /START PAPER TRADING/i });
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(screen.queryByText(/WELCOME TO VIBE TRADER AI/i)).not.toBeInTheDocument();
    });
    expect(localStorage.getItem('vibe_onboarding_dismissed')).toBe('true');
  });

  it('renders persistent simulation banner across the terminal', async () => {
    render(<App />);
    expect(await screen.findByText(/LIVE BROKER ORDERS: DISABLED/i)).toBeInTheDocument();
  });

  it('renders signal cards in BUY Approval Center with approval modal gate', async () => {
    (api.approveProposal as any).mockResolvedValue({
      message: 'Proposal approved',
      position_id: 'POS-001',
      fill_price: 2950.0,
      paper_order_id: 'ORD-001',
    });

    render(<App />);
    const buyBtn = screen.getByText('BUY Approval');
    fireEvent.click(buyBtn);

    expect(await screen.findByText('RELIANCE')).toBeInTheDocument();
    expect(screen.getAllByText(/BUY CANDIDATE/i).length).toBeGreaterThanOrEqual(1);

    // Open Approval Modal
    const approveBtn = screen.getByRole('button', { name: /APPROVE PAPER TRADE/i });
    fireEvent.click(approveBtn);

    // Modal opens
    expect(await screen.findByText(/PAPER TRADE APPROVAL/i)).toBeInTheDocument();
    const confirmBtn = screen.getByRole('button', { name: /CONFIRM PAPER TRADE/i });
    expect(confirmBtn).toBeDisabled();

    // Check mandatory understanding checkbox
    const checkbox = screen.getByRole('checkbox', {
      name: /I understand this is a simulated paper trade/i,
    });
    fireEvent.click(checkbox);
    expect(confirmBtn).not.toBeDisabled();

    // Confirm execution
    fireEvent.click(confirmBtn);
    await waitFor(() => {
      expect(api.approveProposal).toHaveBeenCalledWith('PROP-TEST-001', expect.any(String));
    });
  });
});
