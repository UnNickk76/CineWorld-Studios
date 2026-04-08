import React, { useState, useRef, useCallback } from 'react';
import { Button } from '../ui/button';
import { SlidersHorizontal, Check } from 'lucide-react';

export function LightSetupGame({ mode = 'contest', onComplete }) {
  const genTarget = () => 15 + Math.floor(Math.random() * 70);
  const [target, setTarget] = useState(genTarget);
  const [value, setValue] = useState(50);
  const [round, setRound] = useState(0);
  const [scores, setScores] = useState([]);
  const [lastDiff, setLastDiff] = useState(null);
  const [finished, setFinished] = useState(false);
  const totalRounds = 3;
  const sent = useRef(false);

  const confirm = useCallback(() => {
    if (finished) return;
    const diff = Math.abs(value - target);
    const accuracy = Math.max(0, 100 - diff * 2);
    const newScores = [...scores, accuracy];
    setScores(newScores);
    setLastDiff(accuracy);

    const nr = round + 1;
    setRound(nr);

    if (nr >= totalRounds) {
      setFinished(true);
      const avg = Math.round(newScores.reduce((a, b) => a + b, 0) / newScores.length);
      if (!sent.current) {
        sent.current = true;
        setTimeout(() => onComplete(avg), 1200);
      }
    } else {
      // Next round after brief feedback
      setTimeout(() => {
        setTarget(genTarget());
        setValue(50);
        setLastDiff(null);
      }, 800);
    }
  }, [value, target, round, scores, finished, onComplete]);

  const avgScore = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
  const credits = avgScore >= 85 ? 3 : avgScore >= 50 ? 2 : 1;

  // Finished: show result
  if (finished) {
    return (
      <div className="space-y-4 text-center py-4" data-testid="minigame-lightsetup-result">
        <p className="text-[10px] text-gray-500 uppercase font-bold">Risultato</p>
        <div className="text-4xl font-bold text-yellow-400">{avgScore}%</div>
        <p className="text-xs text-gray-400">Precisione media sui {totalRounds} round</p>
        <div className="flex justify-center gap-1">
          {scores.map((s, i) => (
            <span key={i} className={`text-[9px] px-2 py-0.5 rounded-full ${s >= 85 ? 'bg-emerald-500/20 text-emerald-400' : s >= 50 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
              R{i + 1}: {s}%
            </span>
          ))}
        </div>
        <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <p className="text-sm font-bold text-yellow-400">+{credits} crediti</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="minigame-lightsetup">
      <div className="flex justify-between text-xs">
        <span className="text-gray-400">Round {round + 1}/{totalRounds}</span>
        {scores.length > 0 && <span className="text-green-400">Media: {avgScore}%</span>}
      </div>

      {/* Target vs User */}
      <div className="flex items-center justify-center gap-4">
        <div className="w-20 h-20 rounded-xl border-2 border-dashed border-yellow-500/40 flex items-center justify-center transition-colors duration-300"
          style={{ backgroundColor: `hsl(45, 80%, ${target}%)` }}>
          <p className="text-[9px] text-white/80 font-bold drop-shadow">TARGET</p>
        </div>
        <div className="w-20 h-20 rounded-xl border-2 border-cyan-500/40 flex items-center justify-center transition-colors duration-300"
          style={{ backgroundColor: `hsl(45, 80%, ${value}%)` }}>
          <SlidersHorizontal className="w-5 h-5 text-white/60" />
        </div>
      </div>

      {/* Feedback dopo conferma */}
      {lastDiff !== null && (
        <div className={`text-center text-sm font-bold animate-pulse ${lastDiff >= 85 ? 'text-emerald-400' : lastDiff >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
          <Check className="w-4 h-4 inline mr-1" />{lastDiff}% preciso!
        </div>
      )}

      <input type="range" min="0" max="100" value={value}
        onChange={e => setValue(Number(e.target.value))}
        className="w-full accent-yellow-500 h-2"
        disabled={lastDiff !== null}
        data-testid="light-slider" />

      <Button onClick={confirm} disabled={lastDiff !== null}
        className="w-full bg-yellow-600 hover:bg-yellow-700 h-10 text-sm font-bold disabled:opacity-40"
        data-testid="light-confirm">
        {lastDiff !== null ? 'Prossimo round...' : 'Conferma'}
      </Button>
    </div>
  );
}
