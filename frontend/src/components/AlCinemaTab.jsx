// CineWorld Studio's — Al Cinema Tracking Dashboard
// Shown inside MyFilms as a dedicated tab. Displays user's films currently in_theaters
// with sparklines, residual value, trend, AI advice, personal records.

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import {
  Film, Loader2, TrendingUp, TrendingDown, Minus, Star, Clock, Tv,
  Sparkles, Trophy, DollarSign, Zap, Filter, ArrowRight
} from 'lucide-react';
import { openFilmActions } from './FilmActionsSheet';

const API = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API}${url}`;
};

const fmtMoney = (v) => {
  const n = Number(v || 0);
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${Math.round(n)}`;
};

export default function AlCinemaTab() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterRecommended, setFilterRecommended] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get('/films/my/al-cinema');
      setData(r.data);
    } catch {
      setData({ films: [], summary: {} });
    }
    setLoading(false);
  }, [api]);

  useEffect(() => { load(); }, [load]);

  // Auto-refresh when film actions happen elsewhere
  useEffect(() => {
    const handler = () => load();
    window.addEventListener('film-actions-updated', handler);
    return () => window.removeEventListener('film-actions-updated', handler);
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16" data-testid="al-cinema-loading">
        <Loader2 className="w-6 h-6 text-amber-400 animate-spin" />
      </div>
    );
  }

  const films = data?.films || [];
  const summary = data?.summary || {};
  const visible = filterRecommended ? films.filter(f => f.recommended_for_tv) : films;

  if (films.length === 0) {
    return (
      <div className="text-center py-16" data-testid="al-cinema-empty">
        <Film className="w-10 h-10 text-gray-700 mx-auto mb-3" />
        <p className="text-sm text-gray-400 mb-1">Nessun film attualmente in sala</p>
        <p className="text-[10px] text-gray-600">Quando un tuo film sara' "Al Cinema" apparira' qui con tracking giornaliero</p>
      </div>
    );
  }

  return (
    <div className="space-y-3" data-testid="al-cinema-tab">
      {/* Summary Strip */}
      <div className="grid grid-cols-3 gap-1.5 px-1">
        <SummaryCard
          icon={<Film className="w-3.5 h-3.5 text-amber-300" />}
          label="In sala"
          value={summary.count ?? 0}
          cls="from-amber-500/15 to-amber-500/5 border-amber-500/25 text-amber-200"
        />
        <SummaryCard
          icon={<DollarSign className="w-3.5 h-3.5 text-emerald-300" />}
          label="Oggi"
          value={fmtMoney(summary.total_today_revenue)}
          cls="from-emerald-500/15 to-emerald-500/5 border-emerald-500/25 text-emerald-200"
        />
        <SummaryCard
          icon={<Sparkles className="w-3.5 h-3.5 text-sky-300" />}
          label="Residuo"
          value={fmtMoney(summary.total_residual_value)}
          cls="from-sky-500/15 to-sky-500/5 border-sky-500/25 text-sky-200"
        />
      </div>

      {/* Filter pill */}
      {summary.recommended_for_tv_count > 0 && (
        <div className="flex items-center justify-between px-1">
          <button
            onClick={() => setFilterRecommended(v => !v)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold transition-all border
              ${filterRecommended
                ? 'bg-amber-500 text-black border-amber-400 shadow-[0_0_10px_rgba(255,200,80,0.4)]'
                : 'bg-white/5 text-amber-300 border-amber-500/30 hover:bg-amber-500/10'}`}
            data-testid="al-cinema-filter-recommended"
          >
            <Filter className="w-3 h-3" />
            Consigliati per TV · {summary.recommended_for_tv_count}
          </button>
          <span className="text-[9px] text-gray-500">{visible.length}/{films.length} mostrati</span>
        </div>
      )}

      {/* Film list */}
      <div className="space-y-2 px-1">
        {visible.map(film => (
          <FilmRow key={film.id} film={film} onOpen={() => openFilmActions(film)} onDetail={() => navigate(`/films/${film.id}`)} />
        ))}
      </div>
    </div>
  );
}

function SummaryCard({ icon, label, value, cls }) {
  return (
    <div className={`rounded-lg border bg-gradient-to-br ${cls} p-2 text-center`}>
      <div className="flex items-center justify-center gap-1 mb-0.5">
        {icon}
        <p className="text-[8px] uppercase tracking-wider opacity-80">{label}</p>
      </div>
      <p className="text-base font-bold font-['Bebas_Neue'] tracking-wide">{value}</p>
    </div>
  );
}

function FilmRow({ film, onOpen, onDetail }) {
  const trendIcon = film.trend === 'growing'
    ? <TrendingUp className="w-3 h-3" />
    : film.trend === 'declining'
      ? <TrendingDown className="w-3 h-3" />
      : <Minus className="w-3 h-3" />;
  const trendCls = film.trend === 'growing'
    ? 'text-emerald-300 bg-emerald-500/15 border-emerald-500/30'
    : film.trend === 'declining'
      ? 'text-rose-300 bg-rose-500/15 border-rose-500/30'
      : 'text-gray-300 bg-white/5 border-white/10';
  const trendLabel = film.trend === 'growing'
    ? `▲ ${film.trend_delta_pct > 0 ? '+' : ''}${film.trend_delta_pct}%`
    : film.trend === 'declining'
      ? `▼ ${film.trend_delta_pct}%`
      : 'Stabile';

  const adv = film.ai_advice || {};
  const adviceCls = {
    gold: 'bg-gradient-to-r from-amber-500/25 to-yellow-400/10 border-amber-400/50 text-amber-100',
    amber: 'bg-amber-500/10 border-amber-500/30 text-amber-200',
    green: 'bg-emerald-500/10 border-emerald-500/25 text-emerald-200',
    gray: 'bg-white/5 border-white/10 text-gray-400',
  }[adv.level] || 'bg-white/5 border-white/10 text-gray-400';

  return (
    <div
      className={`relative rounded-xl border overflow-hidden transition-all active:scale-[0.99]
        ${film.recommended_for_tv
          ? 'bg-gradient-to-br from-amber-500/10 via-[#0f0b08] to-[#0a0807] border-amber-500/40 shadow-[0_0_18px_rgba(212,175,55,0.15)]'
          : 'bg-[#0d0b0a] border-white/10'}`}
      data-testid={`al-cinema-film-${film.id}`}
    >
      {/* Personal record ribbon */}
      {film.is_personal_record && (
        <div className="absolute top-0 right-0 bg-gradient-to-l from-amber-400 to-amber-500 text-black text-[8px] font-black px-2 py-0.5 tracking-wider rounded-bl-md flex items-center gap-1 shadow-[0_0_10px_rgba(255,200,80,0.5)]" data-testid="personal-record-badge">
          <Trophy className="w-2.5 h-2.5" /> RECORD
        </div>
      )}

      <div className="flex gap-2.5 p-2.5">
        {/* Poster */}
        <button onClick={onDetail} className="flex-shrink-0 relative w-[60px] h-[90px] rounded-md overflow-hidden bg-black border border-white/10 active:scale-95 transition-transform" data-testid={`al-cinema-poster-${film.id}`}>
          {posterSrc(film.poster_url) ? (
            <img src={posterSrc(film.poster_url)} alt={film.title} className="w-full h-full object-cover" loading="lazy" />
          ) : <div className="w-full h-full flex items-center justify-center"><Film className="w-5 h-5 text-gray-700" /></div>}
          {/* Day counter */}
          <div className="absolute bottom-0 inset-x-0 bg-black/80 text-center py-0.5 text-[7px] font-bold text-amber-300">
            G {film.days_in}/{film.planned_days}
          </div>
        </button>

        {/* Main info */}
        <div className="flex-1 min-w-0 flex flex-col justify-between">
          <div>
            <h4 className="text-[12px] font-bold text-white leading-tight truncate">{film.title}</h4>
            <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
              <span className={`inline-flex items-center gap-0.5 text-[8px] font-bold px-1.5 py-0.5 rounded-full border ${trendCls}`}>
                {trendIcon} {trendLabel}
              </span>
              {film.quality_score > 0 && (
                <span className="inline-flex items-center gap-0.5 text-[8px] text-yellow-300">
                  <Star className="w-2.5 h-2.5 fill-current" /> {film.quality_score}
                </span>
              )}
              <span className="text-[8px] text-gray-500">·</span>
              <span className="text-[8px] text-gray-400">{film.current_cinemas} cinema</span>
            </div>
          </div>

          {/* Sparkline */}
          <div className="mt-1">
            <Sparkline values={film.daily_revenues_sparkline} />
          </div>

          {/* Revenue row */}
          <div className="flex items-center justify-between mt-1">
            <div className="flex items-baseline gap-1">
              <p className="text-[8px] text-gray-500">Oggi</p>
              <p className="text-[11px] font-bold text-emerald-300">{fmtMoney(film.today_revenue)}</p>
            </div>
            <div className="flex items-baseline gap-1">
              <p className="text-[8px] text-gray-500">Residuo</p>
              <p className="text-[11px] font-bold text-sky-300">{fmtMoney(film.residual_value)}</p>
            </div>
            <div className="flex items-baseline gap-1">
              <p className="text-[8px] text-gray-500">Totale</p>
              <p className="text-[11px] font-bold text-amber-200">{fmtMoney(film.total_revenue)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* AI Advice */}
      {adv.title && (
        <div className={`mx-2.5 mb-2.5 rounded-lg border p-2 ${adviceCls}`} data-testid={`al-cinema-advice-${film.id}`}>
          <div className="flex items-center gap-1.5 mb-0.5">
            {adv.level === 'gold' ? <Zap className="w-3 h-3 animate-pulse" /> : <Clock className="w-3 h-3" />}
            <p className="text-[10px] font-bold tracking-wide">{adv.title}</p>
          </div>
          <p className="text-[9px] leading-tight opacity-90">{adv.body}</p>
        </div>
      )}

      {/* Quick action button */}
      <div className="flex gap-1.5 px-2.5 pb-2.5">
        <button
          onClick={onOpen}
          className={`flex-1 py-1.5 rounded-lg text-[10px] font-bold active:scale-95 transition-all flex items-center justify-center gap-1
            ${film.recommended_for_tv
              ? 'bg-gradient-to-r from-amber-500 to-yellow-300 text-black shadow-[0_0_12px_rgba(255,200,80,0.35)]'
              : 'bg-white/5 border border-white/10 text-amber-200 hover:bg-amber-500/10'}`}
          data-testid={`al-cinema-actions-${film.id}`}
        >
          {film.recommended_for_tv ? <><Tv className="w-3 h-3" /> AZIONI FILM</> : <>Azioni <ArrowRight className="w-3 h-3" /></>}
        </button>
      </div>
    </div>
  );
}

/* ─── Mini Sparkline SVG ─── */
function Sparkline({ values }) {
  if (!values || values.length === 0) return null;
  const w = 160, h = 22, pad = 1;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const step = (w - pad * 2) / Math.max(1, values.length - 1);
  const pts = values.map((v, i) => {
    const x = pad + i * step;
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const path = `M ${pts.join(' L ')}`;
  const areaPath = `${path} L ${pad + (values.length - 1) * step},${h} L ${pad},${h} Z`;
  const lastIdx = values.length - 1;
  const lastX = pad + lastIdx * step;
  const lastY = h - pad - ((values[lastIdx] - min) / range) * (h - pad * 2);

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-[22px]" preserveAspectRatio="none">
      <defs>
        <linearGradient id="spark-gradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(212,175,55,0.4)" />
          <stop offset="100%" stopColor="rgba(212,175,55,0)" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill="url(#spark-gradient)" />
      <path d={path} stroke="rgba(240,200,120,0.9)" strokeWidth="1.2" fill="none" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={lastX} cy={lastY} r="1.8" fill="rgb(255,220,120)" stroke="#000" strokeWidth="0.5" />
    </svg>
  );
}
