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
import '../styles/content-template.css';

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
function getStatusInfo(film, contentType) {
  const s = (film?.status || '').toLowerCase();
  const cinemas = film?.current_cinemas || 0;
  const onTv = film?.on_tv || film?.tv_broadcast || false;

  if (s.includes('prima') || s === 'premiere_live' || s === 'premiere_setup') {
    return { label: 'LaPrima!', cls: 'ct2-status-laprima' };
  }
  if (s === 'coming_soon' || s === 'pending_release' || s === 'release_pending' || s.includes('hype')) {
    return { label: 'Prossimamente', cls: 'ct2-status-coming' };
  }
  if (cinemas > 0 || s === 'in_theaters') {
    return { label: 'Al Cinema', cls: 'ct2-status-cinema' };
  }
  if (onTv) {
    return { label: 'In TV!', cls: 'ct2-status-tv' };
  }
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
  if (!min) return null;
  const h = Math.floor(min / 60);
  const m = min % 60;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
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
  if (ev.name || ev.description || ev.text) return [ev.description || ev.name || ev.text || ''];
  if (Array.isArray(ev)) {
    return ev.slice(0, 2).map(e => {
      if (typeof e === 'string') return e;
      return e?.description || e?.name || e?.text || e?.title || '';
    }).filter(Boolean);
  }
  return [];
}

// === SUB-POPUP: Cast & Crew ===
function CastPopup({ open, onClose, cast }) {
  const members = [];
  if (cast) {
    if (Array.isArray(cast)) {
      cast.forEach((a) => members.push({ ...a, role: a.role_in_film || a.role || 'Attore' }));
    } else {
      if (cast.director) members.push({ ...cast.director, role: 'Regista' });
      if (Array.isArray(cast.actors)) {
        cast.actors.forEach((a) => members.push({ ...a, role: a.role_in_film || a.role || 'Attore' }));
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
  const shortPlot = film.short_plot ? cleanText(film.short_plot) : null;
  const trendPos = film.trend_position;
  const trendDelta = film.trend_delta;
  const screenplay = cleanText(toStr(film.screenplay) || toStr(film.pre_screenplay) || toStr(film.description) || '');
  const perception = getPublicPerception(film);
  const events = getEventHeadlines(film);
  const typeLabel = isAnime ? 'Anime' : (isSeries || film?.type === 'tv_series') ? 'Serie TV' : 'Film';

  return (
    <div className={`ct2-root ${isSeries ? 'ct2-series' : ''}`} data-testid="content-template">
      {/* BACK */}
      <button className="ct2-back" onClick={() => navigate(-1)} data-testid="ct-close" aria-label="Indietro">
        <X size={18} />
      </button>

      {/* 1. STATUS BAR */}
      <div className={`ct2-status-bar ${statusInfo.cls}`} data-testid="ct-status-bar">
        <span className="ct2-status-label">{statusInfo.label}</span>
        {statusInfo.label === 'LaPrima!' && (
          <div className="ct2-laprima-progress">
            <div className="ct2-laprima-bar">
              <div className="ct2-laprima-fill" style={{ width: `${Math.min(100, Math.max(5, (film.spectators_total || film.cumulative_attendance || 0) / Math.max(1, film.target_spectators || 5000) * 100))}%` }} />
            </div>
          </div>
        )}
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
          {film.producer_nickname && (
            <div className="ct2-info-director" style={{ cursor: 'pointer', opacity: 0.7 }}
              onClick={(e) => { e.stopPropagation(); window.dispatchEvent(new CustomEvent('open-player-popup', { detail: { nickname: film.producer_nickname } })); }}
              data-testid="ct-production-house">
              {film.production_house_name || film.producer_nickname}
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
        <span className="ct2-data-duration">{durationStr || ''}</span>
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
          {events.map((ev, i) => <div key={`ev${i}`} className="ct2-event-line">{ev}</div>)}
          {perception.length === 0 && events.length === 0 && (
            <div className="ct2-public-line">Nessun dato disponibile</div>
          )}
        </div>
      </div>

      {/* 8. SCREENPLAY (scrollable) */}
      <div className="ct2-screenplay-section" data-testid="ct-screenplay">
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
      </div>

      {/* 9. TRAILER PLACEHOLDER */}
      <div className="ct2-trailer-placeholder" data-testid="ct-trailer-placeholder">
        <Play size={20} />
        <span className="ct2-trailer-text">Trailer in sviluppo</span>
        <span className="ct2-trailer-badge">Funzionalita in arrivo</span>
      </div>

      {/* Cast Popup */}
      <CastPopup open={showCast} onClose={setShowCast} cast={film?.cast} />
    </div>
  );
}
