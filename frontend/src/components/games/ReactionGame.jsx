import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Timer, Target } from 'lucide-react';

export function ReactionGame({ mode = 'contest', onComplete }) {
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
      if (!finished.current) { finished.current = true; setTimeout(() => onComplete(Math.max(0, Math.round(100 - avg / 5))), 800); }
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
