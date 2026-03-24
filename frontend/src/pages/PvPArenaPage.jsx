import React, { useState, useEffect, useCallback, useContext } from 'react';
import { AuthContext, API } from '../contexts';
import { motion, AnimatePresence } from 'framer-motion';
import { Swords, Trophy, TrendingUp, Shield, Zap, DollarSign, Star, Clock, ChevronRight, Megaphone, Target, Users, Crown, BarChart3, Film, ArrowRight, Check, X, Sparkles } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';

export default function PvPArenaPage() {
  const { user, api } = useContext(AuthContext);
  const [tab, setTab] = useState('wars');
  const [stats, setStats] = useState(null);
  const [wars, setWars] = useState({ active: [], completed: [] });
  const [challenges, setChallenges] = useState({ active: [], completed: [] });
  const [challengeData, setChallengeData] = useState(null);
  const [showChallengeModal, setShowChallengeModal] = useState(false);
  const [selectedMyFilm, setSelectedMyFilm] = useState(null);
  const [selectedOppFilm, setSelectedOppFilm] = useState(null);
  const [marketingOptions, setMarketingOptions] = useState([]);
  const [showMarketingModal, setShowMarketingModal] = useState(null);
  const [loading, setLoading] = useState(false);
  const [leaderboard, setLeaderboard] = useState([]);

  const loadData = useCallback(async () => {
    try {
      const [statsRes, warsRes, challengesRes] = await Promise.all([
        api.get('/pvp-cinema/stats'),
        api.get('/pvp-cinema/wars'),
        api.get('/pvp-cinema/challenges'),
      ]);
      setStats(statsRes.data);
      setWars(warsRes.data);
      setChallenges(challengesRes.data);
    } catch (e) {
      console.error('Failed to load PvP data', e);
    }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  const openChallengeModal = async () => {
    try {
      const r = await api.get('/pvp-cinema/challengeable-films');
      setChallengeData(r.data);
      setShowChallengeModal(true);
    } catch (e) {
      console.error('Failed to load challengeable films', e);
    }
  };

  const launchChallenge = async () => {
    if (!selectedMyFilm || !selectedOppFilm) return;
    setLoading(true);
    try {
      await api.post('/pvp-cinema/challenge', {
        my_film_id: selectedMyFilm,
        opponent_film_id: selectedOppFilm,
      });
      setShowChallengeModal(false);
      setSelectedMyFilm(null);
      setSelectedOppFilm(null);
      loadData();
    } catch (e) {
      alert(e.response?.data?.detail || 'Errore');
    }
    setLoading(false);
  };

  const openMarketing = async (warId, filmId) => {
    try {
      const r = await api.get('/pvp-cinema/marketing-options');
      setMarketingOptions(r.data.options);
      setShowMarketingModal({ warId, filmId });
    } catch (e) {
      console.error(e);
    }
  };

  const applyBoost = async (boostType) => {
    if (!showMarketingModal) return;
    setLoading(true);
    try {
      await api.post('/pvp-cinema/marketing-boost', {
        war_id: showMarketingModal.warId,
        film_id: showMarketingModal.filmId,
        boost_type: boostType,
      });
      setShowMarketingModal(null);
      loadData();
    } catch (e) {
      alert(e.response?.data?.detail || 'Errore');
    }
    setLoading(false);
  };

  const loadLeaderboard = async () => {
    try {
      const r = await api.get('/pvp-cinema/leaderboard');
      setLeaderboard(r.data.leaderboard);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => { if (tab === 'leaderboard') loadLeaderboard(); }, [tab]);

  const tabs = [
    { id: 'wars', label: 'Box Office', icon: TrendingUp },
    { id: 'challenges', label: 'Testa a Testa', icon: Swords },
    { id: 'leaderboard', label: 'Classifica', icon: Trophy },
  ];

  const remainingTime = (endsAt) => {
    if (!endsAt) return '';
    const diff = new Date(endsAt) - new Date();
    if (diff <= 0) return 'Scaduto';
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    return `${h}h ${m}m`;
  };

  return (
    <div className="min-h-screen bg-[#0A0A0B] pb-20" data-testid="pvp-arena-page">
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-red-950/30 via-orange-950/15 to-transparent" />
        <div className="relative px-4 pt-6 pb-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
              <Swords className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Arena PvP</h1>
              <p className="text-xs text-gray-400">Combatti per il dominio del Box Office</p>
            </div>
          </div>

          {/* Stats Bar */}
          {stats && (
            <div className="grid grid-cols-4 gap-2" data-testid="pvp-stats-bar">
              <StatCard icon={<TrendingUp className="w-3.5 h-3.5" />} label="Guerre" value={stats.wars_won} sub={`/${stats.wars_total}`} color="orange" />
              <StatCard icon={<Swords className="w-3.5 h-3.5" />} label="Sfide" value={stats.challenges_won} sub={`/${stats.challenges_total}`} color="red" />
              <StatCard icon={<Zap className="w-3.5 h-3.5" />} label="Attive" value={stats.active_wars + stats.active_challenges} color="yellow" />
              <StatCard icon={<BarChart3 className="w-3.5 h-3.5" />} label="Win%" value={`${stats.challenges_win_rate}`} color="green" />
            </div>
          )}
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 px-4 mb-4">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${tab === t.id ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-white/5 text-gray-500 border border-transparent'}`}
            data-testid={`pvp-tab-${t.id}`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
          </button>
        ))}
      </div>

      <div className="px-4 space-y-4">
        {/* BOX OFFICE WARS TAB */}
        {tab === 'wars' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            <p className="text-xs text-gray-500">Le guerre si attivano automaticamente quando film dello stesso genere escono nello stesso periodo.</p>
            
            {wars.active.length === 0 && wars.completed.length === 0 && (
              <div className="text-center py-12 text-gray-600">
                <TrendingUp className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Nessuna guerra al box office attiva</p>
                <p className="text-xs text-gray-700 mt-1">Rilascia un film per competere!</p>
              </div>
            )}

            {wars.active.map(war => (
              <WarCard key={war.id} war={war} userId={user?.id} remainingTime={remainingTime} onMarketing={openMarketing} />
            ))}

            {wars.completed.length > 0 && (
              <div className="mt-4">
                <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Guerre Concluse</h3>
                {wars.completed.map(war => (
                  <WarCard key={war.id} war={war} userId={user?.id} completed />
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* TESTA A TESTA TAB */}
        {tab === 'challenges' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            <Button
              onClick={openChallengeModal}
              className="w-full bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white py-3 rounded-xl font-semibold"
              data-testid="launch-challenge-btn"
            >
              <Swords className="w-4 h-4 mr-2" /> Lancia Sfida Testa a Testa
            </Button>

            {challenges.active.length === 0 && challenges.completed.length === 0 && (
              <div className="text-center py-10 text-gray-600">
                <Swords className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Nessuna sfida attiva</p>
                <p className="text-xs text-gray-700 mt-1">Sfida un altro produttore!</p>
              </div>
            )}

            {challenges.active.map(c => (
              <ChallengeCard key={c.id} challenge={c} userId={user?.id} remainingTime={remainingTime} />
            ))}

            {challenges.completed.length > 0 && (
              <div className="mt-4">
                <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Sfide Concluse</h3>
                {challenges.completed.map(c => (
                  <ChallengeCard key={c.id} challenge={c} userId={user?.id} completed />
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* LEADERBOARD TAB */}
        {tab === 'leaderboard' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
            {leaderboard.length === 0 && (
              <div className="text-center py-12 text-gray-600">
                <Trophy className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Nessun dato nella classifica</p>
              </div>
            )}
            {leaderboard.map((entry, i) => (
              <div key={entry.user_id} className={`flex items-center gap-3 p-3 rounded-xl border ${i === 0 ? 'bg-yellow-500/10 border-yellow-500/20' : i === 1 ? 'bg-gray-400/10 border-gray-400/20' : i === 2 ? 'bg-orange-500/10 border-orange-500/20' : 'bg-white/5 border-white/5'}`} data-testid={`leaderboard-entry-${i}`}>
                <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${i === 0 ? 'bg-yellow-500 text-black' : i === 1 ? 'bg-gray-400 text-black' : i === 2 ? 'bg-orange-500 text-black' : 'bg-white/10 text-gray-400'}`}>
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate">{entry.nickname}</p>
                  {entry.studio && <p className="text-[10px] text-gray-500 truncate">{entry.studio}</p>}
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-red-400">{entry.wins} <span className="text-[10px] text-gray-500">vittorie</span></p>
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </div>

      {/* Challenge Modal */}
      <Dialog open={showChallengeModal} onOpenChange={setShowChallengeModal}>
        <DialogContent className="bg-[#141416] border-white/10 max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Swords className="w-5 h-5 text-red-400" /> Lancia Sfida
            </DialogTitle>
          </DialogHeader>
          {challengeData && (
            <div className="space-y-4">
              <div>
                <p className="text-xs text-gray-400 mb-2 font-semibold uppercase">Il tuo film</p>
                {challengeData.my_films.length === 0 ? (
                  <p className="text-xs text-gray-600">Nessun film in sala. Rilascia un film prima!</p>
                ) : (
                  <div className="space-y-1.5">
                    {challengeData.my_films.map(f => (
                      <button
                        key={f.id}
                        onClick={() => setSelectedMyFilm(f.id)}
                        className={`w-full flex items-center gap-2 p-2.5 rounded-lg text-left transition-all ${selectedMyFilm === f.id ? 'bg-red-500/20 border border-red-500/40' : 'bg-white/5 border border-transparent hover:border-white/10'}`}
                        data-testid={`my-film-${f.id}`}
                      >
                        <Film className="w-4 h-4 text-yellow-400 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white truncate">{f.title}</p>
                          <p className="text-[10px] text-gray-500">{f.genre} &middot; Q:{f.quality_score}</p>
                        </div>
                        {selectedMyFilm === f.id && <Check className="w-4 h-4 text-red-400" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <p className="text-xs text-gray-400 mb-2 font-semibold uppercase">Film avversario</p>
                {challengeData.opponent_films.length === 0 ? (
                  <p className="text-xs text-gray-600">Nessun film avversario disponibile.</p>
                ) : (
                  <div className="space-y-1.5 max-h-48 overflow-y-auto">
                    {challengeData.opponent_films.map(f => (
                      <button
                        key={f.id}
                        onClick={() => setSelectedOppFilm(f.id)}
                        className={`w-full flex items-center gap-2 p-2.5 rounded-lg text-left transition-all ${selectedOppFilm === f.id ? 'bg-orange-500/20 border border-orange-500/40' : 'bg-white/5 border border-transparent hover:border-white/10'}`}
                        data-testid={`opp-film-${f.id}`}
                      >
                        <Target className="w-4 h-4 text-orange-400 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white truncate">{f.title}</p>
                          <p className="text-[10px] text-gray-500">{f.nickname} &middot; {f.genre} &middot; Q:{f.quality_score}</p>
                        </div>
                        {selectedOppFilm === f.id && <Check className="w-4 h-4 text-orange-400" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-xs text-gray-400 space-y-1">
                <p className="text-white font-semibold">Costo e Premi</p>
                <div className="flex justify-between"><span>Costo sfida:</span><span className="text-yellow-400">${challengeData.challenge_cost.funds?.toLocaleString()} + {challengeData.challenge_cost.cp} CP</span></div>
                <div className="flex justify-between"><span>Premio vincitore:</span><span className="text-green-400">${challengeData.prizes.winner_funds?.toLocaleString()} + {challengeData.prizes.winner_fame} Fama + {challengeData.prizes.winner_cp} CP</span></div>
                <div className="flex justify-between"><span>Penalita sconfitto:</span><span className="text-red-400">{challengeData.prizes.loser_fame} Fama</span></div>
              </div>

              <Button
                onClick={launchChallenge}
                disabled={!selectedMyFilm || !selectedOppFilm || loading}
                className="w-full bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 disabled:opacity-30"
                data-testid="confirm-challenge-btn"
              >
                {loading ? 'Lancio...' : 'Lancia Sfida!'}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Marketing Boost Modal */}
      <Dialog open={!!showMarketingModal} onOpenChange={() => setShowMarketingModal(null)}>
        <DialogContent className="bg-[#141416] border-white/10 max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Megaphone className="w-5 h-5 text-orange-400" /> Marketing Boost
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            {marketingOptions.map(opt => (
              <button
                key={opt.id}
                onClick={() => applyBoost(opt.id)}
                disabled={!opt.can_afford || loading}
                className={`w-full p-3 rounded-lg text-left transition-all border ${opt.can_afford ? 'bg-white/5 border-white/10 hover:border-orange-500/30' : 'bg-white/[0.02] border-white/5 opacity-40'}`}
                data-testid={`boost-${opt.id}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-semibold text-white">{opt.name}</p>
                  <span className="text-[10px] text-green-400">+{opt.revenue_boost_pct}% Revenue</span>
                </div>
                <p className="text-[11px] text-gray-500 mb-1.5">{opt.description}</p>
                <div className="flex gap-3 text-[10px]">
                  <span className="text-yellow-400">${opt.cost_funds?.toLocaleString()}</span>
                  <span className="text-cyan-400">{opt.cost_cp} CP</span>
                  <span className="text-orange-400">Hype +{opt.hype_boost}</span>
                </div>
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function StatCard({ icon, label, value, sub, color }) {
  const colors = {
    orange: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    red: 'text-red-400 bg-red-500/10 border-red-500/20',
    yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    green: 'text-green-400 bg-green-500/10 border-green-500/20',
  };
  return (
    <div className={`p-2 rounded-lg border ${colors[color]}`}>
      <div className="flex items-center gap-1 mb-0.5">{icon}<span className="text-[9px] text-gray-500">{label}</span></div>
      <p className="text-base font-bold">{value}<span className="text-[10px] text-gray-600">{sub}</span></p>
    </div>
  );
}

function WarCard({ war, userId, remainingTime, onMarketing, completed }) {
  const myFilm = war.films?.find(f => f.user_id === userId);
  const opponents = war.films?.filter(f => f.user_id !== userId) || [];
  const winner = completed && war.results?.length > 0 ? war.results[0] : null;
  const iWon = winner?.user_id === userId;

  return (
    <div className={`p-3 rounded-xl border ${completed ? (iWon ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20') : 'bg-orange-500/5 border-orange-500/20'}`} data-testid={`war-${war.id}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <TrendingUp className={`w-4 h-4 ${completed ? (iWon ? 'text-green-400' : 'text-red-400') : 'text-orange-400'}`} />
          <span className="text-xs font-bold text-white">Guerra al Box Office</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-gray-400">{war.genre}</span>
        </div>
        {!completed && <span className="text-[10px] text-orange-400 font-mono"><Clock className="w-3 h-3 inline mr-0.5" />{remainingTime(war.ends_at)}</span>}
        {completed && <span className={`text-[10px] font-bold ${iWon ? 'text-green-400' : 'text-red-400'}`}>{iWon ? 'VITTORIA' : 'SCONFITTA'}</span>}
      </div>

      <div className="space-y-1.5">
        {war.films?.map((f, i) => {
          const isMine = f.user_id === userId;
          const result = completed ? war.results?.find(r => r.film_id === f.film_id) : null;
          return (
            <div key={f.film_id || i} className={`flex items-center gap-2 p-2 rounded-lg ${isMine ? 'bg-yellow-500/10 border border-yellow-500/15' : 'bg-white/5 border border-white/5'}`}>
              <Film className={`w-3.5 h-3.5 flex-shrink-0 ${isMine ? 'text-yellow-400' : 'text-gray-500'}`} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-white truncate">{f.title}</p>
                <p className="text-[10px] text-gray-500">{isMine ? 'Il tuo film' : f.nickname || 'Avversario'}</p>
              </div>
              {f.marketing_boosts?.length > 0 && (
                <div className="flex gap-0.5">
                  {f.marketing_boosts.map((b, bi) => (
                    <span key={bi} className="text-[8px] px-1 py-0.5 bg-orange-500/20 text-orange-400 rounded">{b.name?.slice(0, 3)}</span>
                  ))}
                </div>
              )}
              {result && <span className="text-xs font-bold text-gray-300">#{result.rank}</span>}
              <span className="text-[10px] text-gray-500">Q:{f.quality_score}</span>
            </div>
          );
        })}
      </div>

      {!completed && myFilm && onMarketing && (
        <Button
          size="sm"
          onClick={() => onMarketing(war.id, myFilm.film_id)}
          className="mt-2 w-full bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 border border-orange-500/20 text-xs"
          data-testid={`marketing-btn-${war.id}`}
        >
          <Megaphone className="w-3.5 h-3.5 mr-1.5" /> Boost Marketing
        </Button>
      )}

      {completed && winner && (
        <div className="mt-2 p-2 rounded-lg bg-white/5 text-[10px] text-gray-400">
          <span className="text-white font-semibold">{winner.title}</span> ha vinto!
          {iWon && winner.prizes && (
            <span className="text-green-400 ml-1">+${winner.prizes.funds?.toLocaleString()} +{winner.prizes.fame} Fama</span>
          )}
        </div>
      )}
    </div>
  );
}

function ChallengeCard({ challenge, userId, remainingTime, completed }) {
  const iAmChallenger = challenge.challenger_id === userId;
  const myTitle = iAmChallenger ? challenge.challenger_film_title : challenge.defender_film_title;
  const oppTitle = iAmChallenger ? challenge.defender_film_title : challenge.challenger_film_title;
  const oppNick = iAmChallenger ? challenge.defender_nickname : challenge.challenger_nickname;
  const iWon = completed && challenge.results?.winner_id === userId;

  return (
    <div className={`p-3 rounded-xl border ${completed ? (iWon ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20') : 'bg-red-500/5 border-red-500/20'}`} data-testid={`challenge-${challenge.id}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Swords className={`w-4 h-4 ${completed ? (iWon ? 'text-green-400' : 'text-red-400') : 'text-red-400'}`} />
          <span className="text-xs font-bold text-white">Testa a Testa</span>
        </div>
        {!completed && <span className="text-[10px] text-red-400 font-mono"><Clock className="w-3 h-3 inline mr-0.5" />{remainingTime(challenge.ends_at)}</span>}
        {completed && <span className={`text-[10px] font-bold ${iWon ? 'text-green-400' : 'text-red-400'}`}>{iWon ? 'VITTORIA' : 'SCONFITTA'}</span>}
      </div>

      <div className="flex items-center gap-2">
        <div className="flex-1 p-2 rounded-lg bg-yellow-500/10 border border-yellow-500/15 text-center">
          <Film className="w-3.5 h-3.5 text-yellow-400 mx-auto mb-0.5" />
          <p className="text-[11px] font-semibold text-white truncate">{myTitle}</p>
          <p className="text-[9px] text-gray-500">Il tuo film</p>
        </div>
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
            <span className="text-red-400 font-bold text-xs">VS</span>
          </div>
        </div>
        <div className="flex-1 p-2 rounded-lg bg-white/5 border border-white/10 text-center">
          <Target className="w-3.5 h-3.5 text-orange-400 mx-auto mb-0.5" />
          <p className="text-[11px] font-semibold text-white truncate">{oppTitle}</p>
          <p className="text-[9px] text-gray-500">{oppNick}</p>
        </div>
      </div>

      {completed && challenge.results && (
        <div className="mt-2 p-2 rounded-lg bg-white/5 text-[10px] space-y-0.5">
          <div className="flex justify-between">
            <span className="text-gray-500">Tuo punteggio:</span>
            <span className="text-white font-mono">{(iAmChallenger ? challenge.results.challenger_scores?.total : challenge.results.defender_scores?.total)?.toFixed(1)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Avversario:</span>
            <span className="text-white font-mono">{(iAmChallenger ? challenge.results.defender_scores?.total : challenge.results.challenger_scores?.total)?.toFixed(1)}</span>
          </div>
          {iWon && (
            <p className="text-green-400 text-center pt-1">+$250K +5 Fama +5 CP</p>
          )}
        </div>
      )}
    </div>
  );
}
