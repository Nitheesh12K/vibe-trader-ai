import React, { useState, useEffect } from 'react';
import {
  Brain,
  Shield,
  Eye,
  GitBranch,
  History,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  RefreshCw,
  Cpu,
  Layers,
  Activity,
  Zap,
  PlusCircle,
  Check,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  MarketType,
  IntelligenceStatusResponse,
  IntelligenceCycleResponse,
  LearningSummaryOutput,
  StrategyCandidateRead,
  LifecycleStage,
  StrategyCandidateCreate,
} from '../../types/market';

export const VibeIntelligenceView: React.FC = () => {
  const [status, setStatus] = useState<IntelligenceStatusResponse | null>(null);
  const [cycleResult, setCycleResult] = useState<IntelligenceCycleResponse | null>(null);
  const [learningSummary, setLearningSummary] = useState<LearningSummaryOutput | null>(null);
  const [candidates, setCandidates] = useState<StrategyCandidateRead[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isCycling, setIsCycling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Cycle Runner parameters
  const [selectedMarket, setSelectedMarket] = useState<MarketType>('FOREX');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('EUR/USD');
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('1D');

  // Candidate Strategy Modal
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newCandidate, setNewCandidate] = useState<StrategyCandidateCreate>({
    name: '',
    version: 'v1.1.0-rc1',
    market: 'FOREX',
    timeframe: '1D',
    parameters_json: '{\n  "rsi_period": 14,\n  "ema_fast": 9,\n  "ema_slow": 21\n}',
    rationale: '',
  });

  const SYMBOLS_BY_MARKET: Record<MarketType, string[]> = {
    FOREX: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD'],
    NSE: ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'NIFTY 50'],
    MCX: ['GOLD', 'SILVER', 'CRUDEOIL', 'NATURALGAS'],
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statusRes, learningRes, candidatesRes] = await Promise.all([
        api.getIntelligenceStatus(),
        api.getLearningSummary(),
        api.getStrategyCandidates(),
      ]);
      setStatus(statusRes);
      setLearningSummary(learningRes);
      setCandidates(candidatesRes);
    } catch (err: any) {
      console.error('Failed to load Vibe Intelligence status:', err);
      setError(err?.message || 'Failed to load Vibe Intelligence Core status.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunCycle = async () => {
    setIsCycling(true);
    setError(null);
    setActionMessage(null);
    try {
      const result = await api.runIntelligenceCycle(selectedSymbol, selectedTimeframe, selectedMarket);
      setCycleResult(result);
      const updatedStatus = await api.getIntelligenceStatus();
      setStatus(updatedStatus);
      setActionMessage(`Intelligence cycle completed for ${selectedSymbol}. Verdict: ${result.overall_decision}`);
    } catch (err: any) {
      console.error('Error running intelligence cycle:', err);
      setError(err?.message || 'Failed to run multi-agent intelligence cycle.');
    } finally {
      setIsCycling(false);
    }
  };

  const handleAdvanceCandidate = async (candidateId: number, targetStage: LifecycleStage) => {
    try {
      const updated = await api.advanceStrategyCandidate(candidateId, targetStage, `Advanced to ${targetStage} via Intelligence Console`);
      setCandidates((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      setActionMessage(`Candidate ${updated.candidate_id} advanced to ${targetStage}`);
    } catch (err: any) {
      setError(err?.message || `Failed to advance candidate stage to ${targetStage}.`);
    }
  };

  const handleActivateCandidate = async (candidateId: number) => {
    if (!window.confirm('Are you sure you want to promote this candidate to ACTIVE trading strategy?')) {
      return;
    }
    try {
      const updated = await api.activateStrategyCandidate(candidateId);
      setCandidates((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      setActionMessage(`Strategy ${updated.name} has been ACTIVATED for paper trading!`);
    } catch (err: any) {
      setError(err?.message || 'Failed to activate candidate.');
    }
  };

  const handleCreateCandidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCandidate.name || !newCandidate.rationale) {
      alert('Please fill out all required fields.');
      return;
    }
    try {
      const created = await api.createStrategyCandidate(newCandidate);
      setCandidates((prev) => [created, ...prev]);
      setShowCreateModal(false);
      setNewCandidate({
        name: '',
        version: 'v1.1.0-rc1',
        market: selectedMarket,
        timeframe: selectedTimeframe,
        parameters_json: '{\n  "rsi_period": 14\n}',
        rationale: '',
      });
      setActionMessage(`New strategy candidate ${created.candidate_id} created in CANDIDATE stage.`);
    } catch (err: any) {
      setError(err?.message || 'Failed to create candidate strategy.');
    }
  };

  const LIFECYCLE_STAGES: LifecycleStage[] = [
    'CANDIDATE',
    'SANDBOX',
    'BACKTESTED',
    'OUT_OF_SAMPLE_VALIDATED',
    'PAPER_TRADING',
    'REVIEW',
    'ACTIVATED',
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 backdrop-blur shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-gradient-to-tr from-purple-600 to-indigo-500 rounded-lg shadow-lg shadow-purple-900/20 text-white">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                  Vibe Intelligence Core
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/30">
                    Multi-Agent Architecture
                  </span>
                </h1>
                <p className="text-sm text-slate-400 mt-0.5">
                  Modular multi-agent coordination layer with deterministic risk gating, explainable confluence, and controlled strategy adaptation.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchInitialData}
              disabled={isLoading || isCycling}
              className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm border border-slate-700/60 transition"
              title="Refresh Intelligence State"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-950/70 border border-slate-800 rounded-lg">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs font-mono text-slate-300 uppercase">
                {status?.core_status || 'OPERATIONAL'}
              </span>
            </div>
          </div>
        </div>

        {/* Global Safety & Guardrails Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-5 border-t border-slate-800/80">
          <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/50">
            <span className="text-xs text-slate-400 block">Surveillance Regime</span>
            <span className="text-sm font-semibold text-slate-200 truncate block mt-0.5">
              {status?.active_regime || 'Multi-Market Surveillance'}
            </span>
          </div>
          <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/50">
            <span className="text-xs text-slate-400 block">Data Freshness</span>
            <span className="text-sm font-semibold text-emerald-400 font-mono mt-0.5 block">
              {status?.data_freshness_seconds !== undefined ? `${status.data_freshness_seconds.toFixed(1)}s` : '--'}
            </span>
          </div>
          <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/50">
            <span className="text-xs text-slate-400 block">Autonomous Sell Permission</span>
            <span className={`text-sm font-semibold mt-0.5 block ${status?.autonomous_sell_enabled ? 'text-emerald-400' : 'text-amber-400'}`}>
              {status?.autonomous_sell_enabled ? 'ENABLED (Pre-authorized)' : 'DISABLED (Manual Fallback)'}
            </span>
          </div>
          <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/50">
            <span className="text-xs text-slate-400 block">Risk Guardian Veto</span>
            <span className="text-sm font-semibold text-indigo-400 font-mono mt-0.5 block flex items-center gap-1">
              <Shield className="w-3.5 h-3.5" /> DETERMINISTIC GATE
            </span>
          </div>
        </div>
      </div>

      {/* Notifications / Alerts */}
      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/50 text-rose-300 rounded-xl flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {actionMessage && (
        <div className="p-4 bg-emerald-950/40 border border-emerald-800/50 text-emerald-300 rounded-xl flex items-center gap-3 text-sm">
          <CheckCircle className="w-5 h-5 flex-shrink-0 text-emerald-400" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* 1. AGENT FLEET MONITOR */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-purple-400" />
            <h2 className="text-base font-semibold text-white">Agent Fleet Status</h2>
          </div>
          <span className="text-xs text-slate-400">8 Logical Coordinated Agents</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { id: 'perception', label: 'Perception Agent', role: 'Data & Feature Extraction', icon: Eye, color: 'text-sky-400' },
            { id: 'reasoning', label: 'Reasoning Agent', role: 'Confluence & Conflict Radar', icon: Brain, color: 'text-purple-400' },
            { id: 'memory', label: 'Memory Agent', role: 'SQLite Historical Recall', icon: History, color: 'text-amber-400' },
            { id: 'learning', label: 'Learning Agent', role: 'Quantitative Performance', icon: TrendingUp, color: 'text-emerald-400' },
            { id: 'planning', label: 'Planning Agent', role: 'Regime Strategy Matching', icon: Layers, color: 'text-indigo-400' },
            { id: 'risk_guardian', label: 'Risk Guardian', role: 'Absolute Veto Gate', icon: Shield, color: 'text-rose-400' },
            { id: 'trade_manager', label: 'Trade Manager', role: 'Position Surveillance & Exit', icon: Zap, color: 'text-teal-400' },
            { id: 'outcome_evaluator', label: 'Outcome Evaluator', role: 'Slippage & Attribution', icon: Activity, color: 'text-orange-400' },
          ].map((agentDef) => {
            const agentMeta = status?.agents?.[agentDef.id];
            const AgentIcon = agentDef.icon;
            const isCompleted = agentMeta?.status === 'COMPLETED' || agentMeta?.status === 'IDLE';

            return (
              <div
                key={agentDef.id}
                className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3 hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AgentIcon className={`w-4 h-4 ${agentDef.color}`} />
                    <span className="text-xs font-semibold text-slate-200">{agentDef.label}</span>
                  </div>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${
                      isCompleted
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}
                  >
                    {agentMeta?.status || 'IDLE'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1">{agentDef.role}</div>
                <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 pt-2 border-t border-slate-900 font-mono">
                  <span>v{agentMeta?.version || '1.0.0'}</span>
                  <span>{agentMeta?.execution_time_ms !== undefined ? `${agentMeta.execution_time_ms.toFixed(1)} ms` : '--'}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. INTERACTIVE MULTI-AGENT CYCLE CONSOLE */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Play className="w-4 h-4 text-emerald-400" />
              Run Multi-Agent Evaluation Cycle
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Dispatches Perception → Reasoning → Memory → Planning → Risk Guardian in strict deterministic order.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Market Select */}
            <select
              value={selectedMarket}
              onChange={(e) => {
                const m = e.target.value as MarketType;
                setSelectedMarket(m);
                setSelectedSymbol(SYMBOLS_BY_MARKET[m][0]);
              }}
              className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-purple-500"
            >
              <option value="FOREX">FOREX</option>
              <option value="NSE">NSE (Indian)</option>
              <option value="MCX">MCX (Commodities)</option>
            </select>

            {/* Symbol Select */}
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-purple-500"
            >
              {SYMBOLS_BY_MARKET[selectedMarket].map((sym) => (
                <option key={sym} value={sym}>
                  {sym}
                </option>
              ))}
            </select>

            {/* Timeframe Select */}
            <select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-purple-500"
            >
              <option value="1m">1m</option>
              <option value="5m">5m</option>
              <option value="15m">15m</option>
              <option value="1h">1h</option>
              <option value="1D">1D</option>
            </select>

            {/* Run Button */}
            <button
              onClick={handleRunCycle}
              disabled={isCycling}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md transition disabled:opacity-50"
            >
              {isCycling ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Running Multi-Agent Cycle...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Evaluate Instrument
                </>
              )}
            </button>
          </div>
        </div>

        {/* 3. CYCLE OUTPUT SYNTHESIS CARDS */}
        {cycleResult ? (
          <div className="mt-5 space-y-4">
            {/* Top Decision Summary */}
            <div
              className={`p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-3 ${
                cycleResult.overall_decision === 'BUY_PROPOSED'
                  ? 'bg-emerald-950/30 border-emerald-800/60'
                  : cycleResult.overall_decision === 'BLOCKED_BY_RISK'
                  ? 'bg-rose-950/30 border-rose-800/60'
                  : 'bg-slate-950/50 border-slate-800'
              }`}
            >
              <div className="flex items-center gap-3">
                {cycleResult.overall_decision === 'BUY_PROPOSED' ? (
                  <CheckCircle className="w-7 h-7 text-emerald-400 flex-shrink-0" />
                ) : cycleResult.overall_decision === 'BLOCKED_BY_RISK' ? (
                  <Shield className="w-7 h-7 text-rose-400 flex-shrink-0" />
                ) : (
                  <XCircle className="w-7 h-7 text-slate-400 flex-shrink-0" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs uppercase font-mono font-bold tracking-wider text-slate-400">
                      Overall Cycle Decision:
                    </span>
                    <span
                      className={`text-sm font-bold font-mono px-2 py-0.5 rounded ${
                        cycleResult.overall_decision === 'BUY_PROPOSED'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : cycleResult.overall_decision === 'BLOCKED_BY_RISK'
                          ? 'bg-rose-500/20 text-rose-300'
                          : 'bg-slate-700/40 text-slate-300'
                      }`}
                    >
                      {cycleResult.overall_decision}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1">
                    {cycleResult.planning.explanation}
                  </p>
                </div>
              </div>

              <div className="text-right flex-shrink-0 text-xs font-mono text-slate-400">
                <div>Cycle ID: {cycleResult.cycle_id}</div>
                <div>{new Date(cycleResult.execution_timestamp).toLocaleTimeString()}</div>
                {cycleResult.cycle_latency_ms !== undefined && (
                  <div className="text-[11px] text-sky-400 font-semibold mt-1">
                    Latency: {cycleResult.cycle_latency_ms}ms | 1 LLM Call ({cycleResult.llm_provider_used || 'DETERMINISTIC'})
                  </div>
                )}
                {cycleResult.token_usage && (
                  <div className="text-[10px] text-slate-400">
                    Tokens: {cycleResult.token_usage.total_tokens} ({cycleResult.token_usage.prompt_tokens} in / {cycleResult.token_usage.completion_tokens} out)
                  </div>
                )}
              </div>
            </div>

            {/* Agent Synthesis Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Perception Output */}
              <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-4">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4 text-sky-400" />
                    <span className="text-xs font-semibold text-slate-200">Perception Agent</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">
                    Freshness: {cycleResult.perception.data_freshness_seconds.toFixed(1)}s
                  </span>
                </div>
                <div className="mt-3 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Classified Regime:</span>
                    <span className="font-semibold text-slate-200">{cycleResult.perception.regime}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Current Price:</span>
                    <span className="font-mono text-emerald-400 font-bold">
                      ${cycleResult.perception.current_price.toFixed(4)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Detected Patterns:</span>
                    <span className="text-slate-300">
                      {cycleResult.perception.detected_patterns.length > 0
                        ? cycleResult.perception.detected_patterns.join(', ')
                        : 'No classical patterns active'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Support / Resistance:</span>
                    <span className="font-mono text-slate-300">
                      S: {cycleResult.perception.support_zones.slice(0, 2).map((v) => v.toFixed(2)).join(', ') || 'None'} | R:{' '}
                      {cycleResult.perception.resistance_zones.slice(0, 2).map((v) => v.toFixed(2)).join(', ') || 'None'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Reasoning & Conflict Radar */}
              <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-4">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-purple-400" />
                    <span className="text-xs font-semibold text-slate-200">Reasoning Agent (Conflict Radar)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-400 font-mono">Uncertainty:</span>
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                        cycleResult.reasoning.uncertainty_score > 0.4
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-emerald-500/20 text-emerald-300'
                      }`}
                    >
                      {(cycleResult.reasoning.uncertainty_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                <div className="mt-3 space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400 block mb-1">Conforming Evidence ({cycleResult.reasoning.conforming_evidence.length}):</span>
                    <div className="space-y-0.5">
                      {cycleResult.reasoning.conforming_evidence.length > 0 ? (
                        cycleResult.reasoning.conforming_evidence.map((ev, i) => (
                          <div key={i} className="text-emerald-400 flex items-center gap-1.5 text-[11px]">
                            <Check className="w-3 h-3 flex-shrink-0" />
                            <span>{ev}</span>
                          </div>
                        ))
                      ) : (
                        <span className="text-slate-500 text-[11px]">No confirming signals</span>
                      )}
                    </div>
                  </div>

                  <div className="pt-1">
                    <span className="text-slate-400 block mb-1">Conflicting / Warning Signals:</span>
                    <div className="space-y-0.5">
                      {cycleResult.reasoning.conflicting_signals.length > 0 ? (
                        cycleResult.reasoning.conflicting_signals.map((sig, i) => (
                          <div key={i} className="text-amber-400 flex items-center gap-1.5 text-[11px]">
                            <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                            <span>{sig}</span>
                          </div>
                        ))
                      ) : (
                        <span className="text-slate-500 text-[11px]">No conflicting signals detected</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Planning Agent Output */}
              <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-4">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-indigo-400" />
                    <span className="text-xs font-semibold text-slate-200">Planning Agent</span>
                  </div>
                  <span className="text-[10px] font-mono text-indigo-300">
                    {cycleResult.planning.strategy_name}
                  </span>
                </div>
                <div className="mt-3 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Plan Decision:</span>
                    <span
                      className={`font-mono font-bold ${
                        cycleResult.planning.decision === 'TRADE_PLAN' ? 'text-emerald-400' : 'text-slate-400'
                      }`}
                    >
                      {cycleResult.planning.decision} ({cycleResult.planning.direction})
                    </span>
                  </div>
                  {cycleResult.planning.decision === 'TRADE_PLAN' && (
                    <>
                      <div className="grid grid-cols-3 gap-2 py-1.5 bg-slate-900/60 rounded px-2 text-center font-mono">
                        <div>
                          <span className="text-[10px] text-slate-400 block">Entry</span>
                          <span className="text-slate-200">${cycleResult.planning.proposed_entry_price?.toFixed(4)}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-rose-400 block">Stop Loss</span>
                          <span className="text-rose-300">${cycleResult.planning.stop_loss?.toFixed(4)}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-emerald-400 block">Target</span>
                          <span className="text-emerald-300">${cycleResult.planning.target?.toFixed(4)}</span>
                        </div>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Risk / Reward Ratio:</span>
                        <span className="font-mono text-slate-200">
                          {cycleResult.planning.risk_reward_ratio?.toFixed(2)} : 1
                        </span>
                      </div>
                    </>
                  )}
                  <div>
                    <span className="text-slate-400 block mb-0.5">Contingency Rules:</span>
                    <div className="text-[11px] text-slate-300 space-y-0.5">
                      {cycleResult.planning.contingency_conditions.map((c, i) => (
                        <div key={i}>• {c}</div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Risk Guardian Independent Gate */}
              <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-4">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-rose-400" />
                    <span className="text-xs font-semibold text-slate-200">Risk Guardian Gate</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                      cycleResult.risk_guardian.verdict === 'PASSED'
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : cycleResult.risk_guardian.verdict === 'REJECTED'
                        ? 'bg-rose-500/20 text-rose-300'
                        : 'bg-slate-700/40 text-slate-400'
                    }`}
                  >
                    VERDICT: {cycleResult.risk_guardian.verdict}
                  </span>
                </div>
                <div className="mt-3 space-y-2 text-xs">
                  <div className="space-y-1">
                    {Object.entries(cycleResult.risk_guardian.checks_summary).map(([chk, passed]) => (
                      <div key={chk} className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-400 capitalize">{chk.replace(/_/g, ' ')}</span>
                        <span className={`font-mono ${passed ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {passed ? '✓ PASSED' : '✗ BLOCKED'}
                        </span>
                      </div>
                    ))}
                  </div>
                  {cycleResult.risk_guardian.blocking_reasons.length > 0 && (
                    <div className="p-2 bg-rose-950/40 border border-rose-900/60 rounded text-[11px] text-rose-300 mt-2">
                      <div className="font-semibold text-rose-200">Blocking Reason(s):</div>
                      {cycleResult.risk_guardian.blocking_reasons.map((r, i) => (
                        <div key={i}>• {r}</div>
                      ))}
                    </div>
                  )}
                  <div className="text-[10px] text-slate-500 italic pt-1">
                    Risk Guardian operates independently with absolute veto authority over all proposed trade plans.
                  </div>
                </div>
              </div>
            </div>

            {/* Memory Agent Context */}
            <div className="bg-slate-950/30 border border-slate-800/60 rounded-xl p-3 text-xs text-slate-400 flex items-start gap-3">
              <History className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-300">Memory Agent Retrieval: </span>
                Found {cycleResult.memory.similar_setups_found} similar historical setups. Regime win rate:{' '}
                {(cycleResult.memory.regime_historical_win_rate * 100).toFixed(1)}%.{' '}
                <span className="text-slate-500 italic">{cycleResult.memory.disclaimer}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="mt-5 p-8 border border-dashed border-slate-800 rounded-xl text-center text-slate-400">
            <Cpu className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            <div className="text-sm font-semibold text-slate-300">Ready to Evaluate</div>
            <div className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              Select an instrument and timeframe above and click "Evaluate Instrument" to initiate the multi-agent decision cycle.
            </div>
          </div>
        )}
      </div>

      {/* 4. QUANTITATIVE LEARNING & CONTINUOUS ADAPTATION METRICS */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            <h2 className="text-base font-semibold text-white">Learning Agent: System-Wide Quantitative Metrics</h2>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {learningSummary?.total_trades_analyzed || 0} Closed Trades Analyzed
          </span>
        </div>

        {learningSummary?.performance_deterioration_detected && (
          <div className="mb-4 p-3 bg-amber-950/40 border border-amber-800/60 text-amber-300 rounded-lg flex items-center gap-2 text-xs">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-400" />
            <span>
              <strong>Performance Decay Warning:</strong>{' '}
              {learningSummary.deterioration_reasons.join('; ')}
            </span>
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/60">
            <span className="text-[11px] text-slate-400 block">Win Rate</span>
            <span className="text-base font-bold font-mono text-emerald-400 mt-0.5 block">
              {((learningSummary?.win_rate || 0) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/60">
            <span className="text-[11px] text-slate-400 block">Profit Factor</span>
            <span className="text-base font-bold font-mono text-slate-200 mt-0.5 block">
              {(learningSummary?.profit_factor || 0).toFixed(2)}
            </span>
          </div>
          <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/60">
            <span className="text-[11px] text-slate-400 block">Expectancy</span>
            <span className="text-base font-bold font-mono text-indigo-400 mt-0.5 block">
              ${(learningSummary?.expectancy || 0).toFixed(2)}
            </span>
          </div>
          <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/60">
            <span className="text-[11px] text-slate-400 block">Max Drawdown</span>
            <span className="text-base font-bold font-mono text-rose-400 mt-0.5 block">
              {(learningSummary?.max_drawdown_pct || 0).toFixed(1)}%
            </span>
          </div>
          <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/60">
            <span className="text-[11px] text-slate-400 block">Avg Slippage</span>
            <span className="text-base font-bold font-mono text-slate-300 mt-0.5 block">
              ${(learningSummary?.average_slippage || 0).toFixed(4)}
            </span>
          </div>
          <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/60">
            <span className="text-[11px] text-slate-400 block">Candidate Strategies</span>
            <span className="text-base font-bold font-mono text-purple-400 mt-0.5 block">
              {learningSummary?.candidate_strategy_count || candidates.length}
            </span>
          </div>
        </div>
      </div>

      {/* 5. CONTROLLED STRATEGY ADAPTATION LIFECYCLE */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-3 border-b border-slate-800">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-indigo-400" />
              Controlled Strategy Adaptation Lifecycle
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Candidate → Sandbox → Backtest → Out-of-Sample → Review → Explicit User Activation.
              Strategies cannot alter live execution parameters autonomously.
            </p>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow transition"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            New Candidate
          </button>
        </div>

        {/* Candidate List Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 font-mono uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Candidate ID</th>
                <th className="py-2.5 px-3">Strategy Name</th>
                <th className="py-2.5 px-3">Market / Timeframe</th>
                <th className="py-2.5 px-3">Lifecycle Stage</th>
                <th className="py-2.5 px-3">Rationale</th>
                <th className="py-2.5 px-3">Validation Metrics</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {candidates.length > 0 ? (
                candidates.map((cand) => (
                  <tr key={cand.id} className="hover:bg-slate-950/30 transition">
                    <td className="py-3 px-3 font-mono font-semibold text-purple-400">
                      {cand.candidate_id}
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-200">{cand.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{cand.version}</div>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">
                      {cand.market} / {cand.timeframe}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          cand.lifecycle_stage === 'ACTIVATED'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : cand.lifecycle_stage === 'REVIEW'
                            ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                            : 'bg-slate-800 text-slate-300 border border-slate-700'
                        }`}
                      >
                        {cand.lifecycle_stage}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-300 max-w-xs truncate" title={cand.rationale}>
                      {cand.rationale}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-400">
                      {cand.validation_metrics && Object.keys(cand.validation_metrics).length > 0 ? (
                        <span>
                          WR: {((cand.validation_metrics.win_rate || 0) * 100).toFixed(0)}% | PF:{' '}
                          {(cand.validation_metrics.profit_factor || 0).toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-slate-600">Pending Run</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {cand.lifecycle_stage !== 'ACTIVATED' && cand.lifecycle_stage !== 'ARCHIVED' && (
                          <div className="flex items-center gap-1">
                            {/* Advance stage dropdown */}
                            <select
                              value={cand.lifecycle_stage}
                              onChange={(e) => handleAdvanceCandidate(cand.id, e.target.value as LifecycleStage)}
                              className="bg-slate-950 border border-slate-700 text-slate-300 text-[11px] rounded px-2 py-1 font-mono focus:outline-none"
                            >
                              {LIFECYCLE_STAGES.map((stg) => (
                                <option key={stg} value={stg}>
                                  {stg}
                                </option>
                              ))}
                            </select>

                            {/* Direct Activate Button (Only in REVIEW or later) */}
                            {cand.lifecycle_stage === 'REVIEW' && (
                              <button
                                onClick={() => handleActivateCandidate(cand.id)}
                                className="px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-semibold transition"
                                title="Explicitly activate strategy"
                              >
                                Activate
                              </button>
                            )}
                          </div>
                        )}
                        {cand.lifecycle_stage === 'ACTIVATED' && (
                          <span className="text-emerald-400 text-[11px] font-mono font-bold flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" /> LIVE
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-500 text-xs">
                    No candidate strategies registered. Click "New Candidate" to initiate a controlled adaptation lifecycle.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CREATE CANDIDATE MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 w-full max-w-lg shadow-2xl relative">
            <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              <PlusCircle className="w-5 h-5 text-indigo-400" />
              Register Strategy Candidate
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Candidates start in CANDIDATE / SANDBOX and undergo backtesting before explicit activation.
            </p>

            <form onSubmit={handleCreateCandidate} className="space-y-4 text-xs">
              <div>
                <label className="text-slate-300 font-semibold block mb-1">Candidate Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Adaptive EMA Trend-Rider"
                  value={newCandidate.name}
                  onChange={(e) => setNewCandidate({ ...newCandidate, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Version</label>
                  <input
                    type="text"
                    value={newCandidate.version}
                    onChange={(e) => setNewCandidate({ ...newCandidate, version: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Market</label>
                  <select
                    value={newCandidate.market}
                    onChange={(e) => setNewCandidate({ ...newCandidate, market: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                  >
                    <option value="FOREX">FOREX</option>
                    <option value="NSE">NSE</option>
                    <option value="MCX">MCX</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Timeframe</label>
                  <select
                    value={newCandidate.timeframe}
                    onChange={(e) => setNewCandidate({ ...newCandidate, timeframe: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                  >
                    <option value="1m">1m</option>
                    <option value="5m">5m</option>
                    <option value="15m">15m</option>
                    <option value="1h">1h</option>
                    <option value="1D">1D</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Rationale / Adaptation Hypothesis *</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Explain why this parameter adjustment or logic should outperform..."
                  value={newCandidate.rationale}
                  onChange={(e) => setNewCandidate({ ...newCandidate, rationale: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                ></textarea>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Parameters (JSON)</label>
                <textarea
                  rows={4}
                  value={newCandidate.parameters_json}
                  onChange={(e) => setNewCandidate({ ...newCandidate, parameters_json: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 font-mono text-[11px] focus:outline-none focus:border-indigo-500"
                ></textarea>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow transition"
                >
                  Create in Sandbox
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
