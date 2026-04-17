import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Shield, Swords, Flame, Zap } from 'lucide-react';

const OUTCOME_CONFIG = {
  support_success: {
    image: '/assets/outcomes/supporto_successo.png',
    title: 'Supporto riuscito!',
    color: 'text-green-400',
    borderColor: 'border-green-500/40',
    glow: 'shadow-green-500/20',
    bgGlow: 'radial-gradient(circle at 50% 30%, rgba(74,222,128,0.15) 0%, transparent 70%)',
    icon: Flame,
    shakeClass: '',
    particleColor: '#4ade80',
  },
  support_fail: {
    image: '/assets/outcomes/supporto_fallito.png',
    title: 'Supporto fallito...',
    color: 'text-orange-400',
    borderColor: 'border-orange-500/40',
    glow: 'shadow-orange-500/20',
    bgGlow: 'radial-gradient(circle at 50% 30%, rgba(251,146,60,0.1) 0%, transparent 70%)',
    icon: null,
    shakeClass: '',
    particleColor: '#fb923c',
  },
  boycott_success: {
    image: '/assets/outcomes/boicotto_successo.png',
    title: 'Boicotto riuscito!',
    color: 'text-red-400',
    borderColor: 'border-red-500/40',
    glow: 'shadow-red-500/30',
    bgGlow: 'radial-gradient(circle at 50% 30%, rgba(248,113,113,0.2) 0%, transparent 70%)',
    icon: Swords,
    shakeClass: 'animate-shake',
    particleColor: '#f87171',
  },
  boycott_fail: {
    image: '/assets/outcomes/boicotto_fallito.png',
    title: 'Boicotto fallito!',
    color: 'text-gray-400',
    borderColor: 'border-gray-500/40',
    glow: 'shadow-gray-500/20',
    bgGlow: '',
    icon: null,
    shakeClass: '',
    particleColor: '#9ca3af',
  },
  boycott_backfire: {
    image: '/assets/outcomes/boicotto_ritorto.png',
    title: 'Boicotto ritorto!',
    color: 'text-purple-400',
    borderColor: 'border-purple-500/40',
    glow: 'shadow-purple-500/30',
    bgGlow: 'radial-gradient(circle at 50% 30%, rgba(167,139,250,0.2) 0%, transparent 70%)',
    icon: Zap,
    shakeClass: 'animate-shake',
    particleColor: '#a78bfa',
  },
  boycott_blocked: {
    image: '/assets/outcomes/boicotto_fallito.png',
    title: 'Attacco bloccato!',
    color: 'text-cyan-400',
    borderColor: 'border-cyan-500/40',
    glow: 'shadow-cyan-500/30',
    bgGlow: 'radial-gradient(circle at 50% 30%, rgba(34,211,238,0.15) 0%, transparent 70%)',
    icon: Shield,
    shakeClass: '',
    particleColor: '#22d3ee',
  },
};

export function getOutcomeType(action, outcome) {
  if (action === 'support' || action === 'hype') {
    return outcome === 'success' ? 'support_success' : 'support_fail';
  }
  if (outcome === 'blocked') return 'boycott_blocked';
  if (outcome === 'success') return 'boycott_success';
  if (outcome === 'backfire') return 'boycott_backfire';
  return 'boycott_fail';
}

export function parseOutcome(category, data) {
  if (data.blocked) return 'blocked';
  if (category === 'boycott' && data.boycott_success === false) return 'backfire';
  if (data.success || data.boycott_success) return 'success';
  return 'fail';
}

// Particle burst effect
function ParticleBurst({ color, active }) {
  if (!active) return null;
  const particles = Array.from({ length: 12 }, (_, i) => {
    const angle = (i / 12) * Math.PI * 2;
    const dist = 60 + Math.random() * 40;
    return { x: Math.cos(angle) * dist, y: Math.sin(angle) * dist, delay: i * 0.03, size: 3 + Math.random() * 4 };
  });

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 1 }}>
      {particles.map((p, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{ left: '50%', top: '40%', width: p.size, height: p.size, backgroundColor: color }}
          initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
          animate={{ x: p.x, y: p.y, opacity: 0, scale: 0 }}
          transition={{ duration: 0.6, delay: p.delay, ease: 'easeOut' }}
        />
      ))}
    </div>
  );
}

// Impact flash
function ImpactFlash({ color, active }) {
  if (!active) return null;
  return (
    <motion.div
      className="absolute inset-0 pointer-events-none"
      style={{ zIndex: 2, background: `radial-gradient(circle, ${color}40 0%, transparent 70%)` }}
      initial={{ opacity: 1, scale: 0.5 }}
      animate={{ opacity: 0, scale: 2 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    />
  );
}

export function OutcomePopup({ open, onClose, outcomeType, title, message, diminishInfo, rivalryInfo }) {
  const config = OUTCOME_CONFIG[outcomeType] || OUTCOME_CONFIG.support_success;
  const IconComp = config.icon;
  const isImpact = outcomeType === 'boycott_success' || outcomeType === 'boycott_backfire';

  // Auto-close after 6s
  useEffect(() => {
    if (open) {
      const t = setTimeout(onClose, 6000);
      return () => clearTimeout(t);
    }
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 flex items-center justify-center px-4"
          style={{ zIndex: 9999 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          data-testid="outcome-popup-overlay"
        >
          <motion.div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />

          <motion.div
            className={`relative w-[300px] max-w-[92vw] rounded-2xl overflow-hidden border-2 ${config.borderColor} bg-[#0A0A0B] shadow-2xl ${config.glow}`}
            initial={{ scale: 0.3, opacity: 0, rotateX: 30 }}
            animate={{ scale: 1, opacity: 1, rotateX: 0 }}
            exit={{ scale: 0.7, opacity: 0, y: 40 }}
            transition={{ type: 'spring', damping: 15, stiffness: 300 }}
            data-testid="outcome-popup"
          >
            {/* Background glow */}
            {config.bgGlow && <div className="absolute inset-0 pointer-events-none" style={{ background: config.bgGlow }} />}

            {/* Particle burst */}
            <ParticleBurst color={config.particleColor} active={isImpact} />
            <ImpactFlash color={config.particleColor} active={isImpact} />

            <button onClick={onClose}
              className="absolute top-2 right-2 z-20 w-7 h-7 rounded-full bg-black/70 flex items-center justify-center text-gray-400 hover:text-white"
              data-testid="outcome-close-btn">
              <X className="w-4 h-4" />
            </button>

            {/* Image with icon overlay */}
            <div className="relative">
              <motion.img
                src={config.image} alt={config.title}
                className={`w-full aspect-square object-cover ${isImpact ? 'brightness-110' : ''}`}
                initial={isImpact ? { scale: 1.1 } : {}}
                animate={isImpact ? { scale: 1 } : {}}
                transition={{ duration: 0.3 }}
              />
              {IconComp && (
                <motion.div
                  className="absolute top-3 left-3 w-10 h-10 rounded-full bg-black/50 backdrop-blur-md flex items-center justify-center"
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ delay: 0.2, type: 'spring', stiffness: 300 }}
                >
                  <IconComp className={`w-5 h-5 ${config.color}`} />
                </motion.div>
              )}

              <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-[#0A0A0B] via-[#0A0A0B]/90 to-transparent p-3 pt-20">
                <motion.h2
                  className={`font-['Bebas_Neue'] text-2xl ${config.color} tracking-wide`}
                  initial={{ y: 15, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.15 }}
                >
                  {config.title}
                </motion.h2>
                {title && (
                  <motion.p className="text-sm font-semibold text-white mt-0.5"
                    initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.25 }}>
                    {title}
                  </motion.p>
                )}
              </div>
            </div>

            <div className="px-4 pb-4 pt-1 space-y-2">
              {message && (
                <motion.p className="text-[11px] text-gray-300 leading-relaxed"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }}>
                  {message}
                </motion.p>
              )}

              {/* Diminishing returns warning */}
              {diminishInfo && diminishInfo < 1.0 && (
                <motion.div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-500/10 border border-amber-500/20"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
                  <span className="text-[9px] text-amber-400">Efficacia ridotta al {Math.round(diminishInfo * 100)}% — stesso bersaglio</span>
                </motion.div>
              )}

              {/* Rivalry badge */}
              {rivalryInfo?.is_rivalry && (
                <motion.div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-red-500/10 border border-red-500/20"
                  initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.45, type: 'spring' }}>
                  <Swords className="w-3 h-3 text-red-400" />
                  <span className="text-[9px] text-red-400 font-bold">RIVALITA ATTIVA — Danni +20%!</span>
                </motion.div>
              )}

              <motion.button
                className={`w-full h-9 text-sm rounded-lg border font-bold transition-all ${
                  outcomeType.includes('success')
                    ? `bg-gradient-to-r ${outcomeType === 'boycott_success' ? 'from-red-600/20 to-orange-600/20 border-red-500/30 text-red-400' : 'from-green-600/20 to-emerald-600/20 border-green-500/30 text-green-400'}`
                    : 'bg-white/10 border-white/10 text-white'
                }`}
                onClick={onClose}
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.5 }}
                data-testid="outcome-ok-btn"
                whileTap={{ scale: 0.95 }}
              >
                OK
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
