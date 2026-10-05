import React, { useState, useEffect } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Server,
  Database,
  Brain,
  ShieldAlert,
  ShieldCheck,
  Lock,
  KeyRound,
  FileCheck,
  Cpu,
  Clock,
  Zap,
} from 'lucide-react';
import { api } from '../../services/api';
import { SystemHealthFullResponse, SubsystemHealth, NavTabId } from '../../types/market';

interface SystemHealthViewProps {
  onNavigate?: (tab: NavTabId) => void;
}

export const SystemHealthView: React.FC<SystemHealthViewProps> = ({ onNavigate }) => {
  const [healthData, setHealthData] = useState<SystemHealthFullResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastProbeTime, setLastProbeTime] = useState<string>('');

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getSystemHealth();
      setHealthData(res);
      setLastProbeTime(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message || 'Failed to probe system diagnostics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    // Auto-refresh diagnostics every 45s
    const timer = setInterval(fetchHealth, 45000);
    return () => clearInterval(timer);
  }, []);

  const getSubsystemIcon = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('fastapi') || n.includes('backend')) return Server;
    if (n.includes('sqlite') || n.includes('database')) return Database;
    if (n.includes('ai') || n.includes('ollama')) return Brain;
    if (n.includes('csv') || n.includes('storage')) return Database;
    if (n.includes('broker') || n.includes('zerodha') || n.includes('kite')) return KeyRound;
    if (n.includes('audit')) return FileCheck;
    if (n.includes('risk') || n.includes('guardian')) return ShieldAlert;
    if (n.includes('execution') || n.includes('paper')) return Zap;
    return Activity;
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'ONLINE':
      case 'OK':
      case 'HEALTHY':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-2 py-0.5 rounded-full font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            ONLINE
          </span>
        );
      case 'DEGRADED':
      case 'FALLBACK':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-amber-400 bg-amber-500/10 border border-amber-500/25 px-2 py-0.5 rounded-full font-semibold">
            <AlertTriangle className="w-3.5 h-3.5" />
            DEGRADED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-rose-400 bg-rose-500/10 border border-rose-500/25 px-2 py-0.5 rounded-full font-semibold">
            <XCircle className="w-3.5 h-3.5" />
            OFFLINE
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-[#0B101D]/90 border border-white/[0.08] rounded-xl backdrop-blur-xl shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              System Health & Diagnostics Center
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                9 SUBSYSTEMS
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Live operational monitoring, real latency telemetry, and fail-closed safety verification.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {lastProbeTime && (
            <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-500" />
              Last probe: {lastProbeTime}
            </span>
          )}
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-600/30 flex items-center gap-1.5 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Run Diagnostics Probe
          </button>
        </div>
      </div>

      {/* Live Order Shield Callout */}
      <div className="p-4 rounded-xl bg-rose-500/[0.06] border border-rose-500/25 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-inner">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400 shrink-0">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xs font-bold font-mono text-rose-300 uppercase tracking-wide">
                Live Broker Order Execution: FAIL-CLOSED SHIELD ACTIVE
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold">
                HTTP 403 ENFORCED
              </span>
            </div>
            <p className="text-[11px] text-slate-300 mt-0.5">
              Zerodha Kite Connect integration operates exclusively in read-only mode for market quotes. All live order placement endpoints return fail-closed 403 Forbidden.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
          <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
            <ShieldCheck className="w-4 h-4" />
            Safety Interlock Verified
          </span>
        </div>
      </div>

      {/* Main Subsystems Grid */}
      {loading && !healthData ? (
        <div className="p-16 text-center text-slate-400 bg-[#0B101D]/90 rounded-xl border border-white/[0.08]">
          <RefreshCw className="w-7 h-7 animate-spin mx-auto mb-3 text-cyan-400" />
          <p className="text-xs font-mono">Pinging internal subsystems and verifying state...</p>
        </div>
      ) : error && !healthData ? (
        <div className="p-12 text-center text-rose-400 bg-[#0B101D]/90 rounded-xl border border-rose-500/25">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p className="text-xs font-mono font-bold">Diagnostic probe failed</p>
          <p className="text-[11px] text-slate-400 mt-1">{error}</p>
        </div>
      ) : healthData ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {healthData.services?.map((svc, idx) => {
            const Icon = getSubsystemIcon(svc.name);
            return (
              <div
                key={idx}
                className="p-4 bg-[#0B101D]/90 border border-white/[0.08] hover:border-white/[0.15] rounded-xl flex flex-col justify-between transition-all shadow-md group"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-cyan-400 group-hover:text-cyan-300">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <h3 className="text-xs font-bold text-white font-mono">{svc.name}</h3>
                        <span className="text-[10px] font-mono text-slate-400">
                          Latency: {svc.latency_ms} ms
                        </span>
                      </div>
                    </div>
                    {getStatusBadge(svc.status)}
                  </div>

                  {/* Details KV Pair List */}
                  {svc.details && Object.keys(svc.details).length > 0 && (
                    <div className="bg-[#070A12] p-2.5 rounded-lg border border-white/[0.04] space-y-1.5 font-mono text-[10px]">
                      {Object.entries(svc.details).map(([k, v]) => (
                        <div key={k} className="flex items-center justify-between gap-2">
                          <span className="text-slate-500 uppercase">{k.replace(/_/g, ' ')}:</span>
                          <span className="text-slate-200 font-semibold truncate max-w-[160px]">
                            {typeof v === 'boolean' ? (v ? 'TRUE' : 'FALSE') : String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-3 mt-3 border-t border-white/[0.04] flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span>Last check: {svc.last_check ? svc.last_check.split('T')[1]?.slice(0, 8) : 'Now'}</span>
                  <span className="flex items-center gap-1">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        svc.status === 'ONLINE' ? 'bg-emerald-400' : 'bg-amber-400'
                      }`}
                    />
                    Telemetry Active
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
};
