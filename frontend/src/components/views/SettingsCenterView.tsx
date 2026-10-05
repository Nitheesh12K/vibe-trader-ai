import React, { useState, useEffect } from 'react';
import {
  Settings,
  ShieldAlert,
  ShieldCheck,
  Brain,
  Sliders,
  DollarSign,
  Lock,
  KeyRound,
  Bell,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Save,
  HelpCircle,
  FileCheck,
  X,
  Zap,
} from 'lucide-react';
import { api } from '../../services/api';
import { ConsolidatedSettingsData, NavTabId } from '../../types/market';

interface SettingsCenterViewProps {
  onNavigate?: (tab: NavTabId) => void;
}

export const SettingsCenterView: React.FC<SettingsCenterViewProps> = ({ onNavigate }) => {
  const [settings, setSettings] = useState<ConsolidatedSettingsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form State
  const [activeSection, setActiveSection] = useState<string>('simulation');

  // Simulation / User
  const [theme, setTheme] = useState<string>('dark');
  const [defaultMarket, setDefaultMarket] = useState<string>('NSE');
  const [defaultTimeframe, setDefaultTimeframe] = useState<string>('1D');
  const [riskPercentage, setRiskPercentage] = useState<number>(1.0);
  const [notificationsEnabled, setNotificationsEnabled] = useState<boolean>(true);

  // Risk Boundaries
  const [maxRiskPerTrade, setMaxRiskPerTrade] = useState<number>(2.0);
  const [maxDailyLoss, setMaxDailyLoss] = useState<number>(10000);
  const [maxOpenPositions, setMaxOpenPositions] = useState<number>(5);
  const [emergencyStopActive, setEmergencyStopActive] = useState<boolean>(false);

  // Autonomous Exits
  const [allowStopLoss, setAllowStopLoss] = useState<boolean>(true);
  const [allowTakeProfit, setAllowTakeProfit] = useState<boolean>(true);
  const [allowStrategyExit, setAllowStrategyExit] = useState<boolean>(true);
  const [allowMaxDrawdown, setAllowMaxDrawdown] = useState<boolean>(true);

  // Confirmation Modal for Risk Settings
  const [confirmRiskModalOpen, setConfirmRiskModalOpen] = useState<boolean>(false);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getConsolidatedSettings();
      setSettings(res);

      if (res.user_settings) {
        setTheme(res.user_settings.theme || 'dark');
        setDefaultMarket(res.user_settings.default_market || 'NSE');
        setDefaultTimeframe(res.user_settings.default_timeframe || '1D');
        setRiskPercentage(res.user_settings.risk_percentage || 1.0);
        setNotificationsEnabled(res.user_settings.notifications_enabled ?? true);
      }

      if (res.risk_settings) {
        setMaxRiskPerTrade(res.risk_settings.max_risk_per_trade_pct || 2.0);
        setMaxDailyLoss(res.risk_settings.max_daily_loss || 10000);
        setMaxOpenPositions(res.risk_settings.max_open_positions || 5);
        setEmergencyStopActive(res.risk_settings.emergency_stop_active ?? false);
      }

      if (res.autonomous_exit) {
        setAllowStopLoss(res.autonomous_exit.allow_stop_loss ?? true);
        setAllowTakeProfit(res.autonomous_exit.allow_take_profit ?? true);
        setAllowStrategyExit(res.autonomous_exit.allow_strategy_exit ?? true);
        setAllowMaxDrawdown(res.autonomous_exit.allow_max_drawdown ?? true);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load system settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveAll = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);

      const payload = {
        theme,
        default_market: defaultMarket,
        default_timeframe: defaultTimeframe,
        risk_percentage: Number(riskPercentage),
        notifications_enabled: notificationsEnabled,
        max_risk_per_trade_pct: Number(maxRiskPerTrade),
        max_daily_loss: Number(maxDailyLoss),
        max_open_positions: Number(maxOpenPositions),
        emergency_stop_active: emergencyStopActive,
        allow_stop_loss: allowStopLoss,
        allow_take_profit: allowTakeProfit,
        allow_strategy_exit: allowStrategyExit,
        allow_max_drawdown: allowMaxDrawdown,
      };

      const updated = await api.updateConsolidatedSettings(payload);
      setSettings(updated);
      setSuccessMsg('Settings saved successfully & logged to immutable audit trail.');
      setConfirmRiskModalOpen(false);
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to update settings.');
    } finally {
      setSaving(false);
    }
  };

  const sections = [
    { id: 'simulation', label: 'Simulation & Defaults', icon: Sliders },
    { id: 'risk', label: 'Risk Guardian Bounds', icon: ShieldAlert },
    { id: 'autonomous', label: 'Autonomous Exits', icon: Zap },
    { id: 'ai', label: 'AI Intelligence', icon: Brain },
    { id: 'broker', label: 'Broker & Read-Only Safety', icon: KeyRound },
  ];

  if (loading && !settings) {
    return (
      <div className="p-16 text-center text-slate-400 bg-[#0B101D]/90 rounded-xl border border-white/[0.08]">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-cyan-400" />
        <p className="text-xs font-mono">Loading central system configurations...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-[#0B101D]/90 border border-white/[0.08] rounded-xl backdrop-blur-xl shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              System Settings Center
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                AUDITED CONTROLS
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Configure deterministic risk boundaries, autonomous exit permissions, AI parameters, and broker telemetry.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setConfirmRiskModalOpen(true)}
            disabled={saving}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 flex items-center gap-1.5 transition-all"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save All Changes'}
          </button>
        </div>
      </div>

      {/* Status Banners */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        {/* Navigation Sidebar */}
        <div className="space-y-1 md:col-span-1">
          {sections.map((s) => {
            const Icon = s.icon;
            const isSel = activeSection === s.id;
            return (
              <button
                key={s.id}
                onClick={() => setActiveSection(s.id)}
                className={`w-full flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg text-xs font-medium font-mono transition-all text-left ${
                  isSel
                    ? 'bg-indigo-600/20 border-l-2 border-indigo-400 text-white font-semibold'
                    : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isSel ? 'text-indigo-400' : 'text-slate-500'}`} />
                <span>{s.label}</span>
              </button>
            );
          })}

          <div className="p-3.5 mt-4 rounded-lg bg-white/[0.02] border border-white/[0.06] text-[11px] text-slate-400 space-y-1 font-mono">
            <span className="text-slate-300 font-semibold flex items-center gap-1">
              <FileCheck className="w-3.5 h-3.5 text-indigo-400" />
              Audit Integrity
            </span>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              Every setting change generates an immutable <span className="text-slate-300">CONFIG_CHANGE</span> entry in the audit trail.
            </p>
          </div>
        </div>

        {/* Content Panels */}
        <div className="md:col-span-3 bg-[#0B101D]/90 border border-white/[0.08] rounded-xl p-5 space-y-6">
          {/* Section 1: Simulation & Defaults */}
          {activeSection === 'simulation' && (
            <div className="space-y-5">
              <div className="border-b border-white/[0.06] pb-3">
                <h3 className="font-bold text-sm text-white font-mono flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-indigo-400" />
                  Simulation & Workspace Preferences
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  General market display settings and initial default parameters.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">
                    Default Market Universe
                  </label>
                  <select
                    value={defaultMarket}
                    onChange={(e) => setDefaultMarket(e.target.value)}
                    className="w-full bg-[#070A12] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                  >
                    <option value="NSE">NSE (Indian Equities)</option>
                    <option value="FOREX">FOREX (FX Currency Pairs)</option>
                    <option value="CRYPTO">CRYPTO (Digital Assets)</option>
                    <option value="COMMODITY">COMMODITY (Gold / Crude Oil)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">
                    Default Timeframe
                  </label>
                  <select
                    value={defaultTimeframe}
                    onChange={(e) => setDefaultTimeframe(e.target.value)}
                    className="w-full bg-[#070A12] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                  >
                    <option value="1m">1 Minute</option>
                    <option value="5m">5 Minutes</option>
                    <option value="15m">15 Minutes</option>
                    <option value="1H">1 Hour</option>
                    <option value="1D">1 Day (Standard)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">
                    Interface Theme
                  </label>
                  <select
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                    className="w-full bg-[#070A12] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                  >
                    <option value="dark">Dark High-Contrast Terminal</option>
                    <option value="midnight">Midnight Indigo</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">
                    Notification Banners
                  </label>
                  <div className="flex items-center gap-3 pt-1">
                    <label className="flex items-center gap-2 cursor-pointer text-xs font-mono text-slate-300">
                      <input
                        type="checkbox"
                        checked={notificationsEnabled}
                        onChange={(e) => setNotificationsEnabled(e.target.checked)}
                        className="rounded border-white/[0.2] bg-[#070A12] text-indigo-600 focus:ring-0"
                      />
                      Enable In-App Trigger Alerts
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 2: Deterministic Risk Guardian Bounds */}
          {activeSection === 'risk' && (
            <div className="space-y-5">
              <div className="border-b border-white/[0.06] pb-3">
                <h3 className="font-bold text-sm text-white font-mono flex items-center gap-2 text-rose-300">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  Deterministic Risk Guardian Boundaries
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Immutable rules enforced on all paper execution proposals. Values outside valid ranges will be rejected.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">
                    Max Risk Per Trade (%) (0.1% — 10.0%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="10.0"
                    value={maxRiskPerTrade}
                    onChange={(e) => setMaxRiskPerTrade(parseFloat(e.target.value))}
                    className="w-full bg-[#070A12] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 block mt-1">
                    Proposals risking more than this capital % are blocked.
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">
                    Max Daily Loss Threshold (INR)
                  </label>
                  <input
                    type="number"
                    step="1000"
                    min="1000"
                    value={maxDailyLoss}
                    onChange={(e) => setMaxDailyLoss(parseFloat(e.target.value))}
                    className="w-full bg-[#070A12] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 block mt-1">
                    Halts new buy approvals if daily paper loss exceeds this amount.
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">
                    Max Concurrent Open Positions (1 — 50)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={maxOpenPositions}
                    onChange={(e) => setMaxOpenPositions(parseInt(e.target.value, 10))}
                    className="w-full bg-[#070A12] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 block mt-1">
                    Prevents over-exposure by limiting simultaneous open paper positions.
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">
                    Emergency Circuit Breaker
                  </label>
                  <div className="pt-2">
                    <label className="flex items-center gap-2 cursor-pointer text-xs font-mono text-rose-300 font-bold">
                      <input
                        type="checkbox"
                        checked={emergencyStopActive}
                        onChange={(e) => setEmergencyStopActive(e.target.checked)}
                        className="rounded border-rose-500/40 bg-[#070A12] text-rose-600 focus:ring-0"
                      />
                      EMERGENCY STOP (Blocks all new approvals immediately)
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 3: Autonomous Exit Permissions */}
          {activeSection === 'autonomous' && (
            <div className="space-y-5">
              <div className="border-b border-white/[0.06] pb-3">
                <h3 className="font-bold text-sm text-white font-mono flex items-center gap-2 text-amber-300">
                  <Zap className="w-4 h-4 text-amber-400" />
                  Autonomous Authorized Exit Triggers
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Grant permission to the background monitor to automatically exit open paper positions when deterministic rules are met.
                </p>
              </div>

              <div className="space-y-3">
                <label className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] cursor-pointer hover:bg-white/[0.04]">
                  <input
                    type="checkbox"
                    checked={allowStopLoss}
                    onChange={(e) => setAllowStopLoss(e.target.checked)}
                    className="mt-0.5 rounded border-white/[0.2] bg-[#070A12] text-indigo-600 focus:ring-0"
                  />
                  <div>
                    <span className="text-xs font-bold text-white font-mono block">
                      Allow Autonomous Stop-Loss Exits
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Instantly close position when current market price breaches registered stop-loss price.
                    </span>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] cursor-pointer hover:bg-white/[0.04]">
                  <input
                    type="checkbox"
                    checked={allowTakeProfit}
                    onChange={(e) => setAllowTakeProfit(e.target.checked)}
                    className="mt-0.5 rounded border-white/[0.2] bg-[#070A12] text-indigo-600 focus:ring-0"
                  />
                  <div>
                    <span className="text-xs font-bold text-white font-mono block">
                      Allow Autonomous Take-Profit Exits
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Lock in gains automatically when target take-profit price level is hit.
                    </span>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] cursor-pointer hover:bg-white/[0.04]">
                  <input
                    type="checkbox"
                    checked={allowStrategyExit}
                    onChange={(e) => setAllowStrategyExit(e.target.checked)}
                    className="mt-0.5 rounded border-white/[0.2] bg-[#070A12] text-indigo-600 focus:ring-0"
                  />
                  <div>
                    <span className="text-xs font-bold text-white font-mono block">
                      Allow Strategy Reversal Exits
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Close paper position when generating strategy emits an opposite or invalidation signal.
                    </span>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] cursor-pointer hover:bg-white/[0.04]">
                  <input
                    type="checkbox"
                    checked={allowMaxDrawdown}
                    onChange={(e) => setAllowMaxDrawdown(e.target.checked)}
                    className="mt-0.5 rounded border-white/[0.2] bg-[#070A12] text-indigo-600 focus:ring-0"
                  />
                  <div>
                    <span className="text-xs font-bold text-white font-mono block">
                      Allow Max Position Drawdown Protection
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Liquidate position if unrealized drawdown exceeds emergency threshold.
                    </span>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* Section 4: AI Intelligence Status */}
          {activeSection === 'ai' && (
            <div className="space-y-5">
              <div className="border-b border-white/[0.06] pb-3">
                <h3 className="font-bold text-sm text-white font-mono flex items-center gap-2 text-purple-300">
                  <Brain className="w-4 h-4 text-purple-400" />
                  AI Intelligence & Local LLM Provider
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Status of Ollama local model inference and rule-based deterministic fallback engine.
                </p>
              </div>

              {settings?.ai_status ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                      Provider & Host
                    </span>
                    <span className="text-xs font-bold text-white font-mono">
                      {settings.ai_status.provider_name} ({settings.ai_status.host})
                    </span>
                  </div>

                  <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                      Model Target
                    </span>
                    <span className="text-xs font-bold text-white font-mono">
                      {settings.ai_status.model_name || 'deepseek-r1:1.5b (or fallback)'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                      Online Inference
                    </span>
                    <span
                      className={`text-xs font-bold font-mono ${
                        settings.ai_status.is_online ? 'text-emerald-400' : 'text-amber-400'
                      }`}
                    >
                      {settings.ai_status.is_online ? 'OLLAMA ONLINE' : 'DETERMINISTIC FALLBACK ACTIVE'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                      Latency Telemetry
                    </span>
                    <span className="text-xs font-bold text-white font-mono">
                      {settings.ai_status.latency_ms || 0} ms
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-xs font-mono text-slate-500">AI provider status unavailable.</div>
              )}
            </div>
          )}

          {/* Section 5: Broker & Read-Only Safety */}
          {activeSection === 'broker' && (
            <div className="space-y-5">
              <div className="border-b border-white/[0.06] pb-3">
                <h3 className="font-bold text-sm text-white font-mono flex items-center gap-2 text-emerald-300">
                  <KeyRound className="w-4 h-4 text-emerald-400" />
                  Broker Adapter (Zerodha Kite Connect)
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Free read-only integration status and fail-closed safety interlock.
                </p>
              </div>

              {settings?.broker_status ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                      <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                        Connection Status
                      </span>
                      <span
                        className={`text-xs font-bold font-mono ${
                          settings.broker_status.is_connected ? 'text-emerald-400' : 'text-slate-400'
                        }`}
                      >
                        {settings.broker_status.is_connected ? 'CONNECTED (READ-ONLY)' : 'DISCONNECTED'}
                      </span>
                    </div>

                    <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                      <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                        API Key Masking
                      </span>
                      <span className="text-xs font-bold text-white font-mono">
                        {settings.broker_status.api_key_masked || 'None Configured'}
                      </span>
                    </div>

                    <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                      <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                        Live Execution Mode
                      </span>
                      <span className="text-xs font-bold text-rose-400 font-mono">
                        FAIL-CLOSED (HTTP 403)
                      </span>
                    </div>

                    <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                      <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                        Simulated Balance
                      </span>
                      <span className="text-xs font-bold text-white font-mono">
                        INR {(settings.risk_settings?.simulated_balance || 100000).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.06] text-[11px] font-mono text-slate-400">
                    <span className="text-slate-300 font-bold block mb-1">Broker Notice:</span>
                    {settings.broker_status.disclaimer ||
                      'Zerodha Kite Connect integration operates exclusively in read-only mode for market quotes. All live order placement endpoints return fail-closed 403 Forbidden.'}
                  </div>
                </div>
              ) : (
                <div className="text-xs font-mono text-slate-500">Broker status unavailable.</div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal for Risk Settings Update */}
      {confirmRiskModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-[#0B101D] border border-white/[0.12] rounded-xl shadow-2xl p-5 space-y-4">
            <div className="flex items-center gap-3 text-amber-400">
              <div className="w-9 h-9 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Confirm Configuration Updates</h3>
                <p className="text-[11px] text-slate-400">Deterministic risk limits will be updated immediately.</p>
              </div>
            </div>

            <div className="bg-[#070A12] p-3 rounded-lg border border-white/[0.06] space-y-1.5 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-400">Max Risk Per Trade:</span>
                <span className="text-white font-bold">{maxRiskPerTrade}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Max Daily Loss:</span>
                <span className="text-white font-bold">INR {maxDailyLoss.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Max Open Positions:</span>
                <span className="text-white font-bold">{maxOpenPositions}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Emergency Stop:</span>
                <span className={emergencyStopActive ? 'text-rose-400 font-bold' : 'text-slate-400'}>
                  {emergencyStopActive ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setConfirmRiskModalOpen(false)}
                className="px-4 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveAll}
                disabled={saving}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 flex items-center gap-1.5"
              >
                {saving ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Writing Audit Log...
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    Confirm & Save
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
