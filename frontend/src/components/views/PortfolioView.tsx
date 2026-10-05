import React, { useState, useEffect, useCallback } from 'react';
import {
  Briefcase,
  DollarSign,
  TrendingUp,
  TrendingDown,
  PieChart,
  ShieldCheck,
  RefreshCw,
  Layers,
  Activity,
  ArrowRight,
} from 'lucide-react';
import { api } from '../../services/api';
import { PositionRead, RiskSettingsRead } from '../../types/market';

export const PortfolioView: React.FC<{ onNavigateToApproval?: () => void }> = ({ onNavigateToApproval }) => {
  const [positions, setPositions] = useState<PositionRead[]>([]);
  const [risk, setRisk] = useState<RiskSettingsRead | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchPortfolio = useCallback(async () => {
    try {
      setLoading(true);
      const [posList, riskData] = await Promise.all([
        api.getPositions('OPEN'),
        api.getRiskSettings(),
      ]);
      setPositions(posList);
      setRisk(riskData);
    } catch (err: any) {
      console.error('Failed to load portfolio:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  const virtualBalance = risk?.simulated_balance || 100000;
  const totalUnrealizedPnl = positions.reduce((sum, p) => sum + p.unrealized_pnl, 0);
  const totalInvested = positions.reduce((sum, p) => sum + p.quantity * p.entry_price, 0);
  const availableCash = Math.max(0, virtualBalance + totalUnrealizedPnl - totalInvested);
  const totalEquity = virtualBalance + totalUnrealizedPnl;

  const forexCount = positions.filter((p) => p.market === 'FOREX').length;
  const nseCount = positions.filter((p) => p.market === 'NSE').length;
  const mcxCount = positions.filter((p) => p.market === 'MCX').length;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] p-6 rounded-2xl">
        <div className="flex items-center gap-3.5">
          <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-cyan-400">
            <Briefcase className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2.5">
              Portfolio & Capital Allocation
              <span className="text-[10px] bg-cyan-500/15 text-cyan-400 font-mono font-bold px-2.5 py-0.5 rounded-full border border-cyan-500/30">
                PAPER CAPITAL
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Live virtual equity, margin exposure, and cross-market distribution across Forex, NSE, and MCX.
            </p>
          </div>
        </div>

        <button
          onClick={fetchPortfolio}
          disabled={loading}
          className="p-2.5 bg-[#080D1A] hover:bg-white/[0.04] border border-white/[0.08] rounded-xl text-slate-400 hover:text-white transition-colors"
          title="Refresh portfolio"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-cyan-500/30 transition-all duration-300 group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-cyan-500/10 transition-colors" />
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Total Net Equity</span>
          <div className="text-2xl lg:text-3xl font-extrabold font-mono text-white mt-2 drop-shadow-[0_0_12px_rgba(255,255,255,0.15)]">
            ${totalEquity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">Virtual Balance + Floating P&L</span>
        </div>

        <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-emerald-500/30 transition-all duration-300 group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-emerald-500/10 transition-colors" />
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Available Free Cash</span>
          <div className="text-2xl lg:text-3xl font-extrabold font-mono text-emerald-400 mt-2 drop-shadow-[0_0_12px_rgba(16,185,129,0.2)]">
            ${availableCash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">Unencumbered paper capital</span>
        </div>

        <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-cyan-500/30 transition-all duration-300 group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-indigo-500/10 transition-colors" />
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Capital in Active Positions</span>
          <div className="text-2xl lg:text-3xl font-extrabold font-mono text-cyan-400 mt-2 drop-shadow-[0_0_12px_rgba(14,165,233,0.2)]">
            ${totalInvested.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            {((totalInvested / (virtualBalance || 1)) * 100).toFixed(1)}% of total capital
          </span>
        </div>

        <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-slate-600 transition-all duration-300 group">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Open Positions Count</span>
          <div className="text-2xl lg:text-3xl font-extrabold font-mono text-white mt-2">{positions.length}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Max limit: {risk?.max_open_positions || 5} concurrent
          </span>
        </div>
      </div>

      {/* Asset Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white">FOREX Exposure</span>
            <span className="text-xs font-mono text-slate-400 font-semibold">{forexCount} positions</span>
          </div>
          <div className="w-full bg-[#080D1A] rounded-full h-2 overflow-hidden border border-white/[0.08]">
            <div
              className="bg-cyan-500 h-full rounded-full"
              style={{ width: `${positions.length > 0 ? (forexCount / positions.length) * 100 : 0}%` }}
            />
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white">NSE (Indian Equities)</span>
            <span className="text-xs font-mono text-slate-400 font-semibold">{nseCount} positions</span>
          </div>
          <div className="w-full bg-[#080D1A] rounded-full h-2 overflow-hidden border border-white/[0.08]">
            <div
              className="bg-emerald-400 h-full rounded-full"
              style={{ width: `${positions.length > 0 ? (nseCount / positions.length) * 100 : 0}%` }}
            />
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white">MCX (Commodities)</span>
            <span className="text-xs font-mono text-slate-400 font-semibold">{mcxCount} positions</span>
          </div>
          <div className="w-full bg-[#080D1A] rounded-full h-2 overflow-hidden border border-white/[0.08]">
            <div
              className="bg-amber-400 h-full rounded-full"
              style={{ width: `${positions.length > 0 ? (mcxCount / positions.length) * 100 : 0}%` }}
            />
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-6 shadow-sm space-y-4">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          Active Portfolio Holdings
        </h3>

        {positions.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs">
            No active positions currently held in portfolio.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-[#080D1A]/80 text-slate-400 uppercase font-mono text-[10px] border-b border-white/[0.08]">
                <tr>
                  <th className="p-3.5">Symbol</th>
                  <th className="p-3.5">Market</th>
                  <th className="p-3.5">Quantity</th>
                  <th className="p-3.5">Entry Price</th>
                  <th className="p-3.5">Current Price</th>
                  <th className="p-3.5">Unrealized P&L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {positions.map((p) => {
                  const isProfit = p.unrealized_pnl >= 0;
                  return (
                    <tr key={p.position_id} className="hover:bg-white/[0.02] font-mono text-[11px] transition-colors">
                      <td className="p-3.5 font-bold text-white">{p.symbol}</td>
                      <td className="p-3.5 text-slate-400">{p.market}</td>
                      <td className="p-3.5 text-slate-300">{p.quantity.toLocaleString()}</td>
                      <td className="p-3.5 text-slate-300">${p.entry_price.toFixed(4)}</td>
                      <td className="p-3.5 text-cyan-400 font-semibold">${p.current_price.toFixed(4)}</td>
                      <td className="p-3.5 font-bold">
                        <span className={isProfit ? 'text-emerald-400' : 'text-rose-400'}>
                          {isProfit ? '+' : ''}${p.unrealized_pnl.toFixed(2)} ({isProfit ? '+' : ''}
                          {p.unrealized_pnl_pct.toFixed(2)}%)
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
