import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Layers,
  Play,
  CheckCircle2,
  AlertTriangle,
  Info,
  Sliders,
  RefreshCw,
  Plus,
  Trash2,
  Edit2,
  Shield,
  ArrowRight,
  TrendingUp,
  Activity,
  XCircle,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  StrategyDefinition,
  StrategySignalOutput,
  StrategyItem,
  StrategyCreate,
  MarketType,
} from '../../types/market';
import { LoadingSpinner } from '../common/LoadingSpinner';

export const StrategyLabView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'catalogue' | 'custom'>('catalogue');
  const [catalogue, setCatalogue] = useState<StrategyDefinition[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyDefinition | null>(null);
  const [evalSymbol, setEvalSymbol] = useState<string>('RELIANCE');
  const [evalTimeframe, setEvalTimeframe] = useState<string>('1D');
  const [signalResult, setSignalResult] = useState<StrategySignalOutput | null>(null);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Custom strategies state
  const [customStrategies, setCustomStrategies] = useState<StrategyItem[]>([]);
  const [customLoading, setCustomLoading] = useState<boolean>(false);
  const [showModal, setShowModal] = useState<boolean>(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [customName, setCustomName] = useState<string>('');
  const [customDesc, setCustomDesc] = useState<string>('');
  const [customMarket, setCustomMarket] = useState<string>('ALL');
  const [customTf, setCustomTf] = useState<string>('1D');
  const [customParamsJson, setCustomParamsJson] = useState<string>('{\n  "fast_period": 14,\n  "slow_period": 28\n}');
  const [customActive, setCustomActive] = useState<boolean>(true);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const fetchCatalogue = async () => {
    try {
      setLoading(true);
      const res = await api.getStrategyCatalogue();
      setCatalogue(res.strategies);
      if (res.strategies.length > 0 && !selectedStrategy) {
        setSelectedStrategy(res.strategies[0]);
      }
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to fetch strategy catalogue', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomStrategies = async () => {
    try {
      setCustomLoading(true);
      const res = await api.getStrategies('ALL');
      setCustomStrategies(res.items);
    } catch (err: any) {
      console.warn('Failed to load custom strategies:', err);
    } finally {
      setCustomLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalogue();
    fetchCustomStrategies();
  }, []);

  const handleEvaluate = async () => {
    if (!selectedStrategy) return;
    try {
      setEvaluating(true);
      setMessage(null);
      setSignalResult(null);

      const res = await api.evaluateStrategySignal(selectedStrategy.strategy_code, {
        symbol: evalSymbol,
        timeframe: evalTimeframe,
      });
      setSignalResult(res);
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to evaluate strategy signal', type: 'error' });
    } finally {
      setEvaluating(false);
    }
  };

  // Custom strategy save
  const handleSaveCustomStrategy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      JSON.parse(customParamsJson);
    } catch {
      setJsonError('Invalid JSON format for parameters');
      return;
    }

    try {
      if (editingId) {
        await api.updateStrategy(editingId, {
          name: customName,
          description: customDesc,
          market: customMarket,
          timeframe: customTf,
          parameters_json: customParamsJson,
          is_active: customActive,
        });
      } else {
        await api.createStrategy({
          name: customName,
          description: customDesc,
          market: customMarket,
          timeframe: customTf,
          parameters_json: customParamsJson,
          is_active: customActive,
        });
      }
      setShowModal(false);
      fetchCustomStrategies();
      setMessage({ text: 'Strategy saved successfully', type: 'success' });
    } catch (err: any) {
      setMessage({ text: err.message || 'Error saving strategy', type: 'error' });
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] p-6 rounded-2xl shadow-xl shadow-black/40 relative overflow-hidden">
        <div className="absolute top-0 right-1/4 w-96 h-32 bg-cyan-500/[0.03] rounded-full blur-3xl pointer-events-none" />
        <div className="flex items-center gap-4 relative z-10">
          <div className="p-3 bg-gradient-to-br from-cyan-500/15 to-blue-600/15 border border-cyan-500/30 rounded-xl text-cyan-400 shadow-md shadow-cyan-500/10">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-xl font-bold text-white tracking-tight">
                Strategy Lab & Algorithmic Engine
              </h1>
              <span className="text-[10px] bg-cyan-500/10 text-cyan-300 font-mono px-2.5 py-0.5 rounded-full border border-cyan-500/30 font-semibold tracking-wide">
                7 PRE-CONFIGURED STRATEGIES
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Deterministic rule-based signal generation, parameter testing, and custom strategy lifecycle management.
            </p>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center gap-1.5 bg-white/[0.03] p-1.5 rounded-xl border border-white/[0.06] text-xs relative z-10">
          <button
            onClick={() => setActiveTab('catalogue')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'catalogue'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/20 font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Pre-configured Catalogue ({catalogue.length})
          </button>
          <button
            onClick={() => setActiveTab('custom')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'custom'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/20 font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Custom User Strategies ({customStrategies.length})
          </button>
        </div>
      </div>

      {message && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between shadow-md ${
            message.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}
        >
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-white">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tab 1: Catalogue & Signal Evaluator */}
      {activeTab === 'catalogue' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Strategy List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
                Select Strategy
              </span>
              <span className="text-[10px] text-slate-500 font-mono">{catalogue.length} Models Available</span>
            </div>

            {loading ? (
              <div className="p-8 flex justify-center">
                <LoadingSpinner size="md" />
              </div>
            ) : (
              <div className="space-y-2.5">
                {catalogue.map((strat) => {
                  const isSelected = selectedStrategy?.strategy_code === strat.strategy_code;
                  return (
                    <div
                      key={strat.strategy_code}
                      onClick={() => {
                        setSelectedStrategy(strat);
                        setSignalResult(null);
                      }}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-gradient-to-r from-cyan-500/15 via-cyan-500/5 to-transparent border-cyan-500/60 text-white shadow-lg shadow-cyan-500/10'
                          : 'bg-[#0B101E]/60 border-white/[0.06] text-slate-300 hover:bg-white/[0.02] hover:border-white/[0.14]'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                          {strat.strategy_code}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 uppercase font-semibold">
                          {strat.lifecycle_status}
                        </span>
                      </div>
                      <h3 className="font-bold text-sm text-white mb-1">{strat.name}</h3>
                      <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{strat.description}</p>
                      <div className="mt-3 flex items-center gap-1.5 flex-wrap">
                        {strat.indicators_used.map((ind) => (
                          <span
                            key={ind}
                            className="text-[9px] font-mono px-2 py-0.5 bg-white/[0.04] text-slate-300 rounded-md border border-white/[0.06]"
                          >
                            {ind}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Strategy Details & Interactive Evaluation */}
          <div className="lg:col-span-2 space-y-6">
            {selectedStrategy ? (
              <>
                {/* Details Card */}
                <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 space-y-5 shadow-xl shadow-black/40">
                  <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
                    <div>
                      <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold tracking-wider">
                        {selectedStrategy.family} Family
                      </span>
                      <h2 className="text-base font-bold text-white">{selectedStrategy.name}</h2>
                    </div>
                    <span className="font-mono text-xs text-slate-300 bg-white/[0.04] px-3 py-1 rounded-full border border-white/[0.08]">
                      Code: {selectedStrategy.strategy_code}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">{selectedStrategy.description}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-1">
                    <div className="bg-[#0B101E]/60 p-4 rounded-xl border border-white/[0.06] space-y-1.5 hover:border-white/[0.12] transition-colors">
                      <span className="font-bold text-emerald-400 flex items-center gap-2">
                        <span className="p-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <TrendingUp className="w-3.5 h-3.5" />
                        </span>
                        Entry Rule Logic
                      </span>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {selectedStrategy.entry_rule_summary}
                      </p>
                    </div>

                    <div className="bg-[#0B101E]/60 p-4 rounded-xl border border-white/[0.06] space-y-1.5 hover:border-white/[0.12] transition-colors">
                      <span className="font-bold text-rose-400 flex items-center gap-2">
                        <span className="p-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          <Shield className="w-3.5 h-3.5" />
                        </span>
                        Exit & Risk Rules
                      </span>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {selectedStrategy.exit_rule_summary}
                      </p>
                    </div>
                  </div>

                  {/* Active Strategy Parameters */}
                  <div className="space-y-2 pt-1">
                    <span className="text-xs font-semibold text-slate-300 flex items-center gap-2">
                      <Sliders className="w-3.5 h-3.5 text-cyan-400" /> Configured Parameters
                    </span>
                    <div className="bg-[#070A12]/80 p-3.5 rounded-xl border border-white/[0.06] font-mono text-xs text-cyan-300 shadow-inner">
                      <pre className="overflow-x-auto text-[11px]">
                        {JSON.stringify(selectedStrategy.parameters, null, 2)}
                      </pre>
                    </div>
                  </div>

                  {/* Live Signal Evaluation Controls */}
                  <div className="border-t border-white/[0.06] pt-4 space-y-3">
                    <span className="text-xs font-bold text-white uppercase tracking-wider font-mono block">
                      Live Signal Evaluation
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="text-[11px] text-slate-400 block mb-1">Symbol</label>
                        <select
                          value={evalSymbol}
                          onChange={(e) => setEvalSymbol(e.target.value)}
                          className="w-full bg-[#070A12]/80 border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/60 font-mono shadow-inner"
                        >
                          <option value="RELIANCE">RELIANCE (NSE)</option>
                          <option value="TCS">TCS (NSE)</option>
                          <option value="INFY">INFY (NSE)</option>
                          <option value="HDFCBANK">HDFCBANK (NSE)</option>
                          <option value="EUR/USD">EUR/USD (Forex)</option>
                          <option value="GBP/USD">GBP/USD (Forex)</option>
                          <option value="GOLD">GOLD (MCX)</option>
                          <option value="CRUDEOIL">CRUDEOIL (MCX)</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-[11px] text-slate-400 block mb-1">Timeframe</label>
                        <select
                          value={evalTimeframe}
                          onChange={(e) => setEvalTimeframe(e.target.value)}
                          className="w-full bg-[#070A12]/80 border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/60 font-mono shadow-inner"
                        >
                          <option value="1D">1D (Daily)</option>
                          <option value="4H">4H (4 Hours)</option>
                          <option value="1H">1H (Hourly)</option>
                          <option value="15m">15m (15 Minutes)</option>
                        </select>
                      </div>

                      <div className="flex items-end">
                        <button
                          onClick={handleEvaluate}
                          disabled={evaluating}
                          className="w-full py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all shadow-md shadow-cyan-500/20"
                        >
                          {evaluating ? (
                            <>
                              <LoadingSpinner size="sm" />
                              <span>Evaluating...</span>
                            </>
                          ) : (
                            <>
                              <Play className="w-3.5 h-3.5" />
                              <span>Evaluate Signal</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Signal Output Result */}
                {signalResult && (
                  <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 space-y-5 shadow-2xl shadow-black/50">
                    <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                          <Activity className="w-4 h-4" />
                        </div>
                        <h3 className="font-bold text-sm text-white">Evaluated Signal Output</h3>
                      </div>
                      <span
                        className={`text-xs font-mono px-3.5 py-1 rounded-full font-bold uppercase tracking-wider shadow-sm ${
                          signalResult.signal_state === 'BUY_CANDIDATE'
                            ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/35 shadow-emerald-500/10'
                            : signalResult.signal_state === 'SELL_CANDIDATE'
                            ? 'bg-rose-500/15 text-rose-300 border border-rose-500/35 shadow-rose-500/10'
                            : signalResult.signal_state === 'HOLD'
                            ? 'bg-amber-500/15 text-amber-300 border border-amber-500/35 shadow-amber-500/10'
                            : 'bg-white/[0.04] text-slate-400 border border-white/[0.08]'
                        }`}
                      >
                        {signalResult.signal_state}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5 text-xs">
                      <div className="bg-[#0B101E]/60 p-3 rounded-xl border border-white/[0.06]">
                        <span className="text-[10px] text-slate-400 block mb-0.5">Trigger Price</span>
                        <span className="font-mono text-white font-bold text-sm">
                          ₹{signalResult.trigger_price.toFixed(2)}
                        </span>
                      </div>
                      <div className="bg-[#0B101E]/60 p-3 rounded-xl border border-white/[0.06]">
                        <span className="text-[10px] text-slate-400 block mb-0.5">Confidence</span>
                        <span className="font-mono text-cyan-400 font-bold text-sm">
                          {(signalResult.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="bg-[#0B101E]/60 p-3 rounded-xl border border-white/[0.06]">
                        <span className="text-[10px] text-slate-400 block mb-0.5">Stop Loss</span>
                        <span className="font-mono text-rose-400 font-bold text-sm">
                          {signalResult.stop_loss_level ? `₹${signalResult.stop_loss_level.toFixed(2)}` : 'N/A'}
                        </span>
                      </div>
                      <div className="bg-[#0B101E]/60 p-3 rounded-xl border border-white/[0.06]">
                        <span className="text-[10px] text-slate-400 block mb-0.5">Target / R:R</span>
                        <span className="font-mono text-emerald-400 font-bold text-sm">
                          {signalResult.target_level
                            ? `₹${signalResult.target_level.toFixed(2)} (${signalResult.risk_reward_ratio || '1.5'}:1)`
                            : 'N/A'}
                        </span>
                      </div>
                    </div>

                    {/* Reasons & Caveats */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="space-y-2">
                        <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Confluence Evidence:
                        </span>
                        <ul className="space-y-1.5 bg-[#0B101E]/60 p-4 rounded-xl border border-white/[0.06] text-[11px] text-slate-300">
                          {signalResult.reasons.map((r, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-emerald-400 font-bold">•</span>
                              <span className="leading-relaxed">{r}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="space-y-2">
                        <span className="font-semibold text-amber-400 flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5" /> Risk Caveats:
                        </span>
                        <ul className="space-y-1.5 bg-[#0B101E]/60 p-4 rounded-xl border border-white/[0.06] text-[11px] text-slate-300">
                          {signalResult.caveats.map((c, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-amber-400 font-bold">•</span>
                              <span className="leading-relaxed">{c}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="p-8 text-center text-slate-500">Select a strategy from the left panel to inspect details.</div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Custom User Strategies */}
      {activeTab === 'custom' && (
        <div className="bg-panel border border-border rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div>
              <h2 className="text-sm font-bold text-white">Custom User Strategies Registry</h2>
              <p className="text-xs text-slate-400">Manage user-defined JSON-parameterized strategies in SQLite.</p>
            </div>
            <button
              onClick={() => {
                setEditingId(null);
                setCustomName('');
                setCustomDesc('');
                setCustomMarket('ALL');
                setCustomTf('1D');
                setCustomParamsJson('{\n  "fast_period": 14,\n  "slow_period": 28\n}');
                setShowModal(true);
              }}
              className="px-3 py-1.5 bg-accent hover:bg-accent-hover text-white rounded text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              New Custom Strategy
            </button>
          </div>

          {customLoading ? (
            <div className="py-8 flex justify-center">
              <LoadingSpinner size="md" />
            </div>
          ) : customStrategies.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-6">No custom strategies created yet.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {customStrategies.map((item) => (
                <div key={item.id} className="p-4 bg-panel-subtle border border-border rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-white">{item.name}</span>
                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded uppercase font-bold ${
                        item.is_active
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}
                    >
                      {item.is_active ? 'ACTIVE' : 'DISABLED'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{item.description || 'No description'}</p>
                  <div className="text-[10px] font-mono text-slate-400 flex items-center gap-2">
                    <span>{item.market}</span>
                    <span>•</span>
                    <span>{item.timeframe}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Modal for creating custom strategy */}
          {showModal && (
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
              <div className="bg-panel border border-border rounded-xl p-5 max-w-md w-full space-y-4">
                <h3 className="font-bold text-sm text-white">Create Custom Strategy</h3>
                <form onSubmit={handleSaveCustomStrategy} className="space-y-3 text-xs">
                  <div>
                    <label className="text-slate-300 block mb-1">Name</label>
                    <input
                      type="text"
                      required
                      value={customName}
                      onChange={(e) => setCustomName(e.target.value)}
                      className="w-full bg-panel-subtle border border-border rounded px-3 py-1.5 text-white"
                    />
                  </div>
                  <div>
                    <label className="text-slate-300 block mb-1">Description</label>
                    <textarea
                      value={customDesc}
                      onChange={(e) => setCustomDesc(e.target.value)}
                      className="w-full bg-panel-subtle border border-border rounded px-3 py-1.5 text-white"
                      rows={2}
                    />
                  </div>
                  <div>
                    <label className="text-slate-300 block mb-1">Parameters (JSON)</label>
                    <textarea
                      value={customParamsJson}
                      onChange={(e) => {
                        setCustomParamsJson(e.target.value);
                        setJsonError(null);
                      }}
                      className="w-full bg-panel-subtle border border-border rounded px-3 py-1.5 font-mono text-slate-200"
                      rows={4}
                    />
                    {jsonError && <span className="text-rose-400 text-[10px] block mt-1">{jsonError}</span>}
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowModal(false)}
                      className="px-3 py-1.5 rounded bg-slate-800 text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button type="submit" className="px-3 py-1.5 rounded bg-accent text-white font-semibold">
                      Save Strategy
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
