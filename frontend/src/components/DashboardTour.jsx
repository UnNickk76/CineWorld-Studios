import React, { useState, useEffect, useCallback } from 'react';
import { X, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const TOUR_STEPS = [
  {
    targets: [{ testId: 'logo' }, { testId: 'bottom-nav-home' }],
    title: 'Home',
    desc: 'La tua base operativa: incassi, film e novita.',
  },
  {
    targets: [{ testId: 'bottom-nav-films' }],
    title: 'I Miei',
    desc: 'Tutti i tuoi film, serie TV e anime.',
  },
  {
    targets: [{ testId: 'bottom-nav-produci' }],
    title: 'Produci!',
    desc: 'Crea un nuovo film, serie o anime.',
  },
  {
    targets: [{ testId: 'bottom-nav-mercato' }],
    title: 'Mercato',
    desc: 'Compra e vendi contenuti al mercato.',
  },
  {
    targets: [{ testId: 'bottom-nav-infra' }],
    title: 'Infrastrutture',
    desc: 'Gestisci studi, sale e strutture.',
  },
  {
    targets: [{ testId: 'pvp-arena-nav-btn' }, { testId: 'bottom-nav-arena' }],
    title: 'Arena PvP',
    desc: 'Combatti contro altri produttori.',
  },
  {
    targets: [{ testId: 'notifications-btn' }, { testId: 'bottom-nav-notifiche' }],
    title: 'Eventi & Notifiche',
    desc: 'Tutti gli aggiornamenti del tuo studio.',
  },
  {
    targets: [{ testId: 'major-btn' }],
    title: 'Major',
    desc: 'La tua gilda: livelli, guerre e bonus.',
  },
  {
    targets: [{ testId: 'cineboard-btn' }],
    title: 'CineBoard',
    desc: 'Classifiche film, serie e anime.',
  },
  {
    targets: [{ testId: 'journal-nav-btn' }],
    title: 'Giornale',
    desc: 'Notizie dal mondo del cinema.',
  },
  {
    targets: [{ testId: 'challenges-nav-btn' }],
    title: 'Sfide',
    desc: 'Sfida altri giocatori e vinci premi.',
  },
  {
    targets: [{ testId: 'chat-nav-btn' }],
    title: 'Chat',
    desc: 'Chatta con altri produttori.',
  },
  {
    targets: [{ testId: 'tutorial-nav-btn' }],
    title: 'Tutorial',
    desc: 'Riapri questa guida quando vuoi.',
  },
  {
    targets: [{ testId: 'mobile-menu-btn' }],
    title: 'Menu',
    desc: 'Tutte le sezioni del gioco.',
  },
];

const STORAGE_KEY = 'dashboard_tour_done';

function getElementCenter(testId) {
  const el = document.querySelector(`[data-testid="${testId}"]`);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2, rect: r };
}

function Arrow({ from, to }) {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const angle = Math.atan2(dy, dx) * (180 / Math.PI);
  const len = Math.sqrt(dx * dx + dy * dy);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      className="absolute pointer-events-none"
      style={{
        left: from.x,
        top: from.y,
        width: len,
        height: 4,
        transformOrigin: '0 50%',
        transform: `rotate(${angle}deg)`,
      }}
    >
      <div className="w-full h-full relative">
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-yellow-400/80 to-yellow-500"
          style={{ borderRadius: 2 }}
          animate={{ scaleX: [0, 1] }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        />
        <motion.div
          className="absolute right-0 top-1/2"
          style={{ transform: 'translate(2px, -50%)' }}
          animate={{ x: [0, 4, 0] }}
          transition={{ repeat: Infinity, duration: 1, ease: 'easeInOut' }}
        >
          <div className="w-0 h-0 border-l-[10px] border-l-yellow-400 border-t-[6px] border-t-transparent border-b-[6px] border-b-transparent" />
        </motion.div>
      </div>
    </motion.div>
  );
}

function HighlightRing({ rect }) {
  if (!rect) return null;
  const pad = 4;
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className="absolute pointer-events-none rounded-xl border-2 border-yellow-400/70"
      style={{
        left: rect.left - pad,
        top: rect.top - pad,
        width: rect.width + pad * 2,
        height: rect.height + pad * 2,
      }}
    >
      <motion.div
        className="absolute inset-0 rounded-xl border-2 border-yellow-400/40"
        animate={{ scale: [1, 1.2, 1], opacity: [0.6, 0, 0.6] }}
        transition={{ repeat: Infinity, duration: 1.5 }}
      />
    </motion.div>
  );
}

export default function DashboardTour({ onClose }) {
  const [step, setStep] = useState(0);
  const [positions, setPositions] = useState([]);
  const current = TOUR_STEPS[step];

  const calcPositions = useCallback(() => {
    const pts = current.targets.map(t => getElementCenter(t.testId)).filter(Boolean);
    setPositions(pts);
  }, [current]);

  useEffect(() => {
    calcPositions();
    const onResize = () => calcPositions();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [calcPositions]);

  const advance = useCallback(() => {
    if (step < TOUR_STEPS.length - 1) setStep(s => s + 1);
    else { localStorage.setItem(STORAGE_KEY, '1'); onClose(); }
  }, [step, onClose]);

  const close = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, '1');
    onClose();
  }, [onClose]);

  // Velion position: bottom-right, above bottom nav
  const velionX = window.innerWidth - 80;
  const velionY = window.innerHeight - 160;

  return (
    <div className="fixed inset-0 z-[300]" data-testid="dashboard-tour">
      {/* Dark overlay - tap anywhere to advance */}
      <div className="absolute inset-0 bg-black/70" onClick={advance} />

      {/* Arrows from Velion to targets */}
      <AnimatePresence mode="wait">
        <motion.div key={step} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          {positions.map((pos, i) => (
            <React.Fragment key={i}>
              <Arrow from={{ x: velionX, y: velionY }} to={{ x: pos.x, y: pos.y }} />
              <HighlightRing rect={pos.rect} />
            </React.Fragment>
          ))}
        </motion.div>
      </AnimatePresence>

      {/* Velion character */}
      <motion.div
        className="absolute z-[310]"
        style={{ left: velionX - 40, top: velionY - 10, width: 90, height: 110 }}
        animate={{ y: [0, -6, 0] }}
        transition={{ repeat: Infinity, duration: 2.5, ease: 'easeInOut' }}
      >
        <img src="/velion-tutorial.png" alt="Velion" className="w-full h-full object-contain drop-shadow-[0_0_12px_rgba(234,179,8,0.4)]" />
      </motion.div>

      {/* Description card */}
      <motion.div
        key={step}
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute z-[310] left-3 right-3"
        style={{ bottom: 180 }}
        onClick={e => e.stopPropagation()}
      >
        <div className="bg-[#0d0d10]/95 backdrop-blur-md border border-yellow-500/20 rounded-2xl p-4 shadow-lg max-w-sm mx-auto">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] text-gray-500 font-mono">{step + 1}/{TOUR_STEPS.length}</span>
            <button onClick={close} className="text-gray-500 hover:text-white p-0.5" data-testid="tour-close-btn">
              <X className="w-4 h-4" />
            </button>
          </div>
          <h3 className="font-bold text-sm text-yellow-400 mb-0.5">{current.title}</h3>
          <p className="text-xs text-gray-300 leading-relaxed mb-3">{current.desc}</p>
          <div className="flex items-center justify-between">
            <button onClick={close} className="text-[11px] text-gray-500 hover:text-gray-300 transition-colors" data-testid="tour-skip-btn">
              Salta tour
            </button>
            <button
              onClick={advance}
              className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-yellow-500 text-black font-semibold hover:bg-yellow-400 transition-colors"
              data-testid="tour-next-btn"
            >
              {step === TOUR_STEPS.length - 1 ? 'Fine' : 'Avanti'} <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export { STORAGE_KEY as DASHBOARD_TOUR_KEY };
