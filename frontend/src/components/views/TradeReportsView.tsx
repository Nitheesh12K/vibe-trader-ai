import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Clock,
  ShieldCheck,
  RefreshCw,
  ExternalLink,
  Zap,
  User,
  Filter,
} from 'lucide-react';
import { api } from '../../services/api';
import { TradeReportRead } from '../../types/market';

export const TradeReportsView: React.FC = () => {
  const [reports, setReports] = useState<TradeReportRead[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [marketFilter, setMarketFilter] = useState<string>('ALL');
  const [selectedReport, setSelectedReport] = useState<TradeReportRead | null>(null);

  const fetchReports = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getTradeReports(100);
      setReports(data);
      if (data.length > 0 && !selectedReport) {
        setSelectedReport(data[0]);
      }
    } catch (err: any) {
      console.error('Failed to load trade reports:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedReport]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const filteredReports = reports.filter((r) => {
    if (marketFilter !== 'ALL' && r.market !== marketFilter) return false;
    return true;
  });

  const totalTrades = filteredReports.length;
  const winningTrades = filteredReports.filter((r) => r.net_pnl > 0).length;
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;
  const totalNetPnl = filteredReports.reduce((sum, r) => sum + r.net_pnl, 0);
  const totalFees = filteredReports.reduce((sum, r) => sum + r.fees, 0);
  const totalSlippage = filteredReports.reduce((sum, r) => sum + r.slippage, 0);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-panel border border-border p-5 rounded-xl shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-accent/10 border border-accent/30 rounded-lg text-accent">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              Trade Reports & Post-Mortem Analytics
              <span className="text-[10px] bg-accent/20 text-accent font-mono px-2 py-0.5 rounded border border-accent/30">
                STEP 8 • AUDITED PERFORMANCE
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Comprehensive transaction accounting: gross P&L, micro-slippage, execution fees, and exit rationale.
            </p>
          </div>
        </div>

        <button
          onClick={fetchReports}
          disabled={loading}
          className="p-2 bg-panel-subtle hover:bg-panel border border-border rounded-lg text-slate-400 hover:text-white transition-colors"
          title="Refresh reports"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Aggregate Performance Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border bg-panel border-border">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Total Trades</span>
          <div className="text-2xl font-bold font-mono text-white mt-1">{totalTrades}</div>
          <span className="text-[11px] text-slate-400 mt-1 block">
            {winningTrades} wins • {totalTrades - winningTrades} losses
          </span>
        </div>

        <div className="p-4 rounded-xl border bg-panel border-border">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Win Rate</span>
          <div className="text-2xl font-bold font-mono text-accent mt-1">{winRate.toFixed(1)}%</div>
          <span className="text-[11px] text-slate-400 mt-1 block">Confluence profitability</span>
        </div>

        <div className="p-4 rounded-xl border bg-panel border-border">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Total Net Realized P&L</span>
          <div
            className={`text-2xl font-bold font-mono mt-1 ${
              totalNetPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {totalNetPnl >= 0 ? '+' : ''}${totalNetPnl.toFixed(2)}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">After all fees & slippage</span>
        </div>

        <div className="p-4 rounded-xl border bg-panel border-border">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Fees & Slippage Paid</span>
          <div className="text-2xl font-bold font-mono text-amber-300 mt-1">
            ${(totalFees + totalSlippage).toFixed(2)}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Fees: ${totalFees.toFixed(2)} • Slip: ${totalSlippage.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-2 bg-panel border border-border p-3 rounded-lg text-xs">
        <Filter className="w-3.5 h-3.5 text-accent" />
        <span className="text-slate-400 font-semibold">Filter Market:</span>
        {['ALL', 'FOREX', 'NSE', 'MCX'].map((m) => (
          <button
            key={m}
            onClick={() => setMarketFilter(m)}
            className={`px-2.5 py-1 rounded font-medium transition-colors ${
              marketFilter === m
                ? 'bg-accent/20 text-accent border border-accent/40'
                : 'text-slate-400 hover:bg-panel-subtle hover:text-white'
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Empty State */}
      {!loading && filteredReports.length === 0 && (
        <div className="p-12 text-center bg-panel border border-border rounded-xl space-y-3">
          <FileText className="w-12 h-12 mx-auto text-slate-500" />
          <h3 className="text-base font-semibold text-white">No Closed Trade Reports Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Once positions are closed (either via autonomous SL/TP exits or manual user intervention), comprehensive post-trade reports will appear here automatically.
          </p>
        </div>
      )}

      {/* Reports Table */}
      {filteredReports.length > 0 && (
        <div className="bg-panel border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-panel-subtle border-b border-border text-slate-400 uppercase tracking-wider font-mono text-[10px]">
                <tr>
                  <th className="p-3.5">Symbol / Market</th>
                  <th className="p-3.5">Strategy</th>
                  <th className="p-3.5">Entry / Exit</th>
                  <th className="p-3.5">Gross P&L</th>
                  <th className="p-3.5">Fees & Slip</th>
                  <th className="p-3.5">Net Realized P&L</th>
                  <th className="p-3.5">ROI %</th>
                  <th className="p-3.5">Exit Reason</th>
                  <th className="p-3.5">Execution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredReports.map((report) => {
                  const isProfit = report.net_pnl >= 0;
                  return (
                    <tr
                      key={report.id}
                      onClick={() => setSelectedReport(report)}
                      className={`hover:bg-panel-subtle/70 cursor-pointer transition-colors ${
                        selectedReport?.id === report.id ? 'bg-accent/5' : ''
                      }`}
                    >
                      <td className="p-3.5 font-mono">
                        <div className="font-bold text-white text-xs">{report.symbol}</div>
                        <span className="text-[10px] text-slate-400">{report.market}</span>
                      </td>

                      <td className="p-3.5 text-slate-300">
                        <span className="font-medium text-xs block">{report.strategy_name}</span>
                        <span className="text-[10px] font-mono text-slate-400">Qty: {report.quantity}</span>
                      </td>

                      <td className="p-3.5 font-mono text-slate-300 text-[11px]">
                        <div>In: ${report.entry_price.toFixed(4)}</div>
                        <div className="text-slate-400">Out: ${report.exit_price.toFixed(4)}</div>
                      </td>

                      <td className="p-3.5 font-mono text-slate-300">
                        ${report.gross_pnl.toFixed(2)}
                      </td>

                      <td className="p-3.5 font-mono text-slate-400">
                        ${(report.fees + report.slippage).toFixed(2)}
                      </td>

                      <td className="p-3.5 font-mono font-bold text-xs">
                        <span className={isProfit ? 'text-emerald-400' : 'text-rose-400'}>
                          {isProfit ? '+' : ''}${report.net_pnl.toFixed(2)}
                        </span>
                      </td>

                      <td className="p-3.5 font-mono font-bold text-xs">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[11px] ${
                            isProfit
                              ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                              : 'bg-rose-500/10 text-rose-300 border border-rose-500/30'
                          }`}
                        >
                          {isProfit ? '+' : ''}{report.roi_pct.toFixed(2)}%
                        </span>
                      </td>

                      <td className="p-3.5 font-mono text-[11px] text-slate-300">
                        {report.exit_reason}
                      </td>

                      <td className="p-3.5">
                        {report.autonomous_exit ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                            <Zap className="w-3 h-3" /> Auto SELL
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                            <User className="w-3 h-3" /> Manual
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Selected Report Post-Mortem Modal / Detail Pane */}
      {selectedReport && (
        <div className="bg-panel border border-border p-5 rounded-xl space-y-3">
          <div className="flex items-center justify-between border-b border-border pb-2.5">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-accent" />
              Trade Audit Post-Mortem • {selectedReport.symbol} (Report #{selectedReport.id})
            </h3>
            <span className="text-[10px] font-mono text-slate-400">
              Closed: {new Date(selectedReport.exit_time).toLocaleString()}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="space-y-2 bg-panel-subtle p-3 rounded-lg border border-border">
              <span className="text-[11px] font-semibold text-slate-300 block">Strategy Rationale</span>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                {selectedReport.strategy_rationale || 'Quantitative confluence signals verified at entry.'}
              </p>
            </div>

            <div className="space-y-1 bg-panel-subtle p-3 rounded-lg border border-border font-mono text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Entry Time:</span>
                <span>{new Date(selectedReport.entry_time).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Risk Check Passed:</span>
                <span className="text-emerald-400 font-bold">{selectedReport.risk_check_passed ? 'YES' : 'NO'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Data Source:</span>
                <span>{selectedReport.data_source}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
