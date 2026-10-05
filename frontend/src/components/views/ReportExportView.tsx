import React, { useState } from 'react';
import {
  FileText,
  Download,
  Copy,
  Check,
  ShieldCheck,
  AlertCircle,
  FileSpreadsheet,
  Code2,
  Lock,
  RefreshCw,
  ExternalLink,
  Eye,
  X,
} from 'lucide-react';
import { api } from '../../services/api';
import { NavTabId } from '../../types/market';

interface ReportExportViewProps {
  onNavigate?: (tab: NavTabId) => void;
}

interface ExportCardConfig {
  id: string;
  title: string;
  description: string;
  category: string;
  fields: string[];
  filenamePrefix: string;
}

const EXPORT_ITEMS: ExportCardConfig[] = [
  {
    id: 'trades',
    title: 'Paper Trading Execution Journal',
    category: 'TRADING PERFORMANCE',
    description:
      'Complete chronological log of simulated positions, orders, executed prices, realized P&L, slippage, and fees.',
    fields: ['trade_id', 'symbol', 'market', 'side', 'entry_price', 'exit_price', 'quantity', 'pnl', 'status', 'created_at'],
    filenamePrefix: 'paper_trades_export',
  },
  {
    id: 'journal',
    title: 'Qualitative Trade Reflections',
    category: 'PSYCHOLOGY & JOURNAL',
    description:
      'Trader notes, setup rationale, discipline evaluations, emotional state tags, and trade link references.',
    fields: ['journal_id', 'trade_id', 'symbol', 'title', 'notes', 'tags', 'lessons_learned', 'created_at'],
    filenamePrefix: 'trade_journal_export',
  },
  {
    id: 'portfolio',
    title: 'Portfolio & Capital Allocation Snapshot',
    category: 'CAPITAL & RISK',
    description:
      'Real-time snapshot of simulated account equity, available cash, open risk exposure, and active positions.',
    fields: ['account_balance', 'equity', 'available_cash', 'open_positions_count', 'realized_pnl', 'unrealized_pnl', 'timestamp'],
    filenamePrefix: 'portfolio_snapshot_export',
  },
  {
    id: 'audit',
    title: 'Append-Only System Audit Log',
    category: 'SAFETY & COMPLIANCE',
    description:
      'Cryptographically tracked record of approvals, configuration changes, risk blocks, and autonomous exits.',
    fields: ['audit_id', 'timestamp', 'actor', 'action', 'event_type', 'details_json'],
    filenamePrefix: 'audit_trail_export',
  },
];

export const ReportExportView: React.FC<ReportExportViewProps> = ({ onNavigate }) => {
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<{ title: string; json: any } | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);

  const handleDownload = (reportType: string, format: 'csv' | 'json') => {
    setDownloadingId(`${reportType}-${format}`);
    try {
      const url = api.getExportUrl(reportType, format);
      // Trigger browser download via anchor tag
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportType}_export.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setTimeout(() => setDownloadingId(null), 800);
    }
  };

  const handleCopyUrl = (reportType: string, format: 'csv' | 'json') => {
    const url = api.getExportUrl(reportType, format);
    navigator.clipboard.writeText(url);
    setCopiedId(`${reportType}-${format}`);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handlePreview = async (reportType: string, title: string) => {
    try {
      setPreviewLoading(true);
      setPreviewData(null);
      const data = await api.exportReport(reportType, 'json');
      setPreviewData({ title, json: data });
    } catch (err: any) {
      alert(`Preview failed: ${err.message}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-[#0B101D]/90 border border-white/[0.08] rounded-xl backdrop-blur-xl shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              Report & Data Export Center
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                NO SECRETS GUARANTEE
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Export verified simulation logs, journal notes, portfolio snapshots, and audit trails in CSV and JSON formats.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5 bg-white/[0.02] border border-white/[0.06] px-3 py-1.5 rounded-lg">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Zero Credentials In Exports
          </span>
        </div>
      </div>

      {/* Safety & Redaction Callout */}
      <div className="p-4 rounded-xl bg-emerald-500/[0.04] border border-emerald-500/20 text-xs flex items-start gap-3">
        <Lock className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-emerald-300 font-mono text-xs uppercase tracking-wide">
            Strict Credential Redaction & Security Enforcement
          </span>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            All export streams are generated with strict server-side sanitization. Under no circumstances are Zerodha API secrets, OAuth access tokens, passwords, or system environment variables included in exported CSV or JSON documents.
          </p>
        </div>
      </div>

      {/* Export Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {EXPORT_ITEMS.map((item) => (
          <div
            key={item.id}
            className="p-5 bg-[#0B101D]/90 border border-white/[0.08] hover:border-white/[0.16] rounded-xl flex flex-col justify-between transition-all shadow-md group"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-[10px] font-mono font-bold tracking-wider text-purple-400 uppercase">
                  {item.category}
                </span>
                <span className="text-[10px] font-mono text-slate-500">API: /api/exports/{item.id}</span>
              </div>

              <h3 className="font-bold text-sm text-white font-mono mb-1.5 group-hover:text-purple-300 transition-colors">
                {item.title}
              </h3>
              <p className="text-xs text-slate-400 mb-4 leading-relaxed">{item.description}</p>

              {/* Data Schema Pill Tags */}
              <div className="mb-4">
                <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1.5">
                  Included Schema Fields:
                </span>
                <div className="flex flex-wrap gap-1">
                  {item.fields.map((f) => (
                    <span
                      key={f}
                      className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/[0.03] text-slate-300 border border-white/[0.05]"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions Bar */}
            <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between gap-2">
              <button
                onClick={() => handlePreview(item.id, item.title)}
                className="px-2.5 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 text-xs font-mono flex items-center gap-1.5 transition-colors"
                title="Preview Sample JSON"
              >
                <Eye className="w-3.5 h-3.5 text-slate-400" />
                Preview
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownload(item.id, 'csv')}
                  disabled={downloadingId === `${item.id}-csv`}
                  className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/30 flex items-center gap-1.5 transition-all"
                  title="Download CSV"
                >
                  <Download className="w-3.5 h-3.5" />
                  {downloadingId === `${item.id}-csv` ? 'Downloading...' : 'CSV'}
                </button>

                <button
                  onClick={() => handleDownload(item.id, 'json')}
                  disabled={downloadingId === `${item.id}-json`}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 flex items-center gap-1.5 transition-all"
                  title="Download JSON"
                >
                  <Code2 className="w-3.5 h-3.5" />
                  {downloadingId === `${item.id}-json` ? 'Downloading...' : 'JSON'}
                </button>

                <button
                  onClick={() => handleCopyUrl(item.id, 'json')}
                  className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-400 hover:text-white transition-colors"
                  title="Copy Direct JSON API URL"
                >
                  {copiedId === `${item.id}-json` ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* JSON Preview Modal */}
      {(previewLoading || previewData) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-2xl bg-[#0B101D] border border-white/[0.12] rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-4 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.02]">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-purple-400" />
                <h3 className="font-bold text-sm text-white font-mono">
                  {previewData?.title || 'Loading Preview...'}
                </h3>
              </div>
              <button
                onClick={() => setPreviewData(null)}
                className="p-1 text-slate-400 hover:text-white rounded hover:bg-white/[0.06]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto font-mono text-xs">
              {previewLoading ? (
                <div className="py-12 text-center text-slate-400">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-purple-400" />
                  <p>Generating verified export payload...</p>
                </div>
              ) : (
                <pre className="bg-[#070A12] p-4 rounded-lg border border-white/[0.06] text-slate-300 overflow-x-auto text-[11px] leading-relaxed">
                  {JSON.stringify(previewData?.json, null, 2)}
                </pre>
              )}
            </div>

            <div className="p-4 border-t border-white/[0.08] bg-white/[0.02] flex items-center justify-between">
              <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Deterministic Output Sanitized
              </span>
              <button
                onClick={() => setPreviewData(null)}
                className="px-4 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-slate-200 text-xs font-semibold"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
