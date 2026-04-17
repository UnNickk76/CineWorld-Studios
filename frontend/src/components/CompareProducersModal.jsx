// CineWorld - Confronto Produttori (Side-by-side comparison)
import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { Film, Tv, Sparkles, Star, TrendingUp, Trophy, Crown, BarChart3, Loader2 } from 'lucide-react';

function fmtRev(n) { if (n >= 1e9) return (n/1e9).toFixed(1)+'B'; if (n >= 1e6) return (n/1e6).toFixed(1)+'M'; if (n >= 1e3) return (n/1e3).toFixed(0)+'K'; return n.toString(); }

export function CompareProducersModal({ open, onClose, compareWithId }) {
  const { api, user } = useContext(AuthContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!open || !compareWithId || !user?.id) return;
    setLoading(true);
    api.get(`/players/compare?p1=${user.id}&p2=${compareWithId}`)
      .then(r => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [open, compareWithId, user, api]);

  const p1 = data?.producer_1;
  const p2 = data?.producer_2;

  const metrics = p1 && p2 ? [
    { label: 'Film', icon: <Film size={12} className="text-yellow-400" />, v1: p1.total_films, v2: p2.total_films },
    { label: 'Serie TV', icon: <Tv size={12} className="text-blue-400" />, v1: p1.total_series, v2: p2.total_series },
    { label: 'Anime', icon: <Sparkles size={12} className="text-pink-400" />, v1: p1.total_anime, v2: p2.total_anime },
    { label: 'CWSv Medio', icon: <Star size={12} className="text-amber-400" />, v1: p1.avg_cwsv, v2: p2.avg_cwsv, fmt: v => v > 0 ? v.toFixed(1) : '---' },
    { label: 'Revenue', icon: <TrendingUp size={12} className="text-green-400" />, v1: p1.total_revenue, v2: p2.total_revenue, fmt: v => `$${fmtRev(v)}` },
    { label: 'Fama', icon: <Crown size={12} className="text-purple-400" />, v1: p1.fame, v2: p2.fame, fmt: v => Math.round(v) },
    { label: 'Livello', icon: <Trophy size={12} className="text-cyan-400" />, v1: p1.level, v2: p2.level },
    { label: 'Punteggio', icon: <BarChart3 size={12} className="text-red-400" />, v1: p1.leaderboard_score, v2: p2.leaderboard_score, fmt: v => Math.round(v).toLocaleString() },
  ] : [];

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="bg-[#0A0A0B] border-white/10 max-w-[440px] p-0 [&>button]:hidden" data-testid="compare-producers-modal">
        <DialogHeader className="px-4 pt-4 pb-2">
          <DialogTitle className="text-base flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-purple-400" />
            Confronto Produttori
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 text-purple-400 animate-spin" />
          </div>
        ) : !p1 || !p2 ? (
          <div className="text-center py-12 text-gray-500 text-sm">Confronto non disponibile</div>
        ) : (
          <div className="px-4 pb-4">
            {/* Headers */}
            <div className="grid grid-cols-[1fr_80px_1fr] gap-2 mb-4">
              <ProducerHeader p={p1} side="left" />
              <div className="flex items-center justify-center">
                <span className="text-[10px] text-gray-600 font-bold">VS</span>
              </div>
              <ProducerHeader p={p2} side="right" />
            </div>

            {/* Metrics */}
            <div className="space-y-1.5">
              {metrics.map((m) => {
                const fmt = m.fmt || (v => v);
                const v1 = m.v1 || 0;
                const v2 = m.v2 || 0;
                const winner = v1 > v2 ? 'left' : v2 > v1 ? 'right' : 'tie';
                return (
                  <div key={m.label} className="grid grid-cols-[1fr_80px_1fr] gap-2 items-center" data-testid={`compare-metric-${m.label.toLowerCase().replace(/\s+/g,'-')}`}>
                    <div className={`text-right text-sm font-bold tabular-nums ${winner === 'left' ? 'text-green-400' : winner === 'tie' ? 'text-gray-300' : 'text-gray-500'}`}>
                      {fmt(v1)}
                      {winner === 'left' && <span className="text-[8px] text-green-400 ml-1">W</span>}
                    </div>
                    <div className="flex items-center justify-center gap-1.5 text-[10px] text-gray-400">
                      {m.icon}
                      <span className="truncate">{m.label}</span>
                    </div>
                    <div className={`text-left text-sm font-bold tabular-nums ${winner === 'right' ? 'text-green-400' : winner === 'tie' ? 'text-gray-300' : 'text-gray-500'}`}>
                      {fmt(v2)}
                      {winner === 'right' && <span className="text-[8px] text-green-400 ml-1">W</span>}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Best Production comparison */}
            {(p1.best_production || p2.best_production) && (
              <div className="mt-4 pt-3 border-t border-white/5">
                <p className="text-[9px] text-gray-500 uppercase tracking-wider text-center mb-2">Miglior Produzione</p>
                <div className="grid grid-cols-[1fr_20px_1fr] gap-2">
                  <BestProd prod={p1.best_production} />
                  <div />
                  <BestProd prod={p2.best_production} />
                </div>
              </div>
            )}

            {/* Close button */}
            <button onClick={onClose} className="mt-4 w-full py-2 rounded-lg bg-white/5 border border-white/10 text-gray-400 text-xs hover:bg-white/10 transition" data-testid="compare-close-btn">
              Chiudi
            </button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function ProducerHeader({ p, side }) {
  return (
    <div className={`flex flex-col items-${side === 'left' ? 'end' : 'start'} gap-1`}>
      <div className={`w-10 h-10 rounded-full bg-gradient-to-br from-purple-500/20 to-purple-500/5 flex items-center justify-center text-base font-black text-purple-400 border border-purple-500/20`}>
        {(p.nickname || '?')[0]}
      </div>
      <span className="text-xs font-bold text-white truncate max-w-[120px]">{p.nickname}</span>
      <span className="text-[9px] text-gray-500 truncate max-w-[120px]">{p.production_house_name || ''}</span>
      <Badge className="bg-purple-500/10 text-purple-400 border-0 text-[8px]">Lv.{p.level}</Badge>
    </div>
  );
}

function BestProd({ prod }) {
  if (!prod) return <div className="text-center text-[10px] text-gray-600">---</div>;
  return (
    <div className="rounded-lg bg-amber-500/5 border border-amber-500/10 p-2 text-center">
      <p className="text-[10px] font-bold text-white truncate">{prod.title}</p>
      <p className="text-[9px] text-amber-400">CWSv {prod.cwsv?.toFixed(1) || '?'}</p>
    </div>
  );
}
