import React, { useState, useEffect, useContext, useCallback } from 'react';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import { Trophy, Play, Lock, Check, MousePointerClick, Brain, Target, Zap, Timer } from 'lucide-react';
import { TapCiak, MemoryPro, StopPerfetto, SpamClick, ReactionGame } from '../components/MiniGames';

const STEPS = [
  { name: 'TapCiak', icon: MousePointerClick, Game: TapCiak },
  { name: 'Memory Pro', icon: Brain, Game: MemoryPro },
  { name: 'Stop Perfetto', icon: Target, Game: StopPerfetto },
  { name: 'Spam Click', icon: Zap, Game: SpamClick },
  { name: 'Reaction', icon: Timer, Game: ReactionGame },
];

export default function ContestPage() {
  const { api } = useContext(AuthContext);
  const [progress, setProgress] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadProgress = useCallback(async () => {
    try {
      const res = await api.get('/contest/progress');
      setProgress(res.data);
    } catch { toast.error('Errore caricamento contest'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadProgress(); }, [loadProgress]);

  const finishStep = async (score) => {
    setPlaying(false);
    try {
      const res = await api.post('/contest/complete-step', { score });
      toast.success(`+${res.data.credits} crediti!`);
      loadProgress();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
      loadProgress();
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-400">Caricamento...</div>;

  const currentStep = progress?.current_step || 1;
  const completed = progress?.completed || false;
  const locked = progress?.next_unlock_at && new Date(progress.next_unlock_at) > new Date();

  if (playing) {
    const stepIdx = Math.min(currentStep - 1, STEPS.length - 1);
    const { Game, name } = STEPS[stepIdx];
    return (
      <div className="max-w-sm mx-auto px-3 pt-4 pb-32" data-testid="contest-playing">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs text-gray-400">Step {currentStep}/{STEPS.length} — {name}</p>
          <Button variant="ghost" size="sm" className="text-xs text-gray-500" onClick={() => setPlaying(false)}>Esci</Button>
        </div>
        <Card className="bg-[#1A1A1B] border-gray-800">
          <CardContent className="p-4">
            <Game onFinish={finishStep} />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto px-3 pt-2 pb-32 space-y-3" data-testid="contest-page">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <Trophy className="w-5 h-5 text-yellow-400" /> Contest
        </h2>
        <p className="text-xs text-gray-500">Max 20 crediti/giorno</p>
      </div>

      <Progress value={completed ? 100 : ((currentStep - 1) / STEPS.length) * 100} className="h-1.5" />

      {STEPS.map((step, i) => {
        const stepNum = i + 1;
        const Icon = step.icon;
        const done = stepNum < currentStep;
        const isCurrent = stepNum === currentStep && !completed;
        const isLocked = stepNum > currentStep || (isCurrent && locked);
        return (
          <Card key={i} className={`bg-[#1A1A1B] border-gray-800 ${isLocked && !done ? 'opacity-40' : ''}`} data-testid={`step-card-${stepNum}`}>
            <CardContent className="p-3 flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${done ? 'bg-green-500/20' : isCurrent && !locked ? 'bg-cyan-500/20' : 'bg-gray-800'}`}>
                {done ? <Check className="w-5 h-5 text-green-400" /> : isLocked ? <Lock className="w-5 h-5 text-gray-600" /> : <Icon className="w-5 h-5 text-cyan-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold">{step.name}</p>
                <p className="text-[10px] text-gray-500">
                  {done ? 'Completato' : isCurrent && locked ? 'Sblocco tra poco...' : isCurrent ? 'Disponibile' : 'Bloccato'}
                </p>
              </div>
              {isCurrent && !locked && (
                <Button size="sm" className="bg-cyan-700 hover:bg-cyan-800 text-xs h-8 shrink-0" onClick={() => setPlaying(true)} data-testid={`play-step-${stepNum}`}>
                  <Play className="w-3 h-3 mr-1" /> Gioca
                </Button>
              )}
            </CardContent>
          </Card>
        );
      })}

      {completed && (
        <div className="text-center py-4 text-green-400 font-bold text-sm" data-testid="contest-all-done">
          Tutti gli step completati! Torna domani.
        </div>
      )}
    </div>
  );
}
