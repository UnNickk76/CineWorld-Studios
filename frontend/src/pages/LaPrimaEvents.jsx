import React, { useEffect, useState, useContext, useMemo } from 'react';
import { Star, Trophy, Clock, Info, Ticket, DollarSign, User } from 'lucide-react';
import { AuthContext } from '../contexts';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const imgSrc = (u) => !u ? null : (u.startsWith('http') ? u : `${BACKEND_URL}${u}`);

const TIER_COLORS = {
  legendary: { bg: 'from-amber-400 to-yellow-500', text: 'text-amber-300', ring: 'ring-amber-400/60', glow: '0 0 25px rgba(250,204,21,0.45)' },
  brilliant: { bg: 'from-slate-300 to-gray-400', text: 'text-slate-200', ring: 'ring-slate-300/50', glow: '0 0 18px rgba(203,213,225,0.35)' },
  great:     { bg: 'from-orange-500 to-amber-600', text: 'text-orange-300', ring: 'ring-orange-400/50', glow: '0 0 14px rgba(251,146,60,0.3)' },
  good:      { bg: 'from-stone-500 to-stone-600', text: 'text-stone-300', ring: 'ring-stone-400/40', glow: 'none' },
  ok:        { bg: 'from-gray-600 to-gray-700', text: 'text-gray-300', ring: 'ring-gray-500/40', glow: 'none' },
  weak:      { bg: 'from-gray-700 to-gray-800', text: 'text-gray-400', ring: 'ring-gray-600/30', glow: 'none' },
};

const TIER_LABEL = {
  legendary: 'Leggendaria', brilliant: 'Brillante', great: 'Grandiosa',
  good: 'Buona', ok: 'Discreta', weak: 'Debole',
};

export default function LaPrimaEvents() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [tab, setTab] = useState('daily');
  const [daily, setDaily] = useState(null);
  const [weekly, setWeekly] = useState(null);
  const [formula, setFormula] = useState(null);
  const [myHistory, setMyHistory] = useState(null);
  const [showFormula, setShowFormula] = useState(false);

  useEffect(() => {
    if (!api) return;
    api.get('/events/la-prima/daily').then(r => setDaily(r.data)).catch(() => {});
    api.get('/events/la-prima/weekly').then(r => setWeekly(r.data)).catch(() => {});
    api.get('/events/la-prima/formula').then(r => setFormula(r.data)).catch(() => {});
    api.get('/events/la-prima/my-history').then(r => setMyHistory(r.data)).catch(() => {});
  }, [api]);

  const current = tab === 'daily' ? daily : weekly;

  return (
    <div className="min-h-screen bg-[#050608] text-white pb-24" data-testid="la-prima-events-page">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-[#050608]/95 backdrop-blur border-b border-yellow-500/20 px-3 py-3">
        <div className="flex items-center gap-2">
          <Trophy className="w-5 h-5 text-yellow-400" />
          <h1 className="text-lg font-black tracking-wider" style={{fontFamily:"'Bebas Neue',sans-serif"}}>
            <span className="text-yellow-400">EVENTI LA PRIMA</span>
          </h1>
          <button onClick={() => setShowFormula(!showFormula)}
            className="ml-auto p-1.5 rounded-full bg-yellow-500/15 border border-yellow-500/30 hover:bg-yellow-500/25"
            data-testid="formula-toggle-btn">
            <Info className="w-3.5 h-3.5 text-yellow-400" />
          </button>
        </div>
        <p className="text-[10px] text-gray-500 mt-1">Le La Prima piu' brillanti vincono premi in denaro e CinePass. Il tuo punteggio e' la <span className="text-yellow-400 font-bold">PStar</span>.</p>
      </div>

      {/* Formula explainer */}
      {showFormula && formula && (
        <div className="p-3 bg-yellow-500/5 border-b border-yellow-500/15" data-testid="formula-explainer">
          <p className="text-[10px] text-gray-300 mb-2">{formula.description}</p>
          <div className="space-y-1.5">
            {formula.ingredients.map(ing => (
              <div key={ing.key} className="flex items-center gap-2 text-[10px]">
                <div className="w-20 text-yellow-300 font-bold">{ing.label}</div>
                <div className="flex-1 h-1 bg-black/40 rounded-full overflow-hidden">
                  <div className="h-full bg-yellow-500/60 rounded-full" style={{width:`${(ing.max/100)*100}%`}} />
                </div>
                <div className="text-gray-500 text-[9px] w-24 text-right">{ing.description}</div>
              </div>
            ))}
          </div>
          <p className="text-[9px] text-gray-500 mt-2 italic">Somma totale = <span className="text-yellow-300 font-bold">PStar 0.0 - 100.0</span></p>
          <div className="grid grid-cols-3 gap-1.5 mt-3">
            {formula.tiers.map(t => (
              <div key={t.tier} className="p-1.5 rounded border text-center" style={{borderColor:t.color+'40'}}>
                <p className="text-[9px] font-bold" style={{color:t.color}}>{t.label}</p>
                <p className="text-[7px] text-gray-500">≥{t.min}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* My history summary */}
      {myHistory && myHistory.total_premieres > 0 && (
        <div className="mx-3 mt-3 p-2.5 rounded-lg bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20" data-testid="my-history-summary">
          <div className="flex items-center gap-2">
            <Star className="w-3.5 h-3.5 text-yellow-400" />
            <p className="text-[10px] font-bold text-yellow-400 uppercase tracking-wider">Il mio percorso La Prima</p>
            {myHistory.veteran_unlocked && (
              <span className="ml-auto text-[8px] px-2 py-0.5 rounded-full bg-amber-500/30 text-amber-200 font-bold">VETERANO</span>
            )}
          </div>
          <p className="text-[10px] text-gray-300 mt-1">Premiere completate: <span className="font-black text-yellow-300">{myHistory.total_premieres}</span></p>
          {!myHistory.veteran_unlocked && (
            <p className="text-[8px] text-gray-500">Raggiungi 5 premiere per sbloccare il badge Veterano (+150 fama)</p>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 px-3 mt-3">
        <button onClick={() => setTab('daily')} data-testid="tab-daily"
          className={`flex-1 py-2 rounded-xl border text-[11px] font-bold ${tab === 'daily' ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-300' : 'bg-black/30 border-gray-800 text-gray-500'}`}>
          <Clock className="w-3.5 h-3.5 inline mr-1" /> Giornaliera
        </button>
        <button onClick={() => setTab('weekly')} data-testid="tab-weekly"
          className={`flex-1 py-2 rounded-xl border text-[11px] font-bold ${tab === 'weekly' ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-300' : 'bg-black/30 border-gray-800 text-gray-500'}`}>
          <Trophy className="w-3.5 h-3.5 inline mr-1" /> Settimanale
        </button>
      </div>

      {/* Leaderboard */}
      <div className="p-3 space-y-2" data-testid={`leaderboard-${tab}`}>
        {!current ? (
          <p className="text-gray-500 text-xs text-center py-8">Caricamento...</p>
        ) : current.items.length === 0 ? (
          <div className="text-center py-10">
            <Trophy className="w-10 h-10 text-gray-700 mx-auto mb-2" />
            <p className="text-xs text-gray-400">Nessuna La Prima in classifica {tab === 'daily' ? 'oggi' : 'questa settimana'}.</p>
            <p className="text-[10px] text-gray-600 mt-1">Sii il primo a pubblicare una La Prima memorabile!</p>
          </div>
        ) : (
          current.items.map((e) => {
            const tier = e.tier || 'ok';
            const clr = TIER_COLORS[tier];
            const medal = e.rank === 1 ? '🥇' : e.rank === 2 ? '🥈' : e.rank === 3 ? '🥉' : null;
            return (
              <div key={e.film_id}
                onClick={() => navigate(`/films/${e.film_id}`)}
                className={`flex items-center gap-3 p-2.5 rounded-xl border bg-black/40 cursor-pointer active:scale-[0.98] transition-all ring-1 ${clr.ring}`}
                style={{ boxShadow: clr.glow }}
                data-testid={`pstar-row-${e.film_id}`}>
                <div className="flex-shrink-0 w-8 text-center">
                  {medal ? <span className="text-xl">{medal}</span> : <span className={`text-sm font-black ${clr.text}`}>#{e.rank}</span>}
                </div>
                {e.poster_url && (
                  <div className="w-10 h-14 rounded overflow-hidden bg-gray-900 flex-shrink-0">
                    <img src={imgSrc(e.poster_url)} alt="" className="w-full h-full object-cover" loading="lazy"
                      onError={(ev) => { ev.target.style.display = 'none'; }} />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] font-bold text-white truncate">{e.title}</p>
                  <p className="text-[9px] text-gray-500 truncate">{e.city} · {e.owner_nickname}</p>
                  {e.prize && (
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="flex items-center gap-0.5 text-[9px] text-emerald-400 font-bold"><DollarSign className="w-2.5 h-2.5" />{e.prize.money >= 1000000 ? (e.prize.money/1000000).toFixed(1)+'M' : (e.prize.money/1000).toFixed(0)+'K'}</span>
                      <span className="flex items-center gap-0.5 text-[9px] text-cyan-400 font-bold"><Ticket className="w-2.5 h-2.5" />{e.prize.cinepass}</span>
                    </div>
                  )}
                </div>
                <div className="flex-shrink-0 text-right">
                  <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gradient-to-r ${clr.bg}`}>
                    <Star className="w-3 h-3 text-black fill-black" />
                    <span className="text-[11px] font-black text-black">{e.score?.toFixed(1)}</span>
                  </div>
                  <p className="text-[8px] text-gray-500 mt-0.5 uppercase tracking-wider">{TIER_LABEL[tier]}</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

/**
 * Reusable card showing a film's PStar score with ingredient breakdown.
 */
export function PStarScoreCard({ entry }) {
  if (!entry) return null;
  const tier = entry.tier || 'ok';
  const clr = TIER_COLORS[tier];
  const ing = entry.ingredients || {};
  const items = [
    { key: 'quality', label: 'Qualita CWSv', value: ing.quality || 0 },
    { key: 'hype', label: 'Hype', value: ing.hype || 0 },
    { key: 'affluence', label: 'Affluenza', value: ing.affluence || 0 },
    { key: 'city_match', label: 'Citta Match', value: ing.city_match || 0 },
    { key: 'earnings', label: 'Guadagni', value: ing.earnings || 0 },
  ];
  return (
    <div className={`rounded-2xl border bg-gradient-to-br from-[#1a1508] to-[#0d0906] p-4 ring-1 ${clr.ring}`} style={{ boxShadow: clr.glow }} data-testid="pstar-score-card">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-[10px] font-bold text-yellow-400 uppercase tracking-widest">PStar</p>
          <p className="text-[8px] text-gray-500">La Prima a {entry.city}</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r ${clr.bg}`}>
          <Star className="w-5 h-5 text-black fill-black" />
          <span className="text-2xl font-black text-black">{entry.score?.toFixed(1)}</span>
        </div>
      </div>
      <p className={`text-center text-[9px] font-bold uppercase tracking-wider ${clr.text} mb-3`}>{TIER_LABEL[tier]}</p>
      <div className="space-y-1.5">
        {items.map(i => (
          <div key={i.key} className="flex items-center gap-2">
            <span className="text-[9px] text-gray-400 w-20 flex-shrink-0">{i.label}</span>
            <div className="flex-1 h-1.5 rounded-full bg-black/60 overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-yellow-500 to-amber-400" style={{width:`${(i.value/20)*100}%`}} />
            </div>
            <span className="text-[9px] font-bold text-yellow-300 w-8 text-right">{i.value?.toFixed(1)}</span>
          </div>
        ))}
      </div>
      {(entry.daily_rank || entry.weekly_rank) && (
        <div className="mt-3 flex items-center gap-2 p-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <Trophy className="w-3.5 h-3.5 text-yellow-400" />
          <p className="text-[10px] text-yellow-300 font-bold">
            {entry.daily_rank && <>Giornaliera #{entry.daily_rank}</>}
            {entry.daily_rank && entry.weekly_rank && ' · '}
            {entry.weekly_rank && <>Settimanale #{entry.weekly_rank}</>}
          </p>
        </div>
      )}
    </div>
  );
}
