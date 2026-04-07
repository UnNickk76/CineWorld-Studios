import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from './ui/button';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Zap, Target, Timer, Film, Camera, Star, Award, Heart, Music2, Sparkles, Eye, Flame, Crown, Trophy, Video, Tv, Bookmark, Gift, Sun, Bomb, Scissors, SlidersHorizontal, UserCheck, Crosshair } from 'lucide-react';

/* ================================================================
   MINI-GAMES — 12 giochi condivisi tra Contest, Solo, 1vs1, TestLab
   Props: onFinish(score)
   ================================================================ */

/* ─── 1. TAP CIAK — Ciak cadenti fullscreen ─── */
export function TapCiak({ onFinish }) {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(8);
  const [items, setItems] = useState([]);
  const frameRef = useRef(null);
  const spawnRef = useRef(null);
  const finished = useRef(false);
  const idCounter = useRef(0);

  useEffect(() => {
    const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onFinish(score); } }, [time, score, onFinish]);

  useEffect(() => {
    const spawn = () => {
      const count = Math.floor(Math.random() * 4) + 1;
      const batch = [];
      for (let i = 0; i < count; i++) {
        batch.push({ id: idCounter.current++, x: Math.random() * 80 + 5, y: -8, speed: 1.2 + Math.random() * 2.5, alive: true });
      }
      setItems(prev => [...prev, ...batch]);
    };
    spawnRef.current = setInterval(spawn, 500);
    return () => clearInterval(spawnRef.current);
  }, []);

  useEffect(() => {
    const loop = () => {
      setItems(prev => prev.map(it => ({ ...it, y: it.y + it.speed })).filter(it => it.y < 105 && it.alive));
      frameRef.current = requestAnimationFrame(loop);
    };
    frameRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frameRef.current);
  }, []);

  const tap = (id) => { setScore(s => s + 1); setItems(prev => prev.filter(it => it.id !== id)); };

  return (
    <div className="relative w-full h-80 bg-gray-900/60 rounded-xl overflow-hidden select-none touch-none" data-testid="minigame-tapciak">
      <div className="absolute top-2 left-0 right-0 flex justify-between px-3 z-20 pointer-events-none">
        <span className="text-sm font-black text-yellow-400 bg-black/60 px-2 py-0.5 rounded">{score}</span>
        <span className="text-sm font-black text-white bg-black/60 px-2 py-0.5 rounded">{time}s</span>
      </div>
      {items.map(it => (
        <div key={it.id} className="absolute z-10 cursor-pointer" style={{ left: `${it.x}%`, top: `${it.y}%`, touchAction: 'none', pointerEvents: 'auto' }}
          onPointerDown={(e) => { e.preventDefault(); e.stopPropagation(); tap(it.id); }}>
          <div className="w-11 h-11 rounded-lg bg-yellow-500/30 border-2 border-yellow-500/70 flex items-center justify-center active:scale-75 transition-transform">
            <Film className="w-6 h-6 text-yellow-400 pointer-events-none" />
          </div>
        </div>
      ))}
      <p className="absolute bottom-2 left-0 right-0 text-center text-[10px] text-gray-500 pointer-events-none">Tappa i ciak!</p>
    </div>
  );
}

/* ─── 2. MEMORY PRO — 40 carte con icone cinema ─── */
const MEM_ICONS = [Film, Camera, Star, Award, Heart, Music2, Sparkles, Eye, Flame, Crown, Trophy, Video, Tv, Bookmark, Gift, Sun, Play, Zap, Target, Timer];
const MEM_COLORS = ['bg-red-600','bg-blue-600','bg-green-600','bg-purple-600','bg-yellow-600','bg-cyan-600','bg-pink-600','bg-orange-600','bg-teal-600','bg-indigo-600','bg-rose-600','bg-lime-600','bg-sky-600','bg-violet-600','bg-amber-600','bg-emerald-600','bg-fuchsia-600','bg-red-500','bg-blue-500','bg-green-500'];

export function MemoryPro({ onFinish }) {
  const pairs = 20;
  const [cards] = useState(() => {
    const deck = [];
    for (let i = 0; i < pairs; i++) deck.push(i, i);
    return deck.sort(() => Math.random() - 0.5);
  });
  const [open, setOpen] = useState([]);
  const [matched, setMatched] = useState(new Set());
  const [combo, setCombo] = useState(0);
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(60);
  const checking = useRef(false);
  const finished = useRef(false);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onFinish(score); } }, [time, score, onFinish]);
  useEffect(() => { if (matched.size === pairs && !finished.current) { finished.current = true; onFinish(score + time * 3); } }, [matched, score, time, pairs, onFinish]);

  const click = (i) => {
    if (checking.current || open.includes(i) || matched.has(cards[i])) return;
    const next = [...open, i];
    setOpen(next);
    if (next.length === 2) {
      checking.current = true;
      if (cards[next[0]] === cards[next[1]]) {
        const nc = combo + 1;
        setCombo(nc);
        setScore(s => s + 5 + (nc > 1 ? nc * 2 : 0));
        setMatched(prev => new Set([...prev, cards[next[0]]]));
        setTimeout(() => { setOpen([]); checking.current = false; }, 250);
      } else {
        setCombo(0);
        setTimeout(() => { setOpen([]); checking.current = false; }, 400);
      }
    }
  };

  return (
    <div className="space-y-1.5" data-testid="minigame-memory">
      <div className="flex justify-between text-xs px-0.5">
        <span className="text-green-400 font-bold">{score} pt</span>
        {combo > 1 && <span className="text-yellow-400 font-bold animate-pulse">x{combo}</span>}
        <span className="text-white font-bold">{time}s</span>
      </div>
      <div className="grid grid-cols-8 gap-[3px]">
        {cards.map((c, i) => {
          const revealed = open.includes(i) || matched.has(c);
          const Icon = MEM_ICONS[c];
          return (
            <div key={i} onClick={() => click(i)}
              className={`aspect-square flex items-center justify-center rounded cursor-pointer select-none transition-all duration-150 ${
                matched.has(c) ? 'bg-green-800/30 scale-90' : revealed ? MEM_COLORS[c] + ' scale-95' : 'bg-gray-700 hover:bg-gray-600 active:scale-90'
              }`} data-testid={`mem-${i}`}>
              {revealed ? <Icon className="w-3 h-3 text-white" /> : <span className="text-gray-600 text-[8px]">?</span>}
            </div>
          );
        })}
      </div>
      <p className="text-center text-[10px] text-gray-500">{matched.size}/{pairs}</p>
    </div>
  );
}

/* ─── 3. STOP PERFETTO ─── */
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
      const dt = (now - last) / 1000; last = now;
      posRef.current += dirRef.current * 200 * dt;
      if (posRef.current >= 100) { posRef.current = 100; dirRef.current = -1; }
      if (posRef.current <= 0) { posRef.current = 0; dirRef.current = 1; }
      setPos(posRef.current);
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  const stop = () => {
    if (stopped) return; setStopped(true); cancelAnimationFrame(rafRef.current);
    const s = Math.max(0, Math.round(100 - Math.abs(50 - posRef.current) * 3));
    setFinalScore(s);
    if (!finished.current) { finished.current = true; setTimeout(() => onFinish(s), 600); }
  };

  return (
    <div className="space-y-4" data-testid="minigame-timing">
      <p className="text-xs text-gray-400 text-center">Ferma nella zona verde!</p>
      <div className="h-8 bg-gray-800 rounded-full relative overflow-hidden border border-gray-700">
        <div className="absolute bg-green-500/30 h-full" style={{ left: '46%', width: '8%' }} />
        <div className="absolute bg-red-500 h-full rounded-full shadow-[0_0_10px_rgba(239,68,68,0.7)]" style={{ left: `${pos}%`, width: '2%' }} />
      </div>
      {finalScore !== null ? (
        <div className="text-center"><p className={`text-3xl font-black ${finalScore > 80 ? 'text-green-400' : finalScore > 40 ? 'text-yellow-400' : 'text-red-400'}`}>{finalScore}</p></div>
      ) : (
        <Button onClick={stop} className="w-full bg-blue-600 hover:bg-blue-700 h-14 text-xl font-black" data-testid="timing-stop-btn">STOP!</Button>
      )}
    </div>
  );
}

/* ─── 4. SPAM CLICK ─── */
export function SpamClick({ onFinish }) {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(4);
  const [flash, setFlash] = useState(0);
  const finished = useRef(false);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onFinish(score); } }, [time, score, onFinish]);

  const tap = () => { setScore(s => s + 2); setFlash(f => f + 1); };

  return (
    <div className="text-center space-y-3" data-testid="minigame-spamclick">
      <div className="flex justify-between px-2"><span className="text-lg font-black text-red-400">{score}</span><span className="text-lg font-black text-white">{time}s</span></div>
      <motion.button className="w-full h-28 rounded-2xl border-2 border-red-500 text-red-400 text-3xl font-black select-none bg-red-500/15 active:bg-red-500/40"
        animate={{ scale: flash ? [1, 0.92, 1] : 1 }} key={flash} transition={{ duration: 0.08 }}
        onPointerDown={tap} data-testid="spam-btn"><Zap className="w-10 h-10 mx-auto mb-1" />TAP!</motion.button>
    </div>
  );
}

/* ─── 5. REACTION GAME ─── */
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
    timeoutRef.current = setTimeout(() => { setStartTime(performance.now()); setPhase('go'); }, 1500 + Math.random() * 3000);
  }, []);

  useEffect(() => { startRound(); return () => clearTimeout(timeoutRef.current); }, [startRound]);

  const handleClick = () => {
    if (phase === 'wait') { clearTimeout(timeoutRef.current); setPhase('early'); setTimeout(startRound, 800); return; }
    if (phase !== 'go') return;
    const ms = Math.round(performance.now() - startTime);
    const nr = [...reactions, ms]; setReactions(nr); setPhase('result'); const newRound = round + 1; setRound(newRound);
    if (newRound >= totalRounds) {
      const avg = nr.reduce((a, b) => a + b, 0) / nr.length;
      if (!finished.current) { finished.current = true; setTimeout(() => onFinish(Math.max(0, Math.round(100 - avg / 5))), 800); }
    } else { setTimeout(startRound, 1000); }
  };

  return (
    <div className="space-y-3" data-testid="minigame-reaction">
      <div className="flex justify-between text-xs px-1">
        <span className="text-gray-400">Round {Math.min(round + 1, totalRounds)}/{totalRounds}</span>
        {reactions.length > 0 && <span className="text-cyan-400">{Math.round(reactions.reduce((a,b)=>a+b,0)/reactions.length)}ms</span>}
      </div>
      <div className={`w-full h-40 rounded-2xl flex flex-col items-center justify-center cursor-pointer select-none border-2 ${
        phase === 'wait' ? 'bg-red-900/30 border-red-500/30' : phase === 'go' ? 'bg-green-500/30 border-green-500' : phase === 'early' ? 'bg-yellow-500/20 border-yellow-500/40' : 'bg-gray-800 border-gray-700'
      }`} onPointerDown={handleClick}>
        {phase === 'wait' && <><Timer className="w-8 h-8 text-red-400 mb-1" /><p className="text-sm text-red-400 font-bold">Aspetta...</p></>}
        {phase === 'go' && <><Target className="w-10 h-10 text-green-400 mb-1 animate-pulse" /><p className="text-lg text-green-400 font-black">TAPPA!</p></>}
        {phase === 'early' && <p className="text-sm text-yellow-400 font-bold">Troppo presto!</p>}
        {phase === 'result' && <p className="text-2xl font-black text-cyan-400">{reactions[reactions.length - 1]}ms</p>}
      </div>
    </div>
  );
}

/* ─── 6. SHOT PERFECT — Centra il soggetto ─── */
export function ShotPerfect({ onFinish }) {
  const [pos, setPos] = useState({ x: 50, y: 50 });
  const [shots, setShots] = useState([]);
  const [round, setRound] = useState(0);
  const totalRounds = 5;
  const rafRef = useRef(null);
  const posRef = useRef({ x: 50, y: 50, dx: 2, dy: 1.5 });
  const finished = useRef(false);

  useEffect(() => {
    let last = performance.now();
    const loop = (now) => {
      const dt = (now - last) / 1000; last = now;
      const p = posRef.current;
      p.x += p.dx * 80 * dt; p.y += p.dy * 60 * dt;
      if (p.x > 85 || p.x < 15) p.dx *= -1;
      if (p.y > 80 || p.y < 20) p.dy *= -1;
      setPos({ x: p.x, y: p.y });
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  const shoot = () => {
    if (finished.current) return;
    const dist = Math.sqrt((posRef.current.x - 50) ** 2 + (posRef.current.y - 50) ** 2);
    const s = Math.max(0, Math.round(100 - dist * 2.5));
    const ns = [...shots, s]; setShots(ns);
    const nr = round + 1; setRound(nr);
    if (nr >= totalRounds) { finished.current = true; const avg = Math.round(ns.reduce((a, b) => a + b, 0) / ns.length); setTimeout(() => onFinish(avg), 500); }
    posRef.current.dx *= (Math.random() > 0.5 ? 1 : -1) * (1 + Math.random() * 0.5);
    posRef.current.dy *= (Math.random() > 0.5 ? 1 : -1) * (1 + Math.random() * 0.5);
  };

  return (
    <div className="space-y-2" data-testid="minigame-shotperfect">
      <div className="flex justify-between text-xs"><span className="text-gray-400">Shot {Math.min(round + 1, totalRounds)}/{totalRounds}</span>{shots.length > 0 && <span className="text-cyan-400">{shots[shots.length-1]}pt</span>}</div>
      <div className="relative w-full h-52 bg-gray-900/60 rounded-xl overflow-hidden border border-gray-700 cursor-pointer" onPointerDown={shoot}>
        <Crosshair className="absolute w-8 h-8 text-white/20 pointer-events-none" style={{ left: 'calc(50% - 16px)', top: 'calc(50% - 16px)' }} />
        <div className="absolute w-6 h-6 bg-green-500/30 rounded-full border-2 border-green-400" style={{ left: `calc(50% - 12px)`, top: `calc(50% - 12px)` }} />
        <motion.div className="absolute" style={{ left: `${pos.x}%`, top: `${pos.y}%`, transform: 'translate(-50%, -50%)' }}>
          <Camera className="w-7 h-7 text-yellow-400" />
        </motion.div>
      </div>
      <p className="text-[10px] text-gray-500 text-center">Tappa quando il soggetto e al centro!</p>
    </div>
  );
}

/* ─── 7. LIGHT SETUP — Slider luce ─── */
export function LightSetup({ onFinish }) {
  const [target] = useState(() => 20 + Math.floor(Math.random() * 60));
  const [value, setValue] = useState(50);
  const [round, setRound] = useState(0);
  const [totalScore, setTotalScore] = useState(0);
  const totalRounds = 3;
  const finished = useRef(false);

  const confirm = () => {
    const diff = Math.abs(value - target);
    const s = Math.max(0, 100 - diff * 3);
    const ns = totalScore + s; setTotalScore(ns);
    const nr = round + 1; setRound(nr);
    if (nr >= totalRounds && !finished.current) { finished.current = true; setTimeout(() => onFinish(Math.round(ns / totalRounds)), 500); }
  };

  return (
    <div className="space-y-4" data-testid="minigame-lightsetup">
      <div className="flex justify-between text-xs"><span className="text-gray-400">Round {Math.min(round + 1, totalRounds)}/{totalRounds}</span><span className="text-green-400">{totalScore}pt</span></div>
      <div className="flex items-center justify-center gap-4">
        <div className="w-20 h-20 rounded-xl border-2 border-dashed border-yellow-500/40 flex items-center justify-center" style={{ backgroundColor: `hsl(45, 80%, ${target}%)` }}>
          <p className="text-[9px] text-white/80 font-bold">TARGET</p>
        </div>
        <div className="w-20 h-20 rounded-xl border-2 border-cyan-500/40 flex items-center justify-center" style={{ backgroundColor: `hsl(45, 80%, ${value}%)` }}>
          <SlidersHorizontal className="w-5 h-5 text-white/60" />
        </div>
      </div>
      <input type="range" min="0" max="100" value={value} onChange={e => setValue(Number(e.target.value))} className="w-full accent-yellow-500 h-2" />
      <Button onClick={confirm} className="w-full bg-yellow-600 hover:bg-yellow-700 h-10 text-sm font-bold" data-testid="light-confirm">Conferma</Button>
    </div>
  );
}

/* ─── 8. CAST MATCH — Scegli l'attore corretto ─── */
const CAST_DATA = [
  { film: 'Il Padrino', correct: 'Marlon Brando', wrong: ['Al Pacino', 'Robert De Niro', 'Jack Nicholson'] },
  { film: 'Titanic', correct: 'Leonardo DiCaprio', wrong: ['Brad Pitt', 'Tom Hanks', 'Johnny Depp'] },
  { film: 'Matrix', correct: 'Keanu Reeves', wrong: ['Will Smith', 'Nicolas Cage', 'Mel Gibson'] },
  { film: 'Joker', correct: 'Joaquin Phoenix', wrong: ['Jared Leto', 'Heath Ledger', 'Jack Nicholson'] },
  { film: 'Forrest Gump', correct: 'Tom Hanks', wrong: ['Robin Williams', 'Jim Carrey', 'Steve Martin'] },
];

export function CastMatch({ onFinish }) {
  const [qi, setQi] = useState(0);
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(15);
  const [answered, setAnswered] = useState(false);
  const [options, setOptions] = useState([]);
  const finished = useRef(false);

  useEffect(() => {
    const q = CAST_DATA[qi % CAST_DATA.length];
    setOptions([q.correct, ...q.wrong].sort(() => Math.random() - 0.5));
    setAnswered(false);
  }, [qi]);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onFinish(score); } }, [time, score, onFinish]);

  const answer = (opt) => {
    if (answered) return; setAnswered(true);
    const correct = opt === CAST_DATA[qi % CAST_DATA.length].correct;
    if (correct) setScore(s => s + 20);
    setTimeout(() => { if (qi + 1 < CAST_DATA.length) setQi(qi + 1); else if (!finished.current) { finished.current = true; onFinish(score + (correct ? 20 : 0)); } }, 500);
  };

  return (
    <div className="space-y-3" data-testid="minigame-castmatch">
      <div className="flex justify-between text-xs"><span className="text-gray-400">Film {qi + 1}/{CAST_DATA.length}</span><span className="text-green-400">{score}pt</span><span className="text-white">{time}s</span></div>
      <p className="text-center text-sm font-bold">Chi e il protagonista di <span className="text-yellow-400">{CAST_DATA[qi % CAST_DATA.length].film}</span>?</p>
      <div className="grid grid-cols-2 gap-2">
        {options.map(opt => (
          <Button key={opt} variant="outline" size="sm" disabled={answered}
            className={`text-xs h-10 border-gray-700 ${answered && opt === CAST_DATA[qi % CAST_DATA.length].correct ? 'bg-green-500/20 border-green-500 text-green-400' : answered ? 'opacity-40' : ''}`}
            onClick={() => answer(opt)} data-testid={`cast-${opt}`}>
            <UserCheck className="w-3 h-3 mr-1" />{opt}
          </Button>
        ))}
      </div>
    </div>
  );
}

/* ─── 9. EDITING CUT — Tappa al momento giusto ─── */
export function EditingCut({ onFinish }) {
  const [pos, setPos] = useState(0);
  const [cuts, setCuts] = useState([]);
  const [round, setRound] = useState(0);
  const totalRounds = 4;
  const [cutZone] = useState(() => 30 + Math.random() * 40);
  const rafRef = useRef(null);
  const posRef = useRef(0);
  const finished = useRef(false);

  useEffect(() => {
    const loop = () => {
      posRef.current = (posRef.current + 0.8) % 100;
      setPos(posRef.current);
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  const cut = () => {
    if (finished.current) return;
    cancelAnimationFrame(rafRef.current);
    const diff = Math.abs(posRef.current - cutZone);
    const s = Math.max(0, Math.round(100 - diff * 3));
    const nc = [...cuts, s]; setCuts(nc);
    const nr = round + 1; setRound(nr);
    if (nr >= totalRounds) { finished.current = true; setTimeout(() => onFinish(Math.round(nc.reduce((a, b) => a + b, 0) / nc.length)), 600); }
    else { posRef.current = 0; rafRef.current = requestAnimationFrame(function loop() { posRef.current = (posRef.current + 0.8) % 100; setPos(posRef.current); rafRef.current = requestAnimationFrame(loop); }); }
  };

  return (
    <div className="space-y-3" data-testid="minigame-editingcut">
      <div className="flex justify-between text-xs"><span className="text-gray-400">Cut {Math.min(round + 1, totalRounds)}/{totalRounds}</span>{cuts.length > 0 && <span className="text-cyan-400">{cuts[cuts.length-1]}pt</span>}</div>
      <div className="h-6 bg-gray-800 rounded-full relative overflow-hidden border border-gray-700">
        <div className="absolute bg-green-500/30 h-full" style={{ left: `${cutZone - 4}%`, width: '8%' }} />
        <div className="absolute bg-cyan-400 h-full w-1 rounded-full shadow-[0_0_8px_rgba(34,211,238,0.8)]" style={{ left: `${pos}%` }} />
      </div>
      <Button onClick={cut} className="w-full bg-purple-600 hover:bg-purple-700 h-12 text-lg font-black" data-testid="cut-btn"><Scissors className="w-5 h-5 mr-2" />CUT!</Button>
      <p className="text-[10px] text-gray-500 text-center">Taglia nella zona verde!</p>
    </div>
  );
}

/* ─── 10. FOLLOW CAM — Segui il punto ─── */
export function FollowCam({ onFinish }) {
  const [target, setTarget] = useState({ x: 50, y: 50 });
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(8);
  const [cursor, setCursor] = useState({ x: 50, y: 50 });
  const areaRef = useRef(null);
  const tRef = useRef({ x: 50, y: 50, dx: 3, dy: 2 });
  const finished = useRef(false);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onFinish(score); } }, [time, score, onFinish]);

  useEffect(() => {
    const loop = () => {
      const t = tRef.current;
      t.x += t.dx * 0.5; t.y += t.dy * 0.5;
      if (t.x > 90 || t.x < 10) t.dx *= -1;
      if (t.y > 85 || t.y < 15) t.dy *= -1;
      if (Math.random() < 0.02) { t.dx = (Math.random() - 0.5) * 6; t.dy = (Math.random() - 0.5) * 6; }
      setTarget({ x: t.x, y: t.y });
      requestAnimationFrame(loop);
    };
    const raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    const iv = setInterval(() => {
      const dist = Math.sqrt((cursor.x - tRef.current.x) ** 2 + (cursor.y - tRef.current.y) ** 2);
      if (dist < 15) setScore(s => s + 2);
    }, 200);
    return () => clearInterval(iv);
  }, [cursor]);

  const handleMove = (e) => {
    const rect = areaRef.current?.getBoundingClientRect();
    if (!rect) return;
    const touches = e.touches ? e.touches[0] : e;
    setCursor({ x: ((touches.clientX - rect.left) / rect.width) * 100, y: ((touches.clientY - rect.top) / rect.height) * 100 });
  };

  return (
    <div className="space-y-2" data-testid="minigame-followcam">
      <div className="flex justify-between text-xs"><span className="text-green-400 font-bold">{score}pt</span><span className="text-white font-bold">{time}s</span></div>
      <div ref={areaRef} className="relative w-full h-52 bg-gray-900/60 rounded-xl overflow-hidden border border-gray-700 touch-none cursor-none"
        onPointerMove={handleMove} onTouchMove={handleMove}>
        <div className="absolute w-5 h-5 bg-yellow-500/40 rounded-full border-2 border-yellow-400 transition-none pointer-events-none" style={{ left: `${target.x}%`, top: `${target.y}%`, transform: 'translate(-50%,-50%)' }}>
          <Star className="w-3 h-3 text-yellow-400 absolute top-0.5 left-0.5" />
        </div>
        <div className="absolute w-4 h-4 bg-cyan-500/50 rounded-full border border-cyan-400 pointer-events-none" style={{ left: `${cursor.x}%`, top: `${cursor.y}%`, transform: 'translate(-50%,-50%)' }} />
      </div>
      <p className="text-[10px] text-gray-500 text-center">Segui la stella col dito!</p>
    </div>
  );
}

/* ─── 11. CHAOS PREMIERE — Tap caotico con bombe ─── */
export function ChaosPremiere({ onFinish }) {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(10);
  const [items, setItems] = useState([]);
  const [shake, setShake] = useState(false);
  const idC = useRef(0);
  const finished = useRef(false);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onFinish(Math.max(0, score)); } }, [time, score, onFinish]);

  useEffect(() => {
    const types = [
      { type: 'ciak', points: 2, icon: 'film' },
      { type: 'star', points: 3, icon: 'star' },
      { type: 'ticket', points: 1, icon: 'ticket' },
      { type: 'bomb', points: -5, icon: 'bomb' },
    ];
    const spawn = () => {
      const count = Math.floor(Math.random() * 4) + 2;
      const batch = [];
      for (let i = 0; i < count; i++) {
        const t = types[Math.floor(Math.random() * types.length)];
        batch.push({ id: idC.current++, ...t, x: Math.random() * 80 + 5, y: -10, speed: 1.5 + Math.random() * 3 });
      }
      setItems(prev => [...prev, ...batch]);
    };
    const iv = setInterval(spawn, 400);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    const loop = () => {
      setItems(prev => prev.map(it => ({ ...it, y: it.y + it.speed })).filter(it => it.y < 105));
      requestAnimationFrame(loop);
    };
    const raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  const tap = (item) => {
    setScore(s => s + item.points);
    setItems(prev => prev.filter(it => it.id !== item.id));
    if (item.type === 'bomb') { setShake(true); setTimeout(() => setShake(false), 300); }
  };

  const ICONS = { film: Film, star: Star, ticket: Award, bomb: Bomb };

  return (
    <div className={`relative w-full h-80 bg-gray-900/60 rounded-xl overflow-hidden select-none touch-none ${shake ? 'animate-[shake_0.3s]' : ''}`} data-testid="minigame-chaos">
      <div className="absolute top-2 left-0 right-0 flex justify-between px-3 z-20 pointer-events-none">
        <span className="text-sm font-black text-yellow-400 bg-black/60 px-2 py-0.5 rounded">{score}</span>
        <span className="text-sm font-black text-white bg-black/60 px-2 py-0.5 rounded">{time}s</span>
      </div>
      {items.map(it => {
        const Icon = ICONS[it.icon] || Film;
        const isBomb = it.type === 'bomb';
        return (
          <div key={it.id} className="absolute z-10" style={{ left: `${it.x}%`, top: `${it.y}%`, touchAction: 'none', pointerEvents: 'auto' }}
            onPointerDown={(e) => { e.preventDefault(); tap(it); }}>
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isBomb ? 'bg-red-500/40 border-red-500/70' : 'bg-yellow-500/30 border-yellow-500/60'} border active:scale-75 transition-transform`}>
              <Icon className={`w-5 h-5 pointer-events-none ${isBomb ? 'text-red-400' : 'text-yellow-400'}`} />
            </div>
          </div>
        );
      })}
      <p className="absolute bottom-2 left-0 right-0 text-center text-[10px] text-gray-500 pointer-events-none">Tappa tutto tranne le bombe!</p>
    </div>
  );
}

/* ─── 12. REEL SNAKE — Snake game ─── */
const GRID = 15;
const CELL = 100 / GRID;

export function ReelSnake({ onFinish }) {
  const [snake, setSnake] = useState([{ x: 7, y: 7 }]);
  const [dir, setDir] = useState({ x: 1, y: 0 });
  const [food, setFood] = useState({ x: 10, y: 7, type: 'star' });
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(30);
  const [gameOver, setGameOver] = useState(false);
  const dirRef = useRef({ x: 1, y: 0 });
  const snakeRef = useRef([{ x: 7, y: 7 }]);
  const scoreRef = useRef(0);
  const finished = useRef(false);
  const touchStart = useRef(null);

  const spawnFood = useCallback(() => {
    const types = ['star', 'star', 'star', 'ticket', 'bomb'];
    return { x: Math.floor(Math.random() * GRID), y: Math.floor(Math.random() * GRID), type: types[Math.floor(Math.random() * types.length)] };
  }, []);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);

  useEffect(() => {
    if ((time === 0 || gameOver) && !finished.current) { finished.current = true; onFinish(Math.max(0, scoreRef.current)); }
  }, [time, gameOver, onFinish]);

  useEffect(() => {
    const speed = Math.max(80, 180 - scoreRef.current * 2);
    const iv = setInterval(() => {
      if (finished.current) return;
      const s = snakeRef.current;
      const d = dirRef.current;
      const head = { x: (s[0].x + d.x + GRID) % GRID, y: (s[0].y + d.y + GRID) % GRID };
      if (s.some(seg => seg.x === head.x && seg.y === head.y)) { setGameOver(true); return; }
      const ns = [head, ...s];
      if (head.x === food.x && head.y === food.y) {
        if (food.type === 'bomb') { scoreRef.current = Math.max(0, scoreRef.current - 5); setScore(scoreRef.current); }
        else { scoreRef.current += (food.type === 'star' ? 3 : 1); setScore(scoreRef.current); }
        setFood(spawnFood());
      } else { ns.pop(); }
      snakeRef.current = ns; setSnake(ns);
    }, speed);
    return () => clearInterval(iv);
  }, [food, spawnFood]);

  const handleSwipe = (e) => {
    if (!touchStart.current) return;
    const dx = e.changedTouches[0].clientX - touchStart.current.x;
    const dy = e.changedTouches[0].clientY - touchStart.current.y;
    if (Math.abs(dx) > Math.abs(dy)) { if (dx > 20 && dirRef.current.x !== -1) { dirRef.current = { x: 1, y: 0 }; setDir(dirRef.current); } else if (dx < -20 && dirRef.current.x !== 1) { dirRef.current = { x: -1, y: 0 }; setDir(dirRef.current); } }
    else { if (dy > 20 && dirRef.current.y !== -1) { dirRef.current = { x: 0, y: 1 }; setDir(dirRef.current); } else if (dy < -20 && dirRef.current.y !== 1) { dirRef.current = { x: 0, y: -1 }; setDir(dirRef.current); } }
    touchStart.current = null;
  };

  const FOOD_COLORS = { star: 'bg-yellow-400', ticket: 'bg-cyan-400', bomb: 'bg-red-500' };

  return (
    <div className="space-y-2" data-testid="minigame-snake">
      <div className="flex justify-between text-xs"><span className="text-green-400 font-bold">{score}pt</span><span className="text-white font-bold">{time}s</span></div>
      <div className="relative w-full aspect-square bg-gray-900/60 rounded-xl overflow-hidden border border-gray-700 touch-none"
        onTouchStart={e => { touchStart.current = { x: e.touches[0].clientX, y: e.touches[0].clientY }; }}
        onTouchEnd={handleSwipe}>
        {snake.map((seg, i) => (
          <div key={i} className={`absolute rounded-sm ${i === 0 ? 'bg-yellow-400' : 'bg-yellow-600/60'}`}
            style={{ left: `${seg.x * CELL}%`, top: `${seg.y * CELL}%`, width: `${CELL}%`, height: `${CELL}%` }} />
        ))}
        <div className={`absolute rounded-full ${FOOD_COLORS[food.type]}`}
          style={{ left: `${food.x * CELL}%`, top: `${food.y * CELL}%`, width: `${CELL}%`, height: `${CELL}%` }} />
      </div>
      <p className="text-[10px] text-gray-500 text-center">Swipe per muovere! Raccogli stelle, evita bombe</p>
      {/* Desktop controls */}
      <div className="grid grid-cols-3 gap-1 max-w-[140px] mx-auto">
        <div />
        <Button size="sm" variant="outline" className="h-8 text-xs border-gray-700" onClick={() => { if (dirRef.current.y !== 1) { dirRef.current = { x: 0, y: -1 }; setDir(dirRef.current); } }}>^</Button>
        <div />
        <Button size="sm" variant="outline" className="h-8 text-xs border-gray-700" onClick={() => { if (dirRef.current.x !== 1) { dirRef.current = { x: -1, y: 0 }; setDir(dirRef.current); } }}>&lt;</Button>
        <Button size="sm" variant="outline" className="h-8 text-xs border-gray-700" onClick={() => { if (dirRef.current.y !== -1) { dirRef.current = { x: 0, y: 1 }; setDir(dirRef.current); } }}>v</Button>
        <Button size="sm" variant="outline" className="h-8 text-xs border-gray-700" onClick={() => { if (dirRef.current.x !== -1) { dirRef.current = { x: 1, y: 0 }; setDir(dirRef.current); } }}>&gt;</Button>
      </div>
    </div>
  );
}
