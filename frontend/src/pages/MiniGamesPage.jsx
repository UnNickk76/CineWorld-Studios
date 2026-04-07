import React, { useState, useEffect, useContext, useCallback } from 'react';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy, Play, Gamepad2, BarChart3, Crown, Star, Swords,
  Film, Brain, Target, Zap, Timer, Camera, Sun, UserCheck,
  Scissors, Eye, Sparkles, ArrowLeft, Clock, Medal, Flame
} from 'lucide-react';
import {
  TapCiak, MemoryPro, StopPerfetto, SpamClick, ReactionGame,
  ShotPerfect, LightSetup, CastMatch, EditingCut, FollowCam,
  ChaosPremiere, ReelSnake
} from '../components/MiniGames';

const GAME_ICONS = {
  tap_ciak: Film, memory_pro: Brain, stop_perfetto: Target, spam_tap: Zap,
  reaction: Timer, shot_perfect: Camera, light_setup: Sun, cast_match: UserCheck,
  editing_cut: Scissors, follow_cam: Eye, chaos_premiere: Sparkles, reel_snake: Gamepad2,
};

const GAME_COMPONENTS = {
  tap_ciak: TapCiak, memory_pro: MemoryPro, stop_perfetto: StopPerfetto,
  spam_tap: SpamClick, reaction: ReactionGame, shot_perfect: ShotPerfect,
  light_setup: LightSetup, cast_match: CastMatch, editing_cut: EditingCut,
  follow_cam: FollowCam, chaos_premiere: ChaosPremiere, reel_snake: ReelSnake,
};

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

  const loadGames = useCallback(async () => {
    try {
      const res = await api.get('/arcade/games');
      setGames(res.data);
    } catch {}
  }, [api]);

  const loadStats = useCallback(async () => {
    try {
      const res = await api.get('/arcade/solo/stats');
      setStats(res.data);
    } catch {}
  }, [api]);

  const loadVs = useCallback(async () => {
    try {
      const [p, m] = await Promise.all([api.get('/arcade/vs/pending'), api.get('/arcade/vs/my')]);
      setPendingVs(p.data);
      setMyVs(m.data);
    } catch {}
  }, [api]);

  useEffect(() => { loadGames(); loadStats(); loadVs(); }, [loadGames, loadStats, loadVs]);

  const loadLeaderboard = useCallback(async (gid, per) => {
    try {
      const res = await api.get(`/arcade/leaderboard/${gid}?period=${per}`);
      setLeaderboard(res.data);
    } catch {}
  }, [api]);

  const loadGlobalLb = useCallback(async () => {
    try {
      const res = await api.get('/arcade/leaderboard-global');
      setGlobalLb(res.data);
    } catch {}
  }, [api]);

  useEffect(() => { if (tab === 'classifica') { loadLeaderboard(lbGame, lbPeriod); loadGlobalLb(); } }, [tab, lbGame, lbPeriod, loadLeaderboard, loadGlobalLb]);

  const onSoloComplete = async (score) => {
    try {
      const res = await api.post('/arcade/solo/submit', { game_id: playing, score });
      setLastResult(res.data);
      loadStats();
      if (res.data.is_new_best) toast.success(`Nuovo record: ${score}!`);
      else toast(`Punteggio: ${score}`);
    } catch { toast.error('Errore salvataggio'); }
  };

  const startVsCreate = (gameId) => {
    setVsPlaying(gameId);
    setVsRole('creator');
    setVsChallengeId(null);
    setVsResult(null);
  };

  const onVsCreatorComplete = async (score) => {
    try {
      const createRes = await api.post('/arcade/vs/create', { game_id: vsPlaying, bet: 0 });
      const cid = createRes.data.challenge_id;
      await api.post(`/arcade/vs/${cid}/submit-creator`, { score });
      setVsChallengeId(cid);
      setVsResult({ status: 'waiting', score });
      toast.success(`Punteggio ${score} registrato! In attesa di un avversario...`);
      loadVs();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const joinVs = (challenge) => {
    setVsPlaying(challenge.game_id);
    setVsRole('opponent');
    setVsChallengeId(challenge.id);
    setVsResult(null);
  };

  const onVsOpponentComplete = async (score) => {
    try {
      const res = await api.post(`/arcade/vs/${vsChallengeId}/submit-opponent`, { score });
      setVsResult(res.data);
      loadVs();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const closeVs = () => { setVsPlaying(null); setVsChallengeId(null); setVsRole(null); setVsResult(null); };

  // Playing solo minigame
  if (playing) {
    const GameComp = GAME_COMPONENTS[playing];
    const gameName = games.find(g => g.id === playing)?.name || playing;
    return (
      <div className="max-w-md mx-auto px-3 pt-4 pb-32" data-testid="solo-playing">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm text-gray-400">Solo — {gameName}</p>
          <Button variant="ghost" size="sm" className="text-xs text-gray-500" onClick={() => { setPlaying(null); setLastResult(null); }}>Esci</Button>
        </div>
        {!lastResult ? (
          <Card className="bg-[#1A1A1B] border-gray-800"><CardContent className="p-3">
            <GameComp mode="solo" onComplete={onSoloComplete} />
          </CardContent></Card>
        ) : (
          <Card className="bg-[#1A1A1B] border-gray-800">
            <CardContent className="p-6 text-center space-y-4">
              <Trophy className={`w-12 h-12 mx-auto ${lastResult.is_new_best ? 'text-yellow-400' : 'text-gray-400'}`} />
              <p className="text-3xl font-black text-white">{lastResult.score}</p>
              {lastResult.is_new_best && <Badge className="bg-yellow-500/20 text-yellow-400">Nuovo Record!</Badge>}
              <p className="text-sm text-gray-400">Record: {lastResult.best_score}</p>
              <div className="flex gap-2">
                <Button className="flex-1 bg-cyan-700 hover:bg-cyan-800" onClick={() => setLastResult(null)} data-testid="replay-btn"><Play className="w-4 h-4 mr-1" /> Rigioca</Button>
                <Button variant="outline" className="flex-1 border-gray-700" onClick={() => { setPlaying(null); setLastResult(null); }}>Esci</Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // Playing VS minigame
  if (vsPlaying) {
    const GameComp = GAME_COMPONENTS[vsPlaying];
    const gameName = games.find(g => g.id === vsPlaying)?.name || vsPlaying;
    const onComplete = vsRole === 'creator' ? onVsCreatorComplete : onVsOpponentComplete;
    return (
      <div className="max-w-md mx-auto px-3 pt-4 pb-32" data-testid="vs-playing">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm text-cyan-400">VS 1v1 — {gameName}</p>
          <Button variant="ghost" size="sm" className="text-xs text-gray-500" onClick={closeVs}>Esci</Button>
        </div>
        {!vsResult ? (
          <Card className="bg-[#1A1A1B] border-cyan-500/20"><CardContent className="p-3">
            <GameComp mode="vs" onComplete={onComplete} />
          </CardContent></Card>
        ) : vsResult.status === 'waiting' ? (
          <Card className="bg-[#1A1A1B] border-yellow-500/20">
            <CardContent className="p-6 text-center space-y-3">
              <Clock className="w-10 h-10 mx-auto text-yellow-400 animate-pulse" />
              <p className="text-xl font-bold text-white">Punteggio: {vsResult.score}</p>
              <p className="text-sm text-yellow-400">In attesa di un avversario...</p>
              <Button variant="outline" className="border-gray-700" onClick={closeVs}>Torna ai Minigiochi</Button>
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-[#1A1A1B] border-gray-800">
            <CardContent className="p-6 text-center space-y-4">
              <Trophy className={`w-12 h-12 mx-auto ${vsResult.winner_id === user?.id ? 'text-yellow-400' : vsResult.winner_id === 'draw' ? 'text-gray-400' : 'text-red-400'}`} />
              <p className="text-2xl font-black">{vsResult.winner_id === user?.id ? 'HAI VINTO!' : vsResult.winner_id === 'draw' ? 'PAREGGIO!' : 'HAI PERSO!'}</p>
              <div className="flex justify-center gap-6">
                <div><p className="text-xs text-gray-400">{vsResult.creator_nickname}</p><p className="text-xl font-bold text-cyan-400">{vsResult.creator_score}</p></div>
                <span className="self-center text-gray-600 font-bold">VS</span>
                <div><p className="text-xs text-gray-400">{vsResult.opponent_nickname}</p><p className="text-xl font-bold text-purple-400">{vsResult.score}</p></div>
              </div>
              {vsResult.pot > 0 && vsResult.winner_id === user?.id && <p className="text-lg text-yellow-400 font-bold">+${vsResult.pot.toLocaleString()}</p>}
              <Button variant="outline" className="border-gray-700" onClick={closeVs}>Torna ai Minigiochi</Button>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto px-3 pt-2 pb-32 space-y-3" data-testid="minigiochi-page">
      <div className="flex items-center gap-2 mb-1">
        <Gamepad2 className="w-6 h-6 text-cyan-400" />
        <h1 className="text-xl font-bold">Minigiochi</h1>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="w-full grid grid-cols-4 h-9">
          <TabsTrigger value="solo" className="text-xs" data-testid="tab-solo"><Play className="w-3 h-3 mr-1" />Solo</TabsTrigger>
          <TabsTrigger value="vs" className="text-xs" data-testid="tab-vs"><Swords className="w-3 h-3 mr-1" />VS 1v1</TabsTrigger>
          <TabsTrigger value="classifica" className="text-xs" data-testid="tab-classifica"><Crown className="w-3 h-3 mr-1" />Classifica</TabsTrigger>
          <TabsTrigger value="stats" className="text-xs" data-testid="tab-stats"><BarChart3 className="w-3 h-3 mr-1" />Stats</TabsTrigger>
        </TabsList>

        {/* SOLO TAB */}
        <TabsContent value="solo">
          <div className="grid grid-cols-2 gap-2">
            {games.map(g => {
              const Icon = GAME_ICONS[g.id] || Gamepad2;
              const st = stats[g.id];
              return (
                <Card key={g.id} className={`bg-[#1A1A1B] border-gray-800 cursor-pointer hover:border-cyan-500/30 transition-colors ${g.bonus ? 'border-yellow-500/10' : ''}`}
                  onClick={() => { setPlaying(g.id); setLastResult(null); }} data-testid={`solo-game-${g.id}`}>
                  <CardContent className="p-3 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${g.bonus ? 'bg-yellow-500/20' : 'bg-cyan-500/15'}`}>
                        <Icon className={`w-4 h-4 ${g.bonus ? 'text-yellow-400' : 'text-cyan-400'}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold truncate">{g.name}</p>
                        {g.bonus && <Badge className="bg-yellow-500/20 text-yellow-400 text-[8px] px-1 h-4">BONUS</Badge>}
                      </div>
                    </div>
                    <p className="text-[10px] text-gray-500 line-clamp-1">{g.desc}</p>
                    {st && <p className="text-[10px] text-cyan-400">Record: {st.best} | {st.plays}x</p>}
                    {!st && <p className="text-[10px] text-gray-600">Mai giocato</p>}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* VS 1v1 TAB */}
        <TabsContent value="vs">
          <Tabs value={vsTab} onValueChange={setVsTab}>
            <TabsList className="w-full grid grid-cols-3 h-8 mb-2">
              <TabsTrigger value="create" className="text-[11px]" data-testid="vs-create-tab">Lancia</TabsTrigger>
              <TabsTrigger value="open" className="text-[11px]" data-testid="vs-open-tab">Aperte {pendingVs.length > 0 && <Badge className="ml-1 bg-cyan-500 text-[9px] px-1">{pendingVs.length}</Badge>}</TabsTrigger>
              <TabsTrigger value="history" className="text-[11px]" data-testid="vs-history-tab">Storico</TabsTrigger>
            </TabsList>
            <TabsContent value="create">
              <div className="grid grid-cols-2 gap-2">
                {games.map(g => {
                  const Icon = GAME_ICONS[g.id] || Gamepad2;
                  return (
                    <Card key={g.id} className="bg-gradient-to-br from-cyan-500/5 to-purple-500/5 border-cyan-500/15 cursor-pointer hover:border-cyan-500/40 transition-colors"
                      onClick={() => startVsCreate(g.id)} data-testid={`vs-create-${g.id}`}>
                      <CardContent className="p-2.5 flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-cyan-500/15 flex items-center justify-center shrink-0"><Icon className="w-3.5 h-3.5 text-cyan-400" /></div>
                        <div className="flex-1 min-w-0"><p className="text-xs font-semibold truncate">{g.name}</p><p className="text-[9px] text-gray-500">VS 1v1</p></div>
                        <Swords className="w-3 h-3 text-cyan-500/40 shrink-0" />
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>
            <TabsContent value="open">
              {pendingVs.length === 0 ? (
                <Card className="bg-[#1A1A1B] border-gray-800"><CardContent className="p-8 text-center text-gray-500">
                  <Swords className="w-8 h-8 mx-auto mb-2 opacity-30" /><p className="text-sm">Nessuna sfida aperta</p>
                </CardContent></Card>
              ) : pendingVs.map(vs => (
                <Card key={vs.id} className="bg-[#1A1A1B] border-cyan-500/15 mb-2" data-testid={`vs-pending-${vs.id}`}>
                  <CardContent className="p-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold">{vs.game_name}</p>
                      <p className="text-xs text-gray-400">{vs.creator_nickname} — Punteggio: {vs.creator_score}</p>
                    </div>
                    <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700 text-xs" onClick={() => joinVs(vs)} data-testid={`vs-join-${vs.id}`}>Accetta</Button>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
            <TabsContent value="history">
              {myVs.length === 0 ? (
                <Card className="bg-[#1A1A1B] border-gray-800"><CardContent className="p-8 text-center text-gray-500">
                  <p className="text-sm">Nessuna sfida giocata</p>
                </CardContent></Card>
              ) : myVs.slice(0, 20).map(vs => {
                const isCreator = vs.creator_id === user?.id;
                const myScore = isCreator ? vs.creator_score : vs.opponent_score;
                const oppScore = isCreator ? vs.opponent_score : vs.creator_score;
                const oppName = isCreator ? vs.opponent_nickname : vs.creator_nickname;
                const won = vs.winner_id === user?.id;
                const draw = vs.winner_id === 'draw';
                return (
                  <Card key={vs.id} className={`bg-[#1A1A1B] mb-1.5 ${vs.status === 'completed' ? (won ? 'border-green-500/20' : draw ? 'border-yellow-500/20' : 'border-red-500/20') : 'border-gray-800'}`}>
                    <CardContent className="p-2.5 flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <p className="text-xs font-semibold">{vs.game_name}</p>
                          <Badge className={`text-[9px] px-1 h-4 ${
                            vs.status === 'waiting' ? 'bg-yellow-500/20 text-yellow-400' :
                            vs.status === 'completed' ? (won ? 'bg-green-500/20 text-green-400' : draw ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400') :
                            'bg-blue-500/20 text-blue-400'
                          }`}>
                            {vs.status === 'waiting' ? 'In attesa' : vs.status === 'completed' ? (won ? 'Vittoria' : draw ? 'Pareggio' : 'Sconfitta') : 'In corso'}
                          </Badge>
                        </div>
                        {vs.status === 'completed' && oppName && <p className="text-[10px] text-gray-500">VS {oppName} | {myScore ?? '?'} vs {oppScore ?? '?'}</p>}
                        {vs.status === 'waiting' && <p className="text-[10px] text-gray-500">Punteggio: {myScore} — In attesa...</p>}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </TabsContent>
          </Tabs>
        </TabsContent>

        {/* CLASSIFICA TAB */}
        <TabsContent value="classifica">
          <div className="space-y-3">
            <div className="flex gap-2 overflow-x-auto pb-1">
              <Button size="sm" variant={lbGame === 'global' ? 'default' : 'outline'} className="text-[10px] h-7 shrink-0" onClick={() => { setLbGame('global'); loadGlobalLb(); }} data-testid="lb-global">Globale</Button>
              {games.slice(0, 6).map(g => (
                <Button key={g.id} size="sm" variant={lbGame === g.id ? 'default' : 'outline'} className="text-[10px] h-7 shrink-0 border-gray-700" onClick={() => { setLbGame(g.id); loadLeaderboard(g.id, lbPeriod); }}>{g.name}</Button>
              ))}
            </div>
            {lbGame !== 'global' && (
              <div className="flex gap-1">
                <Button size="sm" variant={lbPeriod === 'all' ? 'default' : 'ghost'} className="text-[10px] h-6" onClick={() => setLbPeriod('all')}>Sempre</Button>
                <Button size="sm" variant={lbPeriod === 'week' ? 'default' : 'ghost'} className="text-[10px] h-6" onClick={() => setLbPeriod('week')}>Settimana</Button>
              </div>
            )}
            <div className="space-y-1">
              {(lbGame === 'global' ? globalLb : leaderboard).length === 0 ? (
                <Card className="bg-[#1A1A1B] border-gray-800"><CardContent className="p-6 text-center text-gray-500">
                  <Crown className="w-8 h-8 mx-auto mb-2 opacity-30" /><p className="text-sm">Nessun dato disponibile</p>
                </CardContent></Card>
              ) : (lbGame === 'global' ? globalLb : leaderboard).map((entry, i) => (
                <Card key={entry.user_id || i} className={`bg-[#1A1A1B] ${entry.user_id === user?.id ? 'border-cyan-500/30' : 'border-gray-800/50'}`}>
                  <CardContent className="p-2 flex items-center gap-2">
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 font-bold text-xs ${
                      entry.rank === 1 ? 'bg-yellow-500 text-black' : entry.rank === 2 ? 'bg-gray-300 text-black' : entry.rank === 3 ? 'bg-orange-600 text-white' : 'bg-gray-800 text-gray-400'
                    }`}>{entry.rank}</div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-semibold truncate ${entry.user_id === user?.id ? 'text-cyan-400' : ''}`}>{entry.nickname}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-bold text-yellow-400">{lbGame === 'global' ? entry.total_score : entry.best}</p>
                      <p className="text-[9px] text-gray-500">{lbGame === 'global' ? `${entry.unique_games} giochi` : `${entry.plays}x`}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* STATS TAB */}
        <TabsContent value="stats">
          <div className="space-y-2">
            {games.map(g => {
              const Icon = GAME_ICONS[g.id] || Gamepad2;
              const st = stats[g.id];
              return (
                <Card key={g.id} className="bg-[#1A1A1B] border-gray-800">
                  <CardContent className="p-2.5 flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${g.bonus ? 'bg-yellow-500/15' : 'bg-cyan-500/10'}`}>
                      <Icon className={`w-4 h-4 ${g.bonus ? 'text-yellow-400' : 'text-cyan-400'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold">{g.name}</p>
                      {st ? (
                        <div className="flex gap-3 text-[10px]">
                          <span className="text-yellow-400">Record: {st.best}</span>
                          <span className="text-gray-400">Media: {st.avg}</span>
                          <span className="text-gray-500">{st.plays} partite</span>
                        </div>
                      ) : <p className="text-[10px] text-gray-600">Mai giocato</p>}
                    </div>
                    <Button size="sm" variant="ghost" className="h-7 text-[10px] text-cyan-400" onClick={() => { setPlaying(g.id); setLastResult(null); setTab('solo'); }}>
                      <Play className="w-3 h-3 mr-0.5" /> Gioca
                    </Button>
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
