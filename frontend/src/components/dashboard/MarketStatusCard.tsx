import React from 'react';
import { Globe2, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { MarketStatusItem } from '../../types/market';
import { Badge } from '../common/Badge';

interface MarketStatusCardProps {
  statuses: MarketStatusItem[];
}

export const MarketStatusCard: React.FC<MarketStatusCardProps> = ({ statuses }) => {
  return (
    <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5">
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Globe2 className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-white">
            Market Sessions Status
          </h3>
        </div>
        <Badge variant="demo" size="sm">
          DEMO SCHEDULE
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {statuses.map((item) => {
          const isOpen = item.status === 'OPEN';

          return (
            <div
              key={item.market}
              className="bg-[#080D1A]/80 border border-white/[0.06] rounded-xl p-3.5 flex flex-col justify-between hover:border-cyan-500/20 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-white">
                  {item.label}
                </span>
                <span
                  className={`inline-flex items-center gap-1.5 text-[10px] font-mono font-bold px-2 py-0.5 rounded-md ${
                    isOpen
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      : 'bg-[#121B2F] text-slate-400 border border-white/[0.08]'
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      isOpen ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse' : 'bg-slate-500'
                    }`}
                  />
                  {item.status}
                </span>
              </div>

              <div className="mt-3 space-y-1 text-[11px] font-mono text-slate-400">
                <div className="flex items-center gap-1.5 text-slate-300">
                  <Clock className="w-3 h-3 text-slate-400 shrink-0" />
                  <span>{item.session_hours}</span>
                </div>
                <div className="text-[10px] text-slate-500">TZ: {item.timezone}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
