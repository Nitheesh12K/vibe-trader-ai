import React, { useState, useEffect, useCallback } from 'react';
import {
  Coins,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Layers,
  Activity,
  AlertTriangle,
  RefreshCw,
  Clock,
  Sparkles,
  KeyRound,
  ShieldAlert,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  XCircle,
  ExternalLink,
  BookOpen,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  PositionRead,
  TradeReportRead,
  BuyProposalRead,
  PaperTradeItem,
  RiskSettingsRead,
  PortfolioSummary,
  AIProviderStatus,
  ZerodhaStatusResponse,
} from '../../types/market';
import { StatusBadge } from '../common/Badge';
import { StatusAlert } from '../common/StatusAlert';
import { SkeletonCard, SkeletonRow } from '../common/Skeleton';
import { ProposalCard } from './ProposalCard';
import { PaperTradeApprovalModal } from '../common/PaperTradeApprovalModal';

interface PaperTradingViewProps {
  onNavigateToJournal?: () => void;
  onNavigateToApproval?: () => void;
}

export const PaperTradingView: React.FC<PaperTradingViewProps> = ({
  onNavigateToJournal,
  onNavigateToApproval,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [positions, setPositions] = useState<PositionRead[]>([]);
  const [tradeReports, setTradeReports] = useState<TradeReportRead[]>([]);
  const [proposals, setProposals] = useState<BuyProposalRead[]>([]);
  const [riskSettings, setRiskSettings] = useState<RiskSettingsRead | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [aiStatus, setAiStatus] = useState<AIProviderStatus | null>(null);
  const [brokerStatus, setBrokerStatus] = useState<ZerodhaStatusResponse | null>(null);
  const [closingPositionId, setClosingPositionId] = useState<string | null>(null);

  // Approval modal state
  const [selectedProposal, setSelectedProposal] = useState<BuyProposalRead | null>(null);
  const [approvalModalOpen, setApprovalModalOpen] = useState<boolean>(false);
  const [approvalLoading, setApprovalLoading] = useState<boolean>(false);
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});

  const [toast, setToast] = useState<{ text: string; type: 'success' | 'error' | 'warning' } | null>(null);

  const showToast = (text: string, type: 'success' | 'error' | 'warning' = 'success') => {
    setToast({ text, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadAllData = useCallback(async () => {
    try {
      setRefreshing(true);
      const [posRes, repRes, propRes, riskRes, dashRes, aiRes, bRes] = await Promise.allSettled([
        api.getPositions('OPEN'),
        api.getTradeReports(10),
        api.getProposals('PENDING'),
        api.getRiskSettings(),
        api.getDemoDashboard(),
        api.getAIStatus(),
        api.getZerodhaStatus(),
      ]);

      if (posRes.status === 'fulfilled') setPositions(posRes.value);
      if (repRes.status === 'fulfilled') setTradeReports(repRes.value);
      if (propRes.status === 'fulfilled') setProposals(propRes.value);
      if (riskRes.status === 'fulfilled') setRiskSettings(riskRes.value);
      if (dashRes.status === 'fulfilled') setPortfolio(dashRes.value.portfolio);
      if (aiRes.status === 'fulfilled') setAiStatus(aiRes.value);
      if (bRes.status === 'fulfilled') setBrokerStatus(bRes.value);
    } catch (err: any) {
      console.warn('Failed to load paper trading terminal state:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 12000);
    return () => clearInterval(interval);
  }, [loadAllData]);

  // Close open position manually
  const handleClosePosition = async (pos: PositionRead) => {
    try {
      setClosingPositionId(pos.position_id);
      const exitPrice = pos.current_price || pos.entry_price;
      const res = await api.closePosition(pos.position_id, 'MANUAL_CLOSE', exitPrice);
      showToast(`Position ${pos.symbol} closed | Realized P&L: ₹${(res.realized_pnl || 0).toFixed(2)}`);
      await loadAllData();
    } catch (err: any) {
      showToast(`Failed to close position: ${err.message}`, 'error');
    } finally {
      setClosingPositionId(null);
    }
  };

  // Proposal approval flow
  const handleOpenApproveModal = (prop: BuyProposalRead) => {
    setApprovalError(null);
    setSelectedProposal(prop);
    setApprovalModalOpen(true);
  };

  const handleConfirmApproval = async (proposalId: string, notes: string) => {
    try {
      setApprovalLoading(true);
      setApprovalError(null);
      setActionLoading((prev) => ({ ...prev, [proposalId]: true }));
      const res = await api.approveProposal(proposalId, notes);
      setApprovalModalOpen(false);
      showToast(`Paper Order Executed! Position: ${res.position_id} @ ₹${res.fill_price}`);
      await loadAllData();
    } catch (err: any) {
      setApprovalError(err.message || 'Approval execution failed.');
      showToast(`Approval failed: ${err.message}`, 'error');
    } finally {
      setApprovalLoading(false);
      setActionLoading((prev) => ({ ...prev, [proposalId]: false }));
    }
  };

  const handleRejectProposal = async (proposalId: string, reason: string) => {
    try {
      setActionLoading((prev) => ({ ...prev, [proposalId]: true }));
      const res = await api.rejectProposal(proposalId, reason);
      showToast(`Proposal rejected: ${res.message}`, 'warning');
      await loadAllData();
    } catch (err: any) {
      showToast(`Rejection failed: ${err.message}`, 'error');
    } finally {
      setActionLoading((prev) => ({ ...prev, [proposalId]: false }));
    }
  };

  // Derived metrics
  const virtualBalance = riskSettings?.simulated_balance || 2000.0;
  const dailyPnl = portfolio?.daily_pnl || 0.0;
  const isPnlPositive = dailyPnl >= 0;
  const openCount = positions.length;
  const totalRiskUsed = positions.reduce((acc, p) => acc + Math.abs(p.entry_price - p.stop_loss) * p.quantity, 0);
  const totalExposure = positions.reduce((acc, p) => acc + (p.entry_price * p.quantity), 0);
  const tradesTodayCount = tradeReports.length + openCount;
  const isEmergencyStop = !!riskSettings?.emergency_stop_active;

  return (
    <div className="space-y-5">
      {/* Toast Alert */}
      {toast && (
        <div
          role="alert"
          className={`fixed top-16 right-6 z-50 px-4 py-2.5 rounded-xl border backdrop-blur-xl text-xs font-semibold flex items-center gap-2 shadow-2xl transition-all ${
            toast.type === 'success'
              ? 'bg-emerald-950/90 text-emerald-200 border-emerald-500/30'
              : toast.type === 'warning'
              ? 'bg-amber-950/90 text-amber-200 border-amber-500/30'
              : 'bg-rose-950/90 text-rose-200 border-rose-500/30'
          }`}
        >
          <ShieldCheck className="w-4 h-4 shrink-0" />
          <span>{toast.text}</span>
        </div>
      )}

      {/* 1. PERSISTENT MANDATORY SIMULATION BANNER */}
      <div className="p-3.5 sm:p-4 rounded-2xl bg-gradient-to-r from-[#0C1A2E] via-[#0E1B2A] to-[#121B24] border border-cyan-500/30 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
            <Coins className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-white uppercase tracking-wider font-mono">
                PAPER TRADING TERMINAL (SIMULATOR)
              </span>
              <span className="px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 font-bold text-[10px] font-mono">
                NO REAL MONEY
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Simulated environment with adverse micro-slippage, brokerage commissions, and guarded autonomous exits.
            </p>
          </div>
        </div>

        {/* Live Status Indicators */}
        <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono">
          <span className="px-2.5 py-1 rounded-lg bg-white/[0.04] border border-white/[0.08] text-slate-300">
            DATA: <span className="text-emerald-400 font-semibold">DEMO / HISTORICAL</span>
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-white/[0.04] border border-white/[0.08] text-slate-300">
            BROKER:{' '}
            <span className={brokerStatus?.is_connected ? 'text-emerald-400' : 'text-slate-400'}>
              {brokerStatus?.is_connected ? 'CONNECTED (READ-ONLY)' : 'NOT CONNECTED'}
            </span>
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 font-bold">
            LIVE ORDERS: DISABLED
          </span>
          <button
            onClick={loadAllData}
            disabled={refreshing}
            className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-400 hover:text-white transition-colors"
            title="Refresh Terminal Data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Emergency Stop Notice if active */}
      {isEmergencyStop && (
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-200 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="font-bold">
              EMERGENCY KILL-SWITCH ACTIVE: All new paper buy proposals are halted.
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Manage in Risk Settings</span>
        </div>
      )}

      {/* 2. TOP SUMMARY METRIC CARDS */}
      {loading && !riskSettings ? (
        <SkeletonCard count={4} />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
          {/* Card 1: Virtual Balance */}
          <div className="p-4 rounded-2xl bg-[#0D1322]/80 border border-white/[0.08] space-y-1">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Virtual Balance</span>
              <Coins className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-xl sm:text-2xl font-extrabold font-mono text-white tracking-tight">
              ₹{virtualBalance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <div className="text-[10px] text-slate-500 font-mono">Simulated Capital</div>
          </div>

          {/* Card 2: Today's P&L */}
          <div className="p-4 rounded-2xl bg-[#0D1322]/80 border border-white/[0.08] space-y-1">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Today's P&amp;L</span>
              {isPnlPositive ? (
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
              )}
            </div>
            <div
              className={`text-xl sm:text-2xl font-extrabold font-mono tracking-tight ${
                isPnlPositive ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {isPnlPositive ? '+' : ''}₹{dailyPnl.toFixed(2)}
            </div>
            <div className="text-[10px] text-slate-500 font-mono">Net Realized + Floating</div>
          </div>

          {/* Card 3: Open Positions */}
          <div className="p-4 rounded-2xl bg-[#0D1322]/80 border border-white/[0.08] space-y-1">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Open Positions</span>
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-xl sm:text-2xl font-extrabold font-mono text-white tracking-tight">
              {openCount} / {riskSettings?.max_open_positions || 1}
            </div>
            <div className="text-[10px] text-slate-500 font-mono">Concurrency Limit Enforced</div>
          </div>

          {/* Card 4: Risk Used */}
          <div className="p-4 rounded-2xl bg-[#0D1322]/80 border border-white/[0.08] space-y-1">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Risk Used</span>
              <Activity className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-xl sm:text-2xl font-extrabold font-mono text-amber-300 tracking-tight">
              ₹{totalRiskUsed.toFixed(2)}
            </div>
            <div className="text-[10px] text-slate-500 font-mono">
              Limit: ₹{((virtualBalance * (riskSettings?.max_risk_per_trade_pct || 0.5)) / 100).toFixed(2)}
            </div>
          </div>

          {/* Card 5: Trades Today */}
          <div className="p-4 rounded-2xl bg-[#0D1322]/80 border border-white/[0.08] space-y-1 col-span-2 sm:col-span-1">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Trades Today</span>
              <Clock className="w-3.5 h-3.5 text-purple-400" />
            </div>
            <div className="text-xl sm:text-2xl font-extrabold font-mono text-white tracking-tight">
              {tradesTodayCount}
            </div>
            <div className="text-[10px] text-slate-500 font-mono">Closed &amp; Active</div>
          </div>
        </div>
      )}

      {/* 3. SECTION A: PENDING BUY PROPOSALS (AWAITING APPROVAL) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-xs sm:text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span>Pending Trade Proposals</span>
            </h2>
            <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-mono font-bold">
              {proposals.length}
            </span>
          </div>

          {onNavigateToApproval && (
            <button
              onClick={onNavigateToApproval}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1 transition-colors"
            >
              <span>Approval Center</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {proposals.length === 0 ? (
          <StatusAlert
            type="NO_PROPOSALS"
            title="NO PENDING PROPOSALS"
            detail="The algorithm engine is evaluating market setups. New trade candidates will appear here awaiting your explicit authorization."
          />
        ) : (
          <div className="space-y-3">
            {proposals.slice(0, 2).map((proposal) => (
              <ProposalCard
                key={proposal.proposal_id}
                proposal={proposal}
                onApproveClick={handleOpenApproveModal}
                onRejectClick={handleRejectProposal}
                isActionLoading={!!actionLoading[proposal.proposal_id]}
              />
            ))}
          </div>
        )}
      </div>

      {/* 4. SECTION B: OPEN POSITIONS TABLE */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-xs sm:text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-400" />
              <span>Open Paper Positions</span>
            </h2>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono font-bold">
              {positions.length}
            </span>
          </div>
        </div>

        {positions.length === 0 ? (
          <StatusAlert
            type="NO_POSITIONS"
            title="NO OPEN POSITIONS"
            detail="Approved paper trades will be actively tracked here with trailing stops, profit targets, and exit monitoring."
          />
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-white/[0.08] bg-[#0D1322]/80">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-white/[0.03] border-b border-white/[0.08] text-slate-400 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3.5">Symbol</th>
                  <th className="p-3.5">Quantity</th>
                  <th className="p-3.5">Entry Price</th>
                  <th className="p-3.5">Current Price</th>
                  <th className="p-3.5">Stop Loss</th>
                  <th className="p-3.5">Target</th>
                  <th className="p-3.5">Unrealized P&amp;L</th>
                  <th className="p-3.5">Exposure</th>
                  <th className="p-3.5">Auto-Exit</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.05] text-slate-200">
                {positions.map((pos) => {
                  const unpnl = pos.unrealized_pnl || 0.0;
                  const posExp = pos.entry_price * pos.quantity;
                  const isClosing = closingPositionId === pos.position_id;

                  return (
                    <tr key={pos.position_id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="p-3.5">
                        <div className="font-bold text-white">{pos.symbol}</div>
                        <div className="text-[10px] text-slate-400">{pos.market}</div>
                      </td>
                      <td className="p-3.5 text-slate-300">{pos.quantity} units</td>
                      <td className="p-3.5">₹{pos.entry_price.toFixed(2)}</td>
                      <td className="p-3.5 font-bold text-white">
                        ₹{(pos.current_price || pos.entry_price).toFixed(2)}
                      </td>
                      <td className="p-3.5 text-rose-400">₹{pos.stop_loss.toFixed(2)}</td>
                      <td className="p-3.5 text-emerald-400">₹{pos.target.toFixed(2)}</td>
                      <td className="p-3.5 font-bold">
                        <span className={unpnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                          {unpnl >= 0 ? '+' : ''}₹{unpnl.toFixed(2)}
                        </span>
                      </td>
                      <td className="p-3.5 text-cyan-300">₹{posExp.toFixed(2)}</td>
                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Active (SL/TP)
                        </span>
                      </td>
                      <td className="p-3.5 text-right">
                        <button
                          onClick={() => handleClosePosition(pos)}
                          disabled={isClosing}
                          className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition-colors"
                        >
                          {isClosing ? 'Closing...' : 'Close Trade'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 5. SECTION C & D: CLOSED TRADES & SYSTEM GUARDRAILS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Closed Trades Table (8 cols) */}
        <div className="lg:col-span-8 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs sm:text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-purple-400" />
              <span>Recent Closed Paper Trades</span>
            </h2>
            {onNavigateToJournal && (
              <button
                onClick={onNavigateToJournal}
                className="text-xs text-purple-400 hover:text-purple-300 font-medium flex items-center gap-1 transition-colors"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Trade Journal</span>
              </button>
            )}
          </div>

          {tradeReports.length === 0 ? (
            <div className="p-6 rounded-2xl border border-white/[0.06] bg-[#0D1322]/40 text-center text-xs text-slate-400 font-mono">
              No closed paper trades recorded in this session.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-white/[0.08] bg-[#0D1322]/80">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-white/[0.03] border-b border-white/[0.08] text-slate-400 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="p-3">Symbol</th>
                    <th className="p-3">Strategy</th>
                    <th className="p-3">Entry</th>
                    <th className="p-3">Exit</th>
                    <th className="p-3">Gross</th>
                    <th className="p-3">Fees &amp; Slip</th>
                    <th className="p-3">Net P&amp;L</th>
                    <th className="p-3">Outcome</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05] text-slate-200">
                  {tradeReports.map((t) => {
                    const isWin = t.net_pnl > 0;
                    return (
                      <tr key={t.id} className="hover:bg-white/[0.02]">
                        <td className="p-3 font-bold text-white">{t.symbol}</td>
                        <td className="p-3 text-slate-400 truncate max-w-[120px]">{t.strategy_name}</td>
                        <td className="p-3">₹{t.entry_price.toFixed(2)}</td>
                        <td className="p-3">₹{t.exit_price.toFixed(2)}</td>
                        <td className="p-3">₹{t.gross_pnl.toFixed(2)}</td>
                        <td className="p-3 text-slate-400">₹{((t.fees || 0) + (t.slippage || 0)).toFixed(2)}</td>
                        <td className={`p-3 font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {isWin ? '+' : ''}₹{t.net_pnl.toFixed(2)}
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] ${
                              t.exit_reason === 'TARGET_HIT' || t.net_pnl > 0
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {t.exit_reason || 'CLOSED'}
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

        {/* System Guardrails & Status (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          <h2 className="text-xs sm:text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
            <span>Terminal Guardrails</span>
          </h2>

          <div className="p-4 rounded-2xl bg-[#0D1322]/80 border border-white/[0.08] space-y-3 text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <span className="text-slate-400">Emergency Stop:</span>
              <span
                className={`font-mono font-bold px-2 py-0.5 rounded text-[10px] ${
                  isEmergencyStop
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                }`}
              >
                {isEmergencyStop ? 'HALTED' : 'READY / ACTIVE'}
              </span>
            </div>

            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <span className="text-slate-400">AI Intelligence:</span>
              <StatusBadge status={aiStatus?.is_online ? 'AI ONLINE' : 'AI FALLBACK'} size="sm" />
            </div>

            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <span className="text-slate-400">Broker Gateway:</span>
              <StatusBadge status={brokerStatus?.is_connected ? 'BROKER CONNECTED' : 'BROKER NOT CONNECTED'} size="sm" />
            </div>

            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <span className="text-slate-400">Live Order Shield:</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                HTTP 403 FAIL-CLOSED
              </span>
            </div>

            <div className="pt-1 text-[11px] text-slate-400 leading-relaxed font-mono">
              Max Risk/Trade: <span className="text-white">0.5% (₹10.00)</span> • Daily Loss Cap: <span className="text-white">₹40.00</span>
            </div>
          </div>
        </div>
      </div>

      {/* Paper Trade Confirmation Modal */}
      <PaperTradeApprovalModal
        proposal={selectedProposal}
        isOpen={approvalModalOpen}
        onClose={() => setApprovalModalOpen(false)}
        onConfirm={handleConfirmApproval}
        loading={approvalLoading}
        error={approvalError}
      />
    </div>
  );
};
