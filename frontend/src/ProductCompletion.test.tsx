import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { WatchlistView } from './components/views/WatchlistView';
import { AlertsView } from './components/views/AlertsView';
import { StrategyComparisonView } from './components/views/StrategyComparisonView';
import { MarketReplayView } from './components/views/MarketReplayView';
import { PerformanceAnalyticsView } from './components/views/PerformanceAnalyticsView';
import { DataManagerView } from './components/views/DataManagerView';
import { ReportExportView } from './components/views/ReportExportView';
import { SystemHealthView } from './components/views/SystemHealthView';
import { SettingsCenterView } from './components/views/SettingsCenterView';
import { GlobalSearchModal } from './components/common/GlobalSearchModal';
import { api } from './services/api';

vi.mock('./services/api', () => ({
  api: {
    getWatchlists: vi.fn(),
    getWatchlistGroups: vi.fn(),
    createWatchlistGroup: vi.fn(),
    addToWatchlist: vi.fn(),
    updateWatchlistItem: vi.fn(),
    deleteWatchlistItem: vi.fn(),
    reorderWatchlistInstruments: vi.fn(),
    getAlertRules: vi.fn(),
    createAlertRule: vi.fn(),
    deleteAlertRule: vi.fn(),
    toggleAlertRule: vi.fn(),
    checkAlerts: vi.fn(),
    getAlertEvents: vi.fn(),
    markAlertEventRead: vi.fn(),
    clearAlertEvents: vi.fn(),
    compareStrategies: vi.fn(),
    getReplaySessions: vi.fn(),
    createReplaySession: vi.fn(),
    getReplaySession: vi.fn(),
    stepReplaySession: vi.fn(),
    playReplaySession: vi.fn(),
    pauseReplaySession: vi.fn(),
    resetReplaySession: vi.fn(),
    approveReplayProposal: vi.fn(),
    closeReplayPosition: vi.fn(),
    getPerformanceSummary: vi.fn(),
    getPerformanceByStrategy: vi.fn(),
    getPerformanceBySymbol: vi.fn(),
    getDatasets: vi.fn(),
    getDatasetDetail: vi.fn(),
    deleteDataset: vi.fn(),
    uploadDatasetFile: vi.fn(),
    getExportUrl: vi.fn((type, fmt) => `http://localhost:8000/api/exports/${type}?format=${fmt}`),
    exportReport: vi.fn(),
    getSystemHealth: vi.fn(),
    getConsolidatedSettings: vi.fn(),
    updateConsolidatedSettings: vi.fn(),
  },
}));

describe('Vibe Trader AI — Product Completion Upgrade Verification', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. Watchlist
  it('renders WatchlistView with groups, instruments, and quick actions', async () => {
    (api.getWatchlists as any).mockResolvedValue([
      {
        id: 1,
        symbol: 'NIFTY 50',
        market: 'NSE',
        name: 'NIFTY 50 Index',
        group_name: 'Core Indices',
        order_index: 1,
        latest_price: 24850.5,
        change_pct: 0.85,
        current_signal: 'STRAT-EMA-CROSS BUY',
        notes: 'Key index tracking',
        created_at: '2026-10-03T10:00:00Z',
      },
    ]);
    (api.getWatchlistGroups as any).mockResolvedValue([
      { group_name: 'Core Indices', count: 1 },
    ]);

    render(<WatchlistView />);

    expect(await screen.findByText(/Watchlist Manager/i)).toBeInTheDocument();
    expect(await screen.findByText('NIFTY 50')).toBeInTheDocument();
    expect(await screen.findByText(/24,850.50/i)).toBeInTheDocument();
    expect(await screen.findByText(/0.85%/i)).toBeInTheDocument();
  });

  // 2. Alerts
  it('renders AlertsView and evaluates trigger rules without trade execution', async () => {
    (api.getAlertRules as any).mockResolvedValue([
      {
        id: 1,
        symbol: 'RELIANCE',
        market: 'NSE',
        alert_type: 'PRICE_ABOVE',
        threshold_value: 3000.0,
        condition: '>=',
        is_active: true,
        trigger_count: 2,
        last_triggered_at: '2026-10-03T11:00:00Z',
        cooldown_seconds: 60,
        notes: 'Resistance breakout alert',
        created_at: '2026-10-03T10:00:00Z',
      },
    ]);
    (api.getAlertEvents as any).mockResolvedValue([
      {
        event_id: 'EVT-01',
        rule_id: 1,
        symbol: 'RELIANCE',
        market: 'NSE',
        message: 'RELIANCE crossed above 3000.00 (Current: 3010.50)',
        triggered_value: 3010.5,
        threshold_value: 3000.0,
        is_read: false,
        created_at: '2026-10-03T11:00:00Z',
      },
    ]);
    (api.checkAlerts as any).mockResolvedValue([
      {
        event_id: 'EVT-01',
        rule_id: 1,
        symbol: 'RELIANCE',
        market: 'NSE',
        message: 'Triggered',
        triggered_value: 3010.5,
        threshold_value: 3000.0,
        is_read: false,
        created_at: '2026-10-03T11:00:00Z',
      },
    ]);

    render(<AlertsView />);

    expect(await screen.findByText(/Autonomous Notification Shield/i)).toBeInTheDocument();
    expect(await screen.findByText('RELIANCE')).toBeInTheDocument();
    expect(screen.getByText(/ZERO TRADE SIDE-EFFECTS/i)).toBeInTheDocument();

    const evalBtn = screen.getByRole('button', { name: /Evaluate Rules Now/i });
    fireEvent.click(evalBtn);

    await waitFor(() => {
      expect(api.checkAlerts).toHaveBeenCalled();
    });
  });

  // 3. Strategy Comparison
  it('renders StrategyComparisonView and runs neutral comparison', async () => {
    (api.compareStrategies as any).mockResolvedValue({
      comparison_id: 'COMP-101',
      symbol: 'RELIANCE',
      market: 'NSE',
      timeframe: '1D',
      initial_capital: 100000,
      total_candles: 250,
      strategies: [
        {
          strategy_code: 'STRAT-EMA-CROSS',
          strategy_name: 'EMA Momentum Trend Following',
          total_trades: 12,
          win_rate: 58.33,
          net_pnl: 14200.0,
          profit_factor: 1.85,
          max_drawdown_pct: 4.2,
          sharpe_ratio: 1.45,
          neutral_evaluation_summary: 'Trend-following strategy showing positive momentum.',
          trade_list: [],
        },
      ],
      created_at: '2026-10-03T12:00:00Z',
    });

    render(<StrategyComparisonView />);

    expect(await screen.findByText(/Multi-Strategy Comparison/i)).toBeInTheDocument();
    expect(screen.getByText(/Neutral Factual Backtests/i)).toBeInTheDocument();

    const runBtn = screen.getByRole('button', { name: /Run Side-by-Side Comparison/i });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(api.compareStrategies).toHaveBeenCalled();
      expect(screen.getByText('STRAT-EMA-CROSS')).toBeInTheDocument();
    });
  });

  // 4. Market Replay
  it('renders MarketReplayView and controls step playback', async () => {
    (api.createReplaySession as any).mockResolvedValue({
      session_id: 'REP-SESSION-001',
      symbol: 'INFY',
      market: 'NSE',
      current_price: 1850.0,
      current_index: 10,
      total_candles: 100,
      initial_capital: 50000,
      available_cash: 50000,
      realized_pnl: 0,
      status: 'INITIALIZED',
      created_at: '2026-10-03T12:00:00Z',
      open_positions: [],
      closed_trades: [],
    });
    (api.stepReplaySession as any).mockResolvedValue({
      session_id: 'REP-SESSION-001',
      symbol: 'INFY',
      market: 'NSE',
      current_price: 1865.0,
      current_index: 11,
      total_candles: 100,
      initial_capital: 50000,
      available_cash: 50000,
      realized_pnl: 0,
      status: 'PAUSED',
      created_at: '2026-10-03T12:00:00Z',
      open_positions: [],
      closed_trades: [],
    });

    render(<MarketReplayView />);

    expect(await screen.findByText(/Market Replay Simulator/i)).toBeInTheDocument();

    const stepBtn = await screen.findByRole('button', { name: /Step \+1/i });
    fireEvent.click(stepBtn);

    await waitFor(() => {
      expect(api.stepReplaySession).toHaveBeenCalledWith('REP-SESSION-001', 1);
    });
  });

  // 5. Performance Analytics
  it('renders PerformanceAnalyticsView with KPI metrics and strategy breakdown', async () => {
    (api.getPerformanceSummary as any).mockResolvedValue({
      mode: 'PAPER_TRADING',
      total_equity: 115000.0,
      available_cash: 95000.0,
      realized_pnl: 15000.0,
      unrealized_pnl: 2500.0,
      total_trades: 20,
      winning_trades: 13,
      losing_trades: 7,
      win_rate: 65.0,
      profit_factor: 2.1,
      max_drawdown_pct: 3.5,
      equity_curve: [
        { time: '2026-10-01', equity: 100000, pnl: 0 },
        { time: '2026-10-02', equity: 108000, pnl: 8000 },
        { time: '2026-10-03', equity: 115000, pnl: 15000 },
      ],
      drawdown_curve: [
        { time: '2026-10-01', drawdown_pct: 0 },
        { time: '2026-10-02', drawdown_pct: 1.2 },
        { time: '2026-10-03', drawdown_pct: 0.5 },
      ],
    });
    (api.getPerformanceByStrategy as any).mockResolvedValue([
      {
        strategy_name: 'Fast/Slow EMA Trend Follower',
        total_trades: 12,
        win_rate: 66.7,
        realized_pnl: 10200.0,
        profit_factor: 2.3,
      },
    ]);
    (api.getPerformanceBySymbol as any).mockResolvedValue([
      {
        symbol: 'RELIANCE',
        market: 'NSE',
        total_trades: 10,
        realized_pnl: 8500.0,
        win_rate: 70.0,
      },
    ]);

    render(<PerformanceAnalyticsView />);

    expect(await screen.findByText(/Performance Analytics/i)).toBeInTheDocument();
    expect(await screen.findByText(/1,15,000.00/i)).toBeInTheDocument();
    expect(screen.getByText('65.0%')).toBeInTheDocument();
    expect(screen.getByText('2.10')).toBeInTheDocument();
    expect(screen.getByText('Fast/Slow EMA Trend Follower')).toBeInTheDocument();
  });

  // 6. Data Manager
  it('renders DataManagerView and opens dataset inspector modal', async () => {
    (api.getDatasets as any).mockResolvedValue({
      datasets: [
        {
          dataset_id: 'DS-NIFTY-01',
          symbol: 'NIFTY 50',
          market: 'NSE',
          timeframe: '1D',
          total_rows: 250,
          start_time: '2025-10-01T00:00:00Z',
          end_time: '2026-10-01T00:00:00Z',
          is_valid: true,
          source: 'DEMO',
        },
      ],
      total_datasets: 1,
    });
    (api.getDatasetDetail as any).mockResolvedValue({
      dataset_id: 'DS-NIFTY-01',
      symbol: 'NIFTY 50',
      market: 'NSE',
      timeframe: '1D',
      total_rows: 250,
      start_time: '2025-10-01T00:00:00Z',
      end_time: '2026-10-01T00:00:00Z',
      is_valid: true,
      source: 'DEMO',
      preview_candles: [
        { time: 1700000000, open: 24500, high: 24650, low: 24450, close: 24600, volume: 1500000 },
      ],
    });

    render(<DataManagerView />);

    expect(await screen.findByText(/Historical Data Manager/i)).toBeInTheDocument();
    expect(await screen.findByText('DS-NIFTY-01')).toBeInTheDocument();

    const inspectBtn = screen.getByTitle(/Inspect Preview & Validation/i);
    fireEvent.click(inspectBtn);

    await waitFor(() => {
      expect(api.getDatasetDetail).toHaveBeenCalledWith('DS-NIFTY-01');
      expect(screen.getByText(/Dataset Inspection & Validation: NIFTY 50/i)).toBeInTheDocument();
    });
  });

  // 7. Report Export
  it('renders ReportExportView and validates export links and disclaimer security', async () => {
    (api.exportReport as any).mockResolvedValue({
      report: 'Paper Trading Summary',
      total_records: 15,
      disclaimer: 'FOR SIMULATION AND ANALYSIS ONLY. ZERO BROKER CREDENTIALS.',
    });

    render(<ReportExportView />);

    expect(await screen.findByText(/Report & Data Export Center/i)).toBeInTheDocument();
    expect(screen.getByText(/NO SECRETS GUARANTEE/i)).toBeInTheDocument();
    expect(screen.getByText('Paper Trading Execution Journal')).toBeInTheDocument();
    expect(screen.getByText('Append-Only System Audit Log')).toBeInTheDocument();

    const previewBtns = screen.getAllByRole('button', { name: /Preview/i });
    fireEvent.click(previewBtns[0]);

    await waitFor(() => {
      expect(api.exportReport).toHaveBeenCalledWith('trades', 'json');
    });
  });

  // 8. System Health
  it('renders SystemHealthView and probes 9 subsystems with Zerodha fail-closed shield', async () => {
    (api.getSystemHealth as any).mockResolvedValue({
      overall_status: 'HEALTHY',
      timestamp: '2026-10-03T12:00:00Z',
      services: [
        { name: 'FastAPI Backend Core', status: 'ONLINE', latency_ms: 1.2, last_check: '2026-10-03T12:00:00Z', details: { uptime: '99.9%' } },
        { name: 'SQLite Database Store', status: 'ONLINE', latency_ms: 0.8, last_check: '2026-10-03T12:00:00Z', details: { connected: true } },
        { name: 'AI Intelligence (Ollama / Local LLM)', status: 'ONLINE', latency_ms: 12.5, last_check: '2026-10-03T12:00:00Z', details: { model: 'deepseek-r1:1.5b' } },
        { name: 'Deterministic Risk Guardian', status: 'ONLINE', latency_ms: 0.3, last_check: '2026-10-03T12:00:00Z', details: { max_risk: '2.0%' } },
        { name: 'Zerodha Kite Connect Adapter', status: 'ONLINE', latency_ms: 45.0, last_check: '2026-10-03T12:00:00Z', details: { mode: 'READ_ONLY', orders_disabled: true } },
      ],
      live_broker_orders: 'DISABLED (HTTP 403 Forbidden)',
      safety_shield: 'ACTIVE',
    });

    render(<SystemHealthView />);

    expect(await screen.findByText(/System Health & Diagnostics Center/i)).toBeInTheDocument();
    expect(await screen.findByText(/FAIL-CLOSED SHIELD ACTIVE/i)).toBeInTheDocument();
    expect(screen.getByText('FastAPI Backend Core')).toBeInTheDocument();
    expect(screen.getByText('Zerodha Kite Connect Adapter')).toBeInTheDocument();
  });

  // 9. Consolidated Settings Center
  it('renders SettingsCenterView and updates risk boundaries with confirmation modal', async () => {
    (api.getConsolidatedSettings as any).mockResolvedValue({
      user_settings: { id: 1, theme: 'dark', default_market: 'NSE', default_timeframe: '1D', risk_percentage: 1.0, notifications_enabled: true },
      risk_settings: { id: 1, simulated_balance: 100000, max_risk_per_trade_pct: 2.0, max_daily_loss: 10000, max_open_positions: 5, max_position_size_pct: 20, emergency_stop_active: false },
      autonomous_exit: { id: 1, is_enabled: true, allow_stop_loss: true, allow_take_profit: true, allow_strategy_exit: true, allow_max_drawdown: true },
      ai_status: { provider_name: 'Ollama', model_name: 'deepseek-r1:1.5b', host: 'http://localhost:11434', is_online: true, fallback_available: true, latency_ms: 12 },
      broker_status: { broker_name: 'Zerodha Kite Connect', is_connected: false, api_key_configured: true, api_key_masked: '****KEY', live_execution_mode: 'FAIL_CLOSED_403', disclaimer: 'Read-only mode active' },
    });
    (api.updateConsolidatedSettings as any).mockResolvedValue({
      user_settings: { id: 1, theme: 'dark', default_market: 'NSE', default_timeframe: '1D', risk_percentage: 1.5, notifications_enabled: true },
      risk_settings: { id: 1, simulated_balance: 100000, max_risk_per_trade_pct: 2.5, max_daily_loss: 12000, max_open_positions: 6, max_position_size_pct: 20, emergency_stop_active: false },
      autonomous_exit: { id: 1, is_enabled: true, allow_stop_loss: true, allow_take_profit: true, allow_strategy_exit: true, allow_max_drawdown: true },
      ai_status: { provider_name: 'Ollama', model_name: 'deepseek-r1:1.5b', host: 'http://localhost:11434', is_online: true, fallback_available: true, latency_ms: 12 },
      broker_status: { broker_name: 'Zerodha Kite Connect', is_connected: false, api_key_configured: true, api_key_masked: '****KEY', live_execution_mode: 'FAIL_CLOSED_403', disclaimer: 'Read-only mode active' },
    });

    render(<SettingsCenterView />);

    expect(await screen.findByText(/System Settings Center/i)).toBeInTheDocument();
    expect(screen.getByText('AUDITED CONTROLS')).toBeInTheDocument();

    const saveBtn = screen.getByRole('button', { name: /Save All Changes/i });
    fireEvent.click(saveBtn);

    // Confirmation modal appears
    expect(await screen.findByText(/Confirm Configuration Updates/i)).toBeInTheDocument();
    const confirmBtn = screen.getByRole('button', { name: /Confirm & Save/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(api.updateConsolidatedSettings).toHaveBeenCalled();
    });
  });

  // 10. Global Command Menu (Ctrl+K)
  it('renders GlobalSearchModal and filters actions and views', async () => {
    const handleSelect = vi.fn();
    const handleClose = vi.fn();

    render(
      <GlobalSearchModal isOpen={true} onClose={handleClose} onSelect={handleSelect} />
    );

    expect(screen.getByPlaceholderText(/Type a view, symbol/i)).toBeInTheDocument();
    expect(screen.getByText('Overview Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Strategy Comparison')).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText(/Type a view, symbol/i);
    fireEvent.change(searchInput, { target: { value: 'Replay' } });

    expect(screen.getByText('Market Replay Mode')).toBeInTheDocument();

    const replayOption = screen.getByText('Market Replay Mode');
    fireEvent.click(replayOption);

    expect(handleSelect).toHaveBeenCalledWith('market_replay', undefined);
    expect(handleClose).toHaveBeenCalled();
  });
});
