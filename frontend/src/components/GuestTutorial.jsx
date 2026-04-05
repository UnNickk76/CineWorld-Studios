import React, { useState, useEffect, useContext, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Sparkles, X, ChevronRight, UserPlus, ChevronDown } from 'lucide-react';
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
    text: 'Clicca su PRODUCI FILM nella barra in alto per iniziare.',
    target: '[data-testid="nav-Produci Film"], [data-testid="nav-Produce Film"], [href="/create-film"]',
  },
  2: {
    title: 'Scegli il tipo',
    text: 'Perfetto! Ora segui la procedura per creare il tuo primo film. Scegli genere e titolo!',
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
    target: '[data-testid="speedup-btn"]',
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

// ─── INLINE STYLES (no external CSS needed) ───
const glowKeyframes = `
@keyframes tutorialPulseGlow {
  0%, 100% { box-shadow: 0 0 8px rgba(255,215,0,0.6), 0 0 20px rgba(255,215,0,0.3), 0 0 40px rgba(255,215,0,0.15); transform: scale(1); }
  50% { box-shadow: 0 0 12px rgba(255,215,0,0.9), 0 0 30px rgba(255,215,0,0.5), 0 0 60px rgba(255,215,0,0.25); transform: scale(1.03); }
}
@keyframes tutorialFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(6px); }
}
.tutorial-target-glow {
  position: relative;
  z-index: 96 !important;
  pointer-events: auto !important;
  animation: tutorialPulseGlow 1.5s ease-in-out infinite !important;
  border-radius: 12px;
}
`;

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
  const [transitioning, setTransitioning] = useState(false);
  const arrowRef = useRef(null);
  const styleRef = useRef(null);

  // Inject keyframes once
  useEffect(() => {
    if (!styleRef.current) {
      const s = document.createElement('style');
      s.textContent = glowKeyframes;
      document.head.appendChild(s);
      styleRef.current = s;
    }
    return () => { if (styleRef.current) { styleRef.current.remove(); styleRef.current = null; } };
  }, []);

  // Sync step from user
  useEffect(() => {
    if (user?.tutorial_step !== undefined) setStep(user.tutorial_step);
  }, [user?.tutorial_step]);

  // ─── SPOTLIGHT: find target, scroll, glow ───
  const updateSpotlight = useCallback(() => {
    // Cleanup previous glow
    document.querySelectorAll('.tutorial-target-glow').forEach(el => el.classList.remove('tutorial-target-glow'));

    const cfg = STEPS[step];
    if (!cfg?.target || minimized) { setTargetRect(null); return; }

    // Try each selector
    const selectors = cfg.target.split(',').map(s => s.trim());
    let el = null;
    for (const sel of selectors) {
      el = document.querySelector(sel);
      if (el) break;
    }

    if (!el) { setTargetRect(null); return; }

    // Scroll into view
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Apply glow after scroll settles
    setTimeout(() => {
      el.classList.add('tutorial-target-glow');
      const rect = el.getBoundingClientRect();
      setTargetRect({ top: rect.top, left: rect.left, width: rect.width, height: rect.height });

      // Vibrate on mobile
      if (navigator.vibrate) navigator.vibrate(30);
    }, 250);
  }, [step, minimized]);

  useEffect(() => {
    setTransitioning(true);
    const t = setTimeout(() => { setTransitioning(false); updateSpotlight(); }, 300);
    return () => clearTimeout(t);
  }, [step, updateSpotlight]);

  // Re-calc on resize/scroll
  useEffect(() => {
    const onUpdate = () => updateSpotlight();
    window.addEventListener('resize', onUpdate);
    window.addEventListener('scroll', onUpdate, true);
    return () => { window.removeEventListener('resize', onUpdate); window.removeEventListener('scroll', onUpdate, true); };
  }, [updateSpotlight]);

  // Don't show if not guest or tutorial completed
  if (!user?.is_guest || user?.tutorial_completed) return null;
  if (!visible) return null;

  const msg = STEPS[step] || STEPS[0];
  const hasTarget = !!msg.target && !!targetRect;
  const showOverlay = step >= 1 && step <= 5 && !minimized;

  // ─── LOGIC (unchanged) ───
  const advanceStep = async (newStep) => {
    try {
      await api.post('/auth/tutorial-step', { step: newStep });
      setStep(newStep);
      if (newStep >= 6) setShowConvert(true);
    } catch {}
  };

  const skipTutorial = async () => {
    document.querySelectorAll('.tutorial-target-glow').forEach(el => el.classList.remove('tutorial-target-glow'));
    try {
      await api.post('/auth/tutorial-skip');
      refreshUser();
      toast.success('Tutorial saltato. Buon gioco!');
    } catch {}
  };

  const handleConvert = async () => {
    if (!convertForm.email || convertForm.password.length < 6) {
      toast.error('Compila email e password (min 6 caratteri)');
      return;
    }
    setConverting(true);
    try {
      const res = await api.post('/auth/convert', convertForm);
      localStorage.removeItem('cineworld_guest_start');
      if (res.data.access_token) localStorage.setItem('cineworld_token', res.data.access_token);
      refreshUser();
      toast.success('Account registrato! I tuoi progressi sono salvi');
      setShowConvert(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella registrazione');
    } finally {
      setConverting(false);
    }
  };

  // Auto-advance on navigation
  useEffect(() => {
    if (step === 1 && location.pathname === '/create-film') advanceStep(2);
  }, [location.pathname, step]);

  // ═══════════ RENDER ═══════════

  // Conversion modal at step 6
  if (showConvert) {
    return (
      <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm" data-testid="guest-tutorial-convert">
        <motion.div
          initial={{ scale: 0.85, opacity: 0, y: 30 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          transition={{ type: 'spring', damping: 20, stiffness: 300 }}
          className="bg-[#0d0d0f] border border-yellow-500/30 rounded-2xl max-w-sm w-[90%] mx-4 overflow-hidden"
        >
          <div className="bg-gradient-to-b from-yellow-500/20 to-transparent p-5 text-center">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0], scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              className="w-14 h-14 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-3"
            >
              <Sparkles className="w-7 h-7 text-yellow-400" />
            </motion.div>
            <h3 className="font-['Bebas_Neue'] text-xl text-yellow-300">Hai creato il tuo primo film!</h3>
            <p className="text-xs text-gray-400 mt-1">Vuoi salvare i tuoi progressi e continuare?</p>
          </div>
          <div className="px-5 pb-5 space-y-2.5">
            <Input placeholder="Email" type="email" value={convertForm.email} onChange={e => setConvertForm(p => ({...p, email: e.target.value}))} className="h-9 bg-white/5 border-white/10 text-sm" data-testid="tutorial-convert-email" />
            <Input placeholder="Password (min 6 caratteri)" type="password" value={convertForm.password} onChange={e => setConvertForm(p => ({...p, password: e.target.value}))} className="h-9 bg-white/5 border-white/10 text-sm" data-testid="tutorial-convert-password" />
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

  // Minimized Velion
  if (minimized) {
    return (
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className="fixed bottom-20 right-3 z-[100] w-12 h-12 rounded-full bg-gradient-to-br from-yellow-500/30 to-amber-600/20 border border-yellow-500/40 flex items-center justify-center shadow-lg shadow-yellow-500/20"
        onClick={() => setMinimized(false)}
        data-testid="tutorial-velion-minimized"
      >
        <span className="text-yellow-400 font-bold text-lg">V</span>
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse" />
      </motion.button>
    );
  }

  // ─── MAIN TUTORIAL RENDER ───
  return (
    <>
      {/* ───── OVERLAY SCURO con pointer-events bloccati ───── */}
      <AnimatePresence>
        {showOverlay && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-[90] pointer-events-auto"
            style={{ background: 'rgba(0,0,0,0.75)' }}
            data-testid="tutorial-overlay"
            onClick={e => e.stopPropagation()}
          />
        )}
      </AnimatePresence>

      {/* ───── SPOTLIGHT HOLE + GLOW RING ───── */}
      {hasTarget && !transitioning && (
        <div
          className="fixed z-[95] pointer-events-none rounded-xl"
          style={{
            top: targetRect.top - 6,
            left: targetRect.left - 6,
            width: targetRect.width + 12,
            height: targetRect.height + 12,
            boxShadow: '0 0 0 9999px rgba(0,0,0,0.75)',
          }}
          data-testid="tutorial-spotlight"
        >
          {/* Animated glow ring */}
          <div
            className="absolute inset-0 rounded-xl"
            style={{
              animation: 'tutorialPulseGlow 1.5s ease-in-out infinite',
              boxShadow: '0 0 12px rgba(255,215,0,0.8), 0 0 30px rgba(255,215,0,0.4), inset 0 0 8px rgba(255,215,0,0.2)',
              border: '2px solid rgba(255,215,0,0.6)',
            }}
          />
        </div>
      )}

      {/* ───── ANIMATED ARROW ───── */}
      {hasTarget && !transitioning && (
        <div
          ref={arrowRef}
          className="fixed z-[96] pointer-events-none"
          style={{
            top: targetRect.top + targetRect.height + 8,
            left: targetRect.left + targetRect.width / 2 - 14,
            animation: 'tutorialFloat 1.2s ease-in-out infinite',
            filter: 'drop-shadow(0 0 8px rgba(255,215,0,0.7))',
          }}
          data-testid="tutorial-arrow"
        >
          <ChevronDown className="w-7 h-7 text-yellow-400" strokeWidth={3} style={{ transform: 'rotate(180deg)' }} />
        </div>
      )}

      {/* ───── VELION PANEL ───── */}
      <motion.div
        initial={{ y: 80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200, delay: 0.15 }}
        className="fixed bottom-20 left-3 right-3 z-[100] sm:left-auto sm:right-4 sm:max-w-xs"
        data-testid="tutorial-velion-panel"
      >
        <div className="bg-[#0d0d0f]/95 backdrop-blur-md border border-yellow-500/25 rounded-2xl shadow-2xl shadow-yellow-500/10 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 bg-gradient-to-r from-yellow-500/15 to-amber-500/5 border-b border-yellow-500/15">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-yellow-400 to-amber-600 flex items-center justify-center shadow-md shadow-yellow-500/30">
                <span className="text-black font-bold text-xs">V</span>
              </div>
              <span className="text-yellow-400 font-['Bebas_Neue'] text-sm tracking-wider">VELION</span>
              <span className="text-[8px] text-yellow-500/60 bg-yellow-500/10 px-1.5 py-0.5 rounded-full font-medium">{step + 1}/7</span>
            </div>
            <div className="flex items-center gap-0.5">
              <button onClick={() => setMinimized(true)} className="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-yellow-400 rounded transition-colors">
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
              <button onClick={skipTutorial} className="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-red-400 rounded transition-colors" data-testid="tutorial-skip-btn">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-3">
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={{ opacity: 0, x: 15 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -15 }}
                transition={{ duration: 0.25 }}
              >
                <p className="text-yellow-300 font-semibold text-sm mb-0.5">{msg.title}</p>
                <p className="text-gray-400 text-xs leading-relaxed">{msg.text}</p>
              </motion.div>
            </AnimatePresence>

            {/* Action button for step 0 */}
            {step === 0 && msg.action && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
                <Button
                  className="mt-3 w-full bg-gradient-to-r from-yellow-500 to-amber-500 text-black hover:from-yellow-400 hover:to-amber-400 h-8 text-xs font-bold shadow-lg shadow-yellow-500/20"
                  onClick={() => advanceStep(1)}
                  data-testid="tutorial-start-btn"
                >
                  <Camera className="w-3.5 h-3.5 mr-1.5" />
                  {msg.action}
                </Button>
              </motion.div>
            )}

            {/* Progress bar */}
            <div className="flex items-center gap-1 mt-3">
              {[0,1,2,3,4,5,6].map(s => (
                <div
                  key={s}
                  className={`h-1 rounded-full transition-all duration-500 ${
                    s === step ? 'flex-[2] bg-yellow-400' : s < step ? 'flex-1 bg-yellow-500/40' : 'flex-1 bg-white/5'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </>
  );
}
