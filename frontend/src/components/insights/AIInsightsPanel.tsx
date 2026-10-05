import React from 'react';
import { Sparkles, Bot, ShieldAlert, Cpu } from 'lucide-react';
import { AIInsightSummary } from '../../types/market';
import { Badge } from '../common/Badge';

interface AIInsightsPanelProps {
  insight: AIInsightSummary | null;
}

export const AIInsightsPanel: React.FC<AIInsightsPanelProps> = ({ insight }) => {
  return (
    <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-indigo-500/25 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 relative overflow-hidden group">
      {/* Background glow effect */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none group-hover:bg-indigo-500/15 transition-colors" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-white">
            AI Market Insights
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="demo" size="sm">
            AI RESEARCH ONLY
          </Badge>
          {insight && (
            <span
              className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded-md border ${
                insight.sentiment === 'Bullish'
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                  : insight.sentiment === 'Bearish'
                  ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                  : 'bg-[#121B2F] text-slate-300 border-white/[0.08]'
              }`}
            >
              {insight.sentiment} ({(insight.confidence * 100).toFixed(0)}%)
            </span>
          )}
        </div>
      </div>

      {/* Insight Content */}
      <div className="space-y-3 text-xs text-slate-300">
        <div className="font-bold text-white flex items-center gap-2 text-sm">
          <Bot className="w-4 h-4 text-indigo-400 shrink-0" />
          <span>{insight?.title || 'Multi-Market Regime & Momentum Overview'}</span>
        </div>

        <p className="leading-relaxed text-slate-300 text-xs sm:text-[13px] bg-[#080D1A]/70 p-4 rounded-xl border border-white/[0.06] shadow-inner">
          {insight?.summary ||
            'Analyzing simulated volatility spreads across Indian equities (NSE), multi-commodity exchange (MCX), and major Forex pairs. Technical momentum indicates selective consolidation with range-bound volume.'}
        </p>

        {/* Safety Disclaimer Banner */}
        <div className="mt-3 flex items-start gap-2.5 text-[11px] bg-amber-500/10 border border-amber-500/25 p-3 rounded-xl text-amber-300 font-mono">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <span>
            <strong>Safety Guardrail:</strong> AI insights are educational research summaries. AI outputs are strictly prohibited from placing, altering, or triggering automated financial transactions.
          </span>
        </div>
      </div>
    </div>
  );
};
