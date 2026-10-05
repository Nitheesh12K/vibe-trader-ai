import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  XCircle,
  ExternalLink,
  Target,
  Sliders,
  DollarSign,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../../services/api';
import { PositionRead, AutonomousExitPermissionRead } from '../../types/market';

export const OpenPositionsView: React.FC<{ onNavigateToRisk?: () => void }> = ({ onNavigateToRisk }) => {
  const [positions, setPositions] = useState<PositionRead[]>([]);
  const [permissions, setPermissions] = useState<AutonomousExitPermissionRead | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [closingId, setClosingId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'OPEN' | 'CLOSED'>('OPEN');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchPositionsData = useCallback(async () => {
    try {
      setLoading(true);
      const [posList, perms] = await Promise.all([
        api.getPositions(activeTab),
        api.getAutonomousExitPermissions().catch(() => null),
      ]);
      setPositions(posList);
      if (perms) setPermissions(perms);
    } catch (err: any) {
      console.error('Failed to load positions data:', err);
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchPositionsData();
    const interval = setInterval(fetchPositionsData, 10000);
    return () => clearInterval(interval);
  }, [fetchPositionsData]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleClosePosition = async (positionId: string) => {
    if (!window.confirm(`Are you sure you want to manually close position ${positionId} at market price?`)) {
      return;
    }

    try {
      setClosingId(positionId);
      const res = await api.closePosition(positionId, 'MANUAL_OPERATOR_CLOSE');
      showToast(`Position ${positionId} closed. Realized P&L: $${res.realized_pnl.toFixed(2)}`);
      await fetchPositionsData();
    } catch (err: any) {
      alert(`Failed to close position: ${err.message}`);
    } finally {
      setClosingId(null);
    }
  };

  const openPositions = positions.filter((p) => p.status === 'OPEN');
  const totalUnrealizedPnl = openPositions.reduce((sum, p) => sum + p.unrealized_pnl, 0);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-16 right-8 z-50 bg-accent text-white px-4 py-2.5 rounded-lg shadow-xl border border-accent-indigo text-xs font-semibold flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-300" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] p-6 rounded-2xl">
        <div className="flex items-center gap-3.5">
          <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-cyan-400">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2.5">
              Positions & Autonomous Exit Monitor
              <span className="text-[10px] bg-cyan-500/15 text-cyan-400 font-mono font-bold px-2.5 py-0.5 rounded-full border border-cyan-500/30">
                STEPS 6 & 7
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Continuous price surveillance. Pre-authorized autonomous SELL exits execute only when permission is enabled.
            </p>
          </div>
        </div>

        {/* Autonomous Exit Permission Status Badge */}
        <div className="flex items-center gap-3">
          <div
            className={`px-4 py-2 rounded-xl border text-xs font-semibold flex items-center gap-2 shadow-sm ${
              permissions?.is_enabled
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
            }`}
          >
            {permissions?.is_enabled ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-amber-400" />
            )}
            <span>
              Autonomous SELL: {permissions?.is_enabled ? 'ENABLED & ARMED' : 'MANUAL SUPERVISION ONLY'}
            </span>
          </div>

          <button
            onClick={fetchPositionsData}
            disabled={loading}
            className="p-2.5 bg-[#080D1A] hover:bg-white/[0.04] border border-white/[0.08] rounded-xl text-slate-400 hover:text-white transition-colors"
            title="Refresh positions"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-cyan-500/30 transition-all duration-300 group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-cyan-500/10 transition-colors" />
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Open Monitored Positions
          </span>
          <div className="text-3xl font-extrabold font-mono text-white mt-2 drop-shadow-[0_0_12px_rgba(255,255,255,0.15)]">
            {openPositions.length}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">Live Virtual Paper Positions</span>
        </div>

        <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-slate-600 transition-all duration-300 group">
          <div className={`absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl pointer-events-none transition-colors ${totalUnrealizedPnl >= 0 ? 'bg-emerald-500/5 group-hover:bg-emerald-500/10' : 'bg-rose-500/5 group-hover:bg-rose-500/10'}`} />
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Net Unrealized P&L
          </span>
          <div
            className={`text-3xl font-extrabold font-mono mt-2 tracking-tight ${
              totalUnrealizedPnl >= 0
                ? 'text-emerald-400 drop-shadow-[0_0_12px_rgba(16,185,129,0.25)]'
                : 'text-rose-400 drop-shadow-[0_0_12px_rgba(244,63,94,0.25)]'
            }`}
          >
            {totalUnrealizedPnl >= 0 ? '+' : ''}${totalUnrealizedPnl.toFixed(2)}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">Floating paper profit / loss</span>
        </div>

        <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 hover:border-cyan-500/30 transition-all duration-300 group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-indigo-500/10 transition-colors" />
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Autonomous Safety Triggers
          </span>
          <div className="text-xs text-slate-300 mt-3 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Stop-Loss Auto-Exit:</span>
              <span className={`font-mono font-bold text-xs ${permissions?.allow_stop_loss ? 'text-emerald-400' : 'text-slate-500'}`}>
                {permissions?.allow_stop_loss ? 'ACTIVE' : 'OFF'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Take-Profit Auto-Exit:</span>
              <span className={`font-mono font-bold text-xs ${permissions?.allow_take_profit ? 'text-emerald-400' : 'text-slate-500'}`}>
                {permissions?.allow_take_profit ? 'ACTIVE' : 'OFF'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 bg-[#080D1A] p-1 rounded-xl border border-white/[0.08] w-fit">
        <button
          onClick={() => setActiveTab('OPEN')}
          className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'OPEN'
              ? 'bg-cyan-500 text-white font-bold shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          Open Positions ({openPositions.length})
        </button>
        <button
          onClick={() => setActiveTab('CLOSED')}
          className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'CLOSED'
              ? 'bg-cyan-500 text-white font-bold shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          Closed Positions History
        </button>
      </div>

      {/* Empty State */}
      {!loading && positions.length === 0 && (
        <div className="p-12 text-center bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl space-y-3">
          <Activity className="w-12 h-12 mx-auto text-slate-500" />
          <h3 className="text-base font-semibold text-white">
            {activeTab === 'OPEN' ? 'No Open Positions' : 'No Closed Positions'}
          </h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {activeTab === 'OPEN'
              ? 'There are currently no active open positions. Once you approve a BUY proposal in the Approval Center, it will appear here under continuous price surveillance.'
              : 'No closed positions recorded yet.'}
          </p>
        </div>
      )}

      {/* Positions Table / Cards */}
      <div className="space-y-4">
        {positions.map((pos) => {
          const isPosClosing = closingId === pos.position_id;
          const isProfitable = (pos.status === 'OPEN' ? pos.unrealized_pnl : (pos.realized_pnl || 0)) >= 0;
          const distToSL = ((pos.current_price - pos.stop_loss) / pos.current_price) * 100;
          const distToTP = ((pos.target - pos.current_price) / pos.current_price) * 100;

          return (
            <div
              key={pos.position_id}
              className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl overflow-hidden hover:border-cyan-500/30 transition-all"
            >
              <div className="p-5 border-b border-white/[0.08] flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#0A0F1D]/80">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      pos.status === 'OPEN' ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse' : 'bg-slate-500'
                    }`}
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-base font-mono">{pos.symbol}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#121B2F] border border-white/[0.08] text-slate-300">
                        {pos.market}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono">
                        {pos.side}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">ID: {pos.position_id}</span>
                    </div>
                  </div>
                </div>

                {/* Live Unrealized P&L */}
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                      {pos.status === 'OPEN' ? 'Unrealized P&L' : 'Realized P&L'}
                    </span>
                    <div className="flex items-center gap-2 justify-end mt-0.5">
                      {isProfitable ? (
                        <TrendingUp className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-rose-400" />
                      )}
                      <span
                        className={`text-lg font-bold font-mono ${
                          isProfitable ? 'text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]' : 'text-rose-400 drop-shadow-[0_0_8px_rgba(244,63,94,0.3)]'
                        }`}
                      >
                        {isProfitable ? '+' : ''}$
                        {(pos.status === 'OPEN' ? pos.unrealized_pnl : (pos.realized_pnl || 0)).toFixed(2)}
                      </span>
                      {pos.status === 'OPEN' && (
                        <span
                          className={`text-xs font-mono font-bold px-2 py-0.5 rounded-md border ${
                            pos.unrealized_pnl_pct >= 0
                              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                              : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                          }`}
                        >
                          {pos.unrealized_pnl_pct >= 0 ? '+' : ''}
                          {pos.unrealized_pnl_pct.toFixed(2)}%
                        </span>
                      )}
                    </div>
                  </div>

                  {pos.status === 'OPEN' && (
                    <button
                      onClick={() => handleClosePosition(pos.position_id)}
                      disabled={isPosClosing}
                      className="px-4 py-2 bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all disabled:opacity-50 shadow-sm"
                    >
                      <XCircle className="w-4 h-4 text-rose-400" />
                      {isPosClosing ? 'Closing...' : 'Close Now'}
                    </button>
                  )}
                </div>
              </div>

              {/* Position Price Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 p-4 bg-[#080D1A]/50 text-xs">
                <div className="p-3 rounded-xl bg-[#0D1322] border border-white/[0.06]">
                  <span className="text-[10px] text-slate-500 block uppercase font-semibold">Entry Price</span>
                  <span className="font-mono font-bold text-white text-xs mt-1 block">
                    ${pos.entry_price.toFixed(4)}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#0D1322] border border-white/[0.06]">
                  <span className="text-[10px] text-slate-500 block uppercase font-semibold">Current Price</span>
                  <span className="font-mono font-bold text-cyan-400 text-xs mt-1 block">
                    ${pos.current_price.toFixed(4)}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#0D1322] border border-white/[0.06]">
                  <span className="text-[10px] text-slate-500 block uppercase font-semibold">Stop Loss (SL)</span>
                  <span className="font-mono font-bold text-rose-400 text-xs mt-1 block">
                    ${pos.stop_loss.toFixed(4)}
                  </span>
                  {pos.status === 'OPEN' && (
                    <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">
                      {distToSL.toFixed(2)}% buffer
                    </span>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-[#0D1322] border border-white/[0.06]">
                  <span className="text-[10px] text-slate-500 block uppercase font-semibold">Target (TP)</span>
                  <span className="font-mono font-bold text-emerald-400 text-xs mt-1 block">
                    ${pos.target.toFixed(4)}
                  </span>
                  {pos.status === 'OPEN' && (
                    <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">
                      {distToTP.toFixed(2)}% away
                    </span>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-[#0D1322] border border-white/[0.06]">
                  <span className="text-[10px] text-slate-500 block uppercase font-semibold">Quantity</span>
                  <span className="font-mono font-bold text-white text-xs mt-1 block">
                    {pos.quantity.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Exit details if closed */}
              {pos.status === 'CLOSED' && (
                <div className="p-3.5 bg-[#080D1A]/80 border-t border-white/[0.06] text-xs flex items-center justify-between text-slate-400">
                  <div>
                    Exit Reason: <span className="font-semibold text-white">{pos.exit_reason}</span>
                  </div>
                  <div>
                    Exit Price: <span className="font-mono text-white font-bold">${pos.exit_price?.toFixed(4)}</span>
                  </div>
                  <div>
                    Closed At: <span className="font-mono text-slate-300">{pos.exit_timestamp ? new Date(pos.exit_timestamp).toLocaleString() : 'N/A'}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
