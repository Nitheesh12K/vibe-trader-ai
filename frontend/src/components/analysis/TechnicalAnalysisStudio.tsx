import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Layers,
  Sliders,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Info,
  ShieldAlert,
  Compass,
  CheckCircle2,
  ChevronDown,
  BarChart2,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  TechnicalAnalysisFullBundle,
  MarketType,
  PatternItem,
  SupportResistanceZone,
} from '../../types/market';
import { TechnicalAnalysisChart, OverlayToggles } from './TechnicalAnalysisChart';
import { Badge } from '../common/Badge';

interface TechnicalAnalysisStudioProps {
  initialSymbol?: string;
  initialMarket?: MarketType;
}

const MARKET_SYMBOLS: Record<MarketType, { symbol: string; label: string }[]> = {
  FOREX: [
    { symbol: 'EUR/USD', label: 'EUR/USD' },
    { symbol: 'GBP/USD', label: 'GBP/USD' },
    { symbol: 'USD/JPY', label: 'USD/JPY' },
    { symbol: 'AUD/USD', label: 'AUD/USD' },
    { symbol: 'USD/CAD', label: 'USD/CAD' },
  ],
  NSE: [
    { symbol: 'NIFTY 50', label: 'NIFTY 50' },
    { symbol: 'RELIANCE.NS', label: 'RELIANCE' },
    { symbol: 'TCS.NS', label: 'TCS' },
    { symbol: 'INFY.NS', label: 'INFOSYS' },
    { symbol: 'HDFCBANK.NS', label: 'HDFC BANK' },
  ],
  MCX: [
    { symbol: 'GOLD', label: 'GOLD' },
    { symbol: 'SILVER', label: 'SILVER' },
    { symbol: 'CRUDEOIL', label: 'CRUDE OIL' },
    { symbol: 'COPPER', label: 'COPPER' },
    { symbol: 'NATURALGAS', label: 'NATURAL GAS' },
  ],
};

const TIMEFRAMES = ['1m', '5m', '15m', '1h', '1D'];

export const TechnicalAnalysisStudio: React.FC<TechnicalAnalysisStudioProps> = ({
  initialSymbol = 'EUR/USD',
  initialMarket = 'FOREX',
}) => {
  const [market, setMarket] = useState<MarketType>(initialMarket);
  const [symbol, setSymbol] = useState<string>(initialSymbol);
  const [timeframe, setTimeframe] = useState<string>('1D');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<TechnicalAnalysisFullBundle | null>(null);
  const [showSettings, setShowSettings] = useState<boolean>(false);

  // Indicator Settings
  const [rsiPeriod, setRsiPeriod] = useState<number>(14);
  const [macdFast, setMacdFast] = useState<number>(12);
  const [macdSlow, setMacdSlow] = useState<number>(26);
  const [macdSignal, setMacdSignal] = useState<number>(9);
  const [tolerance, setTolerance] = useState<number>(0.008);

  // Overlay toggles
  const [overlays, setOverlays] = useState<OverlayToggles>({
    ema9: true,
    ema21: true,
    ema50: false,
    ema200: true,
    sma20: false,
    sma50: false,
    sma200: false,
    bollinger: true,
    srZones: true,
  });

  const [showRSI, setShowRSI] = useState<boolean>(true);
  const [showMACD, setShowMACD] = useState<boolean>(true);

  // Fetch full analysis bundle
  const loadAnalysis = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const bundle = await api.getTechnicalAnalysisBundle(symbol, timeframe, market, {
        rsiPeriod,
        macdFast,
        macdSlow,
        macdSignal,
        tolerance,
      });
      setData(bundle);
    } catch (err: any) {
      console.error('Failed to load technical analysis bundle:', err);
      setError(err.message || 'Unable to compute technical indicators.');
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe, market, rsiPeriod, macdFast, macdSlow, macdSignal, tolerance]);

  useEffect(() => {
    loadAnalysis();
  }, [loadAnalysis]);

  // Handle market switch
  const handleMarketChange = (newMarket: MarketType) => {
    setMarket(newMarket);
    const available = MARKET_SYMBOLS[newMarket];
    if (available && available.length > 0) {
      setSymbol(available[0].symbol);
    }
  };

  const toggleOverlay = (key: keyof OverlayToggles) => {
    setOverlays((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const currentPrice = data?.candles && data.candles.length > 0 ? data.candles[data.candles.length - 1].close : 0;

  return (
    <div className="flex flex-col gap-4 p-4 lg:p-6 w-full max-w-[1680px] mx-auto text-slate-200">
      {/* 1. Header Toolbar */}
      <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2.5 pr-4 border-r border-white/[0.08]">
            <div className="p-2 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-cyan-400">
              <Activity className="w-5 h-5 animate-pulse" />
            </div>
            <span className="font-mono text-lg font-bold tracking-wide text-white">
              Technical Analysis Studio
            </span>
          </div>

          <Badge variant="demo" size="sm">
            DEMO DATA (Simulated)
          </Badge>

          <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-[#121B2F] text-slate-300 border border-white/[0.08]">
            PANDAS / NUMPY ENGINE
          </span>

          <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-[#121B2F] text-slate-300 border border-white/[0.08]">
            RULE-BASED PATTERNS
          </span>
        </div>

        {/* Global Controls & Refresh */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-mono rounded-xl border transition-all ${
              showSettings
                ? 'bg-cyan-500 text-white font-bold shadow-md shadow-cyan-500/20'
                : 'bg-[#080D1A] hover:bg-white/[0.04] border-white/[0.08] text-slate-300'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Parameters & Layers</span>
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showSettings ? 'rotate-180' : ''}`} />
          </button>

          <button
            onClick={loadAnalysis}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-xs font-mono rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 font-bold transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Analysis</span>
          </button>
        </div>
      </div>

      {/* 2. Market, Symbol, and Timeframe Selector Bar */}
      <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-3">
        {/* Market Category */}
        <div className="flex items-center gap-1 bg-[#080D1A] p-1 rounded-xl border border-white/[0.08]">
          {(['FOREX', 'NSE', 'MCX'] as MarketType[]).map((m) => (
            <button
              key={m}
              onClick={() => handleMarketChange(m)}
              className={`px-3.5 py-1 text-xs font-mono font-bold rounded-lg transition-all ${
                market === m
                  ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {m}
            </button>
          ))}
        </div>

        {/* Symbol Quick Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto py-1">
          {MARKET_SYMBOLS[market].map((item) => (
            <button
              key={item.symbol}
              onClick={() => setSymbol(item.symbol)}
              className={`px-3 py-1 text-xs font-mono rounded-lg border transition-all ${
                symbol === item.symbol
                  ? 'bg-cyan-500/15 text-cyan-400 border-cyan-500/40 font-bold shadow-sm'
                  : 'bg-[#080D1A] hover:bg-white/[0.04] text-slate-400 border-white/[0.06] hover:text-white'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center gap-1 bg-[#080D1A] p-1 rounded-xl border border-white/[0.08]">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-2.5 py-1 text-xs font-mono rounded-lg transition-all ${
                timeframe === tf
                  ? 'bg-cyan-500 text-white font-bold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Collapsible Indicator Settings & Layer Toggles */}
      {showSettings && (
        <div className="bg-panel border border-border rounded-lg p-4 flex flex-col gap-4 animate-in fade-in duration-150">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <span className="text-xs font-mono font-bold text-slate-100 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-accent" />
              Chart Overlays & Indicator Configuration
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Changes update calculations dynamically
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
            {/* Moving Averages Toggles */}
            <div className="flex flex-col gap-2 p-3 bg-background/60 rounded border border-border">
              <span className="text-slate-300 font-semibold text-[11px] uppercase tracking-wider">
                Moving Averages
              </span>
              <div className="grid grid-cols-2 gap-2">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={overlays.ema9}
                    onChange={() => toggleOverlay('ema9')}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-[#38BDF8]">EMA 9</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={overlays.ema21}
                    onChange={() => toggleOverlay('ema21')}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-[#F59E0B]">EMA 21</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={overlays.ema50}
                    onChange={() => toggleOverlay('ema50')}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-[#A855F7]">EMA 50</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={overlays.ema200}
                    onChange={() => toggleOverlay('ema200')}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-[#E2E8F0]">EMA 200</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={overlays.sma20}
                    onChange={() => toggleOverlay('sma20')}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-[#10B981]">SMA 20</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={overlays.sma50}
                    onChange={() => toggleOverlay('sma50')}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-[#EAB308]">SMA 50</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={overlays.sma200}
                    onChange={() => toggleOverlay('sma200')}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-[#EF4444]">SMA 200</span>
                </label>
              </div>
            </div>

            {/* Bands & Structural Overlays */}
            <div className="flex flex-col gap-2 p-3 bg-background/60 rounded border border-border">
              <span className="text-slate-300 font-semibold text-[11px] uppercase tracking-wider">
                Bands & Price Levels
              </span>
              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={overlays.bollinger}
                    onChange={() => toggleOverlay('bollinger')}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-[#818CF8]">Bollinger Bands (20, 2)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={overlays.srZones}
                    onChange={() => toggleOverlay('srZones')}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-emerald-400">Support / Resistance Lines</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={showRSI}
                    onChange={(e) => setShowRSI(e.target.checked)}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-purple-400">RSI Oscillator Sub-Panel</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={showMACD}
                    onChange={(e) => setShowMACD(e.target.checked)}
                    className="rounded bg-panel border-border text-accent focus:ring-0"
                  />
                  <span className="text-sky-400">MACD Oscillator Sub-Panel</span>
                </label>
              </div>
            </div>

            {/* Indicator Parameters */}
            <div className="flex flex-col gap-2 p-3 bg-background/60 rounded border border-border">
              <span className="text-slate-300 font-semibold text-[11px] uppercase tracking-wider">
                RSI & S/R Settings
              </span>
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">RSI Period:</span>
                  <input
                    type="number"
                    min={2}
                    max={50}
                    value={rsiPeriod}
                    onChange={(e) => setRsiPeriod(Number(e.target.value) || 14)}
                    className="w-16 px-2 py-0.5 rounded bg-panel border border-border text-right text-slate-200"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">S/R Cluster Tol (%):</span>
                  <input
                    type="number"
                    min={0.1}
                    max={5.0}
                    step={0.1}
                    value={(tolerance * 100).toFixed(1)}
                    onChange={(e) => setTolerance((parseFloat(e.target.value) || 0.8) / 100)}
                    className="w-16 px-2 py-0.5 rounded bg-panel border border-border text-right text-slate-200"
                  />
                </div>
              </div>
            </div>

            {/* MACD Parameters */}
            <div className="flex flex-col gap-2 p-3 bg-background/60 rounded border border-border">
              <span className="text-slate-300 font-semibold text-[11px] uppercase tracking-wider">
                MACD Parameters
              </span>
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Fast EMA:</span>
                  <input
                    type="number"
                    min={2}
                    max={30}
                    value={macdFast}
                    onChange={(e) => setMacdFast(Number(e.target.value) || 12)}
                    className="w-16 px-2 py-0.5 rounded bg-panel border border-border text-right text-slate-200"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Slow EMA:</span>
                  <input
                    type="number"
                    min={10}
                    max={100}
                    value={macdSlow}
                    onChange={(e) => setMacdSlow(Number(e.target.value) || 26)}
                    className="w-16 px-2 py-0.5 rounded bg-panel border border-border text-right text-slate-200"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Signal SMA:</span>
                  <input
                    type="number"
                    min={2}
                    max={30}
                    value={macdSignal}
                    onChange={(e) => setMacdSignal(Number(e.target.value) || 9)}
                    className="w-16 px-2 py-0.5 rounded bg-panel border border-border text-right text-slate-200"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-xs font-mono text-rose-400 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            {error}
          </span>
          <button onClick={loadAnalysis} className="underline hover:text-rose-300">
            Retry
          </button>
        </div>
      )}

      {/* 4. Main Chart Canvas Card */}
      <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl overflow-hidden flex flex-col">
        {/* Chart Header Bar */}
        <div className="px-5 py-3 border-b border-white/[0.08] bg-[#0A0F1D]/80 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <BarChart2 className="w-4 h-4" />
            </div>
            <span className="font-mono text-base font-bold text-white tracking-wide">{symbol}</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#121B2F] text-slate-300 border border-white/[0.08]">
              {market} • {timeframe}
            </span>
            {currentPrice > 0 && (
              <span className="font-mono text-xs text-slate-400 pl-3 border-l border-white/[0.08]">
                Price: <strong className="text-white font-bold">{currentPrice.toFixed(4)}</strong>
              </span>
            )}
          </div>

          <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
            {data?.summary?.regime && (
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#121B2F] border border-white/[0.08] text-slate-200">
                <Compass className="w-3.5 h-3.5 text-cyan-400" />
                Regime: <strong className="text-cyan-400 font-bold">{data.summary.regime}</strong>
              </span>
            )}
          </div>
        </div>

        {/* Chart Viewport */}
        <div className="w-full min-h-[440px] bg-[#080D1A]">
          <TechnicalAnalysisChart
            candles={data?.candles || []}
            indicators={data?.indicators || null}
            zones={data?.support_resistance?.zones || []}
            overlays={overlays}
            showRSI={showRSI}
            showMACD={showMACD}
            loading={loading}
          />
        </div>

        {/* Chart Safety Footer */}
        <div className="px-5 py-2.5 border-t border-white/[0.08] bg-[#0A0F1D]/80 text-[10px] font-mono text-slate-400 flex flex-wrap items-center justify-between gap-2">
          <span className="flex items-center gap-1.5 text-amber-400/90 font-medium">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            DEMO SIMULATION: Computed using Python Pandas & NumPy on demo candle stream. No real trades placed.
          </span>
          <span className="text-slate-500">Lightweight Charts v4 Engine</span>
        </div>
      </div>

      {/* 5. Analysis Details Grid: Summary, S/R Zones, Patterns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Column 1: Factual Rule-Based Summary (5 cols) */}
        <div className="lg:col-span-5 bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 flex flex-col gap-4 shadow-md">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                <Compass className="w-4 h-4" />
              </div>
              <span className="font-mono text-sm font-bold text-white">Factual Technical Summary</span>
            </div>
            {data?.summary?.regime && (
              <Badge
                variant={
                  data.summary.regime.toLowerCase().includes('bullish')
                    ? 'bullish'
                    : data.summary.regime.toLowerCase().includes('bearish')
                    ? 'bearish'
                    : 'neutral'
                }
              >
                {data.summary.regime}
              </Badge>
            )}
          </div>

          {/* Key Takeaways */}
          <div className="flex flex-col gap-2.5">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
              Key Technical Observations
            </span>
            <ul className="flex flex-col gap-2">
              {data?.summary?.key_takeaways?.map((takeaway, idx) => (
                <li key={idx} className="text-xs font-mono text-slate-300 flex items-start gap-2 bg-[#080D1A]/50 p-2.5 rounded-xl border border-white/[0.04]">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{takeaway}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Conflicting Signals Warning Callout */}
          {data?.summary?.conflicts && data.summary.conflicts.length > 0 && (
            <div className="p-3.5 bg-amber-500/10 border border-amber-500/25 rounded-xl flex flex-col gap-2 text-xs font-mono">
              <div className="flex items-center gap-2 text-amber-400 font-bold">
                <AlertTriangle className="w-4 h-4" />
                <span>Conflicting Signals Detected</span>
              </div>
              <ul className="flex flex-col gap-1 text-slate-300 pl-5 list-disc">
                {data.summary.conflicts.map((conflict, idx) => (
                  <li key={idx}>{conflict}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Indicator Breakdowns */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs font-mono pt-1">
            <div className="p-3 bg-[#080D1A]/80 rounded-xl border border-white/[0.06] flex flex-col gap-1">
              <span className="text-purple-400 font-bold text-[11px]">RSI Assessment</span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {data?.summary?.rsi_summary || 'Calculating RSI...'}
              </p>
            </div>

            <div className="p-3 bg-[#080D1A]/80 rounded-xl border border-white/[0.06] flex flex-col gap-1">
              <span className="text-cyan-400 font-bold text-[11px]">MACD Impulse</span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {data?.summary?.macd_summary || 'Calculating MACD...'}
              </p>
            </div>

            <div className="p-3 bg-[#080D1A]/80 rounded-xl border border-white/[0.06] flex flex-col gap-1">
              <span className="text-amber-400 font-bold text-[11px]">Moving Averages</span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {data?.summary?.ma_summary || 'Calculating Moving Averages...'}
              </p>
            </div>

            <div className="p-3 bg-[#080D1A]/80 rounded-xl border border-white/[0.06] flex flex-col gap-1">
              <span className="text-emerald-400 font-bold text-[11px]">Volatility & Dispersion</span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {data?.summary?.volatility_summary || 'Calculating ATR...'}
              </p>
            </div>
          </div>

          {/* Mandatory Disclaimer */}
          <div className="mt-auto p-3 bg-[#080D1A]/60 rounded-xl border border-white/[0.06] text-[10px] font-mono text-slate-400 leading-relaxed">
            <span className="text-amber-400/90 font-bold">DISCLAIMER: </span>
            {data?.summary?.disclaimer}
          </div>
        </div>

        {/* Column 2: Support and Resistance Zones (3 cols) */}
        <div className="lg:col-span-3 bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 flex flex-col gap-4 shadow-md">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <Layers className="w-4 h-4" />
              </div>
              <span className="font-mono text-sm font-bold text-white">S/R Price Zones</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400 bg-[#080D1A] px-2 py-0.5 rounded-md border border-white/[0.06]">
              Tol: {(tolerance * 100).toFixed(1)}%
            </span>
          </div>

          {/* Current Price Banner */}
          <div className="p-3 bg-[#080D1A] rounded-xl border border-white/[0.06] flex items-center justify-between font-mono text-xs">
            <span className="text-slate-400">Current Price</span>
            <span className="text-white font-bold">${currentPrice.toFixed(4)}</span>
          </div>

          {/* List of Zones */}
          <div className="flex flex-col gap-2 overflow-y-auto max-h-[380px] pr-1 scrollbar-thin">
            {(!data?.support_resistance?.zones || data.support_resistance.zones.length === 0) && (
              <div className="text-xs font-mono text-slate-500 text-center py-8">
                No swing pivot clusters identified in selected window.
              </div>
            )}

            {data?.support_resistance?.zones?.map((zone, idx) => {
              const isSupport = zone.zone_type === 'Support';
              const distPct =
                currentPrice > 0
                  ? ((zone.price - currentPrice) / currentPrice) * 100
                  : 0;

              return (
                <div
                  key={idx}
                  className={`p-3 rounded-xl border flex flex-col gap-1.5 font-mono text-xs transition-colors ${
                    isSupport
                      ? 'bg-emerald-500/[0.07] border-emerald-500/25 hover:border-emerald-500/40'
                      : 'bg-rose-500/[0.07] border-rose-500/25 hover:border-rose-500/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white flex items-center gap-1.5">
                      {isSupport ? (
                        <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
                      )}
                      ${zone.price.toFixed(4)}
                    </span>
                    <Badge variant={isSupport ? 'bullish' : 'bearish'} size="sm">
                      {zone.zone_type.toUpperCase()}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className={distPct >= 0 ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                      {distPct >= 0 ? `+${distPct.toFixed(2)}%` : `${distPct.toFixed(2)}%`}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="px-1.5 py-0.5 rounded bg-[#080D1A] border border-white/[0.06] text-[10px]">
                        {zone.touches} touches
                      </span>
                      <span
                        className={`text-[10px] font-bold ${
                          zone.strength === 'Strong'
                            ? 'text-amber-400'
                            : zone.strength === 'Moderate'
                            ? 'text-cyan-400'
                            : 'text-slate-400'
                        }`}
                      >
                        {zone.strength}
                      </span>
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Column 3: Candlestick Patterns Detected (4 cols) */}
        <div className="lg:col-span-4 bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5 flex flex-col gap-4 shadow-md">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <TrendingUp className="w-4 h-4" />
              </div>
              <span className="font-mono text-sm font-bold text-white">Candlestick Patterns</span>
            </div>
            <Badge variant="neutral" size="sm">
              {data?.patterns?.total_detected || 0} Found
            </Badge>
          </div>

          <div className="flex flex-col gap-2.5 overflow-y-auto max-h-[420px] pr-1 scrollbar-thin">
            {(!data?.patterns?.patterns || data.patterns.patterns.length === 0) && (
              <div className="text-xs font-mono text-slate-500 text-center py-8">
                No classic reversal patterns identified in the examined candle sequence.
              </div>
            )}

            {data?.patterns?.patterns?.map((pattern: PatternItem, idx: number) => {
              const isBull = pattern.direction.toLowerCase() === 'bullish';
              const isBear = pattern.direction.toLowerCase() === 'bearish';

              return (
                <div
                  key={idx}
                  className="p-3.5 bg-[#080D1A]/80 border border-white/[0.06] rounded-xl flex flex-col gap-2 font-mono text-xs hover:border-cyan-500/30 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{pattern.pattern_name}</span>
                    <div className="flex items-center gap-1.5">
                      <Badge
                        variant={isBull ? 'bullish' : isBear ? 'bearish' : 'neutral'}
                        size="sm"
                      >
                        {pattern.direction}
                      </Badge>
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#121B2F] text-slate-300 border border-white/[0.06]">
                        {pattern.reliability}
                      </span>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
                    {pattern.explanation}
                  </p>

                  <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1.5 border-t border-white/[0.06]">
                    <span>Offset: Bar #{pattern.candle_index}</span>
                    <span>{new Date(pattern.time * 1000).toLocaleDateString()}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
