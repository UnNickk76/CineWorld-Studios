// CineWorld Studio's - FestivalsPage v2.0
// Reworked: Dynamic nominations, 4-state system, improved UI

import React, { useState, useEffect, useRef, useCallback, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthContext, LanguageContext, PlayerPopupContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { PlayerBadge } from '../components/PlayerBadge';
import { Progress } from '../components/ui/progress';
import { ScrollArea } from '../components/ui/scroll-area';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Film, Star, Award, TrendingUp, Clock, Play, Users, Clapperboard,
  Send, ChevronRight, ChevronLeft, X,
  Zap, Globe, Trophy, Shield, Heart, MessageSquare, Bell,
  Plus, Search, Loader2, RefreshCw, Download,
  Eye, Lock,
  Sparkles, Flame, Target, Music, Camera, Video,
  BookOpen, Gift, Crown, Medal, Gem, Coins,
  ArrowLeft,
  Lightbulb, ThumbsUp, CheckCircle,
  BarChart3, Activity,
  Tv, User, Wand2
} from 'lucide-react';
import { ClickableNickname } from '../components/shared';
import { CinematicCeremony } from '../components/CinematicCeremony';

// ═══════════════════════════════════════════════════
// HOOKS
// ═══════════════════════════════════════════════════

const useCountdown = (targetDate) => {
  const [timeLeft, setTimeLeft] = React.useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  React.useEffect(() => {
    if (!targetDate) return;
    const tick = () => {
      const diff = new Date(targetDate) - new Date();
      if (diff <= 0) { setTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 }); return; }
      setTimeLeft({
        days: Math.floor(diff / 86400000),
        hours: Math.floor((diff % 86400000) / 3600000),
        minutes: Math.floor((diff % 3600000) / 60000),
        seconds: Math.floor((diff % 60000) / 1000)
      });
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [targetDate]);
  return timeLeft;
};

// ═══════════════════════════════════════════════════
// STATE BADGE COMPONENT
// ═══════════════════════════════════════════════════

const StateBadge = ({ state, label }) => {
  const config = {
    upcoming: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    voting: 'bg-green-500/20 text-green-400 border-green-500/30',
    live: 'bg-red-500/20 text-red-400 border-red-500/30 animate-pulse',
    ended: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  };
  const icons = {
    upcoming: <Clock className="w-3 h-3" />,
    voting: <CheckCircle className="w-3 h-3" />,
    live: <Tv className="w-3 h-3" />,
    ended: <Lock className="w-3 h-3" />
  };
  return (
    <Badge className={`${config[state] || config.upcoming} text-[10px] gap-1 border`} data-testid={`state-badge-${state}`}>
      {icons[state]} {label}
    </Badge>
  );
};

// ═══════════════════════════════════════════════════
// VOTING TYPE BADGE
// ═══════════════════════════════════════════════════

const VotingTypeBadge = ({ type }) => {
  const config = {
    player: { label: 'VOTO PLAYER', color: 'border-purple-500/40 text-purple-400', icon: <Users className="w-3 h-3" /> },
    ai: { label: 'AI', color: 'border-cyan-500/40 text-cyan-400', icon: <Wand2 className="w-3 h-3" /> },
    algorithm: { label: 'ALGORITMO', color: 'border-amber-500/40 text-amber-400', icon: <BarChart3 className="w-3 h-3" /> }
  };
  const c = config[type] || config.player;
  return (
    <Badge variant="outline" className={`${c.color} text-[10px] gap-1`} data-testid={`voting-type-${type}`}>
      {c.icon} {c.label}
    </Badge>
  );
};

// ═══════════════════════════════════════════════════
// COUNTDOWN TIMER COMPONENT
// ═══════════════════════════════════════════════════

const CountdownTimer = ({ targetDate, isPalma, compact = false }) => {
  const timeLeft = useCountdown(targetDate);
  if (compact) {
    return (
      <span className="text-xs text-gray-400 font-mono tabular-nums">
        {timeLeft.days}g {String(timeLeft.hours).padStart(2,'0')}:{String(timeLeft.minutes).padStart(2,'0')}:{String(timeLeft.seconds).padStart(2,'0')}
      </span>
    );
  }
  return (
    <div className="flex gap-1.5">
      {[
        { val: timeLeft.days, label: 'G' },
        { val: timeLeft.hours, label: 'O' },
        { val: timeLeft.minutes, label: 'M' },
        { val: timeLeft.seconds, label: 'S' }
      ].map((t, i) => (
        <div key={i} className="text-center">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-['Bebas_Neue'] text-lg ${
            isPalma ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' : 'bg-white/10 text-white border border-white/10'
          }`}>
            {String(t.val).padStart(2, '0')}
          </div>
          <span className="text-[8px] text-gray-500 mt-0.5">{t.label}</span>
        </div>
      ))}
    </div>
  );
};

// ═══════════════════════════════════════════════════
// FESTIVAL CARD (main grid)
// ═══════════════════════════════════════════════════

const FestivalCard = ({ fest, onSelect, onLive }) => {
  const isPalma = fest.has_palma_doro;
  const borderColor = {
    upcoming: 'border-blue-500/20 hover:border-blue-500/40',
    voting: 'border-green-500/20 hover:border-green-500/40',
    live: 'border-red-500/30 ring-1 ring-red-500/20',
    ended: 'border-white/10 hover:border-white/20'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className={`bg-[#141416] ${borderColor[fest.current_state] || borderColor.upcoming} cursor-pointer transition-all duration-200 overflow-hidden`}
        onClick={() => onSelect(fest.id)}
        data-testid={`festival-card-${fest.id}`}
      >
        {/* Top accent bar */}
        <div className={`h-1 w-full ${
          isPalma ? 'bg-gradient-to-r from-yellow-500 via-amber-400 to-yellow-500' :
          fest.current_state === 'live' ? 'bg-gradient-to-r from-red-500 via-pink-500 to-red-500' :
          fest.current_state === 'voting' ? 'bg-gradient-to-r from-green-500 via-emerald-400 to-green-500' :
          'bg-gradient-to-r from-white/10 via-white/20 to-white/10'
        }`} />

        <CardHeader className="pb-2 pt-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <CardTitle className="font-['Bebas_Neue'] text-lg text-yellow-400 leading-tight truncate">
                {fest.name}
              </CardTitle>
              {isPalma && (
                <div className="flex items-center gap-1 mt-1">
                  <Gem className="w-3 h-3 text-yellow-400" />
                  <span className="text-[10px] text-yellow-500/80">Palma d'Oro CineWorld</span>
                </div>
              )}
            </div>
            <div className="flex flex-col items-end gap-1 flex-shrink-0">
              <StateBadge state={fest.current_state} label={fest.state_label} />
              <VotingTypeBadge type={fest.voting_type} />
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-0 pb-4">
          <p className="text-gray-500 text-xs mb-3 line-clamp-2">{fest.description}</p>

          {/* Countdown */}
          {fest.current_state !== 'ended' && (
            <div className="mb-3 flex items-center justify-between">
              <span className="text-[10px] text-gray-600 uppercase tracking-wider">
                {fest.current_state === 'live' ? 'In diretta' : fest.current_state === 'voting' ? 'Cerimonia tra' : 'Prossima edizione'}
              </span>
              <CountdownTimer targetDate={fest.ceremony_datetime} isPalma={isPalma} compact />
            </div>
          )}

          {/* Rewards preview */}
          <div className="grid grid-cols-4 gap-1.5 pt-3 border-t border-white/5">
            <div className="text-center">
              <p className="text-yellow-400 font-bold text-xs">+{fest.rewards.xp}</p>
              <p className="text-[9px] text-gray-600">XP</p>
            </div>
            <div className="text-center">
              <p className="text-purple-400 font-bold text-xs">+{fest.rewards.fame}</p>
              <p className="text-[9px] text-gray-600">Fama</p>
            </div>
            <div className="text-center">
              <p className="text-green-400 font-bold text-xs">${(fest.rewards.money/1000).toFixed(0)}K</p>
              <p className="text-[9px] text-gray-600">Denaro</p>
            </div>
            {fest.rewards.cinepass > 0 && (
              <div className="text-center">
                <p className="text-cyan-400 font-bold text-xs">+{fest.rewards.cinepass}</p>
                <p className="text-[9px] text-gray-600">CP</p>
              </div>
            )}
          </div>

          {/* Live CTA */}
          {fest.current_state === 'live' && (
            <Button
              size="sm"
              onClick={(e) => { e.stopPropagation(); onLive(fest); }}
              className="w-full mt-3 bg-red-500 hover:bg-red-600 text-white text-xs h-8 gap-1"
              data-testid={`live-btn-${fest.id}`}
            >
              <Tv className="w-3.5 h-3.5" /> GUARDA IN DIRETTA
            </Button>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════
// COUNTDOWN BANNER (top hero)
// ═══════════════════════════════════════════════════

const CountdownBanner = ({ festival, onViewFestival }) => {
  const isPalma = festival.has_palma_doro;

  return (
    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} data-testid={`countdown-${festival.id}`}>
      <Card className={`border-0 overflow-hidden ${isPalma
        ? 'bg-gradient-to-r from-yellow-900/40 via-amber-900/30 to-yellow-900/40 ring-1 ring-yellow-500/40'
        : 'bg-gradient-to-r from-[#141416] via-[#1a1a1c] to-[#141416] ring-1 ring-white/10'}`}>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <div className="flex-1 text-center sm:text-left">
              <div className="flex items-center gap-2 justify-center sm:justify-start mb-1 flex-wrap">
                {isPalma && <Gem className="w-4 h-4 text-yellow-400" />}
                <h3 className="font-['Bebas_Neue'] text-lg text-yellow-400">{festival.name}</h3>
                <StateBadge state={festival.current_state} label={festival.state_label} />
                <VotingTypeBadge type={festival.voting_type} />
              </div>
              {isPalma && (
                <p className="text-[11px] text-yellow-500/80 mb-1">Palma d'Oro CineWorld - Bonus permanente +2% qualita</p>
              )}
              {festival.top_nominees?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {festival.top_nominees.map((cat, i) => (
                    <Badge key={i} className="bg-white/5 text-gray-300 text-[9px] px-1.5">
                      {cat.category}: {cat.nominees?.[0]?.name || '?'}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            <CountdownTimer targetDate={festival.target_date} isPalma={isPalma} />
            <div className="text-center sm:text-right">
              <div className="flex gap-2 text-[10px] mb-2 justify-center sm:justify-end">
                <span className="text-yellow-400">+{festival.rewards.xp} XP</span>
                <span className="text-green-400">${(festival.rewards.money/1000).toFixed(0)}K</span>
                {festival.rewards.cinepass > 0 && <span className="text-purple-400">+{festival.rewards.cinepass} CP</span>}
              </div>
              <Button size="sm" onClick={onViewFestival} className={`h-7 text-xs ${
                festival.current_state === 'voting' ? 'bg-green-500 hover:bg-green-400 text-black' :
                festival.current_state === 'live' ? 'bg-red-500 hover:bg-red-400 text-white' :
                isPalma ? 'bg-yellow-500 hover:bg-yellow-400 text-black' : 'bg-white/10 hover:bg-white/20'
              }`} data-testid={`countdown-btn-${festival.id}`}>
                {festival.current_state === 'voting' ? 'Vota Ora' : festival.current_state === 'live' ? 'Diretta' : 'Vedi'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════
// NOMINEE CARD (improved for voting)
// ═══════════════════════════════════════════════════

const NomineeCard = ({ nom, isVoted, canVote, onVote, voting, isWinner }) => {
  return (
    <motion.div
      whileHover={canVote ? { scale: 1.02 } : {}}
      whileTap={canVote ? { scale: 0.98 } : {}}
      className={`p-3 rounded-xl border transition-all ${
        isWinner ? 'bg-yellow-500/15 border-yellow-500/50 shadow-lg shadow-yellow-500/10' :
        isVoted ? 'bg-green-500/10 border-green-500/40' :
        canVote ? 'bg-white/[0.03] border-white/10 hover:border-white/25 cursor-pointer' :
        'bg-white/[0.03] border-white/10'
      }`}
      onClick={() => canVote && !isVoted && onVote()}
      data-testid={`nominee-${nom.id}`}
    >
      <div className="flex items-center gap-3">
        {/* Avatar/Poster placeholder */}
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
          isWinner ? 'bg-yellow-500/20' : 'bg-white/5'
        }`}>
          {isWinner ? <Trophy className="w-6 h-6 text-yellow-400" /> : <Film className="w-5 h-5 text-gray-500" />}
        </div>

        <div className="flex-1 min-w-0">
          <p className={`font-semibold text-sm truncate ${isWinner ? 'text-yellow-400' : ''}`}>
            {nom.name}
          </p>
          {nom.film_title && nom.film_title !== nom.name && (
            <p className="text-[11px] text-gray-500 truncate">{nom.film_title}</p>
          )}
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] text-gray-600">{nom.votes || 0} voti</span>
            {nom.quality_score > 0 && (
              <span className="text-[10px] text-blue-400">{Math.round(nom.quality_score)}% qualita</span>
            )}
          </div>
        </div>

        {/* Vote button or status */}
        <div className="flex-shrink-0">
          {isWinner && (
            <div className="w-8 h-8 rounded-full bg-yellow-500 flex items-center justify-center">
              <Trophy className="w-4 h-4 text-black" />
            </div>
          )}
          {isVoted && !isWinner && (
            <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-green-400" />
            </div>
          )}
          {canVote && !isVoted && !isWinner && (
            <Button size="sm" className="h-7 text-[10px] bg-yellow-500 text-black hover:bg-yellow-400 px-3" disabled={voting}>
              Vota
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════

const FestivalsPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useTranslations();
  const location = useLocation();
  const navigate = useNavigate();
  const [festivals, setFestivals] = useState([]);
  const [customFestivals, setCustomFestivals] = useState([]);
  const [selectedFestival, setSelectedFestival] = useState(null);
  const [currentEdition, setCurrentEdition] = useState(null);
  const [selectedCustomFestival, setSelectedCustomFestival] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [leaderboardPeriod, setLeaderboardPeriod] = useState('all_time');
  const [myAwards, setMyAwards] = useState(null);
  const [activeTab, setActiveTab] = useState('festivals');
  const [voting, setVoting] = useState(false);
  const [creationCost, setCreationCost] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newFestival, setNewFestival] = useState({ name: '', description: '', poster_prompt: '', categories: ['best_film', 'best_director', 'best_actor'], base_participation_cost: 10000, duration_days: 7 });
  const [myFilms, setMyFilms] = useState([]);
  const [selectedFilmIds, setSelectedFilmIds] = useState([]);
  const [participating, setParticipating] = useState(false);
  // Live Ceremony states
  const [liveCeremony, setLiveCeremony] = useState(null);
  const [showLiveCeremony, setShowLiveCeremony] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [sendingChat, setSendingChat] = useState(false);
  const chatRefreshInterval = useRef(null);
  const [autoOpenLiveId, setAutoOpenLiveId] = useState(null);
  const [countdownData, setCountdownData] = useState([]);
  const [historyData, setHistoryData] = useState([]);
  const [votesRemaining, setVotesRemaining] = useState(null);

  // Capture live parameter from URL
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const liveId = params.get('live');
    if (liveId) { setAutoOpenLiveId(liveId); window.history.replaceState({}, '', '/festivals'); }
  }, [location.search]);

  const periodLabels = {
    'monthly': 'Questo Mese',
    'yearly': 'Quest\'Anno',
    'all_time': 'Di Sempre'
  };

  const categoryOptions = [
    { id: 'best_film', name: 'Miglior Film' },
    { id: 'best_director', name: 'Miglior Regia' },
    { id: 'best_actor', name: 'Miglior Attore' },
    { id: 'best_actress', name: 'Miglior Attrice' },
    { id: 'best_screenplay', name: 'Miglior Sceneggiatura' },
    { id: 'best_soundtrack', name: 'Miglior Colonna Sonora' },
    { id: 'audience_choice', name: 'Premio del Pubblico' },
  ];

  useEffect(() => {
    loadFestivals();
    loadCustomFestivals();
    loadLeaderboard();
    loadMyAwards();
    loadCreationCost();
    loadCountdown();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadFestivals = async () => { try { const res = await api.get(`/festivals?language=it`); setFestivals(res.data.festivals); } catch (e) { console.error(e); } };
  const loadCustomFestivals = async () => { try { const res = await api.get('/custom-festivals'); setCustomFestivals(res.data.festivals || []); } catch (e) { console.error(e); } };
  const loadCreationCost = async () => { try { const res = await api.get('/custom-festivals/creation-cost'); setCreationCost(res.data); } catch (e) { console.error(e); } };
  const loadCountdown = async () => { try { const res = await api.get(`/festivals/countdown?language=it`); setCountdownData(res.data.upcoming_festivals || []); } catch (e) { console.error(e); } };
  const loadHistory = async () => { try { const res = await api.get(`/festivals/history?language=it`); setHistoryData(res.data.history || []); } catch (e) { console.error(e); } };
  const loadCustomFestivalDetails = async (festivalId) => {
    try {
      const res = await api.get(`/custom-festivals/${festivalId}`);
      setSelectedCustomFestival(res.data);
      const filmsRes = await api.get('/films/my');
      setMyFilms(filmsRes.data || []);
    } catch (e) { toast.error('Errore caricamento festival'); }
  };

  const loadFestivalEdition = async (festivalId) => {
    try {
      const res = await api.get(`/festivals/${festivalId}/current?language=it`);
      setCurrentEdition(res.data);
      setSelectedFestival(festivalId);
    } catch (e) { toast.error('Errore caricamento festival'); }
  };

  const loadLeaderboard = async (period = leaderboardPeriod) => {
    try { const res = await api.get(`/festivals/awards/leaderboard?period=${period}&language=it`); setLeaderboard(res.data); } catch (e) { console.error(e); }
  };

  const loadMyAwards = async () => {
    try { const res = await api.get(`/festivals/my-awards?language=it`); setMyAwards(res.data); } catch (e) { console.error(e); }
  };

  const handleVote = async (categoryId, nomineeId) => {
    if (!currentEdition || voting) return;
    setVoting(true);
    try {
      const res = await api.post('/festivals/vote', {
        festival_id: selectedFestival,
        edition_id: currentEdition.id,
        category: categoryId,
        nominee_id: nomineeId
      });
      const data = res.data;
      const weightMsg = data.vote_weight ? ` (peso x${data.vote_weight})` : '';
      const remainMsg = data.votes_remaining_today !== undefined ? ` | ${data.votes_remaining_today} voti rimasti oggi` : '';
      toast.success(`+5 XP${weightMsg}${remainMsg}`);
      setVotesRemaining(data.votes_remaining_today);
      loadFestivalEdition(selectedFestival);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore votazione');
    } finally { setVoting(false); }
  };

  // Live Ceremony
  const loadLiveCeremony = async (festivalId) => {
    try {
      const res = await api.get(`/festivals/${festivalId}/live-ceremony?language=it`);
      setLiveCeremony(res.data);
      await api.post(`/festivals/${festivalId}/join-ceremony`);
    } catch (e) { console.error(e); }
  };

  const openLiveCeremony = (festival) => {
    setSelectedFestival(festival.id);
    loadLiveCeremony(festival.id);
    setShowLiveCeremony(true);
    chatRefreshInterval.current = setInterval(() => loadLiveCeremony(festival.id), 5000);
  };

  const closeLiveCeremony = () => {
    setShowLiveCeremony(false); setLiveCeremony(null);
    if (chatRefreshInterval.current) clearInterval(chatRefreshInterval.current);
  };

  useEffect(() => {
    if (autoOpenLiveId && festivals.length > 0) {
      const fest = festivals.find(f => f.id === autoOpenLiveId);
      if (fest) { openLiveCeremony(fest); setAutoOpenLiveId(null); }
    }
  }, [autoOpenLiveId, festivals]); // eslint-disable-line react-hooks/exhaustive-deps

  const sendChatMessage = async () => {
    if (!chatMessage.trim() || !liveCeremony) return;
    setSendingChat(true);
    try {
      await api.post('/festivals/ceremony/chat', { festival_id: liveCeremony.festival_id, edition_id: liveCeremony.edition_id, message: chatMessage });
      setChatMessage('');
      loadLiveCeremony(liveCeremony.festival_id);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore invio'); }
    finally { setSendingChat(false); }
  };

  useEffect(() => {
    return () => { if (chatRefreshInterval.current) clearInterval(chatRefreshInterval.current); };
  }, []);

  const createCustomFestival = async () => {
    if (!newFestival.name.trim()) { toast.error('Inserisci un nome'); return; }
    setCreating(true);
    try {
      const res = await api.post('/custom-festivals/create', newFestival);
      toast.success(res.data.message);
      setShowCreateDialog(false);
      setNewFestival({ name: '', description: '', poster_prompt: '', categories: ['best_film'], base_participation_cost: 10000, duration_days: 7 });
      loadCustomFestivals();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore creazione'); }
    finally { setCreating(false); }
  };

  const participateInFestival = async () => {
    if (!selectedCustomFestival || selectedFilmIds.length === 0) return;
    setParticipating(true);
    try {
      const res = await api.post('/custom-festivals/participate', { festival_id: selectedCustomFestival.id, film_ids: selectedFilmIds });
      toast.success(res.data.message);
      loadCustomFestivalDetails(selectedCustomFestival.id);
      setSelectedFilmIds([]);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore partecipazione'); }
    finally { setParticipating(false); }
  };

  // ═════════════════════════════
  // RENDER
  // ═════════════════════════════

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto" data-testid="festivals-page">
      {/* Header */}
      <div className="text-center mb-6">
        <Award className="w-10 h-10 text-yellow-500 mx-auto mb-2" />
        <h1 className="font-['Bebas_Neue'] text-3xl sm:text-4xl">Festival del Cinema</h1>
        <p className="text-gray-500 text-sm mt-1">Vota i migliori film, assisti alle cerimonie e vinci premi</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1.5 mb-6 justify-center flex-wrap">
        {[
          { id: 'festivals', icon: <Star className="w-3.5 h-3.5" />, label: 'Festival' },
          { id: 'custom', icon: <Crown className="w-3.5 h-3.5" />, label: 'Player' },
          { id: 'leaderboard', icon: <Trophy className="w-3.5 h-3.5" />, label: 'Classifica' },
          { id: 'my_awards', icon: <Medal className="w-3.5 h-3.5" />, label: 'Premi' },
          { id: 'history', icon: <BookOpen className="w-3.5 h-3.5" />, label: 'Storico' },
        ].map(tab => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? 'default' : 'ghost'}
            size="sm"
            onClick={() => { setActiveTab(tab.id); if (tab.id === 'history') loadHistory(); }}
            className={`gap-1.5 text-xs h-8 ${activeTab === tab.id ? (tab.id === 'custom' ? 'bg-purple-500 text-white' : 'bg-yellow-500 text-black') : 'text-gray-400 hover:text-white'}`}
            data-testid={`tab-${tab.id}`}
          >
            {tab.icon} {tab.label}
          </Button>
        ))}
      </div>

      {/* ═══ COUNTDOWN BANNERS ═══ */}
      {countdownData.length > 0 && activeTab === 'festivals' && !selectedFestival && (
        <div className="mb-6 space-y-3" data-testid="countdown-section">
          {countdownData.map(fest => (
            <CountdownBanner key={fest.id} festival={fest} onViewFestival={() => loadFestivalEdition(fest.id)} />
          ))}
        </div>
      )}

      {/* ═══ FESTIVALS TAB ═══ */}
      {activeTab === 'festivals' && (
        <div className="space-y-4">
          {!selectedFestival ? (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {festivals.map(fest => (
                <FestivalCard key={fest.id} fest={fest} onSelect={loadFestivalEdition} onLive={openLiveCeremony} />
              ))}
            </div>
          ) : currentEdition && (
            <div>
              <Button variant="ghost" size="sm" onClick={() => { setSelectedFestival(null); setCurrentEdition(null); }} className="mb-4 text-gray-400 hover:text-white" data-testid="back-to-festivals">
                <ChevronLeft className="w-4 h-4 mr-1" /> Torna ai Festival
              </Button>

              {/* Edition header */}
              <Card className={`mb-6 overflow-hidden border-0 ${
                selectedFestival === 'golden_stars' ? 'bg-gradient-to-r from-yellow-900/30 via-amber-900/20 to-yellow-900/30 ring-1 ring-yellow-500/30' :
                'bg-gradient-to-r from-[#141416] via-[#1a1a1c] to-[#141416] ring-1 ring-white/10'
              }`}>
                <CardHeader>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <CardTitle className="font-['Bebas_Neue'] text-2xl text-yellow-400">{currentEdition.festival_name}</CardTitle>
                      <CardDescription className="mt-1">
                        Edizione {currentEdition.month}/{currentEdition.year} | {currentEdition.voting_type === 'player' ? 'Voto pesato per livello e fama' : currentEdition.voting_type === 'algorithm' ? 'Valutazione algoritmica' : 'Valutazione AI'}
                      </CardDescription>
                      {selectedFestival === 'golden_stars' && (
                        <div className="flex items-center gap-1 mt-2">
                          <Gem className="w-3.5 h-3.5 text-yellow-400" />
                          <span className="text-[11px] text-yellow-500/80 font-medium">Palma d'Oro CineWorld</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <StateBadge state={currentEdition.status === 'ceremony' ? 'live' : currentEdition.status === 'awarded' || currentEdition.status === 'ended' ? 'ended' : currentEdition.status} label={currentEdition.state_label} />
                      <VotingTypeBadge type={currentEdition.voting_type} />
                      {votesRemaining !== null && currentEdition.can_vote && (
                        <Badge className="bg-blue-500/20 text-blue-400 text-xs">{votesRemaining} voti rimasti</Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
              </Card>

              {/* Category list with nominations */}
              <div className="space-y-4">
                {currentEdition.categories?.map(cat => (
                  <Card key={cat.category_id} className="bg-[#141416] border-white/10" data-testid={`category-${cat.category_id}`}>
                    <CardHeader className="pb-2">
                      <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                        <Award className="w-5 h-5 text-yellow-500" />
                        {cat.name}
                        {cat.user_voted && <Badge className="bg-green-500/20 text-green-400 text-xs ml-2">Votato</Badge>}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                        {cat.nominees?.map(nom => (
                          <NomineeCard
                            key={nom.id}
                            nom={nom}
                            isVoted={cat.user_voted === nom.id}
                            canVote={currentEdition.can_vote && !cat.user_voted}
                            onVote={() => handleVote(cat.category_id, nom.id)}
                            voting={voting}
                            isWinner={false}
                          />
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══ CUSTOM FESTIVALS TAB ═══ */}
      {activeTab === 'custom' && (
        <div className="space-y-4">
          {creationCost && (
            <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30">
              <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="font-['Bebas_Neue'] text-lg text-purple-400">Crea il Tuo Festival</h3>
                  <p className="text-xs text-gray-400">
                    {creationCost.can_create
                      ? `Costo: $${creationCost.creation_cost?.toLocaleString()} + ${creationCost.cinepass_cost || 3} CP`
                      : `Richiesto Livello ${creationCost.required_level} (sei ${creationCost.user_level})`}
                  </p>
                </div>
                <Button onClick={() => setShowCreateDialog(true)} disabled={!creationCost.can_create} className="bg-purple-500 hover:bg-purple-400">
                  <Plus className="w-4 h-4 mr-2" /> Crea Festival
                </Button>
              </CardContent>
            </Card>
          )}

          {!selectedCustomFestival ? (
            <div className="grid md:grid-cols-2 gap-4">
              {customFestivals.length === 0 ? (
                <Card className="bg-[#141416] border-white/10 col-span-2">
                  <CardContent className="p-8 text-center">
                    <Crown className="w-12 h-12 text-purple-400/50 mx-auto mb-2" />
                    <p className="text-gray-400">Nessun festival dei player attivo. Creane uno!</p>
                  </CardContent>
                </Card>
              ) : customFestivals.map(fest => (
                <Card key={fest.id} className="bg-[#141416] border-white/10 cursor-pointer hover:border-purple-500/50 transition-colors" onClick={() => loadCustomFestivalDetails(fest.id)}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="font-['Bebas_Neue'] text-lg text-purple-400">{fest.name}</CardTitle>
                      <Badge className={fest.status === 'open' ? 'bg-green-500/20 text-green-400' : fest.status === 'live' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'}>
                        {fest.status === 'open' ? 'APERTO' : fest.status === 'live' ? 'LIVE' : fest.status?.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-400 text-xs mb-2">{fest.description?.substring(0, 100)}...</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <User className="w-3 h-3" /> {fest.creator_name}
                      <span>|</span>
                      <span>${fest.prize_pool?.toLocaleString()} montepremi</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div>
              <Button variant="ghost" size="sm" onClick={() => { setSelectedCustomFestival(null); setSelectedFilmIds([]); }} className="mb-4 text-gray-400">
                <ChevronLeft className="w-4 h-4 mr-1" /> Torna
              </Button>
              <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30 mb-4">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-['Bebas_Neue'] text-2xl text-purple-400">{selectedCustomFestival.name}</CardTitle>
                    <Badge className={selectedCustomFestival.status === 'open' ? 'bg-green-500/20 text-green-400' : 'bg-purple-500/20 text-purple-400'}>
                      {selectedCustomFestival.status?.toUpperCase()}
                    </Badge>
                  </div>
                  <CardDescription>
                    Creato da {selectedCustomFestival.creator_name} | Montepremi: ${selectedCustomFestival.prize_pool?.toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-300 mb-4">{selectedCustomFestival.description}</p>
                  {selectedCustomFestival.status === 'open' && !selectedCustomFestival.user_participating && (
                    <Card className="bg-black/30 border-white/10 mb-4">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">Partecipa!</CardTitle>
                        <CardDescription className="text-xs">Costo: ${selectedCustomFestival.base_participation_cost?.toLocaleString()} per film</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ScrollArea className="h-[150px] mb-3">
                          <div className="space-y-2">
                            {myFilms.map(film => {
                              const isSelected = selectedFilmIds.includes(film.id);
                              return (
                                <div key={film.id} className={`p-2 rounded flex items-center justify-between cursor-pointer ${isSelected ? 'bg-purple-500/20 border border-purple-500' : 'bg-white/5 hover:bg-white/10'}`}
                                  onClick={() => {
                                    if (isSelected) setSelectedFilmIds(selectedFilmIds.filter(id => id !== film.id));
                                    else if (selectedFilmIds.length < 10) setSelectedFilmIds([...selectedFilmIds, film.id]);
                                  }}>
                                  <span className="text-sm">{film.title}</span>
                                  {isSelected && <CheckCircle className="w-4 h-4 text-purple-400" />}
                                </div>
                              );
                            })}
                          </div>
                        </ScrollArea>
                        <Button onClick={participateInFestival} disabled={participating || selectedFilmIds.length === 0} className="w-full bg-purple-500">
                          {participating ? 'Iscrizione...' : `Iscrivi ${selectedFilmIds.length} film`}
                        </Button>
                      </CardContent>
                    </Card>
                  )}
                  {selectedCustomFestival.user_participating && (
                    <Badge className="bg-green-500/20 text-green-400 mb-4">Stai partecipando!</Badge>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {selectedCustomFestival.categories?.map(cat => (
                      <Badge key={cat.id} variant="outline" className="border-purple-500/30">{cat.name}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* Create Festival Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-[#1A1A1A] border-purple-500/30 max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl text-purple-400 flex items-center gap-2">
              <Crown className="w-5 h-5" /> Crea il Tuo Festival
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 max-h-[60vh] overflow-y-auto">
            <div>
              <Label className="text-xs">Nome del Festival</Label>
              <Input value={newFestival.name} onChange={e => setNewFestival({...newFestival, name: e.target.value})} placeholder="Il Mio Festival..." className="bg-black/20 border-white/10" />
            </div>
            <div>
              <Label className="text-xs">Descrizione</Label>
              <Textarea value={newFestival.description} onChange={e => setNewFestival({...newFestival, description: e.target.value})} placeholder="Descrivi il tuo festival..." className="bg-black/20 border-white/10 h-20" />
            </div>
            <div>
              <Label className="text-xs">Categorie Premio</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {categoryOptions.map(cat => (
                  <Badge key={cat.id} variant={newFestival.categories.includes(cat.id) ? 'default' : 'outline'}
                    className={`cursor-pointer ${newFestival.categories.includes(cat.id) ? 'bg-purple-500' : 'hover:bg-white/10'}`}
                    onClick={() => {
                      if (newFestival.categories.includes(cat.id)) setNewFestival({...newFestival, categories: newFestival.categories.filter(c => c !== cat.id)});
                      else setNewFestival({...newFestival, categories: [...newFestival.categories, cat.id]});
                    }}>
                    {cat.name}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs">Costo Partecipazione</Label>
                <Input type="number" value={newFestival.base_participation_cost} onChange={e => setNewFestival({...newFestival, base_participation_cost: parseInt(e.target.value) || 10000})} className="bg-black/20 border-white/10" />
              </div>
              <div>
                <Label className="text-xs">Durata (giorni)</Label>
                <Input type="number" value={newFestival.duration_days} onChange={e => setNewFestival({...newFestival, duration_days: parseInt(e.target.value) || 7})} min={1} max={30} className="bg-black/20 border-white/10" />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Annulla</Button>
            <Button onClick={createCustomFestival} disabled={creating || !newFestival.name || newFestival.categories.length === 0} className="bg-purple-500">
              {creating ? 'Creazione...' : 'Crea Festival'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ═══ LEADERBOARD TAB ═══ */}
      {activeTab === 'leaderboard' && (
        <div>
          <div className="flex gap-2 mb-4 justify-center">
            {['monthly', 'yearly', 'all_time'].map(p => (
              <Button key={p} variant={leaderboardPeriod === p ? 'default' : 'outline'} size="sm" onClick={() => { setLeaderboardPeriod(p); loadLeaderboard(p); }} className={leaderboardPeriod === p ? 'bg-yellow-500 text-black' : ''}>
                {periodLabels[p]}
              </Button>
            ))}
          </div>
          <Card className="bg-[#141416] border-white/10">
            <CardHeader><CardTitle className="font-['Bebas_Neue'] text-xl">Classifica Premi - {periodLabels[leaderboardPeriod]}</CardTitle></CardHeader>
            <CardContent>
              {leaderboard?.leaderboard?.length > 0 ? (
                <div className="space-y-2">
                  {leaderboard.leaderboard.map((entry, i) => (
                    <div key={entry.user_id} className={`flex items-center gap-3 p-3 rounded-lg ${i < 3 ? 'bg-yellow-500/10' : 'bg-white/5'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${i === 0 ? 'bg-yellow-500 text-black' : i === 1 ? 'bg-gray-400 text-black' : i === 2 ? 'bg-amber-600 text-black' : 'bg-white/10'}`}>
                        {entry.rank}
                      </div>
                      <img src={entry.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${entry.nickname}`} alt="" className="w-10 h-10 rounded-full" />
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm truncate"><PlayerBadge badge={entry.badge} badgeExpiry={entry.badge_expiry} badges={entry.badges} size="sm" /><ClickableNickname userId={entry.user_id} nickname={entry.nickname} /></p>
                        <p className="text-xs text-gray-400">Lv.{entry.level} | {entry.fame} Fama</p>
                      </div>
                      <div className="text-right">
                        <p className="text-yellow-400 font-bold text-sm">{entry.total_awards} <Trophy className="w-3.5 h-3.5 inline" /></p>
                        <p className="text-[10px] text-gray-500">{entry.total_prestige} prestige</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-400 py-8">Nessun premio assegnato ancora</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ═══ MY AWARDS TAB ═══ */}
      {activeTab === 'my_awards' && (
        <div>
          {myAwards?.stats && (
            <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30 mb-6">
              <CardContent className="p-6">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <Trophy className="w-8 h-8 text-yellow-500 mx-auto mb-1" />
                    <p className="text-2xl font-bold text-yellow-400">{myAwards.stats.total_awards}</p>
                    <p className="text-xs text-gray-400">Premi Totali</p>
                  </div>
                  <div>
                    <Star className="w-8 h-8 text-purple-400 mx-auto mb-1" />
                    <p className="text-2xl font-bold text-purple-400">{Object.keys(myAwards.stats.by_festival).length}</p>
                    <p className="text-xs text-gray-400">Festival Vinti</p>
                  </div>
                  <div>
                    <Award className="w-8 h-8 text-pink-400 mx-auto mb-1" />
                    <p className="text-2xl font-bold text-pink-400">{Object.keys(myAwards.stats.by_category).length}</p>
                    <p className="text-xs text-gray-400">Categorie</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          <Card className="bg-[#141416] border-white/10">
            <CardHeader><CardTitle className="font-['Bebas_Neue'] text-xl">I Miei Premi</CardTitle></CardHeader>
            <CardContent>
              {myAwards?.awards?.length > 0 ? (
                <div className="space-y-2">
                  {myAwards.awards.map(award => (
                    <div key={award.id} className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                      <Award className="w-8 h-8 text-yellow-500 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-yellow-400 text-sm">{award.category_name}</p>
                        <p className="text-sm truncate">{award.winner_name}</p>
                        <p className="text-xs text-gray-400">{award.festival_name} | {award.film_title}</p>
                      </div>
                      <div className="text-right text-xs text-gray-500 flex-shrink-0">{award.month}/{award.year}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Trophy className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-400">Non hai ancora vinto premi. Partecipa ai festival!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ═══ HISTORY TAB ═══ */}
      {activeTab === 'history' && (
        <div data-testid="history-section">
          <Card className="bg-[#141416] border-white/10">
            <CardHeader>
              <CardTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-amber-500" /> Storico Cerimonie
              </CardTitle>
              <CardDescription>Tutte le edizioni passate e i vincitori</CardDescription>
            </CardHeader>
            <CardContent>
              {historyData.length > 0 ? (
                <div className="space-y-4">
                  {historyData.map(ed => (
                    <Card key={ed.edition_id} className="bg-white/5 border-white/10">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="font-['Bebas_Neue'] text-base text-yellow-400">{ed.festival_name}</CardTitle>
                          <Badge variant="outline" className="text-[10px]">{ed.month}/{ed.year}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="pb-3">
                        <div className="space-y-1.5">
                          {ed.winners?.map((w, i) => (
                            <div key={i} className="flex items-center gap-2 text-sm">
                              <Trophy className="w-3.5 h-3.5 text-yellow-500 flex-shrink-0" />
                              <span className="text-gray-400 text-xs w-28 truncate">{w.category}</span>
                              <span className="font-medium text-white truncate">{w.winner_name}</span>
                              {w.film_title && <span className="text-gray-500 text-xs truncate hidden sm:inline">({w.film_title})</span>}
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BookOpen className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-400">Nessuna cerimonia conclusa ancora.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ═══ LIVE CEREMONY OVERLAY (CINEMATIC) ═══ */}
      {showLiveCeremony && liveCeremony && (
        <CinematicCeremony
          festivalId={liveCeremony.festival_id}
          festivalName={liveCeremony.festival_name}
          edition={liveCeremony}
          rewards={liveCeremony.rewards}
          categories={liveCeremony.categories}
          chatMessages={liveCeremony.chat_messages}
          viewersCount={liveCeremony.viewers_count}
          onClose={closeLiveCeremony}
          onSendChat={async (message) => {
            try {
              await api.post('/festivals/ceremony/chat', { festival_id: liveCeremony.festival_id, edition_id: liveCeremony.edition_id, message });
              loadLiveCeremony(liveCeremony.festival_id);
            } catch (e) { toast.error(e.response?.data?.detail || 'Errore invio'); }
          }}
          sendingChat={sendingChat}
          onAnnounceWinner={async (categoryId) => {
            try {
              const res = await api.post(`/festivals/${liveCeremony.festival_id}/announce-winner/${categoryId}?language=it`);
              loadLiveCeremony(liveCeremony.festival_id);
              return res.data;
            } catch (e) {
              toast.error(e.response?.data?.detail || 'Errore annuncio');
              return null;
            }
          }}
        />
      )}
    </div>
  );
};

export default FestivalsPage;
