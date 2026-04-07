import React, { useState, useEffect, useContext, useCallback, lazy, Suspense } from 'react';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  Trophy, Play, Gamepad2, BarChart3, Crown, Swords,
  Film, Brain, Target, Zap, Timer, Camera, Sun, UserCheck,
  Scissors, Eye, Sparkles, Clock, Flame, Award, Gift, Shield, Binary
} from 'lucide-react';
import {
  TapCiak, MemoryPro, StopPerfetto, SpamClick, ReactionGame,
  ShotPerfect, LightSetup, CastMatch, EditingCut, FollowCam,
  ChaosPremiere, ReelSnake, MatrixDodge, MatrixDodgePro
} from '../components/MiniGames';
import ChallengesPage from './ChallengesPage';

const GAME_ICONS = {
  tap_ciak: Film, memory_pro: Brain, stop_perfetto: Target, spam_tap: Zap,
  reaction: Timer, shot_perfect: Camera, light_setup: Sun, cast_match: UserCheck,
  editing_cut: Scissors, follow_cam: Eye, chaos_premiere: Sparkles, reel_snake: Gamepad2,
  matrix_dodge: Binary, matrix_dodge_pro: Binary,
};

const GAME_COMPONENTS = {
  tap_ciak: TapCiak, memory_pro: MemoryPro, stop_perfetto: StopPerfetto,
  spam_tap: SpamClick, reaction: ReactionGame, shot_perfect: ShotPerfect,
  light_setup: LightSetup, cast_match: CastMatch, editing_cut: EditingCut,
  follow_cam: FollowCam, chaos_premiere: ChaosPremiere, reel_snake: ReelSnake,
  matrix_dodge: MatrixDodge, matrix_dodge_pro: MatrixDodgePro,
};

function StreakBadge({ streak }) {
  if (!streak || streak < 3) return null;
  const color = streak >= 10 ? 'text-red-400 bg-red-500/15' : streak >= 5 ? 'text-orange-400 bg-orange-500/15' : 'text-yellow-400 bg-yellow-500/15';
  return <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold ${color}`}><Flame className="w-2.5 h-2.5" />{streak}</span>;
}

export default function MiniGamesPage() {
  const { api, user } = useContext(AuthContext);
  const [tab, setTab] = useState('solo');
  const [games, setGames] = useState([]);
  const [stats, setStats] = useState({});
  const [playing, setPlaying] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [lbGame, setLbGame] = useState('tap_ciak');
  const [lbPeriod, setLbPeriod] = useState('all');
  const [globalLb, setGlobalLb] = useState([]);
  const [vsTab, setVsTab] = useState('create');
  const [pendingVs, setPendingVs] = useState([]);
  const [myVs, setMyVs] = useState([]);
  const [vsPlaying, setVsPlaying] = useState(null);
  const [vsChallengeId, setVsChallengeId] = useState(null);
  const [vsRole, setVsRole] = useState(null);
  const [vsResult, setVsResult] = useState(null);
  const [streak, setStreak] = useState({ streak: 0, best_streak: 0, wins: 0, losses: 0 });
  const [titles, setTitles] = useState([]);

  const loadGames = useCallback(async () => { try { const r = await api.get('/arcade/games'); setGames(r.data); } catch {} }, [api]);
  const loadStats = useCallback(async () => { try { const r = await api.get('/arcade/solo/stats'); setStats(r.data); } catch {} }, [api]);
  const loadVs = useCallback(async () => { try { const [p, m] = await Promise.all([api.get('/arcade/vs/pending'), api.get('/arcade/vs/my')]); setPendingVs(p.data); setMyVs(m.data); } catch {} }, [api]);
  const loadStreak = useCallback(async () => { try { const r = await api.get('/arcade/streak'); setStreak(r.data); } catch {} }, [api]);
  const loadTitles = useCallback(async () => { try { const r = await api.get('/arcade/titles'); setTitles(r.data); } catch {} }, [api]);

  useEffect(() => { loadGames(); loadStats(); loadVs(); loadStreak(); loadTitles(); }, [loadGames, loadStats, loadVs, loadStreak, loadTitles]);

  const loadLeaderboard = useCallback(async (gid, per) => { try { const r = await api.get(`/arcade/leaderboard/${gid}?period=${per}`); setLeaderboard(r.data); } catch {} }, [api]);
  const loadGlobalLb = useCallback(async () => { try { const r = await api.get('/arcade/leaderboard-global'); setGlobalLb(r.data); } catch {} }, [api]);
  useEffect(() => { if (tab === 'classifica') { loadLeaderboard(lbGame, lbPeriod); loadGlobalLb(); } }, [tab, lbGame, lbPeriod, loadLeaderboard, loadGlobalLb]);

  const setGameStatus = async (s) => { try { await api.post('/arcade/status', { status: s }); } catch {} };

  const startSolo = (gameId) => { setPlaying(gameId); setLastResult(null); setGameStatus('playing'); };
  const exitSolo = () => { setPlaying(null); setLastResult(null); setGameStatus('idle'); };

  const onSoloComplete = async (score) => {
    setGameStatus('idle');
    try {
      const res = await api.post('/arcade/solo/submit', { game_id: playing, score });
      setLastResult(res.data);
      loadStats(); loadTitles();
      if (res.data.is_new_best) toast.success(`Nuovo record: ${score}!`);
      if (res.data.new_title) toast.success(`Nuovo titolo: ${res.data.new_title}!`);
      if (res.data.reward) {
        const r = res.data.reward;
        const p = []; if (r.hype) p.push(`+${r.hype} hype`); if (r.xp) p.push(`+${r.xp} XP`); if (r.funds) p.push(`+$${r.funds.toLocaleString()}`);
        if (p.length) toast(p.join(' | '));
      }
    } catch { toast.error('Errore salvataggio'); }
  };

  const startVsCreate = (gameId) => { setVsPlaying(gameId); setVsRole('creator'); setVsChallengeId(null); setVsResult(null); setGameStatus('in_vs'); };
  const onVsCreatorComplete = async (score) => {
    try {
      const cr = await api.post('/arcade/vs/create', { game_id: vsPlaying, bet: 0 });
      await api.post(`/arcade/vs/${cr.data.challenge_id}/submit-creator`, { score });
      setVsChallengeId(cr.data.challenge_id); setVsResult({ status: 'waiting', score }); setGameStatus('idle');
      toast.success(`Punteggio ${score} registrato!`); loadVs();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); setGameStatus('idle'); }
  };
  const joinVs = (c) => { setVsPlaying(c.game_id); setVsRole('opponent'); setVsChallengeId(c.id); setVsResult(null); setGameStatus('in_vs'); };
  const onVsOpponentComplete = async (score) => {
    setGameStatus('idle');
    try {
      const res = await api.post(`/arcade/vs/${vsChallengeId}/submit-opponent`, { score });
      setVsResult(res.data); loadVs(); loadStreak();
      if (res.data.streak?.milestone_reward) toast.success(`Streak x${res.data.streak.streak}! +$${res.data.streak.milestone_reward.toLocaleString()}`);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };
  const closeVs = () => { setVsPlaying(null); setVsChallengeId(null); setVsRole(null); setVsResult(null); setGameStatus('idle'); };

  // === PLAYING SOLO ===
  if (playing) {
    const GameComp = GAME_COMPONENTS[playing];
    const gameName = games.find(g => g.id === playing)?.name || playing;
    return (
      <div className="max-w-md mx-auto px-3 pt-14 pb-20" data-testid="solo-playing">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-gray-400">Solo — {gameName}</p>
          <Button variant="ghost" size="sm" className="text-[10px] text-gray-500 h-6" onClick={exitSolo}>Esci</Button>
        </div>
        {!lastResult ? (
          <Card className="bg-[#1A1A1B] border-gray-800"><CardContent className="p-3">
            <GameComp mode="solo" onComplete={onSoloComplete} />
          </CardContent></Card>
        ) : (
          <Card className="bg-[#1A1A1B] border-gray-800">
            <CardContent className="p-5 text-center space-y-3">
              <Trophy className={`w-10 h-10 mx-auto ${lastResult.is_new_best ? 'text-yellow-400' : 'text-gray-400'}`} />
              <p className="text-3xl font-black text-white">{lastResult.score}</p>
              {lastResult.is_new_best && <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">Nuovo Record!</Badge>}
              <p className="text-xs text-gray-400">Record: {lastResult.best_score}</p>
              {lastResult.reward && (
                <div className="flex justify-center gap-3 text-[10px]">
                  {lastResult.reward.hype > 0 && <span className="text-pink-400">+{lastResult.reward.hype} hype</span>}
                  {lastResult.reward.xp > 0 && <span className="text-blue-400">+{lastResult.reward.xp} XP</span>}
                  {lastResult.reward.funds > 0 && <span className="text-green-400">+${lastResult.reward.funds.toLocaleString()}</span>}
                </div>
              )}
              {!lastResult.reward && <p className="text-[10px] text-gray-600">Reward in cooldown</p>}
              {lastResult.new_title && <p className="text-xs text-yellow-400 flex items-center justify-center gap-1"><Award className="w-3.5 h-3.5" />{lastResult.new_title}</p>}
              <div className="flex gap-2 pt-1">
                <Button className="flex-1 bg-cyan-700 hover:bg-cyan-800 h-9" onClick={() => setLastResult(null)} data-testid="replay-btn"><Play className="w-3.5 h-3.5 mr-1" />Rigioca</Button>
                <Button variant="outline" className="flex-1 border-gray-700 h-9" onClick={exitSolo}>Esci</Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // === PLAYING VS ===
  if (vsPlaying) {
    const GameComp = GAME_COMPONENTS[vsPlaying];
    const gameName = games.find(g => g.id === vsPlaying)?.name || vsPlaying;
    const onComplete = vsRole === 'creator' ? onVsCreatorComplete : onVsOpponentComplete;
    return (
      <div className="max-w-md mx-auto px-3 pt-14 pb-20" data-testid="vs-playing">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-cyan-400">VS 1v1 — {gameName}</p>
          <Button variant="ghost" size="sm" className="text-[10px] text-gray-500 h-6" onClick={closeVs}>Esci</Button>
        </div>
        {!vsResult ? (
          <Card className="bg-[#1A1A1B] border-cyan-500/20"><CardContent className="p-3">
            <GameComp mode="vs" onComplete={onComplete} />
          </CardContent></Card>
        ) : vsResult.status === 'waiting' ? (
          <Card className="bg-[#1A1A1B] border-yellow-500/20">
            <CardContent className="p-5 text-center space-y-3">
              <Clock className="w-8 h-8 mx-auto text-yellow-400 animate-pulse" />
              <p className="text-lg font-bold">Punteggio: {vsResult.score}</p>
              <p className="text-xs text-yellow-400">In attesa di un avversario...</p>
              <Button variant="outline" className="border-gray-700 h-8 text-xs" onClick={closeVs}>Torna</Button>
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-[#1A1A1B] border-gray-800">
            <CardContent className="p-5 text-center space-y-3">
              <Trophy className={`w-10 h-10 mx-auto ${vsResult.winner_id === user?.id ? 'text-yellow-400' : vsResult.winner_id === 'draw' ? 'text-gray-400' : 'text-red-400'}`} />
              <p className="text-xl font-black">{vsResult.winner_id === user?.id ? 'HAI VINTO!' : vsResult.winner_id === 'draw' ? 'PAREGGIO!' : 'HAI PERSO!'}</p>
              <div className="flex justify-center gap-6">
                <div><p className="text-[10px] text-gray-400">{vsResult.creator_nickname}</p><p className="text-lg font-bold text-cyan-400">{vsResult.creator_score}</p></div>
                <span className="self-center text-gray-600 font-bold text-xs">VS</span>
                <div><p className="text-[10px] text-gray-400">{vsResult.opponent_nickname}</p><p className="text-lg font-bold text-purple-400">{vsResult.score}</p></div>
              </div>
              {vsResult.streak && vsResult.streak.streak >= 3 && (
                <p className="text-xs text-orange-400 flex items-center justify-center gap-1"><Flame className="w-3.5 h-3.5" />Streak x{vsResult.streak.streak}!</p>
              )}
              <Button variant="outline" className="border-gray-700 h-8 text-xs" onClick={closeVs}>Torna</Button>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // === MAIN PAGE ===
  return (
    <div className="max-w-lg mx-auto px-3 pt-14 pb-20 space-y-2" data-testid="minigiochi-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Gamepad2 className="w-5 h-5 text-cyan-400" />
          <h1 className="text-lg font-bold">Minigiochi + Sfide</h1>
        </div>
        <div className="flex items-center gap-2">
          {streak.streak > 0 && <StreakBadge streak={streak.streak} />}
          <p className="text-[9px] text-gray-500">{streak.wins}W/{streak.losses}L</p>
        </div>
      </div>

      {/* Titles */}
      {titles.length > 0 && (
        <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
          {titles.map(t => (
            <span key={t.game_id} className="shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-[9px] text-yellow-400 font-medium">
              <Award className="w-2.5 h-2.5" />{t.title}
            </span>
          ))}
        </div>
      )}

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="w-full grid grid-cols-5 h-8">
          <TabsTrigger value="solo" className="text-[9px] px-1" data-testid="tab-solo"><Play className="w-3 h-3 mr-0.5 hidden sm:block" />Solo</TabsTrigger>
          <TabsTrigger value="vs" className="text-[9px] px-1" data-testid="tab-vs"><Swords className="w-3 h-3 mr-0.5 hidden sm:block" />VS Mini</TabsTrigger>
          <TabsTrigger value="1vs1" className="text-[9px] px-1" data-testid="tab-1vs1"><Swords className="w-3 h-3 mr-0.5 hidden sm:block" />1v1 Film</TabsTrigger>
          <TabsTrigger value="classifica" className="text-[9px] px-1" data-testid="tab-classifica"><Crown className="w-3 h-3 mr-0.5 hidden sm:block" />Top</TabsTrigger>
          <TabsTrigger value="stats" className="text-[9px] px-1" data-testid="tab-stats"><BarChart3 className="w-3 h-3 mr-0.5 hidden sm:block" />Stats</TabsTrigger>
        </TabsList>

        {/* ===== SOLO ===== */}
        <TabsContent value="solo">
          <div className="grid grid-cols-2 gap-2">
            {games.map(g => {
              const Icon = GAME_ICONS[g.id] || Gamepad2;
              const st = stats[g.id];
              const hasReward = !st || st.reward_ready !== false;
              return (
                <Card key={g.id} className={`bg-[#1A1A1B] border-gray-800 active:scale-[0.97] transition-all ${g.bonus ? 'border-yellow-500/10' : ''}`}
                  onClick={() => startSolo(g.id)} data-testid={`solo-game-${g.id}`}>
                  <CardContent className="p-2.5 space-y-1">
                    <div className="flex items-center gap-2">
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${g.bonus ? 'bg-yellow-500/20' : 'bg-cyan-500/15'}`}>
                        <Icon className={`w-3.5 h-3.5 ${g.bonus ? 'text-yellow-400' : 'text-cyan-400'}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold truncate">{g.name}</p>
                        {g.bonus && <Badge className="bg-yellow-500/20 text-yellow-400 text-[7px] px-0.5 h-3">BONUS</Badge>}
                      </div>
                      {hasReward && <Gift className="w-3 h-3 text-green-400 shrink-0" />}
                    </div>
                    <p className="text-[9px] text-gray-500 line-clamp-1">{g.desc}</p>
                    {st ? <p className="text-[9px] text-cyan-400">Best: {st.best} | {st.plays}x</p> : <p className="text-[9px] text-gray-600">Mai giocato</p>}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* ===== VS MINIGIOCHI ===== */}
        <TabsContent value="vs">
          {(streak.streak > 0 || streak.best_streak > 0) && (
            <Card className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border-orange-500/20 mb-2">
              <CardContent className="p-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Flame className="w-4 h-4 text-orange-400" />
                  <div><p className="text-xs font-bold">Streak: {streak.streak}</p><p className="text-[9px] text-gray-400">Record: {streak.best_streak} | {streak.wins}W {streak.losses}L</p></div>
                </div>
                <StreakBadge streak={streak.streak} />
              </CardContent>
            </Card>
          )}
          <Tabs value={vsTab} onValueChange={setVsTab}>
            <TabsList className="w-full grid grid-cols-3 h-7 mb-2">
              <TabsTrigger value="create" className="text-[10px]" data-testid="vs-create-tab">Lancia</TabsTrigger>
              <TabsTrigger value="open" className="text-[10px]" data-testid="vs-open-tab">Aperte{pendingVs.length > 0 && <Badge className="ml-1 bg-cyan-500 text-[8px] px-1 h-3.5">{pendingVs.length}</Badge>}</TabsTrigger>
              <TabsTrigger value="history" className="text-[10px]" data-testid="vs-history-tab">Storico</TabsTrigger>
            </TabsList>
            <TabsContent value="create">
              <div className="grid grid-cols-2 gap-1.5">
                {games.map(g => {
                  const Icon = GAME_ICONS[g.id] || Gamepad2;
                  return (
                    <Card key={g.id} className="bg-gradient-to-br from-cyan-500/5 to-purple-500/5 border-cyan-500/15 active:scale-[0.97] transition-all"
                      onClick={() => startVsCreate(g.id)} data-testid={`vs-create-${g.id}`}>
                      <CardContent className="p-2 flex items-center gap-2">
                        <div className="w-6 h-6 rounded-lg bg-cyan-500/15 flex items-center justify-center shrink-0"><Icon className="w-3 h-3 text-cyan-400" /></div>
                        <p className="text-[11px] font-semibold truncate flex-1">{g.name}</p>
                        <Swords className="w-3 h-3 text-cyan-500/40 shrink-0" />
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>
            <TabsContent value="open">
              {pendingVs.length === 0 ? (
                <Card className="bg-[#1A1A1B] border-gray-800"><CardContent className="p-6 text-center text-gray-500"><Swords className="w-6 h-6 mx-auto mb-1.5 opacity-30" /><p className="text-xs">Nessuna sfida aperta</p></CardContent></Card>
              ) : pendingVs.map(vs => (
                <Card key={vs.id} className="bg-[#1A1A1B] border-cyan-500/15 mb-1.5" data-testid={`vs-pending-${vs.id}`}>
                  <CardContent className="p-2.5 flex items-center justify-between">
                    <div><p className="text-xs font-semibold">{vs.game_name}</p><p className="text-[10px] text-gray-400">{vs.creator_nickname} — {vs.creator_score}</p></div>
                    <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700 text-[10px] h-7" onClick={() => joinVs(vs)}>Accetta</Button>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
            <TabsContent value="history">
              {myVs.length === 0 ? (
                <Card className="bg-[#1A1A1B] border-gray-800"><CardContent className="p-6 text-center text-gray-500"><p className="text-xs">Nessuna sfida</p></CardContent></Card>
              ) : myVs.slice(0, 20).map(vs => {
                const isC = vs.creator_id === user?.id;
                const myS = isC ? vs.creator_score : vs.opponent_score;
                const opS = isC ? vs.opponent_score : vs.creator_score;
                const opN = isC ? vs.opponent_nickname : vs.creator_nickname;
                const won = vs.winner_id === user?.id;
                const draw = vs.winner_id === 'draw';
                return (
                  <Card key={vs.id} className={`bg-[#1A1A1B] mb-1 ${vs.status === 'completed' ? (won ? 'border-green-500/20' : draw ? 'border-yellow-500/20' : 'border-red-500/20') : 'border-gray-800'}`}>
                    <CardContent className="p-2 flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-1">
                          <p className="text-[11px] font-semibold">{vs.game_name}</p>
                          <Badge className={`text-[8px] px-0.5 h-3.5 ${vs.status === 'waiting' ? 'bg-yellow-500/20 text-yellow-400' : vs.status === 'completed' ? (won ? 'bg-green-500/20 text-green-400' : draw ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400') : 'bg-blue-500/20 text-blue-400'}`}>
                            {vs.status === 'waiting' ? 'Attesa' : vs.status === 'completed' ? (won ? 'W' : draw ? 'D' : 'L') : '...'}
                          </Badge>
                        </div>
                        {vs.status === 'completed' && opN && <p className="text-[9px] text-gray-500">vs {opN} | {myS ?? '?'}-{opS ?? '?'}</p>}
                        {vs.status === 'waiting' && <p className="text-[9px] text-gray-500">Score: {myS}</p>}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </TabsContent>
          </Tabs>
        </TabsContent>

        {/* ===== 1VS1 CLASSICO (FILM) ===== */}
        <TabsContent value="1vs1">
          <ChallengesPage embedded />
        </TabsContent>

        {/* ===== CLASSIFICHE ===== */}
        <TabsContent value="classifica">
          <div className="space-y-2">
            <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
              <Button size="sm" variant={lbGame === 'global' ? 'default' : 'outline'} className="text-[9px] h-6 shrink-0 px-2" onClick={() => { setLbGame('global'); loadGlobalLb(); }} data-testid="lb-global">Globale</Button>
              {games.slice(0, 8).map(g => (
                <Button key={g.id} size="sm" variant={lbGame === g.id ? 'default' : 'outline'} className="text-[9px] h-6 shrink-0 border-gray-700 px-2" onClick={() => { setLbGame(g.id); loadLeaderboard(g.id, lbPeriod); }}>{g.name}</Button>
              ))}
            </div>
            {lbGame !== 'global' && (
              <div className="flex gap-1">
                <Button size="sm" variant={lbPeriod === 'all' ? 'default' : 'ghost'} className="text-[9px] h-5 px-2" onClick={() => setLbPeriod('all')}>Sempre</Button>
                <Button size="sm" variant={lbPeriod === 'week' ? 'default' : 'ghost'} className="text-[9px] h-5 px-2" onClick={() => setLbPeriod('week')}>Settimana</Button>
              </div>
            )}
            <div className="space-y-0.5">
              {(lbGame === 'global' ? globalLb : leaderboard).length === 0 ? (
                <Card className="bg-[#1A1A1B] border-gray-800"><CardContent className="p-5 text-center text-gray-500"><Crown className="w-6 h-6 mx-auto mb-1 opacity-30" /><p className="text-xs">Nessun dato</p></CardContent></Card>
              ) : (lbGame === 'global' ? globalLb : leaderboard).map((e, i) => (
                <Card key={e.user_id || i} className={`bg-[#1A1A1B] ${e.user_id === user?.id ? 'border-cyan-500/30' : 'border-gray-800/50'}`}>
                  <CardContent className="p-1.5 flex items-center gap-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 font-bold text-[10px] ${e.rank === 1 ? 'bg-yellow-500 text-black' : e.rank === 2 ? 'bg-gray-300 text-black' : e.rank === 3 ? 'bg-orange-600 text-white' : 'bg-gray-800 text-gray-400'}`}>{e.rank}</div>
                    <p className={`flex-1 text-xs font-semibold truncate ${e.user_id === user?.id ? 'text-cyan-400' : ''}`}>{e.nickname}</p>
                    <div className="text-right shrink-0">
                      <p className="text-xs font-bold text-yellow-400">{lbGame === 'global' ? e.total_score : e.best}</p>
                      <p className="text-[8px] text-gray-500">{lbGame === 'global' ? `${e.unique_games}g` : `${e.plays}x`}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* ===== STATS ===== */}
        <TabsContent value="stats">
          <div className="space-y-1.5">
            <Card className="bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border-cyan-500/20">
              <CardContent className="p-2.5">
                <div className="grid grid-cols-4 gap-2 text-center">
                  <div><p className="text-lg font-black text-cyan-400">{Object.keys(stats).length}</p><p className="text-[8px] text-gray-400">Giochi</p></div>
                  <div><p className="text-lg font-black text-yellow-400">{Object.values(stats).reduce((s, g) => s + g.plays, 0)}</p><p className="text-[8px] text-gray-400">Partite</p></div>
                  <div><p className="text-lg font-black text-orange-400">{streak.wins}</p><p className="text-[8px] text-gray-400">VS Vinte</p></div>
                  <div><p className="text-lg font-black text-purple-400">{titles.length}</p><p className="text-[8px] text-gray-400">Titoli</p></div>
                </div>
              </CardContent>
            </Card>
            {games.map(g => {
              const Icon = GAME_ICONS[g.id] || Gamepad2;
              const st = stats[g.id];
              const title = titles.find(t => t.game_id === g.id);
              const hasReward = !st || st.reward_ready !== false;
              return (
                <Card key={g.id} className="bg-[#1A1A1B] border-gray-800">
                  <CardContent className="p-2 flex items-center gap-2">
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${g.bonus ? 'bg-yellow-500/15' : 'bg-cyan-500/10'}`}>
                      <Icon className={`w-3.5 h-3.5 ${g.bonus ? 'text-yellow-400' : 'text-cyan-400'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1">
                        <p className="text-[11px] font-semibold">{g.name}</p>
                        {title && <Badge className="bg-yellow-500/15 text-yellow-400 text-[7px] px-1 h-3">{title.title}</Badge>}
                        {hasReward && <Gift className="w-2.5 h-2.5 text-green-400" />}
                      </div>
                      {st ? <div className="flex gap-2 text-[9px]"><span className="text-yellow-400">Best: {st.best}</span><span className="text-gray-400">Avg: {st.avg}</span><span className="text-gray-500">{st.plays}x</span></div> : <p className="text-[9px] text-gray-600">Mai giocato</p>}
                    </div>
                    <Button size="sm" variant="ghost" className="h-6 text-[9px] text-cyan-400 px-2" onClick={() => { startSolo(g.id); setTab('solo'); }}><Play className="w-3 h-3" /></Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
