import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import { Crown, Star } from 'lucide-react';

/**
 * Cinematic toast fired when a player's prestige tier rises (fame threshold crossed).
 * Listens to 'cw:prestige-tier-up' with detail { prev_tier, new_tier, new_tier_color, fame, message }.
 * Magenta/purple palette to visually differentiate from Level-Up (gold).
 */
export const PrestigeTierToast = () => {
  const [event, setEvent] = useState(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      const d = e?.detail || {};
      if (!d.new_tier) return;
      setEvent({
        prevTier: d.prev_tier || '',
        newTier: d.new_tier,
        color: d.new_tier_color || '#d946ef',
        fame: d.fame,
        id: Date.now(),
      });
      // Confetti purple burst
      try {
        const shoot = (opts) => confetti({
          particleCount: 55,
          spread: 80,
          startVelocity: 50,
          ticks: 160,
          gravity: 1,
          decay: 0.92,
          scalar: 1,
          colors: ['#d946ef', '#a855f7', '#ec4899', '#f472b6', '#fbcfe8'],
          ...opts,
        });
        shoot({ origin: { x: 0.15, y: 0.28 } });
        shoot({ origin: { x: 0.85, y: 0.28 } });
        setTimeout(() => shoot({ origin: { x: 0.5, y: 0.35 } }), 200);
      } catch (_) { /* ignore */ }
      // Audio cue
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.connect(g); g.connect(ctx.destination);
        o.type = 'sine';
        o.frequency.setValueAtTime(440, ctx.currentTime);
        o.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.3);
        o.frequency.exponentialRampToValueAtTime(1318.51, ctx.currentTime + 0.6);
        g.gain.setValueAtTime(0.0001, ctx.currentTime);
        g.gain.exponentialRampToValueAtTime(0.22, ctx.currentTime + 0.04);
        g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.7);
        o.start();
        o.stop(ctx.currentTime + 0.75);
      } catch (_) { /* ignore */ }

      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setEvent(null), 5200);
    };
    window.addEventListener('cw:prestige-tier-up', handler);
    return () => {
      window.removeEventListener('cw:prestige-tier-up', handler);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <AnimatePresence>
      {event && (
        <motion.div
          key={event.id}
          data-testid="prestige-tier-toast"
          initial={{ opacity: 0, y: -60, scale: 0.92 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -40, scale: 0.95 }}
          transition={{ type: 'spring', stiffness: 280, damping: 22 }}
          className="fixed left-1/2 -translate-x-1/2 z-[9999] pointer-events-none px-4"
          style={{ top: 'calc(3.5rem + env(safe-area-inset-top, 0px) + 8px)', width: 'min(94vw, 420px)' }}
        >
          <div className="relative overflow-hidden rounded-2xl border border-fuchsia-300/40 shadow-[0_10px_40px_rgba(217,70,239,0.4)]"
               style={{ background: 'linear-gradient(135deg, #1a0022 0%, #3d0055 40%, #7a0099 100%)' }}>
            {/* Shimmer */}
            <motion.div
              className="absolute inset-0 pointer-events-none"
              initial={{ x: '-100%' }}
              animate={{ x: '200%' }}
              transition={{ duration: 1.8, ease: 'easeInOut', repeat: 1 }}
              style={{ background: 'linear-gradient(120deg, transparent 30%, rgba(245,200,255,0.35) 50%, transparent 70%)' }}
            />
            <div className="relative flex items-center gap-3 px-4 py-3">
              <motion.div
                initial={{ rotate: -20, scale: 0.6 }}
                animate={{ rotate: 0, scale: 1 }}
                transition={{ type: 'spring', stiffness: 260, damping: 14, delay: 0.1 }}
                className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center"
                style={{
                  background: `radial-gradient(circle, ${event.color} 0%, #a855f7 70%, #6b21a8 100%)`,
                  boxShadow: `0 0 24px ${event.color}80, inset 0 0 8px rgba(255,255,255,0.4)`,
                }}
              >
                <Crown className="w-6 h-6 text-white" strokeWidth={2.5} />
              </motion.div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <Star className="w-3.5 h-3.5 text-fuchsia-300" />
                  <span className="text-[11px] uppercase tracking-[0.18em] font-bold text-fuchsia-300/90 font-['Bebas_Neue']">
                    Nuovo Rango
                  </span>
                </div>
                <div className="text-white font-['Bebas_Neue'] text-2xl leading-none mt-0.5" data-testid="prestige-new-tier">
                  {event.newTier}
                </div>
                <div className="text-[11px] text-fuchsia-100/80 mt-1 truncate">
                  {event.prevTier ? `Da ${event.prevTier} a ${event.newTier}` : 'Prestigio sbloccato!'}
                </div>
              </div>
            </div>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: '100%' }}
              transition={{ duration: 4.8, ease: 'linear' }}
              className="h-[3px] bg-gradient-to-r from-fuchsia-500 via-pink-300 to-purple-500"
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default PrestigeTierToast;
