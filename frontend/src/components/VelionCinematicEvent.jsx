import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Film, Tv, Sparkles } from 'lucide-react';
import MatrixOverlay from './MatrixOverlay';

const TIER_STYLES = {
  common: { border: 'border-gray-500/30', bg: 'from-gray-900/95 to-gray-800/90', glow: '', label: 'EVENTO', labelColor: 'text-gray-400', glowColor: 'rgba(100,100,100,0.15)' },
  rare: { border: 'border-blue-500/40', bg: 'from-[#0a0a1a]/95 to-[#0a1030]/90', glow: 'shadow-[0_0_40px_rgba(59,130,246,0.2)]', label: 'RARO', labelColor: 'text-blue-400', glowColor: 'rgba(59,130,246,0.25)' },
  epic: { border: 'border-purple-500/50', bg: 'from-[#0d0516]/95 to-[#1a0530]/90', glow: 'shadow-[0_0_60px_rgba(168,85,247,0.3)]', label: 'EPICO', labelColor: 'text-purple-400', glowColor: 'rgba(168,85,247,0.3)' },
  legendary: { border: 'border-yellow-500/60', bg: 'from-[#1a1000]/95 to-[#2a1800]/90', glow: 'shadow-[0_0_80px_rgba(234,179,8,0.4)]', label: 'LEGGENDARIO', labelColor: 'text-yellow-400', glowColor: 'rgba(234,179,8,0.4)' },
};

const TYPE_BADGE_MAP = {
  film: { icon: Film, label: 'FILM', color: 'bg-red-500/25 text-red-400 border-red-500/40' },
  series: { icon: Tv, label: 'SERIE', color: 'bg-cyan-500/25 text-cyan-400 border-cyan-500/40' },
  anime: { icon: Sparkles, label: 'ANIME', color: 'bg-pink-500/25 text-pink-400 border-pink-500/40' },
};

function EventCard({ event, onDone }) {
  const style = TIER_STYLES[event.tier] || TIER_STYLES.common;
  const isPositive = event.event_type === 'positive' || event.event_type === 'star_born';
  const canSkip = useRef(false);
  const tb = TYPE_BADGE_MAP[event.project_type];

  // Auto-close timers: legendary 8s, epic 6s, common 4s
  const autoCloseDuration = event.tier === 'legendary' ? 8000 : event.tier === 'epic' ? 6000 : 4000;
  // Skip blocked for 4 seconds (so user sees full animation)
  const skipBlockMs = 4000;

  useEffect(() => {
    const unlock = setTimeout(() => { canSkip.current = true; }, skipBlockMs);
    const autoClose = setTimeout(onDone, autoCloseDuration);
    return () => { clearTimeout(unlock); clearTimeout(autoClose); };
  }, [onDone, autoCloseDuration]);

  const handleTap = useCallback(() => {
    if (canSkip.current) onDone();
  }, [onDone]);

  return (
    <motion.div
      className="fixed inset-0 z-[500] flex items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      onClick={handleTap}
      data-testid="velion-cinematic-event"
    >
      <div className="absolute inset-0 bg-black/90" />

      {/* Velion — lateral, large, left side with glow */}
      <motion.div
        className="absolute bottom-0 left-0 z-[501] pointer-events-none"
        initial={{ x: -120, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 1.0, duration: 0.8, type: 'spring', damping: 15 }}
      >
        <div className="relative">
          {/* Glow behind Velion */}
          <motion.div
            className="absolute inset-0 rounded-full blur-3xl"
            style={{ background: `radial-gradient(circle, ${style.glowColor} 0%, transparent 70%)`, width: '180%', height: '180%', left: '-40%', top: '-40%' }}
            animate={{ scale: [1, 1.15, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.img
            src="/velion-tutorial.png"
            alt="Velion"
            className="w-32 h-40 sm:w-40 sm:h-48 object-contain drop-shadow-[0_0_30px_rgba(234,179,8,0.5)] relative z-10"
            animate={{
              y: [0, -6, 0],
              filter: ['drop-shadow(0 0 20px rgba(234,179,8,0.4))', 'drop-shadow(0 0 35px rgba(234,179,8,0.6))', 'drop-shadow(0 0 20px rgba(234,179,8,0.4))'],
            }}
            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
          />
        </div>
      </motion.div>

      {/* Event Content — centered on screen */}
      <motion.div
        className={`relative z-[502] w-full max-w-[75%] sm:max-w-sm mx-auto rounded-2xl border-2 ${style.border} bg-gradient-to-b ${style.bg} ${style.glow} backdrop-blur-xl overflow-hidden`}
        initial={{ scale: 0.5, y: 40, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        exit={{ scale: 0.85, opacity: 0 }}
        transition={{ delay: 1.2, type: 'spring', damping: 16, stiffness: 180 }}
      >
        {/* Type Badge */}
        {tb && (() => {
          const TIcon = tb.icon;
          return (
            <motion.div
              className={`absolute top-3 right-3 z-20 flex items-center gap-1 px-2 py-0.5 rounded-full border text-[9px] font-mono ${tb.color}`}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 2.0, duration: 0.3 }}
            >
              <TIcon className="w-3 h-3" />
              {tb.label}
            </motion.div>
          );
        })()}

        <div className="px-5 py-5">
          {/* Tier Label — cinematic reveal */}
          <motion.div
            className={`text-[10px] font-mono font-bold tracking-[0.4em] ${style.labelColor} mb-3`}
            initial={{ opacity: 0, letterSpacing: '0.8em' }}
            animate={{ opacity: 1, letterSpacing: '0.4em' }}
            transition={{ delay: 1.6, duration: 0.6 }}
          >
            {style.label}
          </motion.div>

          {/* Event title (film name) */}
          {event.film_title && (
            <motion.p
              className="text-[10px] text-gray-500 font-mono mb-1 uppercase tracking-wider"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.8 }}
            >
              {event.film_title}
            </motion.p>
          )}

          {/* Main event text — staggered character reveal */}
          <motion.p
            className={`text-sm sm:text-base font-bold leading-relaxed ${isPositive ? 'text-white' : 'text-red-200'}`}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 2.0, duration: 0.5 }}
          >
            {event.text}
          </motion.p>

          {/* Effects */}
          <motion.div
            className="flex items-center gap-2 mt-3 flex-wrap"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.5, duration: 0.4 }}
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

          {/* Tap to close hint */}
          <motion.p
            className="text-[9px] text-gray-600 mt-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 3.5 }}
          >
            tap per chiudere
          </motion.p>
        </div>
      </motion.div>
    </motion.div>
  );
}

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

  // PHASE: fadeout (1000ms) → blackhold (3-5s) → matrix (8s+) → event (6-8s)
  useEffect(() => {
    if (phase !== 'fadeout') return;
    const t = setTimeout(() => setPhase('blackhold'), 1000);
    return () => clearTimeout(t);
  }, [phase]);

  // Black screen hold: 3s for epic, 5s for legendary
  useEffect(() => {
    if (phase !== 'blackhold') return;
    const holdMs = current?.tier === 'legendary' ? 5000 : 3000;
    const t = setTimeout(() => setPhase('matrix'), holdMs);
    return () => clearTimeout(t);
  }, [phase, current]);

  const handleMatrixReveal = useCallback(() => {
    setPhase('event');
  }, []);

  const handleEventDone = useCallback(() => {
    setCurrent(null);
    if (queue.length === 0) {
      setPhase('idle');
      if (onAllDone) onAllDone();
    } else {
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
      {/* FADEOUT: blur + desaturation */}
      <AnimatePresence>
        {phase === 'fadeout' && (
          <motion.div
            className="fixed inset-0 z-[390]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.0, ease: 'easeInOut' }}
          >
            <motion.div
              className="absolute inset-0"
              style={{ backdropFilter: 'blur(16px) saturate(0.05) brightness(0.15)' }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1.0 }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* BLACK HOLD: full black 3-5s */}
      <AnimatePresence>
        {(phase === 'blackhold' || phase === 'matrix' || phase === 'event') && (
          <motion.div
            className="fixed inset-0 z-[395] bg-black"
            initial={{ opacity: phase === 'blackhold' ? 0 : 1 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: phase === 'blackhold' ? 0.4 : 0.6 }}
          />
        )}
      </AnimatePresence>

      {/* MATRIX: min 8s */}
      <AnimatePresence>
        {phase === 'matrix' && current && (
          <MatrixOverlay
            filmTitles={[current.film_title || current.movie_title || '']}
            actorNames={[current.actor_name || '']}
            onReveal={handleMatrixReveal}
            duration={current.tier === 'legendary' ? 10000 : 8000}
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
