import React, { useState, useEffect, useRef } from 'react';
import { Camera, Crosshair } from 'lucide-react';

export function ShotPerfectGame({ mode = 'contest', onComplete }) {
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
    if (nr >= totalRounds) { finished.current = true; const avg = Math.round(ns.reduce((a, b) => a + b, 0) / ns.length); setTimeout(() => onComplete(avg), 500); }
    posRef.current.dx *= (Math.random() > 0.5 ? 1 : -1) * (1 + Math.random() * 0.5);
    posRef.current.dy *= (Math.random() > 0.5 ? 1 : -1) * (1 + Math.random() * 0.5);
  };

  return (
    <div className="space-y-2" data-testid="minigame-shotperfect">
      <div className="flex justify-between text-xs"><span className="text-gray-400">Shot {Math.min(round + 1, totalRounds)}/{totalRounds}</span>{shots.length > 0 && <span className="text-cyan-400">{shots[shots.length-1]}pt</span>}</div>
      <div className="relative w-full h-52 bg-gray-900/60 rounded-xl overflow-hidden border border-gray-700 cursor-pointer" onPointerDown={shoot}>
        <Crosshair className="absolute w-8 h-8 text-white/20 pointer-events-none" style={{ left: 'calc(50% - 16px)', top: 'calc(50% - 16px)' }} />
        <div className="absolute w-6 h-6 bg-green-500/30 rounded-full border-2 border-green-400" style={{ left: 'calc(50% - 12px)', top: 'calc(50% - 12px)' }} />
        <div className="absolute" style={{ left: `${pos.x}%`, top: `${pos.y}%`, transform: 'translate(-50%, -50%)' }}>
          <Camera className="w-7 h-7 text-yellow-400" />
        </div>
      </div>
      <p className="text-[10px] text-gray-500 text-center">Tappa quando il soggetto e al centro!</p>
    </div>
  );
}
