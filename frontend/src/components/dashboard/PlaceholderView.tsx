import React from 'react';
import {
  TrendingUp,
  LineChart,
  Sparkles,
  Cpu,
  History,
  Coins,
  Briefcase,
  BookOpen,
  ShieldAlert,
  Settings,
  Construction,
  Layers,
  Brain,
} from 'lucide-react';
import { NavTabId } from '../../types/market';
import { Badge } from '../common/Badge';

interface PlaceholderViewProps {
  tabId: NavTabId;
}

const TAB_METADATA: Record<
  NavTabId,
  { title: string; subtitle: string; icon: React.ElementType; phase: string }
> = {
  overview: {
    title: 'Overview Terminal',
    subtitle: 'Consolidated dashboard metrics and live interactive charting.',
    icon: Layers,
    phase: 'Phase 1 Active',
  },
  market_watch: {
    title: 'Market Watch',
    subtitle: 'Deep multi-market scanner for Forex, Indian Equities (NSE), and MCX Commodities.',
    icon: TrendingUp,
    phase: 'Phase 2 Planned',
  },
  technical_analysis: {
    title: 'Technical Analysis Studio',
    subtitle: 'Automated technical indicators, candlestick pattern detection, and support/resistance zones.',
    icon: LineChart,
    phase: 'Phase 2 Planned',
  },
  ai_insights: {
    title: 'AI Market Explanations',
    subtitle: 'LLM-powered market synthesis, macro summaries, and educational query assistant.',
    icon: Sparkles,
    phase: 'Phase 3 Planned',
  },
  strategies: {
    title: 'Strategy Engine',
    subtitle: 'Rule-based strategy builder, parameter optimization, and multi-timeframe conditions.',
    icon: Cpu,
    phase: 'Phase 3 Planned',
  },
  backtesting: {
    title: 'Historical Backtesting',
    subtitle: 'Event-driven backtesting engine with slippage, transaction costs, and Sharpe ratio analysis.',
    icon: History,
    phase: 'Phase 4 Planned',
  },
  paper_trading: {
    title: 'Paper Trading Simulator',
    subtitle: 'Virtual trade simulation, order book simulation, and risk-free strategy experimentation.',
    icon: Coins,
    phase: 'Phase 4 Planned',
  },
  portfolio: {
    title: 'Portfolio & Position Analytics',
    subtitle: 'Sector exposure breakdown, asset allocation, and draw-down analysis.',
    icon: Briefcase,
    phase: 'Phase 5 Planned',
  },
  trade_journal: {
    title: 'Trader Journal & Logbook',
    subtitle: 'Trade rationale logging, emotional discipline metrics, and performance review tags.',
    icon: BookOpen,
    phase: 'Phase 5 Planned',
  },
  risk_management: {
    title: 'Risk Management Controls',
    subtitle: 'Position sizing calculator, daily max loss guardrails, and value-at-risk limits.',
    icon: ShieldAlert,
    phase: 'Phase 6 Planned',
  },
  settings: {
    title: 'Terminal & Local Settings',
    subtitle: 'API configurations, local SQLite preferences, themes, and adapter credentials.',
    icon: Settings,
    phase: 'Phase 6 Planned',
  },
  buy_approval: {
    title: 'BUY Approval Center',
    subtitle: 'Human-in-the-loop explicit BUY order approval.',
    icon: ShieldAlert,
    phase: 'Workflow Active',
  },
  positions: {
    title: 'Open Positions & Exit Monitor',
    subtitle: 'Real-time price monitoring and autonomous exit tracking.',
    icon: Layers,
    phase: 'Workflow Active',
  },
  reports: {
    title: 'Trade Reports & Post-Mortem',
    subtitle: 'Post-trade audit reports and realized PnL analysis.',
    icon: BookOpen,
    phase: 'Workflow Active',
  },
  audit_trail: {
    title: 'Audit Trail',
    subtitle: 'Append-only chronological audit log.',
    icon: ShieldAlert,
    phase: 'Workflow Active',
  },
  vibe_intelligence: {
    title: 'Vibe Intelligence Core',
    subtitle: 'Modular multi-agent decision architecture, evidence confluence, and controlled strategy adaptation.',
    icon: Brain,
    phase: 'Workflow Active',
  },
  market_data: {
    title: 'Market Data Sources & CSV Provider',
    subtitle: 'Preloaded historical datasets and custom CSV ingestion engine.',
    icon: Layers,
    phase: 'Active',
  },
  broker_connection: {
    title: 'Broker Integration (Zerodha)',
    subtitle: 'Kite Connect Personal Free API and fail-closed live safety enforcement.',
    icon: ShieldAlert,
    phase: 'Active',
  },
  watchlist: {
    title: 'Watchlist Management',
    subtitle: 'Track multi-asset instruments, signals, and price quotes.',
    icon: TrendingUp,
    phase: 'Active',
  },
  strategy_comparison: {
    title: 'Strategy Comparison',
    subtitle: 'Side-by-side neutral comparison of 7 rule-based strategies.',
    icon: Cpu,
    phase: 'Active',
  },
  market_replay: {
    title: 'Market Replay Mode',
    subtitle: 'Causal chronological backtest step playback and simulation.',
    icon: History,
    phase: 'Active',
  },
  performance: {
    title: 'Performance Analytics',
    subtitle: 'Portfolio KPIs, win-rate, equity and drawdown curves.',
    icon: Briefcase,
    phase: 'Active',
  },
  data_manager: {
    title: 'Data Manager & CSV Storage',
    subtitle: 'Historical dataset inspection, uploading, and causal validation.',
    icon: Layers,
    phase: 'Active',
  },
  alerts: {
    title: 'Alert Notification Center',
    subtitle: 'Configurable trigger alerts with zero trade execution side-effects.',
    icon: ShieldAlert,
    phase: 'Active',
  },
  exports: {
    title: 'Report & Data Exports',
    subtitle: 'Downloadable CSV and JSON reports with credentials sanitized.',
    icon: BookOpen,
    phase: 'Active',
  },
  system_health: {
    title: 'System Health Diagnostics',
    subtitle: 'Real-time telemetry across 9 platform subsystems.',
    icon: Layers,
    phase: 'Active',
  },
  xgboost_research: {
    title: 'XGBoost ML Research Engine',
    subtitle: 'Causal machine learning, walk-forward validation, and Qwen synthesis.',
    icon: Cpu,
    phase: 'Active',
  },
};

export const PlaceholderView: React.FC<PlaceholderViewProps> = ({ tabId }) => {
  const meta = TAB_METADATA[tabId] || TAB_METADATA.overview;
  const Icon = meta.icon;

  return (
    <div className="bg-panel border border-border rounded-lg p-12 flex flex-col items-center justify-center text-center shadow-lg shadow-black/20 min-h-[500px]">
      <div className="w-16 h-16 rounded-2xl bg-panel-subtle border border-border flex items-center justify-center mb-4 text-accent shadow-inner">
        <Icon className="w-8 h-8" />
      </div>

      <div className="flex items-center gap-2 mb-2">
        <h2 className="text-xl font-bold text-slate-100 tracking-wide font-mono">
          {meta.title}
        </h2>
        <Badge variant="accent" size="sm">
          {meta.phase}
        </Badge>
      </div>

      <p className="text-sm text-slate-400 max-w-md mb-6 leading-relaxed">
        {meta.subtitle}
      </p>

      <div className="bg-background/80 border border-border/80 rounded-md p-4 max-w-lg text-left text-xs font-mono space-y-2">
        <div className="flex items-center gap-2 text-amber-400 font-semibold">
          <Construction className="w-4 h-4" />
          <span>Foundation Scope (Step 1)</span>
        </div>
        <p className="text-slate-400 leading-normal">
          In this initial phase, the navigation and full Overview dashboard are implemented with SQLite database models, FastAPI backend endpoints, and TradingView charting.
        </p>
        <div className="text-[11px] text-slate-400 pt-2 border-t border-border">
          Database schema for this module is initialized in SQLite. Backend models are ready for integration.
        </div>
      </div>
    </div>
  );
};
