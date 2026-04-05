import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Zap, Sparkles, X, ChevronRight, Gamepad2, Film, UserPlus, Eye } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const VELION_MESSAGES = {
  0: {
    title: 'Benvenuto!',
    text: 'Sono Velion, il tuo assistente. Ti guider\u00f2 nella creazione del tuo primo film!',
    action: 'Iniziamo!',
  },
  1: {
    title: 'Produci il tuo primo film',
    text: 'Clicca su PRODUCI FILM nella barra in alto per iniziare.',
    highlight: '[data-testid="nav-produci-film"], [href="/create-film"], [data-testid="prod-menu-film"]',
    action: null,
  },
  2: {
    title: 'Scegli il tipo',
    text: 'Perfetto! Ora segui la procedura per creare il tuo primo film. Scegli genere e titolo!',
    action: null,
  },
  3: {
    title: 'Coming Soon avviato!',
    text: 'Il tuo film \u00e8 in fase Coming Soon. L\'hype sta crescendo!',
    action: null,
  },
  4: {
    title: 'Velocizzazione gratuita!',
    text: 'Hai 3 velocizzazioni GRATIS! Usale per accelerare il timer del tuo film.',
    highlight: '[data-testid="speedup-btn"]',
    action: null,
  },
  5: {
    title: 'Ottimo lavoro!',
    text: 'Guarda come evolve il tuo progetto. Ogni fase ti avvicina al successo!',
    action: null,
  },
  6: {
    title: 'Sei pronto!',
    text: 'Hai creato il tuo primo film! Vuoi salvare i progressi e continuare a giocare?',
    action: 'convert',
  },
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

  // Sync step from user
  useEffect(() => {
    if (user?.tutorial_step !== undefined) {
      setStep(user.tutorial_step);
    }
  }, [user?.tutorial_step]);

  // Don't show if not guest or tutorial completed
  if (!user?.is_guest || user?.tutorial_completed) return null;

  const msg = VELION_MESSAGES[step] || VELION_MESSAGES[0];

  const advanceStep = async (newStep) => {
    try {
      await api.post('/auth/tutorial-step', { step: newStep });
      setStep(newStep);
      if (newStep >= 6) {
        setShowConvert(true);
      }
    } catch {}
  };

  const skipTutorial = async () => {
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
      if (res.data.access_token) {
        localStorage.setItem('cineworld_token', res.data.access_token);
      }
      refreshUser();
      toast.success('Account registrato! I tuoi progressi sono salvi');
      setShowConvert(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella registrazione');
    } finally {
      setConverting(false);
    }
  };

  // Detect navigation to auto-advance steps
  useEffect(() => {
    if (step === 1 && location.pathname === '/create-film') {
      advanceStep(2);
    }
  }, [location.pathname, step]);

  if (!visible) return null;

  // Conversion modal at step 6
  if (showConvert) {
    return (
      <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/70 backdrop-blur-sm" data-testid="guest-tutorial-convert">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-[#111] border border-yellow-500/30 rounded-2xl max-w-sm w-[90%] mx-4 overflow-hidden"
        >
          <div className="bg-gradient-to-b from-yellow-500/20 to-transparent p-5 text-center">
            <div className="w-14 h-14 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-3">
              <Sparkles className="w-7 h-7 text-yellow-400" />
            </div>
            <h3 className="font-['Bebas_Neue'] text-xl text-yellow-300">Hai creato il tuo primo film!</h3>
            <p className="text-xs text-gray-400 mt-1">Vuoi salvare i tuoi progressi e continuare?</p>
          </div>
          <div className="px-5 pb-5 space-y-2.5">
            <Input
              placeholder="Email"
              type="email"
              value={convertForm.email}
              onChange={e => setConvertForm(p => ({...p, email: e.target.value}))}
              className="h-9 bg-white/5 border-white/10 text-sm"
              data-testid="tutorial-convert-email"
            />
            <Input
              placeholder="Password (min 6 caratteri)"
              type="password"
              value={convertForm.password}
              onChange={e => setConvertForm(p => ({...p, password: e.target.value}))}
              className="h-9 bg-white/5 border-white/10 text-sm"
              data-testid="tutorial-convert-password"
            />
            <Input
              placeholder="Nickname"
              value={convertForm.nickname}
              onChange={e => setConvertForm(p => ({...p, nickname: e.target.value}))}
              className="h-9 bg-white/5 border-white/10 text-sm"
              data-testid="tutorial-convert-nickname"
            />
            <Button
              className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold h-9"
              disabled={converting || !convertForm.email || convertForm.password.length < 6}
              onClick={handleConvert}
              data-testid="tutorial-convert-submit"
            >
              <UserPlus className="w-4 h-4 mr-2" />
              {converting ? 'Registrazione...' : 'Registrati'}
            </Button>
            <button
              className="w-full text-center text-xs text-gray-500 hover:text-gray-300 py-1"
              onClick={() => { setShowConvert(false); skipTutorial(); }}
              data-testid="tutorial-convert-skip"
            >
              Continua come ospite
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Minimized state - just a small Velion icon
  if (minimized) {
    return (
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className="fixed bottom-20 right-3 z-[100] w-12 h-12 rounded-full bg-yellow-500/20 border border-yellow-500/40 flex items-center justify-center shadow-lg"
        onClick={() => setMinimized(false)}
        data-testid="tutorial-velion-minimized"
      >
        <img src="/velion-avatar.png" alt="V" className="w-8 h-8 rounded-full" onError={e => { e.target.style.display='none'; e.target.nextSibling.style.display='flex'; }} />
        <div className="w-8 h-8 rounded-full bg-yellow-500/30 items-center justify-center text-yellow-400 font-bold text-sm" style={{display:'none'}}>V</div>
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse" />
      </motion.button>
    );
  }

  // Full Velion guide panel
  return (
    <>
      {/* Overlay only for steps 0-1 to guide user */}
      {step <= 1 && (
        <div className="fixed inset-0 z-[90] bg-black/40 pointer-events-none" data-testid="tutorial-overlay" />
      )}

      {/* Velion panel */}
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="fixed bottom-20 left-3 right-3 z-[100] sm:left-auto sm:right-4 sm:max-w-xs"
        data-testid="tutorial-velion-panel"
      >
        <div className="bg-[#111113] border border-yellow-500/30 rounded-2xl shadow-2xl shadow-yellow-500/10 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 bg-yellow-500/10 border-b border-yellow-500/20">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-yellow-500/30 flex items-center justify-center">
                <span className="text-yellow-400 font-bold text-xs">V</span>
              </div>
              <span className="text-yellow-400 font-['Bebas_Neue'] text-sm tracking-wide">VELION</span>
              <span className="text-[9px] text-gray-500 bg-white/5 px-1.5 py-0.5 rounded-full">Step {step + 1}/7</span>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => setMinimized(true)} className="w-6 h-6 flex items-center justify-center text-gray-500 hover:text-gray-300 rounded">
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
              <button onClick={skipTutorial} className="w-6 h-6 flex items-center justify-center text-gray-500 hover:text-gray-300 rounded" data-testid="tutorial-skip-btn">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-3">
            <p className="text-yellow-300 font-semibold text-sm mb-1">{msg.title}</p>
            <p className="text-gray-400 text-xs leading-relaxed">{msg.text}</p>

            {/* Action button for step 0 */}
            {step === 0 && msg.action && (
              <Button
                className="mt-3 w-full bg-yellow-500 text-black hover:bg-yellow-400 h-8 text-xs font-bold"
                onClick={() => advanceStep(1)}
                data-testid="tutorial-start-btn"
              >
                <Camera className="w-3.5 h-3.5 mr-1.5" />
                {msg.action}
              </Button>
            )}

            {/* Progress dots */}
            <div className="flex items-center justify-center gap-1.5 mt-3">
              {[0,1,2,3,4,5,6].map(s => (
                <div
                  key={s}
                  className={`w-1.5 h-1.5 rounded-full transition-all ${s === step ? 'w-4 bg-yellow-400' : s < step ? 'bg-yellow-500/50' : 'bg-white/10'}`}
                />
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </>
  );
}
