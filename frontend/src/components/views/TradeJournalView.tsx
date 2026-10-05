import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Plus,
  Trash2,
  Edit2,
  CheckCircle2,
  AlertCircle,
  Tag,
  Lightbulb,
  Search,
  Link as LinkIcon,
} from 'lucide-react';
import { api } from '../../services/api';
import { JournalItem, JournalCreate, PaperTradeItem } from '../../types/market';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';

export const TradeJournalView: React.FC = () => {
  const [entries, setEntries] = useState<JournalItem[]>([]);
  const [recentTrades, setRecentTrades] = useState<PaperTradeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [symbolFilter, setSymbolFilter] = useState<string>('');
  const [showModal, setShowModal] = useState<boolean>(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Form state
  const [tradeId, setTradeId] = useState<string>('');
  const [symbol, setSymbol] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [lessonsLearned, setLessonsLearned] = useState<string>('');
  const [tags, setTags] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);

  useEffect(() => {
    loadJournal();
    loadTradesForSelector();
  }, [symbolFilter]);

  const loadJournal = async () => {
    try {
      setLoading(true);
      const res = await api.getJournal(symbolFilter || undefined);
      setEntries(res.items);
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to load journal entries', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const loadTradesForSelector = async () => {
    try {
      const res = await api.getPaperTrades(undefined, undefined, 1, 20);
      setRecentTrades(res.items);
    } catch {
      // ignore
    }
  };

  const handleOpenCreate = () => {
    setEditingId(null);
    setTradeId('');
    setSymbol('');
    setTitle('');
    setNotes('');
    setLessonsLearned('');
    setTags('breakout,execution');
    setShowModal(true);
  };

  const handleOpenEdit = (item: JournalItem) => {
    setEditingId(item.id);
    setTradeId(item.trade_id ? String(item.trade_id) : '');
    setSymbol(item.symbol || '');
    setTitle(item.title);
    setNotes(item.notes);
    setLessonsLearned(item.lessons_learned || '');
    setTags(item.tags || '');
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this journal entry?')) return;
    try {
      await api.deleteJournal(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
      setMessage({ text: 'Journal entry deleted.', type: 'success' });
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to delete entry', type: 'error' });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const tId = tradeId.trim() ? parseInt(tradeId, 10) : undefined;

      if (editingId) {
        const updated = await api.updateJournal(editingId, {
          trade_id: tId,
          symbol: symbol.trim().toUpperCase() || undefined,
          title,
          notes,
          lessons_learned: lessonsLearned.trim() || undefined,
          tags,
        });
        setEntries((prev) => prev.map((e) => (e.id === editingId ? updated : e)));
        setMessage({ text: 'Journal entry updated successfully.', type: 'success' });
      } else {
        const created = await api.createJournal({
          trade_id: tId,
          symbol: symbol.trim().toUpperCase() || undefined,
          title,
          notes,
          lessons_learned: lessonsLearned.trim() || undefined,
          tags,
        });
        setEntries((prev) => [created, ...prev]);
        setMessage({ text: 'New journal entry logged to SQLite.', type: 'success' });
      }
      setShowModal(false);
    } catch (err: any) {
      alert(err.message || 'Failed to save journal entry');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-panel border border-border rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg shadow-black/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100 font-mono">Trader Journal & Reflection</h2>
            <p className="text-xs text-slate-400">Document trade reflections, emotional discipline, and lessons learned.</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value)}
              placeholder="Filter by symbol..."
              className="bg-background border border-border rounded pl-8 pr-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-accent"
            />
          </div>

          <button
            onClick={handleOpenCreate}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-accent hover:bg-sky-400 text-slate-950 text-xs font-bold font-mono transition-colors shadow-lg shadow-accent/10"
          >
            <Plus className="w-4 h-4" />
            New Reflection
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

      {loading ? (
        <LoadingSpinner label="Loading journal reflections..." />
      ) : entries.length === 0 ? (
        <div className="bg-panel border border-border rounded-lg p-12 text-center text-slate-400">
          <BookOpen className="w-10 h-10 mx-auto mb-3 text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-300 font-mono">No Journal Entries Recorded</h3>
          <p className="text-xs text-slate-400 mt-1 mb-4">Start recording session notes and lessons learned.</p>
          <button
            onClick={handleOpenCreate}
            className="px-4 py-1.5 rounded bg-accent/10 hover:bg-accent/20 border border-accent/30 text-accent text-xs font-mono font-medium"
          >
            Create Your First Entry
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {entries.map((item) => (
            <div
              key={item.id}
              className="bg-panel border border-border rounded-lg p-5 flex flex-col justify-between shadow-lg shadow-black/20 hover:border-border-strong transition-all"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-mono text-sm font-bold text-slate-100">{item.title}</h3>
                  {item.symbol && (
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-accent/10 border border-accent/20 text-accent font-bold">
                      {item.symbol}
                    </span>
                  )}
                </div>

                {item.trade_id && (
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 mb-2.5">
                    <LinkIcon className="w-3 h-3 text-slate-400" />
                    <span>Linked to Paper Trade #{item.trade_id}</span>
                  </div>
                )}

                <div className="bg-background rounded p-3 border border-border/80 text-xs text-slate-200 leading-relaxed mb-3">
                  {item.notes}
                </div>

                {item.lessons_learned && (
                  <div className="bg-amber-500/10 border border-amber-500/20 rounded p-2.5 text-xs text-amber-300 flex items-start gap-2 mb-3">
                    <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <strong className="block text-[10px] font-mono uppercase tracking-wider text-amber-400">
                        Lesson Learned
                      </strong>
                      <span className="text-[11px] leading-normal">{item.lessons_learned}</span>
                    </div>
                  </div>
                )}

                {item.tags && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {item.tags.split(',').map((t, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-panel-subtle text-slate-400 border border-border flex items-center gap-1"
                      >
                        <Tag className="w-2.5 h-2.5" />
                        {t.trim()}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-400">
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleOpenEdit(item)}
                    className="p-1 rounded bg-panel-subtle hover:bg-border text-slate-300 transition-colors border border-border"
                    title="Edit Entry"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-1 rounded bg-panel-subtle hover:bg-rose-500/20 text-rose-400 transition-colors border border-border"
                    title="Delete Entry"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Dialog for Journal Entry */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-border rounded-lg max-w-lg w-full p-6 shadow-2xl space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-accent" />
                {editingId ? 'Edit Journal Entry' : 'Log Trade Reflection'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1">Symbol (Optional)</label>
                  <input
                    type="text"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    placeholder="e.g. NIFTY 50"
                    className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100 uppercase"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Link Paper Trade (Optional)</label>
                  <select
                    value={tradeId}
                    onChange={(e) => setTradeId(e.target.value)}
                    className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100"
                  >
                    <option value="">None (General Reflection)</option>
                    {recentTrades.map((t) => (
                      <option key={t.id} value={t.id}>
                        #{t.id} - {t.symbol} ({t.side} ${t.entry_price})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Early profit taking on Nifty rally"
                  className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Trade Observations & Notes</label>
                <textarea
                  rows={4}
                  required
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Detailed rationale, technical indicators observed, market context..."
                  className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100 resize-none"
                />
              </div>

              <div>
                <label className="block text-amber-400 mb-1">Lessons Learned / Psychological Insight</label>
                <textarea
                  rows={2}
                  value={lessonsLearned}
                  onChange={(e) => setLessonsLearned(e.target.value)}
                  placeholder="What would you do differently next time? Did you stick to risk limits?"
                  className="w-full bg-background border border-amber-500/30 rounded px-3 py-2 text-amber-200 resize-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Tags (Comma-separated)</label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="psychology, breakout, fomo, nse"
                  className="w-full bg-background border border-border rounded px-3 py-2 text-slate-100"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 rounded border border-border text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 rounded bg-accent hover:bg-sky-400 text-slate-950 font-bold"
                >
                  {submitting ? 'Saving...' : editingId ? 'Update Entry' : 'Save Entry'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
