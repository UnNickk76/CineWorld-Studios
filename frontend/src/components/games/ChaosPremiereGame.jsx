import React, { useState, useEffect, useRef } from 'react';
import { Film, Star, Award, Bomb } from 'lucide-react';

export function ChaosPremiereGame({ onComplete }) {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(10);
  const [items, setItems] = useState([]);
  const [shake, setShake] = useState(false);
  const idC = useRef(0);
  const finished = useRef(false);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onComplete(Math.max(0, score)); } }, [time, score, onComplete]);

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
