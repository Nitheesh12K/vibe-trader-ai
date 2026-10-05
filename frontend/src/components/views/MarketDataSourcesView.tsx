import React, { useState, useEffect } from 'react';
import {
  Database,
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Table,
  Layers,
  Info,
  Calendar,
  BarChart2,
} from 'lucide-react';
import { api } from '../../services/api';
import { CSVDatasetInfo, CSVUploadResult, MarketType } from '../../types/market';
import { LoadingSpinner } from '../common/LoadingSpinner';

const PRELOADED_DATASETS = [
  { symbol: 'RELIANCE', name: 'Reliance Industries Ltd.', market: 'NSE', candles: 120, tf: '1D', source: 'DEMO' },
  { symbol: 'TCS', name: 'Tata Consultancy Services', market: 'NSE', candles: 120, tf: '1D', source: 'DEMO' },
  { symbol: 'INFY', name: 'Infosys Limited', market: 'NSE', candles: 120, tf: '1D', source: 'DEMO' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank Limited', market: 'NSE', candles: 120, tf: '1D', source: 'DEMO' },
  { symbol: 'NIFTY 50', name: 'Nifty 50 Benchmark Index', market: 'NSE', candles: 120, tf: '1D', source: 'DEMO' },
  { symbol: 'EUR/USD', name: 'Euro / US Dollar', market: 'FOREX', candles: 120, tf: '1D', source: 'DEMO' },
  { symbol: 'GBP/USD', name: 'British Pound / US Dollar', market: 'FOREX', candles: 120, tf: '1D', source: 'DEMO' },
  { symbol: 'GOLD', name: 'MCX Gold Futures (10g)', market: 'MCX', candles: 120, tf: '1D', source: 'DEMO' },
  { symbol: 'CRUDEOIL', name: 'MCX Crude Oil Futures (Bbl)', market: 'MCX', candles: 120, tf: '1D', source: 'DEMO' },
];

export const MarketDataSourcesView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'demo' | 'csv_upload'>('demo');
  const [datasets, setDatasets] = useState<CSVDatasetInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [uploadSymbol, setUploadSymbol] = useState<string>('RELIANCE_CUSTOM');
  const [uploadMarket, setUploadMarket] = useState<MarketType>('NSE');
  const [csvText, setCsvText] = useState<string>(
`date,open,high,low,close,volume
2026-01-01,2500.0,2540.0,2490.0,2530.0,45000
2026-01-02,2530.0,2565.0,2520.0,2550.0,52000
2026-01-03,2550.0,2570.0,2535.0,2545.0,38000
2026-01-04,2545.0,2590.0,2540.0,2580.0,61000
2026-01-05,2580.0,2610.0,2575.0,2605.0,75000`
  );
  const [uploadResult, setUploadResult] = useState<CSVUploadResult | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const res = await api.getCSVDatasets();
      setDatasets(res.datasets);
    } catch (err: any) {
      console.warn('Failed to load CSV datasets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (content) {
        setCsvText(content);
        // Pre-fill symbol name from file
        const baseName = file.name.replace(/\.[^/.]+$/, '').toUpperCase();
        setUploadSymbol(baseName);
      }
    };
    reader.readAsText(file);
  };

  const handleValidateAndUpload = async () => {
    if (!csvText.trim()) {
      setMessage({ text: 'Please provide CSV content or upload a file.', type: 'error' });
      return;
    }

    try {
      setUploading(true);
      setMessage(null);
      setUploadResult(null);

      const result = await api.uploadCSV(csvText, uploadSymbol, uploadMarket);
      setUploadResult(result);

      if (result.is_valid) {
        setMessage({
          text: `CSV validated successfully! Ingested ${result.total_rows} candles for ${result.symbol}.`,
          type: 'success',
        });
        await fetchDatasets();
      } else {
        setMessage({
          text: `CSV validation failed with ${result.errors.length} error(s). Review report below.`,
          type: 'error',
        });
      }
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to validate/upload CSV', type: 'error' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] p-6 rounded-2xl shadow-xl shadow-black/40 relative overflow-hidden">
        <div className="absolute top-0 right-1/4 w-96 h-32 bg-cyan-500/[0.03] rounded-full blur-3xl pointer-events-none" />
        <div className="flex items-center gap-4 relative z-10">
          <div className="p-3 bg-gradient-to-br from-cyan-500/15 to-blue-600/15 border border-cyan-500/30 rounded-xl text-cyan-400 shadow-md shadow-cyan-500/10">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-xl font-bold text-white tracking-tight">
                Market Data Sources & CSV Provider
              </h1>
              <span className="text-[10px] bg-cyan-500/10 text-cyan-300 font-mono px-2.5 py-0.5 rounded-full border border-cyan-500/30 font-semibold tracking-wide">
                LOCAL-FIRST DATA
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Inspect pre-calibrated multi-market historical datasets or upload custom historical OHLCV CSVs for backtesting and strategy evaluation.
            </p>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center gap-1.5 bg-white/[0.03] p-1.5 rounded-xl border border-white/[0.06] text-xs relative z-10">
          <button
            onClick={() => setActiveTab('demo')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'demo'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/20 font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Preloaded Datasets ({PRELOADED_DATASETS.length})
          </button>
          <button
            onClick={() => setActiveTab('csv_upload')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'csv_upload'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/20 font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            CSV Ingestion & Validation
          </button>
        </div>
      </div>

      {message && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between shadow-md ${
            message.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}
        >
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-white">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tab 1: Preloaded Datasets */}
      {activeTab === 'demo' && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 space-y-1.5 shadow-xl shadow-black/40">
              <span className="text-xs text-slate-400 uppercase font-mono tracking-wider">Indian Equities (NSE)</span>
              <div className="text-2xl font-bold text-white font-mono tracking-tight">5 Instruments</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">Calibrated for ₹2,000 demo capital testing and intraday simulations.</p>
            </div>
            <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 space-y-1.5 shadow-xl shadow-black/40">
              <span className="text-xs text-slate-400 uppercase font-mono tracking-wider">Forex Major Pairs</span>
              <div className="text-2xl font-bold text-white font-mono tracking-tight">2 Pairs</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">High-liquidity 120-day daily OHLCV series for trend evaluation.</p>
            </div>
            <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 space-y-1.5 shadow-xl shadow-black/40">
              <span className="text-xs text-slate-400 uppercase font-mono tracking-wider">MCX Commodities</span>
              <div className="text-2xl font-bold text-white font-mono tracking-tight">2 Commodities</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">Gold & Crude Oil series with ATR volatility swings.</p>
            </div>
          </div>

          <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] rounded-2xl overflow-hidden shadow-xl shadow-black/40">
            <div className="px-6 py-4 border-b border-white/[0.06] flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Table className="w-4 h-4 text-cyan-400" />
                Available Pre-calibrated Demo Datasets
              </h2>
              <span className="text-xs text-slate-400 font-mono">Status: Ready for Analysis</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-panel-subtle text-slate-400 border-b border-border uppercase font-mono text-[10px]">
                  <tr>
                    <th className="px-5 py-3">Symbol</th>
                    <th className="px-5 py-3">Instrument Name</th>
                    <th className="px-5 py-3">Market</th>
                    <th className="px-5 py-3">Candle Count</th>
                    <th className="px-5 py-3">Timeframe</th>
                    <th className="px-5 py-3">Provider</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 text-slate-300">
                  {PRELOADED_DATASETS.map((item) => (
                    <tr key={item.symbol} className="hover:bg-panel-subtle/50 transition-colors">
                      <td className="px-5 py-3 font-mono font-bold text-white">{item.symbol}</td>
                      <td className="px-5 py-3">{item.name}</td>
                      <td className="px-5 py-3">
                        <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-800 border border-slate-700">
                          {item.market}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-mono text-emerald-400">{item.candles} candles</td>
                      <td className="px-5 py-3 font-mono">{item.tf}</td>
                      <td className="px-5 py-3">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/30">
                          LOCAL_MOCK_ENGINE
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: CSV Upload & Validation */}
      {activeTab === 'csv_upload' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upload & Form */}
          <div className="bg-panel border border-border rounded-xl p-5 space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border pb-3">
              <Upload className="w-4 h-4 text-accent" />
              Upload & Validate Custom Market CSV
            </h2>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Target Symbol</label>
                <input
                  type="text"
                  value={uploadSymbol}
                  onChange={(e) => setUploadSymbol(e.target.value)}
                  placeholder="e.g. RELIANCE, NIFTY"
                  className="w-full bg-panel-subtle border border-border rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-accent font-mono uppercase"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Market Category</label>
                <select
                  value={uploadMarket}
                  onChange={(e) => setUploadMarket(e.target.value as MarketType)}
                  className="w-full bg-panel-subtle border border-border rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-accent"
                >
                  <option value="NSE">NSE (Indian Equities)</option>
                  <option value="FOREX">FOREX (Currencies)</option>
                  <option value="MCX">MCX (Commodities)</option>
                </select>
              </div>
            </div>

            {/* File drop or select */}
            <div>
              <label className="text-[11px] font-medium text-slate-300 block mb-1">Upload CSV File</label>
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={handleFileUpload}
                className="w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-panel-subtle file:text-accent hover:file:bg-slate-800 cursor-pointer"
              />
            </div>

            {/* Direct CSV Text Editor */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-medium text-slate-300">CSV Raw Content</label>
                <span className="text-[10px] text-slate-500 font-mono">Required: date/time, open, high, low, close, volume</span>
              </div>
              <textarea
                value={csvText}
                onChange={(e) => setCsvText(e.target.value)}
                rows={8}
                className="w-full bg-panel-subtle border border-border rounded p-2.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-accent leading-relaxed"
                placeholder="Paste CSV rows here..."
              />
            </div>

            <button
              onClick={handleValidateAndUpload}
              disabled={uploading}
              className="w-full py-2.5 bg-accent hover:bg-accent-hover text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm"
            >
              {uploading ? (
                <>
                  <LoadingSpinner size="sm" />
                  Validating & Ingesting Dataset...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  Validate & Ingest CSV Data
                </>
              )}
            </button>
          </div>

          {/* Validation Report & Dataset List */}
          <div className="space-y-6">
            {/* Validation Outcome Report */}
            {uploadResult ? (
              <div className="bg-panel border border-border rounded-xl p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    {uploadResult.is_valid ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-rose-400" />
                    )}
                    Validation Outcome Report
                  </h3>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${
                      uploadResult.is_valid
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    }`}
                  >
                    {uploadResult.is_valid ? 'PASSED CONSISTENCY CHECKS' : 'VALIDATION FAILED'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-panel-subtle p-2.5 rounded border border-border">
                    <span className="text-slate-400 block text-[10px]">Total Parsed Rows</span>
                    <span className="font-mono text-white font-bold">{uploadResult.total_rows}</span>
                  </div>
                  <div className="bg-panel-subtle p-2.5 rounded border border-border">
                    <span className="text-slate-400 block text-[10px]">Valid OHLC Candles</span>
                    <span className="font-mono text-emerald-400 font-bold">{uploadResult.candles?.length || 0}</span>
                  </div>
                </div>

                {uploadResult.errors && uploadResult.errors.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-semibold text-rose-400 block">Errors Detected:</span>
                    <ul className="space-y-1 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded p-2.5 font-mono">
                      {uploadResult.errors.map((err, i) => (
                        <li key={i}>• {err}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {uploadResult.warnings && uploadResult.warnings.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-semibold text-amber-400 block">Warnings:</span>
                    <ul className="space-y-1 text-xs text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded p-2.5 font-mono">
                      {uploadResult.warnings.map((w, i) => (
                        <li key={i}>• {w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-panel border border-border rounded-xl p-5 space-y-2 text-xs text-slate-400">
                <h3 className="font-bold text-white flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-accent" /> CSV Validation Guardrails
                </h3>
                <p className="text-[11px] leading-relaxed">
                  The local CSV parser enforces strict deterministic sanity checks:
                </p>
                <ul className="list-disc list-inside space-y-1 text-[11px] pl-1 text-slate-300 font-mono">
                  <li>Required headers: <code>date/time, open, high, low, close, volume</code></li>
                  <li>Timestamp monotonicity & ISO 8601 / Unix parsing</li>
                  <li>Physical boundary check: <code>high &gt;= low</code>, <code>high &gt;= open</code>, <code>high &gt;= close</code></li>
                  <li>Strict non-negative prices and positive volume</li>
                </ul>
              </div>
            )}

            {/* Ingested Datasets Registry */}
            <div className="bg-panel border border-border rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-purple-400" />
                  Ingested Custom CSV Datasets ({datasets.length})
                </h3>
                <button onClick={fetchDatasets} className="text-slate-400 hover:text-white">
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>

              {datasets.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-4">No custom CSV datasets ingested yet.</p>
              ) : (
                <div className="space-y-2">
                  {datasets.map((ds) => (
                    <div
                      key={ds.dataset_id}
                      className="p-2.5 bg-panel-subtle border border-border rounded-lg flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-bold font-mono text-white block">{ds.symbol}</span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {ds.market} • {ds.total_rows} candles
                        </span>
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                        INGESTED & READY
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
