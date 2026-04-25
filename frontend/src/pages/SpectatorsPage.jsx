/**
 * Spectators Page — mirrors FinancePage "Storico" pattern but for attendance.
 * Mobile-first, shows film poster grid + detail modal with:
 *   - fixed stats (Totale / Oggi / Trend sparkline)
 *   - La Prima block (solo nuovi film con campo la_prima_spectators)
 *   - daily spectators timeline
 */
import React, { useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Users, X, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { AuthContext } from '../contexts/index';

const fmt = (n) => (n || 0).toLocaleString('it-IT');
const fmtShort = (n) => {
  const v = Number(n) || 0;
  if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (Math.abs(v) >= 1_000) return `${(v / 1_000).toFixed(1)}K`;
  return `${v}`;
};

export default function SpectatorsPage() {
  const navigate = useNavigate();
  const { api } = useContext(AuthContext);
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await api.get('/spectators/films-history');
        setFilms(r.data?.films || []);
      } catch {
        setFilms([]);
      }
      setLoading(false);
    })();
  }, [api]);

  const totalCumulative = films.reduce((acc, f) => acc + (f.total_spectators || 0), 0);
  const totalToday = films.reduce((acc, f) => acc + (f.today_spectators || 0), 0);
  const totalLaPrima = films.reduce((acc, f) => acc + (f.la_prima_spectators || 0), 0);
  const laPrimaCount = films.filter(f => f.has_la_prima && (f.la_prima_spectators || 0) > 0).length;

  return (
    <div className="min-h-screen bg-[#0a080b] text-white pb-24" data-testid="spectators-page">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#0a080b]/95 backdrop-blur-sm border-b border-white/5">
        <div className="flex items-center justify-between px-3 py-3">
          <button onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/'))} className="text-white/70 hover:text-white active:scale-90 transition" data-testid="spectators-back-btn">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-base font-black text-white tracking-wider" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>SPETTATORI</h1>
          <div className="w-5 h-5" />
        </div>

        {/* Summary strip */}
        <div className="grid grid-cols-3 gap-1.5 px-3 pb-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/5 border border-cyan-500/25">
            <p className="text-[9px] text-cyan-300/70 uppercase tracking-wider">Totale</p>
            <p className="text-sm font-bold text-cyan-200" data-testid="spectators-total">{fmtShort(totalCumulative)}</p>
          </div>
          <div className="p-2.5 rounded-lg bg-emerald-500/5 border border-emerald-500/25">
            <p className="text-[9px] text-emerald-300/70 uppercase tracking-wider">Ultime 24h</p>
            <p className="text-sm font-bold text-emerald-200" data-testid="spectators-today">{fmtShort(totalToday)}</p>
          </div>
          <div className="p-2.5 rounded-lg bg-amber-500/5 border border-amber-500/25" data-testid="spectators-la-prima-total">
            <div className="flex items-center gap-1">
              <p className="text-[9px] text-amber-300/70 uppercase tracking-wider">La Prima</p>
              {laPrimaCount > 0 && <span className="text-[7px] text-amber-200/50">·{laPrimaCount}</span>}
            </div>
            <p className="text-sm font-bold text-amber-200">{fmtShort(totalLaPrima)}</p>
          </div>
        </div>
      </div>

      <div className="px-3 pt-3">
        {loading ? (
          <p className="text-center py-10 text-[11px] text-gray-500">Caricamento...</p>
        ) : films.length === 0 ? (
          <div className="text-center py-14" data-testid="spectators-empty">
            <Users className="w-8 h-8 text-gray-700 mx-auto mb-2" />
            <p className="text-[11px] text-gray-500">Nessun film rilasciato</p>
            <p className="text-[9px] text-gray-600 mt-1">Distribuisci un film per vedere l'affluenza qui</p>
          </div>
        ) : (
          <>
            <p className="text-[9px] text-gray-500 uppercase tracking-wider mb-1.5">Tap su una locandina per i dettagli</p>
            <div className="grid grid-cols-5 gap-1.5" data-testid="spectators-poster-grid">
              {films.map(f => <SpectatorPosterMini key={f.id} film={f} onClick={() => setSelected(f)} />)}
            </div>
          </>
        )}
      </div>

      {/* Detail modal */}
      {selected && <SpectatorDetailModal film={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function SpectatorPosterMini({ film, onClick }) {
  const trend = film.attendance_trend || 'flat';
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-emerald-300' : trend === 'down' ? 'text-rose-300' : 'text-gray-500';
  return (
    <button onClick={onClick} className="flex flex-col items-center gap-0.5 active:scale-95 transition-transform" data-testid={`spectator-poster-${film.id}`}>
      <div className="relative w-full aspect-[2/3] rounded-md overflow-hidden bg-black border border-white/10 hover:border-cyan-500/40">
        {film.poster_url ? (
          <img src={film.poster_url} alt={film.title} className="w-full h-full object-cover" loading="lazy"
               onError={(e) => { e.target.style.display = 'none'; }} />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-cyan-900/30 to-black flex items-center justify-center">
            <Users className="w-4 h-4 text-cyan-400/50" />
          </div>
        )}
        {film.has_la_prima && (
          <div className="absolute top-0.5 left-0.5 bg-amber-500/90 text-black text-[6px] font-black px-1 py-px rounded leading-none tracking-wide">LP</div>
        )}
      </div>
      <p className="text-[8px] text-white font-semibold truncate w-full leading-tight">{film.title}</p>
      <div className="flex items-center gap-0.5">
        <TrendIcon className={`w-2.5 h-2.5 ${trendColor}`} strokeWidth={3} />
        <span className="text-[7px] font-bold text-cyan-300">{fmtShort(film.total_spectators)}</span>
      </div>
    </button>
  );
}

function SpectatorDetailModal({ film, onClose }) {
  const trend = film.attendance_trend || 'flat';
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-300' : trend === 'down' ? 'bg-rose-500/10 border-rose-500/25 text-rose-300' : 'bg-gray-500/10 border-gray-500/25 text-gray-400';
  const trendLabel = trend === 'up' ? 'In crescita' : trend === 'down' ? 'In calo' : 'Stabile';

  // Sparkline (variable length, matches days_in_theaters)
  const sparkData = film.daily_spectators || [];
  const maxVal = Math.max(1, ...sparkData.map(d => d.total || 0));
  const sparkW = 280, sparkH = 40;
  const pts = sparkData.map((d, i) => {
    const x = (i / Math.max(1, sparkData.length - 1)) * (sparkW - 8) + 4;
    const y = sparkH - 4 - ((d.total / maxVal) * (sparkH - 8));
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="fixed inset-0 z-[2000] bg-black/80 flex items-end sm:items-center justify-center p-0 sm:p-4" onClick={onClose} data-testid="spectator-detail-modal">
      <div onClick={(e) => e.stopPropagation()}
           className="w-full sm:max-w-md bg-[#0f0d10] border-t sm:border border-cyan-500/30 rounded-t-2xl sm:rounded-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="relative p-3 border-b border-white/10">
          <button onClick={onClose} className="absolute top-2 right-2 w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-white active:scale-90 transition-transform z-10" data-testid="spectator-detail-close">
            <X className="w-4 h-4" />
          </button>
          <div className="flex gap-3">
            <div className="w-16 aspect-[2/3] rounded-md overflow-hidden bg-black border border-white/10 flex-shrink-0">
              {film.poster_url ? (
                <img src={film.poster_url} alt={film.title} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-cyan-900/30 to-black" />
              )}
            </div>
            <div className="flex-1 min-w-0 pr-7">
              <p className="text-[9px] text-cyan-400/70 tracking-wider uppercase">Spettatori</p>
              <h3 className="text-lg font-black text-white leading-tight truncate" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>{film.title}</h3>
              <p className="text-[9px] text-gray-500 mt-0.5">{film.days_in_theaters} {film.days_in_theaters === 1 ? 'giorno' : 'giorni'} al cinema</p>
            </div>
          </div>
        </div>

        {/* Fixed stats */}
        <div className="p-3 space-y-2">
          <div className="grid grid-cols-3 gap-1.5">
            <div className="p-2 rounded-lg bg-cyan-500/5 border border-cyan-500/15">
              <p className="text-[8px] text-cyan-300/80 uppercase tracking-wider">Totale</p>
              <p className="text-[11px] font-bold text-cyan-200" data-testid="spectator-detail-total">{fmt(film.total_spectators)}</p>
            </div>
            <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/15">
              <p className="text-[8px] text-emerald-300/80 uppercase tracking-wider">Ora</p>
              <p className="text-[11px] font-bold text-emerald-200" data-testid="spectator-detail-now">{fmt(film.today_spectators)}</p>
            </div>
            <div className={`p-2 rounded-lg border ${trendColor}`}>
              <p className="text-[8px] uppercase tracking-wider opacity-80">Trend</p>
              <p className="text-[11px] font-bold flex items-center gap-0.5" data-testid="spectator-detail-trend">
                <TrendIcon className="w-3 h-3" strokeWidth={3} /> {trendLabel}
              </p>
            </div>
          </div>

          {/* Sparkline dinamico (solo se abbastanza dati) */}
          {sparkData.length >= 2 && (
            <div className="p-2.5 rounded-lg bg-[#0a080b] border border-white/5" data-testid="spectator-sparkline">
              <p className="text-[9px] text-gray-500 uppercase tracking-wider mb-1">Andamento ({sparkData.length} {sparkData.length === 1 ? 'giorno' : 'giorni'})</p>
              <svg viewBox={`0 0 ${sparkW} ${sparkH}`} className="w-full" style={{ height: sparkH }}>
                <polyline
                  fill="none"
                  stroke={trend === 'down' ? '#f43f5e' : '#10b981'}
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={pts}
                />
                {sparkData.map((d, i) => {
                  const x = (i / Math.max(1, sparkData.length - 1)) * (sparkW - 8) + 4;
                  const y = sparkH - 4 - ((d.total / maxVal) * (sparkH - 8));
                  return <circle key={i} cx={x} cy={y} r="1.5" fill={trend === 'down' ? '#f43f5e' : '#10b981'} />;
                })}
              </svg>
            </div>
          )}

          {/* La Prima block */}
          {film.has_la_prima && film.la_prima_spectators > 0 && (
            <div className="p-2.5 rounded-lg bg-gradient-to-r from-amber-500/10 to-transparent border border-amber-500/25" data-testid="spectator-la-prima">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="text-[9px] font-black text-amber-300 tracking-[0.2em] uppercase">La Prima</span>
                  {film.la_prima_city && <span className="text-[9px] text-amber-200/70">· {film.la_prima_city}{film.la_prima_nation ? `, ${film.la_prima_nation}` : ''}</span>}
                </div>
                <span className="text-[11px] font-bold text-amber-300">{fmt(film.la_prima_spectators)}</span>
              </div>
              <p className="text-[8px] text-amber-200/60 mt-0.5">Spettatori delle 24h di premiere</p>
            </div>
          )}

          {/* Daily timeline */}
          <div className="mt-1">
            <p className="text-[9px] text-gray-500 uppercase tracking-wider mb-1.5">Affluenza per giorno al cinema</p>
            {(!film.daily_spectators || film.daily_spectators.length === 0) ? (
              <p className="text-[10px] text-gray-600 text-center py-6">Nessun dato affluenza ancora registrato.<br/>Aggiornato ogni 10 min.</p>
            ) : (
              <div className="space-y-1">
                {film.daily_spectators.map((d, i) => {
                  const pct = maxVal > 0 ? (d.total / maxVal) * 100 : 0;
                  const dayLabel = d.day ? `Giorno ${d.day}` : d.date;
                  return (
                    <div key={i} className="p-2 rounded bg-[#0a080b] border border-white/5" data-testid={`spectator-day-${i}`}>
                      <div className="flex items-center justify-between">
                        <p className="text-[10px] font-semibold text-white">{dayLabel}</p>
                        <p className="text-[11px] font-bold text-cyan-300">{fmt(d.total)}</p>
                      </div>
                      <div className="h-1 bg-white/5 rounded-full overflow-hidden mt-1">
                        <div className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400" style={{ width: `${pct}%` }} />
                      </div>
                      <p className="text-[8px] text-gray-600 mt-0.5">{d.date}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
