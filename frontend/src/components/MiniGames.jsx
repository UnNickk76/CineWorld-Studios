import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from './ui/button';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Zap, Target, Brain, Timer, MousePointerClick } from 'lucide-react';

/* ================================================================
   MINI-GAMES — Shared between ContestPage and TestLab
   Props: onFinish(score), testMode (optional)
   ================================================================ */

/* ─── TAP CIAK ─── */
export function TapCiak({ onFinish }) {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(8);
  const [items, setItems] = useState([]);
  const frameRef = useRef(null);
  const spawnRef = useRef(null);
  const finished = useRef(false);

  useEffect(() => {
    const iv = setInterval(() => {
      setTime(prev => {
        if (prev <= 1) {
          clearInterval(iv);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onFinish(score); } }, [time, score, onFinish]);

  // Spawn falling items
  useEffect(() => {
    let id = 0;
    const spawn = () => {
      const count = Math.floor(Math.random() * 3) + 1;
      const newItems = [];
      for (let i = 0; i < count; i++) {
        newItems.push({ id: id++, x: Math.random() * 85 + 5, y: -10, speed: Math.random() * 2 + 1.5, alive: true });
      }
      setItems(prev => [...prev, ...newItems]);
    };
    spawnRef.current = setInterval(spawn, 600);
    return () => clearInterval(spawnRef.current);
  }, []);

  // Animate items falling
  useEffect(() => {
    const loop = () => {
      setItems(prev => prev
        .map(it => ({ ...it, y: it.y + it.speed }))
        .filter(it => it.y < 110 && it.alive)
      );
      frameRef.current = requestAnimationFrame(loop);
    };
    frameRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frameRef.current);
  }, []);

  const tapItem = (itemId) => {
    setScore(s => s + 1);
    setItems(prev => prev.filter(it => it.id !== itemId));
  };

  return (
    <div className="relative w-full h-72 bg-gray-900/50 rounded-xl overflow-hidden select-none" data-testid="minigame-tapciak">
      <div className="absolute top-2 left-0 right-0 flex justify-between px-3 z-10">
        <span className="text-xs font-bold text-yellow-400 bg-black/50 px-2 py-0.5 rounded">{score} pt</span>
        <span className="text-xs font-bold text-white bg-black/50 px-2 py-0.5 rounded">{time}s</span>
      </div>
      <AnimatePresence>
        {items.filter(it => it.alive).map(it => (
          <motion.div
            key={it.id}
            className="absolute w-10 h-10 cursor-pointer flex items-center justify-center"
            style={{ left: `${it.x}%`, top: `${it.y}%` }}
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.5, opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={() => tapItem(it.id)}
          >
            <div className="w-9 h-9 rounded-lg bg-yellow-500/30 border border-yellow-500/60 flex items-center justify-center active:scale-75 transition-transform">
              <Play className="w-5 h-5 text-yellow-400" />
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
      <p className="absolute bottom-2 left-0 right-0 text-center text-[10px] text-gray-500">Tappa i ciak prima che cadano!</p>
    </div>
  );
}

/* ─── MEMORY PRO ─── */
const MEMORY_SYMBOLS = [
  'A','B','C','D','E','F','G','H','I','J',
  'K','L','M','N','O','P','Q','R','S','T'
];
const MEMORY_COLORS = {
  A:'bg-red-600',B:'bg-blue-600',C:'bg-green-600',D:'bg-purple-600',E:'bg-yellow-600',
  F:'bg-cyan-600',G:'bg-pink-600',H:'bg-orange-600',I:'bg-teal-600',J:'bg-indigo-600',
  K:'bg-rose-600',L:'bg-lime-600',M:'bg-sky-600',N:'bg-violet-600',O:'bg-amber-600',
  P:'bg-emerald-600',Q:'bg-fuchsia-600',R:'bg-red-500',S:'bg-blue-500',T:'bg-green-500',
};

export function MemoryPro({ onFinish }) {
  const pairs = 20;
  const symbols = MEMORY_SYMBOLS.slice(0, pairs);
  const [cards] = useState(() => [...symbols, ...symbols].sort(() => Math.random() - 0.5));
  const [open, setOpen] = useState([]);
  const [matched, setMatched] = useState(new Set());
  const [combo, setCombo] = useState(0);
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(45);
  const checking = useRef(false);
  const finished = useRef(false);

  useEffect(() => {
    const iv = setInterval(() => {
      setTime(prev => {
        if (prev <= 1) { clearInterval(iv); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    if (time === 0 && !finished.current) { finished.current = true; onFinish(score); }
  }, [time, score, onFinish]);

  useEffect(() => {
    if (matched.size === pairs && !finished.current) { finished.current = true; onFinish(score + time * 2); }
  }, [matched, score, time, pairs, onFinish]);

  const click = (i) => {
    if (checking.current || open.includes(i) || matched.has(cards[i])) return;
    const next = [...open, i];
    setOpen(next);
    if (next.length === 2) {
      checking.current = true;
      if (cards[next[0]] === cards[next[1]]) {
        const newCombo = combo + 1;
        setCombo(newCombo);
        const bonus = newCombo > 1 ? newCombo * 2 : 0;
        setScore(s => s + 5 + bonus);
        setMatched(prev => new Set([...prev, cards[next[0]]]));
        setTimeout(() => { setOpen([]); checking.current = false; }, 300);
      } else {
        setCombo(0);
        setTimeout(() => { setOpen([]); checking.current = false; }, 500);
      }
    }
  };

  return (
    <div className="space-y-2" data-testid="minigame-memory">
      <div className="flex justify-between text-xs px-1">
        <span className="text-green-400 font-bold">{score} pt</span>
        {combo > 1 && <span className="text-yellow-400 font-bold animate-pulse">x{combo} COMBO!</span>}
        <span className="text-white font-bold">{time}s</span>
      </div>
      <div className="grid grid-cols-8 gap-0.5">
        {cards.map((c, i) => {
          const revealed = open.includes(i) || matched.has(c);
          return (
            <motion.div
              key={i}
              onClick={() => click(i)}
              className={`aspect-square flex items-center justify-center rounded text-[9px] font-bold cursor-pointer select-none transition-colors ${
                matched.has(c) ? 'bg-green-800/40 text-green-300' :
                revealed ? (MEMORY_COLORS[c] || 'bg-cyan-600') + ' text-white' :
                'bg-gray-700 hover:bg-gray-600 text-gray-700'
              }`}
              whileTap={{ scale: 0.85 }}
              data-testid={`mem-card-${i}`}
            >
              {revealed ? c : '?'}
            </motion.div>
          );
        })}
      </div>
      <p className="text-center text-[10px] text-gray-500">{matched.size}/{pairs} coppie</p>
    </div>
  );
}

/* ─── STOP PERFETTO ─── */
export function StopPerfetto({ onFinish }) {
  const [pos, setPos] = useState(0);
  const [stopped, setStopped] = useState(false);
  const [finalScore, setFinalScore] = useState(null);
  const dirRef = useRef(1);
  const posRef = useRef(0);
  const rafRef = useRef(null);
  const finished = useRef(false);

  useEffect(() => {
    let last = performance.now();
    const loop = (now) => {
      const dt = (now - last) / 1000;
      last = now;
      posRef.current += dirRef.current * 150 * dt;
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
    const s = Math.max(0, Math.round(100 - Math.abs(50 - posRef.current) * 2.5));
    setFinalScore(s);
    if (!finished.current) { finished.current = true; setTimeout(() => onFinish(s), 800); }
  };

  return (
    <div className="space-y-4" data-testid="minigame-timing">
      <p className="text-xs text-gray-400 text-center">Ferma il cursore nella zona verde!</p>
      <div className="h-8 bg-gray-800 rounded-full relative overflow-hidden border border-gray-700">
        <div className="absolute bg-green-500/30 h-full" style={{ left: '45%', width: '10%' }} />
        <motion.div
          className="absolute bg-red-500 h-full rounded-full shadow-[0_0_8px_rgba(239,68,68,0.6)]"
          style={{ left: `${pos}%`, width: '2.5%' }}
        />
      </div>
      {finalScore !== null ? (
        <div className="text-center">
          <p className={`text-2xl font-black ${finalScore > 80 ? 'text-green-400' : finalScore > 40 ? 'text-yellow-400' : 'text-red-400'}`}>{finalScore} pt</p>
          <p className="text-[10px] text-gray-500">{finalScore > 80 ? 'Perfetto!' : finalScore > 40 ? 'Buono!' : 'Riprova!'}</p>
        </div>
      ) : (
        <Button onClick={stop} className="w-full bg-blue-600 hover:bg-blue-700 h-14 text-xl font-black" data-testid="timing-stop-btn">
          STOP!
        </Button>
      )}
    </div>
  );
}

/* ─── SPAM CLICK ─── */
export function SpamClick({ onFinish }) {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(4);
  const [pulse, setPulse] = useState(false);
  const finished = useRef(false);

  useEffect(() => {
    const iv = setInterval(() => {
      setTime(prev => {
        if (prev <= 1) { clearInterval(iv); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onFinish(score); } }, [time, score, onFinish]);

  const tap = () => {
    setScore(s => s + 2);
    setPulse(true);
    setTimeout(() => setPulse(false), 80);
  };

  return (
    <div className="text-center space-y-3" data-testid="minigame-spamclick">
      <div className="flex justify-between px-2">
        <span className="text-lg font-black text-red-400">{score} pt</span>
        <span className="text-lg font-black text-white">{time}s</span>
      </div>
      <p className="text-xs text-gray-400">Tappa il piu veloce possibile!</p>
      <motion.button
        className={`w-full h-28 rounded-2xl border-2 border-red-500 text-red-400 text-3xl font-black select-none transition-colors ${pulse ? 'bg-red-500/40' : 'bg-red-500/15'}`}
        whileTap={{ scale: 0.92 }}
        onClick={tap}
        data-testid="spam-btn"
      >
        <Zap className="w-10 h-10 mx-auto mb-1" />
        TAP!
      </motion.button>
    </div>
  );
}

/* ─── REACTION GAME (NEW) ─── */
export function ReactionGame({ onFinish }) {
  const [phase, setPhase] = useState('wait');
  const [startTime, setStartTime] = useState(0);
  const [reactions, setReactions] = useState([]);
  const [round, setRound] = useState(0);
  const totalRounds = 3;
  const timeoutRef = useRef(null);
  const finished = useRef(false);

  const startRound = useCallback(() => {
    setPhase('wait');
    const delay = 1500 + Math.random() * 3000;
    timeoutRef.current = setTimeout(() => {
      setStartTime(performance.now());
      setPhase('go');
    }, delay);
  }, []);

  useEffect(() => { startRound(); return () => clearTimeout(timeoutRef.current); }, []);

  const handleClick = () => {
    if (phase === 'wait') {
      clearTimeout(timeoutRef.current);
      setPhase('early');
      setTimeout(() => startRound(), 1000);
      return;
    }
    if (phase !== 'go') return;
    const ms = Math.round(performance.now() - startTime);
    const newReactions = [...reactions, ms];
    setReactions(newReactions);
    setPhase('result');
    const newRound = round + 1;
    setRound(newRound);
    if (newRound >= totalRounds) {
      const avg = newReactions.reduce((a, b) => a + b, 0) / newReactions.length;
      const score = Math.max(0, Math.round(100 - avg / 5));
      if (!finished.current) { finished.current = true; setTimeout(() => onFinish(score), 1000); }
    } else {
      setTimeout(() => startRound(), 1200);
    }
  };

  return (
    <div className="space-y-3" data-testid="minigame-reaction">
      <div className="flex justify-between text-xs px-1">
        <span className="text-gray-400">Round {Math.min(round + 1, totalRounds)}/{totalRounds}</span>
        {reactions.length > 0 && <span className="text-cyan-400">Media: {Math.round(reactions.reduce((a,b)=>a+b,0)/reactions.length)}ms</span>}
      </div>
      <motion.div
        className={`w-full h-44 rounded-2xl flex flex-col items-center justify-center cursor-pointer select-none border-2 transition-colors ${
          phase === 'wait' ? 'bg-red-900/30 border-red-500/30' :
          phase === 'go' ? 'bg-green-500/30 border-green-500' :
          phase === 'early' ? 'bg-yellow-500/20 border-yellow-500/40' :
          'bg-gray-800 border-gray-700'
        }`}
        onClick={handleClick}
        whileTap={{ scale: 0.97 }}
      >
        {phase === 'wait' && <>
          <Timer className="w-10 h-10 text-red-400 mb-2" />
          <p className="text-sm text-red-400 font-bold">Aspetta...</p>
        </>}
        {phase === 'go' && <>
          <Target className="w-12 h-12 text-green-400 mb-2 animate-pulse" />
          <p className="text-lg text-green-400 font-black">ORA! TAPPA!</p>
        </>}
        {phase === 'early' && <p className="text-sm text-yellow-400 font-bold">Troppo presto!</p>}
        {phase === 'result' && <>
          <p className="text-3xl font-black text-cyan-400">{reactions[reactions.length - 1]}ms</p>
          <p className="text-[10px] text-gray-400 mt-1">{reactions[reactions.length-1] < 250 ? 'Velocissimo!' : reactions[reactions.length-1] < 400 ? 'Buono!' : 'Puoi fare meglio!'}</p>
        </>}
      </motion.div>
    </div>
  );
}

/* ─── QUIZ ─── */
export function QuizGame({ onFinish }) {
  const questions = [
    { q: 'Regista di Titanic?', options: ['Spielberg', 'Cameron', 'Nolan', 'Scott'], a: 'Cameron' },
    { q: 'Genere di Joker?', options: ['Azione', 'Commedia', 'Dramma', 'Horror'], a: 'Dramma' },
    { q: 'Chi ha diretto Pulp Fiction?', options: ['Coppola', 'Scorsese', 'Tarantino', 'Lynch'], a: 'Tarantino' },
  ];
  const [qi, setQi] = useState(0);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);
  const [selected, setSelected] = useState(null);
  const finished = useRef(false);

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
        if (!finished.current) { finished.current = true; onFinish(correct ? newScore : score); }
      }
    }, 600);
  };

  return (
    <div className="space-y-3" data-testid="minigame-quiz">
      <div className="flex justify-between text-xs px-1">
        <span className="text-gray-400">Domanda {qi + 1}/{questions.length}</span>
        <span className="text-green-400 font-bold">{score} pt</span>
      </div>
      <p className="text-sm font-bold text-center">{questions[qi].q}</p>
      <div className="space-y-1.5">
        {questions[qi].options.map(opt => (
          <Button key={opt} variant="outline" disabled={answered}
            className={`w-full border-gray-700 text-sm h-10 justify-start ${
              answered && opt === questions[qi].a ? 'bg-green-500/20 border-green-500 text-green-400' :
              answered && opt === selected && opt !== questions[qi].a ? 'bg-red-500/20 border-red-500 text-red-400' : ''
            }`}
            onClick={() => answer(opt)} data-testid={`quiz-opt-${opt}`}>
            {opt}
          </Button>
        ))}
      </div>
    </div>
  );
}
