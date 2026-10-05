import React, { useState } from 'react';
import {
  History,
  TrendingUp,
  TrendingDown,
  Play,
  RefreshCw,
  Sliders,
  DollarSign,
  Percent,
  AlertTriangle,
  FileSpreadsheet,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../../services/api';
import { BacktestSummaryResponse, MarketType } from '../../types/market';

const SYMBOLS_BY_MARKET: Record<MarketType, string[]> = {
  FOREX: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD'],
  NSE: ['NIFTY 50', 'BANKNIFTY', 'RELIANCE', 'TCS'],
  MCX: ['GOLD', 'SILVER', 'CRUDEOIL'],
};

export const BacktestingView: React.FC = () => {
  const [market, setMarket] = useState<MarketType>('FOREX');
  const [symbol, setSymbol] = useState<string>('EUR/USD');
  const [timeframe, setTimeframe] = useState<string>('1D');
  const [strategyName, setStrategyName] = useState<string>('EMA Momentum Trend Following');
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [riskPerTrade, setRiskPerTrade] = useState<number>(1.5);
  const [slippagePct, setSlippagePct] = useState<number>(0.05);
  const [commission, setCommission] = useState<number>(2.0);

  const [loading, setLoading] = useState<boolean>(false);
  const [results, setResults] = useState<BacktestSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleMarketChange = (newMarket: MarketType) => {
    setMarket(newMarket);
    const symbols = SYMBOLS_BY_MARKET[newMarket];
    if (symbols.length > 0) {
      setSymbol(symbols[0]);
    }
  };

  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await api.runBacktest({
        symbol,
        timeframe,
        market,
        strategy_name: strategyName,
        initial_capital: initialCapital,
        risk_per_trade_pct: riskPerTrade,
        slippage_pct: slippagePct,
        commission_per_trade: commission,
      });
      setResults(res);
    } catch (err: any) {
      console.error('Backtest simulation failed:', err);
      setError(err.message || 'Backtest simulation execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-panel border border-border p-5 rounded-xl shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-accent/10 border border-accent/30 rounded-lg text-accent">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              Quantitative Backtesting Engine
              <span className="text-[10px] bg-accent/20 text-accent font-mono px-2 py-0.5 rounded border border-accent/30">
                HISTORICAL SIMULATOR
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Stress-test confluence trading strategies with realistic transaction costs, slippage, and drawdown analysis.
            </p>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="bg-panel border border-border rounded-xl p-5 shadow-sm">
        <form onSubmit={handleRunBacktest} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            {/* Market */}
            <div>
              <label className="text-slate-300 block mb-1 font-medium">Market</label>
              <select
                value={market}
                onChange={(e) => handleMarketChange(e.target.value as MarketType)}
                className="w-full bg-panel-subtle border border-border text-white px-3 py-2 rounded-lg focus:border-accent"
              >
                <option value="FOREX">FOREX</option>
                <option value="NSE">NSE (Indian Equities)</option>
                <option value="MCX">MCX (Commodities)</option>
              </select>
            </div>

            {/* Symbol */}
            <div>
              <label className="text-slate-300 block mb-1 font-medium">Symbol</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-panel-subtle border border-border text-white px-3 py-2 rounded-lg font-mono focus:border-accent"
              >
                {SYMBOLS_BY_MARKET[market].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Timeframe */}
            <div>
              <label className="text-slate-300 block mb-1 font-medium">Timeframe</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full bg-panel-subtle border border-border text-white px-3 py-2 rounded-lg font-mono focus:border-accent"
              >
                <option value="1D">1D (Daily Candles)</option>
                <option value="1h">1h (Hourly Candles)</option>
                <option value="15m">15m (Intraday)</option>
                <option value="5m">5m (Scalping)</option>
              </select>
            </div>

            {/* Strategy */}
            <div>
              <label className="text-slate-300 block mb-1 font-medium">Strategy</label>
              <select
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
                className="w-full bg-panel-subtle border border-border text-white px-3 py-2 rounded-lg focus:border-accent"
              >
                <option value="STRAT-EMA-CROSS">EMA Crossover (STRAT-EMA-CROSS)</option>
                <option value="STRAT-RSI-REV">RSI Reversal (STRAT-RSI-REV)</option>
                <option value="STRAT-MACD-MOM">MACD Momentum (STRAT-MACD-MOM)</option>
                <option value="STRAT-VWAP-TREND">VWAP Trend (STRAT-VWAP-TREND)</option>
                <option value="STRAT-BB-REV">Bollinger Band Reversion (STRAT-BB-REV)</option>
                <option value="STRAT-VOL-BREAKOUT">Volume-Confirmed Breakout (STRAT-VOL-BREAKOUT)</option>
                <option value="STRAT-MULTI-CONF">Multi-Indicator Confirmation (STRAT-MULTI-CONF)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs pt-2 border-t border-border/60">
            <div>
              <label className="text-slate-400 block mb-1">Starting Capital ($)</label>
              <input
                type="number"
                step="1000"
                value={initialCapital}
                onChange={(e) => setInitialCapital(parseFloat(e.target.value) || 10000)}
                className="w-full bg-panel-subtle border border-border text-white px-3 py-2 rounded-lg font-mono"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Risk Per Trade (%)</label>
              <input
                type="number"
                step="0.1"
                value={riskPerTrade}
                onChange={(e) => setRiskPerTrade(parseFloat(e.target.value) || 1.0)}
                className="w-full bg-panel-subtle border border-border text-white px-3 py-2 rounded-lg font-mono"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Simulated Slippage (%)</label>
              <input
                type="number"
                step="0.01"
                value={slippagePct}
                onChange={(e) => setSlippagePct(parseFloat(e.target.value) || 0.05)}
                className="w-full bg-panel-subtle border border-border text-white px-3 py-2 rounded-lg font-mono"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Commission ($/trade)</label>
              <input
                type="number"
                step="0.5"
                value={commission}
                onChange={(e) => setCommission(parseFloat(e.target.value) || 2.0)}
                className="w-full bg-panel-subtle border border-border text-white px-3 py-2 rounded-lg font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-gradient-to-r from-accent to-accent-indigo hover:opacity-90 text-white font-bold text-xs rounded-lg shadow-md flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <Play className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Simulating Strategy...' : 'Run Quantitative Simulation'}
            </button>
          </div>
        </form>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Simulation Results */}
      {results && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 rounded-xl border bg-panel border-border text-xs">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Win Rate</span>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                {results.win_rate.toFixed(1)}%
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                {results.winning_trades}W / {results.losing_trades}L
              </span>
            </div>

            <div className="p-4 rounded-xl border bg-panel border-border text-xs">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Profit Factor</span>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {results.profit_factor.toFixed(2)}
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">Gross Win / Gross Loss</span>
            </div>

            <div className="p-4 rounded-xl border bg-panel border-border text-xs">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Net Realized P&L</span>
              <div
                className={`text-xl font-bold font-mono mt-1 ${
                  results.net_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {results.net_pnl >= 0 ? '+' : ''}${results.net_pnl.toFixed(2)}
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                ROI: {results.net_roi_pct.toFixed(2)}%
              </span>
            </div>

            <div className="p-4 rounded-xl border bg-panel border-border text-xs">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Max Drawdown</span>
              <div className="text-xl font-bold font-mono text-rose-400 mt-1">
                -{results.max_drawdown_pct.toFixed(2)}%
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">Peak to trough risk</span>
            </div>

            <div className="p-4 rounded-xl border bg-panel border-border text-xs">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Expectancy</span>
              <div className="text-xl font-bold font-mono text-accent mt-1">
                ${results.expectancy.toFixed(2)}
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">Avg return per trade</span>
            </div>

            <div className="p-4 rounded-xl border bg-panel border-border text-xs">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Final Capital</span>
              <div className="text-xl font-bold font-mono text-white mt-1">
                ${results.final_capital.toFixed(2)}
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                Initial: ${results.initial_capital.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Trade by Trade Log */}
          <div className="bg-panel border border-border rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-accent" />
                Simulated Trades Log ({results.trades.length} Trades)
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-panel-subtle border-b border-border text-slate-400 uppercase font-mono text-[10px]">
                  <tr>
                    <th className="p-3">#</th>
                    <th className="p-3">Symbol</th>
                    <th className="p-3">Entry Price</th>
                    <th className="p-3">Exit Price</th>
                    <th className="p-3">Quantity</th>
                    <th className="p-3">Net P&L</th>
                    <th className="p-3">ROI %</th>
                    <th className="p-3">Exit Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {results.trades.map((t) => {
                    const isWin = t.net_pnl >= 0;
                    return (
                      <tr key={t.trade_id} className="hover:bg-panel-subtle/50 font-mono text-[11px]">
                        <td className="p-3 text-slate-400">{t.trade_id}</td>
                        <td className="p-3 font-bold text-white">{t.symbol}</td>
                        <td className="p-3 text-slate-300">${t.entry_price.toFixed(4)}</td>
                        <td className="p-3 text-slate-300">${t.exit_price.toFixed(4)}</td>
                        <td className="p-3 text-slate-400">{t.quantity.toLocaleString()}</td>
                        <td className="p-3 font-bold">
                          <span className={isWin ? 'text-emerald-400' : 'text-rose-400'}>
                            {isWin ? '+' : ''}${t.net_pnl.toFixed(2)}
                          </span>
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] ${
                              isWin
                                ? 'bg-emerald-500/10 text-emerald-300'
                                : 'bg-rose-500/10 text-rose-300'
                            }`}
                          >
                            {isWin ? '+' : ''}{t.roi_pct.toFixed(2)}%
                          </span>
                        </td>
                        <td className="p-3 text-slate-400">{t.exit_reason}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Disclaimer Banner */}
          <div className="p-3.5 bg-slate-900 border border-border rounded-xl text-slate-400 text-[11px] leading-relaxed flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span>{results.disclaimer}</span>
          </div>
        </div>
      )}
    </div>
  );
};
