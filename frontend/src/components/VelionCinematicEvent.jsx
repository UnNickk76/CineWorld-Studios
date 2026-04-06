import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MatrixOverlay from './MatrixOverlay';

const TIER_STYLES = {
  common: { border: 'border-gray-500/30', bg: 'bg-gray-900/95', glow: '', label: 'EVENTO', labelColor: 'text-gray-400' },
  rare: { border: 'border-blue-500/40', bg: 'bg-[#0a0a1a]/95', glow: 'shadow-[0_0_30px_rgba(59,130,246,0.15)]', label: 'RARO', labelColor: 'text-blue-400' },
  epic: { border: 'border-purple-500/50', bg: 'bg-[#0d0516]/95', glow: 'shadow-[0_0_40px_rgba(168,85,247,0.2)]', label: 'EPICO', labelColor: 'text-purple-400' },
  legendary: { border: 'border-yellow-500/60', bg: 'bg-[#1a1000]/95', glow: 'shadow-[0_0_60px_rgba(234,179,8,0.3)]', label: 'LEGGENDARIO', labelColor: 'text-yellow-400' },
};

function EventCard({ event, onDone }) {
  const style = TIER_STYLES[event.tier] || TIER_STYLES.common;
  const isPositive = event.event_type === 'positive' || event.event_type === 'star_born';

  useEffect(() => {
    const t = setTimeout(onDone, event.tier === 'legendary' ? 4000 : event.tier === 'epic' ? 3500 : 2500);
    return () => clearTimeout(t);
  }, [event.tier, onDone]);

  return (
    <motion.div
      className="fixed inset-0 z-[500] flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      onClick={onDone}
      data-testid="velion-cinematic-event"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/80" />

      <motion.div
        className={`relative z-10 max-w-sm w-full rounded-2xl border-2 ${style.border} ${style.bg} ${style.glow} backdrop-blur-xl overflow-hidden`}
        initial={{ scale: 0.7, y: 40, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        exit={{ scale: 0.8, opacity: 0 }}
        transition={{ type: 'spring', damping: 20, stiffness: 300 }}
      >
        {/* Velion */}
        <div className="flex justify-center pt-4 -mb-2">
          <motion.img
            src="/velion-tutorial.png"
            alt="Velion"
            className="w-20 h-24 object-contain drop-shadow-[0_0_20px_rgba(234,179,8,0.4)]"
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: [0.5, 1.1, 1], opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5, type: 'spring' }}
          />
        </div>

        {/* Content */}
        <div className="px-5 pb-5 pt-2 text-center">
          {/* Tier label */}
          <motion.div
            className={`text-[10px] font-mono font-bold tracking-[0.3em] ${style.labelColor} mb-2`}
            initial={{ opacity: 0, letterSpacing: '0.5em' }}
            animate={{ opacity: 1, letterSpacing: '0.3em' }}
            transition={{ delay: 0.3 }}
          >
            {style.label}
          </motion.div>

          {/* Event text */}
          <motion.p
            className={`text-sm font-semibold leading-relaxed ${isPositive ? 'text-white' : 'text-red-200'}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            {event.text}
          </motion.p>

          {/* Effects badges */}
          <motion.div
            className="flex items-center justify-center gap-2 mt-3 flex-wrap"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
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

          {/* Tap to close */}
          <motion.p
            className="text-[9px] text-gray-600 mt-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
          >
            tap per chiudere
          </motion.p>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function VelionCinematicEvent({ events = [], onAllDone }) {
  const [queue, setQueue] = useState([]);
  const [current, setCurrent] = useState(null);
  const [phase, setPhase] = useState('idle'); // idle | blackout | matrix | reveal | event
  const [blackoutDone, setBlackoutDone] = useState(false);

  // Initialize queue from events
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

    const isEpicOrLegendary = next.tier === 'epic' || next.tier === 'legendary';

    if (isEpicOrLegendary) {
      // Start blackout sequence
      setPhase('blackout');
      setBlackoutDone(false);
    } else {
      // Common/rare: just show event card directly
      setPhase('event');
    }
  }, [phase, queue]);

  // Blackout → Matrix transition
  useEffect(() => {
    if (phase !== 'blackout') return;
    const t = setTimeout(() => {
      setBlackoutDone(true);
      setPhase('matrix');
    }, 600); // 0.3s blur + 0.3s black
    return () => clearTimeout(t);
  }, [phase]);

  const handleMatrixReveal = useCallback(() => {
    setPhase('event');
  }, []);

  const handleEventDone = useCallback(() => {
    setCurrent(null);
    setPhase('idle');
    setBlackoutDone(false);
    // If no more events, signal done
    if (queue.length === 0) {
      if (onAllDone) onAllDone();
    }
  }, [queue, onAllDone]);

  if (!current && queue.length === 0) return null;

  return (
    <>
      {/* BLACKOUT PHASE: blur + desaturation + fade to black */}
      <AnimatePresence>
        {(phase === 'blackout') && (
          <motion.div
            className="fixed inset-0 z-[390]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Phase 1: blur + desaturate */}
            {!blackoutDone && (
              <motion.div
                className="absolute inset-0"
                style={{ backdropFilter: 'blur(8px) saturate(0.2)' }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              />
            )}
            {/* Phase 2: full black */}
            <motion.div
              className="absolute inset-0 bg-black"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.3 }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* MATRIX PHASE */}
      <AnimatePresence>
        {phase === 'matrix' && current && (
          <MatrixOverlay
            filmTitles={[current.film_title || current.movie_title || '']}
            actorNames={[current.actor_name || '']}
            onReveal={handleMatrixReveal}
            duration={current.tier === 'legendary' ? 2500 : 1500}
          />
        )}
      </AnimatePresence>

      {/* EVENT CARD PHASE */}
      <AnimatePresence>
        {phase === 'event' && current && (
          <EventCard event={current} onDone={handleEventDone} />
        )}
      </AnimatePresence>
    </>
  );
}
