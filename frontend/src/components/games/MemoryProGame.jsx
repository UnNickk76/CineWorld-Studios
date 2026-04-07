import React, { useState, useEffect, useRef } from 'react';
import { Film, Camera, Star, Award, Heart, Music2, Sparkles, Eye, Flame, Crown, Trophy, Video, Tv, Bookmark, Gift, Sun, Play, Zap, Target, Timer } from 'lucide-react';

const ICONS = [Film, Camera, Star, Award, Heart, Music2, Sparkles, Eye, Flame, Crown, Trophy, Video, Tv, Bookmark, Gift, Sun, Play, Zap, Target, Timer];
const COLORS = ['bg-red-600','bg-blue-600','bg-green-600','bg-purple-600','bg-yellow-600','bg-cyan-600','bg-pink-600','bg-orange-600','bg-teal-600','bg-indigo-600','bg-rose-600','bg-lime-600','bg-sky-600','bg-violet-600','bg-amber-600','bg-emerald-600','bg-fuchsia-600','bg-red-500','bg-blue-500','bg-green-500'];

export function MemoryProGame({ mode = 'contest', onComplete }) {
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
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onComplete(score); } }, [time, score, onComplete]);
  useEffect(() => { if (matched.size === pairs && !finished.current) { finished.current = true; onComplete(score + time * 3); } }, [matched, score, time, pairs, onComplete]);

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
          const Icon = ICONS[c];
          return (
            <div key={i} onClick={() => click(i)}
              className={`aspect-square flex items-center justify-center rounded cursor-pointer select-none transition-all duration-150 ${
                matched.has(c) ? 'bg-green-800/30 scale-90' : revealed ? COLORS[c] + ' scale-95' : 'bg-gray-700 hover:bg-gray-600 active:scale-90'
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
