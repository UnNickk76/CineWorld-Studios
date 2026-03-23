import React, { useState } from 'react';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Film, Palette, Flame, Zap, Clock, Users, FileText, Building,
  Clapperboard, Globe, DollarSign, Puzzle, Swords, BarChart3,
  Gift, MessageCircle, ChevronLeft, ChevronRight, HelpCircle, Play
} from 'lucide-react';

const STEPS = [
  {
    icon: Film, color: 'text-yellow-400 bg-yellow-500/15',
    title: 'Benvenuto, Produttore',
    lines: [
      'Sei alla guida della tua casa di produzione.',
      'Il tuo obiettivo?',
      'Creare film di successo',
      'Battere gli altri player',
      'Costruire un impero cinematografico',
    ],
  },
  {
    icon: FileText, color: 'text-cyan-400 bg-cyan-500/15',
    title: 'Progetta il Tuo Film',
    subtitle: 'Fase Proposta',
    lines: [
      'Qui nasce tutto. Scegli:',
      'Titolo, Genere, Trama, Location',
      'Questa fase rappresenta la tua "idea di film"',
      'Il sistema calcola una qualita\' iniziale (pre-rating)',
    ],
  },
  {
    icon: Palette, color: 'text-purple-400 bg-purple-500/15',
    title: 'Crea la Locandina',
    lines: [
      'Genera il poster del tuo film: e\' cio\' che i player vedranno durante il Coming Soon.',
      'Piu\' e\' forte, piu\' attirerai hype... o boicottaggi',
    ],
  },
  {
    icon: Zap, color: 'text-orange-400 bg-orange-500/15',
    title: 'Scegli Come Rilasciare',
    lines: [
      'Hai 2 modalita\':',
      'IMMEDIATO: vai diretto alla produzione completa.',
      'COMING SOON: il film entra in fase hype con timer attivo, supporti & boicottaggi, eventi casuali.',
      'Piu\' tempo = piu\' hype + piu\' rischio',
    ],
  },
  {
    icon: Flame, color: 'text-red-400 bg-red-500/15',
    title: 'Coming Soon',
    subtitle: 'Fase Hype',
    lines: [
      'Durante il timer succede di tutto:',
      'Supporti: migliorano il film',
      'Boicottaggi: lo danneggiano',
      'Eventi: bonus o malus casuali',
      'Ogni accesso giornaliero ti da\' piccoli bonus automatici',
      'Puoi velocizzare il timer con CinePass',
    ],
  },
  {
    icon: Users, color: 'text-green-400 bg-green-500/15',
    title: 'Casting',
    lines: [
      'Scegli attori, regista e crew.',
      'Piu\' sei forte, migliori talenti disponibili',
      'Puoi aspettare o accelerare con crediti',
    ],
  },
  {
    icon: FileText, color: 'text-blue-400 bg-blue-500/15',
    title: 'Sceneggiatura',
    lines: [
      'La sceneggiatura viene generata con AI.',
      'Basata sulla tua idea',
      'Migliorabile con infrastrutture',
    ],
  },
  {
    icon: Building, color: 'text-amber-400 bg-amber-500/15',
    title: 'Pre-Produzione',
    lines: [
      'Ottimizzi il film prima delle riprese:',
      'Qualita\', costi, efficienza',
    ],
  },
  {
    icon: Clapperboard, color: 'text-pink-400 bg-pink-500/15',
    title: 'Produzione',
    lines: [
      '"Ciak, si gira!"',
      'Il film entra in lavorazione.',
      'Attendi o accelera',
    ],
  },
  {
    icon: Globe, color: 'text-teal-400 bg-teal-500/15',
    title: 'Distribuzione',
    lines: [
      'Scegli dove lanciare il film:',
      'Nazionale, Continentale o Mondiale',
      'Piu\' investi, piu\' guadagni',
    ],
  },
  {
    icon: DollarSign, color: 'text-emerald-400 bg-emerald-500/15',
    title: 'Incassi',
    lines: [
      'I tuoi film generano entrate nel tempo.',
      'Ricorda di riscuoterle!',
    ],
  },
  {
    icon: Puzzle, color: 'text-violet-400 bg-violet-500/15',
    title: 'Infrastrutture',
    subtitle: 'Il Tuo Vero Potere',
    lines: [
      'Sblocchi funzionalita\' avanzate:',
      'Produzione contenuti (Serie TV / Anime)',
      'Scuole e talenti',
      'Emittenti',
      'Investigazione: scopri chi ti boicotta',
      'Operazioni: boicotta o difenditi',
      'Legale: fai causa agli altri player',
      'Piu\' livelli = piu\' potere',
    ],
  },
  {
    icon: Swords, color: 'text-red-400 bg-red-500/15',
    title: 'PvP',
    subtitle: 'Guerra tra Produttori',
    lines: [
      'Non sei solo.',
      'Sfide 1vs1',
      'Boicottaggi',
      'Strategie',
      'Vendette',
    ],
  },
  {
    icon: BarChart3, color: 'text-sky-400 bg-sky-500/15',
    title: 'Cresci e Domina',
    lines: [
      'Ogni azione ti fa guadagnare:',
      'XP, Livelli, Fame',
      'Accesso a nuove feature',
    ],
  },
  {
    icon: Gift, color: 'text-yellow-400 bg-yellow-500/15',
    title: 'Bonus Giornalieri',
    lines: [
      'Accedi ogni giorno per ottenere CinePass e vantaggi.',
    ],
  },
  {
    icon: MessageCircle, color: 'text-indigo-400 bg-indigo-500/15',
    title: 'Social & Classifiche',
    lines: [
      'Chat, Voti ai film, Ranking globale',
      'Diventa il miglior produttore del gioco.',
    ],
  },
];

export function TutorialPopup({ open, onClose }) {
  const [step, setStep] = useState(0);
  const current = STEPS[step];
  const Icon = current.icon;
  const colorClasses = current.color.split(' ');

  const prev = () => setStep(s => Math.max(0, s - 1));
  const next = () => {
    if (step >= STEPS.length - 1) { onClose(); setStep(0); }
    else setStep(s => s + 1);
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { onClose(); setStep(0); } }}>
      <DialogContent className="bg-[#0d0d0f] border border-white/10 max-w-md p-0 overflow-hidden" data-testid="tutorial-popup">
        <DialogTitle className="sr-only">Tutorial CineWorld</DialogTitle>
        <DialogDescription className="sr-only">Guida al gioco</DialogDescription>

        {/* Progress bar */}
        <div className="flex gap-0.5 px-4 pt-4">
          {STEPS.map((_, i) => (
            <div key={i} className={`h-1 flex-1 rounded-full transition-colors ${i <= step ? 'bg-yellow-500' : 'bg-white/10'}`} />
          ))}
        </div>

        {/* Step counter */}
        <div className="px-4 pt-2 flex items-center justify-between">
          <Badge className="bg-white/5 text-gray-400 text-[10px] border border-white/10">{step + 1} / {STEPS.length}</Badge>
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.2 }}
            className="px-5 pb-2 pt-2 min-h-[220px]"
          >
            <div className={`w-12 h-12 rounded-xl ${colorClasses[1]} flex items-center justify-center mb-3`}>
              <Icon className={`w-6 h-6 ${colorClasses[0]}`} />
            </div>
            <h3 className="font-['Bebas_Neue'] text-xl tracking-wide text-white">{current.title}</h3>
            {current.subtitle && <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-2">{current.subtitle}</p>}
            <div className="space-y-1.5 mt-3">
              {current.lines.map((line, i) => (
                <p key={i} className="text-sm text-gray-300 leading-relaxed">{line}</p>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex items-center justify-between p-4 border-t border-white/5">
          <Button variant="ghost" size="sm" className="text-gray-400 h-8"
            disabled={step === 0} onClick={prev} data-testid="tutorial-prev">
            <ChevronLeft className="w-4 h-4 mr-1" /> Indietro
          </Button>
          <Button size="sm" className="bg-yellow-500 text-black h-8 font-bold"
            onClick={next} data-testid="tutorial-next">
            {step >= STEPS.length - 1 ? (
              <><Play className="w-3.5 h-3.5 mr-1" /> Inizia a Giocare</>
            ) : (
              <>Avanti <ChevronRight className="w-4 h-4 ml-1" /></>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
