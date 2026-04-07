import React, { useState, useRef } from 'react';
import { Button } from '../ui/button';
import { SlidersHorizontal } from 'lucide-react';

export function LightSetupGame({ mode = 'contest', onComplete }) {
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
    if (nr >= totalRounds && !finished.current) { finished.current = true; setTimeout(() => onComplete(Math.round(ns / totalRounds)), 500); }
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
