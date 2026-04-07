import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../ui/button';

export function StopPerfectGame({ onComplete }) {
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
    if (!finished.current) { finished.current = true; setTimeout(() => onComplete(s), 600); }
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
