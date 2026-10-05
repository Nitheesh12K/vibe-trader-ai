import React, { useEffect, useRef } from 'react';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  ColorType,
  UTCTimestamp,
  IPriceLine,
  LineStyle,
} from 'lightweight-charts';
import {
  OHLCCandle,
  IndicatorsResponse,
  SupportResistanceZone,
} from '../../types/market';

export interface OverlayToggles {
  ema9: boolean;
  ema21: boolean;
  ema50: boolean;
  ema200: boolean;
  sma20: boolean;
  sma50: boolean;
  sma200: boolean;
  bollinger: boolean;
  srZones: boolean;
}

interface TechnicalAnalysisChartProps {
  candles: OHLCCandle[];
  indicators: IndicatorsResponse | null;
  zones: SupportResistanceZone[];
  overlays: OverlayToggles;
  showRSI: boolean;
  showMACD: boolean;
  loading: boolean;
}

export const TechnicalAnalysisChart: React.FC<TechnicalAnalysisChartProps> = ({
  candles,
  indicators,
  zones,
  overlays,
  showRSI,
  showMACD,
  loading,
}) => {
  // Main Candlestick Chart refs
  const mainContainerRef = useRef<HTMLDivElement>(null);
  const mainChartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  // Overlay series refs
  const ema9SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema200SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const sma20SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const sma50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const sma200SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbUpperRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbMiddleRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbLowerRef = useRef<ISeriesApi<'Line'> | null>(null);

  // S/R Price Lines ref
  const srPriceLinesRef = useRef<IPriceLine[]>([]);

  // RSI Sub-chart refs
  const rsiContainerRef = useRef<HTMLDivElement>(null);
  const rsiChartRef = useRef<IChartApi | null>(null);
  const rsiSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  // MACD Sub-chart refs
  const macdContainerRef = useRef<HTMLDivElement>(null);
  const macdChartRef = useRef<IChartApi | null>(null);
  const macdLineSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macdSignalSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macdHistSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  const isSyncingRef = useRef(false);

  // 1. Initialize Main Chart
  useEffect(() => {
    if (!mainContainerRef.current) return;

    const chart = createChart(mainContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#101726' },
        textColor: '#94A3B8',
        fontFamily: "'JetBrains Mono', 'Inter', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: 'rgba(31, 46, 69, 0.45)' },
        horzLines: { color: 'rgba(31, 46, 69, 0.45)' },
      },
      crosshair: {
        mode: 1,
        vertLine: { color: '#38BDF8', width: 1, style: 3, labelBackgroundColor: '#1F2E45' },
        horzLine: { color: '#38BDF8', width: 1, style: 3, labelBackgroundColor: '#1F2E45' },
      },
      timeScale: {
        borderColor: '#1F2E45',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#1F2E45',
        scaleMargins: { top: 0.08, bottom: 0.2 },
      },
      autoSize: true,
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10B981',
      downColor: '#F43F5E',
      borderVisible: false,
      wickUpColor: '#10B981',
      wickDownColor: '#F43F5E',
    });

    const volumeSeries = chart.addHistogramSeries({
      color: '#38BDF8',
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    });

    // Create indicator overlay line series
    ema9SeriesRef.current = chart.addLineSeries({ color: '#38BDF8', lineWidth: 1, title: 'EMA 9' });
    ema21SeriesRef.current = chart.addLineSeries({ color: '#F59E0B', lineWidth: 1, title: 'EMA 21' });
    ema50SeriesRef.current = chart.addLineSeries({ color: '#A855F7', lineWidth: 1, title: 'EMA 50' });
    ema200SeriesRef.current = chart.addLineSeries({ color: '#E2E8F0', lineWidth: 2, title: 'EMA 200' });
    sma20SeriesRef.current = chart.addLineSeries({ color: '#10B981', lineWidth: 1, title: 'SMA 20' });
    sma50SeriesRef.current = chart.addLineSeries({ color: '#EAB308', lineWidth: 1, title: 'SMA 50' });
    sma200SeriesRef.current = chart.addLineSeries({ color: '#EF4444', lineWidth: 2, title: 'SMA 200' });

    bbUpperRef.current = chart.addLineSeries({ color: '#6366F1', lineWidth: 1, title: 'BB Upper' });
    bbMiddleRef.current = chart.addLineSeries({ color: '#818CF8', lineWidth: 1, lineStyle: LineStyle.Dotted, title: 'BB Mid' });
    bbLowerRef.current = chart.addLineSeries({ color: '#6366F1', lineWidth: 1, title: 'BB Lower' });

    mainChartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // Sync time scale with RSI & MACD
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (isSyncingRef.current || !range) return;
      isSyncingRef.current = true;
      if (rsiChartRef.current) rsiChartRef.current.timeScale().setVisibleLogicalRange(range);
      if (macdChartRef.current) macdChartRef.current.timeScale().setVisibleLogicalRange(range);
      isSyncingRef.current = false;
    });

    const handleResize = () => {
      if (mainContainerRef.current && mainChartRef.current) {
        mainChartRef.current.applyOptions({
          width: mainContainerRef.current.clientWidth,
          height: mainContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      mainChartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []);

  // 2. Initialize RSI Sub-chart when showRSI is true
  useEffect(() => {
    if (!showRSI || !rsiContainerRef.current) {
      if (rsiChartRef.current) {
        rsiChartRef.current.remove();
        rsiChartRef.current = null;
        rsiSeriesRef.current = null;
      }
      return;
    }

    const chart = createChart(rsiContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0d131f' },
        textColor: '#94A3B8',
        fontFamily: "'JetBrains Mono', 'Inter', monospace",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: 'rgba(31, 46, 69, 0.35)' },
        horzLines: { color: 'rgba(31, 46, 69, 0.35)' },
      },
      timeScale: {
        borderColor: '#1F2E45',
        visible: false,
      },
      rightPriceScale: {
        borderColor: '#1F2E45',
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      autoSize: true,
    });

    const rsiSeries = chart.addLineSeries({
      color: '#C084FC',
      lineWidth: 2,
      title: 'RSI(14)',
    });

    // Reference lines for Overbought (70) and Oversold (30)
    rsiSeries.createPriceLine({
      price: 70,
      color: 'rgba(244, 63, 94, 0.65)',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: 'OB 70',
    });
    rsiSeries.createPriceLine({
      price: 30,
      color: 'rgba(16, 185, 129, 0.65)',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: 'OS 30',
    });
    rsiSeries.createPriceLine({
      price: 50,
      color: 'rgba(148, 163, 184, 0.35)',
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      axisLabelVisible: false,
      title: 'MID 50',
    });

    rsiChartRef.current = chart;
    rsiSeriesRef.current = rsiSeries;

    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (isSyncingRef.current || !range) return;
      isSyncingRef.current = true;
      if (mainChartRef.current) mainChartRef.current.timeScale().setVisibleLogicalRange(range);
      if (macdChartRef.current) macdChartRef.current.timeScale().setVisibleLogicalRange(range);
      isSyncingRef.current = false;
    });

    return () => {
      chart.remove();
      rsiChartRef.current = null;
      rsiSeriesRef.current = null;
    };
  }, [showRSI]);

  // 3. Initialize MACD Sub-chart when showMACD is true
  useEffect(() => {
    if (!showMACD || !macdContainerRef.current) {
      if (macdChartRef.current) {
        macdChartRef.current.remove();
        macdChartRef.current = null;
        macdLineSeriesRef.current = null;
        macdSignalSeriesRef.current = null;
        macdHistSeriesRef.current = null;
      }
      return;
    }

    const chart = createChart(macdContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0d131f' },
        textColor: '#94A3B8',
        fontFamily: "'JetBrains Mono', 'Inter', monospace",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: 'rgba(31, 46, 69, 0.35)' },
        horzLines: { color: 'rgba(31, 46, 69, 0.35)' },
      },
      timeScale: {
        borderColor: '#1F2E45',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#1F2E45',
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      autoSize: true,
    });

    const histSeries = chart.addHistogramSeries({
      color: '#10B981',
      title: 'Hist',
    });
    const macdLine = chart.addLineSeries({
      color: '#38BDF8',
      lineWidth: 1,
      title: 'MACD',
    });
    const signalLine = chart.addLineSeries({
      color: '#F59E0B',
      lineWidth: 1,
      title: 'Signal',
    });

    macdChartRef.current = chart;
    macdHistSeriesRef.current = histSeries;
    macdLineSeriesRef.current = macdLine;
    macdSignalSeriesRef.current = signalLine;

    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (isSyncingRef.current || !range) return;
      isSyncingRef.current = true;
      if (mainChartRef.current) mainChartRef.current.timeScale().setVisibleLogicalRange(range);
      if (rsiChartRef.current) rsiChartRef.current.timeScale().setVisibleLogicalRange(range);
      isSyncingRef.current = false;
    });

    return () => {
      chart.remove();
      macdChartRef.current = null;
      macdHistSeriesRef.current = null;
      macdLineSeriesRef.current = null;
      macdSignalSeriesRef.current = null;
    };
  }, [showMACD]);

  // 4. Update Candlesticks and Volume
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current || candles.length === 0) return;

    try {
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
        color: c.close >= c.open ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)',
      }));

      candleSeriesRef.current.setData(formattedCandles);
      volumeSeriesRef.current.setData(formattedVolumes);

      if (mainChartRef.current) {
        mainChartRef.current.timeScale().fitContent();
      }
    } catch (err) {
      console.error('Error applying candlestick data:', err);
    }
  }, [candles]);

  // 5. Update Overlay Series (EMAs, SMAs, Bollinger)
  useEffect(() => {
    if (!indicators) return;

    const setLineData = (series: ISeriesApi<'Line'> | null, points: { time: number; value: number | null }[], enabled: boolean) => {
      if (!series) return;
      if (!enabled) {
        series.setData([]);
        return;
      }
      const valid = points
        .filter((p) => p.value !== null && p.value !== undefined && !isNaN(p.value))
        .map((p) => ({ time: p.time as UTCTimestamp, value: p.value as number }));
      series.setData(valid);
    };

    setLineData(ema9SeriesRef.current, indicators.ema_9, overlays.ema9);
    setLineData(ema21SeriesRef.current, indicators.ema_21, overlays.ema21);
    setLineData(ema50SeriesRef.current, indicators.ema_50, overlays.ema50);
    setLineData(ema200SeriesRef.current, indicators.ema_200, overlays.ema200);

    setLineData(sma20SeriesRef.current, indicators.sma_20, overlays.sma20);
    setLineData(sma50SeriesRef.current, indicators.sma_50, overlays.sma50);
    setLineData(sma200SeriesRef.current, indicators.sma_200, overlays.sma200);

    // Bollinger
    if (bbUpperRef.current && bbMiddleRef.current && bbLowerRef.current) {
      if (!overlays.bollinger) {
        bbUpperRef.current.setData([]);
        bbMiddleRef.current.setData([]);
        bbLowerRef.current.setData([]);
      } else {
        const uValid = indicators.bollinger
          .filter((p) => p.upper !== null && !isNaN(p.upper!))
          .map((p) => ({ time: p.time as UTCTimestamp, value: p.upper as number }));
        const mValid = indicators.bollinger
          .filter((p) => p.middle !== null && !isNaN(p.middle!))
          .map((p) => ({ time: p.time as UTCTimestamp, value: p.middle as number }));
        const lValid = indicators.bollinger
          .filter((p) => p.lower !== null && !isNaN(p.lower!))
          .map((p) => ({ time: p.time as UTCTimestamp, value: p.lower as number }));

        bbUpperRef.current.setData(uValid);
        bbMiddleRef.current.setData(mValid);
        bbLowerRef.current.setData(lValid);
      }
    }
  }, [indicators, overlays]);

  // 6. Update Support and Resistance Price Lines
  useEffect(() => {
    if (!candleSeriesRef.current) return;

    // Clean up previous lines
    srPriceLinesRef.current.forEach((line) => {
      try {
        candleSeriesRef.current?.removePriceLine(line);
      } catch (e) {
        // ignore
      }
    });
    srPriceLinesRef.current = [];

    if (!overlays.srZones || !zones || zones.length === 0) return;

    zones.forEach((z) => {
      const isSupport = z.zone_type === 'Support';
      const color = isSupport ? '#10B981' : '#F43F5E';
      const style = z.strength === 'Strong' ? LineStyle.Solid : LineStyle.Dashed;
      const width = z.strength === 'Strong' ? 2 : 1;

      const line = candleSeriesRef.current?.createPriceLine({
        price: z.price,
        color: color,
        lineWidth: width,
        lineStyle: style,
        axisLabelVisible: true,
        title: `${z.zone_type.toUpperCase()} (${z.touches}x)`,
      });

      if (line) {
        srPriceLinesRef.current.push(line);
      }
    });
  }, [zones, overlays.srZones]);

  // 7. Update RSI Series
  useEffect(() => {
    if (!showRSI || !rsiSeriesRef.current || !indicators) return;
    const rsiPoints = indicators.rsi
      .filter((p) => p.value !== null && !isNaN(p.value!))
      .map((p) => ({ time: p.time as UTCTimestamp, value: p.value as number }));
    rsiSeriesRef.current.setData(rsiPoints);

    if (rsiChartRef.current && mainChartRef.current) {
      const range = mainChartRef.current.timeScale().getVisibleLogicalRange();
      if (range) rsiChartRef.current.timeScale().setVisibleLogicalRange(range);
    }
  }, [showRSI, indicators]);

  // 8. Update MACD Series
  useEffect(() => {
    if (!showMACD || !macdLineSeriesRef.current || !macdSignalSeriesRef.current || !macdHistSeriesRef.current || !indicators) return;

    const macdPts = indicators.macd
      .filter((p) => p.macd !== null && !isNaN(p.macd!))
      .map((p) => ({ time: p.time as UTCTimestamp, value: p.macd as number }));
    const signalPts = indicators.macd
      .filter((p) => p.signal !== null && !isNaN(p.signal!))
      .map((p) => ({ time: p.time as UTCTimestamp, value: p.signal as number }));
    const histPts = indicators.macd
      .filter((p) => p.histogram !== null && !isNaN(p.histogram!))
      .map((p) => ({
        time: p.time as UTCTimestamp,
        value: p.histogram as number,
        color: (p.histogram || 0) >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(244, 63, 94, 0.7)',
      }));

    macdLineSeriesRef.current.setData(macdPts);
    macdSignalSeriesRef.current.setData(signalPts);
    macdHistSeriesRef.current.setData(histPts);

    if (macdChartRef.current && mainChartRef.current) {
      const range = mainChartRef.current.timeScale().getVisibleLogicalRange();
      if (range) macdChartRef.current.timeScale().setVisibleLogicalRange(range);
    }
  }, [showMACD, indicators]);

  return (
    <div className="flex flex-col w-full h-full relative select-none">
      {loading && (
        <div className="absolute inset-0 z-20 bg-panel/70 backdrop-blur-sm flex items-center justify-center">
          <div className="flex items-center gap-2 text-xs font-mono text-accent">
            <span className="w-2.5 h-2.5 rounded-full bg-accent animate-ping" />
            Computing indicators & plotting patterns...
          </div>
        </div>
      )}

      {/* Main Candlestick Chart */}
      <div className={`relative w-full ${showRSI && showMACD ? 'h-[280px]' : showRSI || showMACD ? 'h-[340px]' : 'h-[440px]'}`}>
        <div ref={mainContainerRef} className="w-full h-full" />
      </div>

      {/* RSI Sub-Chart */}
      {showRSI && (
        <div className="border-t border-border flex flex-col h-[110px] relative bg-panel-subtle/30">
          <div className="absolute top-1 left-3 z-10 text-[10px] font-mono text-purple-400 font-semibold flex items-center gap-2">
            <span>RSI (14)</span>
            <span className="text-slate-400 font-normal">70/30 OB/OS Levels</span>
          </div>
          <div ref={rsiContainerRef} className="w-full h-full" />
        </div>
      )}

      {/* MACD Sub-Chart */}
      {showMACD && (
        <div className="border-t border-border flex flex-col h-[130px] relative bg-panel-subtle/30">
          <div className="absolute top-1 left-3 z-10 text-[10px] font-mono text-sky-400 font-semibold flex items-center gap-2">
            <span>MACD (12, 26, 9)</span>
            <span className="text-slate-400 font-normal">MACD Line / Signal / Histogram</span>
          </div>
          <div ref={macdContainerRef} className="w-full h-full" />
        </div>
      )}
    </div>
  );
};
