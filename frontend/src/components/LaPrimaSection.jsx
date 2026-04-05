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

  return (
    <div data-testid="la-prima-section">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-red-400" />
          <span className="text-red-400">LA PRIMA</span>
          <Badge className="bg-red-500/20 text-red-300 text-[9px] h-4 animate-pulse">LIVE</Badge>
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
        {events.map((ev) => (
          <div
            key={ev.film_id}
            className="flex-shrink-0 w-[140px] rounded-lg bg-[#0E0E10] border border-red-500/10 hover:border-red-500/30 transition-all cursor-pointer overflow-hidden"
            onClick={() => setSelectedFilmId(ev.film_id)}
            data-testid={`la-prima-event-${ev.film_id}`}
          >
            {/* Poster */}
            <div className="relative w-full h-[80px]">
              {posterSrc(ev.poster_url) ? (
                <img
                  src={posterSrc(ev.poster_url)}
                  alt={ev.title}
                  className="w-full h-full object-cover"
                  loading="lazy"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              ) : (
                <div className="w-full h-full bg-red-500/10 flex items-center justify-center">
                  <Film className="w-6 h-6 text-red-400/30" />
                </div>
              )}
              {/* LIVE badge */}
              <div className="absolute top-1 left-1 flex items-center gap-0.5 bg-red-600/90 rounded px-1 py-0.5">
                <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                <span className="text-[7px] font-bold text-white">LIVE</span>
              </div>
              {/* Gradient overlay */}
              <div className="absolute inset-x-0 bottom-0 h-6 bg-gradient-to-t from-[#0E0E10] to-transparent" />
            </div>

            {/* Info compact */}
            <div className="px-2 pb-2 pt-0.5">
              <h4 className="text-[11px] font-semibold truncate leading-tight">{ev.title}</h4>
              <div className="flex items-center gap-1 mt-0.5">
                <MapPin className="w-2.5 h-2.5 text-amber-400 flex-shrink-0" />
                <span className="text-[8px] text-amber-400 truncate">{ev.city}</span>
                {ev.time_remaining && (
                  <>
                    <Clock className="w-2.5 h-2.5 text-gray-500 flex-shrink-0 ml-0.5" />
                    <span className="text-[8px] text-gray-500 truncate">{ev.time_remaining}</span>
                  </>
                )}
              </div>
              {/* Stats */}
              <div className="flex items-center gap-1.5 mt-1">
                <div className="flex items-center gap-0.5" data-testid={`spectators-current-${ev.film_id}`}>
                  <Eye className="w-2.5 h-2.5 text-cyan-400" />
                  <span className="text-[9px] font-bold text-cyan-400">{formatNumber(ev.spectators_current)}</span>
                </div>
                <div className="flex items-center gap-0.5" data-testid={`spectators-total-${ev.film_id}`}>
                  <Users className="w-2.5 h-2.5 text-purple-400" />
                  <span className="text-[9px] font-bold text-purple-400">{formatNumber(ev.spectators_total)}</span>
                </div>
                <div className="flex items-center gap-0.5" data-testid={`hype-live-${ev.film_id}`}>
                  <Flame className="w-2.5 h-2.5 text-orange-400" />
                  <span className="text-[9px] font-bold text-orange-400">{ev.hype_live}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
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
