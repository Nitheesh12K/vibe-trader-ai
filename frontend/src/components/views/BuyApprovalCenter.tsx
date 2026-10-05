import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  RefreshCw,
  Search,
  Filter,
  Zap,
  Activity,
  Layers,
  Inbox,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../../services/api';
import { BuyProposalRead } from '../../types/market';
import { ProposalCard } from './ProposalCard';
import { PaperTradeApprovalModal } from '../common/PaperTradeApprovalModal';
import { StatusAlert } from '../common/StatusAlert';
import { SkeletonRow } from '../common/Skeleton';
import { StatusBadge } from '../common/Badge';

export const BuyApprovalCenter: React.FC = () => {
  const [proposals, setProposals] = useState<BuyProposalRead[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [scanning, setScanning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');
  const [marketFilter, setMarketFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Approval modal state
  const [selectedProposalForApproval, setSelectedProposalForApproval] = useState<BuyProposalRead | null>(null);
  const [approvalModalOpen, setApprovalModalOpen] = useState<boolean>(false);
  const [approvalSubmitting, setApprovalSubmitting] = useState<boolean>(false);
  const [approvalModalError, setApprovalModalError] = useState<string | null>(null);

  // Per-proposal action loading state for duplicate click protection
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' | 'warning' } | null>(null);

  const fetchProposals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getProposals();
      setProposals(data);
    } catch (err: any) {
      console.error('Failed to load buy proposals:', err);
      setError(err.message || 'Unable to fetch buy proposals from server.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProposals();
    const interval = setInterval(fetchProposals, 15000);
    return () => clearInterval(interval);
  }, [fetchProposals]);

  const showToast = (text: string, type: 'success' | 'error' | 'warning' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 4500);
  };

  const handleScanOpportunities = async () => {
    try {
      setScanning(true);
      const res = await api.triggerMonitoringScan();
      showToast(
        `Market scan complete: Scanned ${res.scanned_symbols} symbols, generated ${res.new_proposals} new proposal(s).`,
        'success'
      );
      await fetchProposals();
    } catch (err: any) {
      showToast(`Scan failed: ${err.message}`, 'error');
    } finally {
      setScanning(false);
    }
  };

  const handleOpenApproveModal = (proposal: BuyProposalRead) => {
    setApprovalModalError(null);
    setSelectedProposalForApproval(proposal);
    setApprovalModalOpen(true);
  };

  const handleConfirmApproval = async (proposalId: string, notes: string) => {
    try {
      setApprovalSubmitting(true);
      setApprovalModalError(null);
      setActionLoading((prev) => ({ ...prev, [proposalId]: true }));

      const res = await api.approveProposal(proposalId, notes);
      setApprovalModalOpen(false);
      showToast(`Paper Trade Executed! Position ID: ${res.position_id} @ fill ₹${res.fill_price}`, 'success');
      await fetchProposals();
    } catch (err: any) {
      setApprovalModalError(err.message || 'Approval execution failed.');
      showToast(`Approval failed: ${err.message}`, 'error');
    } finally {
      setApprovalSubmitting(false);
      setActionLoading((prev) => ({ ...prev, [proposalId]: false }));
    }
  };

  const handleReject = async (proposalId: string, reason: string) => {
    try {
      setActionLoading((prev) => ({ ...prev, [proposalId]: true }));
      const res = await api.rejectProposal(proposalId, reason);
      showToast(`Proposal rejected: ${res.message}`, 'warning');
      await fetchProposals();
    } catch (err: any) {
      showToast(`Rejection failed: ${err.message}`, 'error');
    } finally {
      setActionLoading((prev) => ({ ...prev, [proposalId]: false }));
    }
  };

  const filteredProposals = proposals.filter((p) => {
    if (statusFilter !== 'ALL' && p.status !== statusFilter) return false;
    if (marketFilter !== 'ALL' && p.market !== marketFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchSym = p.symbol.toLowerCase().includes(q);
      const matchStrat = p.strategy_name.toLowerCase().includes(q);
      if (!matchSym && !matchStrat) return false;
    }
    return true;
  });

  const pendingCount = proposals.filter((p) => p.status === 'PENDING').length;
  const approvedCount = proposals.filter((p) => p.status === 'APPROVED_AND_EXECUTED').length;
  const rejectedCount = proposals.filter((p) => p.status === 'REJECTED' || p.status === 'EXPIRED').length;

  return (
    <div className="space-y-5">
      {/* Toast Notification */}
      {toastMessage && (
        <div
          role="alert"
          className={`fixed top-16 right-6 z-50 px-4 py-2.5 rounded-xl border backdrop-blur-xl text-xs font-semibold flex items-center gap-2 shadow-2xl transition-all ${
            toastMessage.type === 'success'
              ? 'bg-emerald-950/90 text-emerald-200 border-emerald-500/30'
              : toastMessage.type === 'warning'
              ? 'bg-amber-950/90 text-amber-200 border-amber-500/30'
              : 'bg-rose-950/90 text-rose-200 border-rose-500/30'
          }`}
        >
          <ShieldCheck className="w-4 h-4 shrink-0" />
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="relative overflow-hidden bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] p-5 sm:p-6 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-amber-500/10 border border-amber-500/25 rounded-xl text-amber-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  BUY APPROVAL CENTER
                </h1>
                <StatusBadge status="PAPER TRADING" size="sm" />
              </div>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                Mandatory Human-in-the-Loop Gate • Zero Automated BUY Orders
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button
            onClick={fetchProposals}
            disabled={loading}
            className="p-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-slate-400 hover:text-white transition-colors border border-white/[0.06]"
            title="Refresh Proposals"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>

          <button
            onClick={handleScanOpportunities}
            disabled={scanning}
            className="flex-1 sm:flex-initial px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 shadow-lg shadow-amber-500/20 transition-all flex items-center justify-center gap-2"
          >
            <Zap className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
            <span>{scanning ? 'Scanning Market...' : 'Scan for Opportunities'}</span>
          </button>
        </div>
      </div>

      {/* KPI Filter Badges Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-[#0B101D]/70 border border-white/[0.06]">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setStatusFilter('PENDING')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
              statusFilter === 'PENDING'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white bg-white/[0.02]'
            }`}
          >
            <span>Pending Review</span>
            <span className="px-1.5 py-0.2 rounded-full bg-amber-500/30 text-[10px] text-amber-200">
              {pendingCount}
            </span>
          </button>

          <button
            onClick={() => setStatusFilter('APPROVED_AND_EXECUTED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
              statusFilter === 'APPROVED_AND_EXECUTED'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white bg-white/[0.02]'
            }`}
          >
            <span>Approved</span>
            <span className="px-1.5 py-0.2 rounded-full bg-emerald-500/30 text-[10px] text-emerald-200">
              {approvedCount}
            </span>
          </button>

          <button
            onClick={() => setStatusFilter('REJECTED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
              statusFilter === 'REJECTED'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white bg-white/[0.02]'
            }`}
          >
            <span>Blocked / Rejected</span>
            <span className="px-1.5 py-0.2 rounded-full bg-rose-500/30 text-[10px] text-rose-200">
              {rejectedCount}
            </span>
          </button>

          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
              statusFilter === 'ALL'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-white bg-white/[0.02]'
            }`}
          >
            All ({proposals.length})
          </button>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-56">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter symbols or strategies..."
            className="w-full bg-[#070A12] border border-white/[0.08] rounded-lg pl-8 pr-2.5 py-1 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/40 font-mono"
          />
        </div>
      </div>

      {/* Main Content Area: Cards or Empty/Loading States */}
      {loading && proposals.length === 0 ? (
        <SkeletonRow rows={3} cols={4} />
      ) : error ? (
        <StatusAlert
          type="BACKEND_OFFLINE"
          title="Could Not Load Proposals"
          detail={error}
          onRetry={fetchProposals}
        />
      ) : filteredProposals.length === 0 ? (
        <StatusAlert
          type="NO_PROPOSALS"
          title={statusFilter === 'PENDING' ? 'NO PENDING BUY PROPOSALS' : 'NO PROPOSALS FOUND'}
          detail={
            statusFilter === 'PENDING'
              ? 'The algorithm engine is continuously scanning for valid high-confluence setups. Click "Run Market Scan" to trigger an on-demand scan.'
              : 'No proposals match the current filter criteria.'
          }
        />
      ) : (
        <div className="space-y-4">
          {filteredProposals.map((proposal) => (
            <ProposalCard
              key={proposal.proposal_id}
              proposal={proposal}
              onApproveClick={handleOpenApproveModal}
              onRejectClick={handleReject}
              isActionLoading={!!actionLoading[proposal.proposal_id]}
            />
          ))}
        </div>
      )}

      {/* Paper Trade Confirmation Modal */}
      <PaperTradeApprovalModal
        proposal={selectedProposalForApproval}
        isOpen={approvalModalOpen}
        onClose={() => setApprovalModalOpen(false)}
        onConfirm={handleConfirmApproval}
        loading={approvalSubmitting}
        error={approvalModalError}
      />
    </div>
  );
};
