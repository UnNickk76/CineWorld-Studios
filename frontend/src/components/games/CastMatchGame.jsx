import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../ui/button';
import { UserCheck } from 'lucide-react';

const CAST_DATA = [
  { film: 'Il Padrino', correct: 'Marlon Brando', wrong: ['Al Pacino', 'Robert De Niro', 'Jack Nicholson'] },
  { film: 'Titanic', correct: 'Leonardo DiCaprio', wrong: ['Brad Pitt', 'Tom Hanks', 'Johnny Depp'] },
  { film: 'Matrix', correct: 'Keanu Reeves', wrong: ['Will Smith', 'Nicolas Cage', 'Mel Gibson'] },
  { film: 'Joker', correct: 'Joaquin Phoenix', wrong: ['Jared Leto', 'Heath Ledger', 'Jack Nicholson'] },
  { film: 'Forrest Gump', correct: 'Tom Hanks', wrong: ['Robin Williams', 'Jim Carrey', 'Steve Martin'] },
];

export function CastMatchGame({ onComplete }) {
  const [qi, setQi] = useState(0);
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(15);
  const [answered, setAnswered] = useState(false);
  const [options, setOptions] = useState([]);
  const finished = useRef(false);

  useEffect(() => {
    const q = CAST_DATA[qi % CAST_DATA.length];
    setOptions([q.correct, ...q.wrong].sort(() => Math.random() - 0.5));
    setAnswered(false);
  }, [qi]);

  useEffect(() => { const iv = setInterval(() => setTime(p => { if (p <= 1) { clearInterval(iv); return 0; } return p - 1; }), 1000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (time === 0 && !finished.current) { finished.current = true; onComplete(score); } }, [time, score, onComplete]);

  const answer = (opt) => {
    if (answered) return; setAnswered(true);
    const correct = opt === CAST_DATA[qi % CAST_DATA.length].correct;
    if (correct) setScore(s => s + 20);
    setTimeout(() => { if (qi + 1 < CAST_DATA.length) setQi(qi + 1); else if (!finished.current) { finished.current = true; onComplete(score + (correct ? 20 : 0)); } }, 500);
  };

  return (
    <div className="space-y-3" data-testid="minigame-castmatch">
      <div className="flex justify-between text-xs"><span className="text-gray-400">Film {qi + 1}/{CAST_DATA.length}</span><span className="text-green-400">{score}pt</span><span className="text-white">{time}s</span></div>
      <p className="text-center text-sm font-bold">Chi e il protagonista di <span className="text-yellow-400">{CAST_DATA[qi % CAST_DATA.length].film}</span>?</p>
      <div className="grid grid-cols-2 gap-2">
        {options.map(opt => (
          <Button key={opt} variant="outline" size="sm" disabled={answered}
            className={`text-xs h-10 border-gray-700 ${answered && opt === CAST_DATA[qi % CAST_DATA.length].correct ? 'bg-green-500/20 border-green-500 text-green-400' : answered ? 'opacity-40' : ''}`}
            onClick={() => answer(opt)} data-testid={`cast-${opt}`}>
            <UserCheck className="w-3 h-3 mr-1" />{opt}
          </Button>
        ))}
      </div>
    </div>
  );
}
