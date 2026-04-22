import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Shield, ShieldCheck, Search, DollarSign, Coins, ChevronRight, Minus, Plus, Film, Users, Trash2, AlertTriangle, X, Loader2, Flag, Eye, CheckCircle, XCircle, Wrench, Crown, Star, UserCog, Clock, Ban, Upload, Download, RefreshCw, FlaskConical, Swords, Sparkles, Zap, Play, Trophy, Check, ArrowRightLeft, BookOpen, Lock, Heart, Image as ImageIcon, Video } from 'lucide-react';
import { AuthContext } from '../contexts';
import { useConfirm } from '../components/ConfirmDialog';
import { PlayerBadge } from '../components/PlayerBadge';
import AdminFilmRecovery from '../components/AdminFilmRecovery';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

/* ─── Tab config by role ─── */
const ADMIN_TABS = [
  { id: 'users', label: 'Gestione Utenti', icon: Users },
  { id: 'films', label: 'Gestione Film', icon: Film },
  { id: 'roles', label: 'Gestione Ruoli', icon: UserCog },
  { id: 'reports', label: 'Segnalazioni', icon: Flag },
  { id: 'deletions', label: 'Cancellazioni', icon: Trash2 },
  { id: 'maintenance', label: 'Manutenzione', icon: Wrench },
  { id: 'donations', label: 'Donazioni', icon: Heart },
  { id: 'tutorial', label: 'Tutorial Manager', icon: BookOpen },
  { id: 'migration', label: 'Migrazione', icon: ArrowRightLeft },
  { id: 'ai-providers', label: 'AI Providers', icon: ImageIcon },
  { id: 'promo-video', label: 'Promo Video', icon: Video },
  { id: 'testlab', label: 'Test Lab', icon: FlaskConical },
  { id: 'recovery', label: 'Anti-Limbo', icon: AlertTriangle },
  { id: 'reset', label: 'Reset Gioco', icon: Trash2 },
];

const COADMIN_TABS = [
  { id: 'reports', label: 'Segnalazioni', icon: Flag },
  { id: 'maintenance', label: 'Manutenzione', icon: Wrench },
];


/* ─── Test Lab ─── */
import VelionCinematicEvent from '../components/VelionCinematicEvent';
import { ReleaseCinematic } from '../components/ReleaseCinematic';
import { motion, AnimatePresence } from 'framer-motion';
import { TapCiak, MemoryPro, StopPerfetto, SpamClick, ReactionGame, ShotPerfect, LightSetup, CastMatch, EditingCut, FollowCam, ChaosPremiere, ReelSnake } from '../components/MiniGames';
import { Timer, Target, Brain, MousePointerClick } from 'lucide-react';

const MOCK_EVENTS = {
  common: {
    id: 'test_common', tier: 'common', event_type: 'positive', project_type: 'film',
    film_title: 'Test Film Alpha', movie_title: 'Test Film Alpha', actor_name: 'Marco Rossi',
    text: 'Il tuo film ha ricevuto ottime recensioni dalla critica indie!',
    revenue_mod: 0.15, hype_mod: 3, fame_mod: 1,
  },
  epic: {
    id: 'test_epic', tier: 'epic', event_type: 'positive', project_type: 'series',
    film_title: 'Test Serie Beta', movie_title: 'Test Serie Beta', actor_name: 'Giulia Bianchi',
    text: 'La tua serie diventa virale sui social! Milioni di visualizzazioni in poche ore.',
    revenue_mod: 0.35, hype_mod: 8, fame_mod: 5,
  },
  legendary: {
    id: 'test_legendary', tier: 'legendary', event_type: 'star_born', project_type: 'film',
    film_title: 'Test Film Omega', movie_title: 'Test Film Omega', actor_name: 'Alessandro De Niro',
    text: 'LEGGENDA! Il tuo film viene nominato per 12 Oscar e batte ogni record mondiale!',
    revenue_mod: 0.75, hype_mod: 15, fame_mod: 12,
  },
};

const MOCK_RELEASE = {
  title: 'Il Grande Sogno', quality_score: 87, opening_day_revenue: 2450000,
  hype_level: 72, release_outcome: 'success',
  screenplay_scenes: ['Il protagonista scopre la verita', 'La fuga', 'Il confronto finale'],
  release_event: { id: 'premiere_buzz', text: 'Standing ovation alla premiere!' },
  genre: 'Dramma', audience_score: 91, total_revenue: 14500000,
};

const HISTORY_LABELS = {
  film: 'Pipeline film simulata', contest: 'Contest simulato',
  event_common: 'Evento comune simulato', event_epic: 'Evento epico simulato',
  event_legendary: 'Evento leggendario simulato', arena: 'Arena simulata', major: 'Major simulata',
};
const HISTORY_ICONS = {
  film: Film, contest: Trophy, event_common: Sparkles, event_epic: Sparkles,
  event_legendary: Sparkles, arena: Swords, major: Crown,
};

/* ── Arena Sim (Manual) ── */
function ArenaSimOverlay({ onClose }) {
  const [phase, setPhase] = useState('choose');
  const [action, setAction] = useState(null);
  const outcome = useRef(Math.random() > 0.4 ? 'win' : 'lose');

  const execute = (act) => {
    setAction(act);
    setPhase('executing');
    setTimeout(() => setPhase('result'), 1800);
  };

  return (
    <motion.div className="fixed inset-0 z-[600] flex items-center justify-center bg-black/95" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <div className="w-[90%] max-w-sm space-y-4 text-center">
        <AnimatePresence mode="wait">
          {phase === 'choose' && <motion.div key="ch" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
            <Swords className="w-10 h-10 mx-auto text-red-400" />
            <p className="text-sm font-bold text-white">Scegli la tua azione</p>
            <div className="space-y-2">
              <Button className="w-full bg-green-600/20 border border-green-500/30 text-green-400 h-11" onClick={() => execute('support')} data-testid="arena-support"><Shield className="w-4 h-4 mr-2" /> Supporta il tuo film</Button>
              <Button className="w-full bg-red-600/20 border border-red-500/30 text-red-400 h-11" onClick={() => execute('boycott')} data-testid="arena-boycott"><Swords className="w-4 h-4 mr-2" /> Boicotta il rivale</Button>
              <Button className="w-full bg-purple-600/20 border border-purple-500/30 text-purple-400 h-11" onClick={() => execute('counter')} data-testid="arena-counter"><Shield className="w-4 h-4 mr-2" /> Contromossa difensiva</Button>
            </div>
            <Button variant="ghost" size="sm" className="text-xs text-gray-600" onClick={onClose}>Annulla</Button>
          </motion.div>}
          {phase === 'executing' && <motion.div key="ex" initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="space-y-3">
            <div className="flex items-center justify-center gap-6">
              <div className="text-center"><div className="w-14 h-14 rounded-full bg-cyan-500/20 flex items-center justify-center border border-cyan-500/40"><Users className="w-6 h-6 text-cyan-400" /></div><p className="text-[10px] text-cyan-400 mt-1">Tu</p></div>
              <motion.div animate={{ x: [-5, 5, -5] }} transition={{ repeat: Infinity, duration: 0.3 }}><Swords className="w-8 h-8 text-red-500" /></motion.div>
              <div className="text-center"><div className="w-14 h-14 rounded-full bg-red-500/20 flex items-center justify-center border border-red-500/40"><Users className="w-6 h-6 text-red-400" /></div><p className="text-[10px] text-red-400 mt-1">Rivale</p></div>
            </div>
            <p className="text-xs text-gray-400">{action === 'support' ? 'Supporto in corso...' : action === 'boycott' ? 'Attacco in corso...' : 'Difesa attivata...'}</p>
          </motion.div>}
          {phase === 'result' && <motion.div key="res" initial={{ scale: 1.2, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="space-y-3">
            {outcome.current === 'win' ? <>
              <Trophy className="w-14 h-14 mx-auto text-yellow-400" />
              <p className="text-lg font-bold text-yellow-400">SUCCESSO!</p>
              <p className="text-xs text-gray-400">Azione {action} riuscita</p>
              <div className="flex justify-center gap-2 text-[10px]"><span className="bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">+5 Fama</span><span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">-15% Hype rivale</span></div>
            </> : <>
              <Shield className="w-14 h-14 mx-auto text-orange-400" />
              <p className="text-lg font-bold text-orange-400">BLOCCATO!</p>
              <p className="text-xs text-gray-400">Il rivale ha parato</p>
            </>}
            <Button size="sm" variant="outline" className="border-gray-700 text-xs mt-2" onClick={onClose} data-testid="arena-sim-close">Chiudi</Button>
          </motion.div>}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

/* ── Major Sim (Manual) ── */
function MajorSimOverlay({ onClose }) {
  const [phase, setPhase] = useState('menu');
  const [action, setAction] = useState(null);
  const execute = (act) => { setAction(act); setPhase('exec'); setTimeout(() => setPhase('result'), 2000); };

  return (
    <motion.div className="fixed inset-0 z-[600] flex items-center justify-center bg-black/95" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <div className="w-[90%] max-w-sm space-y-4 text-center">
        <AnimatePresence mode="wait">
          {phase === 'menu' && <motion.div key="m" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
            <Crown className="w-10 h-10 mx-auto text-yellow-400" />
            <p className="text-sm font-bold text-white">Gestione Major — Test</p>
            <div className="bg-[#1a1a1b] rounded-xl border border-yellow-500/20 p-3"><p className="text-xs text-yellow-400 font-bold">DREAMWORKS TEST</p><div className="flex justify-center gap-4 mt-2 text-[10px] text-gray-400"><span>3 Membri</span><span>Lv. 5</span><span>Rep: 850</span></div></div>
            <div className="space-y-2">
              <Button className="w-full bg-yellow-600/20 border border-yellow-500/30 text-yellow-400 h-10 text-xs" onClick={() => execute('challenge')} data-testid="major-challenge"><Swords className="w-4 h-4 mr-2" /> Sfida Major rivale</Button>
              <Button className="w-full bg-green-600/20 border border-green-500/30 text-green-400 h-10 text-xs" onClick={() => execute('recruit')} data-testid="major-recruit"><Users className="w-4 h-4 mr-2" /> Recluta membro</Button>
              <Button className="w-full bg-cyan-600/20 border border-cyan-500/30 text-cyan-400 h-10 text-xs" onClick={() => execute('invest')} data-testid="major-invest"><DollarSign className="w-4 h-4 mr-2" /> Investi in produzione</Button>
            </div>
            <Button variant="ghost" size="sm" className="text-xs text-gray-600" onClick={onClose}>Annulla</Button>
          </motion.div>}
          {phase === 'exec' && <motion.div key="e" initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}><motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}><Loader2 className="w-10 h-10 mx-auto text-yellow-400" /></motion.div><p className="text-xs text-gray-400 mt-2">{action === 'challenge' ? 'Sfida in corso...' : action === 'recruit' ? 'Reclutamento...' : 'Investimento...'}</p></motion.div>}
          {phase === 'result' && <motion.div key="r" initial={{ scale: 1.2, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="space-y-3">
            <Trophy className="w-12 h-12 mx-auto text-yellow-400" />
            <p className="text-base font-bold text-yellow-400">{action === 'challenge' ? 'Sfida Vinta!' : action === 'recruit' ? 'Membro Reclutato!' : 'Investimento Riuscito!'}</p>
            <div className="flex justify-center gap-2 flex-wrap text-[10px]">
              {action === 'challenge' && <><span className="bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">+120 Rep</span><span className="bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full">+3 Fama</span></>}
              {action === 'recruit' && <span className="bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded-full">+1 Membro</span>}
              {action === 'invest' && <span className="bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">+50k Fondi</span>}
            </div>
            <Button size="sm" variant="outline" className="border-gray-700 text-xs mt-2" onClick={onClose} data-testid="major-sim-close">Chiudi</Button>
          </motion.div>}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

/* ── Film Pipeline Sim (Interactive) ── */
function FilmPipelineSimOverlay({ onClose }) {
  const [step, setStep] = useState(0);
  const [choices, setChoices] = useState({});
  const [showRelease, setShowRelease] = useState(false);
  const PIPELINE = [
    { title: 'Sceneggiatura', desc: 'Scegli il tipo di script', options: ['Dramma originale', 'Thriller psicologico', 'Commedia romantica'] },
    { title: 'Hype & Sponsor', desc: 'Strategia di promozione', options: ['Campagna viral social', 'Partnership con brand', 'Premiere esclusiva VIP'] },
    { title: 'Location La Prima', desc: 'Scegli la citta della premiere', options: ['Roma', 'Los Angeles', 'Cannes'] },
    { title: 'Rilascio', desc: 'Conferma il rilascio nelle sale', options: ['Rilascia ora!'] },
  ];
  const choose = (option) => { setChoices(prev => ({ ...prev, [step]: option })); if (step < PIPELINE.length - 1) setStep(step + 1); else setShowRelease(true); };

  if (showRelease) {
    return (
      <motion.div className="fixed inset-0 z-[600] bg-black/95 flex items-center justify-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div className="w-[95%] max-w-md"><ReleaseCinematic data={MOCK_RELEASE} onClose={onClose} directorName="Mario Rossi Test" /></div>
      </motion.div>
    );
  }
  const p = PIPELINE[step];
  return (
    <motion.div className="fixed inset-0 z-[600] flex items-center justify-center bg-black/95" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <div className="w-[90%] max-w-sm space-y-4">
        <div className="flex items-center justify-between"><p className="text-xs text-gray-400">Step {step + 1}/{PIPELINE.length}</p><Button variant="ghost" size="sm" className="text-[10px] text-gray-600" onClick={onClose}>Esci</Button></div>
        <div className="h-1 bg-gray-800 rounded-full overflow-hidden"><motion.div className="h-full bg-cyan-500" animate={{ width: `${((step + 1) / PIPELINE.length) * 100}%` }} /></div>
        <motion.div key={step} initial={{ x: 30, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="bg-[#1a1a1b] rounded-xl border border-gray-800 p-4 space-y-3">
          <div className="flex items-center gap-2"><Film className="w-5 h-5 text-cyan-400" /><div><p className="text-sm font-bold text-white">{p.title}</p><p className="text-[10px] text-gray-500">{p.desc}</p></div></div>
          <div className="space-y-2">{p.options.map(opt => (
            <Button key={opt} variant="outline" className="w-full border-gray-700 text-xs h-10 hover:bg-cyan-500/10 hover:border-cyan-500/30 justify-start" onClick={() => choose(opt)} data-testid={`pipeline-opt-${opt}`}>{opt}</Button>
          ))}</div>
        </motion.div>
        {Object.entries(choices).map(([k, v]) => (<div key={k} className="flex items-center gap-2 text-[10px] text-gray-600"><Check className="w-3 h-3 text-green-500" /> {PIPELINE[k].title}: <span className="text-gray-400">{v}</span></div>))}
      </div>
    </motion.div>
  );
}

/* ── Contest Sim (Real Games) ── */
function ContestSimOverlay({ onClose }) {
  const [gameIdx, setGameIdx] = useState(0);
  const [scores, setScores] = useState([]);
  const [done, setDone] = useState(false);
  const GAMES = [
    { name: 'TapCiak', Game: TapCiak },
    { name: 'Memory Pro', Game: MemoryPro },
    { name: 'Stop Perfetto', Game: StopPerfetto },
    { name: 'Spam Click', Game: SpamClick },
    { name: 'Reaction', Game: ReactionGame },
    { name: 'Shot Perfect', Game: ShotPerfect },
    { name: 'Light Setup', Game: LightSetup },
    { name: 'Cast Match', Game: CastMatch },
    { name: 'Editing Cut', Game: EditingCut },
    { name: 'Follow Cam', Game: FollowCam },
    { name: 'Chaos Premiere', Game: ChaosPremiere },
    { name: 'Reel Snake', Game: ReelSnake },
  ];

  const handleFinish = (score) => {
    const newScores = [...scores, score];
    setScores(newScores);
    if (gameIdx + 1 >= GAMES.length) setDone(true); else setGameIdx(gameIdx + 1);
  };

  if (done) {
    const total = scores.reduce((a, b) => a + b, 0);
    return (
      <motion.div className="fixed inset-0 z-[600] flex items-center justify-center bg-black/95" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="w-[90%] max-w-sm text-center space-y-4">
          <Trophy className="w-14 h-14 mx-auto text-yellow-400" />
          <p className="text-lg font-bold text-yellow-400">Contest Test completato!</p>
          <p className="text-sm text-gray-400">Totale: <span className="text-white font-bold">{total}</span> punti</p>
          <div className="space-y-1">{GAMES.map((g, i) => (<div key={i} className="flex justify-between text-[10px] text-gray-500 px-2"><span>{g.name}</span><span className="text-white">{scores[i] || 0} pt</span></div>))}</div>
          <p className="text-[10px] text-gray-600">(Test mode — nessun salvataggio)</p>
          <Button size="sm" variant="outline" className="border-gray-700 text-xs" onClick={onClose} data-testid="contest-sim-close">Chiudi</Button>
        </motion.div>
      </motion.div>
    );
  }

  const { name, Game } = GAMES[gameIdx];
  return (
    <motion.div className="fixed inset-0 z-[600] flex items-center justify-center bg-black/95 p-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="w-full max-w-sm space-y-3">
        <div className="flex items-center justify-between"><p className="text-xs text-gray-400">Step {gameIdx + 1}/{GAMES.length} — {name}</p><Button variant="ghost" size="sm" className="text-[10px] text-gray-600" onClick={onClose}>Esci</Button></div>
        <div className="h-1 bg-gray-800 rounded-full overflow-hidden"><motion.div className="h-full bg-cyan-500" animate={{ width: `${((gameIdx + 1) / GAMES.length) * 100}%` }} /></div>
        <div className="bg-[#1a1a1b] rounded-xl border border-gray-800 p-4"><Game key={gameIdx} onFinish={handleFinish} /></div>
      </div>
    </motion.div>
  );
}

/* ── TestLab Main Tab ── */
function TestLabTab() {
  const [activeSim, setActiveSim] = useState(null);
  const [history, setHistory] = useState([]);
  const launchSim = (type) => { setActiveSim(type); setHistory(prev => [{ type, ts: new Date() }, ...prev].slice(0, 20)); };
  const closeSim = () => setActiveSim(null);

  const BUTTONS = [
    { id: 'film', label: 'Film Pipeline', icon: Film, color: 'hover:bg-cyan-500/10 hover:border-cyan-500/30' },
    { id: 'contest', label: 'Contest', icon: Trophy, color: 'hover:bg-yellow-500/10 hover:border-yellow-500/30' },
    { id: 'event_common', label: 'Evento Comune', icon: Sparkles, color: 'hover:bg-gray-400/10 hover:border-gray-400/30' },
    { id: 'event_epic', label: 'Evento Epico', icon: Sparkles, color: 'hover:bg-purple-500/10 hover:border-purple-500/30' },
    { id: 'event_legendary', label: 'Evento Leggendario', icon: Sparkles, color: 'hover:bg-yellow-500/10 hover:border-yellow-500/30' },
    { id: 'arena', label: 'Arena', icon: Swords, color: 'hover:bg-red-500/10 hover:border-red-500/30' },
    { id: 'major', label: 'Major', icon: Crown, color: 'hover:bg-yellow-500/10 hover:border-yellow-500/30' },
  ];

  return (
    <>
      <Card className="bg-[#111113] border-white/5" data-testid="testlab-tab">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2"><FlaskConical className="w-4 h-4 text-emerald-400" /> Test Lab</CardTitle>
          <p className="text-[10px] text-gray-500">Sandbox visiva — nessun impatto su DB o dati reali</p>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            {BUTTONS.map(b => { const Icon = b.icon; return (
              <Button key={b.id} size="sm" variant="outline" className={`text-xs border-gray-700 h-10 gap-1.5 ${b.color}`} onClick={() => launchSim(b.id)} data-testid={`test-btn-${b.id}`}><Icon className="w-3.5 h-3.5" /> {b.label}</Button>
            ); })}
          </div>
          {history.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-white/5">
              <p className="text-[10px] text-gray-500 font-semibold">Storico simulazioni</p>
              {history.slice(0, 8).map((h, i) => { const Icon = HISTORY_ICONS[h.type] || Sparkles; return (
                <motion.div key={`${h.type}-${i}`} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-2 py-1.5 px-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] cursor-pointer border border-transparent hover:border-white/5 transition-colors"
                  onClick={() => launchSim(h.type)} data-testid={`history-${i}`}>
                  <Icon className="w-3.5 h-3.5 text-gray-500 shrink-0" />
                  <span className="text-[11px] text-gray-300 flex-1">{HISTORY_LABELS[h.type]}</span>
                  <span className="text-[9px] text-gray-600">{h.ts.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}</span>
                  <ChevronRight className="w-3 h-3 text-gray-700" />
                </motion.div>
              ); })}
            </div>
          )}
        </CardContent>
      </Card>
      <AnimatePresence>
        {activeSim === 'film' && <FilmPipelineSimOverlay onClose={closeSim} />}
        {activeSim === 'contest' && <ContestSimOverlay onClose={closeSim} />}
        {activeSim === 'arena' && <ArenaSimOverlay onClose={closeSim} />}
        {activeSim === 'major' && <MajorSimOverlay onClose={closeSim} />}
      </AnimatePresence>
      {activeSim === 'event_common' && <VelionCinematicEvent events={[MOCK_EVENTS.common]} onAllDone={closeSim} />}
      {activeSim === 'event_epic' && <VelionCinematicEvent events={[MOCK_EVENTS.epic]} onAllDone={closeSim} />}
      {activeSim === 'event_legendary' && <VelionCinematicEvent events={[MOCK_EVENTS.legendary]} onAllDone={closeSim} />}
    </>
  );
}

/* ─── Confirm Modal ─── */
function ConfirmModal({ open, title, message, onConfirm, onCancel, loading }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" data-testid="confirm-modal">
      <Card className="bg-[#111113] border-red-500/40 max-w-sm w-full">
        <CardContent className="p-5 space-y-4">
          <div className="flex items-center gap-2 text-red-400">
            <AlertTriangle className="w-5 h-5" />
            <span className="text-sm font-bold">{title}</span>
          </div>
          <p className="text-xs text-gray-300 leading-relaxed">{message}</p>
          <div className="flex gap-2 justify-end">
            <Button size="sm" variant="outline" className="text-xs border-gray-700 text-gray-400 hover:bg-gray-800"
              onClick={onCancel} disabled={loading} data-testid="confirm-cancel-btn">
              Annulla
            </Button>
            <Button size="sm" className="bg-red-600 hover:bg-red-700 text-xs" onClick={onConfirm} disabled={loading}
              data-testid="confirm-delete-btn">
              {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3 mr-1" />}
              Conferma Eliminazione
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/* ─── Users Tab ─── */
function UsersTab({ api }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [moneyAmount, setMoneyAmount] = useState('');
  const [cpAmount, setCpAmount] = useState('');
  const [actionLoading, setActionLoading] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);

  const searchUsers = useCallback(async (q) => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/search-users?q=${encodeURIComponent(q)}`);
      setUsers(res.data.users || []);
    } catch { toast.error('Errore ricerca'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { searchUsers(''); }, [searchUsers]);

  const handleSearch = (e) => { e.preventDefault(); searchUsers(searchQuery); };

  const modifyFunds = async (nickname, amount) => {
    if (!amount || isNaN(amount)) return;
    setActionLoading(`money-${nickname}`);
    try {
      const res = await api.post('/admin/add-money', { nickname, amount: Number(amount) });
      toast.success(`${nickname}: $${res.data.old_funds.toLocaleString()} → $${res.data.new_funds.toLocaleString()}`);
      setMoneyAmount('');
      searchUsers(searchQuery);
      if (selectedUser?.nickname === nickname) setSelectedUser(prev => ({ ...prev, funds: res.data.new_funds }));
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const modifyCinepass = async (nickname, amount) => {
    if (!amount || isNaN(amount)) return;
    setActionLoading(`cp-${nickname}`);
    try {
      const res = await api.post('/admin/add-cinepass', { nickname, amount: Number(amount) });
      toast.success(`${nickname}: ${res.data.old_cinepass} CP → ${res.data.new_cinepass} CP`);
      setCpAmount('');
      searchUsers(searchQuery);
      if (selectedUser?.nickname === nickname) setSelectedUser(prev => ({ ...prev, cinepass: res.data.new_cinepass }));
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const handleDeleteUser = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      const res = await api.delete(`/admin/delete-user/${deleteTarget.id}`);
      const d = res.data;
      toast.success(`Utente "${deleteTarget.nickname}" eliminato. Contenuti rimossi: ${Object.entries(d.deleted_content || {}).map(([k,v]) => `${k}:${v}`).join(', ') || 'nessuno'}`);
      setDeleteTarget(null);
      if (selectedUser?.id === deleteTarget.id) setSelectedUser(null);
      searchUsers(searchQuery);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore eliminazione'); }
    finally { setDeleteLoading(false); }
  };

  return (
    <div className="space-y-3" data-testid="admin-users-tab">
      <ConfirmModal
        open={!!deleteTarget}
        title="Eliminazione Definitiva Utente"
        message={`Confermi eliminazione definitiva di "${deleteTarget?.nickname}" (${deleteTarget?.email})? Verranno eliminati TUTTI i dati collegati: film, serie TV, anime, classifiche, profilo. Questa azione e' IRREVERSIBILE.`}
        onConfirm={handleDeleteUser}
        onCancel={() => setDeleteTarget(null)}
        loading={deleteLoading}
      />

      {/* Search */}
      <form onSubmit={handleSearch}>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              placeholder="Cerca per username..."
              className="w-full bg-[#111113] border border-gray-800 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none"
              data-testid="admin-search-input" />
          </div>
          <Button type="submit" size="sm" className="bg-red-600 hover:bg-red-700 text-xs px-3" disabled={loading}
            data-testid="admin-search-btn">
            {loading ? '...' : 'Cerca'}
          </Button>
        </div>
      </form>

      {/* User list */}
      <div className="space-y-1.5 max-h-[40vh] overflow-y-auto" data-testid="admin-user-list">
        {users.map(u => (
          <Card key={u.id}
            className={`bg-[#111113] cursor-pointer transition-all ${selectedUser?.id === u.id ? 'border-red-500/40 ring-1 ring-red-500/20' : 'border-white/5 hover:border-gray-700'}`}
            onClick={() => { setSelectedUser(u); setMoneyAmount(''); setCpAmount(''); }}
            data-testid={`admin-user-${u.nickname}`}>
            <CardContent className="p-2.5 flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-500/20 to-orange-500/20 flex items-center justify-center text-xs font-bold text-red-400 flex-shrink-0">
                {u.nickname?.[0]?.toUpperCase() || '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <PlayerBadge badge={u.badge} badgeExpiry={u.badge_expiry} badges={u.badges} size="sm" />
                  <span className="text-xs font-semibold truncate">{u.nickname}</span>
                  {u.role && <Badge className="text-[7px] h-3.5 bg-purple-500/20 text-purple-400">{u.role}</Badge>}
                </div>
                <p className="text-[9px] text-gray-500 truncate">{u.production_house_name || u.email}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-[10px] text-yellow-400 font-mono">${(u.funds || 0).toLocaleString()}</p>
                <p className="text-[9px] text-cyan-400 font-mono">{u.cinepass || 0} CP</p>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
            </CardContent>
          </Card>
        ))}
        {users.length === 0 && !loading && (
          <p className="text-center text-xs text-gray-600 py-4">Nessun utente trovato</p>
        )}
      </div>

      {/* Selected user panel */}
      {selectedUser && (
        <Card className="bg-[#0e0e10] border-red-500/30" data-testid="admin-user-panel">
          <CardHeader className="pb-2 pt-3 px-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-red-500/30 to-orange-500/30 flex items-center justify-center text-xs font-bold text-red-400">
                {selectedUser.nickname?.[0]?.toUpperCase()}
              </div>
              <span className="flex-1">{selectedUser.nickname}</span>
              <Button size="sm" variant="ghost" className="text-red-400 hover:text-red-300 hover:bg-red-500/10 h-7 px-2 text-[10px]"
                onClick={(e) => { e.stopPropagation(); setDeleteTarget(selectedUser); }}
                data-testid="admin-delete-user-btn">
                <Trash2 className="w-3 h-3 mr-1" /> Elimina
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0 space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2 rounded-lg bg-yellow-500/5 border border-yellow-500/20 text-center">
                <DollarSign className="w-3.5 h-3.5 text-yellow-400 mx-auto mb-0.5" />
                <p className="text-sm font-bold text-yellow-400">${(selectedUser.funds || 0).toLocaleString()}</p>
                <p className="text-[8px] text-gray-500">DENARO</p>
              </div>
              <div className="p-2 rounded-lg bg-cyan-500/5 border border-cyan-500/20 text-center">
                <Coins className="w-3.5 h-3.5 text-cyan-400 mx-auto mb-0.5" />
                <p className="text-sm font-bold text-cyan-400">{selectedUser.cinepass || 0}</p>
                <p className="text-[8px] text-gray-500">CINEPASS</p>
              </div>
            </div>

            {/* Money controls */}
            <div className="space-y-1.5">
              <p className="text-[10px] text-yellow-400 font-semibold flex items-center gap-1"><DollarSign className="w-3 h-3" /> Modifica Denaro</p>
              <div className="flex gap-1.5">
                <input type="number" value={moneyAmount} onChange={e => setMoneyAmount(e.target.value)}
                  placeholder="Importo (es: 1000000)"
                  className="flex-1 bg-black/40 border border-gray-700 rounded px-2 py-1.5 text-xs text-white focus:border-yellow-500/50 focus:outline-none"
                  data-testid="admin-money-input" />
                <Button size="sm" className="bg-emerald-700 hover:bg-emerald-600 text-[10px] h-7 px-2"
                  onClick={() => modifyFunds(selectedUser.nickname, Math.abs(Number(moneyAmount)))}
                  disabled={!moneyAmount || actionLoading} data-testid="admin-money-add">
                  <Plus className="w-3 h-3" />
                </Button>
                <Button size="sm" className="bg-red-700 hover:bg-red-600 text-[10px] h-7 px-2"
                  onClick={() => modifyFunds(selectedUser.nickname, -Math.abs(Number(moneyAmount)))}
                  disabled={!moneyAmount || actionLoading} data-testid="admin-money-remove">
                  <Minus className="w-3 h-3" />
                </Button>
              </div>
            </div>

            {/* CinePass controls */}
            <div className="space-y-1.5">
              <p className="text-[10px] text-cyan-400 font-semibold flex items-center gap-1"><Coins className="w-3 h-3" /> Modifica CinePass</p>
              <div className="flex gap-1.5">
                <input type="number" value={cpAmount} onChange={e => setCpAmount(e.target.value)}
                  placeholder="Quantita (es: 50)"
                  className="flex-1 bg-black/40 border border-gray-700 rounded px-2 py-1.5 text-xs text-white focus:border-cyan-500/50 focus:outline-none"
                  data-testid="admin-cp-input" />
                <Button size="sm" className="bg-emerald-700 hover:bg-emerald-600 text-[10px] h-7 px-2"
                  onClick={() => modifyCinepass(selectedUser.nickname, Math.abs(Number(cpAmount)))}
                  disabled={!cpAmount || actionLoading} data-testid="admin-cp-add">
                  <Plus className="w-3 h-3" />
                </Button>
                <Button size="sm" className="bg-red-700 hover:bg-red-600 text-[10px] h-7 px-2"
                  onClick={() => modifyCinepass(selectedUser.nickname, -Math.abs(Number(cpAmount)))}
                  disabled={!cpAmount || actionLoading} data-testid="admin-cp-remove">
                  <Minus className="w-3 h-3" />
                </Button>
              </div>
            </div>

            {/* Badge controls */}
            <div className="space-y-1.5">
              <p className="text-[10px] text-amber-400 font-semibold flex items-center gap-1"><Crown className="w-3 h-3" /> Badge Utente</p>
              <p className="text-[8px] text-gray-500">Attuale: <span className="text-amber-300">{selectedUser.badge || 'none'}</span> {selectedUser.badge_expiry && selectedUser.badge !== 'none' ? `(scade: ${new Date(selectedUser.badge_expiry).toLocaleDateString()})` : ''}</p>
              <div className="flex gap-1.5">
                {[{ val: 'none', label: 'Nessuno', cls: 'bg-gray-700 hover:bg-gray-600' }, { val: 'cinevip', label: 'CineVIP', cls: 'bg-yellow-700 hover:bg-yellow-600' }, { val: 'cinestar', label: 'CineSTAR', cls: 'bg-amber-600 hover:bg-amber-500' }].map(b => (
                  <Button key={b.val} size="sm" className={`text-[10px] h-7 px-2 flex-1 ${b.cls} ${selectedUser.badge === b.val ? 'ring-1 ring-white/40' : ''}`}
                    disabled={actionLoading}
                    onClick={async () => {
                      setActionLoading('badge');
                      try {
                        await api.post('/admin/set-badge', { nickname: selectedUser.nickname, badge: b.val });
                        toast.success(`Badge ${b.label} assegnato a ${selectedUser.nickname}`);
                        setSelectedUser(prev => ({ ...prev, badge: b.val, badge_expiry: b.val === 'none' ? null : new Date(Date.now() + 7*24*60*60*1000).toISOString() }));
                        searchUsers(searchQuery);
                      } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
                      setActionLoading(null);
                    }}
                    data-testid={`admin-badge-${b.val}`}>
                    {b.val === 'cinevip' && <Crown className="w-3 h-3 mr-0.5" />}
                    {b.val === 'cinestar' && <Star className="w-3 h-3 mr-0.5" />}
                    {b.label}
                  </Button>
                ))}
              </div>
              <p className="text-[8px] text-gray-600">Durata: 7 giorni dalla assegnazione</p>
            </div>

            {/* Permanent Badge controls */}
            <div className="space-y-1.5">
              <p className="text-[10px] text-red-400 font-semibold flex items-center gap-1"><Shield className="w-3 h-3" /> Badge Permanenti</p>
              <div className="flex gap-1.5">
                {[
                  { key: 'cineadmin', label: 'CineADMIN', icon: Shield, cls: 'bg-red-800 hover:bg-red-700', activeCls: 'ring-1 ring-red-400', color: 'text-red-400', role: 'CO_ADMIN' },
                  { key: 'cinemod', label: 'CineMOD', icon: ShieldCheck, cls: 'bg-blue-800 hover:bg-blue-700', activeCls: 'ring-1 ring-blue-400', color: 'text-blue-400', role: 'MODERATOR' },
                ].map(b => {
                  const isActive = selectedUser.badges?.[b.key];
                  return (
                    <Button key={b.key} size="sm" className={`text-[10px] h-7 px-2 flex-1 ${b.cls} ${isActive ? b.activeCls : 'opacity-60'}`}
                      disabled={actionLoading}
                      onClick={() => {
                        setConfirmAction({
                          title: isActive ? `Rimuovi ${b.label}` : `Assegna ${b.label}`,
                          message: isActive
                            ? `Rimuovere ${b.label} e il ruolo ${b.role} da ${selectedUser.nickname}?`
                            : `Assegnare ${b.label} con ruolo ${b.role} a ${selectedUser.nickname}? Questo utente avrà permessi ${b.key === 'cineadmin' ? 'di co-amministratore' : 'di moderazione'}.`,
                          onConfirm: async () => {
                            setActionLoading('perm-badge');
                            try {
                              const res = await api.post('/admin/set-perm-badge', { nickname: selectedUser.nickname, badge_type: b.key, active: !isActive });
                              toast.success(res.data.message || `${b.label} ${!isActive ? 'assegnato' : 'rimosso'}`);
                              setSelectedUser(prev => ({ ...prev, badges: { ...prev.badges, [b.key]: !isActive }, role: res.data.role || prev.role }));
                              searchUsers(searchQuery);
                            } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
                            setActionLoading(null);
                          },
                        });
                      }}
                      data-testid={`admin-perm-${b.key}`}>
                      <b.icon className={`w-3 h-3 mr-0.5 ${b.color}`} />
                      {isActive ? `Rimuovi ${b.label}` : `Assegna ${b.label}`}
                    </Button>
                  );
                })}
              </div>
              <p className="text-[8px] text-gray-600">Permanenti — rimovibili solo manualmente. Assegnano anche il ruolo effettivo.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Confirm Dialog (our custom one) */}
      {confirmAction && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }} onClick={() => setConfirmAction(null)}>
          <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.7)' }} />
          <div style={{ position: 'relative', width: '100%', maxWidth: 340, background: '#111113', borderRadius: 16, border: '1px solid rgba(255,255,255,0.1)', padding: 20, textAlign: 'center' }} onClick={e => e.stopPropagation()} data-testid="admin-confirm-dialog">
            <p style={{ fontSize: 14, fontWeight: 'bold', color: '#fff', marginBottom: 8 }}>{confirmAction.title}</p>
            <p style={{ fontSize: 11, color: '#9ca3af', marginBottom: 16, lineHeight: '1.4' }}>{confirmAction.message}</p>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={() => setConfirmAction(null)} style={{ flex: 1, padding: '10px 0', borderRadius: 10, background: '#1f2937', color: '#9ca3af', fontSize: 12, fontWeight: 'bold', border: 'none', cursor: 'pointer' }}>Annulla</button>
              <button onClick={() => { const fn = confirmAction.onConfirm; setConfirmAction(null); fn(); }}
                style={{ flex: 1, padding: '10px 0', borderRadius: 10, background: 'linear-gradient(135deg, #dc2626, #b91c1c)', color: '#fff', fontSize: 12, fontWeight: 'bold', border: 'none', cursor: 'pointer' }}
                data-testid="admin-confirm-btn">Conferma</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
function FilmsTab({ api }) {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const loadFilms = useCallback(async (q = '') => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/all-films?q=${encodeURIComponent(q)}`);
      setFilms(res.data.films || []);
    } catch { toast.error('Errore caricamento film'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadFilms(); }, [loadFilms]);

  const handleSearch = (e) => { e.preventDefault(); loadFilms(searchQuery); };

  const handleDeleteFilm = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await api.delete(`/admin/delete-film/${deleteTarget.id}`);
      toast.success(`Film "${deleteTarget.title}" eliminato definitivamente`);
      setDeleteTarget(null);
      loadFilms(searchQuery);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore eliminazione'); }
    finally { setDeleteLoading(false); }
  };

  return (
    <div className="space-y-3" data-testid="admin-films-tab">
      <ConfirmModal
        open={!!deleteTarget}
        title="Eliminazione Definitiva Film"
        message={`Confermi eliminazione definitiva del film "${deleteTarget?.title}" di ${deleteTarget?.studio_name}? Il film verra' rimosso da classifiche e liste pubbliche. Questa azione e' IRREVERSIBILE.`}
        onConfirm={handleDeleteFilm}
        onCancel={() => setDeleteTarget(null)}
        loading={deleteLoading}
      />

      {/* Search */}
      <form onSubmit={handleSearch}>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              placeholder="Cerca film per titolo..."
              className="w-full bg-[#111113] border border-gray-800 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none"
              data-testid="admin-film-search-input" />
          </div>
          <Button type="submit" size="sm" className="bg-red-600 hover:bg-red-700 text-xs px-3" disabled={loading}
            data-testid="admin-film-search-btn">
            {loading ? '...' : 'Cerca'}
          </Button>
        </div>
      </form>

      <p className="text-[10px] text-gray-500">{films.length} film trovati</p>

      {/* Compact film grid: 8 mobile / 12 tablet / 16 desktop */}
      <div className="grid gap-1 max-h-[70vh] overflow-y-auto pb-2"
        style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))' }}
        data-testid="admin-film-grid">
        {films.map(f => (
          <div key={f.id} className="group relative bg-[#0d0d0f] border border-white/5 rounded overflow-hidden hover:border-red-500/40 transition-all"
            data-testid={`admin-film-card-${f.id}`}>
            {/* Mini poster */}
            <div className="aspect-[2/3] bg-gray-900 relative">
              {f.poster_url ? (
                <img src={`${API_BASE}${f.poster_url}`} alt={f.title} loading="lazy"
                  className="w-full h-full object-cover"
                  onError={e => { e.target.style.display='none'; }} />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Film className="w-3.5 h-3.5 text-gray-700" />
                </div>
              )}
              {/* Delete icon - always visible, top-right */}
              <button
                className="absolute top-0.5 right-0.5 w-4 h-4 rounded-full bg-red-600/80 hover:bg-red-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => { e.stopPropagation(); setDeleteTarget(f); }}
                data-testid={`admin-film-delete-${f.id}`}>
                <Trash2 className="w-2 h-2 text-white" />
              </button>
              {/* Quality badge */}
              {f.quality_score != null && (
                <span className="absolute bottom-0.5 right-0.5 text-[7px] font-bold bg-black/70 text-yellow-400 px-0.5 rounded leading-none py-px">
                  {Math.round(f.quality_score)}%
                </span>
              )}
            </div>
            {/* Compact info */}
            <div className="px-0.5 py-0.5">
              <p className="text-[7px] font-semibold text-white truncate leading-tight" title={f.title}>{f.title}</p>
              <p className="text-[6px] text-gray-500 truncate leading-tight">{f.studio_name}</p>
            </div>
          </div>
        ))}
      </div>

      {films.length === 0 && !loading && (
        <p className="text-center text-xs text-gray-600 py-8">Nessun film trovato</p>
      )}
    </div>
  );
}

/* ─── Reports Tab ─── */
function ReportsTab({ api }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('pending');
  const [actionLoading, setActionLoading] = useState(null);

  const loadReports = useCallback(async (status) => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/reports?status=${status}`);
      setReports(res.data.reports || []);
    } catch { toast.error('Errore caricamento segnalazioni'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadReports(filter); }, [filter, loadReports]);

  const resolveReport = async (reportId, action) => {
    setActionLoading(reportId);
    try {
      await api.post(`/admin/reports/${reportId}/resolve?action=${action}`);
      toast.success(action === 'delete_content' ? 'Contenuto rimosso e segnalazione risolta' : 'Segnalazione archiviata');
      loadReports(filter);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const TYPE_LABELS = { message: 'Messaggio', image: 'Immagine', user: 'Utente' };
  const TYPE_COLORS = { message: 'bg-blue-500/20 text-blue-400', image: 'bg-purple-500/20 text-purple-400', user: 'bg-orange-500/20 text-orange-400' };
  const STATUS_COLORS = { pending: 'bg-yellow-500/20 text-yellow-400', resolved: 'bg-green-500/20 text-green-400', dismissed: 'bg-gray-500/20 text-gray-400' };

  return (
    <div className="space-y-3" data-testid="admin-reports-tab">
      {/* Filter buttons */}
      <div className="flex gap-1.5 flex-wrap">
        {['pending', 'resolved', 'dismissed', 'all'].map(f => (
          <button key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-full text-[10px] font-semibold transition-all ${
              filter === f ? 'bg-red-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
            data-testid={`report-filter-${f}`}>
            {f === 'pending' ? 'In attesa' : f === 'resolved' ? 'Risolte' : f === 'dismissed' ? 'Archiviate' : 'Tutte'}
          </button>
        ))}
      </div>

      <p className="text-[10px] text-gray-500">{reports.length} segnalazioni trovate</p>

      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 text-red-400 animate-spin" /></div>
      ) : reports.length === 0 ? (
        <div className="text-center py-8">
          <Flag className="w-8 h-8 text-gray-700 mx-auto mb-2" />
          <p className="text-xs text-gray-600">Nessuna segnalazione {filter !== 'all' ? `con stato "${filter}"` : ''}</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[70vh] overflow-y-auto pb-2" data-testid="admin-reports-list">
          {reports.map(r => (
            <Card key={r.id} className="bg-[#111113] border-white/5 hover:border-white/10 transition-all" data-testid={`report-card-${r.id}`}>
              <CardContent className="p-3 space-y-2">
                {/* Header row */}
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-1.5">
                    <Badge className={`text-[8px] h-4 ${TYPE_COLORS[r.target_type] || 'bg-gray-500/20 text-gray-400'}`}>
                      {TYPE_LABELS[r.target_type] || r.target_type}
                    </Badge>
                    <Badge className={`text-[8px] h-4 ${STATUS_COLORS[r.status] || ''}`}>
                      {r.status === 'pending' ? 'In attesa' : r.status === 'resolved' ? 'Risolta' : 'Archiviata'}
                    </Badge>
                  </div>
                  <span className="text-[9px] text-gray-600">
                    {r.created_at ? new Date(r.created_at).toLocaleString('it-IT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''}
                  </span>
                </div>

                {/* Reporter */}
                <p className="text-[10px] text-gray-400">
                  Segnalato da: <span className="text-white font-semibold">{r.reporter_nickname || '?'}</span>
                </p>

                {/* Reason */}
                {r.reason && (
                  <div className="bg-black/30 rounded-lg px-2.5 py-1.5">
                    <p className="text-[10px] text-gray-300">"{r.reason}"</p>
                  </div>
                )}

                {/* Snapshot */}
                {r.snapshot && (
                  <div className="bg-black/20 rounded-lg px-2.5 py-1.5 border border-white/5">
                    {r.target_type === 'user' ? (
                      <div className="flex items-center gap-2">
                        <Users className="w-3 h-3 text-orange-400 flex-shrink-0" />
                        <div>
                          <p className="text-[10px] text-white font-semibold">{r.snapshot.nickname}</p>
                          <p className="text-[9px] text-gray-500">{r.snapshot.email}</p>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <p className="text-[9px] text-gray-500 mb-0.5">
                          Da: <span className="text-gray-300">{r.snapshot.sender_nickname || '?'}</span>
                          {r.snapshot.room_id && <span className="ml-1 text-gray-600">in #{r.snapshot.room_id}</span>}
                        </p>
                        {r.snapshot.content && (
                          <p className="text-[10px] text-gray-300 break-words">"{r.snapshot.content}"</p>
                        )}
                        {r.snapshot.image_url && (
                          <img
                            src={r.snapshot.image_url.startsWith('/') ? `${API_BASE}${r.snapshot.image_url}` : r.snapshot.image_url}
                            alt="" className="mt-1 max-h-24 rounded border border-white/10"
                            onError={e => { e.target.style.display = 'none'; }}
                          />
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Action buttons (only for pending) */}
                {r.status === 'pending' && (
                  <div className="flex gap-1.5 pt-1">
                    {r.target_type !== 'user' && (
                      <Button size="sm" className="bg-red-600 hover:bg-red-700 text-[10px] h-6 px-2"
                        onClick={() => resolveReport(r.id, 'delete_content')}
                        disabled={actionLoading === r.id}
                        data-testid={`report-delete-${r.id}`}>
                        {actionLoading === r.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3 mr-0.5" />}
                        Rimuovi Contenuto
                      </Button>
                    )}
                    <Button size="sm" variant="outline" className="text-[10px] h-6 px-2 border-gray-700 text-gray-400 hover:bg-white/5"
                      onClick={() => resolveReport(r.id, 'dismiss')}
                      disabled={actionLoading === r.id}
                      data-testid={`report-dismiss-${r.id}`}>
                      <XCircle className="w-3 h-3 mr-0.5" />
                      Archivia
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Maintenance Tab (Rewritten — Advanced) ─── */

const DonationsTab = ({ api }) => {
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api.get('/admin/settings').then(r => { setEnabled(r.data.donations_enabled); setLoading(false); }).catch(() => setLoading(false));
  }, [api]);
  const toggle = async () => {
    const newVal = !enabled;
    await api.post('/admin/toggle-donations', { enabled: newVal });
    setEnabled(newVal);
    toast.success(newVal ? 'Donazioni abilitate' : 'Donazioni disabilitate');
  };
  return (
    <Card className="bg-[#111113] border-white/5" data-testid="donations-tab">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2"><Heart className="w-4 h-4 text-pink-400" /> Gestione Donazioni</CardTitle>
        <p className="text-[10px] text-gray-500">Abilita/disabilita il sistema donazioni PayPal</p>
      </CardHeader>
      <CardContent>
        {loading ? <p className="text-xs text-gray-500">Caricamento...</p> : (
          <div className="flex items-center justify-between p-3 bg-white/[0.03] rounded-lg border border-white/5">
            <div>
              <p className="text-sm font-semibold text-white">Donazioni PayPal</p>
              <p className="text-[10px] text-gray-500">{enabled ? 'Il cuore rosa e il banner donazioni sono visibili' : 'Donazioni nascoste per tutti gli utenti'}</p>
            </div>
            <Button size="sm" className={`h-8 text-xs ${enabled ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`} onClick={toggle}>
              {enabled ? 'Disattiva' : 'Attiva'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}



const ResetGamePanel = ({ api }) => {
  const [enabled, setEnabled] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);
  const [loading, setLoading] = useState('');
  const [result, setResult] = useState(null);

  const doReset = async (type) => {
    setConfirmAction(null);
    setLoading(type);
    try {
      const r = await api.post('/admin/recovery/reset-game', { type });
      setResult(r.data || r);
      toast.success('Reset completato');
    } catch (e) { toast.error(e?.response?.data?.detail || e.message || 'Errore'); }
    setLoading('');
  };

  return (
    <Card className="bg-[#111113] border-red-500/20" data-testid="reset-game-panel">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2 text-red-400"><AlertTriangle className="w-4 h-4" /> Reset Gioco</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="p-3 bg-red-500/5 border border-red-500/15 rounded-lg">
          <p className="text-[11px] text-red-400 font-bold">ATTENZIONE: i reset sono irreversibili. Questa azione non può essere annullata.</p>
        </div>

        <div className="flex items-center justify-between p-3 bg-white/[0.02] rounded-lg border border-white/5">
          <div>
            <p className="text-[11px] font-bold text-white">Abilita reset amministrativi</p>
            <p className="text-[9px] text-gray-500">Sblocca i bottoni di reset</p>
          </div>
          <button onClick={() => setEnabled(!enabled)}
            className={`w-12 h-6 rounded-full transition-colors relative ${enabled ? 'bg-red-600' : 'bg-gray-700'}`}>
            <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${enabled ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </button>
        </div>

        <div className="space-y-2">
          <button onClick={() => enabled && setConfirmAction('keep_infra')} disabled={!enabled || !!loading}
            className="w-full text-left p-3 rounded-lg border transition-colors disabled:opacity-30 disabled:cursor-not-allowed bg-orange-500/5 border-orange-500/15 hover:bg-orange-500/10">
            <p className="text-[11px] font-bold text-orange-400">{loading === 'keep_infra' ? 'Reset in corso...' : 'Reset mantenendo infrastrutture'}</p>
            <p className="text-[8px] text-gray-500 mt-0.5">Cancella: film, serie, progetti pipeline, poster, notifiche, eventi, chat, likes, commenti, voti, premi festival, sponsor, sceneggiature. Mantiene: utenti, denaro, CinePass, livello, infrastrutture, NPC.</p>
          </button>

          <button onClick={() => enabled && setConfirmAction('full')} disabled={!enabled || !!loading}
            className="w-full text-left p-3 rounded-lg border transition-colors disabled:opacity-30 disabled:cursor-not-allowed bg-red-500/5 border-red-500/15 hover:bg-red-500/10">
            <p className="text-[11px] font-bold text-red-400">{loading === 'full' ? 'Reset in corso...' : 'Reset totale (eccetto utenti)'}</p>
            <p className="text-[8px] text-gray-500 mt-0.5">Cancella: TUTTO (film, serie, infrastrutture, poster, notifiche, eventi, chat, premi). Resetta denaro a $10M, CP a 50, livello a 1. Mantiene: account utenti registrati e NPC.</p>
          </button>
        </div>

        {result && (
          <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
            <p className="text-[11px] font-bold text-green-400 mb-1.5">Reset completato ({result.type === 'full' ? 'totale' : 'parziale'})</p>
            {result.note && <p className="text-[9px] text-green-300/70 mb-2">{result.note}</p>}
            <div className="space-y-0.5">
              {Object.entries(result.results || {}).map(([k, v]) => (
                <div key={k} className="flex justify-between text-[9px]">
                  <span className="text-gray-400 truncate mr-2">{k.replace(/_/g, ' ')}</span>
                  <span className="text-green-400 font-mono flex-shrink-0">{typeof v === 'number' ? `${v} rimossi` : String(v).substring(0, 30)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>

      {confirmAction && (
        <div style={{position:'fixed',inset:0,zIndex:9999,display:'flex',alignItems:'center',justifyContent:'center',padding:16}} onClick={() => setConfirmAction(null)}>
          <div style={{position:'absolute',inset:0,background:'rgba(0,0,0,0.7)'}} />
          <div style={{position:'relative',width:'100%',maxWidth:360,background:'#111113',borderRadius:16,padding:20,border:'1px solid rgba(239,68,68,0.3)'}} onClick={e => e.stopPropagation()}>
            <p style={{fontSize:14,fontWeight:'bold',color:'#fff',marginBottom:8}}>Conferma Reset</p>
            <p style={{fontSize:12,color:'#9ca3af',marginBottom:16}}>Questa azione è definitiva e non può essere annullata. Vuoi procedere?</p>
            <div style={{display:'flex',gap:8}}>
              <button onClick={() => setConfirmAction(null)} style={{flex:1,padding:'10px 0',borderRadius:8,background:'#1f2937',color:'#9ca3af',fontSize:12,fontWeight:'bold',border:'none',cursor:'pointer'}}>Annulla</button>
              <button onClick={() => doReset(confirmAction)} style={{flex:1,padding:'10px 0',borderRadius:8,background:'#dc2626',color:'#fff',fontSize:12,fontWeight:'bold',border:'none',cursor:'pointer'}}>Conferma Reset</button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};


function MaintenanceTab({ api }) {


const CityTastesAdmin = ({ api }) => {
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testResult, setTestResult] = useState(null);
  const [testCity, setTestCity] = useState('roma');
  const [testGenre, setTestGenre] = useState('comedy');

  const load = () => {
    api.get('/city-tastes/admin/cities').then(r => { setCities(r.data?.cities || []); setLoading(false); }).catch(() => setLoading(false));
  };
  useEffect(load, [api]);

  const LEVEL_COLORS = { fermento: 'text-green-400', forte: 'text-emerald-400', discreto: 'text-yellow-400', tiepido: 'text-orange-400', freddo: 'text-red-400' };
  const getLevel = (v) => v >= 0.85 ? 'fermento' : v >= 0.7 ? 'forte' : v >= 0.5 ? 'discreto' : v >= 0.35 ? 'tiepido' : 'freddo';

  return (
    <div className="space-y-3" data-testid="city-tastes-admin">
      <Card className="bg-[#111113] border-white/5">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2"><Star className="w-4 h-4 text-yellow-400" /> Gusti Città — Sistema Dinamico</CardTitle>
          <p className="text-[10px] text-gray-500">{cities.length} città attive. I gusti evolvono ogni 5-25 giorni.</p>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex gap-2">
            <Button size="sm" className="h-7 text-[10px] bg-purple-600 hover:bg-purple-700" onClick={async () => {
              await api.post('/city-tastes/admin/evolve');
              toast.success('Gusti evoluti!'); load();
            }}>Forza Evoluzione</Button>
            <Button size="sm" className="h-7 text-[10px] bg-red-600 hover:bg-red-700" onClick={async () => {
              await api.post('/city-tastes/admin/seed');
              toast.success('Città re-seedate!'); load();
            }}>Reset Seed</Button>
          </div>

          {/* Test Tool */}
          <div className="p-2 bg-white/[0.02] rounded border border-white/5">
            <p className="text-[9px] text-gray-400 mb-1 font-bold">Test Città vs Genere</p>
            <div className="flex gap-1 items-center">
              <select value={testCity} onChange={e => setTestCity(e.target.value)} className="bg-gray-800 text-[9px] text-white border border-gray-700 rounded px-1 py-1 flex-1">
                {cities.map(c => <option key={c.city_id} value={c.city_id}>{c.name}</option>)}
              </select>
              <select value={testGenre} onChange={e => setTestGenre(e.target.value)} className="bg-gray-800 text-[9px] text-white border border-gray-700 rounded px-1 py-1 flex-1">
                {['action','comedy','drama','horror','romance','sci_fi','thriller','anime','fantasy','documentary','crime','noir','superhero','spy','musical','adventure','war','western','experimental','historical','mystery','biography','sport','family'].map(g => <option key={g} value={g}>{g}</option>)}
              </select>
              <Button size="sm" className="h-6 text-[9px] px-2" onClick={async () => {
                const r = await api.get(`/city-tastes/admin/test/${testCity}/${testGenre}`);
                setTestResult(r.data);
              }}>Test</Button>
            </div>
            {testResult && (
              <div className="mt-1 p-1.5 bg-black/30 rounded text-[8px] space-y-0.5">
                <p className="text-white">{testResult.city} + {testResult.genre}: <span className={LEVEL_COLORS[testResult.level]}>{testResult.level}</span></p>
                <p className="text-gray-500">Base: {testResult.personality_base} | Attuale: {testResult.raw_taste} | Saturazione: {testResult.saturation} | Effettivo: {testResult.effective} | Moltiplicatore: {testResult.multiplier}x | Trend: {testResult.trend}</p>
                <p className="text-cyan-400/70 italic">"{testResult.phrase}"</p>
              </div>
            )}
          </div>

          {/* Cities Grid */}
          {loading ? <p className="text-xs text-gray-500">Caricamento...</p> : (
            <div className="grid grid-cols-1 gap-1 max-h-[300px] overflow-y-auto">
              {cities.map(c => {
                const topGenres = Object.entries(c.current_tastes || {}).sort((a, b) => b[1] - a[1]).slice(0, 3);
                return (
                  <div key={c.city_id} className="flex items-center justify-between p-1.5 bg-white/[0.02] rounded border border-white/5">
                    <div className="flex-1">
                      <span className="text-[10px] font-bold text-white">{c.name}</span>
                      <span className="text-[8px] text-gray-600 ml-1">({c.zone})</span>
                    </div>
                    <div className="flex gap-1">
                      {topGenres.map(([g, v]) => (
                        <span key={g} className={`text-[7px] px-1 py-0.5 rounded ${LEVEL_COLORS[getLevel(v)]} bg-white/5`}>{g}:{v.toFixed(2)}</span>
                      ))}
                    </div>
                    <button onClick={async () => { await api.post(`/city-tastes/admin/toggle/${c.city_id}`); load(); }}
                      className={`ml-1 text-[7px] px-1 py-0.5 rounded ${c.enabled ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                      {c.enabled ? 'ON' : 'OFF'}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


function GuestCleanupPanel({ api }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cleaning, setCleaning] = useState(false);
  useEffect(() => {
    api.get('/admin/recovery/guest-orphans').then(r => { setData(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, [api]);
  const clean = async () => {
    setCleaning(true);
    try {
      const r = await api.post('/admin/recovery/clean-guests');
      toast.success(`Eliminati ${r.data.deleted_users} guest, ${r.data.deleted_films} film, ${r.data.deleted_infra} infrastrutture`);
      setData({ guests: [], total_guests: 0, total_films: 0 });
    } catch (e) { toast.error(e.message || 'Errore'); }
    setCleaning(false);
  };
  if (loading) return <Card className="bg-[#111113] border-white/5 mt-3"><CardContent className="p-3"><p className="text-xs text-gray-500">Caricamento...</p></CardContent></Card>;
  if (!data || data.total_guests === 0) return null; // Hide if no orphans
  return (
    <Card className="bg-[#111113] border-white/5 mt-3" data-testid="guest-cleanup-panel">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2"><Trash2 className="w-4 h-4 text-red-400" /> Pulizia Dati Guest</CardTitle>
        <p className="text-[10px] text-gray-500">Sessioni guest orfane rimaste in memoria</p>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between p-3 bg-red-500/5 rounded-lg border border-red-500/15">
          <div>
            <p className="text-sm font-semibold text-white">{data.total_guests} guest orfani</p>
            <p className="text-[10px] text-gray-500">{data.total_films} film associati</p>
          </div>
          <Button size="sm" className="h-8 text-xs bg-red-600 hover:bg-red-700" onClick={clean} disabled={cleaning}>
            {cleaning ? 'Eliminazione...' : 'Pulisci tutto'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}


  const [username, setUsername] = useState('');
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [targetUser, setTargetUser] = useState('');

  const searchProjects = async (nick) => {
    if (!nick.trim()) return;
    setLoading(true);
    setProjects([]);
    setStats(null);
    try {
      const res = await api.get(`/admin/maintenance/projects?username=${encodeURIComponent(nick.trim())}`);
      setProjects(res.data.projects || []);
      setTargetUser(res.data.user || nick);
      setStats({ total: res.data.total, broken: res.data.broken, stuck: res.data.stuck, incomplete: res.data.incomplete });
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore ricerca'); }
    finally { setLoading(false); }
  };

  const execAction = async (projectId, projectType, action) => {
    const key = `${projectId}-${action}`;
    setActionLoading(key);
    try {
      const res = await api.post('/admin/maintenance/fix-project', { project_id: projectId, project_type: projectType, action });
      const d = res.data;
      if (action === 'auto_fix') toast.success(`Auto-fix: ${(d.fixes || []).join(', ')}`);
      else if (action === 'force_step') toast.success(d.message || 'Step avanzato');
      else if (action === 'complete_project') toast.success(d.message || 'Progetto completato');
      else if (action === 'reset_step') toast.success(d.message || 'Step precedente');
      searchProjects(targetUser);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore azione'); }
    finally { setActionLoading(null); }
  };

  const FLAG_CONFIG = {
    'OK': { label: 'OK', color: 'bg-green-500/20 text-green-400', border: 'border-green-500/20' },
    'STUCK': { label: 'FERMO', color: 'bg-yellow-500/20 text-yellow-400', border: 'border-yellow-500/30' },
    'LOOP': { label: 'LOOP', color: 'bg-orange-500/20 text-orange-400', border: 'border-orange-500/30' },
    'INCOMPLETE': { label: 'INCOMPLETO', color: 'bg-purple-500/20 text-purple-400', border: 'border-purple-500/30' },
    'BROKEN': { label: 'ROTTO', color: 'bg-red-500/20 text-red-400', border: 'border-red-500/30' },
  };

  const TYPE_CONFIG = {
    'film': { label: 'Film', color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
    'serie': { label: 'Serie TV', color: 'text-blue-400', bg: 'bg-blue-500/10' },
    'anime': { label: 'Anime', color: 'text-pink-400', bg: 'bg-pink-500/10' },
  };

  return (
    <div className="space-y-4" data-testid="maintenance-tab">
      {/* Search */}
      <Card className="bg-[#111113] border-amber-500/20">
        <CardContent className="p-3 space-y-2">
          <p className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
            <Search className="w-3.5 h-3.5" /> Cerca Progetti Utente
          </p>
          <form onSubmit={(e) => { e.preventDefault(); searchProjects(username); }} className="flex gap-2">
            <input type="text" value={username} onChange={e => setUsername(e.target.value)}
              placeholder="Nickname utente..."
              className="flex-1 bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-500 focus:border-amber-500/50 focus:outline-none"
              data-testid="maint-search-input" />
            <Button type="submit" size="sm" className="bg-amber-600 hover:bg-amber-700 text-xs px-4" disabled={loading || !username.trim()}
              data-testid="maint-search-btn">
              {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Analizza'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Stats summary */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="maint-stats">
          {[
            { label: 'Totale', value: stats.total, color: 'text-white' },
            { label: 'Rotti', value: stats.broken, color: stats.broken > 0 ? 'text-red-400' : 'text-gray-500' },
            { label: 'Fermi', value: stats.stuck, color: stats.stuck > 0 ? 'text-yellow-400' : 'text-gray-500' },
            { label: 'Incompleti', value: stats.incomplete, color: stats.incomplete > 0 ? 'text-purple-400' : 'text-gray-500' },
          ].map(s => (
            <div key={s.label} className="bg-[#111113] border border-white/5 rounded-lg p-2 text-center">
              <p className={`text-lg font-black ${s.color}`}>{s.value}</p>
              <p className="text-[8px] text-gray-500">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Project cards — mobile-first vertical layout */}
      {projects.length > 0 && (
        <div className="space-y-2 max-h-[60vh] overflow-y-auto pb-2" data-testid="maint-projects">
          <p className="text-[10px] text-gray-500">{projects.length} progetti per <span className="text-white font-semibold">{targetUser}</span></p>
          {projects.map(p => {
            const fc = FLAG_CONFIG[p.flag] || FLAG_CONFIG.OK;
            const tc = TYPE_CONFIG[p.type] || TYPE_CONFIG.film;
            const progress = p.pipeline_total > 0 ? Math.round((p.pipeline_index / (p.pipeline_total - 1)) * 100) : 0;

            return (
              <Card key={p.id} className={`bg-[#0e0e10] ${fc.border}`} data-testid={`maint-project-${p.id}`}>
                <CardContent className="p-3 space-y-2">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${tc.bg} ${tc.color}`}>{tc.label}</span>
                        <Badge className={`text-[8px] h-4 ${fc.color}`}>{fc.label}</Badge>
                        {p.is_legacy && <span className="text-[7px] text-orange-400 bg-orange-500/10 px-1 rounded">LEGACY</span>}
                      </div>
                      <p className="text-xs font-semibold text-white mt-1 truncate">{p.title}</p>
                    </div>
                    <span className="text-[9px] text-gray-500 flex-shrink-0 whitespace-nowrap">{p.idle_text}</span>
                  </div>

                  {/* Status + progress bar */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[9px]">
                      <span className="text-gray-400">
                        Step: <span className="text-white font-semibold">{p.status}</span>
                        {p.next_step && <span className="text-gray-600"> → {p.next_step}</span>}
                      </span>
                      <span className="text-gray-500">{progress}%</span>
                    </div>
                    <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-amber-500 to-red-500 rounded-full transition-all" style={{ width: `${progress}%` }} />
                    </div>
                  </div>

                  {/* Issues */}
                  {p.issues.length > 0 && (
                    <div className="space-y-0.5">
                      {p.issues.map((issue, i) => (
                        <p key={i} className="text-[9px] text-gray-400 flex items-start gap-1">
                          <AlertTriangle className="w-3 h-3 text-yellow-500 flex-shrink-0 mt-0.5" />
                          {issue}
                        </p>
                      ))}
                    </div>
                  )}

                  {/* Data indicators */}
                  <div className="flex gap-2 flex-wrap">
                    {[
                      { label: 'Cast', ok: p.has_cast },
                      { label: 'Genere', ok: p.has_genre },
                      { label: 'Script', ok: p.has_screenplay },
                      { label: 'Poster', ok: p.has_poster },
                    ].map(d => (
                      <span key={d.label} className={`text-[8px] px-1.5 py-0.5 rounded ${d.ok ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                        {d.ok ? <CheckCircle className="w-2.5 h-2.5 inline mr-0.5" /> : <XCircle className="w-2.5 h-2.5 inline mr-0.5" />}
                        {d.label}
                      </span>
                    ))}
                    {p.quality_score != null && (
                      <span className="text-[8px] px-1.5 py-0.5 rounded bg-yellow-500/10 text-yellow-400">Q: {Math.round(p.quality_score)}%</span>
                    )}
                  </div>

                  {/* Action buttons */}
                  <div className="grid grid-cols-2 gap-1.5 pt-1">
                    <Button size="sm" className="bg-emerald-700 hover:bg-emerald-600 text-[9px] h-7"
                      onClick={() => execAction(p.id, p.type, 'auto_fix')}
                      disabled={!!actionLoading} data-testid={`maint-autofix-${p.id}`}>
                      {actionLoading === `${p.id}-auto_fix` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wrench className="w-3 h-3 mr-0.5" />}
                      Fix Automatico
                    </Button>
                    <Button size="sm" className="bg-blue-700 hover:bg-blue-600 text-[9px] h-7"
                      onClick={() => execAction(p.id, p.type, 'force_step')}
                      disabled={!!actionLoading || !p.next_step} data-testid={`maint-force-${p.id}`}>
                      {actionLoading === `${p.id}-force_step` ? <Loader2 className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3 mr-0.5" />}
                      Forza Step
                    </Button>
                    <Button size="sm" className="bg-amber-700 hover:bg-amber-600 text-[9px] h-7"
                      onClick={() => execAction(p.id, p.type, 'complete_project')}
                      disabled={!!actionLoading} data-testid={`maint-complete-${p.id}`}>
                      {actionLoading === `${p.id}-complete_project` ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3 mr-0.5" />}
                      Completa
                    </Button>
                    <Button size="sm" variant="outline" className="text-[9px] h-7 border-gray-700 text-gray-400 hover:bg-white/5"
                      onClick={() => execAction(p.id, p.type, 'reset_step')}
                      disabled={!!actionLoading || !p.prev_step} data-testid={`maint-reset-${p.id}`}>
                      {actionLoading === `${p.id}-reset_step` ? <Loader2 className="w-3 h-3 animate-spin" /> : <XCircle className="w-3 h-3 mr-0.5" />}
                      Reset Step
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {stats && projects.length === 0 && !loading && (
        <div className="text-center py-8">
          <CheckCircle className="w-8 h-8 text-green-500/40 mx-auto mb-2" />
          <p className="text-xs text-gray-500">Nessun progetto attivo per <span className="text-white">{targetUser}</span></p>
        </div>
      )}

    </div>
  );
}

/* ─── Roles Management Tab (ADMIN only) ─── */
function RolesTab({ api }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoading, setActionLoading] = useState(null);

  const searchUsers = useCallback(async (q) => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/search-users?q=${encodeURIComponent(q)}`);
      setUsers(res.data.users || []);
    } catch { toast.error('Errore ricerca'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { searchUsers(''); }, [searchUsers]);

  const setRole = async (userId, nickname, role) => {
    setActionLoading(userId);
    try {
      await api.post('/admin/set-user-role', { user_id: userId, role });
      toast.success(`${nickname} impostato come ${role}`);
      searchUsers(searchQuery);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const ROLE_COLORS = {
    'ADMIN': 'bg-red-500/20 text-red-400 border-red-500/30',
    'CO_ADMIN': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    'MOD': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    'USER': 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };

  return (
    <div className="space-y-3" data-testid="admin-roles-tab">
      <form onSubmit={(e) => { e.preventDefault(); searchUsers(searchQuery); }}>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              placeholder="Cerca utente..."
              className="w-full bg-[#111113] border border-gray-800 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-gray-600 focus:border-amber-500/50 focus:outline-none"
              data-testid="roles-search-input" />
          </div>
          <Button type="submit" size="sm" className="bg-amber-600 hover:bg-amber-700 text-xs px-3" disabled={loading}
            data-testid="roles-search-btn">
            {loading ? '...' : 'Cerca'}
          </Button>
        </div>
      </form>

      <div className="space-y-1.5 max-h-[65vh] overflow-y-auto" data-testid="roles-user-list">
        {users.map(u => {
          const role = u.role || 'USER';
          const isNeo = u.nickname === 'NeoMorpheus';
          return (
            <Card key={u.id} className={`bg-[#111113] border-white/5 ${isNeo ? 'border-red-500/30' : ''}`} data-testid={`role-user-${u.nickname}`}>
              <CardContent className="p-2.5 flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500/20 to-red-500/20 flex items-center justify-center text-xs font-bold text-amber-400 flex-shrink-0">
                  {u.nickname?.[0]?.toUpperCase() || '?'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-white truncate">{u.nickname}</p>
                  <p className="text-[9px] text-gray-500 truncate">{u.email}</p>
                </div>
                <Badge className={`text-[8px] h-5 px-2 ${ROLE_COLORS[role] || ROLE_COLORS.USER}`}>{role}</Badge>
                {!isNeo && (
                  <div className="flex gap-1 flex-shrink-0">
                    {['CO_ADMIN', 'MOD', 'USER'].map(r => (
                      <button key={r}
                        disabled={actionLoading === u.id || role === r}
                        onClick={() => setRole(u.id, u.nickname, r)}
                        className={`px-1.5 py-0.5 rounded text-[8px] font-semibold transition-all disabled:opacity-30 ${
                          role === r ? 'bg-white/10 text-white' : 'bg-white/5 text-gray-500 hover:bg-white/10 hover:text-white'
                        }`}
                        data-testid={`set-role-${u.nickname}-${r}`}>
                        {r === 'CO_ADMIN' ? 'Co-Admin' : r === 'MOD' ? 'Mod' : 'User'}
                      </button>
                    ))}
                  </div>
                )}
                {isNeo && <span className="text-[8px] text-red-400 font-bold flex-shrink-0">PROTETTO</span>}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

/* ─── Deletions Tab (ADMIN only) ─── */
function DeletionsTab({ api }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  const loadRequests = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/deletion-requests');
      setRequests(res.data.requests || []);
    } catch { toast.error('Errore caricamento richieste'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadRequests(); }, [loadRequests]);

  const handleAction = async (userId, action) => {
    setActionLoading(`${userId}-${action}`);
    try {
      await api.post(`/admin/deletion/${userId}/${action}`);
      const msgs = {
        'approve': 'Countdown 10 giorni avviato',
        'reject': 'Richiesta rifiutata (cooldown 5 giorni)',
        'final-approve': 'Account eliminato definitivamente',
        'final-reject': 'Cancellazione annullata',
      };
      toast.success(msgs[action] || 'Azione completata');
      loadRequests();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const STATUS_CONFIG = {
    'requested': { label: 'Richiesta', color: 'bg-yellow-500/20 text-yellow-400', icon: Clock },
    'countdown_active': { label: 'Countdown', color: 'bg-orange-500/20 text-orange-400', icon: Clock },
    'user_confirmed': { label: 'Confermato', color: 'bg-red-500/20 text-red-400', icon: AlertTriangle },
    'final_pending': { label: 'In Attesa Finale', color: 'bg-red-500/30 text-red-300', icon: AlertTriangle },
  };

  return (
    <div className="space-y-3" data-testid="admin-deletions-tab">
      <div className="flex items-center justify-between">
        <p className="text-[10px] text-gray-500">{requests.length} richieste in corso</p>
        <Button size="sm" variant="outline" className="text-[10px] h-6 border-gray-700 text-gray-400"
          onClick={loadRequests} disabled={loading} data-testid="deletions-refresh-btn">
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Aggiorna'}
        </Button>
      </div>

      {requests.length === 0 && !loading ? (
        <div className="text-center py-8">
          <CheckCircle className="w-8 h-8 text-gray-700 mx-auto mb-2" />
          <p className="text-xs text-gray-600">Nessuna richiesta di cancellazione in corso</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[65vh] overflow-y-auto" data-testid="deletions-list">
          {requests.map(r => {
            const cfg = STATUS_CONFIG[r.deletion_status] || { label: r.deletion_status, color: 'bg-gray-500/20 text-gray-400', icon: Clock };
            const StatusIcon = cfg.icon;
            const countdownEnd = r.deletion_countdown_end ? new Date(r.deletion_countdown_end) : null;
            const daysLeft = countdownEnd ? Math.max(0, Math.ceil((countdownEnd - new Date()) / (1000*60*60*24))) : null;

            return (
              <Card key={r.id} className="bg-[#111113] border-white/5" data-testid={`deletion-card-${r.id}`}>
                <CardContent className="p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-red-500/10 flex items-center justify-center text-xs font-bold text-red-400">
                        {r.nickname?.[0]?.toUpperCase() || '?'}
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-white">{r.nickname}</p>
                        <p className="text-[9px] text-gray-500">{r.email}</p>
                      </div>
                    </div>
                    <Badge className={`text-[8px] h-5 ${cfg.color}`}>
                      <StatusIcon className="w-3 h-3 mr-0.5" />{cfg.label}
                    </Badge>
                  </div>

                  {r.deletion_reason && (
                    <p className="text-[10px] text-gray-400 bg-black/30 rounded px-2 py-1">Motivo: "{r.deletion_reason}"</p>
                  )}

                  {r.deletion_requested_by_name && (
                    <p className="text-[9px] text-gray-500">Richiesto da: <span className="text-amber-400">{r.deletion_requested_by_name}</span></p>
                  )}

                  {daysLeft !== null && r.deletion_status === 'countdown_active' && (
                    <p className="text-[10px] text-orange-400 font-semibold">Countdown: {daysLeft} giorni rimanenti</p>
                  )}

                  {/* Actions based on status */}
                  <div className="flex gap-1.5 pt-1">
                    {r.deletion_status === 'requested' && (
                      <>
                        <Button size="sm" className="bg-red-600 hover:bg-red-700 text-[10px] h-6 px-2 flex-1"
                          onClick={() => handleAction(r.id, 'approve')}
                          disabled={!!actionLoading} data-testid={`deletion-approve-${r.id}`}>
                          <CheckCircle className="w-3 h-3 mr-0.5" /> Approva (10gg)
                        </Button>
                        <Button size="sm" variant="outline" className="text-[10px] h-6 px-2 flex-1 border-gray-700 text-gray-400"
                          onClick={() => handleAction(r.id, 'reject')}
                          disabled={!!actionLoading} data-testid={`deletion-reject-${r.id}`}>
                          <Ban className="w-3 h-3 mr-0.5" /> Rifiuta
                        </Button>
                      </>
                    )}
                    {(r.deletion_status === 'user_confirmed' || r.deletion_status === 'final_pending') && (
                      <>
                        <Button size="sm" className="bg-red-600 hover:bg-red-700 text-[10px] h-6 px-2 flex-1"
                          onClick={() => handleAction(r.id, 'final-approve')}
                          disabled={!!actionLoading} data-testid={`deletion-final-approve-${r.id}`}>
                          <Trash2 className="w-3 h-3 mr-0.5" /> Elimina Definitivamente
                        </Button>
                        <Button size="sm" variant="outline" className="text-[10px] h-6 px-2 flex-1 border-gray-700 text-gray-400"
                          onClick={() => handleAction(r.id, 'final-reject')}
                          disabled={!!actionLoading} data-testid={`deletion-final-reject-${r.id}`}>
                          <XCircle className="w-3 h-3 mr-0.5" /> Annulla
                        </Button>
                      </>
                    )}
                    {r.deletion_status === 'countdown_active' && (
                      <p className="text-[9px] text-gray-500 italic">In attesa della scadenza del countdown...</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── DB Management Card (rendered directly by AdminPage — bypasses prop issues) ─── */
function DbManagementCard({ api, isAdmin }) {
  const [subTab, setSubTab] = useState('dashboard');
  const [importFile, setImportFile] = useState(null);
  const [importFileName, setImportFileName] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [dbLoading, setDbLoading] = useState(null);
  const [dbResult, setDbResult] = useState(null);
  const [syncInfo, setSyncInfo] = useState(null);
  const [syncConfirm, setSyncConfirm] = useState('');
  const [loadError, setLoadError] = useState(false);

  // Auto-load sync status on mount
  useEffect(() => {
    setLoadError(false);
    api.get('/admin/db/sync-status', { timeout: 30000 })
      .then(r => setSyncInfo(r.data))
      .catch(() => setLoadError(true));
  }, []);

  const refreshStatus = async () => {
    setDbLoading('status');
    setLoadError(false);
    try { const r = await api.get('/admin/db/sync-status', { timeout: 30000 }); setSyncInfo(r.data); }
    catch { setLoadError(true); toast.error('Errore caricamento stato DB'); }
    finally { setDbLoading(null); }
  };

  // Indicatore colorato
  const getStatusColor = () => {
    if (loadError) return { bg: 'bg-red-500/10', border: 'border-red-500/20', text: 'text-red-400', label: 'Errore connessione' };
    if (!syncInfo) return { bg: 'bg-gray-500/20', border: 'border-gray-500/30', text: 'text-gray-400', label: 'Caricamento...' };
    if (syncInfo.atlas?.messaggio) return { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-400', label: syncInfo.atlas.messaggio };
    if (!syncInfo.atlas?.connesso) return { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-400', label: 'Atlas non raggiungibile' };
    if (syncInfo.sincronizzati) return { bg: 'bg-green-500/15', border: 'border-green-500/30', text: 'text-green-400', label: 'Sincronizzati' };
    return { bg: 'bg-yellow-500/15', border: 'border-yellow-500/30', text: 'text-yellow-400', label: 'Non sincronizzati' };
  };
  const sc = getStatusColor();

  const SUB_TABS = [
    { id: 'dashboard', label: 'Stato DB' },
    { id: 'backup', label: 'Backup / Import' },
    { id: 'sync', label: 'Sincronizzazione' },
  ];

  return (
    <Card className="bg-[#111113] border-indigo-500/30 mt-3" data-testid="db-management-card">
      <CardHeader className="pb-1">
        <CardTitle className="text-sm text-indigo-400 flex items-center gap-2">
          <Wrench className="w-4 h-4" /> Gestione Database
        </CardTitle>
        {/* SOTTOMENU */}
        <div className="flex gap-1 mt-2">
          {SUB_TABS.map(t => (
            <button key={t.id} onClick={() => setSubTab(t.id)}
              className={`px-3 py-1.5 text-[11px] font-semibold rounded-lg transition-colors ${subTab === t.id ? 'bg-indigo-600 text-white' : 'bg-[#1a1a1d] text-gray-400 hover:text-white hover:bg-[#222]'}`}
              data-testid={`db-subtab-${t.id}`}
            >{t.label}</button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-2">

        {/* ━━━ HEADER STATO SEMPRE VISIBILE ━━━ */}
        <div className={`${sc.bg} border ${sc.border} rounded-lg p-3`}>
          <div className="flex items-center justify-between mb-2">
            <p className={`text-xs font-bold ${sc.text} flex items-center gap-1.5`}>
              <span className={`w-2 h-2 rounded-full ${sc.text === 'text-green-400' ? 'bg-green-400' : sc.text === 'text-yellow-400' ? 'bg-yellow-400' : sc.text === 'text-red-400' ? 'bg-red-400' : 'bg-gray-400'} animate-pulse`} />
              {sc.label}
            </p>
            <button onClick={refreshStatus} disabled={dbLoading === 'status'} className="text-gray-500 hover:text-white transition-colors" data-testid="refresh-status-btn">
              <RefreshCw className={`w-3.5 h-3.5 ${dbLoading === 'status' ? 'animate-spin' : ''}`} />
            </button>
          </div>
          {syncInfo && (
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="bg-black/30 rounded-md p-2">
                <p className="text-gray-500 mb-1 font-semibold">DB Corrente ({syncInfo.db_corrente?.tipo})</p>
                <p className="text-white">{syncInfo.db_corrente?.films} Film | {syncInfo.db_corrente?.film_projects} Progetti</p>
                <p className="text-white">{syncInfo.db_corrente?.tv_series} Serie | {syncInfo.db_corrente?.film_drafts} Bozze</p>
                <p className="text-white">{syncInfo.db_corrente?.users} Utenti | {syncInfo.db_corrente?.documenti_totali} Tot</p>
              </div>
              <div className="bg-black/30 rounded-md p-2">
                <p className="text-gray-500 mb-1 font-semibold">Atlas {syncInfo.atlas?.connesso ? '' : syncInfo.atlas?.messaggio ? `(${syncInfo.atlas.messaggio})` : '(offline)'}</p>
                {syncInfo.atlas?.connesso ? (
                  <>
                    <p className="text-white">{syncInfo.atlas?.films} Film | {syncInfo.atlas?.film_projects} Progetti</p>
                    <p className="text-white">{syncInfo.atlas?.tv_series} Serie | {syncInfo.atlas?.film_drafts} Bozze</p>
                    <p className="text-white">{syncInfo.atlas?.users} Utenti | {syncInfo.atlas?.documenti_totali} Tot</p>
                  </>
                ) : (
                  <p className="text-gray-600 text-[9px]">{syncInfo.atlas?.messaggio || 'Non raggiungibile'}</p>
                )}
              </div>
            </div>
          )}
          {loadError && !syncInfo && (
            <p className="text-[10px] text-red-400 mt-1">Impossibile caricare lo stato. Clicca l'icona di aggiornamento per riprovare.</p>
          )}
          {syncInfo?.auto_sync && (
            <p className="text-[9px] text-gray-500 mt-2">
              Auto-sync: {syncInfo.auto_sync.attivo ? `Attivo (ogni ${syncInfo.auto_sync.intervallo_minuti} min)` : 'Non necessario (gia su Atlas)'}
              {syncInfo.auto_sync.ultimo_sync && ` | Ultimo: ${new Date(syncInfo.auto_sync.ultimo_sync).toLocaleString('it-IT')}`}
              {syncInfo.auto_sync.ultimo_errore && <span className="text-red-400"> | Errore: {syncInfo.auto_sync.ultimo_errore}</span>}
            </p>
          )}
        </div>

        {/* ━━━ SUB-TAB: STATO DB (dashboard dettagliata) ━━━ */}
        {subTab === 'dashboard' && syncInfo && (
          <div className="space-y-2 text-[10px]">
            <p className="text-xs text-gray-300 font-semibold">Dettaglio collection con dati</p>
            <div className="bg-black/30 rounded-lg p-2 max-h-56 overflow-y-auto">
              <div className="grid grid-cols-3 gap-1 sticky top-0 bg-black/80 pb-1 mb-1 border-b border-gray-800">
                <p className="text-gray-500 font-bold">Collection</p>
                <p className="text-gray-500 font-bold text-center">Corrente</p>
                <p className="text-gray-500 font-bold text-center">Atlas</p>
              </div>
              {(() => {
                const localD = syncInfo.db_corrente?.dettaglio || {};
                const atlasD = syncInfo.atlas?.dettaglio || {};
                const allKeys = [...new Set([...Object.keys(localD), ...Object.keys(atlasD)])].sort();
                if (allKeys.length === 0) return <p className="text-gray-600 col-span-3">Nessun dato disponibile</p>;
                return allKeys.map(k => {
                  const lv = localD[k] || 0;
                  const av = atlasD[k] || 0;
                  const diff = lv !== av;
                  return (
                    <div key={k} className={`grid grid-cols-3 gap-1 py-0.5 ${diff ? 'bg-yellow-500/5' : ''}`}>
                      <p className="text-gray-400 truncate">{k}</p>
                      <p className="text-white text-center">{lv}</p>
                      <p className={`text-center ${diff ? 'text-yellow-400 font-bold' : 'text-white'}`}>{av}</p>
                    </div>
                  );
                });
              })()}
            </div>
            <p className="text-[9px] text-gray-600">Clicca "Aggiorna" in alto a destra per i dati aggiornati. Le righe gialle indicano differenze.</p>
          </div>
        )}

        {/* ━━━ SUB-TAB: BACKUP / IMPORT ━━━ */}
        {subTab === 'backup' && (
          <div className="space-y-3">
            {/* EXPORT */}
            <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold"
              disabled={dbLoading === 'export'} data-testid="db-export-btn"
              onClick={async () => {
                setDbLoading('export');
                try {
                  const token = localStorage.getItem('cineworld_token');
                  const backendUrl = process.env.REACT_APP_BACKEND_URL;
                  window.open(`${backendUrl}/api/admin/db/download-backup?token=${token}`, '_blank');
                  toast.success('Download backup .zip avviato!');
                } catch (e) { toast.error('Errore avvio download'); }
                finally { setDbLoading(null); }
              }}>
              {dbLoading === 'export' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Download className="w-3 h-3 mr-1" />}
              Scarica Backup (.zip)
            </Button>

            {/* FILE PICKER */}
            <div className="w-full">
              <input type="file" accept=".json,.zip" id="db-import-file" className="hidden" data-testid="db-import-file"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setImportFile(file);
                  setImportFileName(`${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`);
                  toast.success(`File selezionato: ${file.name}`);
                }} />
              <Button type="button" className="w-full bg-gray-700 hover:bg-gray-600 text-white text-xs font-semibold cursor-pointer"
                onClick={() => document.getElementById('db-import-file').click()} data-testid="db-import-file-btn">
                <Upload className="w-3 h-3 mr-1" />
                {importFileName || 'Carica file (.json / .zip)'}
              </Button>
            </div>

            {/* IMPORT SAFE */}
            <Button className="w-full bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold"
              disabled={dbLoading === 'import-safe' || !importFile} data-testid="db-import-safe-btn"
              onClick={async () => {
                setDbLoading('import-safe'); setDbResult(null);
                try {
                  const fd = new FormData(); fd.append('file', importFile);
                  const res = await api.post('/admin/db/import-file-safe', fd, { timeout: 300000, headers: { 'Content-Type': 'multipart/form-data' } });
                  toast.success('Import safe completato');
                  setDbResult({ type: 'import-safe', stats: res.data.stats }); refreshStatus();
                } catch (e) { toast.error(e.response?.data?.detail || 'Errore import'); }
                finally { setDbLoading(null); }
              }}>
              {dbLoading === 'import-safe' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <CheckCircle className="w-3 h-3 mr-1" />}
              Import Safe (upsert)
            </Button>

            {dbResult?.type === 'import-safe' && dbResult.stats && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-2 text-[10px] text-emerald-300 space-y-0.5">
                {Object.entries(dbResult.stats).map(([k,v]) => (
                  <p key={k}>{k}: +{v.inserted} inseriti, ~{v.updated} aggiornati, -{v.skipped} saltati</p>
                ))}
              </div>
            )}

            {/* IMPORT HARD */}
            <div className="border-t border-red-500/20 pt-3">
              <p className="text-[10px] text-red-400 font-bold mb-2 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Hard Reset — Cancella e reimporta tutto
              </p>
              <input type="text" placeholder='Scrivi CONFERMO per procedere' value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                className="w-full bg-black/60 text-red-400 text-xs border border-red-500/30 p-2 rounded-lg placeholder-red-800 focus:border-red-500/60 focus:outline-none"
                data-testid="db-hard-confirm-input" />
              <Button className="w-full mt-2 bg-red-700 hover:bg-red-600 text-white text-xs font-semibold"
                disabled={dbLoading === 'import-hard' || !importFile || confirmText !== 'CONFERMO'} data-testid="db-import-hard-btn"
                onClick={async () => {
                  setDbLoading('import-hard'); setDbResult(null);
                  try {
                    const fd = new FormData(); fd.append('file', importFile);
                    const res = await api.post('/admin/db/import-file-hard?confirm=CONFERMO', fd, { timeout: 300000, headers: { 'Content-Type': 'multipart/form-data' } });
                    toast.success('Import HARD completato');
                    setDbResult({ type: 'import-hard', stats: res.data.stats }); setConfirmText(''); refreshStatus();
                  } catch (e) { toast.error(e.response?.data?.detail || 'Errore import hard'); }
                  finally { setDbLoading(null); }
                }}>
                {dbLoading === 'import-hard' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Trash2 className="w-3 h-3 mr-1" />}
                Import HARD (reset)
              </Button>

              {dbResult?.type === 'import-hard' && dbResult.stats && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-2 mt-2 text-[10px] text-red-300 space-y-0.5">
                  <p className="font-bold">Reset completato:</p>
                  {Object.entries(dbResult.stats).map(([k,v]) => (
                    <p key={k}>{k}: {v.deleted} eliminati, {v.inserted} reinseriti</p>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ━━━ SUB-TAB: SINCRONIZZAZIONE ━━━ */}
        {subTab === 'sync' && (
          <div className="space-y-3">
            <div className="flex gap-2">
              <Button className="flex-1 bg-blue-700 hover:bg-blue-600 text-white text-xs font-semibold"
                disabled={!!dbLoading || syncConfirm !== 'CONFERMO'} data-testid="sync-to-atlas-btn"
                onClick={async () => {
                  setDbLoading('sync-to');
                  try {
                    const res = await api.post('/admin/db/sync-to-atlas', { confirm: 'CONFERMO' }, { timeout: 300000 });
                    toast.success(`Inviati a Atlas: ${res.data.documenti_copiati} documenti`);
                    setSyncConfirm(''); refreshStatus();
                  } catch (e) { toast.error(e.response?.data?.detail || 'Errore sync'); }
                  finally { setDbLoading(null); }
                }}>
                {dbLoading === 'sync-to' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Upload className="w-3 h-3 mr-1" />}
                Invia a Atlas
              </Button>

              <Button className="flex-1 bg-purple-700 hover:bg-purple-600 text-white text-xs font-semibold"
                disabled={!!dbLoading || syncConfirm !== 'CONFERMO'} data-testid="sync-from-atlas-btn"
                onClick={async () => {
                  setDbLoading('sync-from');
                  try {
                    const res = await api.post('/admin/db/sync-from-atlas', { confirm: 'CONFERMO' }, { timeout: 300000 });
                    toast.success(`Ricevuti da Atlas: ${res.data.documenti_copiati} documenti`);
                    setSyncConfirm(''); refreshStatus();
                  } catch (e) { toast.error(e.response?.data?.detail || 'Errore sync'); }
                  finally { setDbLoading(null); }
                }}>
                {dbLoading === 'sync-from' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Download className="w-3 h-3 mr-1" />}
                Ricevi da Atlas
              </Button>
            </div>

            <input placeholder="Scrivi CONFERMO per abilitare sync" value={syncConfirm}
              onChange={(e) => setSyncConfirm(e.target.value)}
              className="w-full bg-black/60 text-white text-xs border border-gray-700 p-2 rounded-lg placeholder-gray-600 focus:border-cyan-500/50 focus:outline-none"
              data-testid="sync-confirm-input" />

            <div className="text-[10px] text-gray-500 space-y-1 bg-black/20 rounded-lg p-2">
              <p><span className="text-blue-400 font-semibold">Invia a Atlas</span> — Copia tutto dal DB corrente verso il tuo Atlas</p>
              <p><span className="text-purple-400 font-semibold">Ricevi da Atlas</span> — Copia tutto da Atlas nel DB corrente</p>
              <p className="text-gray-600">NeoMorpheus viene preservato su entrambi i lati.</p>
            </div>
          </div>
        )}

      </CardContent>
    </Card>
  );
}

/* ─── Migration Tab ─── */
const CAT_CONFIG = {
  A_COMPLETED: { label: 'V1 Completati', color: 'bg-blue-500/20 text-blue-400', icon: CheckCircle },
  A_COMPLETED_NOFILM: { label: 'V1 Completati (no film)', color: 'bg-blue-500/20 text-blue-300', icon: CheckCircle },
  B_STUCK: { label: 'V1 Bloccati', color: 'bg-yellow-500/20 text-yellow-400', icon: AlertTriangle },
  C_SYSTEM: { label: 'Film di Sistema', color: 'bg-gray-500/20 text-gray-400', icon: Ban },
  D_V2_STUCK: { label: 'V2 Bloccati', color: 'bg-orange-500/20 text-orange-400', icon: Clock },
  D_V2_INVALID: { label: 'V2 Stato Invalido', color: 'bg-red-500/20 text-red-400', icon: XCircle },
  OK: { label: 'V2 OK', color: 'bg-emerald-500/20 text-emerald-400', icon: CheckCircle },
};

const V2_STATES = ['draft','idea','proposed','hype_setup','hype_live','casting_live','prep','shooting','postproduction','sponsorship','marketing','premiere_setup','premiere_live','release_pending','released','completed','discarded'];


// ═══════════════════════════════════════════
// TUTORIAL MANAGER TAB
// ═══════════════════════════════════════════
function TutorialManagerTab({ api }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const pollingRef = useRef(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.get('/admin/tutorial/status');
      setStatus(res.data);
      setLoading(false);
      if (res.data.update_job?.status === 'done' || res.data.update_job?.status === 'error') {
        if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      }
    } catch { setLoading(false); }
  }, [api]);

  useEffect(() => { fetchStatus(); return () => { if (pollingRef.current) clearInterval(pollingRef.current); }; }, [fetchStatus]);

  const startPolling = () => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(fetchStatus, 1500);
    fetchStatus();
  };

  const startUpdate = async (type) => {
    try {
      await api.post(`/admin/tutorial/update/${type}`);
      toast.success(`Aggiornamento ${type} (DB) avviato`);
      startPolling();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const startAiUpdate = async (type) => {
    try {
      await api.post(`/admin/tutorial/update-ai/${type}`);
      toast.success(`Generazione AI ${type} avviata`);
      startPolling();
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
  };

  const job = status?.update_job || {};
  const isProcessing = job.status === 'processing' || job.status === 'starting';
  const isAiJob = (job.type || '').includes('_ai');

  const formatDate = (iso) => {
    if (!iso) return 'Mai';
    return new Date(iso).toLocaleString('it-IT', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  };

  if (loading) return <div className="text-center py-8"><Loader2 className="w-6 h-6 animate-spin mx-auto text-yellow-500" /></div>;

  const CARDS = [
    { key: 'static', label: 'Tutorial Statico', sub: `Contenuti: ${status?.static?.content_count || 0} blocchi`, ver: status?.static?.version, date: status?.static?.last_update, dbColor: 'blue', aiColor: 'emerald' },
    { key: 'velion', label: 'Tutorial Velion', sub: `Steps: ${status?.velion?.steps_count || 0}`, ver: status?.velion?.version, date: status?.velion?.last_update, dbColor: 'cyan', aiColor: 'emerald' },
    { key: 'guest', label: 'Tutorial Guest', sub: `Steps: ${status?.guest?.steps_count || 0}`, ver: status?.guest?.version, date: status?.guest?.last_update, dbColor: 'purple', aiColor: 'emerald' },
  ];

  return (
    <div className="space-y-4" data-testid="tutorial-manager-tab">
      <Card className="bg-[#111] border-white/10">
        <CardContent className="p-4">
          <h3 className="font-bold text-sm text-white mb-3 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-yellow-500" /> TUTORIAL MANAGER
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
            {CARDS.map(c => (
              <div key={c.key} className="bg-black/30 rounded-lg p-3 border border-white/5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-300">{c.label}</span>
                  <Badge variant="outline" className="text-[9px] h-4 border-white/10">v{c.ver || 0}</Badge>
                </div>
                <p className="text-[10px] text-gray-500 mb-1">{c.sub}</p>
                <p className="text-[10px] text-gray-600 mb-2.5">Ultimo: {formatDate(c.date)}</p>
                <div className="grid grid-cols-2 gap-1.5">
                  <Button
                    size="sm"
                    className={`h-7 text-[10px] bg-${c.dbColor}-500/15 text-${c.dbColor}-400 hover:bg-${c.dbColor}-500/25 border border-${c.dbColor}-500/20`}
                    style={{ backgroundColor: c.dbColor === 'blue' ? 'rgba(59,130,246,0.15)' : c.dbColor === 'cyan' ? 'rgba(6,182,212,0.15)' : 'rgba(168,85,247,0.15)', color: c.dbColor === 'blue' ? '#60a5fa' : c.dbColor === 'cyan' ? '#22d3ee' : '#c084fc', borderColor: c.dbColor === 'blue' ? 'rgba(59,130,246,0.2)' : c.dbColor === 'cyan' ? 'rgba(6,182,212,0.2)' : 'rgba(168,85,247,0.2)' }}
                    onClick={() => startUpdate(c.key)}
                    disabled={isProcessing}
                    data-testid={`update-${c.key}-db-btn`}
                  >
                    {isProcessing && job.type === c.key ? <Loader2 className="w-3 h-3 animate-spin mr-0.5" /> : <RefreshCw className="w-3 h-3 mr-0.5" />}
                    Da DB
                  </Button>
                  <Button
                    size="sm"
                    className="h-7 text-[10px] border"
                    style={{ backgroundColor: 'rgba(16,185,129,0.15)', color: '#34d399', borderColor: 'rgba(16,185,129,0.25)' }}
                    onClick={() => startAiUpdate(c.key)}
                    disabled={isProcessing}
                    data-testid={`update-${c.key}-ai-btn`}
                  >
                    {isProcessing && job.type === `${c.key}_ai` ? <Loader2 className="w-3 h-3 animate-spin mr-0.5" /> : <Sparkles className="w-3 h-3 mr-0.5" />}
                    Con AI
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* Progress Box */}
          {(isProcessing || job.status === 'done' || job.status === 'error') && (
            <div className={`rounded-lg p-3 border ${isAiJob ? 'bg-emerald-500/5 border-emerald-500/10' : 'bg-black/40 border-white/5'}`} data-testid="tutorial-progress-box">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-300">
                  {isProcessing ? (isAiJob ? 'Generazione AI in corso' : 'Aggiornamento DB in corso') : job.status === 'done' ? 'Completato' : 'Errore'}
                </span>
                <Badge className={`text-[9px] h-4 ${job.status === 'done' ? 'bg-green-500/20 text-green-400' : job.status === 'error' ? 'bg-red-500/20 text-red-400' : isAiJob ? 'bg-emerald-500/20 text-emerald-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                  {isAiJob ? `${(job.type || '').replace('_ai', '')} (AI)` : job.type}
                </Badge>
              </div>
              <div className="w-full bg-white/5 rounded-full h-2 mb-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${job.status === 'done' ? 'bg-green-500' : job.status === 'error' ? 'bg-red-500' : isAiJob ? 'bg-emerald-500' : 'bg-yellow-500'}`}
                  style={{ width: `${job.progress || 0}%` }}
                  data-testid="tutorial-progress-bar"
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-gray-500">{job.current_step || 'Idle'}</span>
                <span className="text-[10px] text-gray-400 font-mono">{job.progress || 0}%</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Frozen Sections Info */}
      <Card className="bg-[#111] border-white/10">
        <CardContent className="p-4">
          <h3 className="font-bold text-sm text-white mb-3 flex items-center gap-2">
            <Lock className="w-4 h-4 text-amber-500" /> SEZIONI TEMPORANEAMENTE FREEZATE
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-black/30 rounded-lg p-3 border border-amber-500/10 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <Lock className="w-4 h-4 text-amber-400" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-300">Note di Rilascio</p>
                <p className="text-[10px] text-amber-400">
                  {status?.frozen_sections?.release_notes?.label || 'In aggiornamento'}
                </p>
              </div>
            </div>
            <div className="bg-black/30 rounded-lg p-3 border border-amber-500/10 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <Lock className="w-4 h-4 text-amber-400" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-300">Note di Sistema</p>
                <p className="text-[10px] text-amber-400">
                  {status?.frozen_sections?.system_notes?.label || 'In aggiornamento'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


function MigrationTab({ api }) {
  const gameConfirm = useConfirm();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(null);
  const [migrating, setMigrating] = useState(null);
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [forceState, setForceState] = useState({});

  const doScan = async () => {
    setLoading(true);
    setScan(null);
    setPreview(null);
    setBatchResult(null);
    try {
      const res = await api.get('/admin/migration/scan');
      setScan(res.data);
    } catch (e) {
      toast.error('Errore scan: ' + (e.response?.data?.detail || e.message));
    }
    setLoading(false);
  };

  const doPreview = async (pid) => {
    setPreviewLoading(pid);
    try {
      const res = await api.get(`/admin/migration/preview/${pid}`);
      setPreview(res.data);
    } catch (e) {
      toast.error('Errore preview: ' + (e.response?.data?.detail || e.message));
    }
    setPreviewLoading(null);
  };

  const doMigrate = async (pid, forceDiscard = false) => {
    setMigrating(pid);
    try {
      const body = { force_discard: forceDiscard };
      if (forceState[pid]) body.force_state = forceState[pid];
      const res = await api.post(`/admin/migration/migrate/${pid}`, body);
      toast.success(res.data.message || 'Migrato!');
      doScan();
      setPreview(null);
    } catch (e) {
      toast.error('Errore migrazione: ' + (e.response?.data?.detail || e.message));
    }
    setMigrating(null);
  };

  const doBatchMigrate = async () => {
    if (!await gameConfirm({ title: 'Migrare TUTTI i progetti?', subtitle: 'Questa azione non è reversibile.', confirmLabel: 'Migra Tutti' })) return;
    setBatchRunning(true);
    try {
      const res = await api.post('/admin/migration/migrate-all', {});
      setBatchResult(res.data);
      toast.success(`Batch: ${res.data.migrated} migrati, ${res.data.fixed} fixati, ${res.data.discarded} scartati`);
      doScan();
    } catch (e) {
      toast.error('Errore batch: ' + (e.response?.data?.detail || e.message));
    }
    setBatchRunning(false);
  };

  const actionable = scan ? ['A_COMPLETED', 'A_COMPLETED_NOFILM', 'B_STUCK', 'C_SYSTEM', 'D_V2_STUCK', 'D_V2_INVALID'] : [];

  return (
    <div className="space-y-4" data-testid="migration-tab">
      {/* Header */}
      <Card className="bg-[#111113] border-white/5">
        <CardContent className="p-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <ArrowRightLeft className="w-4 h-4 text-cyan-400" />
                Tool di Migrazione V1 → V2
              </h2>
              <p className="text-[10px] text-gray-500 mt-0.5">
                Scansiona il DB corrente, anteprima e migra i progetti
              </p>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={doScan} disabled={loading}
                className="bg-cyan-600 hover:bg-cyan-700 text-xs h-8"
                data-testid="migration-scan-btn">
                {loading ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Search className="w-3 h-3 mr-1" />}
                Scansiona DB
              </Button>
              {scan && scan.summary.need_migration + scan.summary.need_fix > 0 && (
                <Button size="sm" onClick={doBatchMigrate} disabled={batchRunning}
                  className="bg-amber-600 hover:bg-amber-700 text-xs h-8"
                  data-testid="migration-batch-btn">
                  {batchRunning ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Zap className="w-3 h-3 mr-1" />}
                  Migra Tutti ({scan.summary.need_migration + scan.summary.need_fix})
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      {scan && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            { label: 'Da Migrare', val: scan.summary.need_migration, color: 'text-yellow-400' },
            { label: 'Da Fixare', val: scan.summary.need_fix, color: 'text-orange-400' },
            { label: 'OK', val: scan.summary.ok, color: 'text-emerald-400' },
            { label: 'Sistema (skip)', val: scan.summary.skip, color: 'text-gray-400' },
          ].map(s => (
            <Card key={s.label} className="bg-[#111113] border-white/5">
              <CardContent className="p-3 text-center">
                <div className={`text-xl font-black ${s.color}`}>{s.val}</div>
                <div className="text-[10px] text-gray-500">{s.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Batch Result */}
      {batchResult && (
        <Card className="bg-emerald-500/10 border-emerald-500/30">
          <CardContent className="p-3">
            <p className="text-xs font-bold text-emerald-400">Batch completato</p>
            <p className="text-[10px] text-gray-400 mt-1">
              Migrati: {batchResult.migrated} | Fixati: {batchResult.fixed} | Scartati: {batchResult.discarded} | Errori: {batchResult.errors}
            </p>
            {batchResult.details?.map((d, i) => (
              <p key={i} className="text-[10px] text-gray-500">{d.title}: {d.action}</p>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Projects by Category */}
      {scan && actionable.map(cat => {
        const items = scan.categories[cat] || [];
        if (!items.length) return null;
        const cfg = CAT_CONFIG[cat] || CAT_CONFIG.OK;
        const CatIcon = cfg.icon;
        return (
          <Card key={cat} className="bg-[#111113] border-white/5">
            <CardHeader className="p-3 pb-2">
              <CardTitle className="text-xs font-bold text-white flex items-center gap-2">
                <CatIcon className="w-3.5 h-3.5" />
                {cfg.label} ({items.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0 space-y-2">
              {items.map(item => (
                <div key={item.id} className="bg-black/30 rounded-lg p-3 border border-white/5" data-testid={`migration-item-${item.id}`}>
                  <div className="flex items-start justify-between gap-2 flex-wrap">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-bold text-white truncate">{item.title}</span>
                        <Badge className={`text-[9px] h-4 ${cfg.color}`}>
                          {item.classification?.label}
                        </Badge>
                        {item.content_type && item.content_type !== 'film' && (
                          <Badge className="text-[9px] h-4 bg-purple-500/20 text-purple-400">
                            {item.content_type === 'serie_tv' ? 'Serie TV' : 'Anime'}
                          </Badge>
                        )}
                      </div>
                      <div className="flex gap-3 mt-1 text-[10px] text-gray-500 flex-wrap">
                        <span>Utente: {scan.users_map?.[item.user_id] || item.user_id?.slice(0,8) || 'N/A'}</span>
                        <span>Genere: {item.genre}</span>
                        {item.has_cast && <span>Cast: {item.actor_count} attori</span>}
                        {item.has_screenplay && <span>Sceneggiatura</span>}
                        {item.has_poster && <span>Poster</span>}
                        {item.final_quality && <span>Qualita: {item.final_quality}</span>}
                        {item.film_id && <span>Film rilasciato</span>}
                      </div>
                      {item.classification?.issues?.length > 0 && (
                        <div className="flex gap-1 mt-1 flex-wrap">
                          {item.classification.issues.map((iss, i) => (
                            <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400">{iss}</span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-1.5 items-center flex-shrink-0">
                      {/* Force state selector for stuck projects */}
                      {(cat.startsWith('D_') || cat === 'B_STUCK') && (
                        <select
                          value={forceState[item.id] || ''}
                          onChange={e => setForceState(prev => ({...prev, [item.id]: e.target.value}))}
                          className="bg-black/50 border border-white/10 rounded text-[10px] text-gray-300 h-7 px-1"
                          data-testid={`force-state-${item.id}`}>
                          <option value="">Auto</option>
                          {V2_STATES.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                      )}
                      <Button size="sm" variant="outline"
                        className="text-[10px] h-7 px-2 border-white/10"
                        onClick={() => doPreview(item.id)}
                        disabled={previewLoading === item.id}
                        data-testid={`preview-btn-${item.id}`}>
                        {previewLoading === item.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Eye className="w-3 h-3 mr-1" />}
                        Anteprima
                      </Button>
                      <Button size="sm"
                        className="text-[10px] h-7 px-2 bg-cyan-600 hover:bg-cyan-700"
                        onClick={() => doMigrate(item.id)}
                        disabled={migrating === item.id}
                        data-testid={`migrate-btn-${item.id}`}>
                        {migrating === item.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <ArrowRightLeft className="w-3 h-3 mr-1" />}
                        {cat === 'C_SYSTEM' ? 'Scarta' : cat.startsWith('D_') ? 'Fix' : 'Migra'}
                      </Button>
                      {cat !== 'C_SYSTEM' && (
                        <Button size="sm" variant="outline"
                          className="text-[10px] h-7 px-2 border-red-500/30 text-red-400 hover:bg-red-500/10"
                          onClick={() => doMigrate(item.id, true)}
                          disabled={migrating === item.id}
                          data-testid={`discard-btn-${item.id}`}>
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        );
      })}

      {/* OK Projects (collapsed) */}
      {scan && (scan.categories.OK || []).length > 0 && (
        <Card className="bg-[#111113] border-white/5">
          <CardContent className="p-3">
            <p className="text-xs font-bold text-emerald-400 flex items-center gap-2">
              <CheckCircle className="w-3.5 h-3.5" />
              V2 OK ({scan.categories.OK.length} progetti)
            </p>
            <div className="mt-2 flex flex-wrap gap-1">
              {scan.categories.OK.map(item => (
                <span key={item.id} className="text-[10px] px-2 py-1 rounded bg-emerald-500/10 text-emerald-400/70">
                  {item.title}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preview Panel */}
      {preview && (
        <Card className="bg-[#0D1117] border-cyan-500/30">
          <CardHeader className="p-3 pb-2">
            <CardTitle className="text-xs font-bold text-cyan-400 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Eye className="w-3.5 h-3.5" />
                Anteprima Migrazione: {preview.project?.title}
              </span>
              <button onClick={() => setPreview(null)} className="text-gray-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0 space-y-3">
            {/* Current → Target */}
            <div className="flex items-center gap-2 text-xs">
              <span className="px-2 py-1 rounded bg-red-500/20 text-red-400">
                {preview.current_state?.pipeline_state || preview.current_state?.status || '?'}
              </span>
              <ArrowRightLeft className="w-3 h-3 text-gray-500" />
              <span className="px-2 py-1 rounded bg-cyan-500/20 text-cyan-400">
                {preview.proposed_changes?.target_state || preview.proposed_changes?.fixes?.pipeline_state || preview.proposed_changes?.action || '?'}
              </span>
            </div>

            {/* Data Preserved */}
            {preview.data_preserved?.length > 0 && (
              <div>
                <p className="text-[10px] font-semibold text-emerald-400 mb-1">Dati Preservati:</p>
                <div className="flex flex-wrap gap-1">
                  {preview.data_preserved.map((d, i) => (
                    <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">{d}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Fields Added */}
            {preview.proposed_changes?.fields_added > 0 && (
              <p className="text-[10px] text-gray-400">
                Campi aggiunti: <span className="text-white">{preview.proposed_changes.fields_added}</span> |
                Campi aggiornati: <span className="text-white">{preview.proposed_changes.fields_updated}</span>
              </p>
            )}

            {/* Fix Actions */}
            {preview.proposed_changes?.actions && (
              <div>
                <p className="text-[10px] font-semibold text-orange-400 mb-1">Azioni Fix:</p>
                {preview.proposed_changes.actions.map((a, i) => (
                  <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400 mr-1">{a}</span>
                ))}
              </div>
            )}

            {/* Warnings */}
            {preview.warnings?.length > 0 && (
              <div>
                <p className="text-[10px] font-semibold text-red-400 mb-1">Avvisi:</p>
                {preview.warnings.map((w, i) => (
                  <p key={i} className="text-[9px] text-red-400/70">{w}</p>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {!scan && !loading && (
        <Card className="bg-[#111113] border-white/5">
          <CardContent className="p-8 text-center">
            <ArrowRightLeft className="w-8 h-8 mx-auto mb-3 text-gray-600" />
            <p className="text-xs text-gray-500">Premi "Scansiona DB" per analizzare i progetti</p>
            <p className="text-[10px] text-gray-600 mt-1">Funziona su qualsiasi DB a cui l'app e connessa</p>
          </CardContent>
        </Card>
      )}

      {/* ═══ MIGRAZIONE SERIE / ANIME ═══ */}
      <SeriesAnimeMigrationSection api={api} />
    </div>
  );
}

// ═══════════════════════════════════════════
// MIGRAZIONE SERIE / ANIME (vecchio → nuovo formato)
// ═══════════════════════════════════════════
function SeriesAnimeMigrationSection({ api }) {
  const [series, setSeries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [migrationStatus, setMigrationStatus] = useState({});
  const pollingRefs = useRef({});
  const gameConfirm = useConfirm();

  const fetchSeries = async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/migration/old-series');
      setSeries(res.data.series || []);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setLoading(false);
  };

  useEffect(() => { fetchSeries(); return () => { Object.values(pollingRefs.current).forEach(clearInterval); }; }, []);

  const startMigration = async (sid) => {
    if (!await gameConfirm({ title: 'Migrare questa serie?', subtitle: 'AI generera titoli e trame episodi. Il valore IMDb restera invariato.', confirmLabel: 'Migra con AI' })) return;
    try {
      await api.post('/admin/migration/migrate-series', { series_id: sid });
      toast.success('Migrazione avviata');
      // Start polling
      pollingRefs.current[sid] = setInterval(async () => {
        try {
          const res = await api.get(`/admin/migration/migrate-status/${sid}`);
          setMigrationStatus(prev => ({ ...prev, [sid]: res.data }));
          if (res.data.status === 'done' || res.data.status === 'error') {
            clearInterval(pollingRefs.current[sid]);
            delete pollingRefs.current[sid];
            if (res.data.status === 'done') fetchSeries();
          }
        } catch { }
      }, 1500);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  return (
    <Card className="bg-[#111113] border-white/5" data-testid="series-migration-section">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Film className="w-4 h-4 text-purple-400" />
            Migrazione Serie TV / Anime
          </h2>
          <Button size="sm" onClick={fetchSeries} disabled={loading} className="bg-purple-600 hover:bg-purple-700 text-xs h-7" data-testid="scan-series-btn">
            {loading ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <RefreshCw className="w-3 h-3 mr-1" />}
            Aggiorna
          </Button>
        </div>
        <p className="text-[10px] text-gray-500 mb-3">
          Converte serie/anime dal vecchio formato al nuovo (episodi con titoli AI, cast strutturato). IMDb invariato.
        </p>

        {series.length === 0 && !loading && (
          <p className="text-xs text-gray-600 text-center py-4">Nessuna serie/anime trovata</p>
        )}

        <div className="space-y-2">
          {series.map(s => {
            const ms = migrationStatus[s.id] || {};
            const isProcessing = ms.status === 'processing';
            return (
              <div key={s.id} className={`bg-black/30 rounded-lg p-3 border ${s.migrated ? 'border-emerald-500/20' : 'border-white/5'}`} data-testid={`series-item-${s.id}`}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-bold text-white truncate">{s.title}</span>
                      <Badge className={`text-[9px] h-4 ${s.type === 'anime' ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'}`}>
                        {s.type === 'anime' ? 'Anime' : 'Serie TV'}
                      </Badge>
                      {s.migrated && <Badge className="text-[9px] h-4 bg-emerald-500/20 text-emerald-400">Migrato</Badge>}
                      {!s.migrated && s.needs_migration && <Badge className="text-[9px] h-4 bg-yellow-500/20 text-yellow-400">Da migrare</Badge>}
                    </div>
                    <div className="flex gap-3 mt-1 text-[10px] text-gray-500 flex-wrap">
                      <span>{s.genre}</span>
                      <span>{s.episodes_count} ep</span>
                      <span>Cast: {s.cast_format}</span>
                      {s.quality_score > 0 && <span>Q: {Math.round(s.quality_score)}</span>}
                    </div>
                  </div>
                  {!s.migrated && (
                    <Button size="sm" onClick={() => startMigration(s.id)} disabled={isProcessing}
                      className="h-7 text-[10px] bg-purple-500/15 text-purple-400 hover:bg-purple-500/25 border border-purple-500/20 flex-shrink-0"
                      data-testid={`migrate-btn-${s.id}`}>
                      {isProcessing ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Sparkles className="w-3 h-3 mr-1" />}
                      Migra AI
                    </Button>
                  )}
                </div>
                {/* Progress bar */}
                {(isProcessing || ms.status === 'done' || ms.status === 'error') && (
                  <div className="mt-2">
                    <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                      <div className={`h-1.5 rounded-full transition-all duration-500 ${ms.status === 'done' ? 'bg-emerald-500' : ms.status === 'error' ? 'bg-red-500' : 'bg-purple-500'}`}
                        style={{ width: `${ms.progress || 0}%` }} />
                    </div>
                    <p className="text-[9px] text-gray-500 mt-0.5">{ms.step || ''} {ms.progress ? `(${ms.progress}%)` : ''}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

/* ─── Promo Video Tab — Automated Instagram promo video generator ─── */
function PromoVideoTab({ api }) {
  const [screens, setScreens] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [duration, setDuration] = useState(30);
  const [frameCount, setFrameCount] = useState(0); // 0 = auto
  const [tone, setTone] = useState('energico');
  const [music, setMusic] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [jobs, setJobs] = useState([]);
  const [currentJob, setCurrentJob] = useState(null);
  const [loadingStart, setLoadingStart] = useState(false);
  const pollRef = useRef(null);

  const loadScreens = useCallback(async () => {
    try {
      const r = await api.get('/admin/promo-video/screens');
      setScreens(r.data || []);
      setSelected(new Set((r.data || []).map(s => s.key)));
    } catch { /* noop */ }
  }, [api]);

  const loadJobs = useCallback(async () => {
    try {
      const r = await api.get('/admin/promo-video/jobs?limit=10');
      setJobs(r.data?.jobs || []);
    } catch { /* noop */ }
  }, [api]);

  useEffect(() => { loadScreens(); loadJobs(); }, [loadScreens, loadJobs]);

  const toggleScreen = (key) => {
    setSelected(prev => {
      const s = new Set(prev);
      s.has(key) ? s.delete(key) : s.add(key);
      return s;
    });
  };

  const pollJob = useCallback(async (jobId) => {
    try {
      const r = await api.get(`/admin/promo-video/jobs/${jobId}`);
      setCurrentJob(r.data);
      if (r.data.status === 'completed' || r.data.status === 'failed') {
        clearInterval(pollRef.current); pollRef.current = null;
        loadJobs();
        if (r.data.status === 'completed') toast.success('Video pronto!');
        else toast.error(`Errore: ${r.data.error || 'sconosciuto'}`);
      }
    } catch { /* noop */ }
  }, [api, loadJobs]);

  const startJob = async () => {
    if (selected.size === 0) { toast.error('Seleziona almeno una pagina'); return; }
    setLoadingStart(true);
    try {
      const r = await api.post('/admin/promo-video/generate', {
        duration_seconds: duration,
        screens: Array.from(selected),
        custom_prompt: customPrompt.trim(),
        tone, music,
        frame_count: frameCount,
      });
      const jobId = r.data.job_id;
      setCurrentJob({ job_id: jobId, status: 'queued', progress: 0, stage: 'queued', log: [] });
      pollRef.current = setInterval(() => pollJob(jobId), 2000);
      toast('Generazione avviata');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setLoadingStart(false); }
  };

  const download = async (jobId) => {
    try {
      const r = await api.get(`/admin/promo-video/download/${jobId}`, { responseType: 'blob' });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement('a');
      a.href = url; a.download = `cineworld_promo_${jobId}.mp4`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch { toast.error('Download fallito'); }
  };

  const deleteJob = async (jobId) => {
    if (!window.confirm('Eliminare questo video?')) return;
    try { await api.delete(`/admin/promo-video/jobs/${jobId}`); loadJobs(); toast.success('Eliminato'); }
    catch { toast.error('Errore'); }
  };

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const running = currentJob && currentJob.status !== 'completed' && currentJob.status !== 'failed';

  return (
    <Card className="bg-[#111113] border-white/5" data-testid="promo-video-tab">
      <CardHeader className="p-4 pb-2">
        <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
          <Video className="w-4 h-4 text-rose-400" /> Promo Video Generator
        </CardTitle>
        <p className="text-[10px] text-gray-500">Genera automaticamente un video 1080×1920 Instagram-ready con screenshot del gioco + caption AI.</p>
      </CardHeader>
      <CardContent className="p-4 pt-2 space-y-4">

        <div className="bg-amber-500/10 border border-amber-500/30 rounded-md p-3 text-[10px] text-amber-200 leading-relaxed" data-testid="promo-preview-notice">
          <div className="font-bold text-amber-300 mb-1">⚠️ Raccomandato: usa la Preview</div>
          Questa funzione richiede Chromium + FFmpeg e funziona in modo affidabile solo su preview. In produzione alcune dipendenze potrebbero non essere disponibili.
          <a href="https://invisible-cash-boost.preview.emergentagent.com/admin" target="_blank" rel="noopener noreferrer"
             className="block mt-1.5 text-amber-300 underline font-semibold break-all"
             data-testid="promo-preview-link">
            → Apri Admin su Preview
          </a>
        </div>

        {/* Duration */}
        <div>
          <label className="text-[10px] font-bold text-gray-400 uppercase">Durata video</label>
          <div className="grid grid-cols-4 gap-1.5 mt-1">
            {[30, 60, 90, 120].map(d => (
              <button key={d} onClick={() => setDuration(d)} disabled={running}
                className={`text-[11px] py-2 rounded-md font-semibold border ${duration === d ? 'bg-rose-500/20 border-rose-500/40 text-rose-300' : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'}`}
                data-testid={`duration-${d}`}>
                {d}s
              </button>
            ))}
          </div>
        </div>

        {/* Tone */}
        <div>
          <label className="text-[10px] font-bold text-gray-400 uppercase">Tono caption</label>
          <div className="grid grid-cols-3 gap-1.5 mt-1">
            {[{k:'energico',l:'🎬 Energico'},{k:'neutro',l:'📃 Neutro'},{k:'ironico',l:'😄 Ironico'}].map(o => (
              <button key={o.k} onClick={() => setTone(o.k)} disabled={running}
                className={`text-[10px] py-2 rounded-md font-semibold border ${tone === o.k ? 'bg-purple-500/20 border-purple-500/40 text-purple-300' : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'}`}
                data-testid={`tone-${o.k}`}>
                {o.l}
              </button>
            ))}
          </div>
        </div>

        {/* Music */}
        <div className="flex items-center gap-2">
          <input id="promo-music" type="checkbox" checked={music} onChange={e => setMusic(e.target.checked)} disabled={running} className="w-4 h-4" data-testid="promo-music"/>
          <label htmlFor="promo-music" className="text-xs text-gray-300">Aggiungi musica di sottofondo (se disponibile)</label>
        </div>

        {/* Frame count */}
        {(() => {
          const effective = frameCount > 0 ? frameCount : Math.max(1, selected.size);
          const perFrame = duration / Math.max(1, effective);
          const ratioLabel = perFrame.toFixed(2) + 's/frame';
          let warnColor = 'text-emerald-400', warnMsg = 'Ritmo cinematografico ottimale';
          if (perFrame < 0.8) { warnColor = 'text-red-400'; warnMsg = '⚠️ Troppo veloce! Frame illeggibili, caption non hanno tempo di essere lette'; }
          else if (perFrame < 1.3) { warnColor = 'text-amber-400'; warnMsg = '⚠️ Ritmo frenetico — consigliato per flash/preview ma rischia caos visivo'; }
          else if (perFrame > 5) { warnColor = 'text-amber-400'; warnMsg = 'ℹ️ Ritmo lento — frame fermi a lungo, rischia di essere noioso'; }
          else if (perFrame > 3.5) { warnColor = 'text-sky-400'; warnMsg = 'ℹ️ Ritmo rilassato — ok per narrazione estesa'; }
          return (
            <div data-testid="frame-count-row">
              <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold text-gray-400 uppercase">Numero frame</label>
                <span className="text-[10px] text-gray-500">
                  {frameCount === 0 ? <>auto ({selected.size})</> : frameCount}
                  <span className="text-gray-600"> · {ratioLabel}</span>
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <button onClick={() => setFrameCount(0)} disabled={running}
                  className={`text-[10px] px-2 py-1 rounded border font-semibold ${frameCount === 0 ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300' : 'bg-white/5 border-white/10 text-gray-400'}`}
                  data-testid="frame-auto">auto</button>
                <input type="range" min="5" max="100" step="1"
                  value={frameCount === 0 ? (selected.size || 14) : frameCount}
                  onChange={e => setFrameCount(Number(e.target.value))}
                  disabled={running}
                  className="flex-1 accent-rose-500"
                  data-testid="frame-count-slider"/>
                <input type="number" min="5" max="100"
                  value={frameCount === 0 ? '' : frameCount}
                  placeholder="auto"
                  onChange={e => setFrameCount(Math.max(0, Math.min(100, Number(e.target.value) || 0)))}
                  disabled={running}
                  className="w-14 text-[10px] bg-black/40 border border-white/10 rounded px-2 py-1 text-gray-200 text-right"
                  data-testid="frame-count-input"/>
              </div>
              <div className={`text-[10px] mt-1 ${warnColor}`} data-testid="frame-warning">{warnMsg}</div>
              <div className="text-[9px] text-gray-600 mt-0.5">
                Esempi coerenti: 15 frame/30s · 30 frame/60s · 50 frame/120s. Se N supera le pagine selezionate, le pagine vengono ciclate con caption diverse.
              </div>
            </div>
          );
        })()}

        {/* Custom prompt */}
        <div>
          <label className="text-[10px] font-bold text-gray-400 uppercase">Prompt personalizzato (opzionale)</label>
          <textarea value={customPrompt} onChange={e => setCustomPrompt(e.target.value)} disabled={running}
            rows={2} maxLength={400}
            placeholder="Es. Enfatizza il lato competitivo dei trailer e la community…"
            className="w-full mt-1 text-xs bg-black/40 border border-white/10 rounded-md p-2 text-gray-200 placeholder:text-gray-600"
            data-testid="promo-custom-prompt"/>
          <div className="text-[9px] text-gray-600 text-right">{customPrompt.length}/400</div>
        </div>

        {/* Screens picker */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-[10px] font-bold text-gray-400 uppercase">Pagine incluse ({selected.size}/{screens.length})</label>
            <div className="flex gap-1">
              <button onClick={() => setSelected(new Set(screens.map(s => s.key)))} disabled={running} className="text-[9px] text-gray-400 hover:text-white">tutti</button>
              <span className="text-gray-600 text-[9px]">·</span>
              <button onClick={() => setSelected(new Set())} disabled={running} className="text-[9px] text-gray-400 hover:text-white">nessuno</button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-1 max-h-48 overflow-y-auto pr-1">
            {screens.map(s => (
              <label key={s.key} className={`text-[10px] flex items-center gap-1.5 py-1.5 px-2 rounded-md border cursor-pointer ${selected.has(s.key) ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200' : 'bg-white/5 border-white/10 text-gray-400'}`}>
                <input type="checkbox" checked={selected.has(s.key)} onChange={() => toggleScreen(s.key)} disabled={running} className="w-3 h-3" />
                <span className="truncate">{s.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Start button */}
        <button onClick={startJob} disabled={running || loadingStart}
          className="w-full text-xs py-3 rounded-md bg-rose-500/20 border border-rose-500/40 text-rose-300 font-bold hover:bg-rose-500/30 disabled:opacity-50 flex items-center justify-center gap-2"
          data-testid="btn-generate-promo">
          {running ? <><Loader2 className="w-3.5 h-3.5 animate-spin"/>Generazione in corso…</> : <><Video className="w-3.5 h-3.5"/>Genera video promo</>}
        </button>

        {/* Progress / Log panel */}
        {currentJob && (
          <div className="bg-black/40 rounded-md border border-white/10 p-3 space-y-2" data-testid="promo-progress">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                <div className={`h-full transition-all duration-500 ${currentJob.status === 'failed' ? 'bg-red-500' : currentJob.status === 'completed' ? 'bg-emerald-500' : 'bg-rose-500'}`} style={{ width: `${currentJob.progress || 0}%` }} />
              </div>
              <span className="text-[10px] font-bold text-white">{currentJob.progress || 0}%</span>
            </div>
            <div className="text-[10px] text-gray-500">
              Stato: <span className="text-white font-semibold">{currentJob.stage}</span>
            </div>
            {(currentJob.log || []).slice(-8).map((line, i) => (
              <div key={i} className="text-[10px] text-gray-400 font-mono leading-tight">{line}</div>
            ))}
            {currentJob.status === 'completed' && (
              <button onClick={() => download(currentJob.job_id)}
                className="w-full text-[11px] py-2 mt-2 rounded-md bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold hover:bg-emerald-500/30 flex items-center justify-center gap-2"
                data-testid="btn-download-promo">
                <Download className="w-3.5 h-3.5"/>Scarica MP4
              </button>
            )}
          </div>
        )}

        {/* History */}
        {jobs.length > 0 && (
          <div>
            <div className="text-[10px] font-bold text-gray-400 uppercase mb-1">Storico ultimi video</div>
            <div className="space-y-1 max-h-56 overflow-y-auto">
              {jobs.map(j => (
                <div key={j.job_id} className="flex items-center gap-2 bg-white/5 rounded-md p-2 border border-white/5">
                  <div className="flex-1 min-w-0">
                    <div className="text-[10px] text-white font-semibold flex items-center gap-1.5">
                      <span className={`inline-block w-1.5 h-1.5 rounded-full ${j.status === 'completed' ? 'bg-emerald-400' : j.status === 'failed' ? 'bg-red-400' : 'bg-amber-400'}`}></span>
                      {j.params?.duration_seconds}s · {j.params?.screens?.length || '—'} pagine · {j.status}
                    </div>
                    <div className="text-[9px] text-gray-500 truncate">{j.created_at?.slice(0,16)?.replace('T',' ')} — {j.video_size ? `${Math.round(j.video_size/1024)} KB` : j.stage}</div>
                  </div>
                  {j.status === 'completed' && (
                    <button onClick={() => download(j.job_id)} className="text-[9px] px-2 py-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30" title="Scarica"><Download className="w-3 h-3"/></button>
                  )}
                  <button onClick={() => deleteJob(j.job_id)} className="text-[9px] px-2 py-1 rounded bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20" title="Elimina"><Trash2 className="w-3 h-3"/></button>
                </div>
              ))}
            </div>
          </div>
        )}

      </CardContent>
    </Card>
  );
}

/* ─── AI Providers Tab — Multi-provider rotation (CF + HF + Pollinations + Emergent) ─── */
function AIProvidersTab({ api }) {
  const [cfg, setCfg] = useState(null);
  const [usage, setUsage] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [test, setTest] = useState(null);
  const pollRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get('/admin/ai-providers');
      setCfg(r.data || {});
    } catch { toast.error('Impossibile caricare config AI'); }
    finally { setLoading(false); }
  }, [api]);

  const loadUsage = useCallback(async () => {
    try {
      const r = await api.get('/admin/ai-providers/usage');
      setUsage(r.data || {});
    } catch { /* noop */ }
  }, [api]);

  useEffect(() => { load(); loadUsage(); }, [load, loadUsage]);
  useEffect(() => {
    pollRef.current = setInterval(loadUsage, 10000);
    return () => clearInterval(pollRef.current);
  }, [loadUsage]);

  const save = async (patch) => {
    const next = { ...cfg, ...patch };
    setCfg(next); setSaving(true);
    try {
      const r = await api.post('/admin/ai-providers', next);
      setCfg(r.data?.config || next);
      toast.success('Configurazione aggiornata');
    } catch { toast.error('Salvataggio fallito'); }
    finally { setSaving(false); }
  };

  const runTest = async () => {
    setTesting(true); setTest(null);
    try {
      const r = await api.post('/admin/ai-providers/test');
      setTest(r.data);
    } catch { toast.error('Test fallito'); }
    finally { setTesting(false); }
  };

  if (loading || !cfg) {
    return <div className="flex items-center justify-center py-10 text-gray-500 text-xs"><Loader2 className="w-4 h-4 animate-spin mr-2"/>Caricamento…</div>;
  }

  const PROVIDER_META = {
    cloudflare: { label: 'Cloudflare SDXL', color: 'bg-orange-500/20 border-orange-500/40 text-orange-300' },
    huggingface_flux: { label: 'HF FLUX', color: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300' },
    huggingface_together: { label: 'HF·Together', color: 'bg-amber-500/20 border-amber-500/40 text-amber-300' },
    pixazo: { label: 'Pixazo FLUX (FREE)', color: 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300' },
    wavespeed: { label: 'WaveSpeed FLUX', color: 'bg-indigo-500/20 border-indigo-500/40 text-indigo-300' },
    pollinations: { label: 'Pollinations', color: 'bg-pink-500/20 border-pink-500/40 text-pink-300' },
    emergent: { label: 'Emergent', color: 'bg-purple-500/20 border-purple-500/40 text-purple-300' },
    auto: { label: '⚡ Auto (smart)', color: 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300' },
    auto_rr: { label: '🎲 Auto RR (bilanciato)', color: 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300' },
  };

  const PROVIDER_OPTIONS_POSTER = ['auto', 'cloudflare', 'huggingface_flux', 'huggingface_together', 'pixazo', 'wavespeed', 'pollinations', 'emergent'];
  const PROVIDER_OPTIONS_TRAILER = ['auto_rr', 'auto', 'cloudflare', 'huggingface_flux', 'huggingface_together', 'pixazo', 'wavespeed', 'pollinations', 'emergent'];

  const ProviderRow = ({ label, field, options }) => (
    <div className="space-y-1.5" data-testid={`ai-provider-row-${field}`}>
      <span className="text-xs text-gray-300 block">{label}</span>
      <div className="grid grid-cols-2 gap-1.5">
        {options.map(p => {
          const meta = PROVIDER_META[p] || { label: p, color: 'bg-white/5 border-white/10 text-gray-400' };
          const active = cfg[field] === p;
          return (
            <button key={p} onClick={() => save({ [field]: p })} disabled={saving}
              className={`text-[10px] px-2 py-2 rounded-md font-semibold border transition ${active ? meta.color : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'}`}
              data-testid={`btn-${field}-${p}`}>
              {meta.label}
            </button>
          );
        })}
      </div>
    </div>
  );

  return (
    <Card className="bg-[#111113] border-white/5" data-testid="ai-providers-tab">
      <CardHeader className="p-4 pb-2">
        <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-emerald-400" /> AI Image Providers
        </CardTitle>
        <p className="text-[10px] text-gray-500">Multi-provider rotation: Cloudflare SDXL + HuggingFace FLUX + Pixazo (FREE) + WaveSpeed FLUX + Pollinations + Emergent. Auto = smart fallback. Auto RR = round-robin bilanciato.</p>
      </CardHeader>
      <CardContent className="p-4 pt-2 space-y-3">
        <ProviderRow label="Locandine" field="poster_provider" options={PROVIDER_OPTIONS_POSTER} />
        <ProviderRow label="Trailer" field="trailer_provider" options={PROVIDER_OPTIONS_TRAILER} />

        {/* Usage tracker */}
        <div className="pt-2 border-t border-white/5" data-testid="usage-tracker">
          <div className="text-[10px] font-bold text-gray-400 uppercase mb-1">Quota giornaliera</div>
          <div className="space-y-1">
            {['cloudflare', 'huggingface_flux', 'huggingface_together', 'pixazo', 'wavespeed', 'pollinations'].map(p => {
              const u = usage[p] || { used: 0, limit: 0, remaining: 0 };
              const pct = u.limit > 0 ? Math.min(100, Math.round(u.used / u.limit * 100)) : 0;
              const meta = PROVIDER_META[p];
              return (
                <div key={p} className="flex items-center gap-2 text-[10px]">
                  <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-bold ${meta.color}`}>{meta.label}</span>
                  <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className={`h-full ${pct > 80 ? 'bg-red-500' : pct > 50 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-gray-400 tabular-nums min-w-14 text-right">{u.used}/{u.limit}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex items-start gap-2 pt-2 border-t border-white/5">
          <input id="fallback" type="checkbox" checked={!!cfg.fallback_on_error}
            onChange={e => save({ fallback_on_error: e.target.checked })}
            disabled={saving} className="w-4 h-4 mt-0.5" data-testid="toggle-fallback"/>
          <label htmlFor="fallback" className="text-xs text-gray-300 leading-tight">Fallback automatico su provider successivo in caso di errore</label>
        </div>

        <div className="text-[10px] text-gray-500 bg-white/5 rounded-md p-2 border border-white/5 leading-relaxed">
          <strong className="text-gray-300">Strategia raccomandata:</strong><br/>
          Locandine → <span className="text-emerald-300">Auto</span> (usa il migliore disponibile).<br/>
          Trailer → <span className="text-emerald-300">Auto RR</span> (bilancia il carico tra i 6 provider).<br/>
          Tutte le immagini convertite in <strong>WebP ≤1280px</strong> per mobile.
        </div>

        <div className="pt-2 border-t border-white/5">
          <button onClick={runTest} disabled={testing}
            className="w-full text-xs py-2 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-semibold hover:bg-emerald-500/25 disabled:opacity-50"
            data-testid="btn-test-providers">
            {testing ? <span className="inline-flex items-center gap-2"><Loader2 className="w-3 h-3 animate-spin"/>Test in corso…</span> : 'Test connettività tutti i provider'}
          </button>
          {test && (
            <div className="mt-3 space-y-1" data-testid="test-report">
              {Object.entries(test).map(([p, v]) => (
                <div key={p} className={`rounded-md border p-2 text-[10px] ${v?.ok ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{PROVIDER_META[p]?.label || p}</span>
                    <span className={v?.ok ? 'text-emerald-400' : 'text-red-400'}>{v?.ok ? `✅ ${v.latency_ms}ms` : '❌ FAIL'}</span>
                  </div>
                  <div className="text-gray-500 mt-0.5 break-all">{v?.details}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/* ─── Main Admin Page ─── */
export default function AdminPage() {
  const { api, user } = useContext(AuthContext);
  const isAdmin = user?.nickname === 'NeoMorpheus';
  const isCoadmin = user?.role === 'CO_ADMIN';
  const hasAccess = isAdmin || isCoadmin;
  const tabs = isAdmin ? ADMIN_TABS : COADMIN_TABS;
  const [activeTab, setActiveTab] = useState(tabs[0]?.id || 'reports');

  if (!hasAccess) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center p-4">
        <Card className="bg-[#111113] border-red-500/30 max-w-sm w-full">
          <CardContent className="p-6 text-center">
            <Shield className="w-10 h-10 mx-auto mb-3 text-red-500/50" />
            <p className="text-sm text-red-400 font-semibold">Accesso Negato</p>
            <p className="text-xs text-gray-500 mt-1">Permessi insufficienti per accedere a questa pagina.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0B] p-4 pb-24" data-testid="admin-page">
      <div className="max-w-[1600px] mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center gap-2.5 mb-1">
          <div className={`p-2 rounded-lg ${isAdmin ? 'bg-red-500/15' : 'bg-amber-500/15'}`}>
            <Shield className={`w-5 h-5 ${isAdmin ? 'text-red-400' : 'text-amber-400'}`} />
          </div>
          <div>
            <h1 className="text-lg font-black text-white tracking-tight">
              {isAdmin ? 'Pannello Admin' : 'Pannello Co-Admin'}
            </h1>
            <p className="text-[10px] text-gray-500">
              {isAdmin ? 'Controllo completo del sistema' : 'Segnalazioni e manutenzione'}
            </p>
          </div>
          <Badge className={`ml-auto text-[9px] h-5 ${isAdmin ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
            {isAdmin ? 'ADMIN' : 'CO_ADMIN'}
          </Badge>
        </div>

        {/* Tabs — scroll orizzontale su mobile */}
        <div className="flex gap-1 bg-[#111113] rounded-lg p-1 border border-white/5 overflow-x-auto no-scrollbar" data-testid="admin-tabs">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center justify-center gap-1.5 py-2.5 px-3 sm:px-4 rounded-md text-xs font-semibold transition-all whitespace-nowrap flex-shrink-0 min-w-[44px] sm:min-w-0 sm:flex-1 ${
                  isActive
                    ? (isAdmin ? 'bg-red-600 text-white' : 'bg-amber-600 text-white')
                    : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                }`}
                data-testid={`admin-tab-${tab.id}`}>
                <Icon className="w-4 h-4 sm:w-3.5 sm:h-3.5" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        {activeTab === 'users' && isAdmin && <UsersTab api={api} />}
        {activeTab === 'films' && isAdmin && <FilmsTab api={api} />}
        {activeTab === 'roles' && isAdmin && <RolesTab api={api} />}
        {activeTab === 'reports' && <ReportsTab api={api} />}
        {activeTab === 'deletions' && isAdmin && <DeletionsTab api={api} />}
        {activeTab === 'maintenance' && <MaintenanceTab api={api} />}
        {activeTab === 'donations' && isAdmin && <DonationsTab api={api} />}
        {activeTab === 'donations' && isAdmin && <GuestCleanupPanel api={api} />}
        {/* CityTastesAdmin temporarily disabled - investigating deploy issue */}
        {activeTab === 'maintenance' && isAdmin && <DbManagementCard api={api} isAdmin={isAdmin} />}
        {activeTab === 'maintenance' && isAdmin && (
          <Card className="bg-[#111113] border-white/5 mt-3"><CardContent className="p-3">
            <p className="text-xs font-bold text-orange-400 mb-2">Pulizia Eventi</p>
            <button onClick={async () => { if(window.confirm('Cancellare TUTTI gli eventi?')) { await api.post('/admin/recovery/clear-events'); toast.success('Eventi cancellati'); }}} className="w-full text-[10px] py-2 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400 font-bold">Cancella tutti gli eventi</button>
          </CardContent></Card>
        )}
        {activeTab === 'testlab' && isAdmin && <TestLabTab />}
        {activeTab === 'ai-providers' && isAdmin && <AIProvidersTab api={api} />}
        {activeTab === 'promo-video' && isAdmin && <PromoVideoTab api={api} />}
        {activeTab === 'recovery' && isAdmin && <AdminFilmRecovery />}
        {activeTab === 'reset' && isAdmin && <ResetGamePanel api={api} />}
        {activeTab === 'migration' && isAdmin && <MigrationTab api={api} />}
        {activeTab === 'tutorial' && isAdmin && <TutorialManagerTab api={api} />}
      </div>
    </div>
  );
}
