import React, { useState, useEffect, useContext, useCallback, useMemo, useRef } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { MapPin, Clock, Flame, Users, BarChart3, Star, TrendingUp, X, Film } from 'lucide-react';
import '../styles/la-prima-popup.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

function formatNum(n) {
  if (typeof n !== 'number') return '0';
  return n.toLocaleString();
}

// === AUDIENCE REACTIONS ===
const REACTIONS = [
  { icon: '\u{1F44F}', text: 'Applausi in sala' },
  { icon: '\u{1F4A5}', text: 'Pubblico coinvolto' },
  { icon: '\u{2B50}', text: 'Prime reazioni positive' },
  { icon: '\u{1F910}', text: 'Silenzio teso in sala' },
  { icon: '\u{1F60D}', text: 'Il pubblico sembra entusiasta' },
  { icon: '\u{1F3AC}', text: 'Scena memorabile in corso' },
  { icon: '\u{1F62E}', text: 'Colpo di scena!' },
  { icon: '\u{1F929}', text: 'Atmosfera elettrica' },
  { icon: '\u{1F3B6}', text: 'Colonna sonora avvolgente' },
  { icon: '\u{1F4F8}', text: 'Flashback potente' },
  { icon: '\u{1F62D}', text: 'Momento toccante' },
  { icon: '\u{1F525}', text: 'Tensione altissima' },
];

// === COUNT-UP HOOK ===
function useCountUp(target, duration = 800) {
  const [display, setDisplay] = useState(target);
  const [flashing, setFlashing] = useState(false);
  const prev = useRef(target);
  const raf = useRef(null);

  useEffect(() => {
    const from = prev.current;
    const to = target;
    prev.current = target;

    if (from === to) return;

    setFlashing(true);
    const start = performance.now();
    const diff = to - from;

    const step = (now) => {
      const t = Math.min((now - start) / duration, 1);
      // ease-out quad
      const ease = 1 - (1 - t) * (1 - t);
      setDisplay(Math.round(from + diff * ease));
      if (t < 1) {
        raf.current = requestAnimationFrame(step);
      } else {
        setFlashing(false);
      }
    };
    raf.current = requestAnimationFrame(step);

    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
  }, [target, duration]);

  return { value: display, flashing };
}

// === SPECTATOR MICRO-JITTER ===
function useSpectatorJitter(base, active) {
  const [jittered, setJittered] = useState(base);
  const [delta, setDelta] = useState(0);

  useEffect(() => { setJittered(base); setDelta(0); }, [base]);

  useEffect(() => {
    if (!active || !base) return;
    const id = setInterval(() => {
      // Tiny random variation: +-0.5% max, biased positive
      const maxShift = Math.max(3, Math.floor(base * 0.005));
      const shift = Math.floor(Math.random() * maxShift * 2) - Math.floor(maxShift * 0.7);
      setJittered(prev => {
        const next = Math.max(0, prev + shift);
        setDelta(d => d + shift);
        return next;
      });
    }, 5000 + Math.random() * 3000); // every 5-8s
    return () => clearInterval(id);
  }, [base, active]);

  return { value: jittered, delta };
}

// === PARTICLES (enhanced) ===
function Particles() {
  const particles = useMemo(() => {
    const arr = [];
    // Rising particles (bottom → up)
    for (let i = 0; i < 14; i++) {
      arr.push({
        type: 'rise',
        left: `${8 + Math.random() * 84}%`,
        size: 1.5 + Math.random() * 2,
        dur: `${6 + Math.random() * 5}s`,
        delay: `${Math.random() * 8}s`,
        drift: `${-15 + Math.random() * 30}px`,
      });
    }
    // Drifting particles (gentle horizontal movement)
    for (let i = 0; i < 10; i++) {
      arr.push({
        type: 'drift',
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        size: 1.5 + Math.random() * 2,
        dur: `${8 + Math.random() * 6}s`,
        delay: `${Math.random() * 6}s`,
      });
    }
    // Twinkle stars (stationary, pulsing)
    for (let i = 0; i < 8; i++) {
      arr.push({
        type: 'twinkle',
        left: `${5 + Math.random() * 90}%`,
        top: `${5 + Math.random() * 90}%`,
        size: 1 + Math.random() * 1.5,
        dur: `${3 + Math.random() * 4}s`,
        delay: `${Math.random() * 5}s`,
      });
    }
    return arr;
  }, []);

  return (
    <div className="particles">
      {particles.map((p, i) => (
        <div
          key={i}
          className={`particle particle--${p.type}`}
          style={{
            left: p.left,
            top: p.top,
            width: `${p.size}px`,
            height: `${p.size}px`,
            '--dur': p.dur,
            '--delay': p.delay,
            '--drift': p.drift,
          }}
        />
      ))}
    </div>
  );
}

// === TREND CHART (enhanced with bezier + colored dots) ===
function TrendChart({ points }) {
  if (!points || points.length < 2) return null;

  const width = 340;
  const height = 70;
  const padX = 10;
  const padY = 8;

  const maxVal = Math.max(...points, 1);
  const minVal = Math.min(...points, 0);
  const range = maxVal - minVal || 1;

  const coords = points.map((val, i) => ({
    x: padX + (i / (points.length - 1)) * (width - 2 * padX),
    y: padY + (1 - (val - minVal) / range) * (height - 2 * padY),
    val,
    trend: i > 0 ? (val > points[i - 1] ? 'positive' : val < points[i - 1] ? 'negative' : 'neutral') : 'neutral',
  }));

  // Build smooth bezier path
  let bezierPath = `M ${coords[0].x} ${coords[0].y}`;
  for (let i = 0; i < coords.length - 1; i++) {
    const curr = coords[i];
    const next = coords[i + 1];
    const cpx = (curr.x + next.x) / 2;
    bezierPath += ` C ${cpx} ${curr.y}, ${cpx} ${next.y}, ${next.x} ${next.y}`;
  }

  const areaPath = `${bezierPath} L ${coords[coords.length - 1].x} ${height - padY} L ${coords[0].x} ${height - padY} Z`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="goldGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#d4af37" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#d4af37" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {[0.25, 0.5, 0.75].map((pct) => (
        <line
          key={pct}
          x1={padX}
          y1={padY + pct * (height - 2 * padY)}
          x2={width - padX}
          y2={padY + pct * (height - 2 * padY)}
          className="grid-line"
        />
      ))}

      {/* Area fill */}
      <path d={areaPath} className="trend-area" />

      {/* Main bezier line */}
      <path d={bezierPath} className="trend-line" />

      {/* Colored dots */}
      {coords.map((c, i) => (
        <circle
          key={i}
          cx={c.x}
          cy={c.y}
          className={`trend-dot trend-dot--${c.trend} ${i === coords.length - 1 ? 'breathe' : ''}`}
          style={{ animationDelay: `${2.5 + i * 0.2}s` }}
          r="0"
        />
      ))}
    </svg>
  );
}

// === GENERATE TREND DATA ===
function generateTrendPoints(specCurrent, specTotal, hype) {
  const points = [];
  const steps = 9;
  const baseVal = Math.max(10, specTotal * 0.04);
  const peak = specCurrent;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const noise = Math.sin(i * 2.1) * 0.08 + Math.cos(i * 3.7) * 0.05;
    const val = baseVal + (peak - baseVal) * Math.pow(t, 1.3) * (1 + noise);
    // Occasional dip to make it realistic
    const dip = (i === 3 || i === 6) ? -peak * 0.04 : 0;
    points.push(Math.max(0, Math.round(val + dip)));
  }
  return points;
}

// === MAIN POPUP ===
export function LaPrimaPopup({ filmId, open, onClose }) {
  const { api } = useContext(AuthContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reactionIdx, setReactionIdx] = useState(0);
  const [reactionKey, setReactionKey] = useState(0);

  const fetchData = useCallback(async () => {
    if (!filmId || !open) return;
    try {
      const res = await api.get(`/la-prima/live/${filmId}`);
      setData(res.data);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [api, filmId, open]);

  useEffect(() => {
    if (open && filmId) {
      setLoading(true);
      fetchData();
      const interval = setInterval(fetchData, 60000);
      return () => clearInterval(interval);
    }
  }, [open, filmId, fetchData]);

  // Rotate audience reactions
  useEffect(() => {
    if (!open || !data) return;
    const id = setInterval(() => {
      setReactionIdx(prev => {
        let next;
        do { next = Math.floor(Math.random() * REACTIONS.length); } while (next === prev);
        return next;
      });
      setReactionKey(k => k + 1);
    }, 8000 + Math.random() * 4000);
    return () => clearInterval(id);
  }, [open, data]);

  // Count-up hooks
  const hypeDisplay = useCountUp(data?.hype_live ?? 0);
  const specTotalDisplay = useCountUp(data?.spectators_total ?? 0);

  // Spectator jitter
  const specLive = useSpectatorJitter(data?.spectators_current ?? 0, open && !!data);

  const trendPoints = useMemo(() => {
    if (!data) return [];
    return generateTrendPoints(data.spectators_current, data.spectators_total, data.hype_live);
  }, [data]);

  const reaction = REACTIONS[reactionIdx];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className="p-0 border-none bg-transparent max-w-[440px] overflow-hidden shadow-2xl"
        data-testid="la-prima-popup"
        hideClose
      >
        <div className="la-prima-popup">
          {/* Decorative layers */}
          <Particles />
          <div className="curtain-left" />
          <div className="curtain-right" />
          <div className="spotlight-top" />
          <div className="red-carpet" />

          {/* Content */}
          <div className="content">
            {/* Banner */}
            <div className="la-prima-banner">
              <h2>LA PRIMA!</h2>
              <button
                className="close-btn"
                onClick={() => onClose(false)}
                data-testid="la-prima-popup-close"
              >
                <X size={16} />
              </button>
            </div>

            {loading || !data ? (
              <div style={{ padding: '60px 0', textAlign: 'center' }}>
                <div
                  style={{
                    width: 32,
                    height: 32,
                    border: '2px solid #d4af37',
                    borderTopColor: 'transparent',
                    borderRadius: '50%',
                    margin: '0 auto',
                    animation: 'spin 1s linear infinite',
                  }}
                />
                <p style={{ color: '#8a7a5a', fontSize: 12, marginTop: 12 }}>Caricamento evento...</p>
              </div>
            ) : (
              <>
                {/* Film card */}
                <div className="la-prima-card">
                  <div className="la-prima-card-inner">
                    {/* Poster */}
                    <div className="la-prima-poster">
                      {posterSrc(data.poster_url) ? (
                        <img
                          src={posterSrc(data.poster_url)}
                          alt={data.title}
                          onError={(e) => { e.target.style.display = 'none'; }}
                        />
                      ) : (
                        <div className="poster-placeholder">
                          <Film size={32} color="#3a3020" />
                        </div>
                      )}
                    </div>

                    {/* Info */}
                    <div className="la-prima-info">
                      {/* Title + LIVE badge */}
                      <div className="la-prima-title-row">
                        <div className="la-prima-title" data-testid="la-prima-popup-title">
                          {data.title}
                        </div>
                        <div className="la-prima-live-badge" data-testid="la-prima-live-badge">
                          <span className="live-dot" />
                          <span className="live-text">LIVE ORA</span>
                        </div>
                      </div>

                      {/* City + Timer */}
                      <div className="la-prima-info-row">
                        <MapPin className="icon" size={16} />
                        <span className="value">{data.city}</span>
                        <span className="separator">|</span>
                        <Clock className="icon" size={16} />
                        <span className="value">{data.time_remaining || '--'}</span>
                      </div>

                      {/* Hype */}
                      <div className="la-prima-info-row">
                        <Flame className="icon" size={16} />
                        <span className="label">Hype:</span>
                        <span
                          className={`value pulse ${hypeDisplay.flashing ? 'flash' : ''}`}
                          data-testid="la-prima-popup-hype"
                        >
                          {formatNum(hypeDisplay.value)}
                        </span>
                      </div>

                      {/* Spettatori attuali (jittered + delta) */}
                      <div className="la-prima-info-row">
                        <Users className="icon" size={16} />
                        <span className="label">Spettatori attuali:</span>
                        <span className="value pulse" data-testid="la-prima-popup-spectators-current">
                          {formatNum(specLive.value)}
                        </span>
                        {specLive.delta !== 0 && (
                          <span
                            className={`la-prima-delta ${specLive.delta > 0 ? 'positive' : 'negative'}`}
                            key={specLive.delta}
                          >
                            {specLive.delta > 0 ? '+' : ''}{specLive.delta}
                          </span>
                        )}
                      </div>

                      {/* Spettatori totali */}
                      <div className="la-prima-info-row">
                        <BarChart3 className="icon" size={16} />
                        <span className="label">Spettatori totali:</span>
                        <span
                          className={`value ${specTotalDisplay.flashing ? 'flash' : ''}`}
                          data-testid="la-prima-popup-spectators-total"
                        >
                          {formatNum(specTotalDisplay.value)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Synopsis */}
                {data.pre_screenplay && (
                  <div className="la-prima-synopsis" data-testid="la-prima-popup-synopsis">
                    {data.pre_screenplay}
                  </div>
                )}

                {/* Audience reaction */}
                <div className="la-prima-reaction" data-testid="la-prima-reaction">
                  <span className="reaction-icon">{reaction.icon}</span>
                  <span className="reaction-text" key={reactionKey}>{reaction.text}</span>
                </div>

                {/* LA PRIMA IN CORSO! */}
                <div className="la-prima-live-section">
                  <div className="la-prima-live-title">LA PRIMA IN CORSO!</div>

                  {/* Stats row */}
                  <div className="la-prima-stats-row">
                    <div className="la-prima-stat-item">
                      <Star className="stat-icon" size={14} color="#d4af37" />
                      <span className="stat-value" style={{ color: '#d4af37' }}>
                        {data.pre_imdb_score?.toFixed(1) || '0.0'}
                      </span>
                    </div>
                    <span className="la-prima-stat-item stat-separator">|</span>
                    <div className="la-prima-stat-item">
                      <Flame className="stat-icon" size={14} color="#e87040" />
                      <span className="stat-value" style={{ color: '#e87040' }}>
                        +IMDB {formatNum(hypeDisplay.value)}
                      </span>
                    </div>
                    <span className="la-prima-stat-item stat-separator">|</span>
                    <div className="la-prima-stat-item">
                      <TrendingUp className="stat-icon" size={14} color="#5cb85c" />
                      <span className="stat-value" style={{ color: '#5cb85c' }}>
                        {formatNum(specLive.value)}
                      </span>
                    </div>
                  </div>

                  {/* +X spettatori negli ultimi minuti */}
                  {specLive.delta > 0 && (
                    <div
                      style={{
                        fontSize: 10,
                        color: '#b0a070',
                        marginBottom: 6,
                        animation: 'la-prima-delta-slide 1s ease-out',
                      }}
                      data-testid="la-prima-spectator-delta-msg"
                    >
                      +{specLive.delta} spettatori negli ultimi minuti
                    </div>
                  )}

                  {/* Trend */}
                  <div className="la-prima-trend">
                    <div className="trend-label">TENDENZA</div>
                    <TrendChart points={trendPoints} />
                  </div>
                </div>

                {/* Brand */}
                <div className="la-prima-brand">
                  <div className="brand-main">CineWorld</div>
                  <div className="brand-sub">Studio's</div>
                </div>

                {/* OK button */}
                <button
                  className="la-prima-ok-btn"
                  onClick={() => onClose(false)}
                  data-testid="la-prima-popup-ok"
                >
                  OK!
                </button>
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
