import { useState, useEffect, useContext, useCallback } from 'react';
import { AuthContext, LanguageContext } from '../contexts';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Film, Tv, Sparkles, Play, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import VelionCinematicEvent from '../components/VelionCinematicEvent';

const RARITY_STYLES = {
  common: { bg: 'bg-gray-800/60', border: 'border-gray-600/30', text: 'text-gray-400', label: 'COMUNE', dot: 'bg-gray-500' },
  rare: { bg: 'bg-blue-950/40', border: 'border-blue-500/30', text: 'text-blue-400', label: 'RARO', dot: 'bg-blue-500' },
  epic: { bg: 'bg-purple-950/40', border: 'border-purple-500/40', text: 'text-purple-400', label: 'EPICO', dot: 'bg-purple-500' },
  legendary: { bg: 'bg-yellow-950/30', border: 'border-yellow-500/40', text: 'text-yellow-400', label: 'LEGGENDARIO', dot: 'bg-yellow-500' },
};

const TYPE_BADGE = {
  film: { icon: Film, label: 'FILM', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
  series: { icon: Tv, label: 'SERIE', color: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30' },
  anime: { icon: Sparkles, label: 'ANIME', color: 'bg-pink-500/20 text-pink-400 border-pink-500/30' },
};

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const now = new Date();
  const d = new Date(dateStr);
  const mins = Math.floor((now - d) / 60000);
  if (mins < 1) return 'ora';
  if (mins < 60) return `${mins}m fa`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h fa`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return 'ieri';
  return `${days}g fa`;
}

export default function EventHistoryPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [replayEvent, setReplayEvent] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    api.get('/events/history?limit=50')
      .then(r => setEvents(r.data?.events || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [api]);

  const handleReplay = useCallback((ev) => {
    const cinematicEv = {
      text: ev.description,
      tier: ev.rarity,
      event_type: ev.event_type,
      revenue_mod: ev.effects?.revenue_mod || 0,
      hype_mod: ev.effects?.hype_mod || 0,
      fame_mod: ev.effects?.fame_mod || 0,
      film_title: ev.title,
      actor_name: ev.actor_name || '',
      project_type: ev.project_type,
      is_replay: true,
    };
    setReplayEvent(cinematicEv);
  }, []);

  const filtered = filter === 'all' ? events : events.filter(e => e.rarity === filter);

  return (
    <div className="min-h-screen bg-[#0a0a0a] pb-24" data-testid="event-history-page">
      {/* Header */}
      <div className="sticky top-0 z-40 bg-[#0a0a0a]/95 backdrop-blur-sm border-b border-white/5 px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-white" data-testid="event-history-back">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-bold text-white">Cronologia Eventi</h1>
          <span className="text-xs text-gray-500 ml-auto">{events.length} eventi</span>
        </div>

        {/* Filter pills */}
        <div className="flex gap-2 mt-2 overflow-x-auto no-scrollbar">
          {['all', 'legendary', 'epic', 'rare', 'common'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-full text-[10px] font-mono uppercase whitespace-nowrap border transition-colors ${
                filter === f
                  ? 'bg-white/10 border-white/20 text-white'
                  : 'bg-transparent border-white/5 text-gray-500 hover:text-gray-300'
              }`}
              data-testid={`filter-${f}`}
            >
              {f === 'all' ? 'Tutti' : RARITY_STYLES[f]?.label || f}
            </button>
          ))}
        </div>
      </div>

      {/* Events List */}
      <div className="px-3 py-3 space-y-2">
        {loading ? (
          <div className="text-center py-12 text-gray-500 text-sm">Caricamento...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12 text-gray-600 text-sm">
            Nessun evento {filter !== 'all' ? RARITY_STYLES[filter]?.label?.toLowerCase() : ''} trovato
          </div>
        ) : (
          filtered.map((ev, i) => {
            const style = RARITY_STYLES[ev.rarity] || RARITY_STYLES.common;
            const typeBadge = TYPE_BADGE[ev.project_type] || TYPE_BADGE.film;
            const TypeIcon = typeBadge.icon;
            const canReplay = ev.rarity === 'epic' || ev.rarity === 'legendary';

            return (
              <motion.div
                key={ev.created_at + '_' + i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                className={`rounded-xl border ${style.border} ${style.bg} p-3 relative overflow-hidden`}
                data-testid={`event-card-${i}`}
              >
                {/* Type badge - top right */}
                <div className={`absolute top-2 right-2 flex items-center gap-1 px-2 py-0.5 rounded-full border text-[9px] font-mono ${typeBadge.color}`}>
                  <TypeIcon className="w-3 h-3" />
                  {typeBadge.label}
                </div>

                {/* Rarity dot + label */}
                <div className="flex items-center gap-2 mb-1.5">
                  <div className={`w-2 h-2 rounded-full ${style.dot}`} />
                  <span className={`text-[9px] font-mono tracking-widest ${style.text}`}>{style.label}</span>
                </div>

                {/* Title */}
                <p className="text-xs font-semibold text-gray-200 pr-16 leading-relaxed">{ev.title}</p>

                {/* Description */}
                <p className="text-[11px] text-gray-400 mt-1 leading-relaxed">{ev.description}</p>

                {/* Effects */}
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  {ev.effects?.revenue_mod !== 0 && ev.effects?.revenue_mod && (
                    <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded-full ${ev.effects.revenue_mod > 0 ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400'}`}>
                      {ev.effects.revenue_mod > 0 ? '+' : ''}{Math.round(ev.effects.revenue_mod * 100)}% incassi
                    </span>
                  )}
                  {ev.effects?.hype_mod !== 0 && ev.effects?.hype_mod && (
                    <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded-full ${ev.effects.hype_mod > 0 ? 'bg-cyan-500/15 text-cyan-400' : 'bg-red-500/15 text-red-400'}`}>
                      {ev.effects.hype_mod > 0 ? '+' : ''}{ev.effects.hype_mod} hype
                    </span>
                  )}
                  {ev.effects?.fame_mod !== 0 && ev.effects?.fame_mod && (
                    <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded-full ${ev.effects.fame_mod > 0 ? 'bg-yellow-500/15 text-yellow-400' : 'bg-red-500/15 text-red-400'}`}>
                      {ev.effects.fame_mod > 0 ? '+' : ''}{ev.effects.fame_mod} fama
                    </span>
                  )}
                </div>

                {/* Footer: timestamp + replay */}
                <div className="flex items-center justify-between mt-2">
                  <span className="text-[9px] text-gray-600 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {timeAgo(ev.created_at)}
                  </span>
                  {canReplay && (
                    <button
                      onClick={() => handleReplay(ev)}
                      className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-mono border ${style.border} ${style.text} hover:bg-white/5 transition-colors`}
                      data-testid={`replay-btn-${i}`}
                    >
                      <Play className="w-3 h-3" />
                      Rivedi
                    </button>
                  )}
                </div>
              </motion.div>
            );
          })
        )}
      </div>

      {/* Cinematic Replay (visual only) */}
      <AnimatePresence>
        {replayEvent && (
          <VelionCinematicEvent
            events={[replayEvent]}
            onAllDone={() => setReplayEvent(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
