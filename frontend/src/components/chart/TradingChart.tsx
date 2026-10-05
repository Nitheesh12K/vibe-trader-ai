import React, { useEffect, useRef, useState } from 'react';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  ColorType,
  UTCTimestamp,
} from 'lightweight-charts';
import { BarChart3, Maximize2, ShieldAlert } from 'lucide-react';
import { InstrumentItem, OHLCCandle } from '../../types/market';
import { Badge } from '../common/Badge';

interface TradingChartProps {
  instrument: InstrumentItem | null;
  candles: OHLCCandle[];
  loading: boolean;
  timeframe: string;
  onTimeframeChange: (tf: string) => void;
}

const TIMEFRAMES = ['1m', '5m', '15m', '1h', '1D'];

export const TradingChart: React.FC<TradingChartProps> = ({
  instrument,
  candles,
  loading,
  timeframe,
  onTimeframeChange,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create TradingView lightweight chart instance
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#080D1A' },
        textColor: '#64748B',
        fontFamily: "'JetBrains Mono', 'Inter', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#0EA5E9',
          width: 1,
          style: 3,
          labelBackgroundColor: '#121B2F',
        },
        horzLine: {
          color: '#0EA5E9',
          width: 1,
          style: 3,
          labelBackgroundColor: '#121B2F',
        },
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        scaleMargins: {
          top: 0.1,
          bottom: 0.25,
        },
      },
      autoSize: true,
    });

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10B981',
      downColor: '#F43F5E',
      borderVisible: false,
      wickUpColor: '#10B981',
      wickDownColor: '#F43F5E',
    });

    // Add volume histogram series
    const volumeSeries = chart.addHistogramSeries({
      color: '#38BDF8',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // Set as overlay
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // Responsive resize handler
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []);

  // Update candle data when candles change
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current || candles.length === 0) {
      return;
    }

    try {
      // Sort candles chronologically
      const sorted = [...candles].sort((a, b) => a.time - b.time);

      const formattedCandles = sorted.map((c) => ({
        time: c.time as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));

      const formattedVolumes = sorted.map((c) => ({
        time: c.time as UTCTimestamp,
        value: c.volume || 1000,
        color: c.close >= c.open ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)',
      }));

      candleSeriesRef.current.setData(formattedCandles);
      volumeSeriesRef.current.setData(formattedVolumes);

      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
      }
    } catch (err) {
      console.error('Error applying chart data:', err);
    }
  }, [candles]);

  const lastCandle = candles.length > 0 ? candles[candles.length - 1] : null;
  const isUp = lastCandle ? lastCandle.close >= lastCandle.open : true;

  return (
    <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl flex flex-col h-[460px] overflow-hidden">
      {/* Top Chart Toolbar */}
      <div className="px-5 py-3 border-b border-white/[0.08] bg-[#0A0F1D]/80 backdrop-blur-md flex flex-wrap items-center justify-between gap-3 shrink-0">
        {/* Symbol Details */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <BarChart3 className="w-4 h-4" />
            </div>
            <span className="font-mono text-base font-bold text-white tracking-wide">
              {instrument?.symbol || 'DEMO CHART'}
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#121B2F] text-slate-300 border border-white/[0.08]">
              {instrument?.market || 'FOREX'}
            </span>
          </div>

          <Badge variant="demo" size="sm">
            SAMPLE OHLC
          </Badge>

          {instrument && (
            <div className="hidden sm:flex items-center gap-3 font-mono text-xs pl-3 border-l border-white/[0.08]">
              <span className="text-slate-400">
                Last:{' '}
                <strong className="text-white font-semibold">
                  {instrument.currency_symbol}
                  {instrument.last_price.toLocaleString()}
                </strong>
              </span>
              <span className={instrument.change >= 0 ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                {instrument.change >= 0 ? '+' : ''}
                {instrument.change_percent.toFixed(2)}%
              </span>
            </div>
          )}
        </div>

        {/* Timeframe Controls */}
        <div className="flex items-center gap-1 bg-[#080D1A] p-1 rounded-lg border border-white/[0.08]">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => onTimeframeChange(tf)}
              className={`px-2.5 py-1 text-xs font-mono rounded-md transition-all ${
                timeframe === tf
                  ? 'bg-cyan-500 text-white font-bold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Canvas Area */}
      <div className="relative flex-1 w-full h-full min-h-[360px] bg-[#080D1A]">
        {loading && (
          <div className="absolute inset-0 z-10 bg-[#080D1A]/80 backdrop-blur-sm flex items-center justify-center">
            <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 bg-[#0D1322] px-4 py-2 rounded-xl border border-cyan-500/30 shadow-lg">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              Loading {instrument?.symbol || ''} OHLC stream...
            </div>
          </div>
        )}
        <div ref={chartContainerRef} className="w-full h-full" />
      </div>

      {/* Chart Sub-footer with Safety Disclaimer */}
      <div className="px-5 py-2.5 border-t border-white/[0.08] bg-[#0A0F1D]/80 text-[10px] text-slate-400 font-mono flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-amber-400/90 font-medium">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          SIMULATION ENVIRONMENT: Candles are synthetic mock data for research and UI verification.
        </span>
        <span className="hidden md:inline text-slate-500">TradingView Lightweight Charts v4</span>
      </div>
    </div>
  );
};
