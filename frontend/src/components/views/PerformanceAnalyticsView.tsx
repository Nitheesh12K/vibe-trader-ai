import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  BarChart2,
  PieChart,
  RotateCcw,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  Briefcase,
  Layers,
  ArrowUpRight,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  PerformanceSummaryData,
  PerformanceByStrategyData,
  PerformanceBySymbolData,
  NavTabId,
} from '../../types/market';

interface PerformanceAnalyticsViewProps {
  onNavigate?: (tab: NavTabId, symbol?: string) => void;
}

export const PerformanceAnalyticsView: React.FC<PerformanceAnalyticsViewProps> = ({ onNavigate }) => {
  const [summary, setSummary] = useState<PerformanceSummaryData | null>(null);
  const [strategyStats, setStrategyStats] = useState<PerformanceByStrategyData[]>([]);
  const [symbolStats, setSymbolStats] = useState<PerformanceBySymbolData[]>([]);
  const [activeTab, setActiveTab] = useState<'PAPER' | 'BACKTEST'>('PAPER');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [sum, strat, sym] = await Promise.all([
        api.getPerformanceSummary(),
        api.getPerformanceByStrategy(),
        api.getPerformanceBySymbol(),
      ]);
      setSummary(sum);
      setStrategyStats(strat);
      setSymbolStats(sym);
    } catch (err: any) {
      setError(err.message || 'Failed to load performance analytics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleResetDefaults = async () => {
    if (!window.confirm('Reset simulated balance to calibrated initial state?')) return;
    try {
      await api.resetRiskDefaults();
      await fetchData();
    } catch (err: any) {
      setError('Failed to reset defaults.');
    }
  };

  const isProfitable = (summary?.realized_pnl || 0) >= 0;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-white/10 backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-white flex items-center gap-2">
              <span className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <BarChart2 className="w-5 h-5" />
              </span>
              Performance Analytics
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Reconciled Quantitative Ledger
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Realized trade attribution, win-loss distributions, risk parameters, and equity curve trajectory.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white transition border border-white/5"
            title="Refresh Ledger"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
          <button
            onClick={handleResetDefaults}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-mono border border-white/10 transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Initial Baseline
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="underline">
            Dismiss
          </button>
        </div>
      )}

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/10 space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Total Virtual Equity</span>
          <span className="text-lg font-bold font-mono text-white">
            ₹{summary?.total_equity?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || '0.00'}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block">Cash: ₹{summary?.available_cash?.toFixed(2)}</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/10 space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Realized Net P&amp;L</span>
          <span className={`text-lg font-bold font-mono ${isProfitable ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isProfitable ? '+' : ''}₹{summary?.realized_pnl?.toFixed(2) || '0.00'}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block">Excludes open floating</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/10 space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Win Rate</span>
          <span className="text-lg font-bold font-mono text-cyan-400">
            {summary?.win_rate !== undefined ? summary.win_rate.toFixed(1) : '0.0'}%
          </span>
          <span className="text-[10px] text-slate-500 font-mono block">
            {summary?.winning_trades || 0} Wins / {summary?.losing_trades || 0} Losses
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/10 space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Total Trades</span>
          <span className="text-lg font-bold font-mono text-white">
            {summary?.total_trades || 0}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block">Paper closed cycles</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/10 space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Profit Factor</span>
          <span className="text-lg font-bold font-mono text-slate-200">
            {summary?.profit_factor !== undefined ? summary.profit_factor.toFixed(2) : '1.00'}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block">Gross gain / loss</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/10 space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Max Drawdown</span>
          <span className="text-lg font-bold font-mono text-rose-400">
            {summary?.max_drawdown_pct || 0}%
          </span>
          <span className="text-[10px] text-slate-500 font-mono block">Peak-to-trough</span>
        </div>
      </div>

      {/* Equity Curve Graph Card */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            Equity Curve &amp; Cumulative Performance Trajectory
          </h3>
          <span className="text-xs font-mono text-slate-400">
            Total Points: {summary?.equity_curve?.length || 0}
          </span>
        </div>

        {summary?.equity_curve && summary.equity_curve.length > 1 ? (
          <div className="space-y-2">
            {/* Simple visual representation of equity curve */}
            <div className="h-44 w-full bg-slate-950/70 rounded-xl p-4 flex items-end gap-1.5 overflow-x-auto border border-white/5">
              {summary.equity_curve.map((pt, idx) => {
                const minEq = Math.min(...summary.equity_curve.map((p) => p.equity));
                const maxEq = Math.max(...summary.equity_curve.map((p) => p.equity));
                const range = maxEq - minEq || 1;
                const heightPct = Math.max(10, Math.min(100, Math.round(((pt.equity - minEq) / range) * 90 + 10)));
                return (
                  <div
                    key={idx}
                    className="flex-1 min-w-[12px] bg-gradient-to-t from-cyan-500/20 to-emerald-400 rounded-t transition-all hover:to-cyan-300 relative group/bar"
                    style={{ height: `${heightPct}%` }}
                  >
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover/bar:block z-10 bg-slate-900 text-white text-[10px] font-mono px-2 py-1 rounded shadow border border-white/10 whitespace-nowrap">
                      <div>₹{pt.equity.toFixed(2)}</div>
                      <div className="text-slate-400">{pt.time}</div>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>Origin</span>
              <span>Latest Snapshot</span>
            </div>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-500 font-mono text-xs">
            Equity curve generates automatically as paper trades are opened and closed.
          </div>
        )}
      </div>

      {/* Two-Column Breakdowns: By Strategy and By Symbol */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Strategy Breakdown */}
        <div className="bg-slate-900/60 rounded-2xl border border-white/10 overflow-hidden shadow-xl">
          <div className="p-4 bg-slate-950/60 border-b border-white/10 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              Performance by Strategy
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/40 text-slate-400 uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4">Strategy</th>
                  <th className="py-2.5 px-3 text-right">Trades</th>
                  <th className="py-2.5 px-3 text-right">Win Rate</th>
                  <th className="py-2.5 px-4 text-right">Net P&amp;L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {strategyStats.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-500">
                      No closed strategy trades recorded yet.
                    </td>
                  </tr>
                ) : (
                  strategyStats.map((st, i) => (
                    <tr key={i} className="hover:bg-white/[0.02]">
                      <td className="py-2.5 px-4 text-white font-medium">{st.strategy_name}</td>
                      <td className="py-2.5 px-3 text-right text-slate-300">{st.total_trades}</td>
                      <td className="py-2.5 px-3 text-right text-cyan-400">{st.win_rate}%</td>
                      <td
                        className={`py-2.5 px-4 text-right font-bold ${
                          st.realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {st.realized_pnl >= 0 ? '+' : ''}₹{st.realized_pnl?.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Symbol Breakdown */}
        <div className="bg-slate-900/60 rounded-2xl border border-white/10 overflow-hidden shadow-xl">
          <div className="p-4 bg-slate-950/60 border-b border-white/10 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-cyan-400" />
              Performance by Symbol
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/40 text-slate-400 uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4">Symbol</th>
                  <th className="py-2.5 px-3">Market</th>
                  <th className="py-2.5 px-3 text-right">Trades</th>
                  <th className="py-2.5 px-4 text-right">Net P&amp;L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {symbolStats.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-500">
                      No trades attributed to symbols yet.
                    </td>
                  </tr>
                ) : (
                  symbolStats.map((sym, i) => (
                    <tr key={i} className="hover:bg-white/[0.02]">
                      <td className="py-2.5 px-4 text-white font-bold">{sym.symbol}</td>
                      <td className="py-2.5 px-3 text-slate-400">{sym.market}</td>
                      <td className="py-2.5 px-3 text-right text-slate-300">{sym.total_trades}</td>
                      <td
                        className={`py-2.5 px-4 text-right font-bold ${
                          sym.realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {sym.realized_pnl >= 0 ? '+' : ''}₹{sym.realized_pnl?.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
