import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Activity,
  Layers,
  Sparkles,
  ShieldAlert,
  UserCheck,
  Coins,
  ArrowRight,
  X,
  Lock,
  Database,
  KeyRound,
} from 'lucide-react';
import { api } from '../../services/api';
import { StatusBadge } from './Badge';

interface WelcomeOnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartPaperTrading: () => void;
}

export const WelcomeOnboardingModal: React.FC<WelcomeOnboardingModalProps> = ({
  isOpen,
  onClose,
  onStartPaperTrading,
}) => {
  const [virtualCapital, setVirtualCapital] = useState<number>(2000.0);
  const [brokerConnected, setBrokerConnected] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [dontShowAgain, setDontShowAgain] = useState<boolean>(true);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    const fetchState = async () => {
      try {
        setLoading(true);
        const [risk, broker] = await Promise.allSettled([
          api.getRiskSettings(),
          api.getZerodhaStatus(),
        ]);
        if (!isMounted) return;

        if (risk.status === 'fulfilled' && risk.value?.simulated_balance) {
          setVirtualCapital(risk.value.simulated_balance);
        }
        if (broker.status === 'fulfilled' && broker.value?.is_connected) {
          setBrokerConnected(broker.value.is_connected);
        }
      } catch (e) {
        console.warn('Welcome modal state fetch fallback:', e);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchState();
    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleDismiss = () => {
    if (dontShowAgain) {
      localStorage.setItem('vibe_onboarding_dismissed', 'true');
    }
    onClose();
  };

  const handleGetStarted = () => {
    if (dontShowAgain) {
      localStorage.setItem('vibe_onboarding_dismissed', 'true');
    }
    onStartPaperTrading();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in select-none"
    >
      <div className="relative w-full max-w-2xl bg-[#0B101D] border border-white/[0.12] rounded-3xl shadow-2xl shadow-cyan-500/10 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-cyan-500 via-sky-400 to-indigo-500" />
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-48 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 pb-4 border-b border-white/[0.06] relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 id="onboarding-title" className="text-base sm:text-lg font-bold text-white tracking-tight">
                WELCOME TO VIBE TRADER AI
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Hybrid Quantitative Algorithm &amp; AI Research Terminal
              </p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            aria-label="Close welcome modal"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-300">
          {/* Prominent Paper Trading Warning Banner */}
          <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 text-amber-200">
            <ShieldCheck className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <div className="font-bold text-xs uppercase tracking-wider text-amber-300">
                PAPER TRADING — NO REAL MONEY
              </div>
              <p className="text-[11px] text-amber-200/90 mt-0.5 leading-relaxed">
                All trades are simulated through the internal paper broker. Real capital is never exchanged, and live broker order routing is fail-closed.
              </p>
            </div>
          </div>

          {/* Real Current Application State Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] space-y-1">
              <div className="text-[10px] uppercase font-mono text-slate-400">Mode</div>
              <div className="font-bold text-cyan-400 font-mono">PAPER TRADING</div>
            </div>

            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] space-y-1">
              <div className="text-[10px] uppercase font-mono text-slate-400">Virtual Capital</div>
              <div className="font-bold text-white font-mono">
                {loading ? '...' : `₹${virtualCapital.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] space-y-1">
              <div className="text-[10px] uppercase font-mono text-slate-400">Market Data</div>
              <div className="font-bold text-emerald-400 font-mono">DEMO / HISTORICAL</div>
            </div>

            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] space-y-1">
              <div className="text-[10px] uppercase font-mono text-slate-400">Broker Status</div>
              <div className="font-bold text-slate-300 font-mono">
                {brokerConnected ? 'CONNECTED' : 'NOT CONNECTED'}
              </div>
            </div>
          </div>

          {/* 5 Architectural Steps Concise Explanations */}
          <div className="space-y-2">
            <div className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
              Core Execution Architecture
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
              <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-1">
                <div className="font-semibold text-cyan-400 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-cyan-400" />
                  1. Algorithm Engine
                </div>
                <p className="text-slate-400 leading-snug">
                  13 causal technical indicators and 7 rule-based strategies calculate signals without human emotion.
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-1">
                <div className="font-semibold text-indigo-400 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  2. AI Reasoning
                </div>
                <p className="text-slate-400 leading-snug">
                  Local Ollama synthesizes market state; switches automatically to deterministic fallback when offline.
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-1">
                <div className="font-semibold text-amber-400 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                  3. Risk Guardian
                </div>
                <p className="text-slate-400 leading-snug">
                  Deterministic gatekeeper enforcing ₹2,000 capital limits, 0.5% risk/trade, and ₹40 daily loss stops.
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-1">
                <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                  4. Human Approval
                </div>
                <p className="text-slate-400 leading-snug">
                  Zero automated BUYs. Every new paper trade proposal requires your explicit inspection and approval.
                </p>
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04] text-[11px] flex items-center gap-2">
              <Coins className="w-4 h-4 text-cyan-400 shrink-0" />
              <div className="text-slate-400 leading-snug">
                <span className="font-semibold text-slate-200">5. Paper Execution &amp; Auto-Exits: </span>
                Executes via internal virtual broker with realistic slippage and commissions. Autonomous exits guard stop losses.
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-5 border-t border-white/[0.06] bg-[#070A12]/80 flex flex-col sm:flex-row items-center justify-between gap-3 relative z-10">
          <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
              className="rounded bg-white/[0.05] border-white/[0.2] text-cyan-500 focus:ring-cyan-500/20"
            />
            <span>Do not show again automatically</span>
          </label>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            <button
              onClick={handleDismiss}
              className="flex-1 sm:flex-initial px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] transition-colors"
            >
              Explore Overview
            </button>
            <button
              onClick={handleGetStarted}
              className="flex-1 sm:flex-initial px-5 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center gap-1.5 group"
            >
              <span>START PAPER TRADING</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
