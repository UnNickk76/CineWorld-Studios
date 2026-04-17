import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Shield, Swords, Flame, Zap, Heart, Skull, Crown, Star, Ban } from 'lucide-react';

// ─── OUTCOME CONFIGS (5 images already exist) ───
const OUTCOME_CONFIG = {
  support_success: {
    images: ['/assets/outcomes/supporto_successo.png'],
    titles: ['SUPPORTO RIUSCITO!', 'GRANDE MOSSA!', 'ALLEANZA VINCENTE!', 'SPINTA DECISIVA!', 'COLPO DA MAESTRO!'],
    colors: { main: '#4ade80', glow: 'rgba(74,222,128,0.3)', bg: 'from-green-900/80 to-emerald-950/90' },
    icon: Heart, iconColor: '#4ade80',
    particles: { count: 20, colors: ['#4ade80', '#22d3ee', '#facc15', '#34d399'] },
    screenFlash: 'rgba(74,222,128,0.15)',
  },
  support_fail: {
    images: ['/assets/outcomes/supporto_fallito.png'],
    titles: ['SUPPORTO FALLITO', 'NESSUN EFFETTO...', 'OCCASIONE PERSA'],
    colors: { main: '#fb923c', glow: 'rgba(251,146,60,0.15)', bg: 'from-orange-950/80 to-gray-950/90' },
    icon: Ban, iconColor: '#fb923c',
    particles: { count: 5, colors: ['#fb923c'] },
    screenFlash: null,
  },
  boycott_success: {
    images: ['/assets/outcomes/boicotto_successo.png'],
    titles: ['BOICOTTO RIUSCITO!', 'COLPO DEVASTANTE!', 'ATTACCO LETALE!', 'SABOTAGGIO PERFETTO!', 'DISTRUZIONE TOTALE!'],
    colors: { main: '#f87171', glow: 'rgba(248,113,113,0.35)', bg: 'from-red-950/80 to-gray-950/90' },
    icon: Skull, iconColor: '#f87171',
    particles: { count: 30, colors: ['#f87171', '#ef4444', '#fbbf24', '#fb923c', '#dc2626'] },
    screenFlash: 'rgba(248,113,113,0.2)',
    shake: true,
  },
  boycott_fail: {
    images: ['/assets/outcomes/boicotto_fallito.png'],
    titles: ['BOICOTTO FALLITO!', 'MANCATO!', 'TENTATIVO VANO'],
    colors: { main: '#6b7280', glow: 'rgba(107,114,128,0.1)', bg: 'from-gray-950/80 to-gray-950/90' },
    icon: Ban, iconColor: '#6b7280',
    particles: { count: 3, colors: ['#6b7280'] },
    screenFlash: null,
  },
  boycott_backfire: {
    images: ['/assets/outcomes/boicotto_ritorto.png'],
    titles: ['RITORSIONE!', 'SI E RITORTO CONTRO!', 'KARMA ISTANTANEO!', 'AUTODISTRUZIONE!'],
    colors: { main: '#a78bfa', glow: 'rgba(167,139,250,0.3)', bg: 'from-purple-950/80 to-gray-950/90' },
    icon: Zap, iconColor: '#a78bfa',
    particles: { count: 25, colors: ['#a78bfa', '#c084fc', '#f87171', '#fbbf24'] },
    screenFlash: 'rgba(167,139,250,0.15)',
    shake: true,
  },
  boycott_blocked: {
    images: ['/assets/outcomes/boicotto_fallito.png'],
    titles: ['BLOCCATO!', 'SCUDO ATTIVO!', 'DIFESA IMPENETRABILE!'],
    colors: { main: '#22d3ee', glow: 'rgba(34,211,238,0.25)', bg: 'from-cyan-950/80 to-gray-950/90' },
    icon: Shield, iconColor: '#22d3ee',
    particles: { count: 15, colors: ['#22d3ee', '#06b6d4', '#67e8f9'] },
    screenFlash: 'rgba(34,211,238,0.12)',
  },
};

export function getOutcomeType(action, outcome) {
  if (action === 'support' || action === 'hype') return outcome === 'success' ? 'support_success' : 'support_fail';
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

// ─── PARTICLES ───
function ParticleExplosion({ config, active }) {
  if (!active || !config) return null;
  const particles = Array.from({ length: config.count }, (_, i) => {
    const angle = (i / config.count) * Math.PI * 2 + Math.random() * 0.5;
    const dist = 50 + Math.random() * 80;
    const color = config.colors[i % config.colors.length];
    return { x: Math.cos(angle) * dist, y: Math.sin(angle) * dist - 20, delay: Math.random() * 0.15, size: 2 + Math.random() * 6, color, rotation: Math.random() * 360 };
  });
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 3 }}>
      {particles.map((p, i) => (
        <motion.div key={i} className="absolute" style={{ left: '50%', top: '35%', width: p.size, height: p.size, backgroundColor: p.color, borderRadius: p.size > 4 ? '2px' : '50%' }}
          initial={{ x: 0, y: 0, opacity: 1, scale: 1.5, rotate: 0 }}
          animate={{ x: p.x, y: p.y, opacity: 0, scale: 0, rotate: p.rotation }}
          transition={{ duration: 0.8 + Math.random() * 0.4, delay: p.delay, ease: 'easeOut' }} />
      ))}
    </div>
  );
}

// ─── SCREEN SHAKE ───
function useScreenShake(active, intensity = 4) {
  useEffect(() => {
    if (!active) return;
    const el = document.body;
    let frame = 0;
    const maxFrames = 12;
    const shake = () => {
      if (frame >= maxFrames) { el.style.transform = ''; return; }
      const x = (Math.random() - 0.5) * intensity * (1 - frame / maxFrames);
      const y = (Math.random() - 0.5) * intensity * (1 - frame / maxFrames);
      el.style.transform = `translate(${x}px, ${y}px)`;
      frame++;
      requestAnimationFrame(shake);
    };
    shake();
    return () => { el.style.transform = ''; };
  }, [active, intensity]);
}

// ─── RADIAL SHOCKWAVE ───
function Shockwave({ color, active }) {
  if (!active) return null;
  return (
    <motion.div className="absolute pointer-events-none" style={{ left: '50%', top: '35%', zIndex: 2, transform: 'translate(-50%,-50%)' }}
      initial={{ width: 0, height: 0, opacity: 0.8, borderRadius: '50%', border: `3px solid ${color}` }}
      animate={{ width: 300, height: 300, opacity: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }} />
  );
}

// ─── NUMBER COUNTER ───
function AnimatedNumber({ value, suffix = '%', color }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const end = Math.abs(parseFloat(value) || 0);
    const duration = 800;
    const startTime = Date.now();
    const tick = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(+(start + (end - start) * eased).toFixed(1));
      if (progress < 1) requestAnimationFrame(tick);
    };
    tick();
  }, [value]);
  return <span style={{ color, fontFamily: "'Bebas Neue', sans-serif", fontSize: '32px', letterSpacing: '2px' }}>{value < 0 ? '-' : '+'}{display}{suffix}</span>;
}

// ─── MAIN POPUP ───
export function OutcomePopup({ open, onClose, outcomeType, title, message, diminishInfo, rivalryInfo }) {
  const config = OUTCOME_CONFIG[outcomeType] || OUTCOME_CONFIG.support_success;
  const [titleIdx] = useState(() => Math.floor(Math.random() * config.titles.length));
  const [imageIdx] = useState(() => Math.floor(Math.random() * config.images.length));
  const IconComp = config.icon;
  const isImpact = outcomeType === 'boycott_success' || outcomeType === 'boycott_backfire';
  const isPositive = outcomeType === 'support_success' || outcomeType === 'boycott_success';

  useScreenShake(open && config.shake, isImpact ? 6 : 3);

  // Extract numeric value from message
  const numMatch = message?.match(/([+-]?\d+\.?\d*)%/);
  const numValue = numMatch ? parseFloat(numMatch[1]) : null;

  // Auto-close
  useEffect(() => {
    if (open) { const t = setTimeout(onClose, 7000); return () => clearTimeout(t); }
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div className="fixed inset-0 flex items-center justify-center px-3" style={{ zIndex: 99999 }}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} data-testid="outcome-popup-overlay">

          {/* Backdrop */}
          <motion.div className="absolute inset-0" onClick={onClose}
            initial={{ backgroundColor: 'rgba(0,0,0,0)' }} animate={{ backgroundColor: 'rgba(0,0,0,0.85)' }}
            style={{ backdropFilter: 'blur(8px)' }} />

          {/* Screen flash */}
          {config.screenFlash && (
            <motion.div className="absolute inset-0 pointer-events-none" style={{ zIndex: 1, background: config.screenFlash }}
              initial={{ opacity: 1 }} animate={{ opacity: 0 }} transition={{ duration: 0.4 }} />
          )}

          {/* Card */}
          <motion.div className={`relative w-[320px] max-w-[94vw] rounded-2xl overflow-hidden bg-gradient-to-b ${config.colors.bg}`}
            style={{ border: `2px solid ${config.colors.main}40`, boxShadow: `0 0 40px ${config.colors.glow}, 0 0 80px ${config.colors.glow}` }}
            initial={{ scale: 0.2, opacity: 0, y: 50, rotateX: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0, rotateX: 0 }}
            exit={{ scale: 0.6, opacity: 0, y: 60 }}
            transition={{ type: 'spring', damping: 12, stiffness: 200 }}
            data-testid="outcome-popup">

            {/* Particles */}
            <ParticleExplosion config={config.particles} active={open} />
            <Shockwave color={config.colors.main} active={open && isImpact} />

            {/* Close */}
            <button onClick={onClose} className="absolute top-3 right-3 z-30 w-8 h-8 rounded-full bg-black/60 backdrop-blur flex items-center justify-center text-gray-400 hover:text-white transition" data-testid="outcome-close-btn">
              <X className="w-4 h-4" />
            </button>

            {/* Icon badge top-left */}
            <motion.div className="absolute top-3 left-3 z-20 w-10 h-10 rounded-full flex items-center justify-center"
              style={{ background: `${config.colors.main}20`, border: `2px solid ${config.colors.main}40`, boxShadow: `0 0 15px ${config.colors.glow}` }}
              initial={{ scale: 0, rotate: -180 }} animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: 0.15, type: 'spring', stiffness: 300 }}>
              <IconComp className="w-5 h-5" style={{ color: config.iconColor }} />
            </motion.div>

            {/* Image */}
            <motion.div className="relative" initial={{ scale: 1.15 }} animate={{ scale: 1 }} transition={{ duration: 0.5 }}>
              <img src={config.images[imageIdx]} alt="" className="w-full aspect-[4/3] object-cover" style={{ filter: isImpact ? 'brightness(1.1) contrast(1.05)' : '' }} />
              {/* Gradient overlay bottom */}
              <div className="absolute bottom-0 inset-x-0 h-32" style={{ background: `linear-gradient(to top, ${outcomeType.includes('boycott') ? '#0a0a0b' : '#0a0a0b'} 0%, transparent 100%)` }} />

              {/* Animated number overlay */}
              {numValue !== null && (
                <motion.div className="absolute bottom-4 right-4 z-10"
                  initial={{ scale: 0, y: 20 }} animate={{ scale: 1, y: 0 }}
                  transition={{ delay: 0.3, type: 'spring', stiffness: 200 }}>
                  <AnimatedNumber value={numValue * (outcomeType.includes('backfire') ? -1 : outcomeType.includes('boycott_success') ? -1 : 1)} color={config.colors.main} />
                </motion.div>
              )}
            </motion.div>

            {/* Content */}
            <div className="px-4 pb-4 -mt-4 relative z-10">
              {/* Title with stagger animation */}
              <motion.h2 className="font-['Bebas_Neue'] text-2xl tracking-wide leading-none"
                style={{ color: config.colors.main, textShadow: `0 0 20px ${config.colors.glow}` }}
                initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
                {config.titles[titleIdx]}
              </motion.h2>

              {title && (
                <motion.p className="text-sm font-bold text-white mt-1"
                  initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
                  {title}
                </motion.p>
              )}

              {message && (
                <motion.p className="text-[11px] text-gray-300 mt-2 leading-relaxed"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
                  {message}
                </motion.p>
              )}

              {/* Badges */}
              <div className="flex flex-wrap gap-1.5 mt-3">
                {diminishInfo != null && diminishInfo < 1.0 && (
                  <motion.span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[8px] font-bold"
                    style={{ background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.2)', color: '#fbbf24' }}
                    initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.5 }}>
                    <Flame className="w-2.5 h-2.5" /> Efficacia {Math.round(diminishInfo * 100)}%
                  </motion.span>
                )}
                {rivalryInfo?.is_rivalry && (
                  <motion.span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[8px] font-bold"
                    style={{ background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.2)', color: '#f87171' }}
                    initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.55, type: 'spring' }}>
                    <Swords className="w-2.5 h-2.5" /> RIVALITA +20%
                  </motion.span>
                )}
              </div>

              {/* CTA Button */}
              <motion.button onClick={onClose} data-testid="outcome-ok-btn"
                className="w-full mt-4 py-3 rounded-xl text-sm font-bold transition-all active:scale-95"
                style={{
                  background: `linear-gradient(135deg, ${config.colors.main}30, ${config.colors.main}10)`,
                  border: `1px solid ${config.colors.main}40`,
                  color: config.colors.main,
                  boxShadow: `0 0 20px ${config.colors.glow}`,
                }}
                initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.5 }}
                whileTap={{ scale: 0.95 }}>
                {isPositive ? 'CONTINUA' : 'OK'}
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
