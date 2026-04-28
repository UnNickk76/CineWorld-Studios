// CineWorld Studio's — CinemaStatsModal
// Modale "AL CINEMA" completo per qualsiasi contenuto attivo:
//  • Header con totali (incassi, spettatori, giorni)
//  • Performance message Velion (aggiornato ogni ora, badge NUOVO)
//  • Grafico affluenze giornaliere (heatmap colors + forecast)
//  • Top 3 città
//  • Bonus stats (avg ticket, occupancy, badges, comparison vs media player)
//  • Azioni proprietario (Ritira / Prolunga)
//
// Design coerente col gioco: gradient dark, ring cyan/emerald, font compact.
// Mobile-first (390px optimized), scroll interno.

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Loader2, Film, Coins, Users, Calendar, Clock,
  Building2, Trophy, BarChart3, Share2, MapPin, Bell, BellOff,
  TrendingUp, Sparkles,
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { AttendanceChart } from './AttendanceChart';
import { TopCitiesPanel } from './TopCitiesPanel';
import { PerformanceMessage } from './PerformanceMessage';
import { CinemaActions } from './CinemaActions';
import { LaPrimaBanner } from './LaPrimaBanner';

const API = process.env.REACT_APP_BACKEND_URL;

const fmtMoney = (v) => `$${Math.round(Number(v || 0)).toLocaleString('it-IT')}`;
const fmtNum = (v) => Number(v || 0).toLocaleString('it-IT');

export const CinemaStatsModal = ({ contentId, onClose }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [chartMode, setChartMode] = useState(() => {
    try { return localStorage.getItem('cinema_chart_mode') || 'live'; } catch { return 'live'; }
  });
  const [notifSubscribed, setNotifSubscribed] = useState(() => {
    try { return localStorage.getItem(`cinema_notif:${contentId}`) === '1'; } catch { return false; }
  });

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.get(`${API}/api/cinema-stats/${contentId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setStats(res.data);
      setError(null);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Errore caricamento stats');
    } finally {
      setLoading(false);
    }
  }, [contentId]);

  useEffect(() => { if (contentId) fetchStats(); }, [contentId, fetchStats]);

  // Auto-refresh ogni 5 min (per intra-day live)
  useEffect(() => {
    if (!contentId) return;
    const t = setInterval(fetchStats, 5 * 60 * 1000);
    return () => clearInterval(t);
  }, [contentId, fetchStats]);

  const handleActionDone = async () => {
    await fetchStats();
  };

  const toggleNotif = () => {
    const newVal = !notifSubscribed;
    setNotifSubscribed(newVal);
    try {
      localStorage.setItem(`cinema_notif:${contentId}`, newVal ? '1' : '0');
      toast.success(newVal ? '🔔 Riceverai aggiornamenti sull\'andamento' : '🔕 Notifiche disattivate');
    } catch { /* noop */ }
  };

  const handleShare = () => {
    if (!stats) return;
    const text = `🎬 "${stats.content.title}" al cinema · ${fmtMoney(stats.summary.total_revenue)} d'incassi · ${fmtNum(stats.summary.total_spectators)} spettatori · ${stats.performance?.classification?.toUpperCase()}`;
    if (navigator.share) {
      navigator.share({ title: stats.content.title, text }).catch(() => {});
    } else {
      navigator.clipboard?.writeText(text);
      toast.success('Stats copiate negli appunti');
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-[9999] bg-black/85 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
        data-testid="cinema-stats-modal"
      >
        <motion.div
          initial={{ y: 30, scale: 0.96 }}
          animate={{ y: 0, scale: 1 }}
          exit={{ y: 30, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="w-full sm:max-w-lg max-h-[92vh] overflow-y-auto bg-gradient-to-br from-zinc-950 via-zinc-950 to-zinc-900 rounded-t-3xl sm:rounded-3xl ring-1 ring-cyan-700/30 shadow-2xl"
        >
          {/* Header */}
          <div className="sticky top-0 z-10 backdrop-blur-md bg-zinc-950/90 border-b border-cyan-900/30">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
                  <Film className="w-4 h-4 text-cyan-300" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-[10px] uppercase tracking-wider text-cyan-400 font-bold">Al Cinema</div>
                  <div className="text-sm font-bold text-zinc-100 truncate" data-testid="cinema-stats-title">
                    {stats?.content?.title || 'Caricamento…'}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={toggleNotif}
                  className="p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400"
                  title={notifSubscribed ? 'Disattiva notifiche' : 'Attiva notifiche'}
                  data-testid="cinema-stats-notif-toggle"
                >
                  {notifSubscribed ? <Bell className="w-4 h-4 text-amber-400" /> : <BellOff className="w-4 h-4" />}
                </button>
                <button
                  onClick={handleShare}
                  className="p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400"
                  title="Condividi"
                  data-testid="cinema-stats-share"
                >
                  <Share2 className="w-4 h-4" />
                </button>
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400"
                  data-testid="cinema-stats-close"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Body */}
          <div className="p-4 space-y-4">
            {loading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
              </div>
            )}

            {error && !loading && (
              <div className="rounded-xl bg-rose-950/40 ring-1 ring-rose-700/40 p-3 text-xs text-rose-300">
                {error}
              </div>
            )}

            {stats && !loading && (
              <>
                {/* TOP STATS — incassi + spettatori + giorni */}
                <div className="grid grid-cols-2 gap-2">
                  <StatCard
                    icon={<Coins className="w-3.5 h-3.5" />}
                    label="Incassi totali"
                    value={fmtMoney(stats.summary.total_revenue)}
                    accent="emerald"
                    testid="stat-total-revenue"
                  />
                  <StatCard
                    icon={<Users className="w-3.5 h-3.5" />}
                    label="Spettatori totali"
                    value={fmtNum(stats.summary.total_spectators)}
                    accent="cyan"
                    testid="stat-total-spectators"
                  />
                  <StatCard
                    icon={<Calendar className="w-3.5 h-3.5" />}
                    label="Giorni in sala"
                    value={stats.summary.days_in_theater}
                    sub={`/ ${stats.summary.theater_days} totali`}
                    accent="amber"
                    testid="stat-days-in-theater"
                  />
                  <StatCard
                    icon={<Clock className="w-3.5 h-3.5" />}
                    label="Giorni rimasti"
                    value={stats.summary.days_remaining}
                    sub={stats.summary.extension_count > 0 ? `+${stats.summary.extension_count}× estesa` : null}
                    accent="violet"
                    testid="stat-days-remaining"
                  />
                </div>

                {/* MICRO STATS row */}
                <div className="grid grid-cols-3 gap-2">
                  <MiniStat label="Cinema" value={stats.summary.current_cinemas} icon={<Building2 className="w-3 h-3" />} />
                  <MiniStat label="Biglietto" value={fmtMoney(stats.summary.avg_ticket_price)} icon={<Coins className="w-3 h-3" />} />
                  <MiniStat
                    label="Occupazione"
                    value={stats.summary.avg_occupancy_pct != null ? `${stats.summary.avg_occupancy_pct}%` : '—'}
                    icon={<TrendingUp className="w-3 h-3" />}
                  />
                </div>

                {/* PERFORMANCE MESSAGE */}
                <PerformanceMessage
                  performance={stats.performance}
                  contentId={stats.content.id}
                  recentHoldRatio={stats.recent_hold_ratio}
                />

                {/* GRAFICO AFFLUENZE */}
                <Section title="📊 Andamento giornaliero">
                  {/* Toggle modalità chart */}
                  <div className="flex items-center justify-end gap-1 mb-1">
                    <button
                      onClick={() => {
                        setChartMode('live');
                        try { localStorage.setItem('cinema_chart_mode', 'live'); } catch { /* noop */ }
                      }}
                      className={`text-[9px] font-bold px-2 py-1 rounded-full transition ${
                        chartMode === 'live'
                          ? 'bg-cyan-500/30 text-cyan-200 ring-1 ring-cyan-500/50'
                          : 'text-zinc-500 hover:text-zinc-300'
                      }`}
                      data-testid="chart-mode-live"
                    >
                      Live (passati + oggi)
                    </button>
                    <button
                      onClick={() => {
                        setChartMode('full');
                        try { localStorage.setItem('cinema_chart_mode', 'full'); } catch { /* noop */ }
                      }}
                      className={`text-[9px] font-bold px-2 py-1 rounded-full transition ${
                        chartMode === 'full'
                          ? 'bg-cyan-500/30 text-cyan-200 ring-1 ring-cyan-500/50'
                          : 'text-zinc-500 hover:text-zinc-300'
                      }`}
                      data-testid="chart-mode-full"
                    >
                      Tutta la programmazione
                    </button>
                  </div>
                  {/* LaPrima banner sopra il chart */}
                  {stats.laprima && (
                    <div className="mb-2">
                      <LaPrimaBanner laprima={stats.laprima} />
                    </div>
                  )}
                  <AttendanceChart
                    daily={stats.daily_breakdown || []}
                    forecast={stats.forecast || []}
                    totalDays={stats.summary.theater_days}
                    mode={chartMode}
                    height={200}
                  />
                </Section>

                {/* BADGES */}
                {stats.badges && stats.badges.length > 0 && (
                  <Section title="🏆 Riconoscimenti">
                    <div className="flex flex-wrap gap-1.5">
                      {stats.badges.map((b, i) => (
                        <span
                          key={b.key + i}
                          className="text-[10px] font-bold px-2 py-1 rounded-full bg-amber-500/20 ring-1 ring-amber-500/40 text-amber-200"
                          data-testid={`cinema-badge-${b.key}`}
                        >
                          {b.label}
                        </span>
                      ))}
                    </div>
                  </Section>
                )}

                {/* TOP 3 CITTA */}
                <Section title="🏙 Top 3 città" subtitle="dove il film sta funzionando meglio">
                  <TopCitiesPanel cities={stats.top_cities || []} />
                </Section>

                {/* COMPARISON */}
                {stats.comparison && (
                  <Section title="📈 Confronto con i tuoi film">
                    <div className="rounded-xl bg-zinc-900/60 ring-1 ring-zinc-800 p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-[10px] text-zinc-500 uppercase tracking-wider">vs media ultimi {stats.comparison.compared_films_count} film</div>
                          <div className="text-xs text-zinc-300 mt-0.5">
                            Media: <strong className="text-zinc-100">{fmtMoney(stats.comparison.avg_player_revenue)}</strong>
                          </div>
                        </div>
                        <div className={`text-2xl font-black ${stats.comparison.delta_pct >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                          {stats.comparison.delta_pct >= 0 ? '+' : ''}{stats.comparison.delta_pct}%
                        </div>
                      </div>
                    </div>
                  </Section>
                )}

                {/* AZIONI PROPRIETARIO */}
                <Section title="🎬 Azioni" subtitle="solo proprietario">
                  <CinemaActions
                    stats={stats}
                    isOwner={stats.content.is_owner}
                    onActionDone={handleActionDone}
                  />
                </Section>

                <div className="text-[9px] text-zinc-600 text-center italic pt-2">
                  Aggiornato {new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })} · auto-refresh ogni 5 min
                </div>
              </>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// ── Sub-components ──────────────────────────────────────────────────────

const accentMap = {
  emerald: { bg: 'from-emerald-900/40 to-zinc-900/30', ring: 'ring-emerald-700/30', text: 'text-emerald-300', icon: 'text-emerald-400' },
  cyan: { bg: 'from-cyan-900/40 to-zinc-900/30', ring: 'ring-cyan-700/30', text: 'text-cyan-300', icon: 'text-cyan-400' },
  amber: { bg: 'from-amber-900/40 to-zinc-900/30', ring: 'ring-amber-700/30', text: 'text-amber-300', icon: 'text-amber-400' },
  violet: { bg: 'from-violet-900/40 to-zinc-900/30', ring: 'ring-violet-700/30', text: 'text-violet-300', icon: 'text-violet-400' },
};

const StatCard = ({ icon, label, value, sub, accent = 'cyan', testid }) => {
  const a = accentMap[accent] || accentMap.cyan;
  return (
    <div
      className={`rounded-xl bg-gradient-to-br ${a.bg} ring-1 ${a.ring} p-2.5`}
      data-testid={testid}
    >
      <div className={`flex items-center gap-1 text-[10px] uppercase tracking-wider ${a.icon}`}>
        {icon}
        <span>{label}</span>
      </div>
      <div className={`text-lg font-black mt-0.5 ${a.text} truncate`}>{value}</div>
      {sub && <div className="text-[9px] text-zinc-500 truncate">{sub}</div>}
    </div>
  );
};

const MiniStat = ({ label, value, icon }) => (
  <div className="rounded-lg bg-zinc-900/40 ring-1 ring-zinc-800/60 p-2 text-center">
    <div className="text-[9px] text-zinc-500 flex items-center justify-center gap-0.5">{icon} {label}</div>
    <div className="text-xs font-bold text-zinc-200 mt-0.5">{value}</div>
  </div>
);

const Section = ({ title, subtitle, children }) => (
  <div className="space-y-1.5">
    <div className="flex items-baseline gap-2">
      <h3 className="text-[11px] font-bold uppercase tracking-wider text-zinc-300">{title}</h3>
      {subtitle && <span className="text-[9px] text-zinc-600 italic">— {subtitle}</span>}
    </div>
    {children}
  </div>
);

export default CinemaStatsModal;
