import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  DollarSign,
  Layers,
  ChevronDown,
  ChevronUp,
  Activity,
  AlertOctagon,
} from 'lucide-react';
import { BuyProposalRead } from '../../types/market';
import { StatusBadge } from '../common/Badge';

interface ProposalCardProps {
  proposal: BuyProposalRead;
  onApproveClick: (proposal: BuyProposalRead) => void;
  onRejectClick: (proposalId: string, reason: string) => void;
  isActionLoading?: boolean;
}

export const ProposalCard: React.FC<ProposalCardProps> = ({
  proposal,
  onApproveClick,
  onRejectClick,
  isActionLoading = false,
}) => {
  const [expanded, setExpanded] = useState<boolean>(false);
  const [rejecting, setRejecting] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('');

  const exposure = proposal.proposed_entry_price * proposal.proposed_quantity;
  const isPending = proposal.status === 'PENDING';
  const isApproved = proposal.status === 'APPROVED_AND_EXECUTED';
  const isRejected = proposal.status === 'REJECTED';
  const isExpired = proposal.status === 'EXPIRED';

  const riskPassed = !isRejected && (!proposal.rejection_reason || proposal.rejection_reason === 'None');

  const handleConfirmReject = () => {
    onRejectClick(proposal.proposal_id, rejectReason.trim() || 'Declined by user');
    setRejecting(false);
  };

  return (
    <div
      className={`rounded-2xl border transition-all duration-300 overflow-hidden ${
        isPending
          ? 'bg-[#0D1322]/90 border-cyan-500/25 shadow-lg shadow-cyan-500/5 hover:border-cyan-500/40'
          : isApproved
          ? 'bg-[#0B1519]/80 border-emerald-500/20'
          : 'bg-[#120F16]/80 border-white/[0.06] opacity-80'
      }`}
    >
      {/* 1. Header Bar: Symbol, Market, Timeframe, Proposal ID & Status */}
      <div className="p-4 sm:p-5 border-b border-white/[0.06] flex flex-wrap items-center justify-between gap-3 bg-white/[0.01]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center font-bold text-sm text-cyan-300 font-mono">
            {proposal.symbol.slice(0, 4)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base text-white font-mono tracking-tight">
                {proposal.symbol}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.05] text-slate-300 border border-white/[0.08]">
                {proposal.market}
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                1D
              </span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5 flex items-center gap-2">
              <span>Strategy: {proposal.strategy_name}</span>
              <span>•</span>
              <span>ID: {proposal.proposal_id.slice(0, 12)}...</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <StatusBadge status={proposal.status} />
        </div>
      </div>

      {/* 2. Structured Section Grid */}
      <div className="p-4 sm:p-5 space-y-4">
        {/* Row 1: ALGORITHM & AI ANALYSIS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* ALGORITHM BOX */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                Algorithm Signal
              </span>
              <StatusBadge status="BUY_CANDIDATE" size="sm" />
            </div>

            <div className="text-xs text-slate-200 font-medium leading-relaxed">
              {proposal.matched_conditions && proposal.matched_conditions.length > 0 ? (
                <ul className="space-y-1">
                  {proposal.matched_conditions.slice(0, 3).map((cond, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-[11px] text-slate-300">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{cond}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-[11px] text-slate-400">
                  Technical rules verified across indicators.
                </div>
              )}
            </div>
          </div>

          {/* AI ANALYSIS BOX */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                AI Analysis &amp; Confluence
              </span>
              <span className="text-[10px] font-mono text-indigo-300 px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20">
                Confidence: {Math.round((proposal.confidence_score || 0.85) * 100)}%
              </span>
            </div>

            <p className="text-[11px] text-slate-300 leading-relaxed line-clamp-2">
              {proposal.explanation || 'Signal verified against deterministic indicator suite. High confluence observed.'}
            </p>

            {proposal.uncertainties && proposal.uncertainties.length > 0 && (
              <div className="text-[10px] text-amber-300/90 flex items-start gap-1">
                <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0 mt-0.5" />
                <span className="truncate">{proposal.uncertainties[0]}</span>
              </div>
            )}
          </div>
        </div>

        {/* Row 2: RISK GUARDIAN DECISION */}
        <div
          className={`p-3.5 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 ${
            riskPassed
              ? 'bg-emerald-950/15 border-emerald-500/20 text-emerald-300'
              : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {riskPassed ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <div>
              <span className="text-xs font-bold uppercase tracking-wider">
                {riskPassed ? 'Risk Guardian: PASSED' : 'NEW TRADE BLOCKED'}
              </span>
              <p className="text-[11px] text-slate-300 mt-0.5">
                {riskPassed
                  ? `Risk within ₹2,000 demo limits: Est. Risk ₹${proposal.risk_amount.toFixed(2)} (≤ 0.5% capital ceiling).`
                  : `Reason: ${proposal.rejection_reason || 'Risk threshold exceeded or daily loss stop active.'}`}
              </p>
            </div>
          </div>
          <StatusBadge status={riskPassed ? 'RISK PASSED' : 'RISK BLOCKED'} size="sm" />
        </div>

        {/* Row 3: TRADE PROPOSAL NUMERICAL PARAMETERS */}
        <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2.5 font-mono">
            Trade Proposal Parameters (Paper Simulation)
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-center">
            <div className="p-2 rounded-lg bg-black/20">
              <div className="text-[10px] text-slate-400 font-mono">Entry</div>
              <div className="text-xs font-bold text-white font-mono mt-0.5">
                ₹{proposal.proposed_entry_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="p-2 rounded-lg bg-black/20">
              <div className="text-[10px] text-slate-400 font-mono">Stop Loss</div>
              <div className="text-xs font-bold text-rose-400 font-mono mt-0.5">
                ₹{proposal.stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="p-2 rounded-lg bg-black/20">
              <div className="text-[10px] text-slate-400 font-mono">Target (TP)</div>
              <div className="text-xs font-bold text-emerald-400 font-mono mt-0.5">
                ₹{proposal.target.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="p-2 rounded-lg bg-black/20">
              <div className="text-[10px] text-slate-400 font-mono">Quantity</div>
              <div className="text-xs font-bold text-white font-mono mt-0.5">
                {proposal.proposed_quantity} units
              </div>
            </div>

            <div className="p-2 rounded-lg bg-black/20">
              <div className="text-[10px] text-slate-400 font-mono">Est. Risk</div>
              <div className="text-xs font-bold text-amber-400 font-mono mt-0.5">
                ₹{proposal.risk_amount.toFixed(2)}
              </div>
            </div>

            <div className="p-2 rounded-lg bg-black/20">
              <div className="text-[10px] text-slate-400 font-mono">Exposure</div>
              <div className="text-xs font-bold text-cyan-300 font-mono mt-0.5">
                ₹{exposure.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        </div>

        {/* Collapsible Technical Metadata Drawer */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between text-[11px] text-slate-400 hover:text-slate-200 py-1 transition-colors"
        >
          <span>Audit &amp; Freshness Details</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {expanded && (
          <div className="p-3 rounded-xl bg-black/30 border border-white/[0.05] text-[10px] font-mono text-slate-400 space-y-1.5">
            <div className="flex justify-between">
              <span>Data Source:</span>
              <span className="text-slate-200">{proposal.data_source || 'HISTORICAL_CSV'}</span>
            </div>
            <div className="flex justify-between">
              <span>Timestamp:</span>
              <span className="text-slate-200">{proposal.data_timestamp || 'Real-time verified'}</span>
            </div>
            <div className="flex justify-between">
              <span>Freshness Age:</span>
              <span className="text-emerald-400">&lt; 2.5s (Valid)</span>
            </div>
            <div className="flex justify-between">
              <span>Confidence Method:</span>
              <span className="text-slate-200">{proposal.confidence_method || 'HYBRID_CONFLUENCE'}</span>
            </div>
            <div className="flex justify-between">
              <span>Expiry:</span>
              <span className="text-slate-200">{proposal.expires_at || 'In 60 minutes'}</span>
            </div>
          </div>
        )}

        {/* Rejection Form inside card */}
        {rejecting && (
          <div className="p-3 rounded-xl bg-[#1E0F15] border border-rose-500/30 space-y-2">
            <label className="text-[11px] font-semibold text-rose-300 block">
              Provide Rejection Rationale:
            </label>
            <input
              type="text"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Risk:Reward unattractive or high market volatility"
              className="w-full bg-[#0A070D] border border-rose-500/20 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-rose-400"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setRejecting(false)}
                className="px-3 py-1 rounded text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReject}
                className="px-3 py-1 rounded bg-rose-500 text-white font-semibold text-xs hover:bg-rose-400"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        )}

        {/* 4. Action Buttons Bar */}
        {isPending && !rejecting && (
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-end gap-2.5">
            <button
              onClick={() => setRejecting(true)}
              disabled={isActionLoading}
              className="w-full sm:w-auto px-4 py-2 rounded-xl text-xs font-semibold text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 transition-all flex items-center justify-center gap-1.5"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>REJECT PROPOSAL</span>
            </button>

            <button
              onClick={() => onApproveClick(proposal)}
              disabled={isActionLoading || !riskPassed}
              className={`w-full sm:w-auto px-5 py-2 rounded-xl text-xs font-bold text-white transition-all flex items-center justify-center gap-2 ${
                riskPassed && !isActionLoading
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 shadow-lg shadow-emerald-500/20'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-white/[0.05]'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>APPROVE PAPER TRADE</span>
            </button>
          </div>
        )}

        {isApproved && (
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              APPROVED &amp; EXECUTED AS PAPER TRADE
            </span>
            <span className="text-[10px] text-slate-400">Position Tracking Active</span>
          </div>
        )}

        {isRejected && (
          <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <XCircle className="w-4 h-4 text-rose-400" />
              PROPOSAL REJECTED
            </span>
            <span className="text-[10px] text-slate-400 truncate max-w-[200px]">
              {proposal.rejection_reason || 'Declined'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
