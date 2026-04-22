import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import { Trophy, Sparkles } from 'lucide-react';

/**
 * Toast cinematografico LEVEL UP.
 * Ascolta l'evento global `cw:level-up` con detail { newLevel, oldLevel }.
 * Mobile-first: card full-width centrata in alto, animazione gold + confetti.
 */
export const LevelUpToast = () => {
  const [event, setEvent] = useState(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      const detail = e?.detail || {};
      const newLevel = Number(detail.newLevel ?? 0);
      const oldLevel = Number(detail.oldLevel ?? 0);
      if (newLevel <= oldLevel) return;
      setEvent({ newLevel, oldLevel, id: Date.now() });
      // Confetti gold burst
      try {
        const shoot = (opts) => confetti({
          particleCount: 40,
          spread: 70,
          startVelocity: 45,
          ticks: 140,
          gravity: 1.1,
          decay: 0.92,
          scalar: 0.9,
          colors: ['#FFD700', '#FFA500', '#FFEF99', '#FF7A00'],
          ...opts,
        });
        shoot({ origin: { x: 0.15, y: 0.25 } });
        shoot({ origin: { x: 0.85, y: 0.25 } });
        setTimeout(() => shoot({ origin: { x: 0.5, y: 0.3 } }), 180);
      } catch (_) { /* ignore */ }

      // Audio cue (best-effort, silent if blocked)
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.connect(g); g.connect(ctx.destination);
        o.type = 'triangle';
        o.frequency.setValueAtTime(523.25, ctx.currentTime); // C5
        o.frequency.exponentialRampToValueAtTime(1046.5, ctx.currentTime + 0.25); // C6
        g.gain.setValueAtTime(0.0001, ctx.currentTime);
        g.gain.exponentialRampToValueAtTime(0.25, ctx.currentTime + 0.03);
        g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.5);
        o.start();
        o.stop(ctx.currentTime + 0.55);
      } catch (_) { /* ignore */ }

      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setEvent(null), 4800);
    };
    window.addEventListener('cw:level-up', handler);
    return () => {
      window.removeEventListener('cw:level-up', handler);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <AnimatePresence>
      {event && (
        <motion.div
          key={event.id}
          data-testid="level-up-toast"
          initial={{ opacity: 0, y: -60, scale: 0.92 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -40, scale: 0.95 }}
          transition={{ type: 'spring', stiffness: 280, damping: 22 }}
          className="fixed left-1/2 -translate-x-1/2 z-[9999] pointer-events-none px-4"
          style={{ top: 'calc(3.5rem + env(safe-area-inset-top, 0px) + 8px)', width: 'min(94vw, 420px)' }}
        >
          <div className="relative overflow-hidden rounded-2xl border border-amber-300/40 shadow-[0_10px_40px_rgba(255,170,0,0.35)]"
               style={{
                 background: 'linear-gradient(135deg, #1a0f00 0%, #3d2100 40%, #7a3d00 100%)',
               }}>
            {/* Animated shimmer overlay */}
            <motion.div
              className="absolute inset-0 pointer-events-none"
              initial={{ x: '-100%' }}
              animate={{ x: '200%' }}
              transition={{ duration: 1.6, ease: 'easeInOut', repeat: 1 }}
              style={{
                background: 'linear-gradient(120deg, transparent 30%, rgba(255,223,130,0.35) 50%, transparent 70%)',
              }}
            />
            {/* Content */}
            <div className="relative flex items-center gap-3 px-4 py-3">
              <motion.div
                initial={{ rotate: -20, scale: 0.6 }}
                animate={{ rotate: 0, scale: 1 }}
                transition={{ type: 'spring', stiffness: 260, damping: 14, delay: 0.08 }}
                className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center"
                style={{
                  background: 'radial-gradient(circle, #FFE28A 0%, #FFA500 70%, #B56400 100%)',
                  boxShadow: '0 0 24px rgba(255,200,60,0.7), inset 0 0 8px rgba(255,255,255,0.4)',
                }}
              >
                <Trophy className="w-6 h-6 text-amber-900" strokeWidth={2.5} />
              </motion.div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                  <span className="text-[11px] uppercase tracking-[0.18em] font-bold text-amber-300/90 font-['Bebas_Neue']">
                    Level Up
                  </span>
                </div>
                <div className="text-white font-['Bebas_Neue'] text-2xl leading-none mt-0.5">
                  Livello <motion.span
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 12, delay: 0.18 }}
                    className="text-amber-300 inline-block"
                    data-testid="level-up-new-level"
                  >{event.newLevel}</motion.span>
                </div>
                <div className="text-[12px] text-amber-100/80 mt-1 truncate">
                  Complimenti Regista, nuovo traguardo sbloccato!
                </div>
              </div>
            </div>

            {/* Progress bar flash */}
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: '100%' }}
              transition={{ duration: 4.4, ease: 'linear' }}
              className="h-[3px] bg-gradient-to-r from-amber-500 via-amber-300 to-amber-500"
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default LevelUpToast;
