import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { toast } from 'sonner';
import {
  Film, Star, Flame, Users, DollarSign, Heart, ChevronRight, X, Play,
  Building, Sparkles, BookOpen, Clapperboard, Zap, Loader2,
  Newspaper, Crown, Award, Pen
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
const fmtNum = (n) => {
  if (!n) return '0';
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toLocaleString();
};

// Generate critic reviews from quality/hype
const FILM_OUTLETS = ['VARIETY', 'EMPIRE', 'HOLLYWOOD R.'];
const SERIES_OUTLETS = ['IGN', 'COLLIDER', 'ENTERTAINMENT W.'];
const POSITIVE_QUOTES = {
  VARIETY: [
    "Un'esperienza cinematografica straordinaria!",
    "Un'opera che ridefinisce il genere",
    "Spettacolare da ogni punto di vista",
  ],
  EMPIRE: [
    "Impressionante dall'inizio alla fine",
    "Un capolavoro moderno del cinema",
    "Emozionante e visivamente stupendo",
  ],
  'HOLLYWOOD R.': [
    "Uno dei migliori film degli ultimi anni",
    "Un trionfo del cinema contemporaneo",
    "Destinato a diventare un classico",
  ],
  IGN: [
    "Intrigante e piena di suspense!",
    "Una serie che alza il livello del genere",
    "Da non perdere assolutamente",
  ],
  COLLIDER: [
    "Una serie crime da non perdere!",
    "Narrativa avvincente e cast perfetto",
    "Uno show di altissimo livello",
  ],
  'ENTERTAINMENT W.': [
    "Un thriller che tiene incollati alla sedia!",
    "Televisione di qualita superiore",
    "Imperdibile dall'inizio alla fine",
  ],
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
    return { outlet, quote: `"${pool[idx]}"` };
  });
}

// Helper: extract text from string or {text, generated_at} object
const toStr = (v) => typeof v === 'string' ? v : (v?.text || v?.content || '');
// === SUB-POPUP: Comments ===
function CommentsPopup({ open, onClose, reviews }) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="p-0 border-none bg-transparent max-w-[420px]" hideClose>
        <div className="ct-subpopup">
          <div className="ct-subpopup-header">
            <span className="ct-subpopup-title">COMMENTI</span>
            <button className="ct-subpopup-close" onClick={() => onClose(false)}><X size={14} /></button>
          </div>
          <div className="ct-subpopup-body">
            {(!reviews || reviews.length === 0) ? (
              <p style={{ color: '#6a5a3a', textAlign: 'center', padding: 20, fontSize: 12 }}>Nessun commento ancora</p>
            ) : reviews.map((r, i) => (
              <div key={i} className="ct-sub-comment">
                <img
                  src={r.reviewer?.avatar_url || `https://api.dicebear.com/9.x/avataaars/svg?seed=user${i}`}
                  alt="" className="ct-sub-comment-avatar"
                  onError={(e) => { e.target.src = `https://api.dicebear.com/9.x/avataaars/svg?seed=user${i}`; }}
                />
                <div>
                  <div className="ct-sub-comment-name">
                    {r.reviewer?.name || r.reviewer?.display || `Utente ${i + 1}`}
                  </div>
                  <div className="ct-sub-comment-text">{r.text || r.comment || 'Bel film!'}</div>
                  {r.rating && (
                    <div className="ct-sub-comment-rating">
                      <Star size={10} color="#d4af37" fill="#d4af37" />
                      <span style={{ fontSize: 10, color: '#d4af37' }}>{r.rating}/10</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// === SUB-POPUP: Screenplay ===
function ScreenplayPopup({ open, onClose, text }) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="p-0 border-none bg-transparent max-w-[420px]" hideClose>
        <div className="ct-subpopup">
          <div className="ct-subpopup-header">
            <span className="ct-subpopup-title">SCENEGGIATURA</span>
            <button className="ct-subpopup-close" onClick={() => onClose(false)}><X size={14} /></button>
          </div>
          <div className="ct-subpopup-body">
            <div className="ct-sub-screenplay">{toStr(text) || 'Sceneggiatura non disponibile.'}</div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// === SUB-POPUP: Cast & Crew ===
function CastPopup({ open, onClose, cast }) {
  const members = [];
  if (cast) {
    if (Array.isArray(cast)) {
      // Flat array of actors (films use role_in_film, series use role)
      cast.forEach((a) => members.push({ ...a, role: a.role_in_film || a.role || 'Attore' }));
    } else {
      if (cast.director) members.push({ ...cast.director, role: 'Regista' });
      if (Array.isArray(cast.actors)) {
        cast.actors.forEach((a) => members.push({ ...a, role: a.role_in_film || a.role || 'Attore' }));
      }
      // Handle dict format
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
        <div className="ct-subpopup">
          <div className="ct-subpopup-header">
            <span className="ct-subpopup-title">CAST & CREW</span>
            <button className="ct-subpopup-close" onClick={() => onClose(false)}><X size={14} /></button>
          </div>
          <div className="ct-subpopup-body">
            {members.length === 0 ? (
              <p style={{ color: '#6a5a3a', textAlign: 'center', padding: 20, fontSize: 12 }}>Cast non disponibile</p>
            ) : members.map((m, i) => (
              <div key={i} className="ct-sub-cast-item">
                <img
                  src={m.avatar_url || `https://api.dicebear.com/9.x/avataaars/svg?seed=${m.name || i}`}
                  alt="" className="ct-sub-cast-avatar"
                  onError={(e) => { e.target.src = `https://api.dicebear.com/9.x/avataaars/svg?seed=cast${i}`; }}
                />
                <div>
                  <div className="ct-sub-cast-name">{m.name}</div>
                  <div className="ct-sub-cast-role">{m.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// === SUB-POPUP: Trailer ===
function TrailerPopup({ open, onClose, trailerUrl }) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="p-0 border-none bg-transparent max-w-[420px]" hideClose>
        <div className="ct-subpopup">
          <div className="ct-subpopup-header">
            <span className="ct-subpopup-title">TRAILER</span>
            <button className="ct-subpopup-close" onClick={() => onClose(false)}><X size={14} /></button>
          </div>
          <div className="ct-subpopup-body">
            {trailerUrl ? (
              <video src={`${BACKEND_URL}${trailerUrl}`} controls className="w-full rounded" />
            ) : (
              <div className="ct-sub-trailer-placeholder">
                <Play />
                <p style={{ fontSize: 14, color: '#9a8a6a', marginBottom: 4 }}>Funzionalita in Sviluppo</p>
                <p style={{ fontSize: 10 }}>Il trailer sara disponibile prossimamente</p>
              </div>
            )}
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
  const [actions, setActions] = useState(null);
  const [virtualAudience, setVirtualAudience] = useState(null);
  const [performing, setPerforming] = useState(null);

  // Sub-popup states
  const [showComments, setShowComments] = useState(false);
  const [showScreenplay, setShowScreenplay] = useState(false);
  const [showCast, setShowCast] = useState(false);
  const [showTrailer, setShowTrailer] = useState(false);

  const loadFilm = useCallback(async () => {
    if (!filmId) return;
    setLoading(true);
    try {
      const endpoint = contentType === 'series' ? `/series/${filmId}` : contentType === 'anime' ? `/anime/${filmId}` : `/films/${filmId}`;
      const [filmRes, actionsRes, vaRes] = await Promise.all([
        api.get(endpoint),
        api.get(`/films/${filmId}/actions`).catch(() => ({ data: null })),
        api.get(`/films/${filmId}/virtual-audience`).catch(() => ({ data: null })),
      ]);
      if (filmRes.data && !filmRes.data.detail) {
        setFilm(filmRes.data);
        setActions(actionsRes.data);
        setVirtualAudience(vaRes.data);
      }
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [api, filmId, contentType]);

  useEffect(() => { loadFilm(); }, [loadFilm]);

  const isOwner = actions?.is_owner || film?.user_id === user?.id;
  const isComingSoon = film?.status === 'coming_soon' || film?.status === 'pending_release';
  const isInTheaters = film?.status === 'in_theaters' || film?.status === 'completed';

  // Actions
  const doCollect = async () => {
    setPerforming('collect');
    try {
      const res = await api.post(`/films/${film.id}/process-hourly-revenue`);
      if (res.data.processed) toast.success(`Incasso: ${fmtMoney(res.data.revenue)}!`);
      else toast.info(`Attendi ${Math.ceil(res.data.wait_seconds / 60)} minuti`);
      loadFilm();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setPerforming(null);
  };

  const doCreateStar = async () => {
    setPerforming('star');
    try {
      const cast = film.cast;
      const actorId = cast?.protagonist?.id || cast?.actors?.[0]?.id;
      if (!actorId) { toast.error('Nessun attore disponibile'); return; }
      const res = await api.post(`/films/${film.id}/action/create-star?actor_id=${actorId}`);
      toast.success(res.data.message);
      loadFilm();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setPerforming(null);
  };

  const doBoostCrew = async () => {
    setPerforming('boost');
    try {
      const res = await api.post(`/films/${film.id}/action/skill-boost`);
      toast.success(res.data.message);
      loadFilm();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setPerforming(null);
  };

  // Comments from virtual audience (film) or audience_comments (series)
  const isSeries = contentType === 'series';
  const rawComments = isSeries
    ? (film?.audience_comments || [])
    : (virtualAudience?.reviews || []);
  // Normalizza formato commenti
  const comments = rawComments.map((c, i) => ({
    reviewer: c.reviewer || { name: c.reviewer_name || `Spettatore ${i+1}`, display: c.reviewer_name },
    text: typeof c === 'string' ? c : (c.text || c.comment || ''),
    comment: typeof c === 'string' ? c : (c.text || c.comment || ''),
  }));
  const reviews = film ? generateReviews(film.quality_score, film.popularity_score, contentType) : [];
  const templateImg = isSeries ? '/series-template.png' : '/content-template.png';

  const headerText = isComingSoon ? 'COMING SOON' : isInTheaters ? 'IN PROGRAMMAZIONE..' : film?.status?.toUpperCase() || '';

  return (
    <div className={`ct-root ${isSeries ? 'ct-series' : ''}`} data-testid="content-template">
      {/* Template background */}
      <img src={templateImg} alt="" className="ct-bg" draggable={false} />

      {/* Overlay */}
      <div className="ct-overlay">
        {/* Header status badge — arched inside the ribbon */}
        <div className="ct-header-badge" data-testid="ct-header">
          <span className="ct-header-text">{headerText}</span>
        </div>

        {/* Close */}
        <button
          className="ct-close"
          onClick={() => navigate(-1)}
          data-testid="ct-close"
          aria-label="Chiudi"
        >
          <X size={18} />
        </button>

        {loading || !film ? (
          <div className="ct-loading">
            <div className="ct-spinner" />
            <p style={{ color: '#8a7a5a', fontSize: 11, marginTop: 8 }}>Caricamento...</p>
          </div>
        ) : (
          <>
            {/* === POSTER === */}
            <div className="ct-poster">
              {posterSrc(film.poster_url) ? (
                <img src={posterSrc(film.poster_url)} alt={film.title} onError={(e) => { e.target.style.display = 'none'; }} />
              ) : (
                <div className="ct-poster-empty"><Film size={24} color="#3a3020" /></div>
              )}
            </div>

            {/* === TITLE === */}
            <div className="ct-title" data-testid="ct-title">{film.title}</div>

            {isComingSoon ? (
              /* === COMING SOON VARIANT === */
              <>
                <div className="ct-cs-badge">COMING SOON</div>
                <div className="ct-genre-row">
                  <span className="ct-genre-badge">{film.genre}</span>
                  {film.subgenres?.slice(0, 2).map((s, i) => (
                    <span key={i} className="ct-genre-badge">{s}</span>
                  ))}
                </div>
                {(film.hype_score || film.hype) && (
                  <div className="ct-cs-hype">
                    <Flame />
                    <span>Hype: {fmtNum(film.hype_score || film.hype)}</span>
                  </div>
                )}
                <div className="ct-cs-synopsis">
                  {toStr(film.pre_screenplay) || toStr(film.screenplay) || toStr(film.description) || 'Trama non disponibile.'}
                </div>
              </>
            ) : (
              /* === IN PROGRAMMAZIONE VARIANT === */
              <>
                {/* Genre + Cinemas */}
                <div className="ct-genre-row" data-testid="ct-genre">
                  <span className="ct-genre-badge">{film.genre}</span>
                  {film.subgenres?.slice(0, 1).map((s, i) => (
                    <span key={i} className="ct-genre-badge">{s}</span>
                  ))}
                  <div className="ct-cinemas">
                    <Building size={12} />
                    <span>{film.current_cinemas || 0} Cinema</span>
                  </div>
                </div>

                {/* Stats: Revenue + Likes */}
                <div className="ct-stats-row" data-testid="ct-stats">
                  <div className="ct-stat ct-stat-gold">
                    <DollarSign />
                    <span>{fmtMoney(film.realistic_box_office || film.total_revenue || 0)} Totale</span>
                  </div>
                  <div className="ct-stat ct-stat-pink">
                    <Heart />
                    <span>+{fmtNum(film.virtual_likes || film.likes_count || 0)}</span>
                  </div>
                </div>

                {/* Clickable section triggers (Sceneggiatura + Cast) */}
                <div style={{
                  position: 'absolute', top: '29%', left: '29%', width: '58%',
                  display: 'flex', gap: '8px', pointerEvents: 'auto'
                }}>
                  <button
                    onClick={() => setShowScreenplay(true)}
                    style={{
                      background: 'transparent', border: '1px solid rgba(212,175,55,0.2)',
                      borderRadius: 3, padding: '2px 8px', cursor: 'pointer',
                      display: 'flex', alignItems: 'center', gap: 3,
                      fontFamily: "'Bebas Neue', sans-serif", fontSize: 'clamp(8px, 2vw, 10px)',
                      letterSpacing: '0.5px', color: '#c0a060'
                    }}
                    data-testid="ct-screenplay-btn"
                  >
                    <BookOpen size={10} /> Sceneggiatura &gt;
                  </button>
                  <button
                    onClick={() => setShowCast(true)}
                    style={{
                      background: 'transparent', border: '1px solid rgba(212,175,55,0.2)',
                      borderRadius: 3, padding: '2px 8px', cursor: 'pointer',
                      display: 'flex', alignItems: 'center', gap: 3,
                      fontFamily: "'Bebas Neue', sans-serif", fontSize: 'clamp(8px, 2vw, 10px)',
                      letterSpacing: '0.5px', color: '#c0a060'
                    }}
                    data-testid="ct-cast-btn"
                  >
                    <Clapperboard size={10} /> Cast & Crew &gt;
                  </button>
                </div>

                {/* === COMMENTS === */}
                <div className="ct-comments" data-testid="ct-comments">
                  <div className="ct-comments-header">
                    <span className="ct-comments-title">COMMENTI</span>
                    <div className="ct-comments-avatars">
                      {comments.slice(0, 5).map((c, i) => (
                        <img
                          key={i}
                          src={c.reviewer?.avatar_url || `https://api.dicebear.com/9.x/avataaars/svg?seed=va${i}`}
                          alt=""
                          className="ct-comments-avatar"
                          onError={(e) => { e.target.src = `https://api.dicebear.com/9.x/avataaars/svg?seed=va${i}`; }}
                        />
                      ))}
                    </div>
                    <span className="ct-comments-more" onClick={() => setShowComments(true)} data-testid="ct-comments-more">
                      +{comments.length} &gt;
                    </span>
                  </div>
                  {comments.slice(0, 3).map((c, i) => (
                    <div key={i} className="ct-comment-item" onClick={() => setShowComments(true)}>
                      <img
                        src={c.reviewer?.avatar_url || `https://api.dicebear.com/9.x/avataaars/svg?seed=rev${i}`}
                        alt=""
                        className="ct-comment-avatar"
                        onError={(e) => { e.target.src = `https://api.dicebear.com/9.x/avataaars/svg?seed=rev${i}`; }}
                      />
                      <div className="ct-comment-text">
                        <span className="ct-comment-name">{c.reviewer?.name || c.reviewer?.display}: </span>
                        <span className="ct-comment-body">{c.text || c.comment || 'Ottimo film!'}</span>
                      </div>
                      <span className="ct-comment-arrow"><ChevronRight /></span>
                    </div>
                  ))}
                </div>

                {/* === GOLDEN DIVIDER === */}
                <div className="ct-gold-divider" />

                {/* === ACTIONS (owner only) === */}
                <div className="ct-actions" data-testid="ct-actions">
                  <button
                    className="ct-action-btn"
                    onClick={doCollect}
                    disabled={!isOwner || performing === 'collect'}
                    data-testid="ct-action-collect"
                  >
                    {performing === 'collect' ? <Loader2 size={12} className="animate-spin" /> : <DollarSign />}
                    INCASSA ORA
                  </button>
                  <button
                    className="ct-action-btn"
                    onClick={doCreateStar}
                    disabled={!isOwner || !actions?.actions?.create_star?.available || performing === 'star'}
                    data-testid="ct-action-star"
                  >
                    {performing === 'star' ? <Loader2 size={12} className="animate-spin" /> : <Sparkles />}
                    CREA STELLA
                  </button>
                  <button
                    className="ct-action-btn"
                    onClick={doBoostCrew}
                    disabled={!isOwner || !actions?.actions?.skill_boost?.available || performing === 'boost'}
                    data-testid="ct-action-boost"
                  >
                    {performing === 'boost' ? <Loader2 size={12} className="animate-spin" /> : <Users />}
                    BOOST CREW &gt;
                  </button>
                </div>

                {/* === REVIEWS === */}
                <div className="ct-reviews" data-testid="ct-reviews">
                  {reviews.map((r, i) => {
                    const isVariety = r.outlet === 'VARIETY';
                    const isEmpire = r.outlet === 'EMPIRE';
                    // Film: card piene con icone. Series: solo citazione (sfondo nel template)
                    const journalClass = isSeries
                      ? `ct-journal ct-journal-series ct-journal-s${i}`
                      : `ct-journal ${isVariety ? 'ct-journal-variety' : isEmpire ? 'ct-journal-empire' : 'ct-journal-thr'}`;
                    return (
                      <div key={i} className={`ct-review-card ${journalClass}`}>
                        {!isSeries && (
                          <>
                            <div className="ct-journal-icon">
                              {isVariety ? <Award size={12} /> : isEmpire ? <Crown size={12} /> : <Newspaper size={12} />}
                            </div>
                            <div className="ct-review-outlet">{r.outlet}</div>
                            <div className="ct-journal-rule" />
                          </>
                        )}
                        <div className="ct-review-quote">{r.quote}</div>
                      </div>
                    );
                  })}
                </div>

                {/* === TRAMA === */}
                <div className="ct-trama" data-testid="ct-trama">
                  <div className="ct-trama-content">
                    {toStr(film.screenplay) || toStr(film.pre_screenplay) || toStr(film.description) || 'Trama non ancora disponibile per questo contenuto.'}
                  </div>
                </div>

                {/* === FOOTER === */}
                <div className="ct-footer-dev" onClick={() => setShowTrailer(true)} data-testid="ct-footer-dev">
                  Funzionalita in Sviluppo &rarr;
                </div>

                <button className="ct-trailer-btn" onClick={() => setShowTrailer(true)} data-testid="ct-trailer-btn">
                  <span className="ct-trailer-star ct-trailer-star-l">&#10022;</span>
                  <Film size={11} />
                  <span>TRAILER</span>
                  <Clapperboard size={11} />
                  <span className="ct-trailer-star ct-trailer-star-r">&#10022;</span>
                </button>
              </>
            )}
          </>
        )}
      </div>

      {/* Sub-popups */}
      <CommentsPopup open={showComments} onClose={setShowComments} reviews={comments} />
      <ScreenplayPopup open={showScreenplay} onClose={setShowScreenplay} text={toStr(film?.screenplay)} />
      <CastPopup open={showCast} onClose={setShowCast} cast={film?.cast} />
      <TrailerPopup open={showTrailer} onClose={setShowTrailer} trailerUrl={film?.trailer_url} />
    </div>
  );
}
