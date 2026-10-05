import React, { useState } from 'react';
import {
  Layers,
  Play,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Info,
  CheckSquare,
  Square,
  AlertCircle,
  Download,
  BarChart3,
  Calendar,
} from 'lucide-react';
import { api } from '../../services/api';
import { StrategyCompareResponseData, StrategyComparisonResultItem, NavTabId } from '../../types/market';

interface StrategyComparisonViewProps {
  onNavigate?: (tab: NavTabId, symbol?: string) => void;
}

const AVAILABLE_STRATEGIES = [
  { id: 'STRAT-EMA-CROSS', name: 'EMA Momentum Trend Following', desc: 'Fast & slow EMA cross with trend filter' },
  { id: 'STRAT-RSI-REV', name: 'RSI Mean Reversion', desc: 'Overbought / oversold reversal with confirmation' },
  { id: 'STRAT-MACD-MOM', name: 'MACD Multi-Timeframe Velocity', desc: 'Zero-line crossover and signal histogram momentum' },
  { id: 'STRAT-VWAP-TREND', name: 'VWAP Intraday Value Trend', desc: 'Institutional volume-weighted benchmark bias' },
  { id: 'STRAT-BB-REV', name: 'Bollinger Band Dynamic Reversal', desc: 'Standard deviation band rejection and mean return' },
  { id: 'STRAT-VOL-BREAKOUT', name: 'Volume-Confirmed Breakout', desc: 'Volume surge above 20-period moving average breakout' },
  { id: 'STRAT-MULTI-CONF', name: 'Multi-Indicator Confirmation', desc: 'Confluence across EMA, RSI, MACD, and Support zones' },
];

export const StrategyComparisonView: React.FC<StrategyComparisonViewProps> = ({ onNavigate }) => {
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([
    'STRAT-EMA-CROSS',
    'STRAT-RSI-REV',
  ]);
  const [symbol, setSymbol] = useState<string>('RELIANCE');
  const [market, setMarket] = useState<string>('NSE');
  const [timeframe, setTimeframe] = useState<string>('1D');
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<StrategyCompareResponseData | null>(null);
  const [activeTabStrategy, setActiveTabStrategy] = useState<string | null>(null);

  const toggleStrategy = (stratId: string) => {
    setSelectedStrategies((prev) => {
      if (prev.includes(stratId)) {
        if (prev.length <= 1) return prev; // Keep at least one
        return prev.filter((id) => id !== stratId);
      } else {
        if (prev.length >= 7) return prev; // Maximum 7
        return [...prev, stratId];
      }
    });
  };

  const handleRunComparison = async () => {
    try {
      setIsRunning(true);
      setError(null);
      const res = await api.compareStrategies({
        strategy_codes: selectedStrategies,
        symbol: symbol.trim().toUpperCase(),
        market,
        timeframe,
        initial_capital: initialCapital,
      });
      setComparisonData(res);
      if (res.strategies.length > 0) {
        setActiveTabStrategy(res.strategies[0].strategy_code);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute strategy comparison backtests.');
    } finally {
      setIsRunning(false);
    }
  };

  const activeStrategyTrades = comparisonData?.strategies.find(
    (s) => s.strategy_code === activeTabStrategy
  )?.trade_list || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-white/10 backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-white flex items-center gap-2">
              <span className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Layers className="w-5 h-5" />
              </span>
              Multi-Strategy Comparison
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Neutral Factual Backtests
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Simulate and contrast up to 7 rule-based algorithms side-by-side on identical historical data with zero bias.
          </p>
        </div>

        <button
          onClick={handleRunComparison}
          disabled={isRunning || selectedStrategies.length === 0}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-500 via-indigo-600 to-cyan-500 hover:from-purple-400 hover:to-cyan-400 text-white font-bold text-sm shadow-lg shadow-purple-500/25 transition disabled:opacity-50"
        >
          <Play className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          {isRunning ? 'Simulating Backtests...' : 'Run Side-by-Side Comparison'}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Strategy Selector (5 cols) */}
        <div className="lg:col-span-5 bg-slate-900/60 rounded-2xl border border-white/10 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-purple-400" />
              Select Strategies ({selectedStrategies.length}/7)
            </h3>
            <span className="text-[11px] font-mono text-slate-400">7 Prebuilt Catalog</span>
          </div>

          <div className="space-y-2">
            {AVAILABLE_STRATEGIES.map((strat) => {
              const isChecked = selectedStrategies.includes(strat.id);
              return (
                <div
                  key={strat.id}
                  onClick={() => toggleStrategy(strat.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition flex items-start gap-3 ${
                    isChecked
                      ? 'bg-purple-950/30 border-purple-500/40 text-white'
                      : 'bg-slate-950/40 border-white/5 text-slate-400 hover:border-white/15'
                  }`}
                >
                  <div className="mt-0.5 text-purple-400">
                    {isChecked ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4 text-slate-600" />}
                  </div>
                  <div className="space-y-0.5">
                    <div className="text-xs font-bold font-mono text-white flex items-center gap-2">
                      {strat.id}
                      <span className="text-[10px] text-slate-400 font-sans font-normal truncate">
                        {strat.name}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 leading-snug">{strat.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Market & Capital Parameters (7 cols) */}
        <div className="lg:col-span-7 bg-slate-900/60 rounded-2xl border border-white/10 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Calendar className="w-4 h-4 text-cyan-400" />
              Simulation Environment
            </h3>
            <span className="text-[11px] font-mono text-slate-400">Identical Ingestion Window</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Target Symbol</label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white uppercase font-mono focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Market Segment</label>
              <select
                value={market}
                onChange={(e) => setMarket(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:border-cyan-500 focus:outline-none"
              >
                <option value="NSE">NSE India</option>
                <option value="FOREX">FOREX</option>
                <option value="MCX">MCX Commodities</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Timeframe</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:border-cyan-500 focus:outline-none"
              >
                <option value="1D">1 Day (1D)</option>
                <option value="1h">1 Hour (1h)</option>
                <option value="15m">15 Minutes (15m)</option>
                <option value="5m">5 Minutes (5m)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Initial Capital (Virtual)</label>
              <input
                type="number"
                min={1000}
                value={initialCapital}
                onChange={(e) => setInitialCapital(parseFloat(e.target.value) || 100000)}
                className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Friction Model</label>
              <div className="p-2 bg-slate-950/70 border border-white/5 rounded-xl text-[11px] text-slate-400 font-mono flex items-center justify-between">
                <span>Fee: ₹2.00 / trade</span>
                <span>Slip: 0.05%</span>
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/20 text-xs text-purple-300 leading-relaxed flex items-start gap-2">
            <Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
            <span>
              Each strategy is evaluated sequentially across the exact same candle array with identical friction parameters. Metrics reflect realized trade exits without predictive curve fitting.
            </span>
          </div>
        </div>
      </div>

      {/* Results Section */}
      {comparisonData && (
        <div className="space-y-6">
          {/* Side-by-Side Metric Cards */}
          <div>
            <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              Side-by-Side Performance Comparison
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {comparisonData.strategies.map((strat) => {
                const isProfitable = strat.net_pnl >= 0;
                return (
                  <div
                    key={strat.strategy_code}
                    className="p-5 rounded-2xl bg-slate-900/80 border border-white/10 space-y-3.5 shadow-xl hover:border-purple-500/40 transition"
                  >
                    <div className="border-b border-white/10 pb-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-cyan-400">{strat.strategy_code}</span>
                        <span className="text-[10px] font-mono text-slate-500">v{strat.strategy_version}</span>
                      </div>
                      <h4 className="text-sm font-semibold text-white truncate">{strat.strategy_name}</h4>
                    </div>

                    {/* Net P&L & ROI */}
                    <div className="flex items-baseline justify-between">
                      <span className="text-xs text-slate-400 font-mono">Net P&amp;L</span>
                      <span
                        className={`text-base font-bold font-mono ${
                          isProfitable ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {isProfitable ? '+' : ''}₹{strat.net_pnl.toLocaleString()}
                        <span className="text-xs font-normal ml-1">({strat.roi_pct}%)</span>
                      </span>
                    </div>

                    {/* Metric Rows */}
                    <div className="space-y-1.5 text-xs font-mono text-slate-300">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Win Rate</span>
                        <span className="font-bold text-slate-200">{strat.win_rate}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Trades (W / L)</span>
                        <span className="text-slate-200">
                          {strat.total_trades} ({(strat.winning_trades ?? 0)} / {(strat.losing_trades ?? 0)})
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Profit Factor</span>
                        <span className="text-slate-200">{strat.profit_factor ?? 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Max Drawdown</span>
                        <span className="text-rose-400 font-semibold">{strat.max_drawdown_pct}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Expectancy</span>
                        <span className="text-slate-200">₹{(strat.expectancy ?? 0).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Trade List Details for Selected Strategy */}
          <div className="bg-slate-900/60 rounded-2xl border border-white/10 overflow-hidden shadow-xl">
            <div className="p-4 bg-slate-950/60 border-b border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="flex items-center gap-2 overflow-x-auto">
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider shrink-0 mr-2">
                  View Trades:
                </span>
                {comparisonData.strategies.map((strat) => (
                  <button
                    key={strat.strategy_code}
                    onClick={() => setActiveTabStrategy(strat.strategy_code)}
                    className={`px-3 py-1 rounded-xl text-xs font-mono transition shrink-0 ${
                      activeTabStrategy === strat.strategy_code
                        ? 'bg-purple-500 text-white font-bold shadow-md shadow-purple-500/20'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {strat.strategy_code} ({strat.total_trades})
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/70 border-b border-white/10 text-slate-400 font-mono uppercase text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">Trade ID</th>
                    <th className="py-2.5 px-3">Side</th>
                    <th className="py-2.5 px-3 text-right">Entry</th>
                    <th className="py-2.5 px-3 text-right">Exit</th>
                    <th className="py-2.5 px-3 text-right">Qty</th>
                    <th className="py-2.5 px-3 text-right">Net P&amp;L</th>
                    <th className="py-2.5 px-3">Exit Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono">
                  {activeStrategyTrades.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-500">
                        No trade signals generated by this strategy on the tested window.
                      </td>
                    </tr>
                  ) : (
                    activeStrategyTrades.map((t, idx) => {
                      const isWin = (t.net_pnl || 0) >= 0;
                      return (
                        <tr key={idx} className="hover:bg-white/[0.02]">
                          <td className="py-2 px-3 text-slate-400">#{t.trade_id}</td>
                          <td className="py-2 px-3">
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 font-bold">
                              LONG
                            </span>
                          </td>
                          <td className="py-2 px-3 text-right text-slate-200">₹{t.entry_price?.toFixed(2)}</td>
                          <td className="py-2 px-3 text-right text-slate-200">₹{t.exit_price?.toFixed(2)}</td>
                          <td className="py-2 px-3 text-right text-slate-300">{t.quantity}</td>
                          <td className={`py-2 px-3 text-right font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {isWin ? '+' : ''}₹{t.net_pnl?.toFixed(2)}
                          </td>
                          <td className="py-2 px-3 text-slate-400">{t.exit_reason}</td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            <div className="p-3 bg-slate-950/40 border-t border-white/5 text-[11px] text-slate-500 font-mono text-center">
              NEUTRAL FACTUAL METRICS: Historical performance does not guarantee future results. No automatic winner claims.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
