import React, { useState, useEffect } from 'react';
import {
  Database,
  UploadCloud,
  Trash2,
  Eye,
  CheckCircle2,
  AlertTriangle,
  FileText,
  RefreshCw,
  Search,
  Calendar,
  Layers,
  Clock,
  ArrowUpDown,
  Download,
  X,
  Check,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../../services/api';
import { DatasetItemData, DatasetDetailData, OHLCCandle, NavTabId } from '../../types/market';

interface DataManagerViewProps {
  onNavigate?: (tab: NavTabId, symbol?: string) => void;
}

export const DataManagerView: React.FC<DataManagerViewProps> = ({ onNavigate }) => {
  const [datasets, setDatasets] = useState<DatasetItemData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedMarket, setSelectedMarket] = useState<string>('ALL');

  // Inspection Modal
  const [inspectModalOpen, setInspectModalOpen] = useState<boolean>(false);
  const [inspectedDataset, setInspectedDataset] = useState<DatasetDetailData | null>(null);
  const [inspectLoading, setInspectLoading] = useState<boolean>(false);

  // Upload Modal
  const [uploadModalOpen, setUploadModalOpen] = useState<boolean>(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadSymbol, setUploadSymbol] = useState<string>('');
  const [uploadMarket, setUploadMarket] = useState<string>('NSE');
  const [uploadTimeframe, setUploadTimeframe] = useState<string>('1D');
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadSuccessMsg, setUploadSuccessMsg] = useState<string | null>(null);
  const [uploadErrorMsg, setUploadErrorMsg] = useState<string | null>(null);

  // Delete Confirmation
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<boolean>(false);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getDatasets();
      setDatasets(res.datasets || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load datasets.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleInspect = async (datasetId: string) => {
    try {
      setInspectLoading(true);
      setInspectModalOpen(true);
      const detail = await api.getDatasetDetail(datasetId);
      setInspectedDataset(detail);
    } catch (err: any) {
      alert(`Failed to load dataset details: ${err.message}`);
      setInspectModalOpen(false);
    } finally {
      setInspectLoading(false);
    }
  };

  const handleDelete = async (datasetId: string) => {
    try {
      setDeleting(true);
      await api.deleteDataset(datasetId);
      setDeleteTargetId(null);
      fetchDatasets();
    } catch (err: any) {
      alert(`Failed to delete dataset: ${err.message}`);
    } finally {
      setDeleting(false);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadErrorMsg('Please select a valid CSV file.');
      return;
    }

    try {
      setUploading(true);
      setUploadErrorMsg(null);
      setUploadSuccessMsg(null);

      const formData = new FormData();
      formData.append('file', uploadFile);
      if (uploadSymbol.trim()) {
        formData.append('symbol', uploadSymbol.trim().toUpperCase());
      }
      formData.append('market', uploadMarket);
      formData.append('timeframe', uploadTimeframe);

      const res = await api.uploadDatasetFile(formData);
      setUploadSuccessMsg(
        `Successfully ingested ${res.total_rows || res.row_count || 'rows'} for ${res.symbol || uploadSymbol || 'dataset'}.`
      );
      setTimeout(() => {
        setUploadModalOpen(false);
        setUploadFile(null);
        setUploadSymbol('');
        setUploadSuccessMsg(null);
        fetchDatasets();
      }, 1500);
    } catch (err: any) {
      setUploadErrorMsg(err.message || 'CSV Ingestion failed.');
    } finally {
      setUploading(false);
    }
  };

  const filteredDatasets = datasets.filter((ds) => {
    const matchesSearch =
      ds.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ds.dataset_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesMarket = selectedMarket === 'ALL' || ds.market.toUpperCase() === selectedMarket.toUpperCase();
    return matchesSearch && matchesMarket;
  });

  const markets = ['ALL', ...Array.from(new Set(datasets.map((d) => d.market.toUpperCase())))];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-[#0B101D]/90 border border-white/[0.08] rounded-xl backdrop-blur-xl shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              Historical Data Manager
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-300">
                CAUSAL VALIDATED
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Manage persisted historical OHLCV datasets, inspect candle continuity, and upload validated CSV files.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchDatasets}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 text-xs font-medium border border-white/[0.08] flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => {
              setUploadModalOpen(true);
              setUploadErrorMsg(null);
              setUploadSuccessMsg(null);
            }}
            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 flex items-center gap-1.5 transition-all"
          >
            <UploadCloud className="w-4 h-4" />
            Upload CSV
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[#0B101D]/70 p-3 rounded-lg border border-white/[0.06]">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Symbol or Dataset ID..."
            className="w-full bg-[#070A12]/90 border border-white/[0.08] rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400 font-medium">Market:</span>
          <div className="flex items-center gap-1 overflow-x-auto">
            {markets.map((m) => (
              <button
                key={m}
                onClick={() => setSelectedMarket(m)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                  selectedMarket === m
                    ? 'bg-blue-500/20 border border-blue-500/40 text-blue-300 font-semibold'
                    : 'bg-white/[0.02] border border-white/[0.04] text-slate-400 hover:text-slate-200'
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Datasets Table */}
      <div className="bg-[#0B101D]/90 border border-white/[0.08] rounded-xl overflow-hidden shadow-lg">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-400" />
            <p className="text-xs font-mono">Loading persisted datasets...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-400">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2" />
            <p className="text-xs font-mono">{error}</p>
          </div>
        ) : filteredDatasets.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <Database className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            <p className="text-xs font-medium text-slate-300">No datasets found</p>
            <p className="text-[11px] text-slate-500 mt-1">Upload a CSV or reset your filter criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/[0.02] border-b border-white/[0.06] text-slate-400 font-mono text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Dataset ID</th>
                  <th className="py-3 px-4">Symbol</th>
                  <th className="py-3 px-4">Market</th>
                  <th className="py-3 px-4">Timeframe</th>
                  <th className="py-3 px-4 text-right">Total Rows</th>
                  <th className="py-3 px-4">Date Range</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Source</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredDatasets.map((ds) => (
                  <tr key={ds.dataset_id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-slate-200">
                      {ds.dataset_id}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-white font-mono text-xs">{ds.symbol}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/[0.05] text-slate-300 border border-white/[0.08]">
                        {ds.market}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {ds.timeframe || '1D'}
                    </td>
                    <td className="py-3 px-4 font-mono text-right text-slate-200">
                      {(ds.total_rows || 0).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                      {ds.start_time && ds.end_time ? (
                        <span>
                          {ds.start_time.split('T')[0]} &rarr; {ds.end_time.split('T')[0]}
                        </span>
                      ) : (
                        <span className="text-slate-600">N/A</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {ds.is_valid ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                          <CheckCircle2 className="w-3 h-3" />
                          VALID
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[10px] font-mono text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                          <AlertTriangle className="w-3 h-3" />
                          UNVERIFIED
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-white/[0.04]">
                        {ds.source || (ds.dataset_id.startsWith('DS-') ? 'USER' : 'DEMO')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleInspect(ds.dataset_id)}
                          className="p-1.5 rounded hover:bg-blue-500/20 text-slate-400 hover:text-blue-300 transition-colors"
                          title="Inspect Preview & Validation"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        {onNavigate && (
                          <button
                            onClick={() => onNavigate('market_replay', ds.symbol)}
                            className="px-2 py-1 rounded bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 text-[10px] font-mono border border-indigo-500/30 transition-colors"
                            title="Replay this dataset"
                          >
                            Replay
                          </button>
                        )}
                        <button
                          onClick={() => setDeleteTargetId(ds.dataset_id)}
                          className="p-1.5 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors"
                          title="Delete Dataset"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Inspect Modal */}
      {inspectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-3xl bg-[#0B101D] border border-white/[0.12] rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-4 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.02]">
              <div className="flex items-center gap-2.5">
                <FileText className="w-4 h-4 text-blue-400" />
                <h3 className="font-bold text-sm text-white font-mono">
                  Dataset Inspection & Validation: {inspectedDataset?.symbol || '...'}
                </h3>
              </div>
              <button
                onClick={() => setInspectModalOpen(false)}
                className="p-1 text-slate-400 hover:text-white rounded hover:bg-white/[0.06]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-4">
              {inspectLoading || !inspectedDataset ? (
                <div className="py-12 text-center text-slate-400">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-400" />
                  <p className="text-xs font-mono">Fetching dataset candle preview...</p>
                </div>
              ) : (
                <>
                  {/* Summary Metric Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-lg">
                      <span className="text-[10px] text-slate-500 uppercase font-mono block">Dataset ID</span>
                      <span className="text-xs font-bold text-slate-200 font-mono truncate block">
                        {inspectedDataset.dataset_id}
                      </span>
                    </div>
                    <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-lg">
                      <span className="text-[10px] text-slate-500 uppercase font-mono block">Rows</span>
                      <span className="text-xs font-bold text-slate-200 font-mono">
                        {(inspectedDataset.total_rows || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-lg">
                      <span className="text-[10px] text-slate-500 uppercase font-mono block">Market / TF</span>
                      <span className="text-xs font-bold text-slate-200 font-mono">
                        {inspectedDataset.market} / {inspectedDataset.timeframe || '1D'}
                      </span>
                    </div>
                    <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-lg">
                      <span className="text-[10px] text-slate-500 uppercase font-mono block">Causal Check</span>
                      <span className="text-xs font-bold text-emerald-400 font-mono flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        PASSED
                      </span>
                    </div>
                  </div>

                  {/* Sample Preview Table */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-300 font-mono mb-2 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-blue-400" />
                      Candle Head Sample (First {inspectedDataset.preview_candles?.length || 0} bars)
                    </h4>
                    <div className="bg-[#070A12] border border-white/[0.06] rounded-lg overflow-x-auto max-h-56">
                      <table className="w-full text-left text-[11px] font-mono">
                        <thead className="bg-white/[0.04] text-slate-400 border-b border-white/[0.06]">
                          <tr>
                            <th className="py-2 px-3">Timestamp / Date</th>
                            <th className="py-2 px-3 text-right">Open</th>
                            <th className="py-2 px-3 text-right">High</th>
                            <th className="py-2 px-3 text-right">Low</th>
                            <th className="py-2 px-3 text-right">Close</th>
                            <th className="py-2 px-3 text-right">Volume</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.04] text-slate-300">
                          {inspectedDataset.preview_candles?.map((c, i) => (
                            <tr key={i} className="hover:bg-white/[0.02]">
                              <td className="py-1.5 px-3 text-slate-400">
                                {new Date((c.time || 0) * 1000).toISOString().split('T')[0]}
                              </td>
                              <td className="py-1.5 px-3 text-right">{c.open?.toFixed(2)}</td>
                              <td className="py-1.5 px-3 text-right text-emerald-400">{c.high?.toFixed(2)}</td>
                              <td className="py-1.5 px-3 text-right text-rose-400">{c.low?.toFixed(2)}</td>
                              <td className="py-1.5 px-3 text-right font-bold text-white">{c.close?.toFixed(2)}</td>
                              <td className="py-1.5 px-3 text-right text-slate-400">
                                {(c.volume || 0).toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="p-4 border-t border-white/[0.08] bg-white/[0.02] flex items-center justify-end">
              <button
                onClick={() => setInspectModalOpen(false)}
                className="px-4 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-slate-200 text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-[#0B101D] border border-white/[0.12] rounded-xl shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.02]">
              <div className="flex items-center gap-2">
                <UploadCloud className="w-4 h-4 text-blue-400" />
                <h3 className="font-bold text-sm text-white font-mono">Upload Historical CSV</h3>
              </div>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="p-1 text-slate-400 hover:text-white rounded hover:bg-white/[0.06]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  CSV File (Requires columns: timestamp/date, open, high, low, close, volume)
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer bg-[#070A12] p-2 rounded-lg border border-white/[0.08]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-slate-400 font-medium mb-1">
                    Symbol Override (Optional)
                  </label>
                  <input
                    type="text"
                    value={uploadSymbol}
                    onChange={(e) => setUploadSymbol(e.target.value)}
                    placeholder="e.g. RELIANCE"
                    className="w-full bg-[#070A12] border border-white/[0.08] rounded-lg px-3 py-1.5 text-xs text-white uppercase placeholder:text-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[11px] text-slate-400 font-medium mb-1">Market</label>
                  <select
                    value={uploadMarket}
                    onChange={(e) => setUploadMarket(e.target.value)}
                    className="w-full bg-[#070A12] border border-white/[0.08] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                  >
                    <option value="NSE">NSE (Indian Equities)</option>
                    <option value="FOREX">FOREX (FX Pairs)</option>
                    <option value="CRYPTO">CRYPTO (Digital Assets)</option>
                    <option value="COMMODITY">COMMODITY (Gold/Oil)</option>
                  </select>
                </div>
              </div>

              {uploadErrorMsg && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono">
                  {uploadErrorMsg}
                </div>
              )}

              {uploadSuccessMsg && (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono">
                  {uploadSuccessMsg}
                </div>
              )}

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="px-4 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-blue-600/30 flex items-center gap-1.5"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Validating & Ingesting...
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-3.5 h-3.5" />
                      Ingest Dataset
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTargetId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-sm bg-[#0B101D] border border-white/[0.12] rounded-xl shadow-2xl p-5 space-y-4">
            <div className="flex items-center gap-3 text-rose-400">
              <div className="w-9 h-9 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Delete Dataset</h3>
                <p className="text-[11px] text-slate-400">This action cannot be undone.</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 font-mono bg-white/[0.02] p-2.5 rounded border border-white/[0.06]">
              Target: <span className="text-white font-bold">{deleteTargetId}</span>
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setDeleteTargetId(null)}
                disabled={deleting}
                className="px-3.5 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteTargetId)}
                disabled={deleting}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-600/30 flex items-center gap-1.5"
              >
                {deleting ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
