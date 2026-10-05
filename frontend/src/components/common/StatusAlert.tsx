import React from 'react';
import {
  AlertTriangle,
  Clock,
  ShieldAlert,
  ServerCrash,
  KeyRound,
  Inbox,
  Sparkles,
  RefreshCw,
  Layers,
} from 'lucide-react';

export type StatusAlertType =
  | 'AI_UNAVAILABLE'
  | 'AI_FALLBACK'
  | 'MARKET_CLOSED'
  | 'STALE_DATA'
  | 'BACKEND_OFFLINE'
  | 'ZERODHA_DISCONNECTED'
  | 'NO_POSITIONS'
  | 'NO_PROPOSALS';

interface StatusAlertProps {
  type: StatusAlertType;
  title?: string;
  detail?: string;
  timestamp?: string;
  freshnessAgeSeconds?: number;
  dataSource?: string;
  onRetry?: () => void;
  className?: string;
}

export const StatusAlert: React.FC<StatusAlertProps> = ({
  type,
  title,
  detail,
  timestamp,
  freshnessAgeSeconds,
  dataSource,
  onRetry,
  className = '',
}) => {
  switch (type) {
    case 'AI_UNAVAILABLE':
      return (
        <div
          className={`flex items-start gap-3 p-4 rounded-xl border border-indigo-500/20 bg-indigo-950/20 text-indigo-200 ${className}`}
        >
          <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="font-bold text-xs uppercase tracking-wider text-indigo-300">
              {title || 'AI UNAVAILABLE'}
            </div>
            <div className="text-xs text-slate-300 mt-1">
              {detail || 'Deterministic analysis remains active. Algorithmic strategies and paper trading proceed without interruption.'}
            </div>
            {onRetry && (
              <button
                onClick={onRetry}
                className="mt-2.5 inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-indigo-500/20 text-indigo-200 hover:bg-indigo-500/30 border border-indigo-500/30 transition-colors"
              >
                <RefreshCw className="w-3 h-3" /> Recheck Ollama Connection
              </button>
            )}
          </div>
        </div>
      );

    case 'AI_FALLBACK':
      return (
        <div
          className={`flex items-start gap-3 p-3.5 rounded-xl border border-amber-500/20 bg-amber-950/20 text-amber-200 ${className}`}
        >
          <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-xs text-amber-300">
              {title || 'AI FALLBACK ACTIVE'}
            </div>
            <div className="text-[11px] text-slate-300 mt-0.5">
              {detail || 'Deterministic analysis is being used. Factual technical indicators ground all decision rationales.'}
            </div>
          </div>
        </div>
      );

    case 'MARKET_CLOSED':
      return (
        <div
          className={`flex items-start gap-3 p-4 rounded-xl border border-slate-700/60 bg-slate-900/50 text-slate-200 ${className}`}
        >
          <Clock className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="font-bold text-xs uppercase tracking-wider text-slate-300">
              {title || 'NSE CLOSED'}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              {detail || 'Historical / Demo mode is available. You can backtest strategies or review simulated paper portfolios.'}
            </div>
          </div>
        </div>
      );

    case 'STALE_DATA':
      return (
        <div
          className={`flex items-start gap-3 p-4 rounded-xl border border-orange-500/30 bg-orange-950/25 text-orange-200 ${className}`}
        >
          <AlertTriangle className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="font-bold text-xs uppercase tracking-wider text-orange-300 flex items-center gap-1.5">
              <span>{title || 'NEW TRADE BLOCKED'}</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-500/20 border border-orange-500/40">
                MARKET DATA IS STALE
              </span>
            </div>
            <div className="text-xs text-slate-300 mt-1">
              {detail || 'Market data freshness threshold exceeded. Algorithmic signals and proposals are halted to prevent executing on obsolete prices.'}
            </div>
            {(timestamp || freshnessAgeSeconds !== undefined || dataSource) && (
              <div className="mt-2 flex flex-wrap gap-2 text-[10px] font-mono text-orange-300/80">
                {dataSource && <span>Source: {dataSource}</span>}
                {timestamp && <span>Timestamp: {timestamp}</span>}
                {freshnessAgeSeconds !== undefined && <span>Age: {freshnessAgeSeconds}s</span>}
              </div>
            )}
            {onRetry && (
              <button
                onClick={onRetry}
                className="mt-2.5 inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-orange-500/20 text-orange-200 hover:bg-orange-500/30 border border-orange-500/30 transition-colors"
              >
                <RefreshCw className="w-3 h-3" /> Refresh Feed
              </button>
            )}
          </div>
        </div>
      );

    case 'BACKEND_OFFLINE':
      return (
        <div
          className={`flex items-start gap-3 p-4 rounded-xl border border-rose-500/30 bg-rose-950/25 text-rose-200 ${className}`}
        >
          <ServerCrash className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="font-bold text-xs uppercase tracking-wider text-rose-300">
              {title || 'BACKEND OFFLINE'}
            </div>
            <div className="text-xs text-slate-300 mt-1">
              {detail || 'The trading engine backend at 127.0.0.1:8000 is currently unavailable. Please verify uvicorn is running.'}
            </div>
            {onRetry && (
              <button
                onClick={onRetry}
                className="mt-2.5 inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-rose-500/20 text-rose-200 hover:bg-rose-500/30 border border-rose-500/30 transition-colors"
              >
                <RefreshCw className="w-3 h-3" /> Retry Connection
              </button>
            )}
          </div>
        </div>
      );

    case 'ZERODHA_DISCONNECTED':
      return (
        <div
          className={`flex items-start gap-3 p-4 rounded-xl border border-white/[0.08] bg-[#0E1626]/60 text-slate-300 ${className}`}
        >
          <KeyRound className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="font-bold text-xs uppercase tracking-wider text-slate-200">
              {title || 'ZERODHA NOT CONNECTED'}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              {detail || 'Paper trading remains fully available. Zerodha Kite Connect integration is optional and restricted strictly to read-only account surveillance.'}
            </div>
          </div>
        </div>
      );

    case 'NO_POSITIONS':
      return (
        <div
          className={`flex flex-col items-center justify-center p-8 rounded-2xl border border-dashed border-white/[0.08] bg-white/[0.01] text-center ${className}`}
        >
          <Layers className="w-8 h-8 text-slate-500 mb-2.5" />
          <div className="font-semibold text-xs text-slate-300 uppercase tracking-wider">
            {title || 'NO OPEN POSITIONS'}
          </div>
          <div className="text-xs text-slate-500 mt-1 max-w-sm">
            {detail || 'Approved paper trades will appear here with real-time P&L and autonomous exit monitoring.'}
          </div>
        </div>
      );

    case 'NO_PROPOSALS':
      return (
        <div
          className={`flex flex-col items-center justify-center p-8 rounded-2xl border border-dashed border-white/[0.08] bg-white/[0.01] text-center ${className}`}
        >
          <Inbox className="w-8 h-8 text-slate-500 mb-2.5" />
          <div className="font-semibold text-xs text-slate-300 uppercase tracking-wider">
            {title || 'NO VALID TRADE PROPOSALS'}
          </div>
          <div className="text-xs text-slate-500 mt-1 max-w-sm">
            {detail || 'The algorithm engine is waiting for a valid setup satisfying technical indicator rules and Risk Guardian limits.'}
          </div>
        </div>
      );
  }
};
