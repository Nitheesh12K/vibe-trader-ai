import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  X,
  Coins,
  Clock,
  ArrowRight,
  TrendingUp,
  AlertOctagon,
} from 'lucide-react';
import { BuyProposalRead } from '../../types/market';
import { StatusBadge } from './Badge';

interface PaperTradeApprovalModalProps {
  proposal: BuyProposalRead | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (proposalId: string, notes: string) => Promise<void>;
  loading: boolean;
  error?: string | null;
}

export const PaperTradeApprovalModal: React.FC<PaperTradeApprovalModalProps> = ({
  proposal,
  isOpen,
  onClose,
  onConfirm,
  loading,
  error,
}) => {
  const [confirmedCheckbox, setConfirmedCheckbox] = useState<boolean>(false);
  const [notes, setNotes] = useState<string>('');

  if (!isOpen || !proposal) return null;

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!confirmedCheckbox || loading) return;
    await onConfirm(proposal.proposal_id, notes);
  };

  const exposure = proposal.proposed_entry_price * proposal.proposed_quantity;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="approval-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in select-none"
    >
      <div className="relative w-full max-w-lg bg-[#0B101D] border border-white/[0.12] rounded-3xl shadow-2xl shadow-cyan-500/10 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header bar */}
        <div className="p-5 border-b border-white/[0.08] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h2 id="approval-modal-title" className="text-sm font-bold text-white tracking-tight">
                PAPER TRADE APPROVAL
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                Simulated Order Authorization via Internal Paper Broker
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            aria-label="Close approval modal"
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Content */}
        <form onSubmit={handleConfirm} className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {/* Simulation Reminder Banner */}
          <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-200 flex items-start gap-2.5">
            <Coins className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed">
              <span className="font-semibold text-white">VIRTUAL SIMULATION: </span>
              This order will be routed strictly to the internal paper broker. Real money is never used.
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-200 flex items-start gap-2.5">
              <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-[11px]">
                <div className="font-semibold text-rose-300">Approval Denied / Failed</div>
                <div className="mt-0.5 text-slate-300">{error}</div>
              </div>
            </div>
          )}

          {/* Trade Parameters Table */}
          <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-2.5">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div>
                <span className="text-sm font-bold text-white font-mono">{proposal.symbol}</span>
                <span className="text-[10px] text-slate-400 ml-1.5 font-mono">({proposal.market})</span>
              </div>
              <StatusBadge status="BUY_CANDIDATE" />
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div>
                <span className="text-slate-400">Strategy:</span>
                <div className="font-semibold text-slate-200 truncate">{proposal.strategy_name}</div>
              </div>
              <div>
                <span className="text-slate-400">Risk Guardian:</span>
                <div className="font-semibold text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> PASSED
                </div>
              </div>

              <div>
                <span className="text-slate-400">Entry Price:</span>
                <div className="font-semibold text-white">
                  ₹{proposal.proposed_entry_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div>
                <span className="text-slate-400">Quantity:</span>
                <div className="font-semibold text-white">{proposal.proposed_quantity} units</div>
              </div>

              <div>
                <span className="text-slate-400">Stop Loss:</span>
                <div className="font-semibold text-rose-400">
                  ₹{proposal.stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div>
                <span className="text-slate-400">Target (TP):</span>
                <div className="font-semibold text-emerald-400">
                  ₹{proposal.target.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>

              <div>
                <span className="text-slate-400">Estimated Risk:</span>
                <div className="font-semibold text-amber-400">
                  ₹{proposal.risk_amount.toFixed(2)}
                </div>
              </div>
              <div>
                <span className="text-slate-400">Total Exposure:</span>
                <div className="font-semibold text-cyan-300">
                  ₹{exposure.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span>Proposal ID: {proposal.proposal_id.slice(0, 16)}...</span>
              <span>R:R: {proposal.risk_reward_ratio?.toFixed(2) || '2.00'}</span>
            </div>
          </div>

          {/* Optional Notes */}
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-400">
              Approval Notes (Optional):
            </label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Validated 15m breakout confluence"
              className="w-full bg-[#070A12] border border-white/[0.08] rounded-xl px-3 py-1.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>

          {/* Mandatory Checkbox */}
          <label className="flex items-start gap-2.5 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] cursor-pointer select-none">
            <input
              type="checkbox"
              checked={confirmedCheckbox}
              onChange={(e) => setConfirmedCheckbox(e.target.checked)}
              className="mt-0.5 rounded bg-white/[0.05] border-white/[0.2] text-emerald-500 focus:ring-emerald-500/20"
            />
            <span className="text-[11px] text-slate-300 leading-snug">
              I understand this is a simulated paper trade using virtual capital. No real orders will be sent to any external broker.
            </span>
          </label>

          {/* Action buttons */}
          <div className="flex items-center justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!confirmedCheckbox || loading}
              className={`px-5 py-2 rounded-xl text-xs font-bold text-white transition-all flex items-center gap-1.5 ${
                confirmedCheckbox && !loading
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 shadow-lg shadow-emerald-500/20'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-white/[0.05]'
              }`}
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Validating Risk &amp; Executing...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>CONFIRM PAPER TRADE</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
