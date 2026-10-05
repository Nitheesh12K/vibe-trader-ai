import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Plus,
  Trash2,
  Edit2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Layers,
  Code2,
} from 'lucide-react';
import { api } from '../../services/api';
import { StrategyItem, StrategyCreate } from '../../types/market';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';

export const StrategiesView: React.FC = () => {
  const [strategies, setStrategies] = useState<StrategyItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [marketFilter, setMarketFilter] = useState<string>('ALL');
  const [showModal, setShowModal] = useState<boolean>(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Form state
  const [name, setName] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [market, setMarket] = useState<string>('ALL');
  const [timeframe, setTimeframe] = useState<string>('1D');
  const [parametersJson, setParametersJson] = useState<string>('{\n  "fast_period": 14,\n  "slow_period": 28\n}');
  const [isActive, setIsActive] = useState<boolean>(true);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  useEffect(() => {
    loadStrategies();
  }, [marketFilter]);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const res = await api.getStrategies(marketFilter);
      setStrategies(res.items);
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to load strategies', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingId(null);
    setName('');
    setDescription('');
    setMarket('ALL');
    setTimeframe('1D');
    setParametersJson('{\n  "fast_period": 14,\n  "slow_period": 28\n}');
    setIsActive(true);
    setJsonError(null);
    setShowModal(true);
  };

  const handleOpenEdit = (strat: StrategyItem) => {
    setEditingId(strat.id);
    setName(strat.name);
    setDescription(strat.description || '');
    setMarket(strat.market);
    setTimeframe(strat.timeframe);
    try {
      // Pretty-format JSON
      const parsed = JSON.parse(strat.parameters_json);
      setParametersJson(JSON.stringify(parsed, null, 2));
    } catch {
      setParametersJson(strat.parameters_json);
    }
    setIsActive(strat.is_active);
    setJsonError(null);
    setShowModal(true);
  };

  const handleToggleStatus = async (strat: StrategyItem) => {
    try {
      const updated = await api.updateStrategy(strat.id, { is_active: !strat.is_active });
      setStrategies((prev) => prev.map((s) => (s.id === strat.id ? updated : s)));
      setMessage({
        text: `Strategy '${strat.name}' is now ${updated.is_active ? 'Enabled' : 'Disabled'}.`,
        type: 'success',
      });
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to update strategy status', type: 'error' });
    }
  };

  const handleDelete = async (id: number, stratName: string) => {
    if (!window.confirm(`Are you sure you want to delete the strategy '${stratName}'?`)) {
      return;
    }
    try {
      await api.deleteStrategy(id);
      setStrategies((prev) => prev.filter((s) => s.id !== id));
      setMessage({ text: `Strategy '${stratName}' deleted successfully.`, type: 'success' });
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to delete strategy', type: 'error' });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setJsonError(null);

    // Validate JSON
    try {
      const parsed = JSON.parse(parametersJson);
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        setJsonError('Parameters must be a JSON object: {"key": value}');
        return;
      }
    } catch (err: any) {
      setJsonError(`Invalid JSON format: ${err.message}`);
      return;
    }

    try {
      setSubmitting(true);
      if (editingId) {
        const updated = await api.updateStrategy(editingId, {
          name,
          description: description || undefined,
          market,
          timeframe,
          parameters_json: parametersJson,
          is_active: isActive,
        });
        setStrategies((prev) => prev.map((s) => (s.id === editingId ? updated : s)));
        setMessage({ text: `Strategy '${name}' updated successfully.`, type: 'success' });
      } else {
        const created = await api.createStrategy({
          name,
          description: description || undefined,
          market,
          timeframe,
          parameters_json: parametersJson,
          is_active: isActive,
        });
        setStrategies((prev) => [created, ...prev]);
        setMessage({ text: `Strategy '${name}' created successfully.`, type: 'success' });
      }
      setShowModal(false);
    } catch (err: any) {
      setJsonError(err.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-panel border border-border rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg shadow-black/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100 font-mono">Strategy Engine</h2>
            <p className="text-xs text-slate-400">Configure, validate, and manage rule-based analytical strategies.</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Market filter */}
          <div className="flex items-center gap-1 bg-background p-1 rounded-md border border-border">
            {(['ALL', 'FOREX', 'NSE', 'MCX'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setMarketFilter(tab)}
                className={`px-3 py-1 text-xs font-mono font-medium rounded transition-colors ${
                  marketFilter === tab
                    ? 'bg-accent/15 text-accent border border-accent/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <button
            onClick={handleOpenCreate}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-accent hover:bg-sky-400 text-slate-950 text-xs font-bold font-mono transition-colors shadow-lg shadow-accent/10"
          >
            <Plus className="w-4 h-4" />
            New Strategy
          </button>
        </div>
      </div>

      {/* Message Banner */}
      {message && (
        <div
          className={`p-3.5 rounded-lg border text-xs flex items-center justify-between gap-2.5 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {message.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{message.text}</span>
          </div>
          <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-slate-200">
            &times;
          </button>
        </div>
      )}

      {/* Strategies Grid */}
      {loading ? (
        <LoadingSpinner label="Loading strategies from database..." />
      ) : strategies.length === 0 ? (
        <div className="bg-panel border border-border rounded-lg p-12 text-center text-slate-400">
          <Cpu className="w-10 h-10 mx-auto mb-3 text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-300 font-mono">No Strategies Found</h3>
          <p className="text-xs text-slate-400 mt-1 mb-4">No strategies match the selected filter.</p>
          <button
            onClick={handleOpenCreate}
            className="px-4 py-1.5 rounded bg-accent/10 hover:bg-accent/20 border border-accent/30 text-accent text-xs font-mono font-medium"
          >
            Create Your First Strategy
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {strategies.map((strat) => (
            <div
              key={strat.id}
              className="bg-panel border border-border rounded-lg p-5 flex flex-col justify-between shadow-lg shadow-black/20 hover:border-border-strong transition-all"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-mono text-sm font-bold text-slate-100">{strat.name}</h3>
                  <button
                    onClick={() => handleToggleStatus(strat)}
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold cursor-pointer transition-colors ${
                      strat.is_active
                        ? 'bg-bullish-bg/40 text-bullish border-bullish/30'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    {strat.is_active ? 'ENABLED' : 'DISABLED'}
                  </button>
                </div>

                <div className="flex items-center gap-2 mb-3 text-[11px] font-mono text-slate-400">
                  <span className="px-1.5 py-0.5 rounded bg-background border border-border">
                    {strat.market}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-background border border-border">
                    {strat.timeframe}
                  </span>
                  <span>ID: #{strat.id}</span>
                </div>

                {strat.description && (
                  <p className="text-xs text-slate-300/80 mb-4 line-clamp-2 leading-relaxed">
                    {strat.description}
                  </p>
                )}

                {/* Parameters Preview */}
                <div className="bg-background rounded p-2.5 border border-border/80 mb-4 font-mono text-[11px] text-slate-400 overflow-x-auto">
                  <div className="text-[10px] uppercase text-slate-400 mb-1 flex items-center gap-1 font-semibold">
                    <Code2 className="w-3 h-3 text-accent" />
                    Parameters
                  </div>
                  <pre className="text-slate-300 text-[10px]">
                    {strat.parameters_json}
                  </pre>
                </div>
              </div>

              {/* Card Footer Controls */}
              <div className="pt-3 border-t border-border flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-400">
                  {new Date(strat.updated_at).toLocaleDateString()}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleOpenEdit(strat)}
                    className="p-1 rounded bg-panel-subtle hover:bg-border text-slate-300 hover:text-white transition-colors border border-border"
                    title="Edit Strategy"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(strat.id, strat.name)}
                    className="p-1 rounded bg-panel-subtle hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 transition-colors border border-border"
                    title="Delete Strategy"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Dialog for Create/Edit */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-border rounded-lg max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="font-mono text-sm font-bold text-slate-100">
                {editingId ? 'Edit Strategy' : 'Create New Strategy'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            {jsonError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded text-xs">
                {jsonError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-300 mb-1">Strategy Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. RSI 14 Mean Reversion"
                  className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100 focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Description (Optional)</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Strategy thesis and execution rules..."
                  className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100 focus:outline-none focus:border-accent resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1">Target Market</label>
                  <select
                    value={market}
                    onChange={(e) => setMarket(e.target.value)}
                    className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100 focus:outline-none focus:border-accent"
                  >
                    <option value="ALL">ALL Markets</option>
                    <option value="FOREX">FOREX</option>
                    <option value="NSE">NSE</option>
                    <option value="MCX">MCX</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Timeframe</label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100 focus:outline-none focus:border-accent"
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
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-300">Configuration Parameters (JSON)</label>
                  <span className="text-[10px] text-slate-400">Valid JSON Object</span>
                </div>
                <textarea
                  rows={4}
                  required
                  value={parametersJson}
                  onChange={(e) => setParametersJson(e.target.value)}
                  className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100 focus:outline-none focus:border-accent font-mono text-xs"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="rounded bg-background border-border text-accent focus:ring-0"
                  />
                  <span className="text-slate-300">Enable Strategy Immediately</span>
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3.5 py-1.5 rounded border border-border text-slate-300 hover:bg-panel-subtle text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 rounded bg-accent hover:bg-sky-400 text-slate-950 font-bold text-xs disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : editingId ? 'Update Strategy' : 'Create Strategy'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
