import React from 'react';
import {
  LayoutDashboard,
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
  ChevronLeft,
  ChevronRight,
  Activity,
  ShieldCheck,
  Layers,
  FileSpreadsheet,
  FileCheck,
  Brain,
  Database,
  KeyRound,
  Bell,
  PlaySquare,
  BarChart3,
  Sliders,
} from 'lucide-react';
import { NavTabId } from '../../types/market';

interface SidebarProps {
  activeTab: NavTabId;
  onTabChange: (tab: NavTabId) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  pendingProposalsCount?: number;
}

interface NavItem {
  id: NavTabId;
  label: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'watchlist', label: 'Watchlist', icon: TrendingUp, badge: 'Custom', badgeColor: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30' },
  { id: 'market_watch', label: 'Market Watch', icon: TrendingUp },
  { id: 'technical_analysis', label: 'Technical Analysis', icon: LineChart },
  { id: 'ai_insights', label: 'AI Reasoning', icon: Sparkles, badge: 'AI', badgeColor: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30' },
  { id: 'strategies', label: 'Strategy Lab', icon: Cpu, badge: '7 Prebuilt', badgeColor: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30' },
  { id: 'strategy_comparison', label: 'Strategy Comparison', icon: BarChart3, badge: 'Multi', badgeColor: 'text-violet-400 bg-violet-500/10 border-violet-500/30' },
  { id: 'market_replay', label: 'Market Replay', icon: PlaySquare, badge: 'Causal', badgeColor: 'text-sky-400 bg-sky-500/10 border-sky-500/30' },
  {
    id: 'buy_approval',
    label: 'BUY Approval',
    icon: ShieldCheck,
    badge: 'Step 4',
    badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30 font-bold',
  },
  { id: 'positions', label: 'Open Positions', icon: Layers },
  { id: 'paper_trading', label: 'Paper Trading', icon: Coins, badge: 'Demo', badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
  { id: 'portfolio', label: 'Portfolio', icon: Briefcase },
  { id: 'performance', label: 'Performance Analytics', icon: Activity, badge: 'KPIs', badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  { id: 'trade_journal', label: 'Trade Journal', icon: BookOpen },
  { id: 'backtesting', label: 'Backtesting', icon: History },
  {
    id: 'xgboost_research',
    label: 'XGBoost ML',
    icon: Cpu,
    badge: 'Research',
    badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30 font-bold',
  },
  { id: 'data_manager', label: 'Data Manager', icon: Database, badge: 'Datasets', badgeColor: 'text-blue-400 bg-blue-500/10 border-blue-500/30' },
  { id: 'market_data', label: 'Market Data & CSV', icon: Database, badge: 'CSV', badgeColor: 'text-blue-400 bg-blue-500/10 border-blue-500/30' },
  { id: 'alerts', label: 'Alerts', icon: Bell, badge: 'Rules', badgeColor: 'text-pink-400 bg-pink-500/10 border-pink-500/30' },
  { id: 'reports', label: 'Trade Reports', icon: FileSpreadsheet },
  { id: 'exports', label: 'Report Exports', icon: FileSpreadsheet, badge: 'CSV/JSON', badgeColor: 'text-purple-400 bg-purple-500/10 border-purple-500/30' },
  { id: 'system_health', label: 'System Health', icon: Activity, badge: '9 Probes', badgeColor: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30' },
  { id: 'risk_management', label: 'Risk & Safety', icon: ShieldAlert },
  {
    id: 'vibe_intelligence',
    label: 'Vibe Intelligence',
    icon: Brain,
    badge: 'Core',
    badgeColor: 'text-purple-400 bg-purple-500/10 border-purple-500/30 font-bold',
  },
  { id: 'broker_connection', label: 'Broker (Zerodha)', icon: KeyRound, badge: 'Free API', badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  collapsed,
  onToggleCollapse,
  pendingProposalsCount,
}) => {
  return (
    <aside
      className={`h-screen bg-[#0B101D]/90 backdrop-blur-2xl border-r border-white/[0.08] flex flex-col transition-all duration-300 select-none z-30 shrink-0 shadow-lg ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-14 flex items-center justify-between px-3 border-b border-white/[0.08]">
        {!collapsed ? (
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 via-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25 shrink-0">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div className="truncate">
              <span className="font-bold text-sm tracking-tight text-white block">
                VIBE TRADER <span className="text-cyan-400 font-mono text-xs">AI</span>
              </span>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                Multi-Market Research
              </span>
            </div>
          </div>
        ) : (
          <div className="w-full flex justify-center">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 via-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
              <Activity className="w-4 h-4 text-white" />
            </div>
          </div>
        )}

        <button
          onClick={onToggleCollapse}
          className="p-1 rounded-lg hover:bg-white/[0.06] text-slate-400 hover:text-white transition-colors ml-auto"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              title={collapsed ? item.label : undefined}
              className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-all group relative ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/15 via-cyan-500/5 to-transparent border-l-2 border-cyan-400 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-white/[0.04]'
              }`}
            >
              <Icon
                className={`w-4 h-4 shrink-0 transition-transform ${
                  isActive ? 'text-cyan-400 scale-105' : 'text-slate-400 group-hover:text-slate-200'
                }`}
              />

              {!collapsed && (
                <span className="truncate flex-1 text-left">{item.label}</span>
              )}

              {!collapsed && item.id === 'buy_approval' && pendingProposalsCount && pendingProposalsCount > 0 ? (
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase font-bold text-amber-300 bg-amber-500/20 border-amber-500/40 animate-pulse">
                  {pendingProposalsCount} PENDING
                </span>
              ) : (
                !collapsed && item.badge && (
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase font-semibold ${item.badgeColor}`}
                  >
                    {item.badge}
                  </span>
                )
              )}

              {/* Collapsed Tooltip Indicator */}
              {collapsed && (
                <div className="absolute left-full ml-2 px-2.5 py-1 bg-[#0F172A] text-slate-100 text-[11px] rounded-md shadow-xl border border-white/[0.1] opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity">
                  {item.label}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer Environment Tag */}
      <div className="p-3 border-t border-white/[0.08]">
        {!collapsed ? (
          <div className="bg-white/[0.02] rounded-lg p-2.5 border border-white/[0.06] text-[11px]">
            <div className="flex items-center justify-between text-slate-400">
              <span className="font-mono text-[10px] tracking-wider text-slate-500">LOCAL-FIRST</span>
              <span className="flex items-center gap-1.5 font-mono text-[10px] text-emerald-400 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                SIMULATION SAFE
              </span>
            </div>
            <div className="mt-1 text-[10px] text-slate-500 font-mono">
              Broker: Kite Read-Only
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <span className="w-2 h-2 rounded-full bg-emerald-400" title="Local Simulation Safe" />
          </div>
        )}
      </div>
    </aside>
  );
};
