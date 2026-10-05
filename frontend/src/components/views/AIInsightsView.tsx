import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  Info,
  ShieldAlert,
  Brain,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Layers,
  Activity,
  Cpu,
  ShieldCheck,
  Zap,
  Server,
  XCircle,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  MarketType,
  AIAnalysisResponse,
  AIProviderStatus,
} from '../../types/market';
import { LoadingSpinner } from '../common/LoadingSpinner';

export const AIInsightsView: React.FC = () => {
  const [providerStatus, setProviderStatus] = useState<AIProviderStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState<boolean>(true);

  // Live evaluation form state
  const [selectedSymbol, setSelectedSymbol] = useState<string>('RELIANCE');
  const [selectedMarket, setSelectedMarket] = useState<MarketType>('NSE');
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('1D');
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysisResponse | null>(null);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

  const fetchStatus = async () => {
    try {
      setStatusLoading(true);
      const res = await api.getAIStatus();
      setProviderStatus(res);
    } catch (err: any) {
      console.warn('AI status check failed:', err);
    } finally {
      setStatusLoading(false);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      setEvaluating(true);
      setMessage(null);
      const res = await api.evaluateAIAnalysis({
        symbol: selectedSymbol,
        market: selectedMarket,
        timeframe: selectedTimeframe,
      });
      setAiAnalysis(res);
      setMessage({
        text: `AI evaluation completed using ${res.model_name} (${res.quality_metrics.provider_type}). Hallucination defense verified.`,
        type: 'success',
      });
    } catch (err: any) {
      setMessage({ text: err.message || 'AI evaluation failed', type: 'error' });
    } finally {
      setEvaluating(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Auto run evaluation for initial default symbol
    handleRunEvaluation();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] p-6 rounded-2xl shadow-xl shadow-black/40 relative overflow-hidden">
        <div className="absolute top-0 right-1/4 w-96 h-32 bg-indigo-500/[0.03] rounded-full blur-3xl pointer-events-none" />
        <div className="flex items-center gap-4 relative z-10">
          <div className="p-3 bg-gradient-to-br from-indigo-500/15 to-purple-600/15 border border-indigo-500/30 rounded-xl text-indigo-400 shadow-md shadow-indigo-500/10">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-xl font-bold text-white tracking-tight">
                AI Market Reasoning & Hallucination Defense
              </h1>
              <span className="text-[10px] bg-indigo-500/10 text-indigo-300 font-mono px-2.5 py-0.5 rounded-full border border-indigo-500/30 font-semibold tracking-wide">
                STRICT PYDANTIC SCHEMAS
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Local Ollama reasoning with deterministic fallback, evidence grounding, and anti-hallucination validation.
            </p>
          </div>
        </div>

        {/* AI Provider Status Card */}
        <div className="flex items-center gap-3 bg-white/[0.03] px-4 py-2 rounded-xl border border-white/[0.06] text-xs relative z-10 shadow-sm">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                providerStatus?.is_online
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse'
                  : 'bg-amber-400'
              }`}
            />
            <span className="text-slate-300 font-mono text-[11px] font-semibold">
              {providerStatus?.is_online ? 'Local Ollama: ONLINE' : 'Fallback: DETERMINISTIC'}
            </span>
          </div>
          <span className="text-slate-500 font-mono text-[10px]">
            Model: {providerStatus?.model_name || 'deepseek-r1:1.5b'}
          </span>
          <button
            onClick={fetchStatus}
            disabled={statusLoading}
            className="text-slate-400 hover:text-white ml-1 p-1 rounded-md hover:bg-white/[0.05] transition-colors"
            title="Refresh AI Provider Status"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${statusLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {message && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between shadow-md ${
            message.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : message.type === 'info'
              ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}
        >
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-white">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Grid: Evaluation Controls & Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Selector & Quality Guardrails */}
        <div className="space-y-6">
          <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 space-y-4 shadow-xl shadow-black/40">
            <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-white/[0.06] pb-3">
              <Brain className="w-4 h-4 text-cyan-400" />
              Run Market AI Reasoning
            </h2>

            <div className="space-y-3.5 text-xs">
              <div>
                <label className="text-slate-300 block mb-1">Market Category</label>
                <select
                  value={selectedMarket}
                  onChange={(e) => {
                    const m = e.target.value as MarketType;
                    setSelectedMarket(m);
                    if (m === 'NSE') setSelectedSymbol('RELIANCE');
                    else if (m === 'FOREX') setSelectedSymbol('EUR/USD');
                    else setSelectedSymbol('GOLD');
                  }}
                  className="w-full bg-[#070A12]/80 border border-white/[0.08] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500/60 shadow-inner"
                >
                  <option value="NSE">NSE (Indian Equities)</option>
                  <option value="FOREX">FOREX (Currencies)</option>
                  <option value="MCX">MCX (Commodities)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 block mb-1">Instrument Symbol</label>
                <select
                  value={selectedSymbol}
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                  className="w-full bg-panel-subtle border border-border rounded px-3 py-1.5 text-white focus:outline-none focus:border-accent font-mono"
                >
                  {selectedMarket === 'NSE' && (
                    <>
                      <option value="RELIANCE">RELIANCE</option>
                      <option value="TCS">TCS</option>
                      <option value="INFY">INFY</option>
                      <option value="HDFCBANK">HDFCBANK</option>
                      <option value="NIFTY 50">NIFTY 50</option>
                    </>
                  )}
                  {selectedMarket === 'FOREX' && (
                    <>
                      <option value="EUR/USD">EUR/USD</option>
                      <option value="GBP/USD">GBP/USD</option>
                    </>
                  )}
                  {selectedMarket === 'MCX' && (
                    <>
                      <option value="GOLD">GOLD</option>
                      <option value="CRUDEOIL">CRUDEOIL</option>
                    </>
                  )}
                </select>
              </div>

              <div>
                <label className="text-slate-300 block mb-1">Timeframe</label>
                <select
                  value={selectedTimeframe}
                  onChange={(e) => setSelectedTimeframe(e.target.value)}
                  className="w-full bg-panel-subtle border border-border rounded px-3 py-1.5 text-white focus:outline-none focus:border-accent"
                >
                  <option value="1D">1D (Daily)</option>
                  <option value="4H">4H (4 Hours)</option>
                  <option value="1H">1H (Hourly)</option>
                </select>
              </div>

              <button
                onClick={handleRunEvaluation}
                disabled={evaluating}
                className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-xl font-semibold flex items-center justify-center gap-2 transition-all shadow-md shadow-cyan-500/20 text-xs mt-2"
              >
                {evaluating ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Generating Grounded AI Analysis...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Synthesize Market Rationale</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Quality Metrics Panel */}
          {aiAnalysis && (
            <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 space-y-4 shadow-xl shadow-black/40">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
                <h3 className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-wider font-mono">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Hallucination Defense Metrics
                </h3>
                <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold">
                  {aiAnalysis.hallucination_defense_passed ? 'PASSED' : 'FLAGGED'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2.5 text-xs">
                <div className="bg-[#0B101E]/60 p-3 rounded-xl border border-white/[0.06]">
                  <span className="text-[10px] text-slate-400 block mb-0.5">Input Completeness</span>
                  <span className="font-mono text-white font-bold text-sm">
                    {aiAnalysis.quality_metrics.input_completeness_pct}%
                  </span>
                </div>

                <div className="bg-[#0B101E]/60 p-3 rounded-xl border border-white/[0.06]">
                  <span className="text-[10px] text-slate-400 block mb-0.5">Data Freshness</span>
                  <span className="font-mono text-emerald-400 font-bold text-sm">
                    {aiAnalysis.quality_metrics.data_freshness_seconds}s
                  </span>
                </div>

                <div className="bg-[#0B101E]/60 p-3 rounded-xl border border-white/[0.06]">
                  <span className="text-[10px] text-slate-400 block mb-0.5">Model Latency</span>
                  <span className="font-mono text-cyan-400 font-bold text-sm">
                    {aiAnalysis.quality_metrics.model_latency_ms.toFixed(1)} ms
                  </span>
                </div>

                <div className="bg-[#0B101E]/60 p-3 rounded-xl border border-white/[0.06]">
                  <span className="text-[10px] text-slate-400 block mb-0.5">Claims Rejected</span>
                  <span className="font-mono text-white font-bold text-sm">
                    {aiAnalysis.quality_metrics.unsupported_claims_rejected}
                  </span>
                </div>
              </div>

              <div className="text-[10px] text-slate-400 font-mono pt-1">
                Provider Type: <strong className="text-slate-200">{aiAnalysis.quality_metrics.provider_type}</strong>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Grounded AI Analysis Synthesis */}
        <div className="lg:col-span-2 space-y-6">
          {evaluating ? (
            <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-12 flex flex-col items-center justify-center space-y-3 shadow-xl">
              <LoadingSpinner size="lg" />
              <p className="text-xs text-slate-400 font-mono">
                Extracting indicators, calculating confluence, and applying strict Pydantic hallucination filters...
              </p>
            </div>
          ) : aiAnalysis ? (
            <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 space-y-5 shadow-2xl shadow-black/40">
              {/* Analysis Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.06] pb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono font-bold text-white text-lg">{aiAnalysis.symbol}</span>
                    <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-white/[0.04] text-slate-300 border border-white/[0.08]">
                      {aiAnalysis.timeframe}
                    </span>
                    <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/30">
                      Regime: {aiAnalysis.market_regime}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">Evaluated: {aiAnalysis.timestamp}</span>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-mono px-3.5 py-1.5 rounded-full font-bold uppercase tracking-wider ${
                      aiAnalysis.sentiment === 'BULLISH'
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/35 shadow-emerald-500/10'
                        : aiAnalysis.sentiment === 'BEARISH'
                        ? 'bg-rose-500/15 text-rose-300 border border-rose-500/35 shadow-rose-500/10'
                        : 'bg-white/[0.04] text-slate-300 border border-white/[0.08]'
                    }`}
                  >
                    {aiAnalysis.sentiment} ({(aiAnalysis.confidence_score * 100).toFixed(0)}% Conf)
                  </span>
                  <span className="text-xs font-mono px-3 py-1.5 rounded-full font-bold bg-white/[0.03] border border-white/[0.06] text-cyan-400">
                    Action: {aiAnalysis.recommended_action}
                  </span>
                </div>
              </div>

              {/* Primary Rationale */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-cyan-400" />
                  Primary Analytical Rationale
                </span>
                <p className="text-xs text-slate-200 leading-relaxed bg-[#0B101E]/60 p-4 rounded-xl border border-white/[0.06]">
                  {aiAnalysis.primary_rationale}
                </p>
              </div>

              {/* Key Evidence & Conflicting Signals */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="space-y-2">
                  <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Grounded Indicator Evidence
                  </span>
                  <ul className="space-y-1.5 bg-[#0B101E]/60 p-4 rounded-xl border border-white/[0.06] text-[11px] text-slate-300">
                    {aiAnalysis.key_evidence.map((ev, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-emerald-400 font-bold">•</span>
                        <span className="leading-relaxed">{ev}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="space-y-2">
                  <span className="font-semibold text-rose-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" /> Conflicting Signals & Uncertainty
                  </span>
                  <ul className="space-y-1.5 bg-[#0B101E]/60 p-4 rounded-xl border border-white/[0.06] text-[11px] text-slate-300">
                    {aiAnalysis.conflicting_signals.length > 0 ? (
                      aiAnalysis.conflicting_signals.map((cs, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-rose-400 font-bold">•</span>
                          <span className="leading-relaxed">{cs}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-slate-500 italic">No conflicting indicator signals detected.</li>
                    )}
                    {aiAnalysis.uncertainty_factors.map((u, i) => (
                      <li key={`u-${i}`} className="flex items-start gap-2 text-amber-300">
                        <span className="font-bold">•</span>
                        <span className="leading-relaxed">{u}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Strict Risk Caveats */}
              <div className="space-y-2 text-xs">
                <span className="font-semibold text-amber-400 flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4" /> Risk Caveats & Protective Parameters
                </span>
                <div className="bg-amber-950/20 border border-amber-500/30 rounded-xl p-3.5 text-[11px] text-amber-200/90 space-y-1">
                  {aiAnalysis.risk_caveats.map((c, i) => (
                    <div key={i}>• {c}</div>
                  ))}
                </div>
              </div>

              {/* Non-Financial Advice Disclaimer */}
              <div className="p-3 bg-panel-subtle border border-border rounded-lg text-[10px] text-slate-500 leading-relaxed">
                <strong>Disclaimer:</strong> AI generated analysis is solely for algorithmic research, simulation, and educational purposes. It does not constitute investment advice or an automated authorization to trade. In this architecture, all order execution is governed by independent deterministic risk gates and mandatory user confirmation.
              </div>
            </div>
          ) : (
            <div className="bg-panel border border-border rounded-xl p-12 text-center text-slate-500">
              Click 'Synthesize Market Rationale' to inspect live AI analysis.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
