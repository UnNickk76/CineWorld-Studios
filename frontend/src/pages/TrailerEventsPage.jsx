import React, { useContext, useEffect, useState } from 'react';
import { ArrowLeft, Trophy, Crown, Calendar, Tag, Film, Play, Sparkles, Medal, Award, HelpCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import TrailerPlayerModal from '../components/TrailerPlayerModal';

const TABS = [
  { id: 'daily', label: 'Giornaliera', icon: Calendar, color: 'text-cyan-300' },
  { id: 'weekly', label: 'Settimanale', icon: Trophy, color: 'text-purple-300' },
  { id: 'genre', label: 'Per Genere', icon: Tag, color: 'text-amber-300' },
  { id: 'hof', label: 'Hall of Fame', icon: Crown, color: 'text-yellow-300' },
  { id: 'me', label: 'I Miei', icon: Medal, color: 'text-emerald-300' },
];

const GENRES = ['action', 'drama', 'horror', 'comedy', 'romance', 'sci_fi', 'thriller', 'fantasy', 'documentary', 'animation'];

export default function TrailerEventsPage() {
  const navigate = useNavigate();
  const { api, user } = useContext(AuthContext) || {};
  const [tab, setTab] = useState('daily');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [genre, setGenre] = useState('action');
  const [formula, setFormula] = useState(null);
  const [showFormula, setShowFormula] = useState(false);
  const [selected, setSelected] = useState(null);
  const [trailerData, setTrailerData] = useState(null);

  useEffect(() => {
    if (!api) return;
    api.get('/events/trailers/formula').then(r => setFormula(r.data)).catch(() => {});
  }, [api]);

  useEffect(() => {
    if (!api) return;
    setLoading(true);
    const req = tab === 'daily' ? api.get('/events/trailers/daily')
              : tab === 'weekly' ? api.get('/events/trailers/weekly')
              : tab === 'genre' ? api.get('/events/trailers/by-genre', { params: { genre } })
              : tab === 'hof' ? api.get('/events/trailers/hall-of-fame')
              : api.get('/events/trailers/my-history');
    req.then(r => setData(r.data)).catch(() => setData({ items: [] })).finally(() => setLoading(false));
  }, [api, tab, genre]);

  const posterUrl = (p) => {
    if (!p) return null;
    if (p.startsWith('http') || p.startsWith('data:')) return p;
    return `${process.env.REACT_APP_BACKEND_URL}${p}`;
  };

  const openTrailer = async (item) => {
    try {
      const r = await api.get(`/trailers/${item.content_id}`);
      if (r.data?.trailer) {
        setTrailerData(r.data.trailer);
        setSelected(item);
      }
    } catch { /* */ }
  };

  const items = data?.items || [];

  const tstarColor = (score) => {
    if (score >= 85) return 'text-yellow-300 border-yellow-400/60';
    if (score >= 70) return 'text-gray-200 border-gray-400/60';
    if (score >= 55) return 'text-orange-300 border-orange-400/60';
    if (score >= 40) return 'text-emerald-300 border-emerald-400/60';
    if (score >= 25) return 'text-sky-300 border-sky-400/60';
    return 'text-gray-400 border-gray-700/60';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0c15] via-[#0d0e1a] to-[#060810] text-white pb-20" data-testid="trailer-events-page">
      {/* Header */}
      <div className="sticky top-0 z-30 backdrop-blur-xl bg-black/70 border-b border-white/5">
        <div className="max-w-5xl mx-auto px-3 py-3 flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10" data-testid="trailer-events-back">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-black tracking-wider text-white flex items-center gap-2">
              <Trophy className="w-4 h-4 text-yellow-400" />
              EVENTI TRAILER
            </h1>
            <p className="text-[9px] text-gray-400 truncate">TStar 0-100 · Premi giornalieri e settimanali</p>
          </div>
          <button onClick={() => setShowFormula(v => !v)} className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 hover:bg-amber-500/20" data-testid="trailer-events-formula-btn">
            <HelpCircle className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-3 pt-3">
        {/* Formula explainer */}
        {showFormula && formula && (
          <div className="mb-3 p-3 rounded-xl border border-amber-500/30 bg-amber-500/5" data-testid="formula-card">
            <p className="text-[11px] font-black text-amber-300 mb-2">{formula.title} · come funziona</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {formula.components?.map(c => (
                <div key={c.key} className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  <span className="text-[10px] font-bold text-white">{c.label}</span>
                  <span className="text-[9px] text-gray-400">max {c.max}</span>
                  <span className="text-[8px] text-gray-500">— {c.desc}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 overflow-x-auto pb-2 -mx-3 px-3 sm:-mx-0 sm:px-0 snap-x">
          {TABS.map(t => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`snap-start shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all ${
                  active ? 'bg-white/10 border border-white/20' : 'bg-white/[0.02] border border-white/5 text-gray-400'
                }`}
                data-testid={`trailer-events-tab-${t.id}`}>
                <Icon className={`w-3.5 h-3.5 ${active ? t.color : 'text-gray-500'}`} />
                <span className={active ? t.color : ''}>{t.label}</span>
              </button>
            );
          })}
        </div>

        {/* Genre filter */}
        {tab === 'genre' && (
          <div className="mt-2 flex gap-1 overflow-x-auto pb-2">
            {GENRES.map(g => (
              <button key={g} onClick={() => setGenre(g)}
                className={`shrink-0 px-2.5 py-1 rounded-md text-[9px] font-bold uppercase border transition-all ${
                  genre === g ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' : 'bg-white/[0.02] border-white/5 text-gray-500'
                }`}>{g}</button>
            ))}
          </div>
        )}

        {/* My stats summary */}
        {tab === 'me' && data && (
          <div className="mt-3 grid grid-cols-3 gap-2" data-testid="my-trailer-stats">
            <div className="p-2 rounded-xl bg-white/[0.03] border border-white/5">
              <p className="text-[8px] text-gray-500 uppercase">Trailer creati</p>
              <p className="text-xl font-black text-white">{data.total ?? 0}</p>
            </div>
            <div className="p-2 rounded-xl bg-white/[0.03] border border-white/5">
              <p className="text-[8px] text-gray-500 uppercase">Vittorie</p>
              <p className="text-xl font-black text-emerald-300">{data.total_wins ?? 0}</p>
            </div>
            <div className={`p-2 rounded-xl bg-white/[0.03] border border-white/5 ${data.badge_maestro ? 'ring-1 ring-yellow-400/40' : ''}`}>
              <p className="text-[8px] text-gray-500 uppercase flex items-center gap-1">Badge <Award className="w-3 h-3" /></p>
              <p className={`text-xs font-black ${data.badge_maestro ? 'text-yellow-300' : 'text-gray-500'}`}>{data.badge_maestro ? 'MAESTRO' : '—'}</p>
            </div>
          </div>
        )}

        {/* Leaderboard list */}
        <div className="mt-3 space-y-2">
          {loading && (
            <div className="text-center py-12 text-gray-500 text-xs">Caricamento…</div>
          )}
          {!loading && items.length === 0 && (
            <div className="text-center py-12 text-gray-500 text-xs">
              Nessun trailer per questa categoria.
              {tab !== 'me' && <><br/>Genera il tuo trailer e potresti entrare in classifica!</>}
            </div>
          )}
          {!loading && items.map((it, i) => {
            const rank = it.rank || (i + 1);
            const rankColor = rank === 1 ? 'text-yellow-300' : rank === 2 ? 'text-gray-200' : rank === 3 ? 'text-orange-300' : 'text-gray-500';
            const isOwn = it.owner_id === user?.id;
            const tstar = Math.round(it.tstar ?? 0);
            return (
              <div key={`${it.content_id}-${i}`}
                className={`p-2.5 rounded-xl border bg-white/[0.02] flex items-center gap-2.5 ${isOwn ? 'border-emerald-500/30 bg-emerald-500/[0.04]' : 'border-white/5'}`}
                data-testid={`trailer-lb-item-${it.content_id}`}>
                <span className={`text-xl font-black w-7 text-center shrink-0 ${rankColor}`}>#{rank}</span>
                <button onClick={() => openTrailer(it)} className="relative w-12 h-16 rounded-lg overflow-hidden shrink-0 bg-gray-800 group">
                  {posterUrl(it.poster_url) && (
                    <img src={posterUrl(it.poster_url)} alt="" className="absolute inset-0 w-full h-full object-cover" onError={e => { e.target.style.display = 'none'; }} />
                  )}
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Play className="w-5 h-5 text-white fill-white" />
                  </div>
                </button>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-bold text-white truncate">{it.title}</p>
                  <p className="text-[9px] text-gray-400 truncate">
                    {it.owner_nickname && <>di <span className="text-white">{it.owner_nickname}</span></>}
                    {it.owner_studio && <span className="text-gray-500"> · {it.owner_studio}</span>}
                  </p>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span className="text-[8px] px-1.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-gray-300 uppercase font-bold">{it.tier}</span>
                    {it.mode === 'highlights' && <span className="text-[8px] px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-300 font-black">HIGHLIGHTS</span>}
                    <span className="text-[8px] text-gray-400 flex items-center gap-0.5"><Film className="w-2.5 h-2.5" />{it.views_count} viste</span>
                    {it.likes_count > 0 && <span className="text-[8px] text-emerald-300">▲{it.likes_count}</span>}
                  </div>
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1">
                  <span className={`text-[9px] px-2 py-0.5 rounded-full font-black border bg-black/40 ${tstarColor(it.tstar)}`}>
                    TStar {tstar}
                  </span>
                  {it.prize && (
                    <div className="text-[8px] text-yellow-300 font-bold flex items-center gap-0.5">
                      <Sparkles className="w-2.5 h-2.5" />
                      ${(it.prize.funds / 1000).toFixed(0)}K + {it.prize.cinepass}CP
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Prize table preview */}
        {(tab === 'daily' || tab === 'weekly') && data?.prizes && (
          <div className="mt-5 p-3 rounded-xl border border-yellow-500/20 bg-yellow-500/[0.03]" data-testid="trailer-prizes-table">
            <p className="text-[11px] font-black text-yellow-300 mb-2 uppercase tracking-wider">Tabella Premi {tab === 'daily' ? 'Giornalieri' : 'Settimanali'}</p>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-1">
              {data.prizes.map(p => (
                <div key={p.rank} className="p-1.5 rounded-lg bg-black/30 border border-white/5 text-center">
                  <p className="text-[9px] text-gray-400">#{p.rank}</p>
                  <p className="text-[8px] text-yellow-300 font-bold">${(p.funds / 1000).toFixed(0)}K</p>
                  <p className="text-[8px] text-cyan-300">{p.cinepass} CP</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {selected && trailerData && (
        <TrailerPlayerModal
          trailer={trailerData}
          contentTitle={selected.title}
          contentGenre={selected.genre || ''}
          contentId={selected.content_id}
          currentUserId={user?.id}
          api={api}
          onClose={() => { setSelected(null); setTrailerData(null); }}
        />
      )}
    </div>
  );
}
