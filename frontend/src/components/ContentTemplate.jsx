import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { toast } from 'sonner';
import {
  Film, Star, Flame, Users, DollarSign, Heart, ChevronRight, X, Play,
  Building, Sparkles, BookOpen, Clapperboard, Zap, Loader2,
  Newspaper, Crown, Award, Pen, Clock, Tv, Popcorn, Eye
} from 'lucide-react';
import LikeButton, { SystemLikeBadge, PreReleaseSnapshotBadge } from './LikeButton';
import TrailerPlayerModal from './TrailerPlayerModal';
import PStarBanner from './PStarBanner';
import '../styles/content-template.css';

// ═══ THEATER INFO BAR — expandable cinema stats + owner actions ═══
const TheaterInfoBar = ({ film }) => {
  const authCtx = useContext(AuthContext) || {};
  const user = authCtx.user;
  const [loading, setLoading] = useState('');
  const [stats, setStats] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);
  const [tvStations, setTvStations] = useState([]);
  const [selectedTv, setSelectedTv] = useState('');

  const ts = film?.theater_stats || {};
  const isReleased = film?.pipeline_state === 'released' || (Number(film?.cinemas_showing) > 0) || (Number(film?.cinema_count) > 0);
  const isOwner = user?.id === film?.user_id;
  const BACKEND = process.env.REACT_APP_BACKEND_URL || '';

  const fetchStats = () => {
    const token = localStorage.getItem('cineworld_token');
    if (!token || !film?.id) return;
    fetch(`${BACKEND}/api/pipeline-v2/films/${film.id}/theater-stats`, { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json()).then(d => setStats(d?.theater_stats || d)).catch(() => {});
  };

  const fetchTvStations = () => {
    const token = localStorage.getItem('cineworld_token');
    if (!token) return;
    fetch(`${BACKEND}/api/my-tv/stations`, { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json()).then(d => setTvStations(Array.isArray(d) ? d : d?.stations || [])).catch(() => setTvStations([]));
  };

  const doWithdraw = async () => {
    setConfirmAction(null); setLoading('withdraw');
    try {
      const token = localStorage.getItem('cineworld_token');
      await fetch(`${BACKEND}/api/pipeline-v2/films/${film.id}/withdraw-theater`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } });
      toast.success('Film ritirato dalle sale');
      window.location.reload();
    } catch (e) { toast.error('Errore'); }
    setLoading('');
  };

  const doSendToTv = async () => {
    setConfirmAction(null); setLoading('tv');
    try {
      const token = localStorage.getItem('cineworld_token');
      // Send to TV (also withdraws from cinema)
      await fetch(`${BACKEND}/api/pipeline-v2/films/${film.id}/send-to-tv`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ station_id: selectedTv }) });
      if (isReleased) {
        await fetch(`${BACKEND}/api/pipeline-v2/films/${film.id}/withdraw-theater`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } });
      }
      toast.success('Film inviato in TV!');
      window.location.reload();
    } catch (e) { toast.error('Errore'); }
    setLoading('');
  };

  const doSendUpcoming = async () => {
    setConfirmAction(null); setLoading('upcoming');
    try {
      const token = localStorage.getItem('cineworld_token');
      await fetch(`${BACKEND}/api/pipeline-v2/films/${film.id}/send-to-tv`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ station_id: selectedTv, as_upcoming: true }) });
      toast.success('Film aggiunto ai Prossimamente in TV!');
      window.location.reload();
    } catch (e) { toast.error('Errore'); }
    setLoading('');
  };

  const perfColors = { great:'text-green-400', good:'text-emerald-400', ok:'text-yellow-400', declining:'text-orange-400', bad:'text-red-400', flop:'text-red-500' };
  const perfLabels = { great:'Straordinario', good:'Ottimo', ok:'Discreto', declining:'In calo', bad:'Scarso', flop:'Flop' };
  const fullStats = stats?.theater_stats || stats || ts;

  // Auto-fetch stats on mount
  useEffect(() => {
    if (!stats) { fetchStats(); if (isOwner) fetchTvStations(); }
  }, [film.id]);

  return (
    <div className="mx-4 mb-1 rounded-lg border border-yellow-500/15 bg-black/30 p-2.5 space-y-2" data-testid="ct-theater-panel">
      <div className="grid grid-cols-3 gap-1.5">
        <div className="text-center p-1.5 rounded bg-white/[0.03] border border-white/5">
          <p className="text-[7px] text-gray-500">Cinema</p>
          <p className="text-[11px] font-bold text-white">{Number(fullStats.current_cinemas) || 0}</p>
        </div>
        <div className="text-center p-1.5 rounded bg-white/[0.03] border border-white/5">
          <p className="text-[7px] text-gray-500">Spett. oggi</p>
          <p className="text-[11px] font-bold text-cyan-400">{Number(fullStats.daily_spectators || 0).toLocaleString()}</p>
        </div>
        <div className="text-center p-1.5 rounded bg-white/[0.03] border border-white/5">
          <p className="text-[7px] text-gray-500">Spett. totali</p>
          <p className="text-[11px] font-bold text-yellow-400">{Number(fullStats.total_spectators || 0).toLocaleString()}</p>
        </div>
      </div>
      {fullStats.daily_history?.length > 0 && (
        <div>
          <p className="text-[7px] text-gray-500 uppercase font-bold mb-1">Ultimi 3 giorni</p>
          <div className="flex gap-1">
            {(fullStats.daily_history || []).slice(-3).map((d, i) => (
              <div key={i} className="flex-1 p-1 rounded bg-white/[0.02] border border-white/5 text-center">
                <p className="text-[7px] text-gray-600">G{d.day}</p>
                <p className={`text-[8px] font-bold ${d.trend === 'up' ? 'text-green-400' : d.trend === 'down' ? 'text-red-400' : 'text-gray-400'}`}>{d.trend === 'up' ? '▲' : d.trend === 'down' ? '▼' : '●'} {d.spectators?.toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="flex justify-between px-1 text-[8px]">
        <span className="text-gray-500">Incassi sala</span>
        <span className="font-bold text-green-400">${Number(fullStats.total_revenue || 0).toLocaleString()}</span>
      </div>
      {isOwner && (
        <div className="space-y-1.5 pt-1">
          {tvStations.length > 0 && (
            <select value={selectedTv} onChange={e => setSelectedTv(e.target.value)}
              className="w-full bg-gray-800 text-[9px] text-white border border-gray-700 rounded px-2 py-1.5">
              <option value="">Scegli emittente TV...</option>
              {tvStations.map(s => <option key={s.id || s.name} value={s.id || s.name}>{s.name || s.channel_name}</option>)}
            </select>
          )}
          <div className="flex gap-1.5">
            {isReleased && (
              <button onClick={() => setConfirmAction('withdraw')} disabled={!!loading}
                className="flex-1 text-[8px] py-1.5 rounded bg-red-500/10 border border-red-500/20 text-red-400 font-bold disabled:opacity-40" data-testid="ct-withdraw-btn">
                {loading === 'withdraw' ? '...' : 'Ritira dal cinema'}
              </button>
            )}
            {selectedTv && (
              <>
                <button onClick={() => setConfirmAction('tv')} disabled={!!loading}
                  className="flex-1 text-[8px] py-1.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 font-bold disabled:opacity-40" data-testid="ct-send-tv-btn">
                  {loading === 'tv' ? '...' : 'Manda in TV'}
                </button>
                <button onClick={() => setConfirmAction('upcoming')} disabled={!!loading}
                  className="flex-1 text-[8px] py-1.5 rounded bg-purple-500/10 border border-purple-500/20 text-purple-400 font-bold disabled:opacity-40" data-testid="ct-upcoming-tv-btn">
                  {loading === 'upcoming' ? '...' : 'Prossimamente TV'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
      {confirmAction === 'withdraw' && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center px-4" onClick={() => setConfirmAction(null)}>
          <div className="absolute inset-0 bg-black/60" />
          <div className="relative bg-[#111113] rounded-2xl p-4 border border-red-500/20 max-w-sm w-full" onClick={e => e.stopPropagation()}>
            <p className="text-sm font-bold text-white mb-1">Ritirare il film dalle sale?</p>
            <p className="text-[10px] text-gray-400 mb-3">Il film uscirà immediatamente dal cinema.</p>
            <div className="flex gap-2">
              <button onClick={() => setConfirmAction(null)} className="flex-1 text-[10px] py-2 rounded-lg bg-gray-800 text-gray-400">Annulla</button>
              <button onClick={doWithdraw} className="flex-1 text-[10px] py-2 rounded-lg bg-red-600 text-white font-bold">Ritira</button>
            </div>
          </div>
        </div>
      )}
      {confirmAction === 'tv' && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center px-4" onClick={() => setConfirmAction(null)}>
          <div className="absolute inset-0 bg-black/60" />
          <div className="relative bg-[#111113] rounded-2xl p-4 border border-blue-500/20 max-w-sm w-full" onClick={e => e.stopPropagation()}>
            <p className="text-sm font-bold text-white mb-1">Inviare in TV e ritirare dalle sale?</p>
            <p className="text-[10px] text-gray-400 mb-3">Il film verrà ritirato dal cinema e messo in programmazione TV.</p>
            <div className="flex gap-2">
              <button onClick={() => setConfirmAction(null)} className="flex-1 text-[10px] py-2 rounded-lg bg-gray-800 text-gray-400">Annulla</button>
              <button onClick={doSendToTv} className="flex-1 text-[10px] py-2 rounded-lg bg-blue-600 text-white font-bold">Conferma</button>
            </div>
          </div>
        </div>
      )}
      {confirmAction === 'upcoming' && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center px-4" onClick={() => setConfirmAction(null)}>
          <div className="absolute inset-0 bg-black/60" />
          <div className="relative bg-[#111113] rounded-2xl p-4 border border-purple-500/20 max-w-sm w-full" onClick={e => e.stopPropagation()}>
            <p className="text-sm font-bold text-white mb-1">Aggiungere ai Prossimamente in TV?</p>
            <p className="text-[10px] text-gray-400 mb-3">Quando uscirà dalle sale andrà automaticamente in programmazione.</p>
            <div className="flex gap-2">
              <button onClick={() => setConfirmAction(null)} className="flex-1 text-[10px] py-2 rounded-lg bg-gray-800 text-gray-400">Annulla</button>
              <button onClick={doSendUpcoming} className="flex-1 text-[10px] py-2 rounded-lg bg-purple-600 text-white font-bold">Conferma</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};
const fmtMoney = (n) => {
  if (!n || n === 0) return '$0';
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
  return `$${n.toLocaleString()}`;
};

// === STATUS MAPPING ===
// Returns { label, cls } for the top status bar. Covers all V3 pipeline phases,
// legacy statuses and series/anime TV broadcast state. `cls` maps to animated
// glow variants defined in content-template.css.
function getStatusInfo(film, contentType) {
  const s = (film?.status || '').toLowerCase();
  const ps = (film?.pipeline_state || '').toLowerCase();
  const cinemas = film?.current_cinemas || 0;
  const onTv = film?.on_tv || film?.tv_broadcast || false;
  const isSeriesLike = contentType === 'series' || contentType === 'anime' || film?.type === 'tv_series' || film?.type === 'anime';

  // 1) AL CINEMA / IN TV — release state (highest priority for released content)
  if (cinemas > 0 || s === 'in_theaters') {
    return { label: isSeriesLike ? 'In TV' : 'Al Cinema', cls: isSeriesLike ? 'ct2-status-ontv' : 'ct2-status-cinema' };
  }
  if (onTv) {
    return { label: 'In TV', cls: 'ct2-status-ontv' };
  }

  // 2) LA PRIMA (either V3 pipeline phase, legacy status, or premiere flags)
  if (ps === 'la_prima' || ps === 'premiere_live' || ps === 'premiere_setup' ||
      s.includes('prima') || s === 'premiere_live' || s === 'premiere_setup') {
    return { label: 'La Prima', cls: 'ct2-status-laprima' };
  }

  // 3) V3 pipeline phases (takes priority when present)
  const V3_PHASE = {
    idea: { label: 'Sceneggiatura', cls: 'ct2-status-screenplay' },
    hype: { label: 'Hype', cls: 'ct2-status-hype' },
    cast: { label: 'Casting', cls: 'ct2-status-cast' },
    prep: { label: 'Pre-Produzione', cls: 'ct2-status-prep' },
    ciak: { label: 'Riprese', cls: 'ct2-status-shooting' },
    finalcut: { label: 'Final Cut', cls: 'ct2-status-finalcut' },
    marketing: { label: 'Marketing', cls: 'ct2-status-marketing' },
    distribution: { label: 'Distribuzione', cls: 'ct2-status-distribution' },
    release_pending: { label: 'In Uscita', cls: 'ct2-status-coming' },
  };
  if (V3_PHASE[ps]) return V3_PHASE[ps];

  // 4) Legacy statuses
  if (s === 'coming_soon' || s === 'pending_release' || s === 'release_pending' || s.includes('hype')) {
    return { label: 'Prossimamente', cls: 'ct2-status-coming' };
  }
  if (s === 'shooting' || s === 'in_production' || s === 'production') {
    return { label: 'Riprese', cls: 'ct2-status-shooting' };
  }
  if (s === 'casting' || s === 'ready_for_casting') {
    return { label: 'Casting', cls: 'ct2-status-cast' };
  }
  if (s === 'screenplay' || s === 'draft' || s === 'proposed' || s === 'concept' || s === 'idea') {
    return { label: 'Sceneggiatura', cls: 'ct2-status-screenplay' };
  }
  if (s === 'pre_production' || s === 'prep') {
    return { label: 'Pre-Produzione', cls: 'ct2-status-prep' };
  }
  if (s === 'post_production' || s === 'completed' || s === 'ready_to_release') {
    return { label: 'Post-Produzione', cls: 'ct2-status-finalcut' };
  }
  if (s === 'remastering') {
    return { label: 'In Remastering', cls: 'ct2-status-finalcut' };
  }

  // 5) Fallback: released / in catalogo
  return { label: 'In Catalogo', cls: 'ct2-status-catalogo' };
}

// === CRITIC REVIEWS ===
const FILM_OUTLETS = ['VARIETY', 'EMPIRE', 'HOLLYWOOD R.'];
const SERIES_OUTLETS = ['IGN', 'COLLIDER', 'ENTERTAINMENT W.'];
const POSITIVE_QUOTES = {
  VARIETY: ["Un'esperienza cinematografica straordinaria!", "Un'opera che ridefinisce il genere", "Spettacolare da ogni punto di vista"],
  EMPIRE: ["Impressionante dall'inizio alla fine", "Un capolavoro moderno del cinema", "Emozionante e visivamente stupendo"],
  'HOLLYWOOD R.': ["Uno dei migliori film degli ultimi anni", "Un trionfo del cinema contemporaneo", "Destinato a diventare un classico"],
  IGN: ["Intrigante e piena di suspense!", "Una serie che alza il livello del genere", "Da non perdere assolutamente"],
  COLLIDER: ["Una serie crime da non perdere!", "Narrativa avvincente e cast perfetto", "Uno show di altissimo livello"],
  'ENTERTAINMENT W.': ["Un thriller che tiene incollati alla sedia!", "Televisione di qualita superiore", "Imperdibile dall'inizio alla fine"],
};
const MIXED_QUOTES = {
  VARIETY: ["Ambizioso ma non sempre riuscito", "Ha momenti brillanti e altri meno"],
  EMPIRE: ["Interessante ma con alti e bassi", "Un buon film con qualche difetto"],
  'HOLLYWOOD R.': ["Promettente ma imperfetto", "Merita una visione, con riserve"],
  IGN: ["Buona premessa ma esecuzione altalenante", "Intrattiene senza sorprendere"],
  COLLIDER: ["Una serie dignitosa con margini di crescita", "Merita una chance, con riserve"],
  'ENTERTAINMENT W.': ["Alti e bassi in ogni episodio", "Ha potenziale ma non lo esprime tutto"],
};

function generateReviews(quality, hype, contentType) {
  const outlets = contentType === 'series' ? SERIES_OUTLETS : FILM_OUTLETS;
  const score = (quality || 50) / 10;
  return outlets.map((outlet) => {
    const pool = score >= 7 ? POSITIVE_QUOTES[outlet] : MIXED_QUOTES[outlet];
    const idx = Math.floor((hype || 0) % pool.length);
    return { outlet, quote: pool[idx] };
  });
}

const toStr = (v) => typeof v === 'string' ? v : (v?.text || v?.content || '');

// Clean markdown artifacts from screenplay/plot text
const cleanText = (text) => {
  if (!text) return '';
  return text
    .replace(/\*\*([^*]+)\*\*/g, '$1')  // **bold** → bold
    .replace(/\*([^*]+)\*/g, '$1')        // *italic* → italic
    .replace(/^#{1,3}\s+/gm, '')          // # headers
    .replace(/^[-*]\s+/gm, '')            // bullet points
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // [link](url) → link
    .replace(/\n{3,}/g, '\n\n')           // multiple newlines
    .trim();
};

// === DURATION FORMATTER ===
function formatDuration(film, contentType) {
  if (contentType === 'series' || contentType === 'anime') {
    const eps = film?.num_episodes || film?.episode_count;
    const epMin = film?.episode_runtime_minutes;
    if (eps && epMin) return `${eps} episodi | ${epMin}m`;
    if (eps) return `${eps} episodi`;
    return null;
  }
  const min = film?.duration_minutes;
  if (min) {
    const h = Math.floor(min / 60);
    const m = min % 60;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  }
  // Fallback: estimate from duration_category
  const cat = film?.duration_category;
  const catLabels = { cortometraggio: '~30m', feature_breve: '~60m', standard: '~110m', extended: '~170m', kolossal: '~240m' };
  if (cat && catLabels[cat]) return catLabels[cat];
  // Default fallback for films without duration data
  if (film?.pipeline_state && film.pipeline_state !== 'draft') return '~110m';
  return null;
}

// === CAST EXTRACTOR (top 4-5, sorted by fame then value) ===
function extractCastInfo(cast, film) {
  let director = null;
  let actors = [];

  // Director from film.director (old format) or cast.director (V2)
  if (film?.director?.name) {
    director = film.director.name;
  }

  if (!cast) return { director, actors: [] };

  if (Array.isArray(cast)) {
    actors = cast.filter(a => a && a.name);
  } else if (typeof cast === 'object') {
    if (!director && cast.director?.name) director = cast.director.name;
    if (Array.isArray(cast.actors)) {
      actors = cast.actors.filter(a => a && a.name);
    }
    ['protagonist', 'antagonist', 'co_protagonist'].forEach(k => {
      if (cast[k]?.name && !actors.find(a => a.name === cast[k].name)) {
        actors.unshift(cast[k]);
      }
    });
  }

  actors.sort((a, b) => {
    const fameA = a.fame || a.fame_score || 0;
    const fameB = b.fame || b.fame_score || 0;
    if (fameB !== fameA) return fameB - fameA;
    return (b.value || b.skill || 0) - (a.value || a.skill || 0);
  });

  return { director, actors: actors.slice(0, 5) };
}

// === PUBLIC PERCEPTION ===
function getPublicPerception(film) {
  const q = film?.quality_score || 50;
  const likes = film?.virtual_likes || film?.likes_count || 0;
  const hype = film?.hype_score || film?.popularity_score || 0;

  const lines = [];
  if (q >= 80) lines.push('Pubblico entusiasta');
  else if (q >= 60) lines.push('Pubblico soddisfatto');
  else if (q >= 40) lines.push('Reazioni miste dal pubblico');
  else lines.push('Pubblico deluso');

  if (likes > 5000) lines.push('Passaparola in crescita');
  else if (likes > 1000) lines.push('Interesse moderato');

  if (hype > 70) lines.push('Boom di interesse');
  else if (hype > 40) lines.push('Attenzione mediatica stabile');

  return lines;
}

function getEventHeadlines(film) {
  const ev = film?.release_event || film?.news_events;
  if (!ev) return [];
  if (typeof ev === 'string') return [ev];
  if (typeof ev === 'number') return [String(ev)];
  // Object with text fields
  if (typeof ev === 'object' && !Array.isArray(ev)) {
    const txt = ev.description || ev.name || ev.text || ev.title;
    return txt ? [String(txt)] : [];
  }
  if (Array.isArray(ev)) {
    return ev.slice(0, 2).map(e => {
      if (typeof e === 'string') return e;
      if (typeof e === 'number') return String(e);
      if (e && typeof e === 'object') return String(e?.description || e?.name || e?.text || e?.title || '');
      return '';
    }).filter(Boolean);
  }
  return [];
}

// === SUB-POPUP: Cast & Crew ===
const CastPopup = ({ open, onClose, cast }) => {
  const members = [];
  if (cast) {
    if (Array.isArray(cast)) {
      cast.forEach((a) => { if (a && typeof a === 'object') members.push({ ...a, role: a.role_in_film || a.role || 'Attore' }); });
    } else if (typeof cast === 'object') {
      if (cast.director && typeof cast.director === 'object') members.push({ ...cast.director, role: 'Regista' });
      if (Array.isArray(cast.actors)) {
        cast.actors.forEach((a) => { if (a && typeof a === 'object') members.push({ ...a, role: a.role_in_film || a.role || 'Attore' }); });
      }
      Object.entries(cast).forEach(([key, val]) => {
        if (key !== 'director' && key !== 'actors' && val?.name) {
          members.push({ ...val, role: key === 'protagonist' ? 'Protagonista' : key === 'antagonist' ? 'Antagonista' : key });
        }
      });
    }
  }
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="p-0 border-none bg-transparent max-w-[420px]" hideClose>
        <div className="ct2-subpopup">
          <div className="ct2-subpopup-header">
            <span className="ct2-subpopup-title">CAST & CREW</span>
            <button className="ct2-subpopup-close" onClick={() => onClose(false)}><X size={14} /></button>
          </div>
          <div className="ct2-subpopup-body">
            {members.length === 0 ? (
              <p className="ct2-empty-text">Cast non disponibile</p>
            ) : members.map((m, i) => (
              <div key={i} className="ct2-cast-popup-item">
                <img
                  src={m.avatar_url || `https://api.dicebear.com/9.x/avataaars/svg?seed=${m.name || i}`}
                  alt="" className="ct2-cast-popup-avatar"
                  onError={(e) => { e.target.src = `https://api.dicebear.com/9.x/avataaars/svg?seed=cast${i}`; }}
                />
                <div>
                  <div className="ct2-cast-popup-name">{m.name}</div>
                  <div className="ct2-cast-popup-role">{m.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// === MAIN TEMPLATE COMPONENT ===
export function ContentTemplate({ filmId, contentType = 'film' }) {
  const { api, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [film, setFilm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [virtualAudience, setVirtualAudience] = useState(null);
  const [showCast, setShowCast] = useState(false);
  const [showCinemaModal, setShowCinemaModal] = useState(false);
  const [trailer, setTrailer] = useState(null);
  const [showTrailer, setShowTrailer] = useState(false);
  const [likes, setLikes] = useState({ poster: { count: 0, liked_by_me: false, system_count: 0 }, screenplay: { count: 0, liked_by_me: false, system_count: 0 }, trailer: { count: 0, liked_by_me: false, system_count: 0 } });
  const [likesSnapshot, setLikesSnapshot] = useState(null);

  const isSeries = contentType === 'series' || contentType === 'anime';
  const isAnime = contentType === 'anime' || film?.type === 'anime' || film?.content_type === 'anime';

  const loadFilm = useCallback(async () => {
    if (!filmId) return;
    setLoading(true);
    try {
      const endpoint = isSeries ? `/series/${filmId}` : `/films/${filmId}`;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      const [filmRes, vaRes] = await Promise.all([
        api.get(endpoint, { signal: controller.signal }),
        isSeries ? Promise.resolve({ data: null }) : api.get(`/films/${filmId}/virtual-audience`, { signal: controller.signal }).catch(() => ({ data: null })),
      ]);
      clearTimeout(timeout);
      const data = filmRes.data;
      if (data && !data.detail) {
        setFilm(data);
        setVirtualAudience(vaRes.data);
      }
    } catch {
      // Fallback: try getting just the basic film data
      try {
        const endpoint = isSeries ? `/series/${filmId}` : `/films/${filmId}`;
        const res = await api.get(endpoint);
        if (res.data && !res.data.detail) setFilm(res.data);
      } catch { /* truly failed */ }
    }
    finally { setLoading(false); }
  }, [api, filmId, isSeries]);

  useEffect(() => { loadFilm(); }, [loadFilm]);

  // Trailer fetch (independent, non-blocking)
  useEffect(() => {
    if (!filmId) return;
    api.get(`/trailers/${filmId}`).then(r => setTrailer(r.data?.trailer || null)).catch(() => {});
  }, [filmId, api]);

  // Likes fetch
  useEffect(() => {
    if (!filmId) return;
    api.get(`/content/${filmId}/likes`).then(r => {
      setLikes(r.data?.likes || {});
      setLikesSnapshot(r.data?.snapshot || null);
    }).catch(() => {});
  }, [filmId, api]);

  if (loading || !film) {
    return (
      <div className="ct2-root" data-testid="content-template">
        <div className="ct2-loading">
          <div className="ct2-spinner" />
          <p className="ct2-loading-text">Caricamento...</p>
        </div>
      </div>
    );
  }

  const statusInfo = getStatusInfo(film, contentType);
  const reviews = generateReviews(film.quality_score, film.popularity_score, contentType);
  const castInfo = extractCastInfo(film.cast, film);
  const imdb = film.imdb_rating || (film.quality_score ? (film.quality_score / 10).toFixed(1) : null);
  const durationStr = formatDuration(film, contentType);
  const shortPlot = (film.short_plot || film.preplot || film.pre_trama) ? cleanText(film.short_plot || film.preplot || film.pre_trama) : null;
  const trendPos = film.trend_position;
  const trendDelta = film.trend_delta;
  const screenplay = cleanText(toStr(film.screenplay) || toStr(film.screenplay_text) || toStr(film.pre_screenplay) || toStr(film.description) || '');
  const perception = getPublicPerception(film);
  const events = getEventHeadlines(film);
  const typeLabel = isAnime ? 'Anime' : (isSeries || film?.type === 'tv_series') ? 'Serie TV' : 'Film';

  // Cinema days — safe local variables, no hooks, no effects
  const _ts = (film && typeof film.theater_stats === 'object' && film.theater_stats !== null) ? film.theater_stats : null;
  const _cinemaDays = _ts ? (Number.isFinite(Number(_ts.days_in_theater)) ? Number(_ts.days_in_theater) : null) : null;
  const _cinemaRemain = _ts ? (Number.isFinite(Number(_ts.days_remaining)) ? Number(_ts.days_remaining) : null) : null;
  // Fallback: calculate from released_at if theater_stats missing
  const _relDate = film?.released_at || (film?.release_schedule && typeof film.release_schedule === 'object' ? film.release_schedule.scheduled_at : null);
  const _calcDays = (() => { try { if (_relDate) { const d = Math.floor((Date.now() - new Date(String(_relDate)).getTime()) / 86400000); return d >= 0 ? d : null; } return null; } catch(e) { return null; } })();
  const _calcRemain = (() => { try { if (_calcDays !== null) { const tw = Number.isFinite(Number(film?.theater_weeks)) ? Number(film.theater_weeks) : 3; return Math.max(0, tw * 7 - _calcDays); } return null; } catch(e) { return null; } })();
  const cinemaDays = _cinemaDays !== null ? _cinemaDays : _calcDays;
  const cinemaRemain = _cinemaRemain !== null ? _cinemaRemain : _calcRemain;
  const hasCinemaDays = Number.isFinite(cinemaDays);
  const hasCinemaRemain = Number.isFinite(cinemaRemain);

  // Extra cinema stats — safe
  const cinemaCount = _ts && Number.isFinite(Number(_ts.current_cinemas)) ? Number(_ts.current_cinemas) : null;
  const specDaily = _ts && Number.isFinite(Number(_ts.daily_spectators)) ? Number(_ts.daily_spectators) : null;
  const specTotal = _ts && Number.isFinite(Number(_ts.total_spectators)) ? Number(_ts.total_spectators) : null;
  const cinemaRev = _ts && Number.isFinite(Number(_ts.total_revenue)) ? Number(_ts.total_revenue) : null;
  const cinemaPerf = _ts && typeof _ts.performance === 'string' ? _ts.performance : null;
  const cinemaExt = _ts && Number.isFinite(Number(_ts.days_extended)) ? Number(_ts.days_extended) : 0;
  const cinemaRed = _ts && Number.isFinite(Number(_ts.days_reduced)) ? Number(_ts.days_reduced) : 0;

  // Ownership normalizzato (film.user_id / producer_id / owner_id / creator_id)
  const ownerId = film?.user_id || film?.producer_id || film?.owner_id || film?.creator_id;
  const isOwner = !!ownerId && ownerId === user?.id;

  return (
    <div className={`ct2-root ${isSeries ? 'ct2-series' : ''}`} data-testid="content-template">
      {/* BACK */}
      <button className="ct2-back" onClick={() => navigate(-1)} data-testid="ct-close" aria-label="Indietro">
        <X size={18} />
      </button>

      {/* 1. STATUS BAR */}
      <div className={`ct2-status-bar ${statusInfo.cls}`} data-testid="ct-status-bar">
        <span className="ct2-status-label">{statusInfo.label}</span>
        {statusInfo.cls === 'ct2-status-laprima' && (
          <div className="ct2-laprima-progress">
            <div className="ct2-laprima-bar">
              <div className="ct2-laprima-fill" style={{ width: `${Math.min(100, Math.max(5, (film.spectators_total || film.cumulative_attendance || 0) / Math.max(1, film.target_spectators || 5000) * 100))}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* 2. POSTER + INFO BOX */}
      <div className="ct2-top-block" data-testid="ct-top-block">
        <div className="ct2-poster relative" data-testid="ct-poster">
          {posterSrc(film.poster_url) ? (
            <img src={posterSrc(film.poster_url)} alt={film.title} onError={(e) => { e.target.style.display = 'none'; }} />
          ) : (
            <div className="ct2-poster-empty"><Film size={28} /></div>
          )}
          {/* Likes overlay on poster */}
          <div className="absolute left-2 bottom-2 flex items-center gap-1" data-testid="poster-like-real">
            <LikeButton contentId={filmId} context="poster" api={api} count={likes.poster?.count || 0} liked={likes.poster?.liked_by_me || false} disabled={isOwner} onChange={s => setLikes(prev => ({ ...prev, poster: { ...prev.poster, count: s.count, liked_by_me: s.liked, system_count: s.system_count ?? prev.poster?.system_count } }))} variant="chip" />
            <PreReleaseSnapshotBadge snapshot={likesSnapshot} context="poster" />
          </div>
          <div className="absolute right-2 bottom-2" data-testid="poster-like-system">
            <SystemLikeBadge count={likes.poster?.system_count || 0} variant="chip" />
          </div>
        </div>
        <div className="ct2-short-plot" data-testid="ct-short-plot">
          <div className="ct2-info-title">{film.title}</div>
          {castInfo.director && (
            <div className="ct2-info-director">Regia di: {castInfo.director}</div>
          )}
          {film.producer_nickname && (
            <div className="ct2-info-director" style={{ cursor: 'pointer', opacity: 0.7 }}
              onClick={(e) => { e.stopPropagation(); window.dispatchEvent(new CustomEvent('open-player-popup', { detail: { nickname: film.producer_nickname } })); }}
              data-testid="ct-production-house">
              {film.logo_url && <img src={film.logo_url} alt="" className="inline w-3 h-3 rounded-sm object-contain mr-0.5" style={{verticalAlign:'middle'}} />}{film.production_house_name || film.producer_nickname}
            </div>
          )}
          {castInfo.actors.length > 0 && (
            <div className="ct2-info-cast">
              {isAnime ? 'Disegnatori' : 'Cast'}: {castInfo.actors.map(a => a.name).join(', ')}
            </div>
          )}
          {shortPlot ? (
            <div className="ct2-info-plot">{shortPlot}</div>
          ) : screenplay ? (
            <div className="ct2-info-plot">{(() => {
              let text = screenplay;
              text = text.replace(/^(Titolo|Logline|Genere|Sottogenere|Ambientazione|Tono|Cast|Regia|Sceneggiatura)[:\s].+$/gmi, '');
              text = text.replace(/^(ATTO|ACT|SCENA|SCENE|INT\.|EXT\.)[:\s].*/gmi, '');
              text = text.trim();
              // If screenplay is already short (≤5 lines), use it as-is
              const lines = text.split('\n').filter(l => l.trim());
              if (lines.length <= 5) return text;
              // Otherwise extract first narrative paragraphs
              const paragraphs = text.split(/\n\n+/).filter(p => p.trim().length > 30);
              const plot = paragraphs.slice(0, 2).join(' ').trim();
              return plot.substring(0, 400).trim() + (plot.length > 400 ? '...' : '');
            })()}</div>
          ) : null}
        </div>
      </div>

      {/* 3. TITLE */}
      <div className="ct2-title-row" data-testid="ct-title">
        <h1 className="ct2-title">{film.title}</h1>
      </div>
      {/* Production House — clickable */}
      {(film.production_house_name || film.producer_nickname || film.user_id) && (
        <div className="px-4 -mt-1 mb-1">
          <button className="text-[10px] text-amber-400/70 italic hover:text-amber-300 transition-colors"
            onClick={(e) => { e.stopPropagation(); if (film.producer_nickname) window.dispatchEvent(new CustomEvent('open-player-popup', { detail: { nickname: film.producer_nickname } })); }}
            data-testid="ct-production-house-title">
            una produzione {film.logo_url && <img src={film.logo_url} alt="" className="inline w-3 h-3 rounded-sm object-contain mx-0.5" />}<span className="font-bold not-italic">{film.production_house_name || film.producer_nickname || 'Indipendente'}</span>
          </button>
        </div>
      )}

      {/* 5. DATA BAR (fuschia) */}
      <div className="ct2-data-bar" data-testid="ct-data-bar">
        <span className="ct2-data-type">{typeLabel}</span>
        <span className="ct2-data-sep">|</span>
        {imdb && (
          <>
            <Star size={13} fill="#f0c040" color="#f0c040" />
            <span className="ct2-data-imdb">{imdb}</span>
            <span className="ct2-data-sep">|</span>
          </>
        )}
        <Clock size={13} />
        <span className="ct2-data-duration">{durationStr || '~110m'}</span>
        {trendPos && (
          <>
            <span className="ct2-data-sep">|</span>
            <Flame size={13} />
            <span className="ct2-data-trend">#{trendPos}</span>
            {trendDelta != null && trendDelta !== 0 && (
              <span className={`ct2-data-delta ${trendDelta > 0 ? 'ct2-delta-up' : 'ct2-delta-down'}`}>
                {trendDelta > 0 ? '\u2191' : '\u2193'}{trendDelta > 0 ? `+${trendDelta}` : trendDelta}
              </span>
            )}
            {trendDelta === 0 && (
              <span className="ct2-data-delta ct2-delta-flat">&rarr; 0</span>
            )}
          </>
        )}
      </div>

      {/* PROSSIMAMENTE IN TV badge */}
      {film.in_tv_programming === true && (
        <div className="mx-4 mb-1 px-2 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-center">
          <span className="text-[9px] font-bold text-blue-400">PROSSIMAMENTE IN TV</span>
        </div>
      )}

      <div className={`ct2-cinema-bar ct2-perf-${cinemaPerf || 'ok'}`} onClick={() => setShowCinemaModal(true)} data-testid="ct-cinema-bar">
        {hasCinemaDays && hasCinemaRemain ? (
          <>
            <div className="ct2-cinema-bar-main">
              <span>IN SALA</span>
              <span className="ct2-cinema-bar-sep">·</span>
              <span>{cinemaDays}g</span>
              <span className="ct2-cinema-bar-sep">·</span>
              <span>{cinemaRemain}g rimasti</span>
              {cinemaPerf && (() => {
                const trendUp = ['great', 'good'].includes(cinemaPerf);
                const trendDown = ['bad', 'flop', 'declining'].includes(cinemaPerf);
                const trendDelta = film.theater_stats?.trend_delta_pct
                  ?? (cinemaPerf === 'great' ? 18 : cinemaPerf === 'good' ? 9 : cinemaPerf === 'declining' ? -7 : cinemaPerf === 'bad' ? -15 : cinemaPerf === 'flop' ? -30 : 0);
                return (
                  <>
                    <span className="ct2-cinema-bar-sep">·</span>
                    <span className={`ct2-cinema-bar-trend ct2-trend-${trendUp ? 'up' : trendDown ? 'down' : 'flat'}`}>
                      <span className="ct2-trend-icon">{trendUp ? '▲' : trendDown ? '▼' : '■'}</span>
                      <span className="ct2-trend-delta">{trendDelta >= 0 ? '+' : ''}{trendDelta}%</span>
                      <span className="ct2-trend-label">
                        {({great:'Successone', good:'Ottimo', ok:'Stabile', declining:'In calo', bad:'Scarso', flop:'FLOP'})[cinemaPerf]}
                      </span>
                    </span>
                  </>
                );
              })()}
            </div>
            {(() => {
              // Hint di prolungamento negli ultimi 3-4 giorni se performance buona
              const willExtend = cinemaRemain > 0 && cinemaRemain <= 4 && (cinemaPerf === 'great' || cinemaPerf === 'good');
              // Hint di ritiro anticipato se flop/bad
              const willPullEarly = cinemaPerf === 'flop' || cinemaPerf === 'bad';
              if (willExtend) return <div className="ct2-cinema-hint ct2-hint-extend">Possibile prolungamento: il pubblico continua ad affluire</div>;
              if (willPullEarly) return <div className="ct2-cinema-hint ct2-hint-pull">Rischio ritiro anticipato per scarsa affluenza</div>;
              if (cinemaExt > 0) return <div className="ct2-cinema-hint ct2-hint-extend">Prolungato di +{cinemaExt}g per successo</div>;
              if (cinemaRed > 0) return <div className="ct2-cinema-hint ct2-hint-pull">Ridotto di -{cinemaRed}g</div>;
              return null;
            })()}
          </>
        ) : hasCinemaDays ? (
          <div className="ct2-cinema-bar-main">
            <span>IN SALA · {cinemaDays}g</span>
          </div>
        ) : (
          <div className="ct2-cinema-bar-main">
            <span>IN SALA · dati in aggiornamento</span>
          </div>
        )}
      </div>
      <PStarBanner film={film} />

      {/* 6. JOURNALIST REVIEWS (green boxes) */}
      <div className="ct2-section-label" data-testid="ct-reviews-label">Cosa ne pensano i giornali</div>
      <div className="ct2-reviews-row" data-testid="ct-reviews">
        {reviews.map((r, i) => (
          <div key={i} className="ct2-review-box" data-testid={`ct-review-${i}`}>
            <div className="ct2-review-outlet">{r.outlet}</div>
            <div className="ct2-review-quote">"{r.quote}"</div>
          </div>
        ))}
      </div>

      {/* 7. PUBLIC + EVENTS (celeste) */}
      <div className="ct2-public-box" data-testid="ct-public-box">
        <div className="ct2-public-header">
          <Eye size={14} />
          <span>Pubblico & Eventi</span>
        </div>
        <div className="ct2-public-lines">
          {perception.map((line, i) => <div key={i} className="ct2-public-line">{line}</div>)}
          {events.map((ev, i) => <div key={`ev${i}`} className="ct2-event-line">{typeof ev === 'string' ? ev : String(ev || '')}</div>)}
          {perception.length === 0 && events.length === 0 && (
            <div className="ct2-public-line">Nessun dato disponibile</div>
          )}
        </div>
      </div>

      {/* 8. SCREENPLAY (scrollable) */}
      <div className="ct2-screenplay-section relative" data-testid="ct-screenplay">
        <div className="ct2-screenplay-header">
          <BookOpen size={14} />
          <span>Sceneggiatura completa</span>
        </div>
        <div className="ct2-screenplay-box">
          <div className="ct2-screenplay-content">
            {screenplay || 'Sceneggiatura non disponibile.'}
          </div>
          <div className="ct2-screenplay-fade-top" />
          <div className="ct2-screenplay-fade-bottom" />
        </div>
        {/* Likes row sceneggiatura */}
        <div className="flex items-center justify-between px-2 pt-2" data-testid="screenplay-likes-row">
          <div className="flex items-center gap-1">
            <LikeButton contentId={filmId} context="screenplay" api={api} count={likes.screenplay?.count || 0} liked={likes.screenplay?.liked_by_me || false} disabled={isOwner} onChange={s => setLikes(prev => ({ ...prev, screenplay: { ...prev.screenplay, count: s.count, liked_by_me: s.liked, system_count: s.system_count ?? prev.screenplay?.system_count } }))} variant="chip" />
            <PreReleaseSnapshotBadge snapshot={likesSnapshot} context="screenplay" />
          </div>
          <SystemLikeBadge count={likes.screenplay?.system_count || 0} variant="chip" />
        </div>
      </div>

      {/* 9. TRAILER — visibile sia se esiste (Guarda Trailer) sia come placeholder */}
      {trailer ? (
        <div>
          <button
            onClick={() => setShowTrailer(true)}
            className="ct2-trailer-placeholder hover:brightness-110 transition-all cursor-pointer"
            data-testid="ct-trailer-watch-btn"
            style={{ background: 'linear-gradient(135deg, rgba(245,166,35,0.15), rgba(233,78,119,0.12))', border: '1px solid rgba(245,166,35,0.3)' }}>
            <Play size={24} fill="#f5a623" color="#f5a623" />
            <span className="ct2-trailer-text" style={{ color: '#f5a623', fontWeight: 700 }}>Guarda Trailer</span>
            <span className="ct2-trailer-badge" style={{ color: '#f5a623', opacity: 0.75 }}>
              {trailer.duration_seconds}s · {(trailer.views_count || 0)} viste{trailer.trending ? ' · 🔥 TRENDING' : ''}
            </span>
          </button>
          <div className="flex items-center justify-between px-2 pt-2" data-testid="trailer-likes-row">
            <div className="flex items-center gap-1">
              <LikeButton contentId={filmId} context="trailer" api={api} count={likes.trailer?.count || 0} liked={likes.trailer?.liked_by_me || false} disabled={isOwner} onChange={s => setLikes(prev => ({ ...prev, trailer: { ...prev.trailer, count: s.count, liked_by_me: s.liked, system_count: s.system_count ?? prev.trailer?.system_count } }))} variant="chip" />
              <PreReleaseSnapshotBadge snapshot={likesSnapshot} context="trailer" />
            </div>
            <SystemLikeBadge count={likes.trailer?.system_count || 0} variant="chip" />
          </div>
        </div>
      ) : (
        <div className="ct2-trailer-placeholder" data-testid="ct-trailer-placeholder">
          <Play size={20} />
          <span className="ct2-trailer-text">Trailer in sviluppo</span>
          <span className="ct2-trailer-badge">Genera dalla pipeline del film</span>
        </div>
      )}
      {showTrailer && trailer && (
        <TrailerPlayerModal trailer={trailer} contentTitle={film?.title} contentGenre={film?.genre || ''} contentId={filmId} contentOwnerId={film?.user_id} currentUserId={user?.id} api={api} onClose={() => setShowTrailer(false)} />
      )}

      {/* Cast Popup */}
      <CastPopup open={showCast} onClose={setShowCast} cast={film?.cast} />

      {/* Cinema Stats Modal */}
      {showCinemaModal && (
        <div style={{position:"fixed",top:0,left:0,width:"100%",height:"100%",background:"rgba(0,0,0,0.8)",zIndex:9999,display:"flex",alignItems:"center",justifyContent:"center"}} onClick={() => setShowCinemaModal(false)}>
          <div style={{background:"#111",borderRadius:"12px",padding:"20px",width:"85%",maxWidth:"400px",color:"#fff",textAlign:"center"}} onClick={(e) => e.stopPropagation()}>
            <h3 style={{marginBottom:"12px",color:"#00ffff",fontSize:"16px"}}>Dati Cinema</h3>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"8px",marginBottom:"12px"}}>
              <div style={{background:"rgba(255,255,255,0.05)",borderRadius:"8px",padding:"8px"}}>
                <div style={{fontSize:"9px",color:"#6b7280"}}>Giorni in sala</div>
                <div style={{fontSize:"18px",fontWeight:"bold",color:"#facc15"}}>{hasCinemaDays ? '' + cinemaDays : 'N/D'}</div>
              </div>
              <div style={{background:"rgba(255,255,255,0.05)",borderRadius:"8px",padding:"8px"}}>
                <div style={{fontSize:"9px",color:"#6b7280"}}>Giorni rimasti</div>
                <div style={{fontSize:"18px",fontWeight:"bold",color:"#38bdf8"}}>{hasCinemaRemain ? '' + cinemaRemain : 'N/D'}</div>
              </div>
            </div>
            {(cinemaExt > 0 || cinemaRed > 0) && (
              <div style={{display:"flex",justifyContent:"center",gap:"12px",marginBottom:"10px",fontSize:"12px"}}>
                {cinemaExt > 0 && <span style={{color:"#4ade80",fontWeight:"bold"}}>{'+' + cinemaExt + ' giorni estesi'}</span>}
                {cinemaRed > 0 && <span style={{color:"#f87171",fontWeight:"bold"}}>{'-' + cinemaRed + ' giorni ridotti'}</span>}
              </div>
            )}
            <div style={{borderTop:"1px solid rgba(255,255,255,0.1)",paddingTop:"10px",marginBottom:"10px"}}>
              <p style={{margin:"5px 0",fontSize:"13px"}}>{'Cinema attivi: ' + (cinemaCount !== null ? '' + cinemaCount : 'non disponibile')}</p>
              <p style={{margin:"5px 0",fontSize:"13px"}}>{'Affluenza giornaliera: ' + (specDaily !== null ? '' + specDaily.toLocaleString() : 'non disponibile')}</p>
              <p style={{margin:"5px 0",fontSize:"13px"}}>{'Affluenza totale: ' + (specTotal !== null ? '' + specTotal.toLocaleString() : 'non disponibile')}</p>
              <p style={{margin:"5px 0",fontSize:"13px"}}>{'Incassi sala: ' + (cinemaRev !== null ? '$' + cinemaRev.toLocaleString() : 'non disponibile')}</p>
              {cinemaPerf && <p style={{margin:"8px 0",fontSize:"12px",color: cinemaPerf === 'great' ? '#4ade80' : cinemaPerf === 'good' ? '#34d399' : cinemaPerf === 'declining' ? '#fb923c' : cinemaPerf === 'bad' || cinemaPerf === 'flop' ? '#f87171' : '#facc15'}}>{'Andamento: ' + (cinemaPerf === 'great' ? 'Straordinario' : cinemaPerf === 'good' ? 'Ottimo' : cinemaPerf === 'ok' ? 'Discreto' : cinemaPerf === 'declining' ? 'In calo' : cinemaPerf === 'bad' ? 'Scarso' : cinemaPerf === 'flop' ? 'Flop' : cinemaPerf)}</p>}
            </div>
            <button style={{marginTop:"5px",padding:"8px 15px",borderRadius:"8px",border:"none",background:"#00ffff",color:"#000",fontWeight:"bold",cursor:"pointer"}} onClick={() => setShowCinemaModal(false)}>Chiudi</button>
          </div>
        </div>
      )}
    </div>
  );
}
