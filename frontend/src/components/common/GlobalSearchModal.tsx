import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  LayoutDashboard,
  TrendingUp,
  LineChart,
  Sparkles,
  Cpu,
  Layers,
  ShieldCheck,
  Coins,
  Briefcase,
  BookOpen,
  History,
  Brain,
  Database,
  KeyRound,
  FileSpreadsheet,
  FileCheck,
  ShieldAlert,
  Settings,
  Bell,
  PlaySquare,
  Activity,
  ArrowRight,
  Command,
  Zap,
} from 'lucide-react';
import { NavTabId } from '../../types/market';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (tab: NavTabId, symbol?: string) => void;
}

interface SearchItem {
  id: string;
  category: 'NAVIGATION' | 'INSTRUMENT' | 'ACTION';
  label: string;
  sublabel: string;
  icon: React.ElementType;
  tab: NavTabId;
  symbol?: string;
}

const SEARCH_DATABASE: SearchItem[] = [
  // Navigation
  { id: 'nav-overview', category: 'NAVIGATION', label: 'Overview Dashboard', sublabel: 'Main cockpit with market summary and quick stats', icon: LayoutDashboard, tab: 'overview' },
  { id: 'nav-watchlist', category: 'NAVIGATION', label: 'Watchlist Management', sublabel: 'Organized instruments, price tags, and custom groups', icon: TrendingUp, tab: 'watchlist' },
  { id: 'nav-market-watch', category: 'NAVIGATION', label: 'Market Watch', sublabel: 'Live multi-asset ticker board and quotes', icon: TrendingUp, tab: 'market_watch' },
  { id: 'nav-ta', category: 'NAVIGATION', label: 'Technical Analysis Studio', sublabel: '13 causal indicators, candlestick chart, overlays', icon: LineChart, tab: 'technical_analysis' },
  { id: 'nav-ai', category: 'NAVIGATION', label: 'AI Reasoning & Intelligence', sublabel: 'Deep multi-agent causal market analysis', icon: Sparkles, tab: 'ai_insights' },
  { id: 'nav-strat', category: 'NAVIGATION', label: 'Strategy Lab', sublabel: '7 prebuilt deterministic algorithmic strategies', icon: Cpu, tab: 'strategies' },
  { id: 'nav-strat-comp', category: 'NAVIGATION', label: 'Strategy Comparison', sublabel: 'Side-by-side neutral multi-strategy evaluation', icon: Cpu, tab: 'strategy_comparison' },
  { id: 'nav-replay', category: 'NAVIGATION', label: 'Market Replay Mode', sublabel: 'Step-by-step chronological backtest simulation', icon: PlaySquare, tab: 'market_replay' },
  { id: 'nav-buy', category: 'NAVIGATION', label: 'BUY Approval Center', sublabel: 'Step 4 mandatory human gatekeeper for proposals', icon: ShieldCheck, tab: 'buy_approval' },
  { id: 'nav-positions', category: 'NAVIGATION', label: 'Open Positions', sublabel: 'Active paper portfolio positions with P&L', icon: Layers, tab: 'positions' },
  { id: 'nav-paper', category: 'NAVIGATION', label: 'Paper Trading Terminal', sublabel: 'Simulated execution orders, P&L, and blotter', icon: Coins, tab: 'paper_trading' },
  { id: 'nav-port', category: 'NAVIGATION', label: 'Portfolio Analytics', sublabel: 'Simulated cash, equity curve, margin exposure', icon: Briefcase, tab: 'portfolio' },
  { id: 'nav-perf', category: 'NAVIGATION', label: 'Performance Analytics', sublabel: 'Win-rate, profit factor, drawdown curves', icon: Activity, tab: 'performance' },
  { id: 'nav-journal', category: 'NAVIGATION', label: 'Trade Journal', sublabel: 'Qualitative reflections, psychology tags, notes', icon: BookOpen, tab: 'trade_journal' },
  { id: 'nav-backtest', category: 'NAVIGATION', label: 'Dynamic Backtesting', sublabel: 'Historical backtests on validated datasets', icon: History, tab: 'backtesting' },
  { id: 'nav-xgboost', category: 'NAVIGATION', label: 'XGBoost Research Engine', sublabel: 'Causal machine learning, walk-forward validation, Qwen synthesis', icon: Cpu, tab: 'xgboost_research' },
  { id: 'nav-data', category: 'NAVIGATION', label: 'Data Manager & CSV', sublabel: 'Inspect, upload, and validate historical OHLCV data', icon: Database, tab: 'data_manager' },
  { id: 'nav-alerts', category: 'NAVIGATION', label: 'Alert Notification Center', sublabel: 'Threshold rules, notifications, zero trading side-effects', icon: Bell, tab: 'alerts' },
  { id: 'nav-exports', category: 'NAVIGATION', label: 'Report & Data Exports', sublabel: 'Download CSV and JSON with zero credentials', icon: FileSpreadsheet, tab: 'exports' },
  { id: 'nav-health', category: 'NAVIGATION', label: 'System Health Diagnostics', sublabel: 'Real-time telemetry across 9 subsystems', icon: Activity, tab: 'system_health' },
  { id: 'nav-risk', category: 'NAVIGATION', label: 'Risk & Safety Guardian', sublabel: 'Deterministic boundaries and circuit breakers', icon: ShieldAlert, tab: 'risk_management' },
  { id: 'nav-broker', category: 'NAVIGATION', label: 'Broker (Zerodha)', sublabel: 'Free read-only Kite Connect adapter', icon: KeyRound, tab: 'broker_connection' },
  { id: 'nav-settings', category: 'NAVIGATION', label: 'Settings Center', sublabel: 'Consolidated configurations and audited parameters', icon: Settings, tab: 'settings' },

  // Instruments
  { id: 'inst-nifty', category: 'INSTRUMENT', label: 'NIFTY 50', sublabel: 'NSE Benchmark Index • Indian Equities', icon: LineChart, tab: 'technical_analysis', symbol: 'NIFTY 50' },
  { id: 'inst-banknifty', category: 'INSTRUMENT', label: 'BANKNIFTY', sublabel: 'Banking Sector Index • NSE', icon: LineChart, tab: 'technical_analysis', symbol: 'BANKNIFTY' },
  { id: 'inst-reliance', category: 'INSTRUMENT', label: 'RELIANCE', sublabel: 'Reliance Industries Ltd • NSE Equities', icon: LineChart, tab: 'technical_analysis', symbol: 'RELIANCE' },
  { id: 'inst-tcs', category: 'INSTRUMENT', label: 'TCS', sublabel: 'Tata Consultancy Services • NSE Equities', icon: LineChart, tab: 'technical_analysis', symbol: 'TCS' },
  { id: 'inst-eurusd', category: 'INSTRUMENT', label: 'EUR/USD', sublabel: 'Euro / US Dollar • FOREX', icon: LineChart, tab: 'technical_analysis', symbol: 'EUR/USD' },
  { id: 'inst-gbpusd', category: 'INSTRUMENT', label: 'GBP/USD', sublabel: 'British Pound / US Dollar • FOREX', icon: LineChart, tab: 'technical_analysis', symbol: 'GBP/USD' },
  { id: 'inst-btcusd', category: 'INSTRUMENT', label: 'BTC/USD', sublabel: 'Bitcoin / US Dollar • CRYPTO', icon: LineChart, tab: 'technical_analysis', symbol: 'BTC/USD' },
  { id: 'inst-gold', category: 'INSTRUMENT', label: 'GOLD', sublabel: 'Gold Spot / Futures • COMMODITY', icon: LineChart, tab: 'technical_analysis', symbol: 'GOLD' },
  { id: 'inst-crude', category: 'INSTRUMENT', label: 'CRUDEOIL', sublabel: 'Crude Oil Light Sweet • COMMODITY', icon: LineChart, tab: 'technical_analysis', symbol: 'CRUDEOIL' },

  // Quick Actions
  { id: 'act-new-trade', category: 'ACTION', label: 'Execute Paper Order', sublabel: 'Jump straight to paper trading terminal', icon: Zap, tab: 'paper_trading' },
  { id: 'act-approval', category: 'ACTION', label: 'Review Pending Proposals', sublabel: 'Open BUY human approval queue', icon: ShieldCheck, tab: 'buy_approval' },
  { id: 'act-export', category: 'ACTION', label: 'Export Trades CSV', sublabel: 'Download sanitized simulation logs', icon: FileSpreadsheet, tab: 'exports' },
  { id: 'act-diagnostics', category: 'ACTION', label: 'Probe System Health', sublabel: 'Run real-time diagnostics on 9 subsystems', icon: Activity, tab: 'system_health' },
  { id: 'act-alerts', category: 'ACTION', label: 'Configure Alert Rules', sublabel: 'Set up price & indicator trigger notifications', icon: Bell, tab: 'alerts' },
];

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
  onSelect,
}) => {
  const [query, setQuery] = useState<string>('');
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const filteredItems = SEARCH_DATABASE.filter((item) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      item.label.toLowerCase().includes(q) ||
      item.sublabel.toLowerCase().includes(q) ||
      (item.symbol && item.symbol.toLowerCase().includes(q))
    );
  }).slice(0, 10);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % (filteredItems.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % (filteredItems.length || 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredItems[selectedIndex]) {
          const item = filteredItems[selectedIndex];
          onSelect(item.tab, item.symbol);
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredItems, selectedIndex, onClose, onSelect]);

  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/75 backdrop-blur-sm animate-in fade-in"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-xl bg-[#0B101D] border border-white/[0.12] rounded-xl shadow-2xl overflow-hidden flex flex-col"
      >
        {/* Search Input Bar */}
        <div className="p-3.5 border-b border-white/[0.08] flex items-center gap-3 bg-white/[0.02]">
          <Search className="w-4 h-4 text-cyan-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a view, symbol (NIFTY 50, EUR/USD), or action..."
            className="w-full bg-transparent text-sm text-white placeholder:text-slate-500 focus:outline-none font-mono"
          />
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-white/[0.04] border border-white/[0.08] rounded">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 space-y-1">
          {filteredItems.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              <Search className="w-6 h-6 mx-auto mb-2 text-slate-600" />
              <p className="text-xs font-mono">No matching results for "{query}"</p>
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;

              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelect(item.tab, item.symbol);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center justify-between p-2.5 rounded-lg text-left transition-colors font-mono ${
                    isSelected
                      ? 'bg-cyan-500/15 border border-cyan-500/30 text-white'
                      : 'hover:bg-white/[0.04] text-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-3 truncate">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                        isSelected ? 'bg-cyan-500 text-white' : 'bg-white/[0.04] text-slate-400'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div className="truncate">
                      <div className="text-xs font-bold text-white flex items-center gap-2">
                        {item.label}
                        <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-white/[0.04] text-slate-400 border border-white/[0.06]">
                          {item.category}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 truncate">{item.sublabel}</div>
                    </div>
                  </div>

                  <ArrowRight
                    className={`w-3.5 h-3.5 shrink-0 ${
                      isSelected ? 'text-cyan-400 opacity-100' : 'opacity-0'
                    }`}
                  />
                </button>
              );
            })
          )}
        </div>

        {/* Footer Shortcut Hints */}
        <div className="p-2.5 bg-[#070A12] border-t border-white/[0.06] flex items-center justify-between text-[10px] font-mono text-slate-500">
          <div className="flex items-center gap-3">
            <span>&uarr;&darr; Navigate</span>
            <span>&crarr; Select</span>
            <span>ESC Close</span>
          </div>
          <span className="flex items-center gap-1 text-slate-400">
            <Command className="w-3 h-3" /> Quick Switcher
          </span>
        </div>
      </div>
    </div>
  );
};
