import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './ui/button';
import {
  Film, Flame, Users, FileText, Building, Clapperboard, Globe,
  DollarSign, Puzzle, Swords, BarChart3, Gift, MessageCircle,
  ChevronLeft, ChevronRight, X, Sparkles, Trophy, Zap
} from 'lucide-react';

const LS_TUTORIAL_KEY = 'velion_tutorial_done';

const STEPS = [
  {
    icon: Sparkles, color: 'cyan',
    title: 'Benvenuto in CineWorld!',
    text: 'Io sono Velion, il tuo assistente. Ti guidero\' passo passo nella creazione del tuo impero cinematografico.',
    tip: 'Puoi richiamarmi in qualsiasi momento dal menu!',
  },
  {
    icon: Film, color: 'yellow',
    title: 'Produci il Tuo Film',
    text: 'Dalla sezione "Produci" crei i tuoi film. Scegli titolo, genere, trama e location. Il sistema calcola una qualita\' iniziale.',
    tip: 'Clicca su "Produci" nella barra in basso per iniziare!',
    page: '/create-film',
  },
  {
    icon: Flame, color: 'orange',
    title: 'Coming Soon & Hype',
    text: 'Puoi lanciare il film in Coming Soon: un timer durante il quale accumuli hype, ricevi supporti o boicottaggi da altri player.',
    tip: 'Piu\' tempo = piu\' hype ma anche piu\' rischio!',
  },
  {
    icon: Users, color: 'green',
    title: 'Casting',
    text: 'Dopo il Coming Soon, scegli attori, regista e crew. Piu\' sei forte, migliori talenti hai a disposizione.',
    tip: 'Un buon cast migliora enormemente la qualita\' del film.',
  },
  {
    icon: FileText, color: 'blue',
    title: 'Sceneggiatura',
    text: 'La sceneggiatura viene generata con AI basata sulla tua idea. Le infrastrutture la migliorano.',
    tip: 'Investi nelle infrastrutture per sceneggiature migliori.',
  },
  {
    icon: Building, color: 'amber',
    title: 'Pre-Produzione',
    text: 'Ottimizza il film prima delle riprese: migliora qualita\', riduci costi, aumenta efficienza.',
  },
  {
    icon: Clapperboard, color: 'pink',
    title: 'Ciak, si Gira!',
    text: '"Ciak, si gira!" - Il film entra in lavorazione. Attendi il completamento o accelera con CinePass.',
    tip: 'Le riprese sono l\'ultimo passo prima della distribuzione.',
  },
  {
    icon: Globe, color: 'teal',
    title: 'Distribuzione',
    text: 'Scegli dove lanciare il tuo film: Nazionale, Continentale o Mondiale. Piu\' investi, piu\' guadagni.',
    page: '/my-films',
  },
  {
    icon: DollarSign, color: 'emerald',
    title: 'Incassi & Revenue',
    text: 'I tuoi film generano entrate nel tempo. Ricorda di riscuoterle! I fondi servono per nuovi film e infrastrutture.',
  },
  {
    icon: Zap, color: 'purple',
    title: 'CinePass',
    text: 'I CinePass sono la valuta premium. Accelerano timer, sbloccano feature avanzate e sono necessari per le infrastrutture.',
    tip: 'Ottieni CinePass dai bonus giornalieri e dai Festival!',
  },
  {
    icon: Puzzle, color: 'violet',
    title: 'Infrastrutture',
    text: 'Sblocca: Serie TV, Anime, Scuole di talenti, Emittenti TV, Divisioni PvP (Investigativa, Operativa, Legale).',
    tip: 'Ogni livello apre nuove possibilita\' strategiche.',
    page: '/infrastructure',
  },
  {
    icon: Swords, color: 'red',
    title: 'PvP - Guerra tra Produttori',
    text: 'Non sei solo! Indaga sui rivali, boicotta i loro film, difenditi o fai causa. Usa le Divisioni PvP.',
    page: '/hq',
  },
  {
    icon: Trophy, color: 'yellow',
    title: 'Festival & Premi',
    text: 'Ogni mese ci sono 3 Festival: 1 con voto dei player (come gli Oscar!) e 2 automatici. Vinci premi e la Palma d\'Oro!',
    tip: 'Il tuo voto conta di piu\' se hai livello e fama alti!',
    page: '/festivals',
  },
  {
    icon: BarChart3, color: 'sky',
    title: 'Cresci e Domina',
    text: 'Ogni azione ti fa guadagnare XP, Livelli e Fame. Piu\' cresci, piu\' feature sblocchi.',
  },
  {
    icon: Gift, color: 'yellow',
    title: 'Bonus Giornalieri',
    text: 'Accedi ogni giorno per CinePass gratuiti e vantaggi. Streak consecutivi moltiplicano i bonus!',
  },
  {
    icon: MessageCircle, color: 'indigo',
    title: 'Sei Pronto!',
    text: 'Chat, vota i film degli altri, scala le classifiche. Ora sai tutto: vai e conquista CineWorld!',
    tip: 'Buona fortuna, Produttore!',
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
  indigo: { bg: 'bg-indigo-500/15', text: 'text-indigo-400', border: 'border-indigo-500/30', glow: 'rgba(99,102,241,0.15)' },
};

export function VelionTutorial({ open, onClose, onNavigate }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (open) setStep(0);
  }, [open]);

  const current = STEPS[step];
  const Icon = current.icon;
  const c = COLOR_MAP[current.color] || COLOR_MAP.cyan;
  const isLast = step >= STEPS.length - 1;

  const handleClose = () => {
    localStorage.setItem(LS_TUTORIAL_KEY, 'true');
    setStep(0);
    onClose();
  };

  const next = () => {
    if (isLast) handleClose();
    else setStep(s => s + 1);
  };

  const prev = () => setStep(s => Math.max(0, s - 1));

  const goToPage = () => {
    if (current.page && onNavigate) {
      onNavigate(current.page);
    }
  };

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
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={handleClose} />

          {/* Tutorial card */}
          <motion.div
            className="relative w-full max-w-md mx-3 mb-3 sm:mb-0"
            initial={{ y: 60, opacity: 0, scale: 0.95 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 60, opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <div
              className={`rounded-2xl border ${c.border} overflow-hidden`}
              style={{ background: `linear-gradient(180deg, #0d0d10 0%, #111115 100%)`, boxShadow: `0 0 60px ${c.glow}` }}
            >
              {/* Header with Velion */}
              <div className="flex items-start gap-3 p-4 pb-2">
                {/* Velion avatar */}
                <div className="flex-shrink-0 w-14 h-14 rounded-full relative">
                  <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,30,60,0.9) 40%, transparent 100%)' }} />
                  <img
                    src="/velion.png"
                    alt="Velion"
                    className="w-full h-full object-contain rounded-full relative z-10"
                    style={{ mixBlendMode: 'screen', filter: 'brightness(1.4) contrast(1.3)' }}
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-cyan-400 font-['Bebas_Neue'] tracking-widest">VELION</span>
                    <span className="text-[9px] text-gray-600">{step + 1}/{STEPS.length}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <div className={`w-7 h-7 rounded-lg ${c.bg} flex items-center justify-center`}>
                      <Icon className={`w-4 h-4 ${c.text}`} />
                    </div>
                    <h3 className="font-['Bebas_Neue'] text-lg text-white leading-tight">{current.title}</h3>
                  </div>
                </div>

                {/* Close */}
                <button onClick={handleClose} className="p-1 rounded-lg hover:bg-white/10 transition-colors" data-testid="tutorial-close">
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>

              {/* Progress bar */}
              <div className="px-4 pb-2">
                <div className="h-0.5 bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full`}
                    style={{ background: `linear-gradient(90deg, ${c.glow.replace('0.15', '0.8')}, ${c.glow.replace('0.15', '0.5')})` }}
                    animate={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>

              {/* Content */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={step}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="px-4 pb-3"
                >
                  <p className="text-sm text-gray-300 leading-relaxed">{current.text}</p>
                  {current.tip && (
                    <div className={`mt-2 px-3 py-2 rounded-lg ${c.bg} border ${c.border}`}>
                      <p className={`text-xs ${c.text}`}>{current.tip}</p>
                    </div>
                  )}
                  {current.page && (
                    <button
                      onClick={goToPage}
                      className={`mt-2 text-xs ${c.text} underline underline-offset-2 hover:opacity-80`}
                    >
                      Vai alla pagina →
                    </button>
                  )}
                </motion.div>
              </AnimatePresence>

              {/* Navigation */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-white/5">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={prev}
                  disabled={step === 0}
                  className="text-xs text-gray-400 hover:text-white disabled:opacity-30 h-8"
                >
                  <ChevronLeft className="w-3.5 h-3.5 mr-1" /> Indietro
                </Button>

                <button
                  onClick={handleClose}
                  className="text-[10px] text-gray-600 hover:text-gray-400 transition-colors"
                >
                  Salta
                </button>

                <Button
                  size="sm"
                  onClick={next}
                  className={`text-xs h-8 ${isLast ? 'bg-cyan-500 hover:bg-cyan-400 text-black' : 'bg-white/10 hover:bg-white/20 text-white'}`}
                >
                  {isLast ? 'Inizia!' : 'Avanti'} <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
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
