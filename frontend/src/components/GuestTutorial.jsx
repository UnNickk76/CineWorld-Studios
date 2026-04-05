import React, { useState, useEffect, useContext, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Sparkles, X, ChevronRight, UserPlus, ArrowUp, ArrowDown } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';

// ─── STEP CONFIG ───
const STEPS = {
  0: {
    title: 'Benvenuto!',
    text: 'Sono Velion, il tuo assistente. Ti guider\u00f2 nella creazione del tuo primo film!',
    action: 'Iniziamo!',
    target: null,
  },
  1: {
    title: 'Produci il tuo primo film',
    text: 'Clicca su PRODUCI per iniziare!',
    // Multiple selectors: top nav + bottom nav + any matching element
    target: '[data-testid="nav-Produci Film"], [data-testid="nav-Produce Film"], [href="/create-film"], [data-testid="bottom-nav-produci"]',
    arrowDir: 'up',
  },
  2: {
    title: 'Crea il tuo film',
    text: 'Scegli il genere e dai un titolo al tuo primo film!',
    target: null,
  },
  3: {
    title: 'Coming Soon avviato!',
    text: 'Il tuo film \u00e8 in fase Coming Soon. L\'hype sta crescendo!',
    target: null,
  },
  4: {
    title: 'Velocizzazione gratuita!',
    text: 'Hai 3 velocizzazioni GRATIS! Usale per accelerare il timer.',
    target: '[data-testid^="speedup-"]',
    arrowDir: 'up',
  },
  5: {
    title: 'Ottimo lavoro!',
    text: 'Guarda come evolve il tuo progetto. Ogni fase ti avvicina al successo!',
    target: null,
  },
  6: {
    title: 'Sei pronto!',
    text: 'Hai creato il tuo primo film! Vuoi salvare i progressi?',
    action: 'convert',
    target: null,
  },
};

// ─── INLINE KEYFRAMES ───
const injectStyles = () => {
  if (document.getElementById('tutorial-styles')) return;
  const s = document.createElement('style');
  s.id = 'tutorial-styles';
  s.textContent = `
    @keyframes tutGlow {
      0%, 100% { box-shadow: 0 0 10px rgba(255,215,0,0.7), 0 0 25px rgba(255,215,0,0.4), 0 0 50px rgba(255,215,0,0.2); transform: scale(1); }
      50% { box-shadow: 0 0 15px rgba(255,215,0,1), 0 0 35px rgba(255,215,0,0.6), 0 0 70px rgba(255,215,0,0.3); transform: scale(1.04); }
    }
    @keyframes tutArrowBounce {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
    }
    .tut-target-active {
      position: relative !important;
      z-index: 110 !important;
      pointer-events: auto !important;
      animation: tutGlow 1.5s ease-in-out infinite !important;
      border-radius: 12px !important;
    }
  `;
  document.head.appendChild(s);
};

export function GuestTutorial() {
  const { user, api, refreshUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  const [step, setStep] = useState(user?.tutorial_step || 0);
  const [visible, setVisible] = useState(true);
  const [minimized, setMinimized] = useState(false);
  const [showConvert, setShowConvert] = useState(false);
  const [convertForm, setConvertForm] = useState({ email: '', password: '', nickname: '' });
  const [converting, setConverting] = useState(false);
  const [targetRect, setTargetRect] = useState(null);
  const targetElRef = useRef(null);

  const isActive = user?.is_guest && !user?.tutorial_completed && visible;
  const msg = STEPS[step] || STEPS[0];
  const showOverlay = isActive && step >= 1 && step <= 5 && !minimized && msg.target;

  // Inject CSS once
  useEffect(() => { injectStyles(); return () => { const s = document.getElementById('tutorial-styles'); if (s) s.remove(); }; }, []);

  // Sync step
  useEffect(() => { if (user?.tutorial_step !== undefined) setStep(user.tutorial_step); }, [user?.tutorial_step]);

  // Auto-advance on navigation
  // eslint-disable-next-line
  useEffect(() => {
    if (!isActive) return;
    if (step === 1 && location.pathname === '/create-film') {
      api.post('/auth/tutorial-step', { step: 2 }).then(() => setStep(2)).catch(() => {});
    }
  }, [location.pathname, step, isActive, api]);

  // ─── SPOTLIGHT: find + glow + scroll ───
  // eslint-disable-next-line
  useEffect(() => {
    // Cleanup
    document.querySelectorAll('.tut-target-active').forEach(el => el.classList.remove('tut-target-active'));
    setTargetRect(null);
    targetElRef.current = null;

    if (!isActive || !msg.target || minimized) return;

    const findAndHighlight = () => {
      const selectors = msg.target.split(',').map(s => s.trim());
      let el = null;
      for (const sel of selectors) {
        el = document.querySelector(sel);
        if (el && el.offsetParent !== null) break; // visible element
        el = null;
      }
      if (!el) return;

      targetElRef.current = el;
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });

      setTimeout(() => {
        el.classList.add('tut-target-active');
        const rect = el.getBoundingClientRect();
        setTargetRect({ top: rect.top, left: rect.left, width: rect.width, height: rect.height });
        if (navigator.vibrate) navigator.vibrate(30);
      }, 300);
    };

    // Delay to let page render
    const t1 = setTimeout(findAndHighlight, 500);
    const t2 = setTimeout(findAndHighlight, 1500); // retry
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [step, minimized, msg.target, isActive]);

  // Don't show if not guest or tutorial completed
  if (!isActive) return null;

  // ─── LOGIC ───
  const advanceStep = async (newStep) => {
    try {
      await api.post('/auth/tutorial-step', { step: newStep });
      setStep(newStep);
      if (newStep >= 6) setShowConvert(true);
    } catch {}
  };

  const skipTutorial = async () => {
    document.querySelectorAll('.tut-target-active').forEach(el => el.classList.remove('tut-target-active'));
    try {
      await api.post('/auth/tutorial-skip');
      refreshUser();
      toast.success('Tutorial saltato. Buon gioco!');
    } catch {}
  };

  const handleConvert = async () => {
    if (!convertForm.email || convertForm.password.length < 6) { toast.error('Compila email e password (min 6 caratteri)'); return; }
    setConverting(true);
    try {
      const res = await api.post('/auth/convert', convertForm);
      localStorage.removeItem('cineworld_guest_start');
      if (res.data.access_token) localStorage.setItem('cineworld_token', res.data.access_token);
      refreshUser();
      toast.success('Account registrato!');
      setShowConvert(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally { setConverting(false); }
  };

  // ═══════════ RENDER ═══════════

  // Conversion modal
  if (showConvert) {
    return (
      <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm" data-testid="guest-tutorial-convert">
        <motion.div initial={{ scale: 0.85, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', damping: 20, stiffness: 300 }}
          className="bg-[#0d0d0f] border border-yellow-500/30 rounded-2xl max-w-sm w-[90%] mx-4 overflow-hidden">
          <div className="bg-gradient-to-b from-yellow-500/20 to-transparent p-5 text-center">
            <motion.div animate={{ rotate: [0, 10, -10, 0] }} transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              className="w-14 h-14 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-3">
              <Sparkles className="w-7 h-7 text-yellow-400" />
            </motion.div>
            <h3 className="font-['Bebas_Neue'] text-xl text-yellow-300">Hai creato il tuo primo film!</h3>
            <p className="text-xs text-gray-400 mt-1">Vuoi salvare i tuoi progressi?</p>
          </div>
          <div className="px-5 pb-5 space-y-2.5">
            <Input placeholder="Email" type="email" value={convertForm.email} onChange={e => setConvertForm(p => ({...p, email: e.target.value}))} className="h-9 bg-white/5 border-white/10 text-sm" data-testid="tutorial-convert-email" />
            <Input placeholder="Password (min 6)" type="password" value={convertForm.password} onChange={e => setConvertForm(p => ({...p, password: e.target.value}))} className="h-9 bg-white/5 border-white/10 text-sm" data-testid="tutorial-convert-password" />
            <Input placeholder="Nickname" value={convertForm.nickname} onChange={e => setConvertForm(p => ({...p, nickname: e.target.value}))} className="h-9 bg-white/5 border-white/10 text-sm" data-testid="tutorial-convert-nickname" />
            <Button className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold h-9" disabled={converting || !convertForm.email || convertForm.password.length < 6} onClick={handleConvert} data-testid="tutorial-convert-submit">
              <UserPlus className="w-4 h-4 mr-2" />{converting ? 'Registrazione...' : 'Registrati'}
            </Button>
            <button className="w-full text-center text-xs text-gray-500 hover:text-gray-300 py-1" onClick={() => { setShowConvert(false); skipTutorial(); }} data-testid="tutorial-convert-skip">Continua come ospite</button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Minimized
  if (minimized) {
    return (
      <motion.button initial={{ scale: 0 }} animate={{ scale: 1 }} whileTap={{ scale: 0.9 }}
        className="fixed bottom-24 right-3 z-[120] w-14 h-14 rounded-full bg-gradient-to-br from-yellow-500/40 to-amber-600/30 border-2 border-yellow-500/50 flex items-center justify-center"
        style={{ boxShadow: '0 0 20px rgba(255,215,0,0.4), 0 0 40px rgba(255,215,0,0.15)' }}
        onClick={() => setMinimized(false)} data-testid="tutorial-velion-minimized">
        <span className="text-yellow-400 font-bold text-xl">V</span>
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full animate-pulse text-[8px] font-bold flex items-center justify-center text-white">{step + 1}</span>
      </motion.button>
    );
  }

  return (
    <>
      {/* ───── OVERLAY (step 1-5 with target) ───── */}
      <AnimatePresence>
        {showOverlay && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}
            className="fixed inset-0 z-[100]"
            style={{ background: 'rgba(0,0,0,0.7)', pointerEvents: 'auto' }}
            onClick={e => e.stopPropagation()}
            data-testid="tutorial-overlay"
          />
        )}
      </AnimatePresence>

      {/* ───── ANIMATED ARROW pointing from Velion to target ───── */}
      {targetRect && !minimized && (() => {
        const velionEl = document.querySelector('[data-testid="tutorial-velion-panel"]');
        const velionRect = velionEl?.getBoundingClientRect();
        const targetBelow = targetRect.top > (velionRect?.top || 0);
        // Position arrow just above the target
        const arrowTop = targetBelow
          ? targetRect.top - 36
          : targetRect.top + targetRect.height + 4;
        const arrowLeft = targetRect.left + targetRect.width / 2 - 16;
        return (
          <div
            className="fixed z-[130] pointer-events-none flex flex-col items-center"
            style={{
              top: Math.max(0, Math.min(arrowTop, window.innerHeight - 36)),
              left: arrowLeft,
              animation: 'tutArrowBounce 1s ease-in-out infinite',
              filter: 'drop-shadow(0 0 12px rgba(255,215,0,0.9))',
            }}
            data-testid="tutorial-arrow"
          >
            {targetBelow
              ? <ArrowDown className="w-8 h-8 text-yellow-400" strokeWidth={3} />
              : <ArrowUp className="w-8 h-8 text-yellow-400" strokeWidth={3} />
            }
          </div>
        );
      })()}

      {/* ───── VELION GUIDE PANEL ───── */}
      <motion.div
        initial={{ y: 60, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', damping: 22, stiffness: 200, delay: 0.1 }}
        className="fixed left-2 right-2 z-[120]"
        style={{ bottom: 'calc(env(safe-area-inset-bottom, 0px) + 70px)' }}
        data-testid="tutorial-velion-panel"
      >
        <div
          className="bg-[#0a0a0c]/95 backdrop-blur-lg border border-yellow-500/40 rounded-2xl overflow-hidden"
          style={{ boxShadow: '0 0 25px rgba(255,215,0,0.25), 0 -4px 30px rgba(0,0,0,0.8)' }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 bg-gradient-to-r from-yellow-500/20 via-amber-500/10 to-transparent border-b border-yellow-500/20">
            <div className="flex items-center gap-2.5">
              <div
                className="w-9 h-9 rounded-full bg-gradient-to-br from-yellow-400 to-amber-600 flex items-center justify-center shadow-lg"
                style={{ boxShadow: '0 0 12px rgba(255,215,0,0.5)' }}
              >
                <span className="text-black font-black text-sm">V</span>
              </div>
              <div>
                <span className="text-yellow-400 font-['Bebas_Neue'] text-base tracking-wider leading-none">VELION</span>
                <span className="ml-2 text-[9px] text-yellow-500/70 bg-yellow-500/10 px-1.5 py-0.5 rounded-full font-bold">{step + 1}/7</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => setMinimized(true)} className="w-7 h-7 flex items-center justify-center text-gray-500 hover:text-yellow-400 rounded-lg transition-colors">
                <ChevronRight className="w-4 h-4" />
              </button>
              <button onClick={skipTutorial} className="w-7 h-7 flex items-center justify-center text-gray-500 hover:text-red-400 rounded-lg transition-colors" data-testid="tutorial-skip-btn">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="px-3.5 py-3">
            <AnimatePresence mode="wait">
              <motion.div key={step} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}>
                <p className="text-yellow-300 font-bold text-[15px] mb-0.5">{msg.title}</p>
                <p className="text-gray-300 text-xs leading-relaxed">{msg.text}</p>
              </motion.div>
            </AnimatePresence>

            {/* Step 0 action button */}
            {step === 0 && msg.action && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                <Button
                  className="mt-3 w-full bg-gradient-to-r from-yellow-500 to-amber-500 text-black hover:from-yellow-400 hover:to-amber-400 h-10 text-sm font-bold shadow-lg shadow-yellow-500/25 rounded-xl"
                  onClick={() => advanceStep(1)}
                  data-testid="tutorial-start-btn"
                >
                  <Camera className="w-4 h-4 mr-2" />
                  {msg.action}
                </Button>
              </motion.div>
            )}

            {/* Progress bar */}
            <div className="flex items-center gap-1 mt-3">
              {[0,1,2,3,4,5,6].map(s => (
                <div key={s} className={`h-1.5 rounded-full transition-all duration-500 ${
                  s === step ? 'flex-[2.5] bg-gradient-to-r from-yellow-400 to-amber-500' : s < step ? 'flex-1 bg-yellow-500/40' : 'flex-1 bg-white/8'
                }`} />
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </>
  );
}
