import React, { useState, useEffect } from 'react';
import { Settings, Save, CheckCircle2, AlertCircle, Database, Shield, Sliders, ShieldAlert } from 'lucide-react';
import { api } from '../../services/api';
import { UserSettings, UserSettingsUpdate, NavTabId } from '../../types/market';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { SettingsCenterView } from './SettingsCenterView';

interface SettingsViewProps {
  onNavigate?: (tab: NavTabId, symbol?: string) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onNavigate }) => {
  const [activeSubtab, setActiveSubtab] = useState<'preferences' | 'system_center'>('preferences');
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Form states
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [defaultMarket, setDefaultMarket] = useState<'ALL' | 'FOREX' | 'NSE' | 'MCX'>('ALL');
  const [defaultTimeframe, setDefaultTimeframe] = useState<string>('1D');
  const [riskPercentage, setRiskPercentage] = useState<number>(1.0);
  const [notifications, setNotifications] = useState<boolean>(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await api.getSettings();
      setSettings(data);
      setTheme(data.theme);
      setDefaultMarket(data.default_market);
      setDefaultTimeframe(data.default_timeframe || '1D');
      setRiskPercentage(data.risk_percentage || 1.0);
      setNotifications(data.notifications_enabled ?? true);
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to load settings', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (riskPercentage <= 0 || riskPercentage > 100) {
      setMessage({ text: 'Risk percentage must be between 0.1% and 100%.', type: 'error' });
      return;
    }

    try {
      setSaving(true);
      const payload: UserSettingsUpdate = {
        theme,
        default_market: defaultMarket,
        default_timeframe: defaultTimeframe,
        risk_percentage: Number(riskPercentage),
        notifications_enabled: notifications,
      };
      const updated = await api.updateSettings(payload);
      setSettings(updated);
      setMessage({ text: 'Settings successfully saved and persisted to SQLite database.', type: 'success' });
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to update settings.', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading user preferences from SQLite..." />;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* View Header */}
      <div className="bg-panel border border-border rounded-lg p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg shadow-black/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100 font-mono">Terminal & Risk Settings</h2>
            <p className="text-xs text-slate-400">Configure local workspace preferences and risk parameters.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="accent" size="md">
            <Database className="w-3.5 h-3.5" />
            SQLite Storage
          </Badge>
        </div>
      </div>

      {/* Status feedback message */}
      {message && (
        <div
          className={`p-4 rounded-lg border text-xs flex items-center gap-2.5 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Subtab Navigation */}
      <div className="flex items-center gap-2 border-b border-border pb-2 font-mono text-xs">
        <button
          type="button"
          onClick={() => setActiveSubtab('preferences')}
          className={`px-3 py-1.5 rounded-md font-semibold transition-all flex items-center gap-1.5 ${
            activeSubtab === 'preferences'
              ? 'bg-accent/20 text-accent border border-accent/30'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          Workspace & Risk Preferences
        </button>
        <button
          type="button"
          onClick={() => setActiveSubtab('system_center')}
          className={`px-3 py-1.5 rounded-md font-semibold transition-all flex items-center gap-1.5 ${
            activeSubtab === 'system_center'
              ? 'bg-accent/20 text-accent border border-accent/30'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5 text-indigo-400" />
          Consolidated System Center (7 Subsystems)
        </button>
      </div>

      {activeSubtab === 'system_center' ? (
        <SettingsCenterView onNavigate={onNavigate} />
      ) : (
        /* Settings Form */
        <form onSubmit={handleSave} className="bg-panel border border-border rounded-lg p-6 space-y-6 shadow-lg shadow-black/20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Default Market */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 font-mono">
              Default Market Segment
            </label>
            <select
              value={defaultMarket}
              onChange={(e) => setDefaultMarket(e.target.value as any)}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-accent font-mono"
            >
              <option value="ALL">ALL (Multi-Market Overview)</option>
              <option value="FOREX">FOREX (Global Currency Pairs)</option>
              <option value="NSE">NSE (Indian Equities & Indices)</option>
              <option value="MCX">MCX (Indian Commodities)</option>
            </select>
            <p className="text-[11px] text-slate-400 mt-1">Default segment selected upon launching the terminal.</p>
          </div>

          {/* Default Timeframe */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 font-mono">
              Default Chart Timeframe
            </label>
            <select
              value={defaultTimeframe}
              onChange={(e) => setDefaultTimeframe(e.target.value)}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-accent font-mono"
            >
              <option value="1m">1 Minute (1m)</option>
              <option value="5m">5 Minutes (5m)</option>
              <option value="15m">15 Minutes (15m)</option>
              <option value="1h">1 Hour (1h)</option>
              <option value="1D">1 Day (1D - Default)</option>
            </select>
            <p className="text-[11px] text-slate-400 mt-1">Initial candlestick timeframe for the TradingView chart.</p>
          </div>

          {/* Risk Percentage */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 font-mono">
              Max Risk Tolerance Per Trade (%)
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="100.0"
                value={riskPercentage}
                onChange={(e) => setRiskPercentage(parseFloat(e.target.value) || 0)}
                className="w-full bg-background border border-border rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-accent font-mono pr-8"
              />
              <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-mono">%</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Simulated risk allocation guardrail per trade position.</p>
          </div>

          {/* Theme Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 font-mono">
              UI Appearance Theme
            </label>
            <select
              value={theme}
              onChange={(e) => setTheme(e.target.value as any)}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-accent font-mono"
            >
              <option value="dark">Dark Theme (Financial Terminal Default)</option>
              <option value="light">Light Theme (Preview)</option>
            </select>
            <p className="text-[11px] text-slate-400 mt-1">High-contrast dark theme optimized for analytical charts.</p>
          </div>
        </div>

        {/* Notifications Toggle */}
        <div className="pt-4 border-t border-border flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-200 font-mono">Trading Alert Notifications</div>
            <div className="text-[11px] text-slate-400">Receive simulated alerts when price touches SL/TP levels.</div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={notifications}
              onChange={(e) => setNotifications(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
          </label>
        </div>

        {/* Meta / Timestamps */}
        {settings && (
          <div className="pt-4 border-t border-border flex flex-wrap items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>Database Record ID: #{settings.id}</span>
            <span>Last Updated: {new Date(settings.updated_at).toLocaleString()}</span>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2 rounded-md bg-accent hover:bg-sky-400 text-slate-950 text-xs font-bold font-mono transition-colors shadow-lg shadow-accent/10 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving to Database...' : 'Save Settings'}
          </button>
        </div>
      </form>
      )}
    </div>
  );
};
