import React, { useState, useEffect, useContext, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Sparkles, X, UserPlus, ArrowDown, ArrowUp } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';

const STEPS = {
  0: { title: 'Benvenuto!', text: 'Sono Velion, il tuo assistente. Ti guider\u00f2 nella creazione del tuo primo film!', action: 'Iniziamo!', target: null, velionSide: 'right', velionSize: 150 },
  1: { title: 'Produci il tuo primo film', text: 'Clicca su PRODUCI per iniziare!', target: '[data-testid="nav-Produci Film"], [data-testid="nav-Produce Film"], [href="/create-film"], [data-testid="bottom-nav-produci"]', velionSide: 'left', velionSize: 110 },
  2: { title: 'Crea il tuo film', text: 'Scegli il genere e dai un titolo al tuo primo film!', target: null, velionSide: 'right', velionSize: 130 },
  3: { title: 'Coming Soon avviato!', text: 'Il tuo film \u00e8 in fase Coming Soon. L\'hype sta crescendo!', target: null, velionSide: 'left', velionSize: 130 },
  4: { title: 'Velocizzazione gratuita!', text: 'Hai 3 velocizzazioni GRATIS! Usale per accelerare il timer.', target: '[data-testid^="speedup-"]', velionSide: 'left', velionSize: 110 },
  5: { title: 'Ottimo lavoro!', text: 'Guarda come evolve il tuo progetto. Ogni fase ti avvicina al successo!', target: null, velionSide: 'left', velionSize: 140 },
  6: { title: 'Sei pronto!', text: 'Hai creato il tuo primo film! Vuoi salvare i progressi?', action: 'convert', target: null, velionSide: 'right', velionSize: 150 },
};

const VELION_ANIMS = [
  { animate: { y: [0, -10, 0] }, transition: { duration: 2.5, repeat: Infinity, ease: 'easeInOut' } },
  { animate: { y: [0, -6, 0], rotate: [0, 3, -3, 0] }, transition: { duration: 2.8, repeat: Infinity } },
  { animate: { scale: [1, 1.05, 1], x: [0, -4, 0] }, transition: { duration: 3, repeat: Infinity } },
  { animate: { y: [0, -12, 0], scale: [1, 1.06, 1] }, transition: { duration: 2, repeat: Infinity } },
  { animate: { rotate: [0, -4, 4, 0] }, transition: { duration: 2.2, repeat: Infinity } },
  { animate: { y: [0, -14, 0], rotate: [0, 5, -5, 0] }, transition: { duration: 2, repeat: Infinity } },
  { animate: { scale: [1, 1.04, 1], y: [0, -6, 0] }, transition: { duration: 2.5, repeat: Infinity } },
];

const injectStyles = () => {
  if (document.getElementById('tutorial-styles')) return;
  const s = document.createElement('style');
  s.id = 'tutorial-styles';
  s.textContent = `
    @keyframes tutGlow { 0%,100%{box-shadow:0 0 10px rgba(255,215,0,.7),0 0 25px rgba(255,215,0,.4)}50%{box-shadow:0 0 20px rgba(255,215,0,1),0 0 40px rgba(255,215,0,.6),0 0 60px rgba(255,215,0,.3)} }
    @keyframes tutArrowBounce { 0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)} }
    @keyframes velionFloat { 0%,100%{filter:drop-shadow(0 0 15px rgba(0,180,255,.4)) brightness(1.15)}50%{filter:drop-shadow(0 0 30px rgba(0,180,255,.7)) brightness(1.35)} }
    .tut-target-active { position:relative!important; z-index:110!important; pointer-events:auto!important; animation:tutGlow 1.5s ease-in-out infinite!important; border-radius:12px!important }
    .tut-parent-lifted { z-index:105!important }
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
  const hasTarget = !!msg.target;

  useEffect(() => { injectStyles(); return () => { const s = document.getElementById('tutorial-styles'); if (s) s.remove(); }; }, []);
  useEffect(() => { if (user?.tutorial_step !== undefined) setStep(user.tutorial_step); }, [user?.tutorial_step]);

  // eslint-disable-next-line
  useEffect(() => {
    if (!isActive) return;
    if (step === 1 && location.pathname === '/create-film') {
      api.post('/auth/tutorial-step', { step: 2 }).then(() => setStep(2)).catch(() => {});
    }
  }, [location.pathname, step, isActive, api]);

  // eslint-disable-next-line
  useEffect(() => {
    document.querySelectorAll('.tut-target-active').forEach(el => el.classList.remove('tut-target-active'));
    document.querySelectorAll('.tut-parent-lifted').forEach(el => el.classList.remove('tut-parent-lifted'));
    setTargetRect(null);
    targetElRef.current = null;
    if (!isActive || !msg.target || minimized) return;

    const findAndHighlight = () => {
      const selectors = msg.target.split(',').map(s => s.trim());
      let el = null;
      for (const sel of selectors) { el = document.querySelector(sel); if (el && el.offsetParent !== null) break; el = null; }
      if (!el) return;
      targetElRef.current = el;
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setTimeout(() => {
        el.classList.add('tut-target-active');
        let parent = el.parentElement;
        while (parent && parent !== document.body) {
          const st = getComputedStyle(parent);
          if (st.position === 'fixed' || st.position === 'absolute' || st.position === 'sticky') parent.classList.add('tut-parent-lifted');
          parent = parent.parentElement;
        }
        const rect = el.getBoundingClientRect();
        setTargetRect({ top: rect.top, left: rect.left, width: rect.width, height: rect.height });
        if (navigator.vibrate) navigator.vibrate(30);
      }, 300);
    };
    const t1 = setTimeout(findAndHighlight, 500);
    const t2 = setTimeout(findAndHighlight, 1500);
    return () => { clearTimeout(t1); clearTimeout(t2); document.querySelectorAll('.tut-parent-lifted').forEach(el => el.classList.remove('tut-parent-lifted')); };
  }, [step, minimized, msg.target, isActive]);

  if (!isActive) return null;

  const advanceStep = async (newStep) => {
    try { await api.post('/auth/tutorial-step', { step: newStep }); setStep(newStep); if (newStep >= 6) setShowConvert(true); } catch {}
  };
  const skipTutorial = async () => {
    document.querySelectorAll('.tut-target-active').forEach(el => el.classList.remove('tut-target-active'));
    document.querySelectorAll('.tut-parent-lifted').forEach(el => el.classList.remove('tut-parent-lifted'));
    try { await api.post('/auth/tutorial-skip'); refreshUser(); toast.success('Tutorial saltato. Buon gioco!'); } catch {}
  };
  const handleConvert = async () => {
    if (!convertForm.email || convertForm.password.length < 6) { toast.error('Compila email e password (min 6 caratteri)'); return; }
    setConverting(true);
    try {
      const res = await api.post('/auth/convert', convertForm);
      localStorage.removeItem('cineworld_guest_start');
      if (res.data.access_token) localStorage.setItem('cineworld_token', res.data.access_token);
      refreshUser(); toast.success('Account registrato!'); setShowConvert(false);
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); } finally { setConverting(false); }
  };

  const velionAnim = VELION_ANIMS[step] || VELION_ANIMS[0];
  const isRight = msg.velionSide === 'right';

  // ═══════ CONVERSION MODAL with animated Velion ═══════
  if (showConvert) {
    return (
      <div className="fixed inset-0 z-[200] flex items-end sm:items-center justify-center bg-black/80 backdrop-blur-sm pb-4 sm:pb-0" data-testid="guest-tutorial-convert">
        <motion.div initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ type: 'spring', damping: 20, stiffness: 200 }}
          className="bg-[#0d0d0f] border border-cyan-500/20 rounded-2xl max-w-sm w-[92%] mx-4 overflow-hidden relative">
          {/* Velion character on the right */}
          <motion.div
            className="absolute -top-2 -right-3 w-28 h-28 pointer-events-none z-10"
            animate={{ y: [0, -8, 0], rotate: [0, 5, -5, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          >
            <img src="/velion-tutorial.png" alt="Velion" className="w-full h-full object-contain" style={{ animation: 'velionFloat 2.5s ease-in-out infinite' }} />
          </motion.div>

          <div className="bg-gradient-to-br from-cyan-500/15 via-transparent to-yellow-500/10 p-4 pr-28">
            <motion.div initial={{ scale: 0.8 }} animate={{ scale: 1 }} transition={{ delay: 0.2 }}>
              <div className="flex items-center gap-1.5 mb-1">
                <Sparkles className="w-4 h-4 text-yellow-400" />
                <span className="text-cyan-400 font-['Bebas_Neue'] text-sm tracking-wider">VELION</span>
              </div>
              <h3 className="font-bold text-base text-white">Ti sta piacendo il gioco?</h3>
              <p className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">Salva i progressi e continua la tua avventura!</p>
            </motion.div>
          </div>
          <div className="px-4 pb-4 pt-2 space-y-2">
            <Input placeholder="Email" type="email" value={convertForm.email} onChange={e => setConvertForm(p => ({...p, email: e.target.value}))} className="h-9 bg-white/5 border-white/10 text-sm" data-testid="tutorial-convert-email" />
            <Input placeholder="Password (min 6)" type="password" value={convertForm.password} onChange={e => setConvertForm(p => ({...p, password: e.target.value}))} className="h-9 bg-white/5 border-white/10 text-sm" data-testid="tutorial-convert-password" />
            <Input placeholder="Nickname" value={convertForm.nickname} onChange={e => setConvertForm(p => ({...p, nickname: e.target.value}))} className="h-9 bg-white/5 border-white/10 text-sm" data-testid="tutorial-convert-nickname" />
            <Button className="w-full bg-gradient-to-r from-yellow-500 to-amber-500 text-black hover:from-yellow-400 hover:to-amber-400 font-bold h-9 rounded-xl" disabled={converting || !convertForm.email || convertForm.password.length < 6} onClick={handleConvert} data-testid="tutorial-convert-submit">
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
        className="fixed bottom-24 right-3 z-[120] w-16 h-16 rounded-full border-2 border-cyan-500/40 flex items-center justify-center overflow-hidden"
        style={{ boxShadow: '0 0 25px rgba(0,180,255,0.5)', background: 'radial-gradient(circle, rgba(0,20,50,0.95) 30%, #0a0a0c 100%)' }}
        onClick={() => setMinimized(false)} data-testid="tutorial-velion-minimized">
        <img src="/velion-tutorial.png" alt="Velion" className="w-14 h-14 object-cover" style={{ animation: 'velionFloat 2s ease-in-out infinite' }} />
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full animate-pulse text-[8px] font-bold flex items-center justify-center text-white">{step + 1}</span>
      </motion.button>
    );
  }

  // ═══════ TARGET STEPS (1, 4): Panel at TOP so it doesn't block interaction area ═══════
  if (hasTarget) {
    return (
      <>
        {/* OVERLAY */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="fixed inset-0 z-[100] pointer-events-none"
          style={{ background: 'rgba(0,0,0,0.7)' }}
          data-testid="tutorial-overlay"
        />

        {/* ARROW */}
        {targetRect && (() => {
          const arrowTop = targetRect.top - 36;
          const arrowLeft = targetRect.left + targetRect.width / 2 - 16;
          return (
            <div className="fixed z-[130] pointer-events-none" style={{ top: Math.max(0, Math.min(arrowTop, window.innerHeight - 36)), left: arrowLeft, animation: 'tutArrowBounce 1s ease-in-out infinite', filter: 'drop-shadow(0 0 12px rgba(255,215,0,.9))' }} data-testid="tutorial-arrow">
              <ArrowDown className="w-8 h-8 text-yellow-400" strokeWidth={3} />
            </div>
          );
        })()}

        {/* TOP PANEL: Compact speech + Velion character */}
        <motion.div
          initial={{ y: -60, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: 'spring', damping: 20, stiffness: 200 }}
          className="fixed top-0 left-0 right-0 z-[120] pointer-events-none"
          style={{ paddingTop: 'env(safe-area-inset-top, 0px)' }}
          data-testid="tutorial-velion-panel"
        >
          <div className="relative mx-2 mt-1">
            {/* Speech bubble */}
            <div className="pointer-events-auto bg-[#0a0a0c]/95 backdrop-blur-lg border border-yellow-500/25 rounded-2xl overflow-hidden" style={{ boxShadow: '0 4px 30px rgba(0,0,0,0.6)' }}>
              <div className="flex items-center gap-2.5 px-3 py-2.5">
                {/* Small Velion avatar */}
                <motion.div className="flex-shrink-0 w-12 h-12 relative" {...velionAnim}>
                  <img src="/velion-tutorial.png" alt="Velion" className="w-full h-full object-contain" style={{ animation: 'velionFloat 2.5s ease-in-out infinite' }} />
                </motion.div>
                {/* Text */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-cyan-400 font-['Bebas_Neue'] text-xs tracking-widest">VELION</span>
                    <span className="text-[7px] text-cyan-500/50 bg-cyan-500/10 px-1 py-0.5 rounded-full font-bold">{step + 1}/7</span>
                  </div>
                  <p className="text-white font-bold text-[13px] leading-tight">{msg.title}</p>
                  <p className="text-gray-400 text-[10px] leading-tight">{msg.text}</p>
                </div>
                {/* Controls */}
                <div className="flex flex-col items-center gap-0.5 flex-shrink-0">
                  <button onClick={() => setMinimized(true)} className="w-5 h-5 flex items-center justify-center text-gray-600 hover:text-cyan-400 text-[10px]">_</button>
                  <button onClick={skipTutorial} className="w-5 h-5 flex items-center justify-center text-gray-600 hover:text-red-400" data-testid="tutorial-skip-btn"><X className="w-3 h-3" /></button>
                </div>
              </div>
              {/* Progress */}
              <div className="flex items-center gap-0.5 px-3 pb-2">
                {[0,1,2,3,4,5,6].map(s => (
                  <div key={s} className={`h-0.5 rounded-full transition-all duration-500 ${s === step ? 'flex-[2.5] bg-gradient-to-r from-cyan-400 to-blue-500' : s < step ? 'flex-1 bg-cyan-500/30' : 'flex-1 bg-white/5'}`} />
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </>
    );
  }

  // ═══════ NON-TARGET STEPS (0, 2, 3, 5): Panel at BOTTOM with large Velion ═══════
  return (
    <>
      {/* OVERLAY */}
      <AnimatePresence>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] pointer-events-none"
          style={{ background: 'rgba(0,0,0,0.75)' }}
          data-testid="tutorial-overlay"
        />
      </AnimatePresence>

      {/* BOTTOM PANEL: Speech Bubble + Large Velion Character */}
      <motion.div
        initial={{ y: 80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', damping: 20, stiffness: 180, delay: 0.1 }}
        className="fixed left-0 right-0 z-[120] pointer-events-none"
        style={{ bottom: 'calc(env(safe-area-inset-bottom, 0px) + 60px)' }}
        data-testid="tutorial-velion-panel"
      >
        <div className="relative px-2" style={{ height: 210 }}>
          {/* VELION CHARACTER */}
          <motion.div
            key={`velion-char-${step}`}
            initial={{ opacity: 0, scale: 0.6, x: isRight ? 60 : -60 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            transition={{ type: 'spring', damping: 16, stiffness: 150, delay: 0.2 }}
            className="absolute bottom-0 pointer-events-none"
            style={{ [isRight ? 'right' : 'left']: 0, width: msg.velionSize, zIndex: 2 }}
          >
            <motion.img src="/velion-tutorial.png" alt="Velion"
              className="w-full h-auto object-contain select-none"
              style={{ animation: 'velionFloat 2.5s ease-in-out infinite' }}
              {...velionAnim}
            />
          </motion.div>

          {/* SPEECH BUBBLE */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', damping: 22, stiffness: 200, delay: 0.1 }}
            className="absolute pointer-events-auto"
            style={{ [isRight ? 'left' : 'right']: 8, top: 10, width: `calc(100% - ${msg.velionSize + 20}px)`, zIndex: 3 }}
          >
            <div className="bg-[#0a0a0c]/95 backdrop-blur-lg border border-yellow-500/30 rounded-2xl overflow-hidden"
              style={{ boxShadow: '0 0 20px rgba(255,215,0,0.12), 0 4px 30px rgba(0,0,0,0.6)' }}>
              {/* Header */}
              <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/5">
                <div className="flex items-center gap-1.5">
                  <span className="text-cyan-400 font-['Bebas_Neue'] text-xs tracking-widest">VELION</span>
                  <span className="text-[7px] text-cyan-500/50 bg-cyan-500/10 px-1 py-0.5 rounded-full font-bold">{step + 1}/7</span>
                </div>
                <div className="flex items-center gap-0.5">
                  <button onClick={() => setMinimized(true)} className="w-5 h-5 flex items-center justify-center text-gray-600 hover:text-cyan-400 text-[10px]">_</button>
                  <button onClick={skipTutorial} className="w-5 h-5 flex items-center justify-center text-gray-600 hover:text-red-400" data-testid="tutorial-skip-btn"><X className="w-3 h-3" /></button>
                </div>
              </div>
              {/* Body */}
              <div className="px-3 py-2">
                <AnimatePresence mode="wait">
                  <motion.div key={step} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }} transition={{ duration: 0.2 }}>
                    <p className="text-white font-bold text-[13px] mb-0.5 leading-tight">{msg.title}</p>
                    <p className="text-gray-400 text-[11px] leading-relaxed">{msg.text}</p>
                  </motion.div>
                </AnimatePresence>

                {step === 0 && msg.action && (
                  <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
                    <Button className="mt-2 w-full bg-gradient-to-r from-yellow-500 to-amber-500 text-black hover:from-yellow-400 hover:to-amber-400 h-8 text-xs font-bold shadow-lg shadow-yellow-500/20 rounded-xl" onClick={() => advanceStep(1)} data-testid="tutorial-start-btn">
                      <Camera className="w-3.5 h-3.5 mr-1.5" />{msg.action}
                    </Button>
                  </motion.div>
                )}

                {!msg.target && step > 0 && step < 6 && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
                    <Button className="mt-2 w-full bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 h-7 text-[11px] rounded-xl" onClick={() => advanceStep(step + 1)} data-testid="tutorial-continue-btn">
                      Continua
                    </Button>
                  </motion.div>
                )}

                <div className="flex items-center gap-0.5 mt-2">
                  {[0,1,2,3,4,5,6].map(s => (
                    <div key={s} className={`h-1 rounded-full transition-all duration-500 ${s === step ? 'flex-[2.5] bg-gradient-to-r from-cyan-400 to-blue-500' : s < step ? 'flex-1 bg-cyan-500/30' : 'flex-1 bg-white/5'}`} />
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </>
  );
}
