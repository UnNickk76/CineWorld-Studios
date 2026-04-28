// CineWorld Studio's — TopCitiesPanel
// Top 3 città del film: nome + flag + spettatori + incassi + % vs totale.
// Layout coerente col gioco (gradient, ring, bg dark).

import React from 'react';
import { MapPin } from 'lucide-react';

const fmtMoney = (v) => `$${Math.round(Number(v || 0)).toLocaleString('it-IT')}`;
const fmtNum = (v) => Number(v || 0).toLocaleString('it-IT');

const RANK_COLORS = [
  { bg: 'from-amber-600/30 via-amber-700/20 to-amber-900/10', ring: 'ring-amber-500/30', text: 'text-amber-200', medal: '🥇' },
  { bg: 'from-zinc-500/20 via-zinc-600/15 to-zinc-700/10', ring: 'ring-zinc-400/30', text: 'text-zinc-200', medal: '🥈' },
  { bg: 'from-orange-700/20 via-orange-800/15 to-orange-900/10', ring: 'ring-orange-500/25', text: 'text-orange-200', medal: '🥉' },
];

export const TopCitiesPanel = ({ cities = [] }) => {
  if (!cities || cities.length === 0) {
    return (
      <div className="text-[11px] text-zinc-500 italic text-center py-3">
        I dati delle città arriveranno dopo il primo giorno di sala
      </div>
    );
  }

  return (
    <div className="space-y-2" data-testid="top-cities-panel">
      {cities.slice(0, 3).map((c, i) => {
        const style = RANK_COLORS[i] || RANK_COLORS[2];
        return (
          <div
            key={c.name + i}
            className={`relative rounded-xl bg-gradient-to-r ${style.bg} ring-1 ${style.ring} p-2.5 overflow-hidden`}
            data-testid={`top-city-${i}`}
          >
            <div className="flex items-center gap-2.5">
              <div className="text-2xl flex-shrink-0">{style.medal}</div>
              <div className="text-2xl flex-shrink-0">{c.flag}</div>
              <div className="flex-1 min-w-0">
                <div className={`text-sm font-bold ${style.text} flex items-center gap-1.5 truncate`}>
                  <MapPin className="w-3 h-3 opacity-70" />
                  {c.name}
                </div>
                <div className="flex items-baseline gap-2 text-[10px] text-zinc-400 mt-0.5">
                  <span><strong className="text-zinc-200">{fmtNum(c.spectators)}</strong> spettatori</span>
                  <span>•</span>
                  <span><strong className="text-emerald-300">{fmtMoney(c.revenue)}</strong></span>
                </div>
              </div>
              <div className={`text-base font-black ${style.text} flex-shrink-0`}>
                {c.pct_of_total}%
              </div>
            </div>
            {/* Bar visualizing percentage */}
            <div className="absolute inset-x-0 bottom-0 h-0.5 bg-zinc-900/40">
              <div
                className={`h-full bg-gradient-to-r ${i === 0 ? 'from-amber-500 to-amber-300' : i === 1 ? 'from-zinc-400 to-zinc-200' : 'from-orange-500 to-orange-300'}`}
                style={{ width: `${Math.min(100, c.pct_of_total * 2)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default TopCitiesPanel;
