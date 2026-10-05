import React from 'react';
import {
  Wallet,
  TrendingUp,
  Percent,
  Cpu,
  Layers,
  ShieldCheck,
  ArrowUpRight,
} from 'lucide-react';
import { PortfolioSummary } from '../../types/market';
import { Badge } from '../common/Badge';

interface PortfolioCardProps {
  portfolio: PortfolioSummary | null;
}

export const PortfolioCard: React.FC<PortfolioCardProps> = ({ portfolio }) => {
  const isPnlPositive = (portfolio?.daily_pnl || 0) >= 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Total Portfolio Demo Value */}
      <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-cyan-500/30 transition-all duration-300 group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-cyan-500/10 transition-colors" />
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Wallet className="w-3.5 h-3.5 text-cyan-400" />
            Total Demo Value
          </span>
          <Badge variant="demo" size="sm">
            DEMO
          </Badge>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl lg:text-3xl font-extrabold font-mono text-white tracking-tight drop-shadow-[0_0_12px_rgba(255,255,255,0.15)]">
            ${(portfolio?.total_value || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="mt-3 pt-2.5 border-t border-white/[0.05] text-[11px] text-slate-400 font-mono flex items-center justify-between">
          <span className="text-slate-500">Base Currency: USD</span>
          <span className="text-emerald-400 font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Virtual Funds
          </span>
        </div>
      </div>

      {/* 2. Available Virtual Balance */}
      <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-emerald-500/30 transition-all duration-300 group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-emerald-500/10 transition-colors" />
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            Available Virtual Cash
          </span>
          <Badge variant="demo" size="sm">
            DEMO
          </Badge>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl lg:text-3xl font-extrabold font-mono text-emerald-400 tracking-tight drop-shadow-[0_0_12px_rgba(16,185,129,0.2)]">
            ${(portfolio?.available_cash || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="mt-3 pt-2.5 border-t border-white/[0.05] text-[11px] text-slate-400 font-mono flex items-center justify-between">
          <span className="text-slate-500">Unallocated Margin</span>
          <span className="text-slate-300 font-medium">
            {(((portfolio?.available_cash || 0) / (portfolio?.total_value || 1)) * 100).toFixed(0)}% Liquidity
          </span>
        </div>
      </div>

      {/* 3. Daily Simulated P&L */}
      <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-slate-600 transition-all duration-300 group">
        <div className={`absolute top-0 right-0 w-28 h-28 rounded-full blur-2xl pointer-events-none transition-colors ${isPnlPositive ? 'bg-emerald-500/5 group-hover:bg-emerald-500/10' : 'bg-rose-500/5 group-hover:bg-rose-500/10'}`} />
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <TrendingUp className={`w-3.5 h-3.5 ${isPnlPositive ? 'text-emerald-400' : 'text-rose-400'}`} />
            Simulated Daily P&L
          </span>
          <Badge variant="demo" size="sm">
            DEMO
          </Badge>
        </div>
        <div className="mt-3 flex items-baseline gap-2.5">
          <span
            className={`text-2xl lg:text-3xl font-extrabold font-mono tracking-tight ${
              isPnlPositive
                ? 'text-emerald-400 drop-shadow-[0_0_12px_rgba(16,185,129,0.25)]'
                : 'text-rose-400 drop-shadow-[0_0_12px_rgba(244,63,94,0.25)]'
            }`}
          >
            {isPnlPositive ? '+' : ''}${Math.abs(portfolio?.daily_pnl || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
          <span
            className={`text-xs font-semibold font-mono px-2 py-0.5 rounded-md border ${
              isPnlPositive
                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
            }`}
          >
            {isPnlPositive ? '+' : ''}
            {portfolio?.daily_pnl_percent || 0}%
          </span>
        </div>
        <div className="mt-3 pt-2.5 border-t border-white/[0.05] text-[11px] text-slate-400 font-mono flex items-center justify-between">
          <span className="text-slate-500">Paper Session Today</span>
          <span className="text-amber-400/90 font-medium">Non-Monetary</span>
        </div>
      </div>

      {/* 4. Active Strategies & Positions */}
      <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-cyan-500/30 transition-all duration-300 group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-indigo-500/10 transition-colors" />
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            Strategies & Positions
          </span>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline justify-between">
          <div>
            <div className="text-2xl lg:text-3xl font-extrabold font-mono text-white tracking-tight">
              {portfolio?.active_strategies_count || 0}
            </div>
            <div className="text-[10px] text-slate-500 uppercase font-mono mt-0.5 tracking-wider">
              Active Strategies
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl lg:text-3xl font-extrabold font-mono text-cyan-400 drop-shadow-[0_0_10px_rgba(14,165,233,0.3)]">
              {portfolio?.open_positions_count || 0}
            </div>
            <div className="text-[10px] text-slate-500 uppercase font-mono mt-0.5 tracking-wider">
              Open Positions
            </div>
          </div>
        </div>
        <div className="mt-3 pt-2.5 border-t border-white/[0.05] text-[11px] text-slate-400 font-mono flex items-center justify-between">
          <span className="text-slate-500">Model: Rule-based</span>
          <span className="text-cyan-400 font-medium">Surveillance Active</span>
        </div>
      </div>
    </div>
  );
};
