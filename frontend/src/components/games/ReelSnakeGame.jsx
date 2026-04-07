import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '../ui/button';

const GRID = 15;
const CELL = 100 / GRID;

export function ReelSnakeGame({ mode = 'contest', onComplete }) {
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
  useEffect(() => { if ((time === 0 || gameOver) && !finished.current) { finished.current = true; onComplete(Math.max(0, scoreRef.current)); } }, [time, gameOver, onComplete]);

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
