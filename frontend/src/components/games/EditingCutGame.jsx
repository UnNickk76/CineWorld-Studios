import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../ui/button';
import { Scissors } from 'lucide-react';

export function EditingCutGame({ mode = 'contest', onComplete }) {
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
    if (nr >= totalRounds) { finished.current = true; setTimeout(() => onComplete(Math.round(nc.reduce((a, b) => a + b, 0) / nc.length)), 600); }
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
