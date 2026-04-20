import React, { useState, useEffect, useContext, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Sparkles, X, UserPlus, ArrowDown, ArrowUp } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';

// ─── STEP V3: dalla Dashboard al rilascio film (guest = tutto gratis) ───
const STEPS = [
  /* 0 */ { title: 'Benvenuto!', text: 'Sono Velion, il tuo assistente! Ti guider\u00f2 passo passo nella creazione del tuo primo film. Tutto GRATIS!', action: 'Iniziamo!', target: null, position: 'bottom', velionSize: 150 },
  /* 1 */ { title: 'Clicca su PRODUCI', text: 'Tocca l\'icona "Produci" nella barra in alto!', target: '[data-testid="top-nav-produci"]', position: 'bottom', velionSize: 100 },
  /* 2 */ { title: 'Seleziona Film', text: 'Ora scegli "Film" dal menu per iniziare la tua avventura!', target: '[data-testid="produci-film"]', position: 'top', velionSize: 80 },
  /* 3 */ { title: 'Nuovo Film', text: 'Clicca sul riquadro tratteggiato per creare il tuo primo film!', target: '[data-testid="new-project-btn"]', position: 'top', velionSize: 90 },
  /* 4 */ { title: 'Dai un titolo', text: 'Inserisci il titolo del tuo film. Sii creativo!', target: '[data-testid="title-input"]', position: 'bottom', velionSize: 80 },
  /* 5 */ { title: 'Scrivi la pretrama', text: 'Racconta di cosa parla il film in poche righe (minimo 50 caratteri).', target: '[data-testid="preplot-input"]', position: 'bottom', velionSize: 80 },
  /* 6 */ { title: 'Scegli le location', text: 'Scegli dove girare il film! Studios famosi, citt\u00e0, natura o luoghi storici. Durante il tutorial TUTTO \u00E8 GRATIS!', target: '[data-testid="location-categories"]', position: 'top', velionSize: 90 },
  /* 7 */ { title: 'Conferma l\'idea', text: 'Ottimo! Ora premi "OK" per confermare la tua idea!', target: '[data-testid="idea-ok-phase0"]', position: 'top', velionSize: 80 },
  /* 8 */ { title: 'Genera la Locandina AI!', text: 'Clicca "Genera da pretrama" per creare una locandina unica con l\'Intelligenza Artificiale!', target: '[data-testid="poster-ai-auto"]', position: 'top', velionSize: 90 },
  /* 9 */ { title: 'Locandina OK', text: 'Locandina pronta! Premi "OK" per continuare.', target: '[data-testid="idea-ok-poster"]', position: 'top', velionSize: 80 },
  /* 10 */ { title: 'Genera la Sceneggiatura!', text: 'Ora clicca "Genera Sceneggiatura AI" e lascia che l\'AI scriva la storia per te!', target: '[data-testid="screenplay-ai-auto"], [data-testid="write-screenplay-btn"]', position: 'top', velionSize: 90 },
  /* 11 */ { title: 'Sceneggiatura OK', text: 'Perfetto! Conferma la sceneggiatura con "OK".', target: '[data-testid="idea-ok-screenplay"]', position: 'top', velionSize: 80 },
  /* 12 */ { title: 'Avanti verso l\'HYPE!', text: 'Ora premi "Avanti" in alto per lanciare la campagna di marketing (HYPE).', target: '[data-testid="advance-btn"]', position: 'top', velionSize: 90 },
  /* 13 */ { title: 'Velocizza GRATIS!', text: 'Durante il tutorial puoi velocizzare tutto GRATIS! Clicca su uno dei pulsanti velocizza.', target: '[data-testid="speedup-100"], [data-testid^="speedup-"], [data-testid^="ciak-speedup-"], [data-testid^="finalcut-speedup-"]', position: 'top', velionSize: 90 },
  /* 14 */ { title: 'Continua ad avanzare', text: 'Continua a premere "Avanti" per completare le fasi: Cast, Produzione, Montaggio, Marketing. Sono tutte GRATIS per te!', target: '[data-testid="advance-btn"]', position: 'top', velionSize: 90 },
  /* 15 */ { title: 'Rilascia il film!', text: 'Ci siamo! Premi "Rilascia GRATIS" per uscire nelle sale!', target: '[data-testid="confirm-release-btn"]', position: 'top', velionSize: 90 },
  /* 16 */ { title: 'Congratulazioni!', text: 'Hai creato il tuo primo film!\nAdesso non ti resta che esplorare tutte le altre sezioni del gioco!\nPuoi creare Serie Tv, Anime, Sequel\u2026\nE poi c\'\u00e8 l\'Arena dove puoi supportare o boicottare i film degli altri Player.\nE ancora la chat dove puoi fare amicizia o chiedere aiuto agli altri player.\nE tanto, tanto ancora!\nDivertiti con noi in', action: 'finale', target: null, position: 'center', velionSize: 200 },
  /* 17 */ { title: 'Registrati', text: 'Vuoi salvare i progressi?', action: 'convert', target: null, position: 'bottom', velionSize: 150 },
];

// Per-step Velion animations (diverse per ogni step)
const VELION_ANIMS = [
  { animate: { y: [0, -10, 0] }, transition: { duration: 2.5, repeat: Infinity } },
  { animate: { y: [0, -6, 0], rotate: [0, 3, -3, 0] }, transition: { duration: 2.8, repeat: Infinity } },
  { animate: { scale: [1, 1.05, 1] }, transition: { duration: 3, repeat: Infinity } },
  { animate: { y: [0, -8, 0], rotate: [0, -2, 2, 0] }, transition: { duration: 2.2, repeat: Infinity } },
  { animate: { x: [0, -3, 3, 0] }, transition: { duration: 2.5, repeat: Infinity } },
  { animate: { y: [0, -12, 0] }, transition: { duration: 2, repeat: Infinity } },
  { animate: { scale: [1, 1.06, 1], y: [0, -6, 0] }, transition: { duration: 2.4, repeat: Infinity } },
  { animate: { y: [0, -8, 0], x: [0, 3, -3, 0] }, transition: { duration: 2, repeat: Infinity } },
  { animate: { rotate: [0, -4, 4, 0] }, transition: { duration: 2.2, repeat: Infinity } },
  { animate: { y: [0, -10, 0], scale: [1, 1.04, 1] }, transition: { duration: 2, repeat: Infinity } },
  { animate: { y: [0, -14, 0], rotate: [0, 5, -5, 0] }, transition: { duration: 1.8, repeat: Infinity } },
  { animate: { y: [0, -20, 0], scale: [1, 1.1, 1], rotate: [0, 8, -8, 0] }, transition: { duration: 2.5, repeat: Infinity } },
  { animate: { scale: [1, 1.03, 1], y: [0, -8, 0] }, transition: { duration: 2.5, repeat: Infinity } },
];

const injectStyles = () => {
  if (document.getElementById('tutorial-styles')) return;
  const s = document.createElement('style');
  s.id = 'tutorial-styles';
  s.textContent = `
    @keyframes tutGlow { 0%,100%{box-shadow:0 0 10px rgba(255,215,0,.7),0 0 25px rgba(255,215,0,.4)}50%{box-shadow:0 0 20px rgba(255,215,0,1),0 0 40px rgba(255,215,0,.6),0 0 60px rgba(255,215,0,.3)} }
    @keyframes tutArrowBounce { 0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)} }
    @keyframes velionFloat { 0%,100%{filter:drop-shadow(0 0 15px rgba(0,180,255,.4)) brightness(1.15)}50%{filter:drop-shadow(0 0 30px rgba(0,180,255,.7)) brightness(1.35)} }
    @keyframes celebrationPulse { 0%,100%{box-shadow:0 0 30px rgba(255,215,0,.3),0 0 60px rgba(255,215,0,.1)}50%{box-shadow:0 0 60px rgba(255,215,0,.6),0 0 120px rgba(255,215,0,.3)} }
    @keyframes sparkleFloat { 0%{transform:translateY(0) scale(1);opacity:1}100%{transform:translateY(-80px) scale(0);opacity:0} }
    @keyframes celebrationGlow { 0%,100%{filter:drop-shadow(0 0 25px rgba(255,215,0,.6)) brightness(1.2)}50%{filter:drop-shadow(0 0 50px rgba(255,215,0,1)) drop-shadow(0 0 80px rgba(0,180,255,.5)) brightness(1.5)} }
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
  const [demoMode, setDemoMode] = useState(false);

  const isActive = (user?.is_guest && !user?.tutorial_completed && visible) || demoMode;
  const msg = STEPS[step] || STEPS[0];
  const hasTarget = !!msg.target;

  // Listen for replay event (registered users)
  useEffect(() => {
    const handler = () => { setDemoMode(true); setStep(0); setMinimized(false); setVisible(true); };
    window.addEventListener('pipeline-tutorial-open', handler);
    return () => window.removeEventListener('pipeline-tutorial-open', handler);
  }, []);

  useEffect(() => { injectStyles(); return () => { const s = document.getElementById('tutorial-styles'); if (s) s.remove(); }; }, []);
  useEffect(() => { if (user?.tutorial_step !== undefined) setStep(user.tutorial_step); }, [user?.tutorial_step]);

  // ─── ADVANCE HELPER (memoized) ───
  const advanceStep = useCallback(async (newStep) => {
    if (demoMode) {
      // In demo: skip convert step, just close at end
      if (newStep >= STEPS.length - 1) { setDemoMode(false); setVisible(false); toast.success('Tutorial Pipeline completato!'); return; }
      setStep(newStep);
      return;
    }
    try { await api.post('/auth/tutorial-step', { step: newStep }); setStep(newStep); if (newStep >= STEPS.length - 1) setShowConvert(true); } catch {}
  }, [api, demoMode]);

  // ─── AUTO-ADVANCE: detect page changes and DOM elements ───
  const stepEnteredAt = useRef(Date.now());
  useEffect(() => { stepEnteredAt.current = Date.now(); }, [step]);

  useEffect(() => {
    if (!isActive) return;
    const path = location.pathname;

    // Step 1 → 2: production menu opened (produci-film visible)
    if (step === 1) {
      const poll = setInterval(() => {
        const el = document.querySelector('[data-testid="produci-film"]');
        if (el && el.offsetParent !== null) { advanceStep(2); clearInterval(poll); }
      }, 800);
      return () => clearInterval(poll);
    }

    // Step 2 → 3: arrived at /create-film
    if (step === 2 && path === '/create-film') { advanceStep(3); return; }

    // Steps 3-15: poll DOM for element presence (V3 pipeline)
    if (step < 3 || step > 15 || path !== '/create-film') return;

    const poll = setInterval(() => {
      const has = (sel) => {
        const els = document.querySelectorAll(sel);
        for (const el of els) { if (el.offsetParent !== null) return true; }
        return false;
      };
      const val = (sel) => {
        const el = document.querySelector(sel);
        return el ? (el.value || '').trim() : '';
      };
      const elapsed = () => (Date.now() - stepEnteredAt.current) / 1000;

      // Step 3 → 4: clicked "Nuovo Film" → title-input appears
      if (step === 3 && has('[data-testid="title-input"]')) advanceStep(4);
      // Step 4 → 5: Title filled (min 2 chars)
      if (step === 4 && val('[data-testid="title-input"]').length >= 2) advanceStep(5);
      // Step 5 → 6: Pretrama >= 50 chars + 10s read time
      if (step === 5 && val('[data-testid="preplot-input"]').length >= 50 && elapsed() > 10) advanceStep(6);
      // Step 6 → 7: User selected at least one location (selected chips visible)
      if (step === 6 && elapsed() > 3 && has('[data-testid="selected-locations"]')) advanceStep(7);
      // Step 7 → 8: Idea confirmed → OK button gone, poster button appears
      if (step === 7 && !has('[data-testid="idea-ok-phase0"]') && has('[data-testid="poster-ai-auto"]')) advanceStep(8);
      // Step 8 → 9: Poster generated → idea-ok-poster visible OR poster-zoom-trigger visible
      if (step === 8 && (has('[data-testid="idea-ok-poster"]') || has('[data-testid="poster-zoom-trigger"]')) && !has('[data-testid="poster-ai-auto"]')) advanceStep(9);
      // Step 9 → 10: User clicked OK poster → screenplay-ai-auto visible
      if (step === 9 && has('[data-testid="screenplay-ai-auto"]')) advanceStep(10);
      // Step 10 → 11: Screenplay generated → idea-ok-screenplay visible AND generate button gone
      if (step === 10 && has('[data-testid="idea-ok-screenplay"]') && !has('[data-testid="screenplay-ai-auto"]')) advanceStep(11);
      // Step 11 → 12: User clicked OK screenplay → "Idea completa" message visible + advance-btn active
      if (step === 11 && !has('[data-testid="idea-ok-screenplay"]') && has('[data-testid="advance-btn"]') && elapsed() > 2) advanceStep(12);
      // Step 12 → 13: User advanced to HYPE → speedup buttons visible
      if (step === 12 && has('[data-testid^="speedup-"]')) advanceStep(13);
      // Step 13 → 14: User used speedup → wait 3s then go to "continua ad avanzare" step
      if (step === 13 && elapsed() > 3) advanceStep(14);
      // Step 14 → 15: User reached release phase (confirm-release-btn visible)
      if (step === 14 && has('[data-testid="confirm-release-btn"]')) advanceStep(15);
      // Step 15 → 16: Film released (confirm button gone, we're on release success state)
      if (step === 15 && !has('[data-testid="confirm-release-btn"]') && elapsed() > 3) advanceStep(16);
    }, 500);

    return () => clearInterval(poll);
  }, [step, location.pathname, isActive, advanceStep]);

  // ─── SPOTLIGHT: find + glow + scroll target (continuous polling) ───
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
      if (!el) { setTargetRect(null); targetElRef.current = null; return; }
      if (targetElRef.current === el) {
        // Same element — only update rect if moved significantly
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          setTargetRect(prev => {
            if (prev && Math.abs(prev.top - rect.top) < 3 && Math.abs(prev.left - rect.left) < 3) return prev;
            return { top: rect.top, left: rect.left, width: rect.width, height: rect.height };
          });
        }
        return;
      }
      targetElRef.current = el;
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setTimeout(() => {
        if (!targetElRef.current || targetElRef.current !== el) return;
        el.classList.add('tut-target-active');
        let parent = el.parentElement;
        while (parent && parent !== document.body) {
          const st = getComputedStyle(parent);
          if (st.position === 'fixed' || st.position === 'absolute' || st.position === 'sticky') parent.classList.add('tut-parent-lifted');
          parent = parent.parentElement;
        }
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          setTargetRect({ top: rect.top, left: rect.left, width: rect.width, height: rect.height });
        }
      }, 200);
    };
    findAndHighlight();
    const poll = setInterval(findAndHighlight, 1200);
    return () => { clearInterval(poll); document.querySelectorAll('.tut-parent-lifted').forEach(el => el.classList.remove('tut-parent-lifted')); };
  }, [step, minimized, msg.target, isActive]);

  if (!isActive) return null;

  const skipTutorial = async () => {
    document.querySelectorAll('.tut-target-active').forEach(el => el.classList.remove('tut-target-active'));
    document.querySelectorAll('.tut-parent-lifted').forEach(el => el.classList.remove('tut-parent-lifted'));
    if (demoMode) { setDemoMode(false); setVisible(false); return; }
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

  const velionAnim = VELION_ANIMS[step % VELION_ANIMS.length] || VELION_ANIMS[0];
  const totalSteps = STEPS.length;
  const isBottom = msg.position === 'bottom';

  // ═══════ CONVERSION MODAL ═══════
  if (showConvert) {
    return (
      <div className="fixed inset-0 z-[200] flex items-end sm:items-center justify-center bg-black/80 backdrop-blur-sm pb-4 sm:pb-0" data-testid="guest-tutorial-convert">
        <motion.div initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
          className="bg-[#0d0d0f] border border-cyan-500/20 rounded-2xl max-w-sm w-[92%] mx-4 overflow-hidden relative">
          <motion.div className="absolute -top-2 -right-3 w-28 h-28 pointer-events-none z-10"
            animate={{ y: [0, -8, 0], rotate: [0, 5, -5, 0] }} transition={{ duration: 3, repeat: Infinity }}>
            <img src="/velion-tutorial.png" alt="Velion" className="w-full h-full object-contain" style={{ animation: 'velionFloat 2.5s ease-in-out infinite' }} />
          </motion.div>
          <div className="bg-gradient-to-br from-cyan-500/15 via-transparent to-yellow-500/10 p-4 pr-28">
            <div className="flex items-center gap-1.5 mb-1"><Sparkles className="w-4 h-4 text-yellow-400" /><span className="text-cyan-400 font-['Bebas_Neue'] text-sm tracking-wider">VELION</span></div>
            <h3 className="font-bold text-base text-white">Ti sta piacendo il gioco?</h3>
            <p className="text-[11px] text-gray-400 mt-0.5">Salva i progressi e continua la tua avventura!</p>
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

  // ═══════ MINIMIZED ═══════
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

  // ═══════ SHARED: Speech bubble content ═══════
  const SpeechBubble = ({ className = '', style = {} }) => (
    <div className={`bg-[#0a0a0c]/95 backdrop-blur-lg border border-yellow-500/25 rounded-2xl overflow-hidden ${className}`}
      style={{ boxShadow: '0 0 20px rgba(255,215,0,0.12), 0 4px 30px rgba(0,0,0,0.6)', ...style }}>
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/5">
        <div className="flex items-center gap-1.5">
          <span className="text-cyan-400 font-['Bebas_Neue'] text-xs tracking-widest">VELION</span>
          <span className="text-[7px] text-cyan-500/50 bg-cyan-500/10 px-1 py-0.5 rounded-full font-bold">{step + 1}/{totalSteps}</span>
        </div>
        <div className="flex items-center gap-0.5 pointer-events-auto">
          <button onClick={() => setMinimized(true)} className="w-5 h-5 flex items-center justify-center text-gray-600 hover:text-cyan-400 text-[10px]">_</button>
          <button onClick={skipTutorial} className="w-5 h-5 flex items-center justify-center text-gray-600 hover:text-red-400" data-testid="tutorial-skip-btn"><X className="w-3 h-3" /></button>
        </div>
      </div>
      <div className="px-3 py-2">
        <AnimatePresence mode="wait">
          <motion.div key={step} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }} transition={{ duration: 0.2 }}>
            <p className="text-white font-bold text-[13px] leading-tight">{msg.title}</p>
            <p className="text-gray-400 text-[11px] leading-relaxed">{msg.text}</p>
          </motion.div>
        </AnimatePresence>
        {step === 0 && msg.action === 'Iniziamo!' && (
          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
            <Button className="mt-2 w-full bg-gradient-to-r from-yellow-500 to-amber-500 text-black hover:from-yellow-400 hover:to-amber-400 h-8 text-xs font-bold shadow-lg shadow-yellow-500/20 rounded-xl pointer-events-auto"
              onClick={() => advanceStep(1)} data-testid="tutorial-start-btn">
              <Camera className="w-3.5 h-3.5 mr-1.5" />{msg.action}
            </Button>
          </motion.div>
        )}
        {!hasTarget && step > 0 && step < STEPS.length - 2 && !msg.action && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
            <Button className="mt-2 w-full bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 h-7 text-[11px] rounded-xl pointer-events-auto"
              onClick={() => advanceStep(step + 1)} data-testid="tutorial-continue-btn">Continua</Button>
          </motion.div>
        )}
        <div className="flex items-center gap-0.5 mt-2">
          {STEPS.map((_, i) => (
            <div key={i} className={`h-1 rounded-full transition-all duration-500 ${i === step ? 'flex-[2] bg-gradient-to-r from-cyan-400 to-blue-500' : i < step ? 'flex-1 bg-cyan-500/30' : 'flex-1 bg-white/5'}`} />
          ))}
        </div>
      </div>
    </div>
  );

  // ═══════ VELION CHARACTER ═══════
  const VelionCharacter = ({ side = 'right' }) => (
    <motion.div
      key={`velion-${step}`}
      initial={{ opacity: 0, scale: 0.6, x: side === 'right' ? 50 : -50 }}
      animate={{ opacity: 1, scale: 1, x: 0 }}
      transition={{ type: 'spring', damping: 16, stiffness: 150, delay: 0.2 }}
      className="absolute bottom-0 pointer-events-none"
      style={{ [side]: 0, width: msg.velionSize, zIndex: 2 }}
    >
      <motion.img src="/velion-tutorial.png" alt="Velion"
        className="w-full h-auto object-contain select-none"
        style={{ animation: 'velionFloat 2.5s ease-in-out infinite' }}
        {...velionAnim}
      />
    </motion.div>
  );

  // ═══════ MAIN RENDER ═══════

  // ═══════ FINALE CELEBRATIVO (Step 11) ═══════
  if (step === 16) {
    return (
      <>
        {/* Overlay scuro di base */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="fixed inset-0 z-[100]"
          style={{ background: 'radial-gradient(ellipse at center, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.95) 100%)' }}
          data-testid="tutorial-finale-overlay"
        />

        {/* Sparkle particles */}
        <div className="fixed inset-0 z-[101] pointer-events-none overflow-hidden" data-testid="tutorial-finale-sparkles">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute rounded-full"
              style={{
                width: Math.random() * 6 + 2,
                height: Math.random() * 6 + 2,
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                background: i % 3 === 0 ? '#FFD700' : i % 3 === 1 ? '#00B4FF' : '#FF6B6B',
              }}
              animate={{
                y: [0, -(Math.random() * 200 + 100)],
                x: [0, (Math.random() - 0.5) * 100],
                opacity: [0, 1, 1, 0],
                scale: [0, 1.5, 1, 0],
              }}
              transition={{
                duration: Math.random() * 3 + 2,
                repeat: Infinity,
                delay: Math.random() * 2,
                ease: 'easeOut',
              }}
            />
          ))}
        </div>

        {/* Contenuto centrale — scrollable safe */}
        <div className="fixed inset-0 z-[120] flex flex-col items-center justify-start overflow-y-auto px-3 pt-6 pb-20 pointer-events-none" data-testid="tutorial-finale-content">

          {/* Velion con glow celebrativo */}
          <motion.div
            initial={{ scale: 0, rotate: -20 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', damping: 12, stiffness: 100, delay: 0.3 }}
            className="relative flex-shrink-0 mb-1"
          >
            <motion.img
              src="/velion-tutorial.png"
              alt="Velion"
              className="w-36 h-36 sm:w-44 sm:h-44 object-contain select-none"
              style={{ animation: 'celebrationGlow 2s ease-in-out infinite' }}
              animate={{ y: [0, -14, 0], scale: [1, 1.06, 1], rotate: [0, 4, -4, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              data-testid="tutorial-finale-velion"
            />
            <motion.div
              className="absolute inset-[-12px] rounded-full border-2 border-yellow-400/40"
              animate={{ scale: [1, 1.15, 1], opacity: [0.4, 0.8, 0.4] }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{ animation: 'celebrationPulse 2s ease-in-out infinite' }}
            />
          </motion.div>

          {/* Titolo */}
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="text-xl sm:text-2xl font-extrabold text-center mb-2 flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #FFD700, #FFA500, #FF6B35)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
            data-testid="tutorial-finale-title"
          >
            Congratulazioni!
          </motion.h2>

          {/* Messaggio — compatto e leggibile */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="bg-[#0a0a0c]/85 backdrop-blur-xl border border-yellow-500/30 rounded-2xl px-4 py-3 w-full max-w-[340px] text-center flex-shrink-0"
            style={{ boxShadow: '0 0 30px rgba(255,215,0,0.12), 0 6px 30px rgba(0,0,0,0.5)' }}
            data-testid="tutorial-finale-message"
          >
            <div className="flex items-center justify-center gap-1.5 mb-1.5">
              <Sparkles className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-cyan-400 font-['Bebas_Neue'] text-xs tracking-widest">VELION</span>
              <Sparkles className="w-3.5 h-3.5 text-yellow-400" />
            </div>
            <p className="text-white text-[11px] sm:text-xs leading-[1.6] font-medium whitespace-pre-line">
              {msg.text}
            </p>
            <p className="text-lg sm:text-xl font-extrabold mt-1.5"
              style={{ background: 'linear-gradient(135deg, #00B4FF, #00E5FF, #FFD700)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
            >
              CineWorld Studio's!!!
            </p>
          </motion.div>

          {/* Bottone */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.3 }}
            className="mt-3 pointer-events-auto flex-shrink-0"
          >
            <Button
              className="bg-gradient-to-r from-yellow-500 via-amber-500 to-orange-500 text-black hover:from-yellow-400 hover:to-orange-400 font-bold px-8 h-10 text-xs rounded-xl shadow-lg shadow-yellow-500/30"
              onClick={() => advanceStep(17)}
              data-testid="tutorial-finale-continue-btn"
            >
              <Sparkles className="w-4 h-4 mr-2" />Continua l'avventura!
            </Button>
          </motion.div>
        </div>
      </>
    );
  }

  return (
    <>
      {/* OVERLAY — lighter when target is found */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        className="fixed inset-0 z-[100] pointer-events-none"
        style={{ background: targetRect ? 'rgba(0,0,0,0.55)' : 'rgba(0,0,0,0.4)' }}
        data-testid="tutorial-overlay"
      />

      {/* SPOTLIGHT cutout on target */}
      {targetRect && !minimized && (
        <div className="fixed z-[101] pointer-events-none" style={{
          top: targetRect.top - 8,
          left: targetRect.left - 8,
          width: targetRect.width + 16,
          height: targetRect.height + 16,
          borderRadius: 12,
          boxShadow: '0 0 0 9999px rgba(0,0,0,0.55), 0 0 30px 8px rgba(255,215,0,0.4)',
          animation: 'tutGlow 1.5s ease-in-out infinite',
        }} />
      )}

      {/* ARROW to target */}
      {targetRect && !minimized && (() => {
        const panelEl = document.querySelector('[data-testid="tutorial-velion-panel"]');
        const panelRect = panelEl?.getBoundingClientRect();
        const targetCenter = targetRect.top + targetRect.height / 2;
        const panelCenter = panelRect ? (panelRect.top + panelRect.height / 2) : 0;
        const pointDown = targetCenter > panelCenter;
        const arrowTop = pointDown ? targetRect.top - 36 : targetRect.top + targetRect.height + 4;
        const arrowLeft = targetRect.left + targetRect.width / 2 - 16;
        return (
          <div className="fixed z-[130] pointer-events-none" style={{ top: Math.max(0, Math.min(arrowTop, window.innerHeight - 36)), left: Math.max(4, Math.min(arrowLeft, window.innerWidth - 36)), animation: 'tutArrowBounce 1s ease-in-out infinite', filter: 'drop-shadow(0 0 12px rgba(255,215,0,.9))' }} data-testid="tutorial-arrow">
            {pointDown ? <ArrowDown className="w-8 h-8 text-yellow-400" strokeWidth={3} /> : <ArrowUp className="w-8 h-8 text-yellow-400" strokeWidth={3} />}
          </div>
        );
      })()}

      {/* VELION PANEL */}
      <div className="fixed inset-0 z-[120] pointer-events-none" data-testid="tutorial-velion-panel">
        {isBottom ? (
          /* ─── BOTTOM LAYOUT: large Velion right + speech left ─── */
          <motion.div
            initial={{ y: 80, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
            transition={{ type: 'spring', damping: 20, stiffness: 180 }}
            className="absolute left-0 right-0 px-2"
            style={{ bottom: 'calc(env(safe-area-inset-bottom, 0px) + 60px)' }}
          >
            <div className="relative" style={{ height: 200 }}>
              <VelionCharacter side="right" />
              <div className="absolute left-0 top-2" style={{ width: `calc(100% - ${msg.velionSize + 16}px)`, zIndex: 3 }}>
                <SpeechBubble />
              </div>
            </div>
          </motion.div>
        ) : (
          /* ─── TOP LAYOUT: large Velion right + speech left, upper area ─── */
          <motion.div
            initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', damping: 18, stiffness: 180, delay: 0.1 }}
            className="absolute left-0 right-0 px-2"
            style={{ top: 'max(env(safe-area-inset-top, 8px), 8px)' }}
          >
            <div className="relative" style={{ height: 130 }}>
              <VelionCharacter side="right" />
              <div className="absolute left-0 top-1" style={{ width: `calc(100% - ${msg.velionSize + 12}px)`, zIndex: 3 }}>
                <SpeechBubble />
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </>
  );
}
