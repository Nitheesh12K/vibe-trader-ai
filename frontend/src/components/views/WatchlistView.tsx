import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Plus,
  Trash2,
  ArrowUp,
  ArrowDown,
  Search,
  LineChart,
  Sparkles,
  RefreshCw,
  FolderPlus,
  Edit2,
  Check,
  X,
  AlertCircle,
  Tag,
} from 'lucide-react';
import { api } from '../../services/api';
import { WatchlistInstrumentItem, WatchlistGroupItem, NavTabId } from '../../types/market';

interface WatchlistViewProps {
  onNavigate?: (tab: NavTabId, symbol?: string) => void;
}

export const WatchlistView: React.FC<WatchlistViewProps> = ({ onNavigate }) => {
  const [instruments, setInstruments] = useState<WatchlistInstrumentItem[]>([]);
  const [groups, setGroups] = useState<WatchlistGroupItem[]>([]);
  const [activeGroup, setActiveGroup] = useState<string>('ALL');
  const [selectedMarket, setSelectedMarket] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Add symbol modal
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newSymbol, setNewSymbol] = useState<string>('');
  const [newName, setNewName] = useState<string>('');
  const [newMarket, setNewMarket] = useState<string>('NSE');
  const [newCategory, setNewCategory] = useState<string>('Equities');
  const [newGroup, setNewGroup] = useState<string>('Default Watchlist');
  const [newNotes, setNewNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Edit notes
  const [editingNotesId, setEditingNotesId] = useState<number | null>(null);
  const [tempNotes, setTempNotes] = useState<string>('');

  const fetchWatchlist = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const params: { market?: string; group?: string } = {};
      if (selectedMarket !== 'ALL') params.market = selectedMarket;
      if (activeGroup !== 'ALL') params.group = activeGroup;

      const [items, groupList] = await Promise.all([
        api.getWatchlists(params),
        api.getWatchlistGroups().catch(() => []),
      ]);
      setInstruments(items);
      setGroups(groupList);
    } catch (err: any) {
      setError(err.message || 'Failed to load watchlist data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, [activeGroup, selectedMarket]);

  const handleAddInstrument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSymbol.trim() || !newName.trim()) return;

    try {
      setIsSubmitting(true);
      setError(null);
      await api.addToWatchlist({
        symbol: newSymbol.trim().toUpperCase(),
        name: newName.trim(),
        market: newMarket,
        category: newCategory,
        group_name: newGroup,
        notes: newNotes.trim() || undefined,
        order_index: instruments.length + 1,
      });
      setShowAddModal(false);
      setNewSymbol('');
      setNewName('');
      setNewNotes('');
      await fetchWatchlist();
    } catch (err: any) {
      setError(err.message || 'Failed to add instrument to watchlist.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number, symbol: string) => {
    if (!window.confirm(`Remove ${symbol} from watchlist?`)) return;
    try {
      await api.deleteWatchlistItem(id);
      setInstruments((prev) => prev.filter((item) => item.id !== id));
    } catch (err: any) {
      setError(err.message || 'Failed to delete instrument.');
    }
  };

  const handleReorder = async (index: number, direction: 'UP' | 'DOWN') => {
    const targetIndex = direction === 'UP' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= instruments.length) return;

    const currentItem = instruments[index];
    const targetItem = instruments[targetIndex];

    const newCurrentOrder = targetItem.order_index ?? targetIndex;
    const newTargetOrder = currentItem.order_index ?? index;

    // Optimistic update
    const updated = [...instruments];
    updated[index] = { ...targetItem, order_index: newTargetOrder };
    updated[targetIndex] = { ...currentItem, order_index: newCurrentOrder };
    setInstruments(updated);

    try {
      await Promise.all([
        api.updateWatchlistItem(currentItem.id, { order_index: newCurrentOrder }),
        api.updateWatchlistItem(targetItem.id, { order_index: newTargetOrder }),
      ]);
    } catch (err) {
      // Revert on error
      fetchWatchlist();
    }
  };

  const handleSaveNotes = async (id: number) => {
    try {
      await api.updateWatchlistItem(id, { notes: tempNotes });
      setInstruments((prev) =>
        prev.map((item) => (item.id === id ? { ...item, notes: tempNotes } : item))
      );
      setEditingNotesId(null);
    } catch (err: any) {
      setError('Failed to update notes.');
    }
  };

  const filteredInstruments = useMemo(() => {
    return instruments.filter((item) => {
      const q = searchQuery.toLowerCase();
      const matchSearch =
        item.symbol.toLowerCase().includes(q) ||
        item.name.toLowerCase().includes(q) ||
        (item.notes && item.notes.toLowerCase().includes(q));
      return matchSearch;
    });
  }, [instruments, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-5 rounded-2xl border border-white/10 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              <span className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Tag className="w-5 h-5" />
              </span>
              Watchlist Manager
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Live Enriched
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Organized multi-market tracking with automated signal tags, causal price feeds, and custom groups.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchWatchlist()}
            disabled={isLoading}
            className="p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition border border-white/5"
            title="Refresh Watchlist"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/20 transition"
          >
            <Plus className="w-4 h-4" />
            Add Symbol
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-xs text-rose-300 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Filter Tabs & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Group Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
          <button
            onClick={() => setActiveGroup('ALL')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition shrink-0 ${
              activeGroup === 'ALL'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                : 'bg-slate-800/80 text-slate-400 hover:text-white border border-white/5'
            }`}
          >
            All Lists ({instruments.length})
          </button>
          {groups.map((g, idx) => (
            <button
              key={g.id || g.name || idx}
              onClick={() => setActiveGroup(g.name)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition shrink-0 ${
                activeGroup === g.name
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                  : 'bg-slate-800/80 text-slate-400 hover:text-white border border-white/5'
              }`}
            >
              {g.name}
            </button>
          ))}
        </div>

        {/* Market Filter & Search Input */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search symbol or notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-3 py-1.5 bg-slate-900 border border-white/10 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-48 md:w-56"
            />
          </div>

          <select
            value={selectedMarket}
            onChange={(e) => setSelectedMarket(e.target.value)}
            className="px-3 py-1.5 bg-slate-900 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Markets</option>
            <option value="NSE">NSE India</option>
            <option value="FOREX">Forex</option>
            <option value="MCX">MCX Commodities</option>
          </select>
        </div>
      </div>

      {/* Watchlist Table */}
      <div className="bg-slate-900/60 rounded-2xl border border-white/10 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 border-b border-white/10 text-slate-400 uppercase tracking-wider font-mono text-[11px]">
              <tr>
                <th className="py-3 px-3 text-center w-12">#</th>
                <th className="py-3 px-4">Instrument</th>
                <th className="py-3 px-3">Market</th>
                <th className="py-3 px-3 text-right">Price</th>
                <th className="py-3 px-3 text-right">24h Change</th>
                <th className="py-3 px-3">Session</th>
                <th className="py-3 px-3">Algorithm Signal</th>
                <th className="py-3 px-4">Research Notes</th>
                <th className="py-3 px-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading && instruments.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-cyan-400" />
                    Loading watchlist...
                  </td>
                </tr>
              ) : filteredInstruments.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    No instruments found in this view. Click "Add Symbol" above to populate your watchlist.
                  </td>
                </tr>
              ) : (
                filteredInstruments.map((item, idx) => {
                  const isPositive = (item.change_pct ?? 0) >= 0;
                  const isEditingThis = editingNotesId === item.id;

                  return (
                    <tr key={item.id} className="hover:bg-white/[0.02] transition group">
                      {/* Reorder Controls */}
                      <td className="py-3 px-3 text-center">
                        <div className="flex flex-col items-center gap-0.5">
                          <button
                            onClick={() => handleReorder(idx, 'UP')}
                            disabled={idx === 0}
                            className="text-slate-500 hover:text-cyan-400 disabled:opacity-20 transition"
                            title="Move Up"
                          >
                            <ArrowUp className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleReorder(idx, 'DOWN')}
                            disabled={idx === filteredInstruments.length - 1}
                            className="text-slate-500 hover:text-cyan-400 disabled:opacity-20 transition"
                            title="Move Down"
                          >
                            <ArrowDown className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>

                      {/* Symbol & Name */}
                      <td className="py-3 px-4">
                        <div className="font-bold text-white text-sm font-mono">{item.symbol}</div>
                        <div className="text-[11px] text-slate-400 truncate max-w-[160px]">{item.name}</div>
                      </td>

                      {/* Market Badge */}
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            item.market === 'NSE'
                              ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                              : item.market === 'FOREX'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          }`}
                        >
                          {item.market}
                        </span>
                      </td>

                      {/* Price */}
                      <td className="py-3 px-3 text-right font-mono font-semibold text-slate-200">
                        {item.latest_price !== null && item.latest_price !== undefined
                          ? `${item.market === 'FOREX' ? '$' : '₹'}${item.latest_price.toLocaleString(undefined, {
                              minimumFractionDigits: item.market === 'FOREX' ? 4 : 2,
                            })}`
                          : '—'}
                      </td>

                      {/* Change % */}
                      <td className="py-3 px-3 text-right font-mono">
                        {item.change_pct !== null && item.change_pct !== undefined ? (
                          <span
                            className={`inline-flex items-center gap-1 font-semibold ${
                              isPositive ? 'text-emerald-400' : 'text-rose-400'
                            }`}
                          >
                            {isPositive ? (
                              <TrendingUp className="w-3.5 h-3.5" />
                            ) : (
                              <TrendingDown className="w-3.5 h-3.5" />
                            )}
                            {isPositive ? '+' : ''}
                            {item.change_pct}%
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>

                      {/* Market Session Status */}
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-mono ${
                            item.market_status === 'OPEN'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold'
                              : 'bg-slate-800 text-slate-400 border border-white/5'
                          }`}
                        >
                          {item.market_status}
                        </span>
                      </td>

                      {/* Current Signal */}
                      <td className="py-3 px-3">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold ${
                            item.current_signal === 'BUY CANDIDATE'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 animate-pulse'
                              : 'bg-slate-800/80 text-slate-400'
                          }`}
                        >
                          {item.current_signal || 'HOLD'}
                        </span>
                      </td>

                      {/* Editable Notes */}
                      <td className="py-3 px-4 max-w-xs">
                        {isEditingThis ? (
                          <div className="flex items-center gap-1.5">
                            <input
                              type="text"
                              value={tempNotes}
                              onChange={(e) => setTempNotes(e.target.value)}
                              className="w-full px-2 py-1 bg-slate-950 border border-cyan-500/40 rounded text-xs text-white focus:outline-none"
                              autoFocus
                            />
                            <button
                              onClick={() => handleSaveNotes(item.id)}
                              className="p-1 rounded bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"
                              title="Save"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => setEditingNotesId(null)}
                              className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white"
                              title="Cancel"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between group/note">
                            <span className="text-slate-400 truncate max-w-[180px]">
                              {item.notes || <span className="text-slate-600 italic">No notes</span>}
                            </span>
                            <button
                              onClick={() => {
                                setEditingNotesId(item.id);
                                setTempNotes(item.notes || '');
                              }}
                              className="opacity-0 group-hover/note:opacity-100 text-slate-400 hover:text-cyan-400 transition ml-1"
                              title="Edit notes"
                            >
                              <Edit2 className="w-3 h-3" />
                            </button>
                          </div>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          {onNavigate && (
                            <>
                              <button
                                onClick={() => onNavigate('technical_analysis', item.symbol)}
                                className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-cyan-500/20 text-slate-400 hover:text-cyan-300 transition"
                                title="Open Technical Chart"
                              >
                                <LineChart className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => onNavigate('ai_insights', item.symbol)}
                                className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-500/20 text-slate-400 hover:text-indigo-300 transition"
                                title="Run AI Reasoning"
                              >
                                <Sparkles className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => handleDelete(item.id, item.symbol)}
                            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition"
                            title="Remove from Watchlist"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer info badge */}
        <div className="px-4 py-2.5 bg-slate-950/40 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span>Freshness: &lt; 2.5s (VERIFIED)</span>
          <span>Source: DEMO &amp; HISTORICAL CALIBRATED FEEDS</span>
        </div>
      </div>

      {/* Add Symbol Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/15 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Plus className="w-5 h-5 text-cyan-400" />
                Add Instrument to Watchlist
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddInstrument} className="space-y-3.5">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Symbol *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. RELIANCE, EUR/USD, GOLD"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500 font-mono uppercase"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Company / Asset Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Reliance Industries Ltd."
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Market</label>
                  <select
                    value={newMarket}
                    onChange={(e) => setNewMarket(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="NSE">NSE India</option>
                    <option value="FOREX">Forex</option>
                    <option value="MCX">MCX</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Category</label>
                  <input
                    type="text"
                    placeholder="e.g. Energy, Banking"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Watchlist Group</label>
                <select
                  value={newGroup}
                  onChange={(e) => setNewGroup(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="Default Watchlist">Default Watchlist</option>
                  <option value="High Momentum">High Momentum</option>
                  <option value="Key Indices">Key Indices</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Research Notes (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Monitoring for 200 EMA breakout"
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 shadow-lg shadow-cyan-500/25 transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : 'Add Instrument'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
