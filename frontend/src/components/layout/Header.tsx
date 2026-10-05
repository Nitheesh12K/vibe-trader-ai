import React from 'react';
import {
  Search,
  Server,
  RefreshCw,
  Clock,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  Menu,
  Coins,
  Bell,
  Command,
} from 'lucide-react';
import { HealthResponse, MarketStatusItem, NavTabId } from '../../types/market';
import { Badge, StatusBadge } from '../common/Badge';

interface HeaderProps {
  health: HealthResponse | null;
  healthLoading: boolean;
  marketStatuses: MarketStatusItem[];
  onRefresh: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onOpenHelp?: () => void;
  onToggleMobileSidebar?: () => void;
  onOpenSearch?: () => void;
  onNavigateTab?: (tab: NavTabId) => void;
  unreadAlertsCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  healthLoading,
  marketStatuses,
  onRefresh,
  searchQuery,
  onSearchChange,
  onOpenHelp,
  onToggleMobileSidebar,
  onOpenSearch,
  onNavigateTab,
  unreadAlertsCount = 0,
}) => {
  const isConnected = !!health && health.status === 'ok';

  return (
    <header className="h-14 bg-[#0B101D]/85 backdrop-blur-xl border-b border-white/[0.08] px-3 sm:px-4 flex items-center justify-between gap-3 select-none shrink-0 z-20 shadow-sm">
      {/* Left: Mobile Menu Toggle + Search Bar */}
      <div className="flex items-center gap-2.5 flex-1 max-w-md">
        {onToggleMobileSidebar && (
          <button
            onClick={onToggleMobileSidebar}
            aria-label="Toggle navigation menu"
            className="md:hidden p-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-300"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        <div className="relative w-full flex items-center">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            onClick={() => onOpenSearch && onOpenSearch()}
            placeholder="Search instruments or press Ctrl+K..."
            className="w-full bg-[#070A12]/80 border border-white/[0.08] rounded-lg pl-8 pr-14 py-1.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/20 font-mono"
          />
          {onOpenSearch && (
            <button
              onClick={onOpenSearch}
              className="absolute right-2 top-1/2 -translate-y-1/2 hidden sm:flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-400 hover:text-slate-200 text-[10px] font-mono border border-white/[0.08]"
              title="Open Command Palette (Ctrl+K)"
            >
              <span>Ctrl K</span>
            </button>
          )}
        </div>
      </div>

      {/* Middle: Market Status Indicators */}
      <div className="hidden xl:flex items-center gap-2">
        {marketStatuses.map((m) => (
          <div
            key={m.market}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] text-[11px] font-mono shadow-sm"
            title={`${m.label} (${m.session_hours}) - Status: ${m.status}`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                m.status === 'OPEN'
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse'
                  : 'bg-slate-500'
              }`}
            />
            <span className="text-slate-300 font-semibold">{m.market}:</span>
            <span className={m.status === 'OPEN' ? 'text-emerald-400 font-medium' : 'text-slate-400'}>
              {m.status}
            </span>
          </div>
        ))}
      </div>

      {/* Right Controls: Notification Bell, Paper Badge, API Status, Tour, Refresh */}
      <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
        {/* Prominent Paper Trading & Demo Badges */}
        <StatusBadge status="PAPER TRADING" size="sm" className="hidden sm:inline-flex" />
        <StatusBadge status="DEMO DATA" size="sm" className="hidden sm:inline-flex" />

        {/* In-App Notification Center Bell */}
        {onNavigateTab && (
          <button
            onClick={() => onNavigateTab('alerts')}
            className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 hover:text-white transition-colors border border-white/[0.06] relative"
            title="Alert Notifications Center"
          >
            <Bell className="w-4 h-4 text-slate-400" />
            {unreadAlertsCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-cyan-500 text-white text-[9px] font-bold font-mono flex items-center justify-center animate-pulse">
                {unreadAlertsCount > 9 ? '9+' : unreadAlertsCount}
              </span>
            )}
          </button>
        )}

        {/* Backend Online/Offline Badge */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border shadow-sm ${
            isConnected
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
          title={isConnected ? 'FastAPI Backend Online & SQLite Connected' : 'Backend Unreachable'}
        >
          <Server className="w-3 h-3" />
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isConnected
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse'
                : 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]'
            }`}
          />
          <span className="font-semibold hidden sm:inline">
            {isConnected ? 'API ONLINE' : 'API OFFLINE'}
          </span>
        </div>

        {/* Help / Guide Onboarding Modal Trigger */}
        {onOpenHelp && (
          <button
            onClick={onOpenHelp}
            className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 hover:text-white transition-colors border border-white/[0.06] flex items-center gap-1 text-xs"
            title="Open Welcome Guide & System Architecture"
          >
            <HelpCircle className="w-4 h-4 text-cyan-400" />
            <span className="hidden md:inline font-mono text-[11px]">Tour</span>
          </button>
        )}

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={healthLoading}
          className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-400 hover:text-slate-100 transition-colors border border-white/[0.06]"
          title="Refresh Market Data"
        >
          <RefreshCw className={`w-4 h-4 ${healthLoading ? 'animate-spin text-cyan-400' : ''}`} />
        </button>
      </div>
    </header>
  );
};
