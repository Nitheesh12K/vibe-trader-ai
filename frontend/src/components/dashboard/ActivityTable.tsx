import React from 'react';
import { History, ArrowUpRight, ArrowDownRight, Info } from 'lucide-react';
import { ActivityItem } from '../../types/market';
import { Badge } from '../common/Badge';

interface ActivityTableProps {
  activities: ActivityItem[];
}

export const ActivityTable: React.FC<ActivityTableProps> = ({ activities }) => {
  return (
    <div className="bg-[#0D1322]/80 backdrop-blur-xl border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] rounded-2xl p-5">
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <History className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-white">
            Recent Simulated Activity
          </h3>
        </div>
        <Badge variant="demo" size="sm">
          DEMO LOGS
        </Badge>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-400 text-[11px]">
              <th className="pb-3 font-semibold">TIMESTAMP</th>
              <th className="pb-3 font-semibold">TYPE</th>
              <th className="pb-3 font-semibold">SYMBOL</th>
              <th className="pb-3 font-semibold">MARKET</th>
              <th className="pb-3 font-semibold">SIDE</th>
              <th className="pb-3 font-semibold text-right">PRICE</th>
              <th className="pb-3 font-semibold text-right">SIMULATED P&L</th>
              <th className="pb-3 font-semibold text-right">STATUS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {activities.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-500">
                  No simulated activity recorded.
                </td>
              </tr>
            ) : (
              activities.map((act) => {
                const isBuy = act.side === 'BUY';
                const hasPnl = act.pnl !== null && act.pnl !== undefined;
                const isPnlPositive = (act.pnl || 0) >= 0;

                return (
                  <tr key={act.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 text-slate-400 text-[11px] whitespace-nowrap">
                      {act.timestamp}
                    </td>
                    <td className="py-3">
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#121B2F] border border-white/[0.06] text-slate-300">
                        {act.type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 font-bold text-white whitespace-nowrap">
                      {act.symbol}
                    </td>
                    <td className="py-3 text-slate-400">{act.market}</td>
                    <td className="py-3">
                      {act.side === 'BUY' && (
                        <span className="text-emerald-400 font-bold flex items-center gap-0.5">
                          <ArrowUpRight className="w-3 h-3" /> BUY
                        </span>
                      )}
                      {act.side === 'SELL' && (
                        <span className="text-rose-400 font-bold flex items-center gap-0.5">
                          <ArrowDownRight className="w-3 h-3" /> SELL
                        </span>
                      )}
                      {act.side === 'INFO' && (
                        <span className="text-cyan-400 font-bold flex items-center gap-0.5">
                          <Info className="w-3 h-3" /> INFO
                        </span>
                      )}
                    </td>
                    <td className="py-3 text-right font-semibold text-white">
                      ${act.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 text-right font-semibold">
                      {hasPnl ? (
                        <span className={isPnlPositive ? 'text-emerald-400' : 'text-rose-400'}>
                          {isPnlPositive ? '+' : ''}${act.pnl?.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-3 text-right">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-[#121B2F] text-slate-300 border border-white/[0.08]">
                        {act.status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
