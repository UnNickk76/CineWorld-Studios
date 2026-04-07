import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import { Trophy, Play, Lock, Check, Clock, Zap, Target, Brain, MousePointerClick, HelpCircle } from 'lucide-react';

const STEP_NAMES = [
  'TapCiak', 'Memory', 'Timing', 'SpamClick', 'Quiz',
  'TapCiak II', 'Timing II', 'Memory II', 'SpamClick II', 'Quiz II', 'BONUS'
];
const STEP_ICONS = [
  MousePointerClick, Brain, Target, Zap, HelpCircle,
  MousePointerClick, Target, Brain, Zap, HelpCircle, Trophy
];

/* ======================== MINI-GAMES ======================== */

function TapCiak({ onFinish }) {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(15);
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setTime(prev => {
        if (prev <= 1) { clearInterval(timerRef.current); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  useEffect(() => { if (time === 0) onFinish(score); }, [time]);

  return (
    <div className="text-center space-y-4" data-testid="minigame-tapciak">
      <p className="text-3xl font-bold text-yellow-400">{time}s</p>
      <p className="text-xs text-gray-400">Tappa il ciak il piu veloce possibile!</p>
      <button
        className="w-28 h-28 mx-auto rounded-full bg-yellow-500/20 border-2 border-yellow-500 flex items-center justify-center active:scale-90 transition-transform"
        onClick={() => setScore(s => s + 1)}
        data-testid="tap-btn"
      >
        <Play className="w-12 h-12 text-yellow-400" />
      </button>
      <p className="text-lg font-bold">{score} tap</p>
    </div>
  );
}

function MemoryGame({ onFinish }) {
  const base = ['A', 'B', 'C', 'D'];
  const [cards] = useState(() => [...base, ...base].sort(() => 0.5 - Math.random()));
  const [open, setOpen] = useState([]);
  const [matched, setMatched] = useState([]);
  const checking = useRef(false);

  useEffect(() => {
    if (matched.length === base.length) onFinish(50);
  }, [matched]);

  const click = (i) => {
    if (checking.current || open.includes(i) || matched.includes(cards[i])) return;
    const next = [...open, i];
    setOpen(next);
    if (next.length === 2) {
      checking.current = true;
      if (cards[next[0]] === cards[next[1]]) {
        setMatched(prev => [...prev, cards[next[0]]]);
      }
      setTimeout(() => { setOpen([]); checking.current = false; }, 600);
    }
  };

  const COLORS = { A: 'bg-cyan-600', B: 'bg-purple-600', C: 'bg-green-600', D: 'bg-orange-600' };

  return (
    <div className="space-y-3" data-testid="minigame-memory">
      <p className="text-xs text-gray-400 text-center">Trova le coppie!</p>
      <div className="grid grid-cols-4 gap-2">
        {cards.map((c, i) => {
          const revealed = open.includes(i) || matched.includes(c);
          return (
            <div
              key={i}
              onClick={() => click(i)}
              className={`h-16 flex items-center justify-center rounded-lg text-lg font-bold cursor-pointer transition-all ${revealed ? COLORS[c] + ' text-white scale-95' : 'bg-gray-700 hover:bg-gray-600'}`}
              data-testid={`mem-card-${i}`}
            >
              {revealed ? c : <HelpCircle className="w-5 h-5 text-gray-500" />}
            </div>
          );
        })}
      </div>
      <p className="text-center text-xs text-gray-500">{matched.length}/{base.length} trovate</p>
    </div>
  );
}

function TimingGame({ onFinish }) {
  const [pos, setPos] = useState(0);
  const [stopped, setStopped] = useState(false);
  const dirRef = useRef(1);
  const posRef = useRef(0);
  const rafRef = useRef(null);

  useEffect(() => {
    let last = performance.now();
    const loop = (now) => {
      const dt = (now - last) / 1000;
      last = now;
      posRef.current += dirRef.current * 80 * dt;
      if (posRef.current >= 100) { posRef.current = 100; dirRef.current = -1; }
      if (posRef.current <= 0) { posRef.current = 0; dirRef.current = 1; }
      setPos(posRef.current);
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  const stop = () => {
    if (stopped) return;
    setStopped(true);
    cancelAnimationFrame(rafRef.current);
    const score = Math.max(0, 100 - Math.abs(50 - posRef.current) * 2);
    setTimeout(() => onFinish(Math.round(score)), 500);
  };

  return (
    <div className="space-y-4" data-testid="minigame-timing">
      <p className="text-xs text-gray-400 text-center">Ferma il cursore nella zona verde!</p>
      <div className="h-6 bg-gray-700 rounded-full relative overflow-hidden">
        <div className="absolute bg-green-500/40 h-full rounded" style={{ left: '40%', width: '20%' }} />
        <div className="absolute bg-red-500 h-full rounded-full transition-none" style={{ left: `${pos}%`, width: '3%' }} />
      </div>
      <Button onClick={stop} disabled={stopped} className="w-full bg-blue-600 hover:bg-blue-700 h-12 text-lg font-bold" data-testid="timing-stop-btn">
        {stopped ? `Score: ${Math.round(Math.max(0, 100 - Math.abs(50 - pos) * 2))}` : 'STOP!'}
      </Button>
    </div>
  );
}

function SpamClick({ onFinish }) {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(10);
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setTime(prev => {
        if (prev <= 1) { clearInterval(timerRef.current); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  useEffect(() => { if (time === 0) onFinish(score); }, [time]);

  return (
    <div className="text-center space-y-4" data-testid="minigame-spamclick">
      <p className="text-3xl font-bold text-red-400">{time}s</p>
      <p className="text-xs text-gray-400">Tappa piu volte che puoi!</p>
      <button
        className="w-full h-24 rounded-xl bg-red-500/20 border-2 border-red-500 text-red-400 text-2xl font-bold active:scale-95 transition-transform"
        onClick={() => setScore(s => s + 2)}
        data-testid="spam-btn"
      >
        <Zap className="w-8 h-8 mx-auto" /> TAP!
      </button>
      <p className="text-lg font-bold">{score} punti</p>
    </div>
  );
}

function QuizGame({ onFinish }) {
  const questions = [
    { q: 'Regista di Titanic?', options: ['Spielberg', 'Cameron', 'Nolan', 'Scott'], a: 'Cameron' },
    { q: 'Genere di Joker?', options: ['Azione', 'Commedia', 'Dramma', 'Horror'], a: 'Dramma' },
  ];
  const [qi, setQi] = useState(0);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);
  const [selected, setSelected] = useState(null);

  const answer = (v) => {
    if (answered) return;
    setAnswered(true);
    setSelected(v);
    const correct = v === questions[qi].a;
    const newScore = score + (correct ? 25 : 0);
    if (correct) setScore(newScore);
    setTimeout(() => {
      if (qi + 1 < questions.length) {
        setQi(qi + 1);
        setAnswered(false);
        setSelected(null);
      } else {
        onFinish(newScore);
      }
    }, 700);
  };

  return (
    <div className="space-y-4" data-testid="minigame-quiz">
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>Domanda {qi + 1}/{questions.length}</span>
        <span className="text-green-400">{score} pt</span>
      </div>
      <p className="text-sm font-semibold text-center">{questions[qi].q}</p>
      <div className="space-y-2">
        {questions[qi].options.map(opt => (
          <Button
            key={opt}
            variant="outline"
            disabled={answered}
            className={`w-full border-gray-700 text-sm h-10 justify-start ${
              answered && opt === questions[qi].a ? 'bg-green-500/20 border-green-500 text-green-400' :
              answered && opt === selected && opt !== questions[qi].a ? 'bg-red-500/20 border-red-500 text-red-400' : ''
            }`}
            onClick={() => answer(opt)}
            data-testid={`quiz-opt-${opt}`}
          >
            {opt}
          </Button>
        ))}
      </div>
    </div>
  );
}

/* ======================== MAIN PAGE ======================== */

const GAME_FOR_STEP = [TapCiak, MemoryGame, TimingGame, SpamClick, QuizGame, TapCiak, TimingGame, MemoryGame, SpamClick, QuizGame, null];

export default function ContestPage() {
  const { api, user } = useContext(AuthContext);
  const [progress, setProgress] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadProgress = useCallback(async () => {
    try {
      const res = await api.get('/contest/progress');
      setProgress(res.data);
    } catch { toast.error('Errore caricamento contest'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadProgress(); }, [loadProgress]);

  const finishStep = async (score) => {
    setPlaying(false);
    try {
      const res = await api.post('/contest/complete-step', { score });
      toast.success(`+${res.data.credits} crediti!`);
      loadProgress();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
      loadProgress();
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-400">Caricamento...</div>;

  const currentStep = progress?.current_step || 1;
  const completed = progress?.completed || false;
  const locked = progress?.next_unlock_at && new Date(progress.next_unlock_at) > new Date();

  if (playing) {
    const GameComponent = GAME_FOR_STEP[(currentStep - 1)] || null;
    if (!GameComponent) { setPlaying(false); return null; }
    return (
      <div className="max-w-sm mx-auto px-3 pt-4 pb-32" data-testid="contest-playing">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs text-gray-400">Step {currentStep}/11</p>
          <Button variant="ghost" size="sm" className="text-xs text-gray-500" onClick={() => setPlaying(false)}>Esci</Button>
        </div>
        <Card className="bg-[#1A1A1B] border-gray-800">
          <CardContent className="p-4">
            <h3 className="text-sm font-bold mb-3 text-center">{STEP_NAMES[currentStep - 1]}</h3>
            <GameComponent onFinish={finishStep} />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto px-3 pt-2 pb-32 space-y-3" data-testid="contest-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <Trophy className="w-5 h-5 text-yellow-400" /> Contest
        </h2>
        <p className="text-xs text-gray-500">Max {20} crediti/giorno</p>
      </div>

      <Progress value={completed ? 100 : ((currentStep - 1) / 11) * 100} className="h-1.5" />

      {/* Steps */}
      {STEP_NAMES.map((name, i) => {
        const stepNum = i + 1;
        const Icon = STEP_ICONS[i];
        const done = stepNum < currentStep;
        const isCurrent = stepNum === currentStep && !completed;
        const isLocked = stepNum > currentStep || (isCurrent && locked);
        return (
          <Card key={i} className={`bg-[#1A1A1B] border-gray-800 ${isLocked && !done ? 'opacity-40' : ''}`} data-testid={`step-card-${stepNum}`}>
            <CardContent className="p-3 flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${done ? 'bg-green-500/20' : isCurrent && !locked ? 'bg-cyan-500/20' : 'bg-gray-800'}`}>
                {done ? <Check className="w-5 h-5 text-green-400" /> : isLocked ? <Lock className="w-5 h-5 text-gray-600" /> : <Icon className="w-5 h-5 text-cyan-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold">{name}</p>
                <p className="text-[10px] text-gray-500">
                  {done ? 'Completato' : isCurrent && locked ? 'Sblocco tra poco...' : isCurrent ? 'Disponibile' : 'Bloccato'}
                </p>
              </div>
              {isCurrent && !locked && (
                <Button size="sm" className="bg-cyan-700 hover:bg-cyan-800 text-xs h-8 shrink-0" onClick={() => setPlaying(true)} data-testid={`play-step-${stepNum}`}>
                  <Play className="w-3 h-3 mr-1" /> Gioca
                </Button>
              )}
            </CardContent>
          </Card>
        );
      })}

      {completed && (
        <div className="text-center py-4 text-green-400 font-bold text-sm" data-testid="contest-all-done">
          Tutti gli step completati! Torna domani.
        </div>
      )}
    </div>
  );
}
