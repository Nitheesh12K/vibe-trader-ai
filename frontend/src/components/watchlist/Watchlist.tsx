import React, { useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Filter } from 'lucide-react';
import { InstrumentItem, MarketType } from '../../types/market';
import { Badge } from '../common/Badge';

interface WatchlistProps {
  instruments: InstrumentItem[];
  selectedSymbol: string;
  onSelectInstrument: (instrument: InstrumentItem) => void;
  searchFilter?: string;
}

export const Watchlist: React.FC<WatchlistProps> = ({
  instruments,
  selectedSymbol,
  onSelectInstrument,
  searchFilter = '',
}) => {
  const [activeTab, setActiveTab] = useState<'ALL' | MarketType>('ALL');

  // Filter instruments based on tab and optional search query
  const filteredInstruments = instruments.filter((inst) => {
    const matchesTab = activeTab === 'ALL' || inst.market === activeTab;
    const matchesSearch =
      searchFilter.trim() === '' ||
      inst.symbol.toLowerCase().includes(searchFilter.toLowerCase()) ||
      inst.name.toLowerCase().includes(searchFilter.toLowerCase());
    return matchesTab && matchesSearch;
  });

  return (
    <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl flex flex-col h-full overflow-hidden">
      {/* Header & Market Tabs */}
      <div className="p-4 border-b border-white/[0.08] bg-[#0A0F1D]/80 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white">
              Market Watch
            </h3>
            <Badge variant="demo" size="sm">
              SIMULATED
            </Badge>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            {filteredInstruments.length} instruments
          </span>
        </div>

        {/* Tab filters */}
        <div className="flex items-center gap-1 bg-[#080D1A] p-1 rounded-lg border border-white/[0.08]">
          {(['ALL', 'FOREX', 'NSE', 'MCX'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-1 text-[11px] font-mono rounded-md transition-all ${
                activeTab === tab
                  ? 'bg-cyan-500 text-white font-bold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Instruments Table / List */}
      <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04] scrollbar-thin">
        {filteredInstruments.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-xs">
            No instruments match the selected filter.
          </div>
        ) : (
          filteredInstruments.map((inst) => {
            const isSelected = inst.symbol === selectedSymbol;
            const isPositive = inst.change >= 0;

            return (
              <div
                key={inst.symbol}
                onClick={() => onSelectInstrument(inst)}
                className={`p-3.5 flex items-center justify-between cursor-pointer transition-all group ${
                  isSelected
                    ? 'bg-cyan-500/10 border-l-2 border-cyan-400'
                    : 'hover:bg-white/[0.03]'
                }`}
              >
                {/* Left: Symbol & Name */}
                <div className="min-w-0 pr-2">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-xs font-bold text-white group-hover:text-cyan-400 transition-colors">
                      {inst.symbol}
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#121B2F] text-slate-400 border border-white/[0.06] font-mono">
                      {inst.market}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 truncate max-w-[150px] mt-0.5">
                    {inst.name}
                  </div>
                </div>

                {/* Right: Price & Change */}
                <div className="text-right shrink-0">
                  <div className="font-mono text-xs font-bold text-white">
                    {inst.currency_symbol}
                    {inst.last_price.toLocaleString(undefined, {
                      minimumFractionDigits: inst.last_price < 2 ? 4 : 2,
                      maximumFractionDigits: 4,
                    })}
                  </div>
                  <div
                    className={`flex items-center justify-end text-[11px] font-mono font-semibold ${
                      isPositive ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {isPositive ? (
                      <ArrowUpRight className="w-3 h-3 inline" />
                    ) : (
                      <ArrowDownRight className="w-3 h-3 inline" />
                    )}
                    <span>
                      {isPositive ? '+' : ''}
                      {inst.change_percent.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Disclaimer */}
      <div className="px-4 py-2.5 border-t border-white/[0.08] bg-[#0A0F1D]/80 text-[10px] text-slate-500 font-mono flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          FEED: SYNTHETIC DEMO
        </span>
        <span>LATENCY: &lt;10ms</span>
      </div>
    </div>
  );
};
