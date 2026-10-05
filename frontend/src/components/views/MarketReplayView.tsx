import React, { useState, useEffect } from 'react';
import {
  History,
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  RefreshCw,
  Plus,
} from 'lucide-react';
import { api } from '../../services/api';
import { ReplaySessionItem, OHLCCandle, NavTabId } from '../../types/market';

interface MarketReplayViewProps {
  onNavigate?: (tab: NavTabId, symbol?: string) => void;
}

export const MarketReplayView: React.FC<MarketReplayViewProps> = ({ onNavigate }) => {
  const [session, setSession] = useState<ReplaySessionItem | null>(null);
  const [symbol, setSymbol] = useState<string>('INFY');
  const [market, setMarket] = useState<string>('NSE');
  const [initialCapital, setInitialCapital] = useState<number>(50000);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isStepping, setIsStepping] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const initSession = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await api.createReplaySession({
        symbol: symbol.trim().toUpperCase(),
        market,
        initial_capital: initialCapital,
        name: `Replay ${symbol}`,
      });
      setSession(res);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize market replay session.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    initSession();
  }, []);

  const handleStep = async (count: number) => {
    if (!session) return;
    try {
      setIsStepping(true);
      setError(null);
      const updated = await api.stepReplaySession(session.session_id, count);
      setSession(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to advance replay step.');
    } finally {
      setIsStepping(false);
    }
  };

  const handleReset = async () => {
    if (!session) return;
    try {
      setIsStepping(true);
      const resetState = await api.resetReplaySession(session.session_id);
      setSession(resetState);
    } catch (err: any) {
      setError(err.message || 'Failed to reset replay session.');
    } finally {
      setIsStepping(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!session || !session.pending_proposal) return;
    try {
      setIsStepping(true);
      await api.approveReplayProposal(session.session_id, session.pending_proposal.proposal_id);
      const refetched = await api.getReplaySession(session.session_id);
      setSession(refetched);
    } catch (err: any) {
      setError(err.message || 'Failed to approve proposal.');
    } finally {
      setIsStepping(false);
    }
  };

  const handleClosePosition = async (positionId: string) => {
    if (!session) return;
    try {
      setIsStepping(true);
      await api.closeReplayPosition(session.session_id, positionId);
      const refetched = await api.getReplaySession(session.session_id);
      setSession(refetched);
    } catch (err: any) {
      setError(err.message || 'Failed to close position.');
    } finally {
      setIsStepping(false);
    }
  };

  const currentCandle = session?.current_candle;
  const progressPct = session ? Math.min(100, Math.round((session.current_index / session.total_candles) * 100)) : 0;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-white/10 backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-white flex items-center gap-2">
              <span className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <History className="w-5 h-5" />
              </span>
              Market Replay Simulator
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Causal • Zero Future Leakage
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Step through historical candles chronologically. Evaluate signals, approve proposals, and monitor exits in an isolated sandbox.
          </p>
        </div>

        {/* Player Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleStep(1)}
            disabled={isStepping || !session || session.current_index >= session.total_candles}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20 transition disabled:opacity-40"
            title="Advance 1 Candle"
          >
            <SkipForward className="w-4 h-4" />
            Step +1
          </button>
          <button
            onClick={() => handleStep(5)}
            disabled={isStepping || !session || session.current_index >= session.total_candles}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white font-semibold text-xs border border-white/10 transition disabled:opacity-40"
            title="Advance 5 Candles"
          >
            <SkipForward className="w-4 h-4" />
            Step +5
          </button>
          <button
            onClick={handleReset}
            disabled={isStepping || !session}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-white/5 transition"
            title="Reset to Candle 20"
          >
            <RotateCcw className="w-4 h-4" />
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

      {/* Progress & Timeline Scrubber */}
      {session && (
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/10 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="flex items-center gap-2">
              <span className="text-white font-bold">{session.symbol}</span>
              <span>({session.market})</span>
              <span className="text-cyan-400">Timeframe: {session.timeframe}</span>
            </span>
            <span>
              Candle <span className="text-white font-bold">{session.current_index}</span> / {session.total_candles} ({progressPct}%)
            </span>
          </div>

          <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-white/5">
            <div
              className="bg-gradient-to-r from-cyan-500 to-indigo-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}

      {/* Current Candle Inspector & Account State */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Current Candle Stats (7 cols) */}
        <div className="md:col-span-7 p-5 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Current Historical Candle
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Index #{session?.current_index}
              </span>
            </h3>
            {session?.current_signal && (
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                  session.current_signal.includes('BUY')
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : session.current_signal.includes('SELL')
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                {session.current_signal}
              </span>
            )}
          </div>

          {currentCandle ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-white/5">
                <span className="text-[10px] font-mono text-slate-500 block uppercase">Open</span>
                <span className="text-sm font-mono font-bold text-white">₹{currentCandle.open.toFixed(2)}</span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-white/5">
                <span className="text-[10px] font-mono text-slate-500 block uppercase">High</span>
                <span className="text-sm font-mono font-bold text-emerald-400">₹{currentCandle.high.toFixed(2)}</span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-white/5">
                <span className="text-[10px] font-mono text-slate-500 block uppercase">Low</span>
                <span className="text-sm font-mono font-bold text-rose-400">₹{currentCandle.low.toFixed(2)}</span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-white/5">
                <span className="text-[10px] font-mono text-slate-500 block uppercase">Close</span>
                <span className="text-sm font-mono font-bold text-cyan-400">₹{currentCandle.close.toFixed(2)}</span>
              </div>
            </div>
          ) : (
            <div className="p-6 text-center text-slate-500 text-xs">No candle loaded.</div>
          )}

          <div className="p-3 rounded-xl bg-slate-950/40 border border-white/5 text-[11px] text-slate-400 font-mono flex items-center justify-between">
            <span>Timestamp: {currentCandle ? new Date(currentCandle.time * 1000).toLocaleString() : '—'}</span>
            <span>Volume: {currentCandle?.volume?.toLocaleString() || '1,000'}</span>
          </div>
        </div>

        {/* Replay Balance Card (5 cols) */}
        <div className="md:col-span-5 p-5 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4">
          <div className="border-b border-white/10 pb-3 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white">Replay Virtual Account</h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
              ISOLATED SANDBOX
            </span>
          </div>

          <div className="space-y-3 font-mono">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Virtual Cash Balance</span>
              <span className="text-white font-bold">₹{session?.virtual_balance?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Realized P&amp;L</span>
              <span
                className={`font-bold ${
                  (session?.realized_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {(session?.realized_pnl || 0) >= 0 ? '+' : ''}₹{session?.realized_pnl?.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Open Positions</span>
              <span className="text-slate-200">{session?.open_positions?.length || 0}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Closed Trades</span>
              <span className="text-slate-200">{session?.closed_trades?.length || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Human Approval Gate for Replay BUY Proposal */}
      {session?.pending_proposal && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/50 via-slate-900 to-indigo-950/40 border border-emerald-500/40 shadow-2xl space-y-4 animate-in fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
            <div className="flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
                <TrendingUp className="w-5 h-5" />
              </span>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  Causal Strategy Signal Generated
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                    HUMAN APPROVAL REQUIRED
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  {session.pending_proposal.rationale}
                </p>
              </div>
            </div>

            <button
              onClick={handleApproveProposal}
              disabled={isStepping}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/25 transition shrink-0"
            >
              <CheckCircle2 className="w-4 h-4" />
              Approve Paper BUY
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono">
            <div className="p-2.5 bg-slate-950/70 rounded-xl border border-white/5">
              <span className="text-[10px] text-slate-500 block">Entry Price</span>
              <span className="text-white font-bold">₹{session.pending_proposal.entry_price?.toFixed(2)}</span>
            </div>
            <div className="p-2.5 bg-slate-950/70 rounded-xl border border-white/5">
              <span className="text-[10px] text-slate-500 block">Quantity</span>
              <span className="text-slate-200 font-bold">{session.pending_proposal.quantity} units</span>
            </div>
            <div className="p-2.5 bg-slate-950/70 rounded-xl border border-white/5">
              <span className="text-[10px] text-slate-500 block">Stop-Loss</span>
              <span className="text-rose-400 font-bold">₹{session.pending_proposal.stop_loss?.toFixed(2)}</span>
            </div>
            <div className="p-2.5 bg-slate-950/70 rounded-xl border border-white/5">
              <span className="text-[10px] text-slate-500 block">Target (TP)</span>
              <span className="text-emerald-400 font-bold">₹{session.pending_proposal.target?.toFixed(2)}</span>
            </div>
            <div className="p-2.5 bg-slate-950/70 rounded-xl border border-white/5">
              <span className="text-[10px] text-slate-500 block">Risk Amount</span>
              <span className="text-amber-400 font-bold">₹{session.pending_proposal.risk_amount?.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Open Virtual Replay Positions Table */}
      {session && session.open_positions && session.open_positions.length > 0 && (
        <div className="bg-slate-900/60 rounded-2xl border border-white/10 overflow-hidden shadow-xl space-y-2">
          <div className="p-4 bg-slate-950/70 border-b border-white/10">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              Active Positions in Replay ({session.open_positions.length})
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/40 text-slate-400 uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4">Position ID</th>
                  <th className="py-2.5 px-3">Symbol</th>
                  <th className="py-2.5 px-3 text-right">Entry</th>
                  <th className="py-2.5 px-3 text-right">Current</th>
                  <th className="py-2.5 px-3 text-right">Unrealized P&amp;L</th>
                  <th className="py-2.5 px-3">SL / TP</th>
                  <th className="py-2.5 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {session.open_positions.map((pos) => {
                  const pnl = pos.unrealized_pnl || 0;
                  return (
                    <tr key={pos.position_id} className="hover:bg-white/[0.02]">
                      <td className="py-2.5 px-4 text-slate-400">{pos.position_id}</td>
                      <td className="py-2.5 px-3 text-white font-bold">{pos.symbol}</td>
                      <td className="py-2.5 px-3 text-right text-slate-200">₹{pos.entry_price?.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-right text-cyan-400">₹{pos.current_price?.toFixed(2)}</td>
                      <td className={`py-2.5 px-3 text-right font-bold ${pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {pnl >= 0 ? '+' : ''}₹{pnl.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-[11px] text-slate-400">
                        SL: ₹{pos.stop_loss?.toFixed(2)} • TP: ₹{pos.take_profit?.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        <button
                          onClick={() => handleClosePosition(pos.position_id)}
                          className="px-3 py-1 rounded bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 transition text-[11px]"
                        >
                          Close
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
