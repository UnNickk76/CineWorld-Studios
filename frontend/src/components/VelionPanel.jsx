import React, { useState, useEffect, useRef, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './ui/button';
import {
  Film, Flame, Users, FileText, Building, Clapperboard, Globe,
  DollarSign, Swords, Home, Target,
  ChevronLeft, ChevronRight, X, Sparkles, Trophy, Plus, Eye,
  Send, MessageCircle, BookOpen, Loader2
} from 'lucide-react';
import { AuthContext } from '../contexts';

const LS_TUTORIAL_KEY = 'velion_tutorial_done';

// ==================== TUTORIAL STEPS ====================

const STEPS = [
  {
    icon: Sparkles, color: 'cyan',
    title: 'Benvenuto in CineWorld!',
    text: 'Io sono Velion, il tuo assistente personale.\n\nDa questo momento non sei pi\u00f9 solo: costruiremo insieme il tuo impero cinematografico.\n\n\ud83c\udfac Ogni scelta conta.\n\ud83d\udd25 Ogni film pu\u00f2 diventare leggenda.\n\nPronto a iniziare?',
  },
  {
    icon: Home, color: 'yellow',
    title: 'Dashboard',
    text: 'Questa \u00e8 la tua base operativa.\n\nQui controlli tutto: incassi, progressi, film e opportunit\u00e0.\n\nTienila sempre d\'occhio\u2026 il successo parte da qui.',
    page: '/',
  },
  {
    icon: Clapperboard, color: 'orange',
    title: 'Produci!',
    text: 'Qui nasce tutto.\n\nClicca su "Produci!": \u00e8 da qui che iniziano i tuoi film.\n\nOgni grande produttore \u00e8 partito da un\'idea.',
    page: '/create-film',
  },
  {
    icon: Plus, color: 'green',
    title: 'Nuovo Film',
    text: '\u00c8 il momento di creare.\n\nScegli se:\n\u26a1 Produzione immediata\n\ud83d\udd25 Coming Soon (pi\u00f9 strategico)\n\nLe scelte giuste fanno la differenza.',
  },
  {
    icon: Film, color: 'blue',
    title: 'Creazione',
    text: 'Qui stai proponendo il tuo film.\n\nTitolo, trama, location: \u00e8 qui che nasce la magia.\n\nPi\u00f9 \u00e8 forte l\'idea\u2026 pi\u00f9 pu\u00f2 diventare un successo.',
  },
  {
    icon: Eye, color: 'amber',
    title: 'Pre-Valutazione',
    text: 'Il sistema analizza il tuo progetto.\n\nRiceverai un punteggio iniziale.\n\nNon \u00e8 definitivo\u2026 ma \u00e8 un primo segnale.',
  },
  {
    icon: Users, color: 'pink',
    title: 'Casting',
    text: 'Adesso scegli il cast.\n\nAttori, regista, sceneggiatori.\n\nRicorda:\n\u2b50 il talento costa\u2026 ma fa la differenza.',
  },
  {
    icon: FileText, color: 'purple',
    title: 'Sceneggiatura',
    text: 'La storia prende forma.\n\nPuoi aspettare\u2026 oppure velocizzare con i CinePass.\n\n\ud83c\udfaf Qui si decide la qualit\u00e0 del film.',
  },
  {
    icon: Clapperboard, color: 'teal',
    title: 'Produzione',
    text: 'Ciak\u2026 si gira!\n\nIl film entra in produzione.\n\n\u23f3 Puoi attendere oppure accelerare.',
  },
  {
    icon: Flame, color: 'orange',
    title: 'Coming Soon',
    text: 'Se hai scelto Coming Soon:\n\nIl tempo gioca a tuo favore.\n\n\ud83d\udcc8 Pi\u00f9 hype = pi\u00f9 successo.\n\nOgni accesso pu\u00f2 migliorare il risultato.',
  },
  {
    icon: Globe, color: 'emerald',
    title: 'Uscita',
    text: '\u00c8 il momento della verit\u00e0.\n\nIl tuo film arriva al pubblico.\n\n\ud83c\udfac Successo o flop?\nDipende da te.',
    page: '/films',
  },
  {
    icon: DollarSign, color: 'yellow',
    title: 'Incassi',
    text: 'I tuoi film generano guadagni nel tempo.\n\n\ud83d\udcb0 Ricordati di riscuotere!\n\nPi\u00f9 investi\u2026 pi\u00f9 guadagni.',
  },
  {
    icon: Building, color: 'violet',
    title: 'Infrastrutture',
    text: 'Qui costruisci il tuo impero.\n\nCinema, studi, divisioni speciali.\n\nSbloccano nuove possibilit\u00e0.',
    page: '/infrastructure',
  },
  {
    icon: Swords, color: 'red',
    title: 'PvP / Sfide',
    text: 'Sfida altri giocatori.\n\n\ud83c\udfaf Vinci \u2192 premi e fama\n\u26a0\ufe0f Perdi \u2192 impari e migliori\n\nQui si vede chi \u00e8 il migliore.',
    page: '/hq',
  },
  {
    icon: Target, color: 'sky',
    title: 'Eventi & Boicottaggi',
    text: 'Il mondo del cinema non \u00e8 sempre pulito\u2026\n\nEventi, aiuti, sabotaggi.\n\nSta a te reagire.',
  },
  {
    icon: Trophy, color: 'cyan',
    title: 'Conclusione',
    text: 'Ora sai tutto quello che serve.\n\nMa ricordalo:\n\n\ud83d\udd25 Non vince il pi\u00f9 ricco.\n\ud83c\udfac Non vince il pi\u00f9 veloce.\n\nVince chi fa le scelte giuste.\n\nBenvenuto in CineWorld, produttore.',
  },
];

const COLOR_MAP = {
  cyan: { bg: 'bg-cyan-500/15', text: 'text-cyan-400', border: 'border-cyan-500/30', glow: 'rgba(0,200,255,0.15)' },
  yellow: { bg: 'bg-yellow-500/15', text: 'text-yellow-400', border: 'border-yellow-500/30', glow: 'rgba(255,200,0,0.15)' },
  orange: { bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/30', glow: 'rgba(255,150,0,0.15)' },
  green: { bg: 'bg-green-500/15', text: 'text-green-400', border: 'border-green-500/30', glow: 'rgba(0,200,100,0.15)' },
  blue: { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/30', glow: 'rgba(0,100,255,0.15)' },
  amber: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30', glow: 'rgba(245,158,11,0.15)' },
  pink: { bg: 'bg-pink-500/15', text: 'text-pink-400', border: 'border-pink-500/30', glow: 'rgba(236,72,153,0.15)' },
  teal: { bg: 'bg-teal-500/15', text: 'text-teal-400', border: 'border-teal-500/30', glow: 'rgba(20,184,166,0.15)' },
  emerald: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', glow: 'rgba(16,185,129,0.15)' },
  purple: { bg: 'bg-purple-500/15', text: 'text-purple-400', border: 'border-purple-500/30', glow: 'rgba(168,85,247,0.15)' },
  violet: { bg: 'bg-violet-500/15', text: 'text-violet-400', border: 'border-violet-500/30', glow: 'rgba(139,92,246,0.15)' },
  red: { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/30', glow: 'rgba(239,68,68,0.15)' },
  sky: { bg: 'bg-sky-500/15', text: 'text-sky-400', border: 'border-sky-500/30', glow: 'rgba(14,165,233,0.15)' },
};

// ==================== TUTORIAL TAB ====================

function TutorialTab({ onClose, onNavigate }) {
  const [step, setStep] = useState(0);
  const current = STEPS[step];
  const Icon = current.icon;
  const c = COLOR_MAP[current.color] || COLOR_MAP.cyan;
  const isLast = step >= STEPS.length - 1;

  const handleDone = () => {
    localStorage.setItem(LS_TUTORIAL_KEY, 'true');
    setStep(0);
    onClose();
  };

  const goToPage = () => {
    if (current.page && onNavigate) {
      onNavigate(current.page);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Step header */}
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <div className={`w-7 h-7 rounded-lg ${c.bg} flex items-center justify-center`}>
          <Icon className={`w-4 h-4 ${c.text}`} />
        </div>
        <h3 className="font-['Bebas_Neue'] text-lg text-white leading-tight flex-1">{current.title}</h3>
        <span className="text-[9px] text-gray-600">{step + 1}/{STEPS.length}</span>
      </div>

      {/* Progress bar */}
      <div className="px-4 pb-2">
        <div className="h-0.5 bg-white/5 rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: `linear-gradient(90deg, ${c.glow.replace('0.15', '0.8')}, ${c.glow.replace('0.15', '0.5')})` }}
            animate={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-2">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">{current.text}</p>
            {current.page && (
              <button
                onClick={goToPage}
                className={`mt-2 text-xs ${c.text} underline underline-offset-2 hover:opacity-80`}
                data-testid="tutorial-goto-page"
              >
                Vai alla pagina →
              </button>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between px-4 py-2.5 border-t border-white/5">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setStep(s => Math.max(0, s - 1))}
          disabled={step === 0}
          className="text-xs text-gray-400 hover:text-white disabled:opacity-30 h-8"
          data-testid="tutorial-prev"
        >
          <ChevronLeft className="w-3.5 h-3.5 mr-1" /> Indietro
        </Button>
        <button onClick={handleDone} className="text-[10px] text-gray-600 hover:text-gray-400 transition-colors">
          Salta
        </button>
        <Button
          size="sm"
          onClick={() => isLast ? handleDone() : setStep(s => s + 1)}
          className={`text-xs h-8 ${isLast ? 'bg-cyan-500 hover:bg-cyan-400 text-black' : 'bg-white/10 hover:bg-white/20 text-white'}`}
          data-testid="tutorial-next"
        >
          {isLast ? 'Inizia!' : 'Avanti'} <ChevronRight className="w-3.5 h-3.5 ml-1" />
        </Button>
      </div>
    </div>
  );
}

// ==================== CHAT TAB ====================

function ChatTab() {
  const { api } = useContext(AuthContext);
  const [messages, setMessages] = useState([
    { role: 'velion', text: 'Sono Velion. Chiedimi qualsiasi cosa sul gioco.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', text }]);
    setLoading(true);

    try {
      const res = await api.post('/velion/ask', { text });
      setMessages(prev => [...prev, { role: 'velion', text: res.data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'velion', text: 'Un momento... qualcosa non ha funzionato. Riprova.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-2 space-y-2.5" style={{ maxHeight: '280px' }}>
        {messages.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.role === 'velion' && (
              <div className="flex-shrink-0 w-6 h-6 rounded-full mr-1.5 mt-0.5 relative">
                <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,30,60,0.9) 40%, transparent 100%)' }} />
                <img src="/velion.png" alt="" className="w-full h-full object-contain rounded-full relative z-10" style={{ mixBlendMode: 'screen', filter: 'brightness(1.4) contrast(1.3)' }} />
              </div>
            )}
            <div className={`max-w-[80%] px-3 py-2 rounded-xl text-[13px] leading-relaxed ${
              m.role === 'user'
                ? 'bg-cyan-500/20 text-cyan-100 rounded-br-sm'
                : 'bg-white/5 text-gray-300 border border-white/5 rounded-bl-sm'
            }`}>
              {m.text}
            </div>
          </motion.div>
        ))}
        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-1.5 px-1">
            <div className="w-6 h-6 rounded-full relative flex-shrink-0">
              <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,30,60,0.9) 40%, transparent 100%)' }} />
              <img src="/velion.png" alt="" className="w-full h-full object-contain rounded-full relative z-10" style={{ mixBlendMode: 'screen', filter: 'brightness(1.4) contrast(1.3)' }} />
            </div>
            <div className="flex gap-1 py-2 px-3 bg-white/5 rounded-xl rounded-bl-sm border border-white/5">
              <span className="w-1.5 h-1.5 bg-cyan-400/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-cyan-400/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-cyan-400/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </motion.div>
        )}
      </div>

      {/* Input */}
      <div className="px-3 py-2.5 border-t border-white/5">
        <div className="flex items-center gap-2 bg-white/5 rounded-xl px-3 py-1.5 border border-white/10 focus-within:border-cyan-500/40 transition-colors">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Chiedi a Velion..."
            className="flex-1 bg-transparent text-sm text-white placeholder-gray-500 outline-none"
            disabled={loading}
            data-testid="velion-chat-input"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="p-1.5 rounded-lg text-cyan-400 hover:bg-cyan-500/10 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            data-testid="velion-chat-send"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}

// ==================== MAIN PANEL ====================

export function VelionPanel({ open, onClose, onNavigate, defaultTab }) {
  const [tab, setTab] = useState(defaultTab || 'tutorial');

  useEffect(() => {
    if (open && defaultTab) setTab(defaultTab);
  }, [open, defaultTab]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[80] flex items-end sm:items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Dark overlay */}
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

          {/* Panel card */}
          <motion.div
            className="relative w-full max-w-md mx-3 mb-3 sm:mb-0"
            initial={{ y: 60, opacity: 0, scale: 0.95 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 60, opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <div
              className="rounded-2xl border border-cyan-500/20 overflow-hidden"
              style={{ background: 'linear-gradient(180deg, #0d0d10 0%, #111115 100%)', boxShadow: '0 0 60px rgba(0,200,255,0.08)' }}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-4 pt-3 pb-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full relative">
                    <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,30,60,0.9) 40%, transparent 100%)' }} />
                    <img src="/velion.png" alt="Velion" className="w-full h-full object-contain rounded-full relative z-10" style={{ mixBlendMode: 'screen', filter: 'brightness(1.4) contrast(1.3)' }} />
                  </div>
                  <span className="text-[10px] text-cyan-400 font-['Bebas_Neue'] tracking-widest">VELION</span>
                </div>
                <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/10 transition-colors" data-testid="velion-panel-close">
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex px-4 gap-1 pb-2">
                <button
                  onClick={() => setTab('tutorial')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    tab === 'tutorial'
                      ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                      : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                  }`}
                  data-testid="velion-tab-tutorial"
                >
                  <BookOpen className="w-3.5 h-3.5" /> Tutorial
                </button>
                <button
                  onClick={() => setTab('chat')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    tab === 'chat'
                      ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                      : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                  }`}
                  data-testid="velion-tab-chat"
                >
                  <MessageCircle className="w-3.5 h-3.5" /> Chiedi a Velion
                </button>
              </div>

              {/* Tab content */}
              <div style={{ minHeight: '320px', maxHeight: '420px' }} className="flex flex-col">
                {tab === 'tutorial' ? (
                  <TutorialTab onClose={onClose} onNavigate={onNavigate} />
                ) : (
                  <ChatTab />
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function shouldAutoShowTutorial() {
  return localStorage.getItem(LS_TUTORIAL_KEY) !== 'true';
}
