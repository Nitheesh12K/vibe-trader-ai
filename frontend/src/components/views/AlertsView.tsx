import React, { useState, useEffect } from 'react';
import {
  Bell,
  BellRing,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldCheck,
  RefreshCw,
  Power,
  X,
  Filter,
} from 'lucide-react';
import { api } from '../../services/api';
import { AlertRuleItem, AlertEventItem, NavTabId } from '../../types/market';

interface AlertsViewProps {
  onNavigate?: (tab: NavTabId, symbol?: string) => void;
}

export const AlertsView: React.FC<AlertsViewProps> = ({ onNavigate }) => {
  const [rules, setRules] = useState<AlertRuleItem[]>([]);
  const [events, setEvents] = useState<AlertEventItem[]>([]);
  const [filterUnread, setFilterUnread] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Create rule modal state
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [symbol, setSymbol] = useState<string>('RELIANCE');
  const [market, setMarket] = useState<string>('NSE');
  const [alertType, setAlertType] = useState<string>('PRICE_ABOVE');
  const [threshold, setThreshold] = useState<string>('3000.00');
  const [condition, setCondition] = useState<string>('>=');
  const [cooldown, setCooldown] = useState<number>(60);
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [rulesList, eventsList] = await Promise.all([
        api.getAlertRules(),
        api.getAlertEvents(filterUnread),
      ]);
      setRules(rulesList);
      setEvents(eventsList);
    } catch (err: any) {
      setError(err.message || 'Failed to load alert rules.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filterUnread]);

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      setError(null);
      await api.createAlertRule({
        symbol: symbol.trim().toUpperCase(),
        market,
        alert_type: alertType,
        condition,
        threshold: threshold ? parseFloat(threshold) : undefined,
        cooldown_seconds: cooldown,
        notes: notes.trim() || undefined,
      });
      setShowCreateModal(false);
      await fetchData();
    } catch (err: any) {
      setError(err.message || 'Failed to create alert rule.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggle = async (ruleId: string) => {
    try {
      await api.toggleAlertRule(ruleId);
      setRules((prev) =>
        prev.map((r) => (r.alert_id === ruleId ? { ...r, is_enabled: !r.is_enabled } : r))
      );
    } catch (err: any) {
      setError('Failed to toggle rule state.');
    }
  };

  const handleDelete = async (ruleId: string) => {
    if (!window.confirm('Delete this alert rule?')) return;
    try {
      await api.deleteAlertRule(ruleId);
      setRules((prev) => prev.filter((r) => r.alert_id !== ruleId));
    } catch (err: any) {
      setError('Failed to delete alert rule.');
    }
  };

  const handleEvaluateNow = async () => {
    try {
      setIsEvaluating(true);
      setError(null);
      const triggered = await api.checkAlerts();
      await fetchData();
      if (triggered.length === 0) {
        alert('Check completed: No rules met trigger conditions or rules are in cooldown.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to evaluate rules.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleMarkRead = async (eventId: string) => {
    try {
      await api.markAlertEventRead(eventId);
      setEvents((prev) =>
        prev.map((ev) => (ev.event_id === eventId ? { ...ev, is_read: true } : ev))
      );
    } catch (err) {
      // Ignored
    }
  };

  const handleClearEvents = async () => {
    if (!window.confirm('Clear all triggered notification events?')) return;
    try {
      await api.clearAlertEvents();
      setEvents([]);
    } catch (err: any) {
      setError('Failed to clear events.');
    }
  };

  const unreadCount = events.filter((e) => !e.is_read).length;

  return (
    <div className="space-y-6">
      {/* Safety Shield Header Banner */}
      <div className="p-4 rounded-2xl bg-cyan-950/40 border border-cyan-500/20 backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              Autonomous Notification Shield
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                ZERO TRADE SIDE-EFFECTS
              </span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Alert conditions monitor market price thresholds, RSI bounds, and risk state. They create informational in-app notifications and <span className="text-slate-200 font-semibold">NEVER</span> trigger live broker executions.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleEvaluateNow}
            disabled={isEvaluating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-white/10 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isEvaluating ? 'animate-spin text-cyan-400' : ''}`} />
            Evaluate Rules Now
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-bold shadow-md shadow-cyan-500/25 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            New Alert Rule
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Rules (Left) and Notification Center (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Configured Rules (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Bell className="w-4 h-4 text-cyan-400" />
              Configured Alert Rules ({rules.length})
            </h2>
            <span className="text-xs font-mono text-slate-500">
              Active: {rules.filter((r) => r.is_enabled).length}
            </span>
          </div>

          <div className="space-y-2.5">
            {isLoading && rules.length === 0 ? (
              <div className="p-8 text-center text-slate-500 bg-slate-900/40 rounded-2xl border border-white/5">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-cyan-400" />
                Loading rules...
              </div>
            ) : rules.length === 0 ? (
              <div className="p-8 text-center text-slate-500 bg-slate-900/40 rounded-2xl border border-white/5 text-xs">
                No alert rules configured. Click "New Alert Rule" to monitor price levels or indicator bounds.
              </div>
            ) : (
              rules.map((rule) => (
                <div
                  key={rule.id}
                  className={`p-4 rounded-2xl border transition flex items-center justify-between gap-4 ${
                    rule.is_enabled
                      ? 'bg-slate-900/70 border-white/10 shadow-lg'
                      : 'bg-slate-950/40 border-white/5 opacity-60'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-white text-sm">{rule.symbol}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {rule.market}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {rule.alert_type}
                      </span>
                    </div>

                    <div className="text-xs text-slate-300 font-mono">
                      Condition: <span className="text-cyan-400 font-bold">{rule.condition}</span>{' '}
                      {rule.threshold !== null && rule.threshold !== undefined && (
                        <span>
                          {rule.market === 'FOREX' ? '$' : '₹'}
                          {rule.threshold.toLocaleString()}
                        </span>
                      )}
                      <span className="text-slate-500 ml-2">
                        (Cooldown: {rule.cooldown_seconds}s • Triggers: {rule.trigger_count})
                      </span>
                    </div>

                    {rule.notes && <div className="text-[11px] text-slate-400 italic">{rule.notes}</div>}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleToggle(rule.alert_id)}
                      className={`p-2 rounded-xl transition ${
                        rule.is_enabled
                          ? 'bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 border border-emerald-500/30'
                          : 'bg-slate-800 text-slate-500 hover:text-white'
                      }`}
                      title={rule.is_enabled ? 'Disable rule' : 'Enable rule'}
                    >
                      <Power className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(rule.alert_id)}
                      className="p-2 rounded-xl bg-slate-800/80 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                      title="Delete rule"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Notification Feed (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BellRing className="w-4 h-4 text-amber-400" />
              In-App Notification Feed
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  {unreadCount} unread
                </span>
              )}
            </h2>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setFilterUnread(!filterUnread)}
                className={`p-1.5 rounded-lg text-xs font-mono transition flex items-center gap-1 border ${
                  filterUnread
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                    : 'bg-slate-800 text-slate-400 border-white/5 hover:text-white'
                }`}
                title="Toggle unread only"
              >
                <Filter className="w-3 h-3" />
                Unread
              </button>
              {events.length > 0 && (
                <button
                  onClick={handleClearEvents}
                  className="text-xs text-slate-400 hover:text-rose-400 transition underline"
                >
                  Clear All
                </button>
              )}
            </div>
          </div>

          <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
            {events.length === 0 ? (
              <div className="p-8 text-center text-slate-500 bg-slate-900/40 rounded-2xl border border-white/5 text-xs">
                No notification events recorded yet. Triggered price/RSI thresholds appear here.
              </div>
            ) : (
              events.map((ev) => (
                <div
                  key={ev.event_id || ev.id}
                  onClick={() => !ev.is_read && handleMarkRead(ev.event_id)}
                  className={`p-3.5 rounded-2xl border transition cursor-pointer ${
                    !ev.is_read
                      ? 'bg-slate-900/90 border-cyan-500/30 shadow-lg shadow-cyan-500/5'
                      : 'bg-slate-950/40 border-white/5 opacity-70'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {ev.severity === 'CRITICAL' ? (
                        <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                      ) : ev.severity === 'WARNING' ? (
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                      ) : (
                        <Info className="w-4 h-4 text-cyan-400 shrink-0" />
                      )}
                      <span className="font-semibold text-white text-xs leading-snug">{ev.title}</span>
                    </div>
                    {!ev.is_read && (
                      <span className="w-2 h-2 rounded-full bg-cyan-400 shrink-0 mt-1" />
                    )}
                  </div>

                  <p className="text-[11px] text-slate-300 mt-1 pl-6 leading-relaxed">
                    {ev.message}
                  </p>

                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono mt-2 pl-6">
                    <span>{new Date(ev.triggered_at).toLocaleTimeString()}</span>
                    <span>{ev.alert_type}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Create Alert Rule Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/15 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Bell className="w-4 h-4 text-cyan-400" />
                Create New Alert Rule
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-3.5">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Symbol *</label>
                  <input
                    type="text"
                    required
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white uppercase font-mono focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Market</label>
                  <select
                    value={market}
                    onChange={(e) => setMarket(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:border-cyan-500 focus:outline-none"
                  >
                    <option value="NSE">NSE</option>
                    <option value="FOREX">FOREX</option>
                    <option value="MCX">MCX</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Alert Rule Type</label>
                <select
                  value={alertType}
                  onChange={(e) => setAlertType(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:border-cyan-500 focus:outline-none"
                >
                  <option value="PRICE_ABOVE">Price Above Target (PRICE_ABOVE)</option>
                  <option value="PRICE_BELOW">Price Below Target (PRICE_BELOW)</option>
                  <option value="RSI_THRESHOLD">RSI(14) Bound (RSI_THRESHOLD)</option>
                  <option value="MARKET_SESSION_OPEN">Market Session Open (MARKET_SESSION_OPEN)</option>
                  <option value="MARKET_SESSION_CLOSE">Market Session Close (MARKET_SESSION_CLOSE)</option>
                  <option value="DAILY_LOSS_LIMIT">Risk Guardian Bound (DAILY_LOSS_LIMIT)</option>
                </select>
              </div>

              {(alertType.includes('PRICE') || alertType === 'RSI_THRESHOLD') && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-mono text-slate-400 mb-1">Condition</label>
                    <select
                      value={condition}
                      onChange={(e) => setCondition(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:border-cyan-500 focus:outline-none font-mono"
                    >
                      <option value=">=">&gt;= (Greater or equal)</option>
                      <option value="<=">&lt;= (Less or equal)</option>
                      <option value="ABOVE">ABOVE</option>
                      <option value="BELOW">BELOW</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-mono text-slate-400 mb-1">
                      {alertType === 'RSI_THRESHOLD' ? 'RSI Value (0-100)' : 'Target Price'}
                    </label>
                    <input
                      type="number"
                      step="any"
                      required
                      value={threshold}
                      onChange={(e) => setThreshold(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Cooldown (Seconds)</label>
                <input
                  type="number"
                  min={10}
                  max={3600}
                  value={cooldown}
                  onChange={(e) => setCooldown(parseInt(e.target.value) || 60)}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
                />
                <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">
                  Prevents notification spam while price oscillates around threshold.
                </span>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Notes (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Breakout level resistance alert"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 shadow-md transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create Rule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
