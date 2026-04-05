import React, { useState, useEffect, useContext, useCallback, useMemo, useRef } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { Film } from 'lucide-react';
import '../styles/la-prima-popup.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

function fmtNum(n) {
  if (typeof n !== 'number') return '0';
  return n.toLocaleString();
}

// Audience reactions
const REACTIONS = [
  '\u{1F44F} Applausi in sala',
  '\u{1F4A5} Pubblico coinvolto',
  '\u{2B50} Prime reazioni positive',
  '\u{1F910} Silenzio teso in sala',
  '\u{1F60D} Il pubblico sembra entusiasta',
  '\u{1F3AC} Scena memorabile in corso',
  '\u{1F62E} Colpo di scena!',
  '\u{1F929} Atmosfera elettrica',
  '\u{1F3B6} Colonna sonora avvolgente',
  '\u{1F525} Tensione altissima',
];

// Count-up hook
function useCountUp(target, dur = 800) {
  const [val, setVal] = useState(target);
  const [flash, setFlash] = useState(false);
  const prev = useRef(target);
  const raf = useRef(null);

  useEffect(() => {
    const from = prev.current;
    prev.current = target;
    if (from === target) return;
    setFlash(true);
    const start = performance.now();
    const diff = target - from;
    const step = (now) => {
      const t = Math.min((now - start) / dur, 1);
      const ease = 1 - (1 - t) * (1 - t);
      setVal(Math.round(from + diff * ease));
      if (t < 1) raf.current = requestAnimationFrame(step);
      else setFlash(false);
    };
    raf.current = requestAnimationFrame(step);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
  }, [target, dur]);

  return { val, flash };
}

// Spectator jitter
function useJitter(base, active) {
  const [v, setV] = useState(base);
  const [delta, setDelta] = useState(0);

  useEffect(() => { setV(base); setDelta(0); }, [base]);

  useEffect(() => {
    if (!active || !base) return;
    const id = setInterval(() => {
      const maxShift = Math.max(3, Math.floor(base * 0.005));
      const shift = Math.floor(Math.random() * maxShift * 2) - Math.floor(maxShift * 0.7);
      setV(p => Math.max(0, p + shift));
      setDelta(d => d + shift);
    }, 5000 + Math.random() * 3000);
    return () => clearInterval(id);
  }, [base, active]);

  return { val: v, delta };
}

// Generate trend points
function genTrend(specCurr, specTotal) {
  const pts = [];
  const steps = 8;
  const base = Math.max(10, specTotal * 0.04);
  const peak = specCurr;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const noise = Math.sin(i * 2.1) * 0.08 + Math.cos(i * 3.7) * 0.05;
    const dip = (i === 3 || i === 6) ? -peak * 0.04 : 0;
    pts.push(Math.max(0, Math.round(base + (peak - base) * Math.pow(t, 1.3) * (1 + noise) + dip)));
  }
  return pts;
}

// SVG Chart
function Chart({ points }) {
  if (!points || points.length < 2) return null;
  const W = 300, H = 100, px = 8, py = 8;
  const max = Math.max(...points, 1), min = Math.min(...points, 0), rng = max - min || 1;
  const coords = points.map((v, i) => ({
    x: px + (i / (points.length - 1)) * (W - 2 * px),
    y: py + (1 - (v - min) / rng) * (H - 2 * py),
    trend: i > 0 ? (v > points[i - 1] ? 'pos' : v < points[i - 1] ? 'neg' : 'neu') : 'neu',
  }));

  let bezier = `M ${coords[0].x} ${coords[0].y}`;
  for (let i = 0; i < coords.length - 1; i++) {
    const c = coords[i], n = coords[i + 1], cpx = (c.x + n.x) / 2;
    bezier += ` C ${cpx} ${c.y}, ${cpx} ${n.y}, ${n.x} ${n.y}`;
  }
  const area = `${bezier} L ${coords[coords.length - 1].x} ${H - py} L ${coords[0].x} ${H - py} Z`;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="lpGoldGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#d4af37" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#d4af37" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} className="trend-area" />
      <path d={bezier} className="trend-line" />
      {coords.map((c, i) => (
        <circle
          key={i} cx={c.x} cy={c.y}
          className={`trend-dot trend-dot--${c.trend} ${i === coords.length - 1 ? 'breathe' : ''}`}
          style={{ animationDelay: `${2.5 + i * 0.2}s` }}
          r="0"
        />
      ))}
    </svg>
  );
}

// === MAIN POPUP ===
export function LaPrimaPopup({ filmId, open, onClose }) {
  const { api } = useContext(AuthContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rxIdx, setRxIdx] = useState(0);
  const [rxKey, setRxKey] = useState(0);

  const fetchData = useCallback(async () => {
    if (!filmId || !open) return;
    try { setData((await api.get(`/la-prima/live/${filmId}`)).data); }
    catch { setData(null); }
    finally { setLoading(false); }
  }, [api, filmId, open]);

  useEffect(() => {
    if (open && filmId) {
      setLoading(true);
      fetchData();
      const id = setInterval(fetchData, 60000);
      return () => clearInterval(id);
    }
  }, [open, filmId, fetchData]);

  // Rotate reactions
  useEffect(() => {
    if (!open || !data) return;
    const id = setInterval(() => {
      setRxIdx(p => { let n; do { n = Math.floor(Math.random() * REACTIONS.length); } while (n === p); return n; });
      setRxKey(k => k + 1);
    }, 8000 + Math.random() * 4000);
    return () => clearInterval(id);
  }, [open, data]);

  const hype = useCountUp(data?.hype_live ?? 0);
  const specTotal = useCountUp(data?.spectators_total ?? 0);
  const specLive = useJitter(data?.spectators_current ?? 0, open && !!data);
  const trend = useMemo(() => data ? genTrend(data.spectators_current, data.spectators_total) : [], [data]);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className="p-0 border-none bg-transparent max-w-[440px] overflow-visible shadow-2xl"
        data-testid="la-prima-popup"
        hideClose
      >
        <div className="lp-root">
          {/* Template background image */}
          <img
            src="/la-prima-template.jpg"
            alt=""
            className="lp-bg"
            draggable={false}
          />

          {/* Overlay container */}
          <div className="lp-overlay">
            {/* Close button (clickable area over template X) */}
            <button
              className="lp-close"
              onClick={() => onClose(false)}
              data-testid="la-prima-popup-close"
              aria-label="Chiudi"
            />

            {loading || !data ? (
              <div className="lp-loading">
                <div className="lp-spinner" />
                <p>Caricamento evento...</p>
              </div>
            ) : (
              <>
                {/* Poster */}
                <div className="lp-poster">
                  {posterSrc(data.poster_url) ? (
                    <img
                      src={posterSrc(data.poster_url)}
                      alt={data.title}
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  ) : (
                    <div className="lp-poster-empty">
                      <Film size={28} color="#3a3020" />
                    </div>
                  )}
                </div>

                {/* Title */}
                <div className="lp-title" data-testid="la-prima-popup-title">
                  {data.title}
                </div>

                {/* City | Timer */}
                <div className="lp-row-city">
                  <span>{data.city}</span>
                  <span className="lp-sep">|</span>
                  <span>{data.time_remaining || '--'}</span>
                </div>

                {/* Hype */}
                <div className="lp-row-hype">
                  <span className="lp-label">Hype:</span>
                  <span className={`lp-val pulse ${hype.flash ? 'flash' : ''}`} data-testid="la-prima-popup-hype">
                    {fmtNum(hype.val)}
                  </span>
                </div>

                {/* Spettatori attuali */}
                <div className="lp-row-spec">
                  <span className="lp-label">Spettatori attuali:</span>
                  <span className="lp-val pulse" data-testid="la-prima-popup-spectators-current">
                    {fmtNum(specLive.val)}
                  </span>
                  {specLive.delta !== 0 && (
                    <span className={`lp-delta ${specLive.delta > 0 ? 'pos' : 'neg'}`} key={specLive.delta}>
                      {specLive.delta > 0 ? '+' : ''}{specLive.delta}
                    </span>
                  )}
                </div>

                {/* Spettatori totali */}
                <div className="lp-row-total">
                  <span className="lp-label">Spettatori totali:</span>
                  <span className={`lp-val ${specTotal.flash ? 'flash' : ''}`} data-testid="la-prima-popup-spectators-total">
                    {fmtNum(specTotal.val)}
                  </span>
                </div>

                {/* Synopsis */}
                {data.pre_screenplay && (
                  <div className="lp-synopsis" data-testid="la-prima-popup-synopsis">
                    {data.pre_screenplay}
                  </div>
                )}

                {/* Audience reaction */}
                <div className="lp-reaction" data-testid="la-prima-reaction">
                  <span key={rxKey}>{REACTIONS[rxIdx]}</span>
                </div>

                {/* Stats row (values placed next to template icons) */}
                <div className="lp-stats">
                  <span className="lp-stat-gold">
                    {data.pre_imdb_score?.toFixed(1) || '0.0'}
                  </span>
                  <span className="lp-stat-sep">|</span>
                  <span className="lp-stat-orange">
                    +IMDB {fmtNum(hype.val)}
                  </span>
                  <span className="lp-stat-sep">|</span>
                  <span className="lp-stat-green">
                    {fmtNum(specLive.val)}
                  </span>
                </div>

                {/* Chart */}
                <div className="lp-chart">
                  <Chart points={trend} />
                </div>

                {/* OK button (clickable area over template OK!) */}
                <button
                  className="lp-ok"
                  onClick={() => onClose(false)}
                  data-testid="la-prima-popup-ok"
                  aria-label="OK"
                />
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
