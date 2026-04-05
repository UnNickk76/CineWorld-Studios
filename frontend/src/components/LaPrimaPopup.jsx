import React, { useState, useEffect, useContext, useCallback, useMemo } from 'react';
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

// Generate deterministic trend data from spectators
function generateTrendPoints(specCurrent, specTotal, hype) {
  const points = [];
  const steps = 8;
  const baseVal = Math.max(10, specTotal * 0.05);
  const peak = specCurrent;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    // Exponential-ish growth curve
    const val = baseVal + (peak - baseVal) * Math.pow(t, 1.4) * (0.85 + Math.sin(t * 3) * 0.15);
    points.push(Math.max(0, Math.round(val)));
  }
  return points;
}

// Particles
function Particles() {
  const particles = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 30; i++) {
      arr.push({
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        animDelay: `${Math.random() * 6}s`,
        size: 1.5 + Math.random() * 2.5,
      });
    }
    return arr;
  }, []);

  return (
    <div className="particles">
      {particles.map((p, i) => (
        <div
          key={i}
          className="particle"
          style={{
            left: p.left,
            top: p.top,
            animationDelay: p.animDelay,
            width: `${p.size}px`,
            height: `${p.size}px`,
          }}
        />
      ))}
    </div>
  );
}

// SVG Trend Chart
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
  }));

  const linePath = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x} ${c.y}`).join(' ');
  const areaPath = `${linePath} L ${coords[coords.length - 1].x} ${height - padY} L ${coords[0].x} ${height - padY} Z`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="goldGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#d4af37" stopOpacity="0.3" />
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

      {/* Main line */}
      <path d={linePath} className="trend-line" />

      {/* Dots */}
      {coords.map((c, i) => (
        <circle
          key={i}
          cx={c.x}
          cy={c.y}
          className="trend-dot"
          style={{ animationDelay: `${2 + i * 0.15}s` }}
          r="0"
        />
      ))}
    </svg>
  );
}

export function LaPrimaPopup({ filmId, open, onClose }) {
  const { api } = useContext(AuthContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

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
      // Refresh every 60s for live feel
      const interval = setInterval(fetchData, 60000);
      return () => clearInterval(interval);
    }
  }, [open, filmId, fetchData]);

  const trendPoints = useMemo(() => {
    if (!data) return [];
    return generateTrendPoints(data.spectators_current, data.spectators_total, data.hype_live);
  }, [data]);

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
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      ) : (
                        <div className="poster-placeholder">
                          <Film size={32} color="#3a3020" />
                        </div>
                      )}
                    </div>

                    {/* Info */}
                    <div className="la-prima-info">
                      <div className="la-prima-title" data-testid="la-prima-popup-title">
                        {data.title}
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
                        <span className="value pulse" data-testid="la-prima-popup-hype">
                          {formatNum(data.hype_live)}
                        </span>
                      </div>

                      {/* Spettatori attuali */}
                      <div className="la-prima-info-row">
                        <Users className="icon" size={16} />
                        <span className="label">Spettatori attuali:</span>
                        <span className="value pulse" data-testid="la-prima-popup-spectators-current">
                          {formatNum(data.spectators_current)}
                        </span>
                      </div>

                      {/* Spettatori totali */}
                      <div className="la-prima-info-row">
                        <BarChart3 className="icon" size={16} />
                        <span className="label">Spettatori totali:</span>
                        <span className="value" data-testid="la-prima-popup-spectators-total">
                          {formatNum(data.spectators_total)}
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
                        +IMDB {formatNum(data.hype_live)}
                      </span>
                    </div>
                    <span className="la-prima-stat-item stat-separator">|</span>
                    <div className="la-prima-stat-item">
                      <TrendingUp className="stat-icon" size={14} color="#5cb85c" />
                      <span className="stat-value" style={{ color: '#5cb85c' }}>
                        {formatNum(data.spectators_current)}
                      </span>
                      <span style={{ color: '#6a5a3a', fontSize: 10 }}>-</span>
                    </div>
                  </div>

                  {/* Trend label */}
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
