import React, { useEffect, useState, useContext } from 'react';
import { Trophy, Play, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};
const avatarSrc = posterSrc;

const TIER_COLORS = {
  base: 'from-sky-600 to-blue-500',
  cinematic: 'from-purple-600 to-fuchsia-500',
  pro: 'from-amber-500 to-orange-500',
};

const TIER_LABELS = { base: 'Base', cinematic: 'Cinematico', pro: 'PRO' };

/**
 * BestHighlightsLeaderboard — Top 10 trailer highlights (post-release).
 * Mobile-first horizontal scroll row, similar to LaPrimaSection.
 */
export default function BestHighlightsLeaderboard({ limit = 10, compact = true }) {
  const { api } = useContext(AuthContext);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!api) return;
    setLoading(true);
    api.get('/trailers/leaderboard/highlights', { params: { limit } })
      .then(r => setItems(r.data.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [api, limit]);

  if (loading) {
    return (
      <div className="mb-3">
        <h3 className="font-['Bebas_Neue'] text-lg flex items-center gap-2 mb-2">
          <Trophy className="w-4 h-4 text-amber-400" />
          <span className="text-amber-400">BEST HIGHLIGHTS</span>
        </h3>
        <div className="h-24 rounded-lg bg-white/[0.02] animate-pulse" />
      </div>
    );
  }

  if (items.length === 0) {
    return null; // Hide section if no highlights trailers exist yet
  }

  return (
    <div data-testid="best-highlights-section" className="mb-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
          <Trophy className="w-4 h-4 text-amber-400" />
          <span className="text-amber-400">BEST HIGHLIGHTS</span>
          <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-bold tracking-wider">POST-LANCIO</span>
        </h3>
        <span className="text-[10px] text-gray-500">Trailer più visti</span>
      </div>

      <div className="flex gap-2.5 overflow-x-auto pb-1.5 scrollbar-hide"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}
        data-testid="best-highlights-scroll-row">
        {items.map((it) => {
          const tierClr = TIER_COLORS[it.tier] || TIER_COLORS.base;
          const medal = it.rank === 1 ? '🥇' : it.rank === 2 ? '🥈' : it.rank === 3 ? '🥉' : null;
          return (
            <div key={it.content_id}
              className="flex-shrink-0 w-[110px] rounded-lg bg-[#0E0E10] border border-amber-500/20 hover:border-amber-500/40 transition-all cursor-pointer overflow-hidden"
              style={{ boxShadow: '0 0 10px rgba(212,175,55,0.08)' }}
              onClick={() => navigate(`/films/${it.content_id}`)}
              data-testid={`best-highlight-${it.content_id}`}>
              <div className="relative aspect-[2/3] overflow-hidden">
                {posterSrc(it.poster_url) ? (
                  <img src={posterSrc(it.poster_url)} alt={it.title}
                    className="w-full h-full object-cover transition-transform active:scale-105"
                    loading="lazy"
                    onError={(e) => { e.target.style.display = 'none'; }} />
                ) : (
                  <div className="w-full h-full bg-gradient-to-b from-amber-500/10 to-black flex items-center justify-center">
                    <Trophy className="w-8 h-8 text-amber-400/30" />
                  </div>
                )}
                {/* Rank badge */}
                <div className="absolute top-1 left-1 flex items-center gap-0.5 bg-black/80 rounded px-1 py-0.5">
                  {medal ? (
                    <span className="text-[10px] leading-none">{medal}</span>
                  ) : (
                    <span className="text-[8px] font-bold text-amber-400 tracking-wider">#{it.rank}</span>
                  )}
                </div>
                {/* Tier chip */}
                <div className={`absolute top-1 right-1 bg-gradient-to-r ${tierClr} rounded px-1 py-0.5`}>
                  <span className="text-[7px] font-black text-white tracking-wider">{TIER_LABELS[it.tier]}</span>
                </div>
                {/* Play overlay */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity bg-black/40">
                  <Play className="w-8 h-8 text-white fill-white drop-shadow-xl" />
                </div>
                {/* Bottom gradient with views */}
                <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/95 via-black/60 to-transparent pt-4 pb-1 px-1.5">
                  <div className="flex items-center gap-1">
                    <Play className="w-2 h-2 text-white fill-white" />
                    <span className="text-[8px] font-bold text-white">{(it.views_count || 0).toLocaleString()}</span>
                  </div>
                </div>
              </div>
              {/* Info */}
              <div className="px-1.5 pb-1.5 pt-1">
                <h4 className="text-[9px] font-semibold truncate leading-tight">{it.title}</h4>
                <div className="flex items-center gap-1 mt-0.5">
                  <div className="w-3 h-3 rounded-full overflow-hidden bg-gray-800 flex-shrink-0">
                    {it.owner_avatar_url ? (
                      <img src={avatarSrc(it.owner_avatar_url)} alt="" className="w-full h-full object-cover"
                        onError={(e) => { e.target.style.display = 'none'; }} />
                    ) : (
                      <User className="w-2 h-2 text-gray-600" />
                    )}
                  </div>
                  <span className="text-[7px] text-gray-400 truncate">{it.owner_nickname}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
