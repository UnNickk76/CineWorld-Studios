import React, { useState, useEffect, useContext, useCallback } from 'react';
import {
  Film, Star, Clock, Users, Megaphone, X, BookOpen, Eye,
  Trash2, AlertTriangle, Flame, TrendingUp, Tv
} from 'lucide-react';
import { AuthContext } from '../../contexts';
import { toast } from 'sonner';
import ProducerProfileModal from '../ProducerProfileModal';
import '../../styles/content-template.css';

const BACKEND = process.env.REACT_APP_BACKEND_URL || '';
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND}${url}`;
  return url;
};

/* ═══ REVIEW GENERATION (same as ContentTemplate) ═══ */
const FILM_OUTLETS = ['VARIETY', 'EMPIRE', 'HOLLYWOOD R.'];
const POSITIVE_QUOTES = {
  VARIETY: ["Un'esperienza cinematografica straordinaria!", "Un'opera che ridefinisce il genere", "Spettacolare da ogni punto di vista"],
  EMPIRE: ["Impressionante dall'inizio alla fine", "Un capolavoro moderno del cinema", "Emozionante e visivamente stupendo"],
  'HOLLYWOOD R.': ["Uno dei migliori film degli ultimi anni", "Un trionfo del cinema contemporaneo", "Destinato a diventare un classico"],
};
const MIXED_QUOTES = {
  VARIETY: ["Ambizioso ma non sempre riuscito", "Ha momenti brillanti e altri meno"],
  EMPIRE: ["Interessante ma con alti e bassi", "Un buon film con qualche difetto"],
  'HOLLYWOOD R.': ["Promettente ma imperfetto", "Merita una visione, con riserve"],
};
function generateReviews(quality, hype) {
  const score = (quality || 50) / 10;
  return FILM_OUTLETS.map((outlet) => {
    const pool = score >= 7 ? POSITIVE_QUOTES[outlet] : MIXED_QUOTES[outlet];
    const idx = Math.floor((hype || 0) % pool.length);
    return { outlet, quote: pool[idx] };
  });
}

/* ═══ PUBLIC PERCEPTION ═══ */
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

/* ═══ CAST EXTRACTOR (V3 format) ═══ */
function extractCastInfo(cast) {
  let director = null;
  let actors = [];
  if (!cast) return { director, actors: [] };
  if (typeof cast === 'object' && !Array.isArray(cast)) {
    if (cast.director?.name) director = cast.director.name;
    if (Array.isArray(cast.actors)) actors = cast.actors.filter(a => a && a.name);
    if (cast.screenwriter?.name && !actors.find(a => a.name === cast.screenwriter.name)) {
      actors.push({ ...cast.screenwriter, role: 'Sceneggiatore' });
    }
    if (cast.composer?.name && !actors.find(a => a.name === cast.composer.name)) {
      actors.push({ ...cast.composer, role: 'Compositore' });
    }
  } else if (Array.isArray(cast)) {
    actors = cast.filter(a => a && a.name);
  }
  return { director, actors: actors.slice(0, 5) };
}

/* ═══ DURATION FORMATTER ═══ */
function formatDuration(film) {
  // Use the label set during V3 pipeline creation first
  if (film?.film_duration_label) return film.film_duration_label;
  const min = film?.film_duration_minutes;
  if (min) {
    const h = Math.floor(min / 60);
    const m = min % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }
  return null;
}

const cleanText = (text) => {
  if (!text) return '';
  return text.replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1')
    .replace(/^#{1,3}\s+/gm, '').replace(/^[-*]\s+/gm, '')
    .replace(/\n{3,}/g, '\n\n').trim();
};
const toStr = (v) => typeof v === 'string' ? v : (v?.text || v?.content || '');

/* ═══ ADV PANEL ═══ */
const AdvPanel = ({ filmId, api, onDone }) => {
  const [platforms, setPlatforms] = useState([]);
  const [selected, setSelected] = useState([]);
  const [days, setDays] = useState(3);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get('/advertising/platforms').then(r => {
      const data = Array.isArray(r.data) ? r.data : r.data.platforms || r.data;
      setPlatforms(data);
    }).catch(() => {});
  }, [api]);

  const totalCost = selected.reduce((acc, pid) => {
    const p = platforms.find(x => x.id === pid);
    return acc + (p ? p.cost_per_day * days : 0);
  }, 0);

  const toggle = (pid) => setSelected(prev =>
    prev.includes(pid) ? prev.filter(x => x !== pid) : [...prev, pid]
  );

  const launch = async () => {
    if (selected.length === 0) return toast.error('Seleziona almeno una piattaforma');
    setLoading(true);
    try {
      const r = await api.post(`/films/${filmId}/advertise`, { platforms: selected, days, budget: totalCost });
      toast.success(`Campagna lanciata! Revenue boost: $${(r.data.revenue_boost || 0).toLocaleString()}`);
      onDone?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore campagna ADV'); }
    setLoading(false);
  };

  return (
    <div style={{ margin: '8px 10px', padding: '12px', borderRadius: '8px', background: 'rgba(0,80,120,0.15)', border: '1px solid rgba(0,200,255,0.2)' }} data-testid="adv-panel">
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', fontFamily: "'Bebas Neue', sans-serif", fontSize: '12px', letterSpacing: '1.5px', color: '#60a8d8' }}>
        <Megaphone size={14} /> Campagna Pubblicitaria
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '8px' }}>
        {platforms.map(p => (
          <button key={p.id} onClick={() => toggle(p.id)} data-testid={`adv-platform-${p.id}`}
            style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', borderRadius: '6px', border: selected.includes(p.id) ? '1px solid rgba(0,200,255,0.4)' : '1px solid rgba(255,255,255,0.05)', background: selected.includes(p.id) ? 'rgba(0,200,255,0.1)' : 'rgba(255,255,255,0.02)', cursor: 'pointer', color: '#fff', fontSize: '11px', textAlign: 'left' }}>
            <span>{p.name_it || p.name} <span style={{ color: '#6b7280', fontSize: '9px' }}>x{p.reach_multiplier}</span></span>
            <span style={{ color: '#f0c040', fontWeight: 'bold' }}>${(p.cost_per_day * days).toLocaleString()}</span>
          </button>
        ))}
      </div>
      <div style={{ display: 'flex', gap: '4px', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '10px', color: '#6b7280' }}>Giorni:</span>
        {[1, 3, 5, 7].map(d => (
          <button key={d} onClick={() => setDays(d)}
            style={{ padding: '3px 8px', borderRadius: '4px', border: days === d ? '1px solid #00bcd4' : '1px solid #333', background: days === d ? 'rgba(0,188,212,0.15)' : 'transparent', color: days === d ? '#00bcd4' : '#666', fontSize: '10px', fontWeight: 'bold', cursor: 'pointer' }}>{d}g</button>
        ))}
      </div>
      {selected.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '6px', padding: '0 4px' }}>
          <span style={{ color: '#6b7280' }}>Costo totale</span>
          <span style={{ color: '#f0c040', fontWeight: 'bold' }}>${totalCost.toLocaleString()}</span>
        </div>
      )}
      <button onClick={launch} disabled={loading || selected.length === 0} data-testid="launch-adv-btn"
        style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid rgba(0,200,255,0.3)', background: 'rgba(0,200,255,0.12)', color: '#00bcd4', fontWeight: 'bold', fontSize: '11px', cursor: selected.length > 0 ? 'pointer' : 'default', opacity: selected.length === 0 ? 0.4 : 1 }}>
        {loading ? '...' : `Lancia Campagna ($${totalCost.toLocaleString()})`}
      </button>
    </div>
  );
};


/* ═══════════════════════════════════════════════════
   MAIN COMPONENT — FilmDetailV3 (ContentTemplate style)
   ═══════════════════════════════════════════════════ */
export default function FilmDetailV3({ filmId, onClose }) {
  const { api, user } = useContext(AuthContext);
  const [film, setFilm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [showAdv, setShowAdv] = useState(false);
  const [showCinemaPopup, setShowCinemaPopup] = useState(false);
  const [showProducerModal, setShowProducerModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const loadFilm = useCallback(async () => {
    if (!filmId) return;
    setLoading(true);
    try {
      const res = await api.get(`/pipeline-v3/released-film/${filmId}`);
      setFilm(res.data);
    } catch { /* */ }
    setLoading(false);
  }, [filmId, api]);

  useEffect(() => { loadFilm(); }, [loadFilm]);

  const withdrawFromTheaters = async () => {
    setActionLoading(true);
    try {
      const pid = film?.source_project_id;
      if (pid) await api.post(`/pipeline-v3/films/${pid}/withdraw-theaters`);
      toast.success('Film ritirato dalle sale');
      onClose?.();
    } catch { toast.error('Errore nel ritiro'); }
    setActionLoading(false);
  };

  const deleteFilm = async () => {
    setActionLoading(true);
    try {
      await api.post(`/pipeline-v3/films/${filmId}/delete-film`);
      toast.success('Film eliminato permanentemente');
      onClose?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore eliminazione'); }
    setActionLoading(false);
  };

  if (!filmId) return null;

  /* ─── Overlay (fixed fullscreen, scrollable) ─── */
  return (
    <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-0 sm:p-4" onClick={onClose} data-testid="film-detail-v3-modal">
      <div className="w-full max-w-[480px] h-full sm:h-auto sm:max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()} style={{ overscrollBehavior: 'contain', WebkitOverflowScrolling: 'touch' }}>

        {loading ? (
          <div className="ct2-root" data-testid="content-template">
            <div className="ct2-loading">
              <div className="ct2-spinner" />
              <p className="ct2-loading-text">Caricamento...</p>
            </div>
          </div>
        ) : !film ? (
          <div className="ct2-root" data-testid="content-template">
            <div className="ct2-loading">
              <p className="ct2-loading-text">Film non trovato</p>
            </div>
          </div>
        ) : (
          <FilmContent film={film} filmId={filmId} onClose={onClose} user={user} api={api}
            showAdv={showAdv} setShowAdv={setShowAdv}
            showWithdraw={showWithdraw} setShowWithdraw={setShowWithdraw}
            showDelete={showDelete} setShowDelete={setShowDelete}
            showCinemaPopup={showCinemaPopup} setShowCinemaPopup={setShowCinemaPopup}
            showProducerModal={showProducerModal} setShowProducerModal={setShowProducerModal}
            actionLoading={actionLoading}
            withdrawFromTheaters={withdrawFromTheaters}
            deleteFilm={deleteFilm}
            onRefresh={loadFilm} />
        )}
      </div>
    </div>
  );
}

/* ═══ INNER RENDER — avoids hooks in conditional ═══ */
function FilmContent({ film, filmId, onClose, user, api, showAdv, setShowAdv, showWithdraw, setShowWithdraw, showDelete, setShowDelete, showCinemaPopup, setShowCinemaPopup, showProducerModal, setShowProducerModal, actionLoading, withdrawFromTheaters, deleteFilm, onRefresh }) {
  const isOwner = film?.user_id === user?.id;
  const isLive = film?.status === 'in_theaters';

  const reviews = generateReviews(film.quality_score, film.popularity_score || film.hype_score);
  const castInfo = extractCastInfo(film.cast);
  const cwsv = film.cwsv_display || (film.quality_score ? (film.quality_score % 1 === 0 ? String(Math.round(film.quality_score)) : film.quality_score.toFixed(1)) : null);
  const cwsvNum = film.quality_score || 0;
  const durationStr = formatDuration(film);
  const screenplay = cleanText(toStr(film.screenplay_text) || toStr(film.preplot) || '');
  const perception = getPublicPerception(film);

  const cinemaDays = film.days_in_theater ?? 0;
  const cinemaRemain = film.days_remaining ?? 0;

  return (
    <div className="ct2-root" data-testid="content-template" style={{ paddingBottom: '16px' }}>
      {/* CLOSE */}
      <button className="ct2-back" onClick={onClose} data-testid="close-film-detail" aria-label="Chiudi">
        <X size={18} />
      </button>

      {/* 1. STATUS BAR */}
      <div className={`ct2-status-bar ${isLive ? 'ct2-status-cinema' : 'ct2-status-catalogo'}`} data-testid="ct-status-bar">
        <span className="ct2-status-label">{isLive ? 'Al Cinema' : 'Fuori Sala'}</span>
      </div>

      {/* 2. POSTER + INFO BOX */}
      <div className="ct2-top-block" data-testid="ct-top-block">
        <div className="ct2-poster" data-testid="ct-poster">
          {posterSrc(film.poster_url) ? (
            <img src={posterSrc(film.poster_url)} alt={film.title} onError={(e) => { e.target.style.display = 'none'; }} />
          ) : (
            <div className="ct2-poster-empty"><Film size={28} /></div>
          )}
        </div>
        <div className="ct2-short-plot" data-testid="ct-short-plot">
          <div className="ct2-info-title">{film.title}</div>
          {castInfo.director && (
            <div className="ct2-info-director">Regia di: {castInfo.director}</div>
          )}
          {film.producer?.nickname && (
            <div className="ct2-info-director">{film.producer.production_house_name || film.producer.nickname}</div>
          )}
          {castInfo.actors.length > 0 && (
            <div className="ct2-info-cast">
              Cast: {castInfo.actors.map(a => a.name).join(', ')}
            </div>
          )}
          {film.preplot ? (
            <div className="ct2-info-plot">{film.preplot}</div>
          ) : null}
        </div>
      </div>

      {/* 3. TITLE */}
      <div className="ct2-title-row" data-testid="ct-title">
        <h1 className="ct2-title" data-testid="film-title">{film.title}</h1>
      </div>
      {/* Production House */}
      {(film.producer?.production_house_name || film.producer?.nickname) && (
        <div className="px-4 -mt-1 mb-1 cursor-pointer" onClick={() => setShowProducerModal(true)} data-testid="producer-link">
          <span className="text-[10px] text-amber-400/70 italic hover:text-amber-400 transition-colors">
            una produzione <span className="font-bold not-italic underline decoration-dotted">{film.producer.production_house_name || film.producer.nickname}</span>
          </span>
        </div>
      )}

      {/* 5. DATA BAR — CWSv */}
      <div className="ct2-data-bar" data-testid="ct-data-bar">
        <span className="ct2-data-type">Film</span>
        <span className="ct2-data-sep">|</span>
        {cwsv && (
          <>
            <Star size={13} fill={cwsvNum >= 8 ? '#f0c040' : cwsvNum >= 6 ? '#4ade80' : cwsvNum >= 4 ? '#facc15' : '#f87171'} color={cwsvNum >= 8 ? '#f0c040' : cwsvNum >= 6 ? '#4ade80' : cwsvNum >= 4 ? '#facc15' : '#f87171'} />
            <span className="ct2-data-imdb" style={{ color: cwsvNum >= 8 ? '#f0c040' : cwsvNum >= 6 ? '#4ade80' : cwsvNum >= 4 ? '#facc15' : '#f87171' }}>CWSv {cwsv}</span>
            <span className="ct2-data-sep">|</span>
          </>
        )}
        {durationStr && (
          <>
            <Clock size={13} />
            <span className="ct2-data-duration">{durationStr}</span>
          </>
        )}
      </div>

      {/* IN SALA BAR — CLICKABLE → opens cinema popup */}
      <div
        onClick={() => setShowCinemaPopup(true)}
        style={{ border: '2px solid #00ffff', background: 'rgba(0,255,255,0.08)', padding: '10px', marginTop: '8px', marginLeft: '10px', marginRight: '10px', textAlign: 'center', fontWeight: 'bold', color: '#00ffff', borderRadius: '8px', fontFamily: "'Bebas Neue', sans-serif", fontSize: '14px', letterSpacing: '1px', cursor: 'pointer', transition: 'background 0.2s' }}
        data-testid="in-sala-bar">
        {isLive
          ? `IN SALA - ${cinemaDays} giorni - ${cinemaRemain} rimanenti`
          : 'FUORI SALA'}
      </div>

      {/* 6. JOURNALIST REVIEWS */}
      <div className="ct2-section-label" data-testid="ct-reviews-label">Cosa ne pensano i giornali</div>
      <div className="ct2-reviews-row" data-testid="ct-reviews">
        {reviews.map((r, i) => (
          <div key={i} className="ct2-review-box" data-testid={`ct-review-${i}`}>
            <div className="ct2-review-outlet">{r.outlet}</div>
            <div className="ct2-review-quote">"{r.quote}"</div>
          </div>
        ))}
      </div>

      {/* 7. PUBLIC + EVENTS */}
      <div className="ct2-public-box" data-testid="ct-public-box">
        <div className="ct2-public-header">
          <Eye size={14} />
          <span>Pubblico & Eventi</span>
        </div>
        <div className="ct2-public-lines">
          {perception.map((line, i) => <div key={i} className="ct2-public-line">{line}</div>)}
          {perception.length === 0 && <div className="ct2-public-line">Nessun dato disponibile</div>}
        </div>
      </div>

      {/* 8. SCREENPLAY */}
      {screenplay && (
        <div className="ct2-screenplay-section" data-testid="ct-screenplay">
          <div className="ct2-screenplay-header">
            <BookOpen size={14} />
            <span>Sceneggiatura completa</span>
          </div>
          <div className="ct2-screenplay-box">
            <div className="ct2-screenplay-content">{screenplay}</div>
            <div className="ct2-screenplay-fade-top" />
            <div className="ct2-screenplay-fade-bottom" />
          </div>
        </div>
      )}

      {/* ═══ CINEMA STATS POPUP — Premium Design ═══ */}
      {showCinemaPopup && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '12px' }} onClick={() => setShowCinemaPopup(false)} data-testid="cinema-popup">
          <div style={{ background: 'linear-gradient(180deg, #0d1117 0%, #0a0c10 100%)', borderRadius: '16px', width: '100%', maxWidth: '400px', color: '#fff', border: '1px solid rgba(0,255,255,0.15)', maxHeight: '88vh', overflowY: 'auto', boxShadow: '0 0 40px rgba(0,255,255,0.08)', WebkitOverflowScrolling: 'touch' }} onClick={(e) => e.stopPropagation()}>

            {/* Header con gradient */}
            <div style={{ padding: '16px 16px 12px', background: 'linear-gradient(135deg, rgba(0,255,255,0.08), rgba(56,189,248,0.05))', borderBottom: '1px solid rgba(0,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderRadius: '16px 16px 0 0' }}>
              <div>
                <h3 style={{ color: '#00ffff', fontSize: '15px', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '2px', margin: 0 }}>Dati Cinema</h3>
                <p style={{ fontSize: '9px', color: '#4a5568', margin: 0 }}>{film.title}</p>
              </div>
              <button onClick={() => setShowCinemaPopup(false)} style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#666', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><X size={14} /></button>
            </div>

            <div style={{ padding: '14px' }}>
              {/* Performance Label */}
              {(() => {
                const cwt = film.cwtrend || 0;
                const perf = cwt >= 8 ? { l: 'Straordinario', c: '#facc15', bg: 'rgba(250,204,21,0.1)', b: 'rgba(250,204,21,0.2)' }
                  : cwt >= 6.5 ? { l: 'Ottimo', c: '#4ade80', bg: 'rgba(74,222,128,0.1)', b: 'rgba(74,222,128,0.2)' }
                  : cwt >= 5 ? { l: 'Discreto', c: '#60a5fa', bg: 'rgba(96,165,250,0.1)', b: 'rgba(96,165,250,0.2)' }
                  : cwt >= 3 ? { l: 'In Calo', c: '#fb923c', bg: 'rgba(251,146,60,0.1)', b: 'rgba(251,146,60,0.2)' }
                  : { l: 'Flop', c: '#f87171', bg: 'rgba(248,113,113,0.1)', b: 'rgba(248,113,113,0.2)' };
                return (
                  <div style={{ textAlign: 'center', padding: '10px', borderRadius: '10px', background: perf.bg, border: `1px solid ${perf.b}`, marginBottom: '12px' }}>
                    <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '2px' }}>Performance</div>
                    <div style={{ fontSize: '18px', fontWeight: '900', color: perf.c, fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '2px' }}>{perf.l}</div>
                  </div>
                );
              })()}

              {/* Stats 2x2 */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
                {[
                  { label: 'Giorni in sala', value: cinemaDays, color: '#facc15', icon: '📅' },
                  { label: 'Giorni rimasti', value: cinemaRemain, color: '#38bdf8', icon: '⏳' },
                  { label: 'Cinema attivi', value: film.current_cinemas || 0, color: '#e2e8f0', icon: '🎬' },
                  { label: 'Spettatori', value: Math.floor((film.total_revenue || 0) / 12).toLocaleString(), color: '#c084fc', icon: '👥' },
                ].map((s, i) => (
                  <div key={i} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '10px', padding: '10px', textAlign: 'center', border: '1px solid rgba(255,255,255,0.04)' }}>
                    <div style={{ fontSize: '8px', color: '#4a5568', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{s.icon} {s.label}</div>
                    <div style={{ fontSize: '22px', fontWeight: '900', color: s.color, fontFamily: "'Bebas Neue', sans-serif" }}>{s.value}</div>
                  </div>
                ))}
              </div>

              {/* Incassi Breakdown */}
              <div style={{ background: 'rgba(74,222,128,0.04)', borderRadius: '10px', padding: '12px', border: '1px solid rgba(74,222,128,0.1)', marginBottom: '12px' }}>
                <div style={{ fontSize: '9px', color: '#4a5568', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>Incassi</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '10px', color: '#6b7280' }}>Apertura</span>
                  <span style={{ fontSize: '10px', color: '#4ade80', fontWeight: 'bold' }}>${(film.opening_day_revenue || 0).toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '10px', color: '#6b7280' }}>Media giornaliera</span>
                  <span style={{ fontSize: '10px', color: '#4ade80', fontWeight: 'bold' }}>${cinemaDays > 0 ? Math.floor((film.total_revenue || 0) / cinemaDays).toLocaleString() : '—'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid rgba(74,222,128,0.1)', paddingTop: '6px', marginTop: '4px' }}>
                  <span style={{ fontSize: '11px', color: '#fff', fontWeight: 'bold' }}>Totale</span>
                  <span style={{ fontSize: '14px', color: '#4ade80', fontWeight: '900' }}>${(film.total_revenue || 0).toLocaleString()}</span>
                </div>
              </div>

              {/* CWTrend */}
              <div style={{ background: 'linear-gradient(135deg, rgba(0,255,255,0.04), rgba(167,139,250,0.04))', borderRadius: '10px', padding: '12px', border: '1px solid rgba(0,255,255,0.1)', marginBottom: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#00ffff', fontWeight: 'bold', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1px' }}>CWTrend</div>
                  <div style={{ fontSize: '8px', color: '#4a5568' }}>Andamento attuale</div>
                </div>
                <div style={{ fontSize: '32px', fontWeight: '900', color: (film.cwtrend || 0) >= 8 ? '#facc15' : (film.cwtrend || 0) >= 6 ? '#4ade80' : (film.cwtrend || 0) >= 4 ? '#fb923c' : '#f87171', fontFamily: "'Bebas Neue', sans-serif" }}>
                  {film.cwtrend_display || film.cwtrend || '—'}
                </div>
              </div>

              {/* Actions */}
              {isOwner && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>

                  {/* ADV */}
                  {isLive && !showAdv && (
                    <button onClick={() => setShowAdv(true)} data-testid="open-adv-btn"
                      style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '11px', borderRadius: '10px', border: '1px solid rgba(0,200,255,0.2)', background: 'linear-gradient(135deg, rgba(0,200,255,0.08), rgba(0,200,255,0.03))', color: '#00bcd4', fontWeight: 'bold', fontSize: '11px', cursor: 'pointer', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1px' }}>
                      <Megaphone size={14} /> Lancia Pubblicita (ADV)
                    </button>
                  )}
                  {showAdv && (
                    <div>
                      <AdvPanel filmId={filmId} api={api} onDone={() => { setShowAdv(false); setShowCinemaPopup(false); onRefresh(); }} />
                      <button onClick={() => setShowAdv(false)} style={{ width: '100%', textAlign: 'center', fontSize: '9px', color: '#555', padding: '4px', cursor: 'pointer', background: 'transparent', border: 'none' }}>Chiudi ADV</button>
                    </div>
                  )}

                  {/* SEND TO TV (Prossimamente) */}
                  {isLive && (
                    <button data-testid="send-to-tv-btn"
                      style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '11px', borderRadius: '10px', border: '1px solid rgba(167,139,250,0.2)', background: 'linear-gradient(135deg, rgba(167,139,250,0.08), rgba(167,139,250,0.03))', color: '#a78bfa', fontWeight: 'bold', fontSize: '11px', cursor: 'pointer', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1px' }}
                      onClick={() => toast.info('Prossimamente in TV — disponibile dopo il ritiro dalle sale')}>
                      <Tv size={14} /> Prossimamente in TV
                    </button>
                  )}

                  {/* WITHDRAW */}
                  {isLive && (
                    <>
                      {!showWithdraw ? (
                        <button onClick={() => setShowWithdraw(true)} data-testid="withdraw-btn"
                          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '11px', borderRadius: '10px', border: '1px solid rgba(249,115,22,0.15)', background: 'linear-gradient(135deg, rgba(249,115,22,0.06), rgba(249,115,22,0.02))', color: '#f97316', fontWeight: 'bold', fontSize: '11px', cursor: 'pointer', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1px' }}>
                          <Trash2 size={14} /> Ritira dalle Sale
                        </button>
                      ) : (
                        <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(249,115,22,0.04)', border: '1px solid rgba(249,115,22,0.15)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                            <AlertTriangle size={16} color="#f97316" />
                            <span style={{ fontWeight: 'bold', color: '#fb923c', fontSize: '12px' }}>Ritirare il film?</span>
                          </div>
                          <p style={{ fontSize: '10px', color: '#555', marginBottom: '8px' }}>L'incasso accumulato restera invariato.</p>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button onClick={() => setShowWithdraw(false)} style={{ flex: 1, padding: '7px', borderRadius: '8px', border: '1px solid #222', color: '#666', fontSize: '10px', fontWeight: 'bold', cursor: 'pointer', background: 'transparent' }}>Annulla</button>
                            <button onClick={withdrawFromTheaters} disabled={actionLoading} data-testid="confirm-withdraw-btn"
                              style={{ flex: 1, padding: '7px', borderRadius: '8px', border: '1px solid rgba(249,115,22,0.3)', background: 'rgba(249,115,22,0.12)', color: '#f97316', fontSize: '10px', fontWeight: 'bold', cursor: 'pointer', opacity: actionLoading ? 0.5 : 1 }}>
                              {actionLoading ? '...' : 'Conferma'}
                            </button>
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  {/* DELETE */}
                  {!showDelete ? (
                    <button onClick={() => setShowDelete(true)} data-testid="delete-film-btn"
                      style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '11px', borderRadius: '10px', border: '1px solid rgba(239,68,68,0.1)', background: 'rgba(239,68,68,0.03)', color: 'rgba(239,68,68,0.5)', fontWeight: 'bold', fontSize: '11px', cursor: 'pointer', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1px' }}>
                      <Trash2 size={14} /> Elimina Film
                    </button>
                  ) : (
                    <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(239,68,68,0.04)', border: '1px solid rgba(239,68,68,0.15)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                        <AlertTriangle size={16} color="#ef4444" />
                        <span style={{ fontWeight: 'bold', color: '#f87171', fontSize: '12px' }}>Eliminazione permanente!</span>
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button onClick={() => setShowDelete(false)} style={{ flex: 1, padding: '7px', borderRadius: '8px', border: '1px solid #222', color: '#666', fontSize: '10px', fontWeight: 'bold', cursor: 'pointer', background: 'transparent' }}>Annulla</button>
                        <button onClick={deleteFilm} disabled={actionLoading} data-testid="confirm-delete-btn"
                          style={{ flex: 1, padding: '7px', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.12)', color: '#ef4444', fontSize: '10px', fontWeight: 'bold', cursor: 'pointer', opacity: actionLoading ? 0.5 : 1 }}>
                          {actionLoading ? '...' : 'Elimina'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Producer Profile Modal */}
      <ProducerProfileModal
        producerId={film?.user_id}
        producerData={film?.producer}
        isOpen={showProducerModal}
        onClose={() => setShowProducerModal(false)}
      />
    </div>
  );
}
