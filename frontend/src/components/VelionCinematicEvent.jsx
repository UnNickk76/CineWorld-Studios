import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Film, Tv, Sparkles } from 'lucide-react';
import MatrixOverlay from './MatrixOverlay';

const TIER_STYLES = {
  common: { border: 'border-gray-500/30', bg: 'bg-gray-900/95', glow: '', label: 'EVENTO', labelColor: 'text-gray-400' },
  rare: { border: 'border-blue-500/40', bg: 'bg-[#0a0a1a]/95', glow: 'shadow-[0_0_30px_rgba(59,130,246,0.15)]', label: 'RARO', labelColor: 'text-blue-400' },
  epic: { border: 'border-purple-500/50', bg: 'bg-[#0d0516]/95', glow: 'shadow-[0_0_40px_rgba(168,85,247,0.2)]', label: 'EPICO', labelColor: 'text-purple-400' },
  legendary: { border: 'border-yellow-500/60', bg: 'bg-[#1a1000]/95', glow: 'shadow-[0_0_60px_rgba(234,179,8,0.3)]', label: 'LEGGENDARIO', labelColor: 'text-yellow-400' },
};

const TYPE_BADGE_MAP = {
  film: { icon: Film, label: 'FILM', color: 'bg-red-500/25 text-red-400 border-red-500/40' },
  series: { icon: Tv, label: 'SERIE', color: 'bg-cyan-500/25 text-cyan-400 border-cyan-500/40' },
  anime: { icon: Sparkles, label: 'ANIME', color: 'bg-pink-500/25 text-pink-400 border-pink-500/40' },
};

// Minimum display time before tap-to-close is allowed
const SKIP_BLOCK_MS = 2500;

function EventCard({ event, onDone }) {
  const style = TIER_STYLES[event.tier] || TIER_STYLES.common;
  const isPositive = event.event_type === 'positive' || event.event_type === 'star_born';
  const canSkip = useRef(false);

  useEffect(() => {
    // Block skip for first 2.5 seconds
    const unlock = setTimeout(() => { canSkip.current = true; }, SKIP_BLOCK_MS);
    // Auto-close after generous time
    const autoClose = setTimeout(onDone, event.tier === 'legendary' ? 8000 : event.tier === 'epic' ? 6000 : 3500);
    return () => { clearTimeout(unlock); clearTimeout(autoClose); };
  }, [event.tier, onDone]);

  const handleTap = useCallback(() => {
    if (canSkip.current) onDone();
  }, [onDone]);

  return (
    <motion.div
      className="fixed inset-0 z-[500] flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      onClick={handleTap}
      data-testid="velion-cinematic-event"
    >
      <div className="absolute inset-0 bg-black/85" />

      <motion.div
        className={`relative z-10 max-w-sm w-full rounded-2xl border-2 ${style.border} ${style.bg} ${style.glow} backdrop-blur-xl overflow-hidden`}
        initial={{ scale: 0.6, y: 50, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        exit={{ scale: 0.85, opacity: 0 }}
        transition={{ delay: 0.8, type: 'spring', damping: 18, stiffness: 200 }}
      >
        {/* Type Badge: FILM / SERIE / ANIME */}
        {(() => {
          const tb = TYPE_BADGE_MAP[event.project_type];
          if (!tb) return null;
          const TIcon = tb.icon;
          return (
            <motion.div
              className={`absolute top-3 right-3 z-20 flex items-center gap-1 px-2 py-0.5 rounded-full border text-[9px] font-mono ${tb.color}`}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.4, duration: 0.3 }}
            >
              <TIcon className="w-3 h-3" />
              {tb.label}
            </motion.div>
          );
        })()}
        {/* Velion — fade in 600ms, starts after card appears */}
        <div className="flex justify-center pt-4 -mb-2">
          <motion.img
            src="/velion-tutorial.png"
            alt="Velion"
            className="w-20 h-24 object-contain drop-shadow-[0_0_20px_rgba(234,179,8,0.4)]"
            initial={{ scale: 0.3, opacity: 0 }}
            animate={{ scale: [0.3, 1.15, 1], opacity: 1 }}
            transition={{ delay: 1.0, duration: 0.6, type: 'spring', damping: 12 }}
          />
        </div>

        <div className="px-5 pb-5 pt-2 text-center">
          <motion.div
            className={`text-[10px] font-mono font-bold tracking-[0.3em] ${style.labelColor} mb-2`}
            initial={{ opacity: 0, letterSpacing: '0.6em' }}
            animate={{ opacity: 1, letterSpacing: '0.3em' }}
            transition={{ delay: 1.3, duration: 0.5 }}
          >
            {style.label}
          </motion.div>

          <motion.p
            className={`text-sm font-semibold leading-relaxed ${isPositive ? 'text-white' : 'text-red-200'}`}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.6, duration: 0.4 }}
          >
            {event.text}
          </motion.p>

          <motion.div
            className="flex items-center justify-center gap-2 mt-3 flex-wrap"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.0, duration: 0.4 }}
          >
            {event.revenue_mod !== 0 && (
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${event.revenue_mod > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                {event.revenue_mod > 0 ? '+' : ''}{Math.round(event.revenue_mod * 100)}% incassi
              </span>
            )}
            {event.hype_mod !== 0 && (
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${event.hype_mod > 0 ? 'bg-cyan-500/20 text-cyan-400' : 'bg-red-500/20 text-red-400'}`}>
                {event.hype_mod > 0 ? '+' : ''}{event.hype_mod} hype
              </span>
            )}
            {event.fame_mod !== 0 && (
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${event.fame_mod > 0 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                {event.fame_mod > 0 ? '+' : ''}{event.fame_mod} fama
              </span>
            )}
          </motion.div>

          <motion.p
            className="text-[9px] text-gray-600 mt-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.5 }}
          >
            tap per chiudere
          </motion.p>
        </div>
      </motion.div>
    </motion.div>
  );
}

// Gap between queued events (3 seconds)
const QUEUE_GAP_MS = 3000;

export default function VelionCinematicEvent({ events = [], onAllDone }) {
  const [queue, setQueue] = useState([]);
  const [current, setCurrent] = useState(null);
  const [phase, setPhase] = useState('idle');

  useEffect(() => {
    if (events.length > 0) {
      setQueue([...events]);
    }
  }, [events]);

  // Process queue
  useEffect(() => {
    if (phase !== 'idle' || queue.length === 0) return;
    const next = queue[0];
    setCurrent(next);
    setQueue(q => q.slice(1));

    if (next.tier === 'epic' || next.tier === 'legendary') {
      setPhase('fadeout');
    } else {
      setPhase('event');
    }
  }, [phase, queue]);

  // PHASE: fadeout (800ms) → blackpause (500ms) → matrix
  useEffect(() => {
    if (phase !== 'fadeout') return;
    const t = setTimeout(() => setPhase('blackpause'), 800);
    return () => clearTimeout(t);
  }, [phase]);

  useEffect(() => {
    if (phase !== 'blackpause') return;
    const t = setTimeout(() => setPhase('matrix'), 500);
    return () => clearTimeout(t);
  }, [phase]);

  const handleMatrixReveal = useCallback(() => {
    setPhase('event');
  }, []);

  const handleEventDone = useCallback(() => {
    setCurrent(null);
    if (queue.length === 0) {
      setPhase('idle');
      if (onAllDone) onAllDone();
    } else {
      // 3s gap before next event
      setPhase('gap');
    }
  }, [queue, onAllDone]);

  useEffect(() => {
    if (phase !== 'gap') return;
    const t = setTimeout(() => setPhase('idle'), QUEUE_GAP_MS);
    return () => clearTimeout(t);
  }, [phase]);

  if (!current && queue.length === 0) return null;

  return (
    <>
      {/* FADEOUT: blur + desaturation over 800ms */}
      <AnimatePresence>
        {phase === 'fadeout' && (
          <motion.div
            className="fixed inset-0 z-[390]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, ease: 'easeInOut' }}
          >
            <motion.div
              className="absolute inset-0"
              style={{ backdropFilter: 'blur(12px) saturate(0.1) brightness(0.3)' }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8 }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* BLACKPAUSE: full black 500ms */}
      <AnimatePresence>
        {(phase === 'blackpause' || phase === 'matrix' || phase === 'event') && (
          <motion.div
            className="fixed inset-0 z-[395] bg-black"
            initial={{ opacity: phase === 'blackpause' ? 0 : 1 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: phase === 'blackpause' ? 0.3 : 0.5 }}
          />
        )}
      </AnimatePresence>

      {/* MATRIX: min 2000ms epic, 3000ms legendary */}
      <AnimatePresence>
        {phase === 'matrix' && current && (
          <MatrixOverlay
            filmTitles={[current.film_title || current.movie_title || '']}
            actorNames={[current.actor_name || '']}
            onReveal={handleMatrixReveal}
            duration={current.tier === 'legendary' ? 3000 : 2000}
          />
        )}
      </AnimatePresence>

      {/* EVENT CARD */}
      <AnimatePresence>
        {phase === 'event' && current && (
          <EventCard event={current} onDone={handleEventDone} />
        )}
      </AnimatePresence>
    </>
  );
}
