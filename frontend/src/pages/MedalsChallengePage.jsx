// CineWorld — Medaglie & Sfide Settimanali
import React, { useState, useEffect, useContext, useCallback } from 'react';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Medal, Trophy, Star, Film, Tv, Sparkles, Crown, Swords, Shield, Building2,
  DollarSign, TrendingUp, Users, Flame, Heart, Skull, BookOpen, Store,
  Loader2, Clock, Gift, CheckCircle, Lock, ChevronRight, Zap
} from 'lucide-react';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';

const API = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return '';
  if (url.startsWith('http') || url.startsWith('data:')) return url;
  return `${API}${url}`;
};

const ICON_MAP = {
  Film, Tv, Sparkles, Crown, Star, DollarSign, TrendingUp, Store, Swords, Shield,
  Flame, Heart, Skull, BookOpen, Users, Building2, UserPlus: Users, Laugh: Sparkles,
};

const TIER_COLORS = {
  bronze: { bg: 'bg-amber-900/20', border: 'border-amber-700/30', text: 'text-amber-500', glow: '' },
  silver: { bg: 'bg-slate-400/10', border: 'border-slate-400/20', text: 'text-slate-300', glow: 'shadow-slate-400/10' },
  gold: { bg: 'bg-yellow-500/15', border: 'border-yellow-500/25', text: 'text-yellow-400', glow: 'shadow-yellow-500/15' },
  legendary: { bg: 'bg-purple-500/15', border: 'border-purple-500/25', text: 'text-purple-400', glow: 'shadow-purple-500/20' },
};

const TIER_LABELS = { bronze: 'Bronzo', silver: 'Argento', gold: 'Oro', legendary: 'Leggendaria' };

export default function MedalsChallengePage() {
  const { api } = useContext(AuthContext);
  const [tab, setTab] = useState('challenges');
  const [medals, setMedals] = useState([]);
  const [medalsStats, setMedalsStats] = useState({});
  const [challenges, setChallenges] = useState([]);
  const [challengeInfo, setChallengeInfo] = useState({});
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(null);

  const loadMedals = useCallback(async () => {
    try {
      const res = await api.get('/medals/my');
      setMedals(res.data.medals || []);
      setMedalsStats({ earned: res.data.total_earned, total: res.data.total_available });
    } catch { /* */ }
  }, [api]);

  const loadChallenges = useCallback(async () => {
    try {
      const res = await api.get('/challenges/weekly');
      setChallenges(res.data.challenges || []);
      setChallengeInfo({ week_start: res.data.week_start, week_end: res.data.week_end, time_remaining: res.data.time_remaining });
    } catch { /* */ }
  }, [api]);

  useEffect(() => {
    setLoading(true);
    Promise.all([loadMedals(), loadChallenges()]).finally(() => setLoading(false));
  }, [loadMedals, loadChallenges]);

  const claimReward = async (challengeId) => {
    setClaiming(challengeId);
    try {
      const res = await api.post(`/challenges/weekly/${challengeId}/claim`);
      toast.success(res.data.message);
      loadChallenges();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setClaiming(null);
  };

  const [festival, setFestival] = useState(null);
  const [festivalVotes, setFestivalVotes] = useState({});
  const [leaderboard, setLeaderboard] = useState(null);
  const [hasVoted, setHasVoted] = useState(false);
  const [votingLoading, setVotingLoading] = useState(false);

  const loadFestival = useCallback(async () => {
    try {
      const res = await api.get('/festivals/current');
      setFestival(res.data.festival);
      setHasVoted(res.data.has_voted);
    } catch { /* */ }
  }, [api]);

  const loadLeaderboard = useCallback(async () => {
    try {
      const res = await api.get('/challenges/leaderboard');
      setLeaderboard(res.data);
    } catch { /* */ }
  }, [api]);

  useEffect(() => { loadFestival(); loadLeaderboard(); }, [loadFestival, loadLeaderboard]);

  const submitVotes = async () => {
    if (!festival) return;
    setVotingLoading(true);
    try {
      await api.post(`/festivals/${festival.id}/vote`, { votes: festivalVotes });
      toast.success('Voto registrato!');
      setHasVoted(true);
      loadFestival();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore voto'); }
    setVotingLoading(false);
  };

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center pt-16">
      <Loader2 className="w-6 h-6 text-amber-400 animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pt-14 pb-20" data-testid="medals-page">
      {/* Header */}
      <div className="px-3 pt-3 pb-2">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
            <Trophy className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold">Sfide & Medaglie</h1>
            <p className="text-[9px] text-gray-500">{medalsStats.earned}/{medalsStats.total} medaglie sbloccate</p>
          </div>
        </div>

        <div className="flex gap-1">
          {[['challenges', 'Sfide', Zap], ['medals', 'Medaglie', Medal], ['festival', 'Festival', Trophy], ['classifica', 'Classifica', Crown]].map(([id, label, Icon]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-[10px] font-semibold
                ${tab === id ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20' : 'bg-white/5 text-gray-500 border border-transparent'}`}
              data-testid={`tab-${id}`}>
              <Icon className="w-3.5 h-3.5" /> {label}
            </button>
          ))}
        </div>
      </div>

      <div className="px-3">
        {/* CHALLENGES TAB */}
        {tab === 'challenges' && (
          <div className="space-y-3">
            {challengeInfo.time_remaining && (
              <div className="flex items-center gap-1.5 p-2 bg-amber-500/5 rounded-lg border border-amber-500/10">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-[10px] text-amber-400">Tempo rimanente: <b>{challengeInfo.time_remaining}</b></span>
              </div>
            )}
            {challenges.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Zap className="w-8 h-8 mx-auto mb-2 opacity-20" />
                <p className="text-sm">Nessuna sfida disponibile</p>
              </div>
            ) : challenges.map((c, i) => (
              <motion.div key={c.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}
                className={`p-3 rounded-xl border ${c.completed ? (c.claimed ? 'bg-green-500/5 border-green-500/15' : 'bg-amber-500/5 border-amber-500/15') : 'bg-white/[0.02] border-white/5'}`}
                data-testid={`challenge-${c.id}`}>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-xs font-bold">{c.name}</h3>
                    <p className="text-[10px] text-gray-400 mt-0.5">{c.desc}</p>
                  </div>
                  {c.claimed ? (
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                  ) : c.completed ? (
                    <Gift className="w-5 h-5 text-amber-400 flex-shrink-0 animate-pulse" />
                  ) : (
                    <span className="text-[10px] text-gray-500">{c.progress}/{c.target}</span>
                  )}
                </div>

                {/* Progress bar */}
                {!c.claimed && (
                  <div className="h-1.5 bg-[#1A1A1D] rounded-full overflow-hidden mb-2">
                    <motion.div
                      className={`h-full rounded-full ${c.completed ? 'bg-amber-400' : 'bg-emerald-500'}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(100, (c.progress / c.target) * 100)}%` }}
                      transition={{ duration: 0.5, delay: 0.2 + i * 0.1 }}
                    />
                  </div>
                )}

                {/* Rewards */}
                <div className="flex items-center gap-2 flex-wrap">
                  {c.reward_funds > 0 && <Badge className="bg-green-500/10 text-green-400 border-0 text-[8px]">${(c.reward_funds/1000).toFixed(0)}K</Badge>}
                  {c.reward_cp > 0 && <Badge className="bg-amber-500/10 text-amber-400 border-0 text-[8px]">{c.reward_cp} CP</Badge>}
                  {c.reward_xp > 0 && <Badge className="bg-blue-500/10 text-blue-400 border-0 text-[8px]">{c.reward_xp} XP</Badge>}
                  {c.reward_fame > 0 && <Badge className="bg-purple-500/10 text-purple-400 border-0 text-[8px]">{c.reward_fame} Fama</Badge>}

                  {c.completed && !c.claimed && (
                    <Button size="sm" className="ml-auto h-6 text-[9px] bg-amber-600 hover:bg-amber-700"
                      onClick={() => claimReward(c.id)} disabled={claiming === c.id} data-testid={`claim-${c.id}`}>
                      {claiming === c.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Gift className="w-3 h-3 mr-0.5" />}
                      Riscuoti
                    </Button>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* MEDALS TAB */}
        {tab === 'medals' && (
          <div className="space-y-1.5">
            {/* Categories */}
            {['produzione', 'qualita', 'business', 'pvp', 'genere', 'social', 'infrastrutture'].map(cat => {
              const catMedals = medals.filter(m => m.category === cat);
              if (catMedals.length === 0) return null;
              const catLabels = { produzione: 'Produzione', qualita: 'Qualità', business: 'Business', pvp: 'Arena PvP', genere: 'Maestria Genere', social: 'Social', infrastrutture: 'Infrastrutture' };
              return (
                <div key={cat}>
                  <h3 className="text-[9px] text-gray-500 uppercase tracking-wider font-bold mb-1 mt-3">{catLabels[cat] || cat}</h3>
                  <div className="grid grid-cols-3 gap-1.5">
                    {catMedals.map((m, i) => {
                      const tier = TIER_COLORS[m.tier] || TIER_COLORS.bronze;
                      const IconComp = ICON_MAP[m.icon] || Star;
                      return (
                        <motion.div
                          key={m.id}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: i * 0.03 }}
                          className={`relative p-2 rounded-xl border text-center ${m.earned ? `${tier.bg} ${tier.border} shadow-lg ${tier.glow}` : 'bg-white/[0.01] border-white/5 opacity-40'}`}
                          data-testid={`medal-${m.id}`}
                        >
                          <div className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center mb-1 ${m.earned ? tier.bg : 'bg-white/5'}`}>
                            {m.earned ? (
                              <IconComp className="w-4 h-4" style={{ color: m.color }} />
                            ) : (
                              <Lock className="w-3 h-3 text-gray-600" />
                            )}
                          </div>
                          <p className={`text-[8px] font-bold leading-tight ${m.earned ? tier.text : 'text-gray-600'}`}>{m.name}</p>
                          <p className="text-[7px] text-gray-600 mt-0.5 leading-tight">{m.desc}</p>
                          <Badge className={`mt-1 text-[6px] border-0 ${m.earned ? `${tier.bg} ${tier.text}` : 'bg-gray-800 text-gray-600'}`}>
                            {TIER_LABELS[m.tier] || m.tier}
                          </Badge>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* FESTIVAL TAB */}
        {tab === 'festival' && (
          <div className="space-y-3">
            {!festival ? (
              <div className="text-center py-12 text-gray-500">
                <Trophy className="w-8 h-8 mx-auto mb-2 opacity-20" />
                <p className="text-sm">Nessun festival attivo</p>
                <p className="text-[10px] text-gray-600 mt-1">I festival vengono creati automaticamente quando ci sono abbastanza film</p>
              </div>
            ) : (
              <>
                <div className="p-3 rounded-xl bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20 text-center">
                  <h2 className="font-['Bebas_Neue'] text-lg text-amber-400 tracking-wide">{festival.name}</h2>
                  <p className="text-[10px] text-gray-400 mt-1">{hasVoted ? 'Hai già votato!' : 'Vota per i tuoi preferiti'}</p>
                </div>

                {Object.entries(festival.categories || {}).map(([catId, cat]) => (
                  <div key={catId} className="p-2.5 bg-white/[0.02] rounded-xl border border-white/5" data-testid={`festival-cat-${catId}`}>
                    <h3 className="text-[11px] font-bold text-amber-400 mb-2">{cat.name}</h3>
                    <div className="space-y-1">
                      {cat.nominees?.map(n => (
                        <button key={n.id}
                          onClick={() => !hasVoted && setFestivalVotes({ ...festivalVotes, [catId]: n.id })}
                          disabled={hasVoted}
                          className={`w-full flex items-center gap-2 p-1.5 rounded-lg text-left transition ${
                            festivalVotes[catId] === n.id ? 'bg-amber-500/15 border border-amber-500/25' :
                            hasVoted ? 'bg-white/[0.02] opacity-50' : 'bg-white/[0.02] hover:bg-white/[0.05] border border-transparent'}`}
                          data-testid={`vote-${catId}-${n.id}`}>
                          {posterSrc(n.poster_url) ? (
                            <img src={posterSrc(n.poster_url)} alt="" className="w-7 h-10 rounded object-cover" />
                          ) : <div className="w-7 h-10 rounded bg-gray-800" />}
                          <div className="flex-1 min-w-0">
                            <p className="text-[10px] font-bold truncate">{n.title}</p>
                            {hasVoted && <span className="text-[8px] text-amber-400">{n.votes} voti</span>}
                          </div>
                          {festivalVotes[catId] === n.id && <CheckCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                {!hasVoted && Object.keys(festivalVotes).length > 0 && (
                  <Button className="w-full bg-amber-600 hover:bg-amber-700 text-sm" onClick={submitVotes}
                    disabled={votingLoading} data-testid="submit-votes-btn">
                    {votingLoading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Trophy className="w-4 h-4 mr-1" />}
                    Invia Voti ({Object.keys(festivalVotes).length} categorie)
                  </Button>
                )}
              </>
            )}
          </div>
        )}

        {/* CLASSIFICA TAB */}
        {tab === 'classifica' && leaderboard && (
          <div className="space-y-3">
            <div className="p-2.5 bg-amber-500/5 rounded-xl border border-amber-500/10 text-center">
              <h3 className="text-xs font-bold text-amber-400">Classifica Sfide Settimanali</h3>
              {leaderboard.my_rank > 0 && (
                <p className="text-[10px] text-gray-400 mt-0.5">La tua posizione: <b className="text-white">#{leaderboard.my_rank}</b></p>
              )}
            </div>
            {leaderboard.leaderboard?.length === 0 ? (
              <p className="text-center text-gray-500 text-sm py-8">Nessun partecipante questa settimana</p>
            ) : leaderboard.leaderboard?.map((entry, i) => (
              <motion.div key={entry.user_id} initial={{ opacity: 0, x: -5 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                className={`flex items-center gap-2 p-2 rounded-lg ${entry.is_me ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-white/[0.02]'}`}
                data-testid={`leaderboard-${i}`}>
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black
                  ${i === 0 ? 'bg-yellow-500/20 text-yellow-400' : i === 1 ? 'bg-gray-400/20 text-gray-300' : i === 2 ? 'bg-orange-500/20 text-orange-400' : 'bg-white/5 text-gray-500'}`}>
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-bold truncate">{entry.nickname}</p>
                  <p className="text-[8px] text-gray-500">{entry.studio}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold text-amber-400">{entry.completed}/{entry.total}</p>
                  <p className="text-[8px] text-gray-500">completate</p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
