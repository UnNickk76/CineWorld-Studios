import React, { useState, useEffect, useRef } from 'react';
import { Star } from 'lucide-react';

export function FollowCamGame({ onComplete }) {
  const [target, setTarget] = useState({ x: 50, y: 50 });
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(8);
  const [cursor, setCursor] = useState({ x: 50, y: 50 });
  const areaRef = useRef(null);
  const tRef = useRef({ x: 50, y: 50, dx: 3, dy: 2 });
  const finished = useRef(false);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onComplete(score); } }, [time, score, onComplete]);

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
        <div className="absolute w-5 h-5 bg-yellow-500/40 rounded-full border-2 border-yellow-400 pointer-events-none" style={{ left: `${target.x}%`, top: `${target.y}%`, transform: 'translate(-50%,-50%)' }}>
          <Star className="w-3 h-3 text-yellow-400 absolute top-0.5 left-0.5" />
        </div>
        <div className="absolute w-4 h-4 bg-cyan-500/50 rounded-full border border-cyan-400 pointer-events-none" style={{ left: `${cursor.x}%`, top: `${cursor.y}%`, transform: 'translate(-50%,-50%)' }} />
      </div>
      <p className="text-[10px] text-gray-500 text-center">Segui la stella col dito!</p>
    </div>
  );
}
