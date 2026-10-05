import React from 'react';
import { PortfolioCard } from './PortfolioCard';
import { MarketStatusCard } from './MarketStatusCard';
import { TradingChart } from '../chart/TradingChart';
import { Watchlist } from '../watchlist/Watchlist';
import { ActivityTable } from './ActivityTable';
import { AIInsightsPanel } from '../insights/AIInsightsPanel';
import { ErrorBanner } from '../common/ErrorBanner';
import { LoadingSpinner } from '../common/LoadingSpinner';
import {
  DashboardSummaryResponse,
  InstrumentItem,
  OHLCCandle,
} from '../../types/market';

interface OverviewViewProps {
  data: DashboardSummaryResponse | null;
  loading: boolean;
  error: string | null;
  selectedInstrument: InstrumentItem | null;
  onSelectInstrument: (inst: InstrumentItem) => void;
  candles: OHLCCandle[];
  chartLoading: boolean;
  timeframe: string;
  onTimeframeChange: (tf: string) => void;
  onRetry: () => void;
  searchFilter: string;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  data,
  loading,
  error,
  selectedInstrument,
  onSelectInstrument,
  candles,
  chartLoading,
  timeframe,
  onTimeframeChange,
  onRetry,
  searchFilter,
}) => {
  if (loading && !data) {
    return <LoadingSpinner label="Connecting to backend and loading market data..." size="lg" />;
  }

  return (
    <div className="space-y-4">
      {/* Error state if connection failed */}
      {error && (
        <ErrorBanner
          title="Backend Connection Notice"
          message={error}
          onRetry={onRetry}
        />
      )}

      {/* 1. Top KPI Summary Cards */}
      <PortfolioCard portfolio={data?.portfolio || null} />

      {/* 2. Main Terminal Grid: Chart (left 8 cols) + Watchlist (right 4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Main Candlestick Chart */}
        <div className="lg:col-span-8">
          <TradingChart
            instrument={selectedInstrument}
            candles={candles}
            loading={chartLoading}
            timeframe={timeframe}
            onTimeframeChange={onTimeframeChange}
          />
        </div>

        {/* Multi-Market Watchlist (Forex, NSE, MCX) */}
        <div className="lg:col-span-4 h-[460px]">
          <Watchlist
            instruments={data?.instruments || []}
            selectedSymbol={selectedInstrument?.symbol || ''}
            onSelectInstrument={onSelectInstrument}
            searchFilter={searchFilter}
          />
        </div>
      </div>

      {/* 3. AI Insights Panel */}
      <AIInsightsPanel insight={data?.ai_insight || null} />

      {/* 4. Bottom Grid: Market Sessions Status + Recent Activity Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-4">
          <MarketStatusCard statuses={data?.market_statuses || []} />
        </div>
        <div className="lg:col-span-8">
          <ActivityTable activities={data?.recent_activity || []} />
        </div>
      </div>
    </div>
  );
};
