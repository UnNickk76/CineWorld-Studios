// CineWorld Studio's — UnifiedRankingPanel
// Pannello classifica unificata di tutti i contenuti di tutti i player.
// Supporta filtri tipo (all/film/series/anime/animation/lampo/saga_chapter),
// sort (revenue/spectators/cwsv/hold/hype) e periodo (daily/weekly/monthly/alltime).
// Usato in CineBoard come tab "Globale".

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import {
  Loader2, Trophy, Film, Tv, Sparkles, Star, Coins, Users,
  ChevronRight, BookOpen, Zap,
} from 'lucide-react';
import { CinemaStatsModal } from '../cinema/CinemaStatsModal';

const API = process.env.REACT_APP_BACKEND_URL;

const TYPE_FILTERS = [
  { key: 'all', label: 'Tutti', icon: Trophy },
  { key: 'film', label: 'Film', icon: Film },
  { key: 'series', label: 'Serie', icon: Tv },
  { key: 'anime', label: 'Anime', icon: Sparkles },
  { key: 'animation', label: 'Animaz.', icon: Sparkles },
  { key: 'lampo', label: 'LAMPO', icon: Zap },
  { key: 'saga_chapter', label: 'Saghe', icon: BookOpen },
];

const SORT_OPTIONS = [
  { key: 'revenue', label: 'Incassi', icon: Coins },
  { key: 'spectators', label: 'Spett.', icon: Users },
  { key: 'cwsv', label: 'CWSv', icon: Star },
  { key: 'hold_ratio', label: 'Hold', icon: ChevronRight },
];

const PERIOD_OPTIONS = [
  { key: 'daily', label: 'Oggi' },
  { key: 'weekly', label: 'Settimana' },
  { key: 'monthly', label: 'Mese' },
  { key: 'alltime', label: 'Sempre' },
];

const fmtMoney = (v) => {
  const n = Number(v || 0);
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n}`;
};
const fmtNum = (v) => Number(v || 0).toLocaleString('it-IT');

export const UnifiedRankingPanel = () => {
  const [contentType, setContentType] = useState('all');
  const [sort, setSort] = useState('revenue');
  const [period, setPeriod] = useState('weekly');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  const fetchRanking = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.get(
        `${API}/api/cineboard-unified/global`,
        {
          params: { content_type: contentType, sort, period, limit: 50 },
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      setData(res.data.ranking || []);
    } catch (e) {
      // toast omitted
    } finally {
      setLoading(false);
    }
  }, [contentType, sort, period]);

  useEffect(() => { fetchRanking(); }, [fetchRanking]);

  return (
    <div className="space-y-3" data-testid="unified-ranking-panel">
      {/* Filters */}
      <div className="space-y-2">
        {/* Type filter — horizontal scroll su mobile */}
        <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-hide">
          {TYPE_FILTERS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setContentType(key)}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-full text-[10px] font-bold whitespace-nowrap transition ${
                contentType === key
                  ? 'bg-cyan-500/30 text-cyan-200 ring-1 ring-cyan-500/50'
                  : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200'
              }`}
              data-testid={`unified-type-${key}`}
            >
              <Icon className="w-3 h-3" />
              {label}
            </button>
          ))}
        </div>

        {/* Sort + Period row */}
        <div className="grid grid-cols-2 gap-2">
          <div className="flex gap-1 overflow-x-auto scrollbar-hide">
            {SORT_OPTIONS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setSort(key)}
                className={`flex-1 px-2 py-1 rounded-md text-[10px] font-bold whitespace-nowrap ${
                  sort === key
                    ? 'bg-emerald-500/30 text-emerald-200 ring-1 ring-emerald-500/50'
                    : 'bg-zinc-900 text-zinc-400'
                }`}
                data-testid={`unified-sort-${key}`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            {PERIOD_OPTIONS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setPeriod(key)}
                className={`flex-1 px-1 py-1 rounded-md text-[10px] font-bold ${
                  period === key
                    ? 'bg-amber-500/30 text-amber-200 ring-1 ring-amber-500/50'
                    : 'bg-zinc-900 text-zinc-400'
                }`}
                data-testid={`unified-period-${key}`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Ranking list */}
      {loading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
        </div>
      ) : data.length === 0 ? (
        <div className="text-center text-zinc-500 text-xs py-10">Nessun risultato per i filtri scelti</div>
      ) : (
        <div className="space-y-1.5">
          {data.map((it, i) => (
            <RankRow key={it.id + i} item={it} rank={i + 1} sort={sort} onClick={() => setSelectedId(it.id)} />
          ))}
        </div>
      )}

      {/* Detail modal */}
      {selectedId && (
        <CinemaStatsModal contentId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
};

const RankRow = ({ item, rank, sort, onClick }) => {
  const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`;
  const bg = rank <= 3 ? 'bg-gradient-to-r from-amber-950/40 via-zinc-900 to-zinc-900 ring-amber-700/30' : 'bg-zinc-900/60 ring-zinc-800';

  const valueByCol = {
    revenue: { label: fmtMoney(item._revenue), accent: 'text-emerald-300' },
    spectators: { label: fmtNum(item._spectators), accent: 'text-cyan-300' },
    cwsv: { label: `${item._cwsv.toFixed(1)}/10`, accent: 'text-amber-300' },
    hold_ratio: { label: `${Math.round((item._hold || 0) * 100)}%`, accent: 'text-violet-300' },
    hype: { label: `${item._hype.toFixed(1)}`, accent: 'text-rose-300' },
  };
  const { label: mainValue, accent } = valueByCol[sort] || valueByCol.revenue;

  const kindBadge = {
    lampo: { icon: '⚡', text: 'LAMPO', bg: 'bg-yellow-500/20 text-yellow-300' },
    saga_chapter: { icon: '📚', text: `Cap.${item.saga_chapter_number || ''}`, bg: 'bg-amber-500/20 text-amber-300' },
    animation: { icon: '🎨', text: 'Animaz.', bg: 'bg-pink-500/20 text-pink-300' },
    anime: { icon: '🌸', text: 'Anime', bg: 'bg-rose-500/20 text-rose-300' },
    series: { icon: '📺', text: 'Serie', bg: 'bg-violet-500/20 text-violet-300' },
    tv_series: { icon: '📺', text: 'Serie', bg: 'bg-violet-500/20 text-violet-300' },
    film: { icon: '🎬', text: 'Film', bg: 'bg-cyan-500/20 text-cyan-300' },
  }[item._kind] || { icon: '🎬', text: 'Film', bg: 'bg-zinc-800 text-zinc-300' };

  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`w-full flex items-center gap-2 rounded-xl ring-1 p-2 ${bg} text-left`}
      data-testid={`unified-rank-${rank}`}
    >
      <div className="text-base font-black w-8 text-center text-zinc-300 flex-shrink-0">
        {medal}
      </div>
      {item.poster_url && (
        <img src={item.poster_url} alt="" className="w-9 h-12 rounded object-cover flex-shrink-0 ring-1 ring-zinc-700" loading="lazy" />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1 mb-0.5">
          <span className={`text-[8px] font-bold px-1 py-0.5 rounded ${kindBadge.bg}`}>
            {kindBadge.icon} {kindBadge.text}
          </span>
          {item._cwsv >= 8 && <span className="text-[8px] text-amber-400">⭐</span>}
        </div>
        <div className="text-xs font-bold text-zinc-100 truncate">{item.title}</div>
        <div className="text-[9px] text-zinc-500 truncate">
          🎭 {item.owner_studio || item.owner_nickname}
        </div>
      </div>
      <div className={`text-sm font-black ${accent} flex-shrink-0`}>
        {mainValue}
      </div>
    </motion.button>
  );
};

export default UnifiedRankingPanel;
