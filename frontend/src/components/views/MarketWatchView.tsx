import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Plus,
  Trash2,
  ArrowUpRight,
  ArrowDownRight,
  Search,
  CheckCircle2,
  AlertCircle,
  Database,
  ExternalLink,
} from 'lucide-react';
import { api } from '../../services/api';
import { WatchlistItem, WatchlistCreate, MarketType, InstrumentItem } from '../../types/market';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface MarketWatchViewProps {
  onSelectInstrument?: (instrument: InstrumentItem) => void;
}

export const MarketWatchView: React.FC<MarketWatchViewProps> = ({ onSelectInstrument }) => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [demoInstruments, setDemoInstruments] = useState<InstrumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [marketFilter, setMarketFilter] = useState<'ALL' | MarketType>('ALL');
  const [search, setSearch] = useState<string>('');
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Form states
  const [symbol, setSymbol] = useState<string>('');
  const [name, setName] = useState<string>('');
  const [market, setMarket] = useState<MarketType>('NSE');
  const [category, setCategory] = useState<string>('Equities');
  const [exchange, setExchange] = useState<string>('NSE');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [marketFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [wlData, demoData] = await Promise.all([
        api.getWatchlist(marketFilter),
        api.getInstruments(marketFilter),
      ]);
      setWatchlist(wlData);
      setDemoInstruments(demoData);
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to load watchlist data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAdd = () => {
    setSymbol('');
    setName('');
    setMarket('NSE');
    setCategory('Equities');
    setExchange('NSE');
    setFormError(null);
    setShowAddModal(true);
  };

  const handleAddInstrument = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const cleanSym = symbol.trim().toUpperCase();
    if (!cleanSym) {
      setFormError('Symbol is required.');
      return;
    }

    try {
      setSubmitting(true);
      const payload: WatchlistCreate = {
        symbol: cleanSym,
        name: name.trim() || cleanSym,
        market,
        category: category.trim() || 'General',
        exchange: exchange.trim() || market,
      };

      const created = await api.addWatchlist(payload);
      setWatchlist((prev) => [created, ...prev]);
      setShowAddModal(false);
      setMessage({
        text: `Instrument '${created.symbol}' successfully added to ${created.market} watchlist.`,
        type: 'success',
      });
      loadData();
    } catch (err: any) {
      setFormError(err.message || 'Failed to add instrument');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number, sym: string, mkt: string) => {
    if (!window.confirm(`Remove ${sym} (${mkt}) from your watchlist?`)) return;
    try {
      await api.deleteWatchlist(id);
      setWatchlist((prev) => prev.filter((item) => item.id !== id));
      setMessage({ text: `Removed ${sym} from watchlist.`, type: 'success' });
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to remove instrument', type: 'error' });
    }
  };

  // Merge SQLite watchlist items with mock live pricing if available
  const mergedItems = watchlist.map((w) => {
    const matched = demoInstruments.find(
      (d) => d.symbol.toUpperCase() === w.symbol.toUpperCase() && d.market === w.market
    );
    return {
      id: w.id,
      symbol: w.symbol,
      name: w.name,
      market: w.market,
      category: w.category,
      exchange: w.exchange || w.market,
      last_price: matched?.last_price || 100.0,
      change: matched?.change || 0.0,
      change_percent: matched?.change_percent || 0.0,
      currency_symbol: matched?.currency_symbol || '$',
      volume: matched?.volume || '—',
    };
  });

  const filteredItems = mergedItems.filter(
    (item) =>
      search.trim() === '' ||
      item.symbol.toLowerCase().includes(search.toLowerCase()) ||
      item.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-panel border border-border rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg shadow-black/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100 font-mono">Market Watchlist</h2>
              <Badge variant="demo" size="sm">
                DATABASE PERSISTED
              </Badge>
            </div>
            <p className="text-xs text-slate-400">Manage tracked instruments across Forex, Indian NSE, and MCX Commodities.</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Segment Filter */}
          <div className="flex items-center gap-1 bg-background p-1 rounded-md border border-border">
            {(['ALL', 'FOREX', 'NSE', 'MCX'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setMarketFilter(tab)}
                className={`px-3 py-1 text-xs font-mono font-medium rounded transition-colors ${
                  marketFilter === tab
                    ? 'bg-accent/15 text-accent border border-accent/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search symbol..."
              className="bg-background border border-border rounded pl-8 pr-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-accent"
            />
          </div>

          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-accent hover:bg-sky-400 text-slate-950 text-xs font-bold font-mono transition-colors shadow-lg shadow-accent/10"
          >
            <Plus className="w-4 h-4" />
            Add Instrument
          </button>
        </div>
      </div>

      {/* Message Banner */}
      {message && (
        <div
          className={`p-3.5 rounded-lg border text-xs flex items-center justify-between gap-2.5 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {message.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{message.text}</span>
          </div>
          <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-slate-200">
            &times;
          </button>
        </div>
      )}

      {/* Watchlist Table */}
      {loading ? (
        <LoadingSpinner label="Loading watchlist from SQLite..." />
      ) : (
        <div className="bg-panel border border-border rounded-lg overflow-hidden shadow-lg shadow-black/20">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-border text-slate-400 text-[11px] bg-background/50">
                  <th className="py-2.5 px-4 font-medium">SYMBOL</th>
                  <th className="py-2.5 px-4 font-medium">NAME</th>
                  <th className="py-2.5 px-4 font-medium">MARKET</th>
                  <th className="py-2.5 px-4 font-medium">CATEGORY</th>
                  <th className="py-2.5 px-4 font-medium text-right">LAST SIMULATED PRICE</th>
                  <th className="py-2.5 px-4 font-medium text-right">24H CHANGE</th>
                  <th className="py-2.5 px-4 font-medium text-right">VOLUME</th>
                  <th className="py-2.5 px-4 font-medium text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredItems.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-10 text-center text-slate-400 text-xs">
                      No instruments found matching your search.
                    </td>
                  </tr>
                ) : (
                  filteredItems.map((item) => {
                    const isPositive = item.change >= 0;

                    return (
                      <tr key={item.id} className="hover:bg-panel-subtle/50 transition-colors group">
                        <td className="py-3 px-4 font-bold text-slate-100 flex items-center gap-2">
                          <span>{item.symbol}</span>
                          <span className="text-[9px] px-1 py-0.2 rounded bg-panel-subtle text-slate-400 border border-border">
                            {item.exchange}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-300 max-w-[200px] truncate">{item.name}</td>
                        <td className="py-3 px-4 text-slate-400">{item.market}</td>
                        <td className="py-3 px-4 text-slate-400">{item.category}</td>
                        <td className="py-3 px-4 text-right font-bold text-slate-100">
                          {item.currency_symbol}
                          {item.last_price.toLocaleString(undefined, {
                            minimumFractionDigits: item.last_price < 2 ? 4 : 2,
                            maximumFractionDigits: 4,
                          })}
                        </td>
                        <td className="py-3 px-4 text-right font-medium">
                          <span
                            className={`inline-flex items-center gap-0.5 ${
                              isPositive ? 'text-bullish' : 'text-bearish'
                            }`}
                          >
                            {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                            {isPositive ? '+' : ''}
                            {item.change_percent.toFixed(2)}%
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right text-slate-400">{item.volume}</td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleDelete(item.id, item.symbol, item.market)}
                            className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                            title="Remove from Watchlist"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Instrument Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-border rounded-lg max-w-md w-full p-6 shadow-2xl space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Plus className="w-4 h-4 text-accent" />
                Add Watchlist Instrument
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleAddInstrument} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1">Symbol</label>
                  <input
                    type="text"
                    required
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    placeholder="e.g. TATAMOTORS"
                    className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100 uppercase"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Market</label>
                  <select
                    value={market}
                    onChange={(e) => setMarket(e.target.value as MarketType)}
                    className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100"
                  >
                    <option value="NSE">NSE</option>
                    <option value="FOREX">FOREX</option>
                    <option value="MCX">MCX</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Instrument Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Tata Motors Ltd"
                  className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1">Category</label>
                  <input
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="Equities, Indices, Currencies..."
                    className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Exchange / Provider</label>
                  <input
                    type="text"
                    value={exchange}
                    onChange={(e) => setExchange(e.target.value)}
                    placeholder="NSE, MCX, FX_CM..."
                    className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded border border-border text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 rounded bg-accent hover:bg-sky-400 text-slate-950 font-bold"
                >
                  {submitting ? 'Adding...' : 'Add to Watchlist'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
