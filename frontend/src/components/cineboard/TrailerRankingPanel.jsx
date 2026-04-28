// CineWorld Studio's — TrailerRankingPanel
// Pannello classifica trailer più visualizzati / piaciuti di tutti i player.

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Loader2, Eye, Heart, Play, Sparkles } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const PERIOD_OPTIONS = [
  { key: 'daily', label: 'Oggi' },
  { key: 'weekly', label: 'Settimana' },
  { key: 'monthly', label: 'Mese' },
  { key: 'alltime', label: 'Sempre' },
];

const fmtNum = (v) => {
  const n = Number(v || 0);
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return String(n);
};

export const TrailerRankingPanel = () => {
  const [period, setPeriod] = useState('weekly');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [playingTrailer, setPlayingTrailer] = useState(null);

  const fetchRanking = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.get(`${API}/api/cineboard-unified/trailers`, {
        params: { period, limit: 30 },
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(res.data.ranking || []);
    } catch { /* silent */ } finally { setLoading(false); }
  }, [period]);

  useEffect(() => { fetchRanking(); }, [fetchRanking]);

  return (
    <div className="space-y-3" data-testid="trailer-ranking-panel">
      <div className="flex gap-1.5">
        {PERIOD_OPTIONS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setPeriod(key)}
            className={`flex-1 px-2 py-1.5 rounded-md text-[10px] font-bold ${
              period === key
                ? 'bg-pink-500/30 text-pink-200 ring-1 ring-pink-500/50'
                : 'bg-zinc-900 text-zinc-400'
            }`}
            data-testid={`trailer-period-${key}`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="w-5 h-5 text-pink-400 animate-spin" />
        </div>
      ) : data.length === 0 ? (
        <div className="text-center text-zinc-500 text-xs py-10">Nessun trailer in classifica</div>
      ) : (
        <div className="space-y-1.5">
          {data.map((it, i) => (
            <TrailerRow key={it.id + i} item={it} rank={i + 1} onPlay={() => setPlayingTrailer(it)} />
          ))}
        </div>
      )}

      {/* Trailer modal */}
      {playingTrailer && (
        <div
          onClick={() => setPlayingTrailer(null)}
          className="fixed inset-0 z-[10000] bg-black/95 flex items-center justify-center p-3"
          data-testid="trailer-player-modal"
        >
          <div onClick={(e) => e.stopPropagation()} className="w-full max-w-md">
            <div className="text-xs text-zinc-300 mb-2 text-center">{playingTrailer.title}</div>
            <video
              src={playingTrailer.trailer_url}
              controls
              autoPlay
              className="w-full rounded-xl"
            />
            <button
              onClick={() => setPlayingTrailer(null)}
              className="mt-3 w-full py-2 rounded-lg bg-zinc-800 text-zinc-300 text-xs font-bold"
            >
              Chiudi
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const TrailerRow = ({ item, rank, onPlay }) => {
  const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`;
  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      onClick={onPlay}
      className={`w-full flex items-center gap-2 rounded-xl ring-1 p-2 text-left transition ${
        rank <= 3
          ? 'bg-gradient-to-r from-pink-950/40 via-zinc-900 to-zinc-900 ring-pink-700/30'
          : 'bg-zinc-900/60 ring-zinc-800 hover:ring-pink-700/40'
      }`}
      data-testid={`trailer-rank-${rank}`}
    >
      <div className="text-base font-black w-8 text-center text-zinc-300">{medal}</div>
      {item.poster_url ? (
        <div className="relative w-10 h-13 flex-shrink-0">
          <img src={item.poster_url} alt="" className="w-10 h-13 rounded object-cover ring-1 ring-zinc-700" loading="lazy" />
          <div className="absolute inset-0 flex items-center justify-center bg-black/40 rounded">
            <Play className="w-3.5 h-3.5 text-white" fill="white" />
          </div>
        </div>
      ) : (
        <div className="w-10 h-13 bg-zinc-800 rounded flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-zinc-500" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="text-xs font-bold text-zinc-100 truncate">{item.title}</div>
        <div className="text-[9px] text-zinc-500 truncate">🎭 {item.owner_studio}</div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] text-cyan-300 flex items-center gap-0.5">
            <Eye className="w-2.5 h-2.5" /> {fmtNum(item.trailer_views_display)}
          </span>
          <span className="text-[10px] text-rose-300 flex items-center gap-0.5">
            <Heart className="w-2.5 h-2.5" /> {fmtNum(item.trailer_likes_display)}
          </span>
        </div>
      </div>
    </motion.button>
  );
};

export default TrailerRankingPanel;
