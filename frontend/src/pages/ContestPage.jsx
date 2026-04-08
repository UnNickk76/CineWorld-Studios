import React, { useState, useEffect, useCallback, useContext, lazy, Suspense } from 'react';
import { AuthContext } from '../contexts';
import { Lock, Star, Gift, Clock, CheckCircle, ChevronRight, Trophy } from 'lucide-react';
import {
  TapCiak, MemoryPro, StopPerfetto, SpamClick, ReactionGame,
  ShotPerfect, LightSetup, CastMatch, EditingCut, FollowCam,
  ChaosPremiere, ReelSnake, MatrixDodge, MatrixDodgePro,
  CineDrive, CineDrivePro, SuperCinePro, FlipperPro
} from '../components/MiniGames';

const GAME_COMPONENTS = {
  tap_ciak: TapCiak, memory_pro: MemoryPro, stop_perfetto: StopPerfetto,
  spam_click: SpamClick, reaction: ReactionGame, shot_perfect: ShotPerfect,
  light_setup: LightSetup, cast_match: CastMatch, editing_cut: EditingCut,
  follow_cam: FollowCam, chaos_premiere: ChaosPremiere, reel_snake: ReelSnake,
  matrix_dodge: MatrixDodge, matrix_dodge_pro: MatrixDodgePro,
  cine_drive: CineDrive, cine_drive_pro: CineDrivePro,
  supercine_pro: SuperCinePro, flipper_pro: FlipperPro,
};

export default function ContestPage() {
  const { api } = useContext(AuthContext);
  const [progress, setProgress] = useState(null);
  const [dailyGames, setDailyGames] = useState([]);
  const [activeGame, setActiveGame] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [msg, setMsg] = useState('');

  const fetchProgress = useCallback(async () => {
    try {
      const res = await api.get('/contest/progress');
      setProgress(res.data);
      setDailyGames(res.data.daily_games || []);
    } catch (e) { console.error('Contest progress error', e); }
  }, [api]);

  useEffect(() => { fetchProgress(); }, [fetchProgress]);

  // Countdown timer
  useEffect(() => {
    if (!progress?.next_unlock_at) { setCountdown(0); return; }
    const tick = () => {
      const diff = Math.max(0, Math.ceil((new Date(progress.next_unlock_at) - Date.now()) / 1000));
      setCountdown(diff);
      if (diff <= 0) fetchProgress();
    };
    tick();
    const iv = setInterval(tick, 1000);
    return () => clearInterval(iv);
  }, [progress?.next_unlock_at, fetchProgress]);

  const handleComplete = useCallback(async (score) => {
    setActiveGame(null);
    try {
      const res = await api.post('/contest/complete-step', { score });
      setMsg(`+${res.data.credits} crediti!`);
      setTimeout(() => setMsg(''), 2500);
      fetchProgress();
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Errore');
      setTimeout(() => setMsg(''), 2500);
    }
  }, [api, fetchProgress]);

  if (!progress) return <div className="text-center text-gray-400 py-10">Caricamento...</div>;

  const currentStep = progress.current_step;
  const completed = progress.completed;

  // Active game
  if (activeGame) {
    const GameComp = GAME_COMPONENTS[activeGame.game_id];
    if (!GameComp) return <div className="text-red-400 text-center py-10">Gioco non trovato: {activeGame.game_id}</div>;
    return (
      <div className="max-w-md mx-auto px-3 py-2">
        <div className="flex items-center justify-between mb-2">
          <button className="text-xs text-gray-400 underline" onClick={() => setActiveGame(null)}>Torna al Contest</button>
          <span className="text-xs text-yellow-400 font-mono">Step {activeGame.step}/12 {activeGame.is_bonus ? '(BONUS)' : ''}</span>
        </div>
        <GameComp mode="contest" onComplete={handleComplete} />
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-3 py-4 space-y-4" data-testid="contest-page">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-lg font-bold text-white flex items-center justify-center gap-2">
          <Trophy className="w-5 h-5 text-yellow-400" /> Contest Giornaliero
        </h2>
        <p className="text-xs text-gray-400 mt-1">10 minigiochi + 2 bonus | Max 50 crediti/giorno</p>
      </div>

      {msg && <div className="text-center text-yellow-400 font-bold text-sm animate-pulse">{msg}</div>}

      {/* Countdown */}
      {countdown > 0 && (
        <div className="flex items-center justify-center gap-2 text-xs text-cyan-400">
          <Clock className="w-3.5 h-3.5" />
          <span>Prossimo sblocco: {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, '0')}</span>
        </div>
      )}

      {/* Games list */}
      <div className="space-y-2">
        {dailyGames.map((game) => {
          const isDone = game.step < currentStep;
          const isCurrent = game.step === currentStep && !completed;
          const isLocked = game.step > currentStep;
          const isBonus = game.is_bonus;
          const canPlay = isCurrent && countdown <= 0;

          return (
            <div
              key={game.step}
              className={`rounded-lg p-3 flex items-center gap-3 transition-all ${
                isDone ? 'bg-green-900/20 border border-green-800/30' :
                isCurrent ? 'bg-yellow-900/20 border border-yellow-600/40 shadow-lg shadow-yellow-900/20' :
                'bg-gray-900/40 border border-gray-800/30 opacity-60'
              }`}
              data-testid={`contest-step-${game.step}`}
            >
              {/* Step badge */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                isDone ? 'bg-green-600 text-white' :
                isCurrent ? 'bg-yellow-600 text-black' :
                'bg-gray-700 text-gray-400'
              }`}>
                {isDone ? <CheckCircle className="w-4 h-4" /> : game.step}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className={`text-sm font-semibold truncate ${isDone ? 'text-green-400' : isCurrent ? 'text-white' : 'text-gray-500'}`}>
                    {game.name}
                  </span>
                  {isBonus && <Gift className="w-3.5 h-3.5 text-purple-400 shrink-0" />}
                </div>
                <span className="text-[10px] text-gray-500">
                  {isBonus ? 'Bonus — max 10 crediti' : `Step ${game.step} — max 3 crediti`}
                </span>
              </div>

              {/* Action */}
              {isDone && <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />}
              {isLocked && <Lock className="w-4 h-4 text-gray-600 shrink-0" />}
              {isCurrent && (
                <button
                  className={`px-3 py-1.5 rounded-md text-xs font-bold shrink-0 ${
                    canPlay ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  }`}
                  disabled={!canPlay}
                  onClick={() => canPlay && setActiveGame(game)}
                  data-testid={`contest-play-${game.step}`}
                >
                  {canPlay ? 'GIOCA' : <Clock className="w-3.5 h-3.5" />}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Completed */}
      {completed && (
        <div className="text-center py-4 space-y-1" data-testid="contest-all-done">
          <Star className="w-8 h-8 text-yellow-400 mx-auto" />
          <p className="text-yellow-400 font-bold">Tutti gli step completati!</p>
          <p className="text-xs text-gray-500">Torna domani per nuovi minigiochi.</p>
        </div>
      )}
    </div>
  );
}
