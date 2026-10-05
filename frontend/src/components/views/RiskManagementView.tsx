import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Sliders,
  DollarSign,
  Power,
  RefreshCw,
  Save,
  CheckCircle2,
  Lock,
  Layers,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  RiskSettingsRead,
  RiskSettingsUpdate,
  AutonomousExitPermissionRead,
  AutonomousExitPermissionUpdate,
} from '../../types/market';

export const RiskManagementView: React.FC = () => {
  const [riskSettings, setRiskSettings] = useState<RiskSettingsRead | null>(null);
  const [exitPerms, setExitPerms] = useState<AutonomousExitPermissionRead | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [savingRisk, setSavingRisk] = useState<boolean>(false);
  const [savingPerms, setSavingPerms] = useState<boolean>(false);
  const [togglingEmergency, setTogglingEmergency] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Form states for Risk Settings
  const [simulatedBalance, setSimulatedBalance] = useState<number>(100000);
  const [maxRiskPerTrade, setMaxRiskPerTrade] = useState<number>(2.0);
  const [maxDailyLoss, setMaxDailyLoss] = useState<number>(5000);
  const [maxOpenPositions, setMaxOpenPositions] = useState<number>(5);
  const [maxPositionSizePct, setMaxPositionSizePct] = useState<number>(20.0);

  // Form states for Autonomous Exit Permissions
  const [exitEnabled, setExitEnabled] = useState<boolean>(false);
  const [allowSL, setAllowSL] = useState<boolean>(true);
  const [allowTP, setAllowTP] = useState<boolean>(true);
  const [allowStrategyExit, setAllowStrategyExit] = useState<boolean>(false);
  const [allowMaxDD, setAllowMaxDD] = useState<boolean>(true);
  const [emergencyLimitPct, setEmergencyLimitPct] = useState<number>(10.0);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [risk, perms] = await Promise.all([
        api.getRiskSettings(),
        api.getAutonomousExitPermissions(),
      ]);
      setRiskSettings(risk);
      setExitPerms(perms);

      setSimulatedBalance(risk.simulated_balance);
      setMaxRiskPerTrade(risk.max_risk_per_trade_pct);
      setMaxDailyLoss(risk.max_daily_loss);
      setMaxOpenPositions(risk.max_open_positions);
      setMaxPositionSizePct(risk.max_position_size_pct);

      setExitEnabled(perms.is_enabled);
      setAllowSL(perms.allow_stop_loss);
      setAllowTP(perms.allow_take_profit);
      setAllowStrategyExit(perms.allow_strategy_exit);
      setAllowMaxDD(perms.allow_max_drawdown);
      setEmergencyLimitPct(perms.emergency_risk_limit_pct);
    } catch (err: any) {
      console.error('Failed to load risk management data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleToggleEmergencyStop = async () => {
    if (!riskSettings) return;
    const newState = !riskSettings.emergency_stop_active;
    const confirmMsg = newState
      ? 'HALT ALL TRADING? Activating the Global Emergency Stop will immediately block all new order submissions and pause automated market scans.'
      : 'Resume trading operations and clear Global Emergency Stop?';

    if (!window.confirm(confirmMsg)) return;

    try {
      setTogglingEmergency(true);
      const res = await api.toggleEmergencyStop(
        newState,
        newState ? 'Operator manual emergency kill-switch activation' : 'Operator cleared emergency stop'
      );
      setRiskSettings(res);
      showToast(
        newState
          ? 'EMERGENCY STOP ACTIVATED: All order execution is frozen.'
          : 'Emergency Stop cleared. Trading systems active.'
      );
    } catch (err: any) {
      alert(`Emergency Stop action failed: ${err.message}`);
    } finally {
      setTogglingEmergency(false);
    }
  };

  const handleSaveRiskSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSavingRisk(true);
      const updated = await api.updateRiskSettings({
        simulated_balance: simulatedBalance,
        max_risk_per_trade_pct: maxRiskPerTrade,
        max_daily_loss: maxDailyLoss,
        max_open_positions: maxOpenPositions,
        max_position_size_pct: maxPositionSizePct,
      });
      setRiskSettings(updated);
      showToast('Risk settings successfully saved and enforced.');
    } catch (err: any) {
      alert(`Failed to save risk settings: ${err.message}`);
    } finally {
      setSavingRisk(false);
    }
  };

  const handleSaveAutonomousPermissions = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSavingPerms(true);
      const updated = await api.updateAutonomousExitPermissions({
        is_enabled: exitEnabled,
        allow_stop_loss: allowSL,
        allow_take_profit: allowTP,
        allow_strategy_exit: allowStrategyExit,
        allow_max_drawdown: allowMaxDD,
        emergency_risk_limit_pct: emergencyLimitPct,
      });
      setExitPerms(updated);
      showToast('Autonomous Exit permissions updated.');
    } catch (err: any) {
      alert(`Failed to update autonomous exit permissions: ${err.message}`);
    } finally {
      setSavingPerms(false);
    }
  };

  const isEmergencyActive = !!riskSettings?.emergency_stop_active;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-16 right-8 z-50 bg-accent text-white px-4 py-2.5 rounded-lg shadow-xl border border-accent-indigo text-xs font-semibold flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-300" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] p-6 rounded-2xl">
        <div className="flex items-center gap-3.5">
          <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2.5">
              Risk Management & Emergency Controls
              <span className="text-[10px] bg-rose-500/15 text-rose-300 font-mono font-bold px-2.5 py-0.5 rounded-full border border-rose-500/30">
                CAPITAL PROTECTION GATES
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Strict server-side validation limits, master emergency stop kill-switch, and pre-authorized SELL rules.
            </p>
          </div>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="p-2.5 bg-[#080D1A] hover:bg-white/[0.04] border border-white/[0.08] rounded-xl text-slate-400 hover:text-white transition-colors"
          title="Refresh risk settings"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* MASTER EMERGENCY STOP BANNER */}
      <div
        className={`p-6 rounded-2xl border transition-all ${
          isEmergencyActive
            ? 'bg-gradient-to-r from-rose-950/90 via-red-900/70 to-rose-950/90 border-rose-500 shadow-2xl shadow-rose-950/50'
            : 'bg-[#0D1322]/80 backdrop-blur-xl border-white/[0.08] shadow-sm'
        }`}
      >
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <div
                className={`w-3.5 h-3.5 rounded-full ${
                  isEmergencyActive ? 'bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.9)] animate-ping' : 'bg-emerald-400'
                }`}
              />
              <h2 className="text-lg font-bold text-white tracking-tight font-mono">
                {isEmergencyActive ? 'EMERGENCY STOP IS ACTIVE' : 'GLOBAL SAFETY STATUS: NORMAL'}
              </h2>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              {isEmergencyActive
                ? 'CRITICAL ALERT: All automated market monitoring is halted, all pending proposal approvals are blocked by server-side risk gates, and no paper trades can execute.'
                : 'The master kill-switch allows immediate shutdown of all trading pipelines if unexpected market volatility or connection anomaly occurs.'}
            </p>
          </div>

          <button
            onClick={handleToggleEmergencyStop}
            disabled={togglingEmergency}
            className={`px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-lg transition-all ${
              isEmergencyActive
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-950/40'
                : 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-950/40 animate-pulse'
            }`}
          >
            <Power className="w-4 h-4" />
            {isEmergencyActive ? 'Clear Emergency Stop & Resume' : 'ACTIVATE EMERGENCY STOP'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Core Risk Sizing Settings */}
        <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2.5 border-b border-white/[0.08] pb-3">
            <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Sliders className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-white">Server-Side Risk Limits</h3>
          </div>

          <form onSubmit={handleSaveRiskSettings} className="space-y-4 text-xs">
            <div>
              <label className="text-slate-300 block mb-1 font-semibold">Simulated Virtual Balance ($)</label>
              <input
                type="number"
                step="100"
                value={simulatedBalance}
                onChange={(e) => setSimulatedBalance(parseFloat(e.target.value) || 0)}
                className="w-full bg-[#080D1A] border border-white/[0.08] text-white px-3.5 py-2.5 rounded-xl font-mono focus:border-cyan-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Total virtual account capital for position sizing checks.
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Max Risk Per Trade (%)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10.0"
                  value={maxRiskPerTrade}
                  onChange={(e) => setMaxRiskPerTrade(parseFloat(e.target.value) || 0)}
                  className="w-full bg-[#080D1A] border border-white/[0.08] text-white px-3.5 py-2.5 rounded-xl font-mono focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">Maximum % balance risked on SL.</span>
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Max Daily Loss ($)</label>
                <input
                  type="number"
                  step="50"
                  value={maxDailyLoss}
                  onChange={(e) => setMaxDailyLoss(parseFloat(e.target.value) || 0)}
                  className="w-full bg-[#080D1A] border border-white/[0.08] text-white px-3.5 py-2.5 rounded-xl font-mono focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">Hard cutoff for cumulative daily loss.</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Max Open Positions</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={maxOpenPositions}
                  onChange={(e) => setMaxOpenPositions(parseInt(e.target.value) || 1)}
                  className="w-full bg-[#080D1A] border border-white/[0.08] text-white px-3.5 py-2.5 rounded-xl font-mono focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">Concurrent open position cap.</span>
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Max Position Size (%)</label>
                <input
                  type="number"
                  step="1"
                  min="1"
                  max="100"
                  value={maxPositionSizePct}
                  onChange={(e) => setMaxPositionSizePct(parseFloat(e.target.value) || 1)}
                  className="w-full bg-[#080D1A] border border-white/[0.08] text-white px-3.5 py-2.5 rounded-xl font-mono focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">Notional exposure limit per asset.</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={savingRisk}
              className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:opacity-90 text-white rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-cyan-500/20"
            >
              <Save className="w-3.5 h-3.5" />
              {savingRisk ? 'Updating Risk Policy...' : 'Save & Enforce Risk Limits'}
            </button>
          </form>
        </div>

        {/* Autonomous Exit Permissions (Step 7) */}
        <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <Lock className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-white">Autonomous Exit Authorization</h3>
            </div>
            <span className="text-[10px] bg-emerald-500/15 text-emerald-400 font-mono font-bold px-2.5 py-0.5 rounded-full border border-emerald-500/30">
              STEP 7 RULES
            </span>
          </div>

          <form onSubmit={handleSaveAutonomousPermissions} className="space-y-4 text-xs">
            {/* Master Autonomous Exit Switch */}
            <div className="p-4 rounded-xl bg-[#080D1A] border border-white/[0.06] flex items-center justify-between">
              <div>
                <span className="font-bold text-white block">Pre-Authorize Autonomous SELL Exits</span>
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  Permits the system to execute paper SELL orders automatically when defined exit triggers are met.
                </span>
              </div>
              <input
                type="checkbox"
                checked={exitEnabled}
                onChange={(e) => setExitEnabled(e.target.checked)}
                className="w-5 h-5 accent-emerald-500 cursor-pointer"
              />
            </div>

            {/* Granular Exit Rules */}
            <div className="space-y-2.5 p-4 rounded-xl bg-[#080D1A]/60 border border-white/[0.06]">
              <span className="text-[11px] font-bold text-slate-300 block mb-2">
                Authorized Exit Triggers:
              </span>

              <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-white transition-colors">
                <input
                  type="checkbox"
                  checked={allowSL}
                  onChange={(e) => setAllowSL(e.target.checked)}
                  className="w-4 h-4 accent-cyan-500"
                />
                <span>Execute Stop-Loss immediately if price crosses SL threshold</span>
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-white transition-colors">
                <input
                  type="checkbox"
                  checked={allowTP}
                  onChange={(e) => setAllowTP(e.target.checked)}
                  className="w-4 h-4 accent-cyan-500"
                />
                <span>Execute Take-Profit immediately when profit target reached</span>
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-white transition-colors">
                <input
                  type="checkbox"
                  checked={allowStrategyExit}
                  onChange={(e) => setAllowStrategyExit(e.target.checked)}
                  className="w-4 h-4 accent-cyan-500"
                />
                <span>Execute Strategy Invalidation Exit (e.g. EMA bearish reversal)</span>
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-white transition-colors">
                <input
                  type="checkbox"
                  checked={allowMaxDD}
                  onChange={(e) => setAllowMaxDD(e.target.checked)}
                  className="w-4 h-4 accent-cyan-500"
                />
                <span>Execute Emergency Drawdown Cutoff</span>
              </label>
            </div>

            <div>
              <label className="text-slate-300 block mb-1 font-semibold">Emergency Risk Limit (% of position)</label>
              <input
                type="number"
                step="0.5"
                min="1.0"
                max="50.0"
                value={emergencyLimitPct}
                onChange={(e) => setEmergencyLimitPct(parseFloat(e.target.value) || 10.0)}
                className="w-full bg-[#080D1A] border border-white/[0.08] text-white px-3.5 py-2.5 rounded-xl font-mono focus:border-cyan-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Force-exit position if loss exceeds this safety ceiling regardless of strategy.
              </span>
            </div>

            <button
              type="submit"
              disabled={savingPerms}
              className="w-full py-2.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-950/40"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              {savingPerms ? 'Saving Permissions...' : 'Update Autonomous Exit Permissions'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
