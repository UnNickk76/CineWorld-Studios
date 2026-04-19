import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Users, Flame, MapPin, Clock, ChevronRight, Eye, Sparkles, Loader2, Film } from 'lucide-react';
import { LaPrimaPopup } from './LaPrimaPopup';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

function formatNumber(n) {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toLocaleString();
}

export function LaPrimaSection({ compact = false }) {
  const { api } = useContext(AuthContext);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilmId, setSelectedFilmId] = useState(null);
  const navigate = useNavigate();

  const fetchEvents = useCallback(async () => {
    try {
      const res = await api.get('/la-prima/active');
      setEvents(res.data.events || []);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 60000);
    return () => clearInterval(interval);
  }, [fetchEvents]);

  if (loading) {
    return (
      <div className="bg-gradient-to-r from-red-500/10 to-amber-500/5 border border-red-500/20 rounded-lg animate-pulse p-3 flex items-center justify-center gap-2" data-testid="la-prima-loading">
        <Loader2 className="w-4 h-4 text-red-400 animate-spin" />
        <span className="text-xs text-gray-400">Caricamento La Prima...</span>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div data-testid="la-prima-section">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-red-400" />
            <span className="text-red-400">LA PRIMA</span>
          </h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/social?view=la-prima')}
            className="h-6 text-[10px] text-red-400 hover:text-red-300 px-2"
            data-testid="la-prima-see-all-btn"
          >
            Classifiche <ChevronRight className="w-3 h-3 ml-0.5" />
          </Button>
        </div>
        <div className="bg-gradient-to-r from-red-500/5 to-amber-500/5 border border-white/5 rounded-lg p-4 text-center">
          <Film className="w-6 h-6 text-gray-600 mx-auto mb-1" />
          <p className="text-xs text-gray-500">Nessuna première in programma</p>
        </div>
      </div>
    );
  }

  const hasLive = events.some(e => !e.is_waiting);
  return (
    <div data-testid="la-prima-section">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-red-400" />
          <span className="text-red-400">LA PRIMA</span>
          {hasLive ? (
            <Badge className="bg-red-500/20 text-red-300 text-[9px] h-4 animate-pulse">LIVE</Badge>
          ) : (
            <Badge className="bg-cyan-500/20 text-cyan-300 text-[9px] h-4">IN ARRIVO</Badge>
          )}
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/social?view=la-prima')}
          className="h-6 text-[10px] text-red-400 hover:text-red-300 px-2"
          data-testid="la-prima-see-all-btn"
        >
          Classifiche <ChevronRight className="w-3 h-3 ml-0.5" />
        </Button>
      </div>

      {/* Horizontal scrollable row */}
      <div
        className="flex gap-2.5 overflow-x-auto pb-1.5 scrollbar-hide"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}
        data-testid="la-prima-scroll-row"
      >
        {events.map((ev) => {
          const isWaiting = !!ev.is_waiting;
          return (
          <div
            key={ev.film_id}
            className={`flex-shrink-0 w-[100px] rounded-lg bg-[#0E0E10] border transition-all cursor-pointer overflow-hidden ${
              isWaiting ? 'border-cyan-500/30 hover:border-cyan-500/50' : 'border-amber-500/20 hover:border-amber-500/40'
            }`}
            style={{ boxShadow: isWaiting ? '0 0 10px rgba(96,205,255,0.12)' : '0 0 12px rgba(212,175,55,0.12)' }}
            onClick={() => navigate(`/films/${ev.film_id}`)}
            data-testid={`la-prima-event-${ev.film_id}`}
          >
            {/* Poster 2:3 */}
            <div className="relative aspect-[2/3] overflow-hidden">
              {posterSrc(ev.poster_url) ? (
                <img
                  src={posterSrc(ev.poster_url)}
                  alt={ev.title}
                  className={`w-full h-full object-cover transition-transform active:scale-105 ${isWaiting ? 'opacity-55 grayscale-[30%]' : ''}`}
                  loading="lazy"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-b from-amber-500/10 to-black flex items-center justify-center">
                  <Film className="w-8 h-8 text-amber-400/30" />
                </div>
              )}
              {/* Dark overlay for waiting */}
              {isWaiting && (
                <div className="absolute inset-0 bg-gradient-to-b from-black/35 via-black/55 to-black/85" />
              )}
              {/* Status badge top-left */}
              {isWaiting ? (
                <div className="absolute top-1 left-1 flex items-center gap-0.5 bg-cyan-600/90 rounded px-1 py-0.5">
                  <span className="text-[7px] font-bold text-white tracking-wider">IN ARRIVO</span>
                </div>
              ) : (
                <div className="absolute top-1 left-1 flex items-center gap-0.5 bg-red-600/90 rounded px-1 py-0.5">
                  <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                  <span className="text-[7px] font-bold text-white">LIVE</span>
                </div>
              )}
              {/* Bottom label */}
              <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/95 via-black/70 to-transparent pt-4 pb-1 px-1.5">
                {isWaiting ? (
                  <>
                    <p className="text-[8px] font-bold text-cyan-300 truncate leading-tight">In arrivo a</p>
                    <p className="text-[9px] font-black text-cyan-200 truncate tracking-wide uppercase">{ev.city}</p>
                  </>
                ) : (
                  <span className="text-[7px] font-bold text-amber-400 tracking-wider">LA PRIMA</span>
                )}
              </div>
            </div>

            {/* Info */}
            <div className="px-1.5 pb-1.5 pt-1">
              <h4 className={`text-[9px] font-semibold truncate leading-tight ${isWaiting ? 'text-gray-300' : ''}`}>{ev.title}</h4>
              <div className="flex items-center gap-0.5 mt-0.5">
                <MapPin className={`w-2 h-2 flex-shrink-0 ${isWaiting ? 'text-cyan-400' : 'text-amber-400'}`} />
                <span className={`text-[7px] truncate ${isWaiting ? 'text-cyan-400' : 'text-amber-400'}`}>{ev.city}</span>
              </div>
              {isWaiting ? (
                <div className="mt-1 text-center">
                  <p className="text-[7px] text-cyan-400 font-bold tracking-wider">-{ev.countdown_to_start || '—'}</p>
                  <p className="text-[6px] text-gray-500 uppercase mt-0.5">al via</p>
                </div>
              ) : (
                <>
                  {/* Progress bar */}
                  <div className="mt-1 h-1 rounded-full bg-white/10 overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-amber-500 to-red-500 transition-all" style={{ width: `${Math.min(100, Math.max(5, (ev.spectators_total || 0) / Math.max(1, ev.target_spectators || 1000) * 100))}%` }} />
                  </div>
                  {/* Stats */}
                  <div className="flex items-center gap-1 mt-0.5">
                    <Eye className="w-2 h-2 text-cyan-400" />
                    <span className="text-[7px] font-bold text-cyan-400">{formatNumber(ev.spectators_current)}</span>
                    <Flame className="w-2 h-2 text-orange-400 ml-auto" />
                    <span className="text-[7px] font-bold text-orange-400">{ev.hype_live}</span>
                  </div>
                </>
              )}
            </div>
          </div>
          );
        })}
      </div>

      {/* La Prima Popup */}
      <LaPrimaPopup
        filmId={selectedFilmId}
        open={!!selectedFilmId}
        onClose={() => setSelectedFilmId(null)}
      />
    </div>
  );
}
