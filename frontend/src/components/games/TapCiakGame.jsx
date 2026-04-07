import React, { useState, useEffect, useRef } from 'react';
import { Film } from 'lucide-react';

export function TapCiakGame({ mode = 'contest', onComplete }) {
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

  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onComplete(score); } }, [time, score, onComplete]);

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
