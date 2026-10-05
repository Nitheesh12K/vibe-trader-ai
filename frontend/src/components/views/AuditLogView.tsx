import React, { useState, useEffect, useCallback } from 'react';
import {
  FileCheck,
  Shield,
  Search,
  Filter,
  RefreshCw,
  Clock,
  User,
  Cpu,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../../services/api';
import { AuditLogRead } from '../../types/market';

export const AuditLogView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogRead[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getAuditLogs(
        eventTypeFilter !== 'ALL' ? eventTypeFilter : undefined,
        undefined,
        150
      );
      setLogs(data);
    } catch (err: any) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  }, [eventTypeFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const filteredLogs = logs.filter((log) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      log.action.toLowerCase().includes(q) ||
      log.event_type.toLowerCase().includes(q) ||
      log.actor.toLowerCase().includes(q) ||
      (log.symbol && log.symbol.toLowerCase().includes(q)) ||
      (log.proposal_id && log.proposal_id.toLowerCase().includes(q)) ||
      (log.position_id && log.position_id.toLowerCase().includes(q))
    );
  });

  const getEventBadge = (type: string) => {
    if (type.includes('EMERGENCY')) {
      return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
    }
    if (type.includes('APPROVED') || type.includes('EXECUTED')) {
      return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
    if (type.includes('REJECTED') || type.includes('BLOCKED')) {
      return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
    }
    return 'bg-accent/20 text-accent border-accent/40';
  };

  const getActorBadge = (actor: string) => {
    switch (actor) {
      case 'USER':
        return 'bg-blue-500/10 text-blue-300 border-blue-500/30';
      case 'PAPER_BROKER':
        return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
      case 'POSITION_MONITOR':
        return 'bg-purple-500/10 text-purple-300 border-purple-500/30';
      case 'STRATEGY_ENGINE':
        return 'bg-accent/10 text-accent border-accent/30';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-panel border border-border p-5 rounded-xl shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-accent/10 border border-accent/30 rounded-lg text-accent">
            <FileCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              Append-Only Security Audit Trail
              <span className="text-[10px] bg-accent/20 text-accent font-mono px-2 py-0.5 rounded border border-accent/30">
                FORENSIC LOGS
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Immutable event log recording every strategy proposal, user approval, risk check gate, and order execution.
            </p>
          </div>
        </div>

        <button
          onClick={fetchLogs}
          disabled={loading}
          className="p-2 bg-panel-subtle hover:bg-panel border border-border rounded-lg text-slate-400 hover:text-white transition-colors"
          title="Refresh logs"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-panel border border-border p-3 rounded-lg text-xs">
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search audit trail by symbol, action, proposal ID, actor..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-panel-subtle border border-border text-white text-xs pl-9 pr-3 py-2 rounded-lg focus:outline-none focus:border-accent"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-accent" />
          <span className="text-slate-400 font-semibold">Event:</span>
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="bg-panel-subtle border border-border text-white text-xs px-2.5 py-1.5 rounded-lg focus:outline-none focus:border-accent"
          >
            <option value="ALL">All Event Types</option>
            <option value="PROPOSAL_GENERATED">PROPOSAL_GENERATED</option>
            <option value="PROPOSAL_APPROVED">PROPOSAL_APPROVED</option>
            <option value="PROPOSAL_REJECTED">PROPOSAL_REJECTED</option>
            <option value="ORDER_EXECUTED">ORDER_EXECUTED</option>
            <option value="AUTONOMOUS_EXIT_TRIGGERED">AUTONOMOUS_EXIT_TRIGGERED</option>
            <option value="EMERGENCY_STOP_TRIGGERED">EMERGENCY_STOP_TRIGGERED</option>
            <option value="RISK_SETTINGS_UPDATED">RISK_SETTINGS_UPDATED</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-panel border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-panel-subtle border-b border-border text-slate-400 uppercase tracking-wider font-mono text-[10px]">
              <tr>
                <th className="p-3.5">Timestamp (UTC)</th>
                <th className="p-3.5">Event Type</th>
                <th className="p-3.5">Actor</th>
                <th className="p-3.5">Target</th>
                <th className="p-3.5">Action Summary</th>
                <th className="p-3.5 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {filteredLogs.map((log) => {
                const isExpanded = expandedId === log.id;
                return (
                  <React.Fragment key={log.id}>
                    <tr
                      onClick={() => setExpandedId(isExpanded ? null : log.id)}
                      className="hover:bg-panel-subtle/70 cursor-pointer transition-colors"
                    >
                      <td className="p-3.5 font-mono text-slate-400 text-[11px] whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-3 h-3 text-slate-500" />
                          <span>{new Date(log.timestamp).toLocaleString()}</span>
                        </div>
                      </td>

                      <td className="p-3.5">
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold border ${getEventBadge(
                            log.event_type
                          )}`}
                        >
                          {log.event_type}
                        </span>
                      </td>

                      <td className="p-3.5">
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded font-medium border ${getActorBadge(
                            log.actor
                          )}`}
                        >
                          {log.actor}
                        </span>
                      </td>

                      <td className="p-3.5 font-mono text-[11px] text-white">
                        {log.symbol ? (
                          <div>
                            <span className="font-bold">{log.symbol}</span>
                            {log.market && <span className="text-slate-400 text-[10px]"> ({log.market})</span>}
                          </div>
                        ) : log.proposal_id ? (
                          <span className="text-slate-300">{log.proposal_id}</span>
                        ) : log.position_id ? (
                          <span className="text-slate-300">{log.position_id}</span>
                        ) : (
                          <span className="text-slate-500">SYSTEM</span>
                        )}
                      </td>

                      <td className="p-3.5 text-slate-300 max-w-md truncate">
                        {log.action}
                      </td>

                      <td className="p-3.5 text-right">
                        <button className="text-slate-400 hover:text-white p-1">
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                      </td>
                    </tr>

                    {/* Expandable Forensic JSON details */}
                    {isExpanded && (
                      <tr className="bg-panel-subtle/40 border-b border-border/80">
                        <td colSpan={6} className="p-4">
                          <div className="space-y-1">
                            <span className="text-[10px] uppercase font-mono text-slate-400 font-semibold block">
                              Forensic Details Payload (Log ID: #{log.id})
                            </span>
                            <pre className="bg-slate-950 p-3 rounded-lg text-emerald-400 font-mono text-[11px] overflow-x-auto border border-border/60">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        {!loading && filteredLogs.length === 0 && (
          <div className="p-8 text-center text-slate-500 text-xs">
            No audit records match the current filter criteria.
          </div>
        )}
      </div>
    </div>
  );
};
