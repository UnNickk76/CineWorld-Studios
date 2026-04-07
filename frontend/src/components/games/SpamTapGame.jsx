import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';

export function SpamTapGame({ onComplete }) {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(4);
  const [flash, setFlash] = useState(0);
  const finished = useRef(false);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onComplete(score); } }, [time, score, onComplete]);

  const tap = () => { setScore(s => s + 2); setFlash(f => f + 1); };

  return (
    <div className="text-center space-y-3" data-testid="minigame-spamclick">
      <div className="flex justify-between px-2"><span className="text-lg font-black text-red-400">{score}</span><span className="text-lg font-black text-white">{time}s</span></div>
      <motion.button className="w-full h-28 rounded-2xl border-2 border-red-500 text-red-400 text-3xl font-black select-none bg-red-500/15 active:bg-red-500/40"
        animate={{ scale: flash ? [1, 0.92, 1] : 1 }} key={flash} transition={{ duration: 0.08 }}
        onPointerDown={tap} data-testid="spam-btn"><Zap className="w-10 h-10 mx-auto mb-1" />TAP!</motion.button>
    </div>
  );
}
