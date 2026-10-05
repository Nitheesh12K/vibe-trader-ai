import React, { useEffect, useState, useCallback } from 'react';
import { TerminalLayout } from './components/layout/TerminalLayout';
import { OverviewView } from './components/dashboard/OverviewView';
import { SettingsView } from './components/views/SettingsView';
import { StrategyLabView } from './components/views/StrategyLabView';
import { StrategyComparisonView } from './components/views/StrategyComparisonView';
import { MarketReplayView } from './components/views/MarketReplayView';
import { WatchlistView } from './components/views/WatchlistView';
import { AlertsView } from './components/views/AlertsView';
import { PerformanceAnalyticsView } from './components/views/PerformanceAnalyticsView';
import { DataManagerView } from './components/views/DataManagerView';
import { ReportExportView } from './components/views/ReportExportView';
import { SystemHealthView } from './components/views/SystemHealthView';
import { MarketDataSourcesView } from './components/views/MarketDataSourcesView';
import { BrokerConnectionView } from './components/views/BrokerConnectionView';
import { PaperTradingView } from './components/views/PaperTradingView';
import { TradeJournalView } from './components/views/TradeJournalView';
import { MarketWatchView } from './components/views/MarketWatchView';
import { TechnicalAnalysisStudio } from './components/analysis/TechnicalAnalysisStudio';
import { BuyApprovalCenter } from './components/views/BuyApprovalCenter';
import { OpenPositionsView } from './components/views/OpenPositionsView';
import { RiskManagementView } from './components/views/RiskManagementView';
import { TradeReportsView } from './components/views/TradeReportsView';
import { AuditLogView } from './components/views/AuditLogView';
import { BacktestingView } from './components/views/BacktestingView';
import { AIInsightsView } from './components/views/AIInsightsView';
import { PortfolioView } from './components/views/PortfolioView';
import { VibeIntelligenceView } from './components/views/VibeIntelligenceView';
import { XGBoostResearchView } from './components/views/XGBoostResearchView';
import { MarketAssistantChat } from './components/assistant/MarketAssistantChat';
import { GlobalSearchModal } from './components/common/GlobalSearchModal';
import { api } from './services/api';
import {
  HealthResponse,
  DashboardSummaryResponse,
  InstrumentItem,
  OHLCCandle,
  NavTabId,
  PaperTradeItem,
  StrategyItem,
} from './types/market';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTabId>('overview');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(false);
  const [dashboardData, setDashboardData] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInstrument, setSelectedInstrument] = useState<InstrumentItem | null>(null);
  const [candles, setCandles] = useState<OHLCCandle[]>([]);
  const [chartLoading, setChartLoading] = useState<boolean>(false);
  const [timeframe, setTimeframe] = useState<string>('1D');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [pendingProposalsCount, setPendingProposalsCount] = useState<number>(0);
  const [unreadAlertsCount, setUnreadAlertsCount] = useState<number>(0);
  const [searchModalOpen, setSearchModalOpen] = useState<boolean>(false);

  // 1. Fetch Health Status
  const fetchHealth = useCallback(async () => {
    try {
      setHealthLoading(true);
      const res = await api.getHealth();
      setHealth(res);
    } catch (err: any) {
      console.warn('Health check failed:', err.message);
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  // 2. Fetch Chart Candles for active instrument
  const fetchCandles = useCallback(
    async (symbol: string, tf: string) => {
      try {
        setChartLoading(true);
        const res = await api.getOHLC(symbol, tf);
        setCandles(res.candles);
      } catch (err: any) {
        console.error(`Failed to fetch candles for ${symbol}:`, err);
      } finally {
        setChartLoading(false);
      }
    },
    []
  );

  // 3. Fetch Unread Alerts
  const fetchUnreadAlerts = useCallback(async () => {
    try {
      const events = await api.getAlertEvents(true);
      setUnreadAlertsCount(events.length);
    } catch {
      // Non-blocking
    }
  }, []);

  // 4. Fetch Consolidated Dashboard Data + Sync with SQLite DB
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Perform health check, demo dashboard, real DB queries, and proposals count concurrently
      const [dashRes, dbTradesRes, dbStrategiesRes, pendingProps] = await Promise.all([
        api.getDemoDashboard(),
        api.getPaperTrades(undefined, undefined, 1, 10).catch(() => ({ items: [], total: 0 })),
        api.getStrategies(undefined, true, 1, 10).catch(() => ({ items: [], total: 0 })),
        api.getProposals('PENDING').catch(() => []),
        fetchHealth(),
        fetchUnreadAlerts(),
      ]);

      setPendingProposalsCount(pendingProps.length);

      // If user has real paper trades in DB, augment recent activities with live DB trades
      let recentActivities = dashRes.recent_activity;
      if (dbTradesRes.items && dbTradesRes.items.length > 0) {
        const liveTradeActivities = dbTradesRes.items.map((t) => ({
          id: `trade-${t.id}`,
          symbol: t.symbol,
          market: t.market,
          type: 'PAPER_TRADE' as const,
          side: (t.side.toUpperCase() === 'SHORT' ? 'SELL' : 'BUY') as 'BUY' | 'SELL',
          quantity: t.quantity,
          price: t.entry_price,
          pnl: t.pnl,
          status: t.status.toUpperCase(),
          timestamp: new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          is_mock: true,
        }));
        recentActivities = [...liveTradeActivities, ...dashRes.recent_activity].slice(0, 8);
      }

      // Sync active strategy and open position counts with DB
      const openCount = dbTradesRes.items.filter((t) => t.status === 'Open').length;
      const activeStratCount = dbStrategiesRes.total > 0 ? dbStrategiesRes.total : dashRes.portfolio.active_strategies_count;

      const syncedDashboard: DashboardSummaryResponse = {
        ...dashRes,
        portfolio: {
          ...dashRes.portfolio,
          open_positions_count: openCount > 0 ? openCount : dashRes.portfolio.open_positions_count,
          active_strategies_count: activeStratCount,
        },
        recent_activity: recentActivities,
      };

      setDashboardData(syncedDashboard);

      // Default selected instrument if not set
      if (dashRes.instruments && dashRes.instruments.length > 0) {
        const defaultInst =
          selectedInstrument ||
          dashRes.instruments.find((i) => i.symbol === 'NIFTY 50') ||
          dashRes.instruments[0];

        setSelectedInstrument(defaultInst);
        fetchCandles(defaultInst.symbol, timeframe);
      }
    } catch (err: any) {
      console.error('Failed to load dashboard:', err);
      setError(err.message || 'Unable to connect to the backend server.');
    } finally {
      setLoading(false);
    }
  }, [fetchHealth, fetchCandles, fetchUnreadAlerts, timeframe, selectedInstrument]);

  // Global Ctrl+K Shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setSearchModalOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Initial load
  useEffect(() => {
    fetchDashboardData();

    // Auto-ping health and alerts every 30 seconds
    const interval = setInterval(() => {
      fetchHealth();
      fetchUnreadAlerts();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Handle instrument selection
  const handleSelectInstrument = (inst: InstrumentItem) => {
    setSelectedInstrument(inst);
    fetchCandles(inst.symbol, timeframe);
  };

  // Handle timeframe change
  const handleTimeframeChange = (newTf: string) => {
    setTimeframe(newTf);
    if (selectedInstrument) {
      fetchCandles(selectedInstrument.symbol, newTf);
    }
  };

  const handleGlobalNavigate = (tab: NavTabId, symbol?: string) => {
    setActiveTab(tab);
    if (symbol) {
      const match = dashboardData?.instruments.find((i) => i.symbol.toUpperCase() === symbol.toUpperCase());
      if (match) {
        setSelectedInstrument(match);
        fetchCandles(match.symbol, timeframe);
      } else {
        fetchCandles(symbol, timeframe);
      }
    }
  };

  return (
    <>
      <TerminalLayout
        activeTab={activeTab}
        onTabChange={setActiveTab}
        health={health}
        healthLoading={healthLoading}
        marketStatuses={dashboardData?.market_statuses || []}
        onRefresh={fetchDashboardData}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        pendingProposalsCount={pendingProposalsCount}
        onOpenSearch={() => setSearchModalOpen(true)}
        unreadAlertsCount={unreadAlertsCount}
      >
        {activeTab === 'overview' && (
          <OverviewView
            data={dashboardData}
            loading={loading}
            error={error}
            selectedInstrument={selectedInstrument}
            onSelectInstrument={handleSelectInstrument}
            candles={candles}
            chartLoading={chartLoading}
            timeframe={timeframe}
            onTimeframeChange={handleTimeframeChange}
            onRetry={fetchDashboardData}
            searchFilter={searchQuery}
          />
        )}

        {activeTab === 'watchlist' && (
          <WatchlistView onNavigate={handleGlobalNavigate} />
        )}

        {activeTab === 'market_watch' && (
          <MarketWatchView
            onSelectInstrument={(inst) => {
              handleSelectInstrument(inst);
              setActiveTab('overview');
            }}
          />
        )}

        {activeTab === 'technical_analysis' && (
          <TechnicalAnalysisStudio
            initialSymbol={selectedInstrument?.symbol}
            initialMarket={selectedInstrument?.market}
          />
        )}

        {activeTab === 'strategy_comparison' && (
          <StrategyComparisonView onNavigate={handleGlobalNavigate} />
        )}

        {activeTab === 'market_replay' && (
          <MarketReplayView onNavigate={handleGlobalNavigate} />
        )}

        {activeTab === 'buy_approval' && <BuyApprovalCenter />}

        {activeTab === 'positions' && (
          <OpenPositionsView onNavigateToRisk={() => setActiveTab('risk_management')} />
        )}

        {activeTab === 'ai_insights' && <AIInsightsView />}

        {activeTab === 'strategies' && <StrategyLabView />}

        {activeTab === 'backtesting' && <BacktestingView />}

        {activeTab === 'paper_trading' && (
          <PaperTradingView
            onNavigateToJournal={() => setActiveTab('trade_journal')}
            onNavigateToApproval={() => setActiveTab('buy_approval')}
          />
        )}

        {activeTab === 'portfolio' && (
          <PortfolioView onNavigateToApproval={() => setActiveTab('buy_approval')} />
        )}

        {activeTab === 'performance' && (
          <PerformanceAnalyticsView onNavigate={handleGlobalNavigate} />
        )}

        {activeTab === 'trade_journal' && <TradeJournalView />}

        {activeTab === 'data_manager' && (
          <DataManagerView onNavigate={handleGlobalNavigate} />
        )}

        {activeTab === 'market_data' && <MarketDataSourcesView />}

        {activeTab === 'alerts' && (
          <AlertsView onNavigate={handleGlobalNavigate} />
        )}

        {activeTab === 'exports' && (
          <ReportExportView onNavigate={handleGlobalNavigate} />
        )}

        {activeTab === 'system_health' && (
          <SystemHealthView onNavigate={handleGlobalNavigate} />
        )}

        {activeTab === 'broker_connection' && <BrokerConnectionView />}

        {activeTab === 'reports' && <TradeReportsView />}

        {activeTab === 'audit_trail' && <AuditLogView />}

        {activeTab === 'vibe_intelligence' && <VibeIntelligenceView />}

        {activeTab === 'risk_management' && <RiskManagementView />}

        {activeTab === 'xgboost_research' && (
          <XGBoostResearchView onNavigate={handleGlobalNavigate} />
        )}

        {activeTab === 'settings' && <SettingsView onNavigate={handleGlobalNavigate} />}
      </TerminalLayout>

      {/* Global Command Menu Dialog (Ctrl+K) */}
      <GlobalSearchModal
        isOpen={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
        onSelect={handleGlobalNavigate}
      />

      {/* Floating Interactive AI Market Assistant */}
      <MarketAssistantChat
        currentInstrument={selectedInstrument}
        timeframe={timeframe}
      />
    </>
  );
};

export default App;
