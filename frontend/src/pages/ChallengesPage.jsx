// CineWorld Studio's - ChallengesPage
// Extracted from App.js for modularity

import React, { useState, useEffect, useRef, useCallback, useMemo, useContext } from 'react';
import { useNavigate, useLocation, useSearchParams, useParams } from 'react-router-dom';
import { AuthContext, LanguageContext, PlayerPopupContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ScrollArea } from '../components/ui/scroll-area';
import { Slider } from '../components/ui/slider';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '../components/ui/alert-dialog';
import { Checkbox } from '../components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import {
  Film, Star, Award, TrendingUp, Clock, Play, Pause, Volume2, Users, Clapperboard,
  Send, Image, ChevronRight, ChevronDown, ChevronLeft, Menu, X, Settings,
  Zap, Globe, Trophy, Shield, Swords, Heart, MessageSquare, Bell, Home,
  Plus, Minus, Search, Filter, Trash2, Edit, Save, Copy, ExternalLink,
  Check, AlertCircle, Info, HelpCircle, Loader2, RefreshCw, Download,
  Eye, EyeOff, Lock, Unlock, Mail, Phone, Calendar, MapPin, Building,
  Sparkles, Flame, Target, Gamepad2, Music, Palette, Camera, Video,
  BookOpen, Newspaper, Gift, Crown, Medal, Gem, Coins, Wallet,
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, MoreHorizontal, MoreVertical,
  ChevronUp, ChevronsUpDown, Lightbulb, Megaphone, Share2, ThumbsUp,
  ThumbsDown, Bookmark, Flag, AlertTriangle, XCircle, CheckCircle,
  BarChart3, PieChart, Activity, Percent, DollarSign, Hash, AtSign,
  Scissors, Wand2, Brush, Layers, Grid, List, LayoutGrid, Table,
  CircleDollarSign, Store, Package, ShoppingCart, Tag, Receipt,
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding, History,
  Wifi, WifiOff
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { ClickableNickname } from '../components/shared';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const ChallengesPage = () => {
  const { user, api, refreshUser } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  
  // Helper for relative time display
  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const mins = Math.floor((now - date) / 60000);
    if (mins < 1) return 'ora';
    if (mins < 60) return `${mins} min fa`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h fa`;
    const days = Math.floor(hrs / 24);
    if (days === 1) return 'ieri';
    return `${days}g fa`;
  };
  
  const [view, setView] = useState('home'); // home, 1v1, 2v2, 3v3, 4v4, ffa, create, battle, leaderboard, pending, completed, history
  const [challengeType, setChallengeType] = useState(null);
  const [myFilms, setMyFilms] = useState([]);
  const [selectedFilms, setSelectedFilms] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [myChallenges, setMyChallenges] = useState([]);
  const [waitingChallenges, setWaitingChallenges] = useState([]);
  const [activeBattle, setActiveBattle] = useState(null);
  const [battleStep, setBattleStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [teamType, setTeamType] = useState('random');
  const [ffaPlayerCount, setFfaPlayerCount] = useState(4);
  const [opponentId, setOpponentId] = useState('');
  const [myStats, setMyStats] = useState(null);
  const [showTutorial, setShowTutorial] = useState(false);
  const [showPending, setShowPending] = useState(false);
  const [showCompleted, setShowCompleted] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [offlineMode, setOfflineMode] = useState(user?.accept_offline_challenges || false);
  const [offlinePlayers, setOfflinePlayers] = useState([]);
  const [offlineOpponent, setOfflineOpponent] = useState(null);
  const [showOfflineDialog, setShowOfflineDialog] = useState(false);
  const [offlineLoading, setOfflineLoading] = useState(false);
  const [challengeLimits, setChallengeLimits] = useState(null);
  const [lastCinepassReward, setLastCinepassReward] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [filmsRes, leaderboardRes, myChallengesRes, waitingRes, statsRes, limitsRes] = await Promise.all([
        api.get('/challenges/my-films'),
        api.get('/challenges/leaderboard'),
        api.get('/challenges/my'),
        api.get('/challenges/waiting'),
        api.get(`/challenges/stats/${user.id}`),
        api.get('/challenges/limits')
      ]);
      setMyFilms(filmsRes.data);
      setLeaderboard(leaderboardRes.data);
      setMyChallenges(myChallengesRes.data);
      setWaitingChallenges(waitingRes.data);
      setMyStats(statsRes.data);
      setChallengeLimits(limitsRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  // State for challenge mode selection
  const [challengeMode, setChallengeMode] = useState(null); // 'offline' | 'online'
  const [onlinePlayers, setOnlinePlayers] = useState([]);
  const [offlinePlayersList, setOfflinePlayersList] = useState([]);
  const [boosterFilmId, setBoosterFilmId] = useState(null); // Film to boost
  const [boosterActive, setBoosterActive] = useState(false);

  const loadPlayersForChallenge = async () => {
    try {
      const res = await api.get('/users/all-players');
      const players = Array.isArray(res.data) ? res.data : [];
      const others = players.filter(p => p.id !== user?.id);
      setOnlinePlayers(others.filter(p => p.is_online));
      setOfflinePlayersList(others.filter(p => !p.is_online));
    } catch (e) { 
      setOnlinePlayers([]); 
      setOfflinePlayersList([]); 
    }
  };

  const selectChallengeType = (type) => {
    setChallengeType(type);
    setSelectedFilms([]);
    setChallengeMode(null);
    setOpponentId('');
    setBoosterFilmId(null);
    setBoosterActive(false);
    setView('create');
  };

  // Booster cost: exponential based on film quality (worse film = higher cost)
  const getBoosterCost = (film) => {
    if (!film) return 0;
    const quality = film.quality_score || film.scores?.global || 50;
    // Inverse exponential: low quality = expensive, high quality = cheap
    // quality 20 → $80k, quality 50 → $40k, quality 80 → $15k, quality 100 → $5k
    const cost = Math.round(100000 * Math.exp(-quality / 40));
    return Math.max(5000, Math.min(100000, cost));
  };

  const toggleFilmSelection = (film) => {
    if (selectedFilms.find(f => f.id === film.id)) {
      setSelectedFilms(selectedFilms.filter(f => f.id !== film.id));
    } else if (selectedFilms.length < 3) {
      setSelectedFilms([...selectedFilms, film]);
    }
  };

  const createChallenge = async () => {
    if (selectedFilms.length !== 3) {
      toast.error('Seleziona esattamente 3 film!');
      return;
    }
    if (!opponentId) {
      toast.error('Seleziona un avversario!');
      return;
    }
    
    setLoading(true);
    try {
      const isOffline = challengeMode === 'offline';
      const res = await api.post('/challenges/create', {
        challenge_type: '1v1',
        film_ids: selectedFilms.map(f => f.id),
        opponent_id: opponentId,
        is_live: !isOffline,
        is_offline_challenge: isOffline,
        booster_film_id: boosterActive && boosterFilmId ? boosterFilmId : undefined
      });
      
      toast.success(res.data.message);
      
      if (res.data.result) {
        // Battle started immediately (offline auto-accept)
        setActiveBattle(res.data.result);
        setView('battle');
        runBattleAnimation(res.data.result);
      } else {
        // Online - waiting for opponent to accept
        setView('home');
        loadData();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore creazione sfida');
    } finally {
      setLoading(false);
    }
  };

  const joinChallenge = async (challengeId) => {
    if (selectedFilms.length !== 3) {
      toast.error(language === 'it' ? 'Seleziona 3 film prima!' : 'Select 3 films first!');
      return;
    }
    
    setLoading(true);
    try {
      const res = await api.post(`/challenges/${challengeId}/join`, selectedFilms.map(f => f.id));
      
      if (res.data.result) {
        setActiveBattle(res.data.result);
        setView('battle');
        runBattleAnimation(res.data.result);
      } else {
        toast.success(res.data.message);
        loadData();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setLoading(false);
    }
  };

  const viewBattleResult = async (challengeId) => {
    try {
      const res = await api.get(`/challenges/${challengeId}`);
      if (res.data.result) {
        setActiveBattle(res.data.result);
        setView('battle');
        setBattleStep(99); // Show final result
      }
    } catch (e) {
      toast.error('Errore caricamento sfida');
    }
  };

  const cancelChallenge = async (challengeId) => {
    try {
      await api.post(`/challenges/${challengeId}/cancel`);
      toast.success(language === 'it' ? 'Sfida annullata!' : 'Challenge cancelled!');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore annullamento');
    }
  };

  const resendChallenge = async (challengeId) => {
    try {
      await api.post(`/challenges/${challengeId}/resend`);
      toast.success(language === 'it' ? 'Sfida riproposta!' : 'Challenge resent!');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const toggleOfflineMode = async () => {
    try {
      const res = await api.post('/challenges/toggle-offline');
      setOfflineMode(res.data.accept_offline_challenges);
      toast.success(res.data.message);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const loadOfflinePlayers = async () => {
    try {
      const res = await api.get('/users/all-players');
      const players = Array.isArray(res.data) ? res.data : [];
      // Show ALL players (online and offline), exclude self
      setOfflinePlayers(players.filter(p => p.id !== user?.id));
    } catch (e) { setOfflinePlayers([]); }
  };

  const startOfflineBattle = async () => {
    if (!offlineOpponent || selectedFilms.length !== 3) {
      toast.error('Seleziona un avversario e 3 film!');
      return;
    }
    setOfflineLoading(true);
    try {
      const res = await api.post('/challenges/offline-battle', {
        opponent_id: offlineOpponent.id,
        film_ids: selectedFilms.map(f => f.id)
      });
      const cinepassBonus = res.data.cinepass_reward || 0;
      const cinepassMsg = cinepassBonus > 0 ? ` +${cinepassBonus} CinePass!` : '';
      toast.success(`Sfida completata! ${res.data.winner_name} vince!${cinepassMsg}`);
      setLastCinepassReward(cinepassBonus);
      refreshUser();
      setActiveBattle(res.data.result);
      setView('battle');
      runBattleAnimation(res.data.result);
      setShowOfflineDialog(false);
      setOfflineOpponent(null);
      setSelectedFilms([]);
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore sfida offline');
    } finally {
      setOfflineLoading(false);
    }
  };

  // Battle phrases pool - varied and exciting
  const battlePhrases = {
    win_dominant: [
      "Dominio assoluto! Nessuno può competere con questa potenza.",
      "Vittoria schiacciante! L'avversario non ha avuto scampo.",
      "Maestria pura! Un capolavoro di superiorità tecnica.",
      "Impressionante! La differenza di classe è evidente.",
      "Devastante! Come un uragano che spazza via tutto.",
    ],
    win_close: [
      "Per un soffio! La tensione era palpabile fino all'ultimo!",
      "Vittoria di misura! Il pubblico è in delirio!",
      "Che battaglia! Solo i dettagli hanno fatto la differenza.",
      "Incredibile! Un finale da brividi decide tutto.",
      "Adrenalina pura! Vince chi ha osato di più.",
    ],
    lose: [
      "Sconfitto... ma con onore! La prossima volta sarà diverso.",
      "Non è bastato... l'avversario era troppo forte stavolta.",
      "Caduti in battaglia, ma mai arresi!",
      "Bruciante sconfitta... il dolore della creatività tradita.",
      "Ci vuole coraggio per sfidare i migliori. Ritorna più forte!",
    ],
    draw: [
      "Pareggio perfetto! Due titani si equivalgono!",
      "Nessun vincitore, nessun perdente. Solo puro cinema!",
      "Equilibrio totale! Entrambi meritano la gloria.",
    ],
    skill_win: [
      "Colpo magistrale! {winner} domina in {skill}!",
      "{winner} non lascia scampo: {skill} superiore!",
      "Che classe! {winner} mostra la sua forza in {skill}.",
      "{skill} parla chiaro: {winner} è imbattibile!",
      "Netta superiorità! {winner} conquista {skill} con stile.",
      "Il pubblico applaude! {winner} eccelle in {skill}.",
      "{winner} dimostra perché è il migliore: {skill} perfetta!",
      "Standing ovation per {winner}! {skill} da manuale.",
    ],
    skill_close: [
      "Che duello in {skill}! {winner} vince per un pelo!",
      "{skill}: quasi pareggio, ma {winner} la spunta!",
      "Tensione alle stelle! {winner} strappa {skill} all'ultimo!",
      "Colpo di scena in {skill}! {winner} ribalta tutto!",
      "Il pubblico trattiene il fiato... {winner} vince {skill}!",
    ],
    skill_draw: [
      "Pareggio in {skill}! Due visioni si equivalgono!",
      "{skill}: impossibile separarli! Pari perfetto.",
      "Nessuno cede in {skill}! Un muro contro muro epico.",
    ]
  };

  const getRandomPhrase = (category, vars = {}) => {
    const pool = battlePhrases[category] || battlePhrases.win_close;
    let phrase = pool[Math.floor(Math.random() * pool.length)];
    Object.entries(vars).forEach(([k, v]) => { phrase = phrase.replace(`{${k}}`, v); });
    return phrase;
  };

  // Per-skill animation state
  const [currentSkillIndex, setCurrentSkillIndex] = useState(-1);
  const [skillPhrase, setSkillPhrase] = useState('');
  const [mancheComplete, setMancheComplete] = useState(false);

  const runBattleAnimation = (battle) => {
    setBattleStep(0);
    setCurrentSkillIndex(-1);
    setMancheComplete(false);
    setTimeout(() => setBattleStep(1), 2000);   // Teams
    setTimeout(() => { setBattleStep(2); animateSkills(battle, 0); }, 5000);
  };

  const animateSkills = (battle, matchIndex) => {
    const match = (battle.matches || [])[matchIndex];
    if (!match) return;
    const skills = match.skill_battles || [];
    setCurrentSkillIndex(-1);
    setMancheComplete(false);
    
    // Animate each skill: 2.5-4s per skill = ~20-32s for 8 skills
    const SKILL_DELAY = 3000; // 3s per skill
    skills.forEach((sb, i) => {
      setTimeout(() => {
        setCurrentSkillIndex(i);
        const winner = sb.winner === 'team_a' ? (battle.team_a?.name || 'Team A') : 
                       sb.winner === 'team_b' ? (battle.team_b?.name || 'Team B') : null;
        const skillName = sb.skill_name_it || sb.skill;
        if (!winner) {
          setSkillPhrase(getRandomPhrase('skill_draw', { skill: skillName }));
        } else {
          const diff = Math.abs((sb.team_a_power || 0) - (sb.team_b_power || 0));
          setSkillPhrase(getRandomPhrase(diff > 20 ? 'skill_win' : 'skill_close', { winner, skill: skillName }));
        }
      }, i * SKILL_DELAY);
    });
    
    // After all skills, show manche result then auto-advance
    const step = matchIndex + 2; // matchIndex 0 → step 2, 1 → step 3, 2 → step 4
    setTimeout(() => {
      setMancheComplete(true);
      // Auto-advance to next manche after 3 seconds
      setTimeout(() => {
        const nextStep = step + 1;
        if (nextStep <= 4) {
          setBattleStep(nextStep);
          setCurrentSkillIndex(-1);
          setMancheComplete(false);
          setTimeout(() => animateSkills(battle, nextStep - 2), 500);
        } else {
          setBattleStep(99);
        }
      }, 3000);
    }, skills.length * SKILL_DELAY + 500);
  };

  const getSkillIcon = (skill) => {
    const icons = {
      direction: '🎬', cinematography: '📷', screenplay: '📝', acting: '🎭',
      soundtrack: '🎵', effects: '💥', editing: '✂️', charisma: '⭐',
      drama: '🎭', comedy: '😂', action: '💥', horror: '👻',
      voice_acting: '🎙️', improvisation: '🎪', physical_acting: '🤸',
      emotional_depth: '💎', method_acting: '🎯', timing: '⏱️',
      vision: '👁️', leadership: '👑', storytelling: '📖', innovation: '💡',
      pacing: '🏃', atmosphere: '🌙', dialogue: '💬', originality: '✨',
      humor_writing: '😄', suspense_craft: '🔍', melodic: '🎹',
      orchestration: '🎼', emotional_scoring: '💗', genre_versatility: '🎪',
      sound_design: '🔊', rhythm: '🥁', harmony: '🎶'
    };
    return icons[skill] || '🎯';
  };

  const getSkillName = (skill) => {
    const names = {
      direction: language === 'it' ? 'Regia' : 'Direction',
      cinematography: language === 'it' ? 'Fotografia' : 'Cinematography',
      screenplay: language === 'it' ? 'Sceneggiatura' : 'Screenplay',
      acting: language === 'it' ? 'Recitazione' : 'Acting',
      soundtrack: language === 'it' ? 'Colonna Sonora' : 'Soundtrack',
      effects: language === 'it' ? 'Effetti' : 'Effects',
      editing: language === 'it' ? 'Montaggio' : 'Editing',
      charisma: language === 'it' ? 'Carisma' : 'Charisma'
    };
    return names[skill] || skill;
  };

  // HOME VIEW - Challenge Type Selection
  if (view === 'home') {
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="challenges-page">
        {/* Tutorial Modal */}
        <Dialog open={showTutorial} onOpenChange={setShowTutorial}>
          <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden bg-[#1A1A1A] border-pink-500/30">
            <DialogHeader>
              <DialogTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2 text-pink-400">
                <Lightbulb className="w-6 h-6" /> {language === 'it' ? 'COME FUNZIONANO LE SFIDE' : 'HOW CHALLENGES WORK'}
              </DialogTitle>
            </DialogHeader>
            <ScrollArea className="h-[60vh] pr-4">
              <div className="space-y-6 text-sm">
                {/* Step 1 */}
                <div className="bg-white/5 rounded-lg p-4">
                  <h3 className="font-bold text-yellow-400 mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 bg-yellow-500 text-black rounded-full flex items-center justify-center text-xs">1</span>
                    {language === 'it' ? 'Scegli la Modalità' : 'Choose Mode'}
                  </h3>
                  <p className="text-gray-300">
                    Seleziona la sfida 1v1 per un duello diretto contro un altro giocatore, online o offline!
                  </p>
                </div>

                {/* Step 2 */}
                <div className="bg-white/5 rounded-lg p-4">
                  <h3 className="font-bold text-orange-400 mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs">2</span>
                    {language === 'it' ? 'Seleziona 3 Film' : 'Select 3 Films'}
                  </h3>
                  <p className="text-gray-300">
                    {language === 'it' 
                      ? 'Scegli 3 dei tuoi film che sono in programmazione o completati. Ogni film ha 8 skill cinematografiche che determinano la sua forza in battaglia!'
                      : 'Choose 3 of your films that are in theaters or completed. Each film has 8 cinematic skills that determine its battle strength!'}
                  </p>
                </div>

                {/* Skills */}
                <div className="bg-white/5 rounded-lg p-4">
                  <h3 className="font-bold text-pink-400 mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 bg-pink-500 text-white rounded-full flex items-center justify-center text-xs">⚡</span>
                    {language === 'it' ? 'Le 8 Skill' : 'The 8 Skills'}
                  </h3>
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    {[
                      { icon: '🎬', name: language === 'it' ? 'Regia' : 'Direction' },
                      { icon: '📷', name: language === 'it' ? 'Fotografia' : 'Cinematography' },
                      { icon: '📝', name: language === 'it' ? 'Sceneggiatura' : 'Screenplay' },
                      { icon: '🎭', name: language === 'it' ? 'Recitazione' : 'Acting' },
                      { icon: '🎵', name: language === 'it' ? 'Colonna Sonora' : 'Soundtrack' },
                      { icon: '💥', name: language === 'it' ? 'Effetti' : 'Effects' },
                      { icon: '✂️', name: language === 'it' ? 'Montaggio' : 'Editing' },
                      { icon: '⭐', name: language === 'it' ? 'Carisma' : 'Charisma' }
                    ].map(skill => (
                      <div key={skill.name} className="bg-black/30 rounded p-2 text-xs flex items-center gap-2">
                        <span>{skill.icon}</span>
                        <span>{skill.name}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-gray-400 text-xs mt-2">
                    {language === 'it' ? 'Ogni skill va da 1 a 9 e contribuisce ai punteggi di Attacco e Difesa!' : 'Each skill ranges from 1-9 and contributes to Attack and Defense scores!'}
                  </p>
                </div>

                {/* Step 3 */}
                <div className="bg-white/5 rounded-lg p-4">
                  <h3 className="font-bold text-green-400 mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs">3</span>
                    {language === 'it' ? 'La Battaglia' : 'The Battle'}
                  </h3>
                  <p className="text-gray-300">
                    {language === 'it' 
                      ? 'La sfida si svolge in 3 manche! In ogni round, le skill dei tuoi film si scontrano con quelle avversarie. Chi vince più manche vince la sfida!'
                      : 'The challenge unfolds in 3 rounds! Each round, your films\' skills clash against the opponent\'s. Win more rounds to win the challenge!'}
                  </p>
                </div>

                {/* Rewards */}
                <div className="bg-gradient-to-r from-yellow-500/20 to-green-500/10 rounded-lg p-4 border border-yellow-500/30">
                  <h3 className="font-bold text-yellow-400 mb-2 flex items-center gap-2">
                    <Trophy className="w-5 h-5" />
                    {language === 'it' ? 'Premi e Bonus' : 'Rewards & Bonuses'}
                  </h3>
                  <div className="space-y-2 text-gray-300">
                    <p className="flex items-center gap-2">
                      <span className="text-yellow-400">$</span> 
                      Costo partecipazione: $50.000
                    </p>
                    <p className="flex items-center gap-2">
                      <span className="text-green-400">$</span> 
                      Vincitori: $100.000 (tutto il montepremi), +XP, +Fama, +Qualità Film
                    </p>
                    <p className="flex items-center gap-2">
                      <span className="text-red-400">-</span> 
                      Perdenti: +XP consolazione, -Fama, -Affluenze. Perdi il costo di partecipazione.
                    </p>
                  </div>
                </div>

                {/* Tips */}
                <div className="bg-purple-500/10 rounded-lg p-4 border border-purple-500/30">
                  <h3 className="font-bold text-purple-400 mb-2 flex items-center gap-2">
                    <Zap className="w-5 h-5" />
                    {language === 'it' ? 'Consigli Pro' : 'Pro Tips'}
                  </h3>
                  <ul className="space-y-1 text-gray-300 text-xs">
                    <li>• {language === 'it' ? 'Film con rating alto hanno skill migliori!' : 'Higher rated films have better skills!'}</li>
                    <li>• {language === 'it' ? 'I film premiati ai festival hanno bonus Carisma!' : 'Award-winning films get Charisma bonuses!'}</li>
                    <li>• {language === 'it' ? 'Bilancia attacco e difesa per una squadra equilibrata!' : 'Balance attack and defense for a balanced team!'}</li>
                    <li>• {language === 'it' ? 'Le sfide live danno +20% bonus premi!' : 'Live challenges give +20% bonus rewards!'}</li>
                  </ul>
                </div>
              </div>
            </ScrollArea>
            <div className="mt-4">
              <Button onClick={() => setShowTutorial(false)} className="w-full bg-pink-500 hover:bg-pink-600">
                {language === 'it' ? 'Ho capito, sfidiamoci!' : 'Got it, let\'s battle!'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Pending Challenges Dialog */}
        <Dialog open={showPending} onOpenChange={setShowPending}>
          <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden bg-[#1A1A1A] border-yellow-500/30">
            <DialogHeader>
              <DialogTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2 text-yellow-400">
                <Clock className="w-6 h-6" /> {language === 'it' ? 'SFIDE IN SOSPESO' : 'PENDING CHALLENGES'}
              </DialogTitle>
            </DialogHeader>
            <ScrollArea className="h-[60vh] pr-4">
              <div className="space-y-3">
                {myChallenges.filter(c => c.status === 'waiting' || c.status === 'pending').length === 0 ? (
                  <div className="text-center py-8">
                    <Clock className="w-12 h-12 mx-auto mb-3 text-gray-500" />
                    <p className="text-gray-400">{language === 'it' ? 'Nessuna sfida in sospeso' : 'No pending challenges'}</p>
                  </div>
                ) : (
                  myChallenges.filter(c => c.status === 'waiting' || c.status === 'pending').map(c => (
                    <Card key={c.id} className="bg-yellow-500/10 border-yellow-500/20">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <p className="font-bold text-lg">{c.type.toUpperCase()}</p>
                            <p className="text-xs text-gray-400">
                              {c.participants?.length || 1}/{c.required_players || 2} {language === 'it' ? 'giocatori' : 'players'}
                            </p>
                          </div>
                          <Badge className="bg-yellow-500/20 text-yellow-400">
                            {c.status === 'waiting' ? (language === 'it' ? 'In Attesa' : 'Waiting') : 'Pending'}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-400 mb-3">
                          {language === 'it' ? 'Creata il' : 'Created'}: {new Date(c.created_at).toLocaleString()}
                        </p>
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-black"
                            onClick={() => resendChallenge(c.id)}
                          >
                            <RefreshCw className="w-4 h-4 mr-1" /> {language === 'it' ? 'Riproponi' : 'Resend'}
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            className="flex-1 border-red-500/30 text-red-400 hover:bg-red-500/10"
                            onClick={() => cancelChallenge(c.id)}
                          >
                            <X className="w-4 h-4 mr-1" /> {language === 'it' ? 'Annulla' : 'Cancel'}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </DialogContent>
        </Dialog>

        {/* Completed Challenges Dialog */}
        <Dialog open={showCompleted} onOpenChange={setShowCompleted}>
          <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden bg-[#1A1A1A] border-green-500/30">
            <DialogHeader>
              <DialogTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2 text-green-400">
                <CheckCircle className="w-6 h-6" /> {language === 'it' ? 'SFIDE COMPLETATE' : 'COMPLETED CHALLENGES'}
              </DialogTitle>
            </DialogHeader>
            <ScrollArea className="h-[60vh] pr-4">
              <div className="space-y-3">
                {myChallenges.filter(c => c.status === 'completed').length === 0 ? (
                  <div className="text-center py-8">
                    <Trophy className="w-12 h-12 mx-auto mb-3 text-gray-500" />
                    <p className="text-gray-400">{language === 'it' ? 'Nessuna sfida completata' : 'No completed challenges'}</p>
                  </div>
                ) : (
                  myChallenges.filter(c => c.status === 'completed').map(c => {
                    const isWinner = c.result?.winner === 'team_a' && c.participants?.find(p => p.user_id === user.id)?.team === 'a' ||
                                     c.result?.winner === 'team_b' && c.participants?.find(p => p.user_id === user.id)?.team === 'b';
                    return (
                      <Card 
                        key={c.id} 
                        className={`cursor-pointer hover:scale-[1.01] transition-transform ${isWinner ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'}`}
                        onClick={() => { setShowCompleted(false); viewBattleResult(c.id); }}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className={`p-3 rounded-lg ${isWinner ? 'bg-green-500' : 'bg-red-500'}`}>
                                {isWinner ? <Trophy className="w-5 h-5" /> : <X className="w-5 h-5" />}
                              </div>
                              <div>
                                <p className="font-bold">{c.type.toUpperCase()}</p>
                                <p className="text-xs text-gray-400">{new Date(c.completed_at).toLocaleString()}</p>
                              </div>
                            </div>
                            <Badge className={isWinner ? 'bg-green-500' : 'bg-red-500'}>
                              {isWinner ? (language === 'it' ? 'VITTORIA' : 'VICTORY') : (language === 'it' ? 'SCONFITTA' : 'DEFEAT')}
                            </Badge>
                          </div>
                          {c.result && (
                            <div className="mt-3 pt-3 border-t border-white/10 text-xs text-gray-400">
                              {c.result.team_a?.name} {c.result.team_a?.rounds_won} - {c.result.team_b?.rounds_won} {c.result.team_b?.name}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })
                )}
              </div>
            </ScrollArea>
          </DialogContent>
        </Dialog>

        {/* History Dialog */}
        <Dialog open={showHistory} onOpenChange={setShowHistory}>
          <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden bg-[#1A1A1A] border-blue-500/30">
            <DialogHeader>
              <DialogTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2 text-blue-400">
                <History className="w-6 h-6" /> {language === 'it' ? 'STORICO SFIDE' : 'CHALLENGE HISTORY'}
              </DialogTitle>
            </DialogHeader>
            <ScrollArea className="h-[60vh] pr-4">
              <div className="space-y-3">
                {myChallenges.length === 0 ? (
                  <div className="text-center py-8">
                    <History className="w-12 h-12 mx-auto mb-3 text-gray-500" />
                    <p className="text-gray-400">{language === 'it' ? 'Nessuna sfida nel tuo storico' : 'No challenges in your history'}</p>
                  </div>
                ) : (
                  myChallenges.map(c => {
                    const isWinner = c.status === 'completed' && (
                      c.result?.winner === 'team_a' && c.participants?.find(p => p.user_id === user.id)?.team === 'a' ||
                      c.result?.winner === 'team_b' && c.participants?.find(p => p.user_id === user.id)?.team === 'b'
                    );
                    return (
                      <Card 
                        key={c.id} 
                        className={`${
                          c.status === 'completed' 
                            ? (isWinner ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20')
                            : c.status === 'cancelled' 
                              ? 'bg-gray-500/5 border-gray-500/20' 
                              : 'bg-yellow-500/5 border-yellow-500/20'
                        } cursor-pointer hover:bg-white/5`}
                        onClick={() => c.status === 'completed' && viewBattleResult(c.id)}
                      >
                        <CardContent className="p-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-lg ${
                                c.status === 'completed' 
                                  ? (isWinner ? 'bg-green-500' : 'bg-red-500')
                                  : c.status === 'cancelled' 
                                    ? 'bg-gray-500' 
                                    : 'bg-yellow-500'
                              }`}>
                                {c.status === 'completed' 
                                  ? (isWinner ? <Trophy className="w-4 h-4" /> : <X className="w-4 h-4" />)
                                  : c.status === 'cancelled' 
                                    ? <X className="w-4 h-4" />
                                    : <Clock className="w-4 h-4 text-black" />
                                }
                              </div>
                              <div>
                                <p className="font-semibold text-sm">{c.type.toUpperCase()}</p>
                                <p className="text-[10px] text-gray-500">{new Date(c.created_at).toLocaleDateString()}</p>
                              </div>
                            </div>
                            <Badge className={`text-[10px] ${
                              c.status === 'completed' 
                                ? (isWinner ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400')
                                : c.status === 'cancelled' 
                                  ? 'bg-gray-500/20 text-gray-400' 
                                  : 'bg-yellow-500/20 text-yellow-400'
                            }`}>
                              {c.status === 'completed' 
                                ? (isWinner ? (language === 'it' ? 'Vinta' : 'Won') : (language === 'it' ? 'Persa' : 'Lost'))
                                : c.status === 'cancelled' 
                                  ? (language === 'it' ? 'Annullata' : 'Cancelled')
                                  : (language === 'it' ? 'In attesa' : 'Waiting')
                              }
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })
                )}
              </div>
            </ScrollArea>
          </DialogContent>
        </Dialog>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => navigate('/')} className="p-1"><ArrowLeft className="w-5 h-5" /></Button>
              <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2">
                <Swords className="w-8 h-8 text-pink-500" />
                {language === 'it' ? 'SFIDE' : 'CHALLENGES'}
              </h1>
            </div>
            <div className="flex gap-1">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowHistory(true)}
                className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10 px-2"
                title={language === 'it' ? 'Storico' : 'History'}
              >
                <History className="w-4 h-4" />
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowPending(true)}
                className="border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10 px-2 relative"
                title={language === 'it' ? 'In Sospeso' : 'Pending'}
              >
                <Clock className="w-4 h-4" />
                {myChallenges.filter(c => c.status === 'waiting' || c.status === 'pending').length > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-500 rounded-full text-[10px] text-black flex items-center justify-center">
                    {myChallenges.filter(c => c.status === 'waiting' || c.status === 'pending').length}
                  </span>
                )}
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowCompleted(true)}
                className="border-green-500/30 text-green-400 hover:bg-green-500/10 px-2"
                title={language === 'it' ? 'Completate' : 'Completed'}
              >
                <CheckCircle className="w-4 h-4" />
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowTutorial(true)}
                className="border-pink-500/30 text-pink-400 hover:bg-pink-500/10"
                data-testid="tutorial-btn"
              >
                <Lightbulb className="w-4 h-4 mr-1" /> Tutorial
              </Button>
            </div>
          </div>
          <p className="text-gray-400 text-sm">{language === 'it' ? 'Sfida altri giocatori con i tuoi film!' : 'Challenge other players with your films!'}</p>
        </motion.div>

        {/* My Stats Card */}
        {myStats && (
          <Card className="bg-gradient-to-r from-pink-500/20 to-purple-500/10 border-pink-500/30 mb-4">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-pink-500 rounded-lg"><Trophy className="w-6 h-6 text-white" /></div>
                  <div>
                    <h3 className="font-['Bebas_Neue'] text-xl">{language === 'it' ? 'LE TUE STATISTICHE' : 'YOUR STATS'}</h3>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-green-400">🏆 {myStats.wins} {language === 'it' ? 'Vittorie' : 'Wins'}</span>
                      <span className="text-red-400">💔 {myStats.losses} {language === 'it' ? 'Sconfitte' : 'Losses'}</span>
                      <span className="text-yellow-400">🔥 {myStats.current_streak} Streak</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-pink-400">{myStats.win_rate}%</p>
                  <p className="text-xs text-gray-400">Win Rate</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Challenge Limits */}
        {challengeLimits && (
          <div className="flex items-center gap-3 mb-4 text-xs">
            <div className="flex items-center gap-1.5 px-2 py-1 bg-white/5 rounded-lg border border-white/10">
              <Clock className="w-3 h-3 text-orange-400" />
              <span className="text-gray-400">Ora:</span>
              <span className={challengeLimits.hourly.used >= challengeLimits.hourly.limit ? 'text-red-400 font-bold' : 'text-white font-bold'}>
                {challengeLimits.hourly.used}/{challengeLimits.hourly.limit}
              </span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 bg-white/5 rounded-lg border border-white/10">
              <Calendar className="w-3 h-3 text-blue-400" />
              <span className="text-gray-400">Giorno:</span>
              <span className={challengeLimits.daily.used >= challengeLimits.daily.limit ? 'text-red-400 font-bold' : 'text-white font-bold'}>
                {challengeLimits.daily.used}/{challengeLimits.daily.limit}
              </span>
            </div>
          </div>
        )}

        {/* Challenge Type Grid - Only 1v1 */}
        <Card 
          className="bg-gradient-to-br from-red-500/20 to-red-600/5 border-red-500/20 cursor-pointer hover:scale-[1.02] transition-transform mb-4" 
          onClick={() => selectChallengeType('1v1')}
          data-testid="challenge-1v1"
        >
          <CardContent className="p-5 flex items-center gap-4">
            <div className="p-4 bg-red-500 rounded-full w-16 h-16 flex items-center justify-center flex-shrink-0">
              <span className="text-2xl font-bold">1v1</span>
            </div>
            <div className="flex-1">
              <h3 className="font-['Bebas_Neue'] text-xl">SFIDA 1 VS 1</h3>
              <p className="text-xs text-gray-400">Sfida diretta contro un altro giocatore (online o offline)</p>
              <div className="flex items-center gap-3 mt-2">
                <Badge className="bg-yellow-500/20 text-yellow-400">
                  <Coins className="w-3 h-3 mr-1" /> Costo: $50.000
                </Badge>
                <Badge className="bg-green-500/20 text-green-400">
                  <Trophy className="w-3 h-3 mr-1" /> Premio: $100.000
                </Badge>
                <Badge className="bg-cyan-500/20 text-cyan-400">
                  +{challengeLimits?.cinepass_reward_per_win || 2} CinePass
                </Badge>
              </div>
            </div>
            <ChevronRight className="w-6 h-6 text-gray-500" />
          </CardContent>
        </Card>

        {/* Offline Challenge Dialog */}
        <Dialog open={showOfflineDialog} onOpenChange={setShowOfflineDialog}>
          <DialogContent className="bg-[#1A1A1A] border-cyan-500/20 max-w-lg max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-['Bebas_Neue'] text-xl text-cyan-400 flex items-center gap-2">
                <Swords className="w-5 h-5" /> SFIDA OFFLINE VS
              </DialogTitle>
              <DialogDescription>Scegli un avversario e 3 film. L'AI sceglierà i migliori film dell'avversario.</DialogDescription>
            </DialogHeader>
            
            {/* Step 1: Select opponent */}
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-cyan-400">1. Scegli Avversario</h4>
              <ScrollArea className="h-32 border border-white/10 rounded-lg p-2">
                {offlinePlayers.length === 0 ? (
                  <p className="text-xs text-gray-500 text-center py-4">Nessun giocatore disponibile per sfide offline</p>
                ) : (
                  <div className="space-y-1">
                    {offlinePlayers.map(p => (
                      <div
                        key={p.id}
                        onClick={() => setOfflineOpponent(p)}
                        className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${offlineOpponent?.id === p.id ? 'bg-cyan-500/20 border border-cyan-500/40' : 'hover:bg-white/5'}`}
                        data-testid={`offline-player-${p.id}`}
                      >
                        <Avatar className="w-7 h-7"><AvatarFallback className="bg-cyan-500/20 text-cyan-400 text-xs">{p.nickname?.[0]}</AvatarFallback></Avatar>
                        <div className="flex-1">
                          <p className="text-sm font-semibold">{p.nickname}</p>
                          <p className="text-[10px] text-gray-400">{p.production_house_name}</p>
                        </div>
                        <Badge className={`text-[10px] ${p.is_online ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                          {p.is_online ? 'Online' : timeAgo(p.last_active) || 'Offline'}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </div>

            {/* Step 2: Select films */}
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-yellow-400">2. Scegli 3 Film ({selectedFilms.length}/3)</h4>
              <ScrollArea className="h-36 border border-white/10 rounded-lg p-2">
                <div className="space-y-1">
                  {myFilms.map(film => (
                    <div
                      key={film.id}
                      onClick={() => toggleFilmSelection(film)}
                      className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${selectedFilms.find(f => f.id === film.id) ? 'bg-yellow-500/20 border border-yellow-500/40' : 'hover:bg-white/5'}`}
                    >
                      <div className="flex-1">
                        <p className="text-sm font-semibold">{film.title}</p>
                        <p className="text-[10px] text-gray-400">{film.genre} | Q:{film.quality_score}</p>
                      </div>
                      {selectedFilms.find(f => f.id === film.id) && <Check className="w-4 h-4 text-yellow-400" />}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>

            <DialogFooter>
              <Button variant="outline" size="sm" onClick={() => setShowOfflineDialog(false)}>Annulla</Button>
              <Button
                onClick={startOfflineBattle}
                disabled={!offlineOpponent || selectedFilms.length !== 3 || offlineLoading}
                className="bg-gradient-to-r from-cyan-600 to-blue-600 text-white"
                data-testid="start-offline-battle-btn"
              >
                {offlineLoading ? 'Combattimento...' : 'Lancia Sfida!'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <Button 
            variant="outline" 
            className="border-pink-500/30 text-pink-400 h-12"
            onClick={() => setView('leaderboard')}
          >
            <Trophy className="w-4 h-4 mr-2" /> {language === 'it' ? 'Classifica' : 'Leaderboard'}
          </Button>
          <Button 
            variant="outline" 
            className="border-blue-500/30 text-blue-400 h-12"
            onClick={() => setShowHistory(true)}
          >
            <History className="w-4 h-4 mr-2" /> {language === 'it' ? 'Storico' : 'History'}
          </Button>
        </div>

        {/* Waiting Challenges */}
        {waitingChallenges.length > 0 && (
          <Card className="bg-[#1A1A1A] border-white/5 mb-4">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                <Clock className="w-4 h-4 text-yellow-500" /> {language === 'it' ? 'Sfide in Attesa' : 'Waiting Challenges'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {waitingChallenges.slice(0, 5).map(c => (
                <div key={c.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div>
                    <p className="font-semibold">{c.type.toUpperCase()} - {c.creator_nickname}</p>
                    <p className="text-xs text-gray-400">{c.participants?.length || 1}/{c.required_players || 2} {language === 'it' ? 'giocatori' : 'players'}</p>
                  </div>
                  <Button size="sm" onClick={() => { setSelectedFilms([]); viewBattleResult(c.id); }} className="bg-pink-500 hover:bg-pink-600">
                    {language === 'it' ? 'Unisciti' : 'Join'}
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Recent Challenges */}
        {myChallenges.filter(c => c.status === 'completed').length > 0 && (
          <Card className="bg-[#1A1A1A] border-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                <History className="w-4 h-4 text-blue-500" /> {language === 'it' ? 'Sfide Recenti' : 'Recent Challenges'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {myChallenges.filter(c => c.status === 'completed').slice(0, 5).map(c => {
                const isWinner = c.result?.winner === 'team_a' && c.participants?.find(p => p.user_id === user.id)?.team === 'a' ||
                                 c.result?.winner === 'team_b' && c.participants?.find(p => p.user_id === user.id)?.team === 'b';
                return (
                  <div key={c.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10" onClick={() => viewBattleResult(c.id)}>
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${isWinner ? 'bg-green-500' : 'bg-red-500'}`}>
                        {isWinner ? <Trophy className="w-4 h-4" /> : <X className="w-4 h-4" />}
                      </div>
                      <div>
                        <p className="font-semibold">{c.type.toUpperCase()}</p>
                        <p className="text-xs text-gray-400">{new Date(c.completed_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <Badge className={isWinner ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}>
                      {isWinner ? (language === 'it' ? 'Vittoria' : 'Victory') : (language === 'it' ? 'Sconfitta' : 'Defeat')}
                    </Badge>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // CREATE VIEW - Film Selection then Mode Choice
  if (view === 'create') {
    // Sub-view: choose mode (after selecting 3 films and pressing LANCIA)
    if (challengeMode === 'choose') {
      return (
        <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Button variant="ghost" size="sm" onClick={() => setChallengeMode(null)} className="p-1"><ArrowLeft className="w-5 h-5" /></Button>
              <h1 className="font-['Bebas_Neue'] text-3xl">SCEGLI TIPO SFIDA</h1>
            </div>
            <p className="text-gray-400 text-sm">Film selezionati: {selectedFilms.map(f => f.title).join(', ')}</p>
          </motion.div>

          <div className="grid grid-cols-1 gap-4">
            {/* OFFLINE */}
            <Card 
              className="bg-gradient-to-br from-cyan-500/20 to-blue-600/5 border-cyan-500/20 cursor-pointer hover:scale-[1.02] transition-transform"
              onClick={() => { setChallengeMode('offline'); loadPlayersForChallenge(); }}
              data-testid="mode-offline"
            >
              <CardContent className="p-5 flex items-center gap-4">
                <div className="p-4 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full w-16 h-16 flex items-center justify-center flex-shrink-0">
                  <WifiOff className="w-7 h-7 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-['Bebas_Neue'] text-xl text-cyan-400">SFIDA OFFLINE</h3>
                  <p className="text-xs text-gray-400">Sfida un giocatore offline. La sfida viene sempre accettata automaticamente!</p>
                  <Badge className="mt-2 bg-cyan-500/20 text-cyan-400 text-[10px]">Accettata automaticamente</Badge>
                </div>
                <ChevronRight className="w-6 h-6 text-gray-500" />
              </CardContent>
            </Card>

            {/* ONLINE */}
            <Card 
              className="bg-gradient-to-br from-green-500/20 to-emerald-600/5 border-green-500/20 cursor-pointer hover:scale-[1.02] transition-transform"
              onClick={() => { setChallengeMode('online'); loadPlayersForChallenge(); }}
              data-testid="mode-online"
            >
              <CardContent className="p-5 flex items-center gap-4">
                <div className="p-4 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full w-16 h-16 flex items-center justify-center flex-shrink-0">
                  <Wifi className="w-7 h-7 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-['Bebas_Neue'] text-xl text-green-400">SFIDA ONLINE</h3>
                  <p className="text-xs text-gray-400">Sfida un giocatore online. Riceverà una notifica popup per accettare o rifiutare.</p>
                  <Badge className="mt-2 bg-green-500/20 text-green-400 text-[10px]">Notifica in tempo reale</Badge>
                </div>
                <ChevronRight className="w-6 h-6 text-gray-500" />
              </CardContent>
            </Card>
          </div>

          {/* Cost reminder */}
          <Card className="bg-gradient-to-r from-yellow-500/10 to-green-500/5 border-yellow-500/30 mt-4">
            <CardContent className="p-3 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm">
                <Coins className="w-4 h-4 text-yellow-400" />
                <span className="text-yellow-400 font-semibold">Costo: $50.000</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Trophy className="w-4 h-4 text-green-400" />
                <span className="text-green-400 font-semibold">Premio: $100.000</span>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    // Sub-view: Offline player selection
    if (challengeMode === 'offline') {
      return (
        <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Button variant="ghost" size="sm" onClick={() => setChallengeMode('choose')} className="p-1"><ArrowLeft className="w-5 h-5" /></Button>
              <h1 className="font-['Bebas_Neue'] text-3xl text-cyan-400">SFIDA OFFLINE</h1>
            </div>
            <p className="text-gray-400 text-sm">Scegli un avversario offline. La sfida sarà accettata automaticamente.</p>
          </motion.div>

          <ScrollArea className="h-[400px] border border-white/10 rounded-lg mb-4">
            {offlinePlayersList.length === 0 ? (
              <p className="text-xs text-gray-500 text-center py-12">Nessun giocatore offline trovato</p>
            ) : (
              <div className="space-y-1 p-2">
                {offlinePlayersList.map(p => (
                  <div
                    key={p.id}
                    onClick={() => setOpponentId(p.id)}
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${opponentId === p.id ? 'bg-cyan-500/20 border border-cyan-500/40' : 'hover:bg-white/5'}`}
                    data-testid={`offline-player-${p.id}`}
                  >
                    <Avatar className="w-9 h-9"><AvatarFallback className="bg-cyan-500/20 text-cyan-400 text-sm">{p.nickname?.[0]}</AvatarFallback></Avatar>
                    <div className="flex-1">
                      <p className="text-sm font-semibold">{p.nickname}</p>
                      <p className="text-[10px] text-gray-400">{p.production_house_name} {p.level ? `• Lv.${p.level}` : ''}</p>
                    </div>
                    <Badge className="bg-gray-500/20 text-gray-400 text-[10px]">{timeAgo(p.last_active) || 'Offline'}</Badge>
                    {opponentId === p.id && <CheckCircle className="w-5 h-5 text-cyan-400" />}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          <div className="fixed bottom-20 left-0 right-0 p-3 bg-gradient-to-t from-[#0D0D0D] to-transparent">
            <Button 
              className="w-full h-12 bg-cyan-500 hover:bg-cyan-600 font-['Bebas_Neue'] text-lg"
              onClick={() => { createChallenge(); }}
              disabled={!opponentId || loading}
              data-testid="launch-offline-btn"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : (
                <><Swords className="w-5 h-5 mr-2" /> LANCIA SFIDA OFFLINE ($50.000)</>
              )}
            </Button>
          </div>
        </div>
      );
    }

    // Sub-view: Online player selection
    if (challengeMode === 'online') {
      return (
        <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Button variant="ghost" size="sm" onClick={() => setChallengeMode('choose')} className="p-1"><ArrowLeft className="w-5 h-5" /></Button>
              <h1 className="font-['Bebas_Neue'] text-3xl text-green-400">SFIDA ONLINE</h1>
            </div>
            <p className="text-gray-400 text-sm">Scegli un avversario online. Riceverà una notifica popup per accettare.</p>
          </motion.div>

          {onlinePlayers.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/5 mb-4">
              <CardContent className="p-8 text-center">
                <Wifi className="w-12 h-12 mx-auto mb-3 text-gray-500" />
                <p className="text-gray-400">Nessun giocatore online al momento</p>
                <p className="text-xs text-gray-500 mt-2">Riprova più tardi o sfida un giocatore offline</p>
                <Button variant="outline" className="mt-3 border-cyan-500/30 text-cyan-400" onClick={() => setChallengeMode('choose')}>
                  Torna alla scelta
                </Button>
              </CardContent>
            </Card>
          ) : (
            <ScrollArea className="h-[400px] border border-white/10 rounded-lg mb-4">
              <div className="space-y-1 p-2">
                {onlinePlayers.map(p => (
                  <div
                    key={p.id}
                    onClick={() => setOpponentId(p.id)}
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${opponentId === p.id ? 'bg-green-500/20 border border-green-500/40' : 'hover:bg-white/5'}`}
                    data-testid={`online-player-${p.id}`}
                  >
                    <div className="relative">
                      <Avatar className="w-9 h-9"><AvatarFallback className="bg-green-500/20 text-green-400 text-sm">{p.nickname?.[0]}</AvatarFallback></Avatar>
                      <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-[#0D0D0D]"></div>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold">{p.nickname}</p>
                      <p className="text-[10px] text-gray-400">{p.production_house_name} {p.level ? `• Lv.${p.level}` : ''}</p>
                    </div>
                    <Badge className="bg-green-500/20 text-green-400 text-[10px]">Online</Badge>
                    {opponentId === p.id && <CheckCircle className="w-5 h-5 text-green-400" />}
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}

          {onlinePlayers.length > 0 && (
            <div className="fixed bottom-20 left-0 right-0 p-3 bg-gradient-to-t from-[#0D0D0D] to-transparent">
              <Button 
                className="w-full h-12 bg-green-500 hover:bg-green-600 font-['Bebas_Neue'] text-lg"
                onClick={() => { createChallenge(); }}
                disabled={!opponentId || loading}
                data-testid="launch-online-btn"
              >
                {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : (
                  <><Swords className="w-5 h-5 mr-2" /> INVIA SFIDA ONLINE ($50.000)</>
                )}
              </Button>
            </div>
          )}
        </div>
      );
    }

    // Main create view: Film Selection
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Button variant="ghost" size="sm" onClick={() => setView('home')} className="p-1"><ArrowLeft className="w-5 h-5" /></Button>
            <h1 className="font-['Bebas_Neue'] text-3xl">CREA SFIDA 1v1</h1>
          </div>
          <p className="text-gray-400 text-sm">Seleziona 3 film per la sfida</p>
        </motion.div>

        {/* Cost Info Banner */}
        <Card className="bg-gradient-to-r from-yellow-500/10 to-green-500/5 border-yellow-500/30 mb-4">
          <CardContent className="p-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <Coins className="w-4 h-4 text-yellow-400" />
              <span className="text-yellow-400 font-semibold">Costo: $50.000</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Trophy className="w-4 h-4 text-green-400" />
              <span className="text-green-400 font-semibold">Premio: $100.000</span>
            </div>
          </CardContent>
        </Card>

        {/* Selected Films */}
        <Card className="bg-gradient-to-r from-pink-500/20 to-purple-500/10 border-pink-500/30 mb-4">
          <CardContent className="p-4">
            <h3 className="font-['Bebas_Neue'] text-lg mb-3">FILM SELEZIONATI ({selectedFilms.length}/3)</h3>
            <div className="flex gap-2">
              {[0, 1, 2].map(i => (
                <div key={i} className={`flex-1 h-24 rounded-lg border-2 border-dashed flex items-center justify-center ${selectedFilms[i] ? 'border-pink-500 bg-pink-500/10' : 'border-gray-600'}`}>
                  {selectedFilms[i] ? (
                    <div className="text-center p-2">
                      <p className="text-xs font-semibold truncate max-w-[80px]">{selectedFilms[i].title}</p>
                      <p className="text-[10px] text-pink-400">{selectedFilms[i].scores?.global}</p>
                    </div>
                  ) : (
                    <Plus className="w-6 h-6 text-gray-500" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Film Grid */}
        <h3 className="font-['Bebas_Neue'] text-lg mb-3">I TUOI FILM</h3>
        {myFilms.length === 0 ? (
          <Card className="bg-[#1A1A1A] border-white/5">
            <CardContent className="p-8 text-center">
              <Film className="w-12 h-12 mx-auto mb-3 text-gray-500" />
              <p className="text-gray-400">Non hai film disponibili per le sfide.</p>
              <p className="text-xs text-gray-500 mt-2">Crea film e portali nei cinema!</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {myFilms.map(film => {
              const isSelected = selectedFilms.find(f => f.id === film.id);
              return (
                <Card 
                  key={film.id}
                  className={`cursor-pointer transition-all ${isSelected ? 'border-pink-500 bg-pink-500/10' : 'bg-[#1A1A1A] border-white/5 hover:border-white/20'}`}
                  onClick={() => toggleFilmSelection(film)}
                >
                  <CardContent className="p-3">
                    <div className="flex gap-3">
                      {film.poster_url && (
                        <img src={film.poster_url} alt={film.title} className="w-16 h-24 object-cover rounded" />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold truncate max-w-[150px]">{film.title}</h4>
                          {isSelected && <CheckCircle className="w-5 h-5 text-pink-500" />}
                        </div>
                        <div className="grid grid-cols-4 gap-1 mb-2">
                          {Object.entries(film.skills || {}).slice(0, 4).map(([skill, value]) => (
                            <div key={skill} className="text-center bg-black/30 rounded p-1">
                              <p className="text-[10px]">{getSkillIcon(skill)}</p>
                              <p className="text-xs font-bold">{value}</p>
                            </div>
                          ))}
                        </div>
                        <div className="flex gap-2 text-xs">
                          <span className="text-yellow-400">Punteggio: {film.scores?.global}</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* LANCIA SFIDA - goes to mode selection */}
        <div className="fixed bottom-20 left-0 right-0 p-3 bg-gradient-to-t from-[#0D0D0D] to-transparent">
          {/* Booster System */}
          {selectedFilms.length === 3 && (
            <div className="mb-2 p-2 bg-orange-500/10 border border-orange-500/30 rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-orange-400 flex items-center gap-1">
                  <Flame className="w-3 h-3" /> BOOSTER (opzionale)
                </span>
                <Button
                  size="sm"
                  variant={boosterActive ? 'default' : 'outline'}
                  className={`h-5 text-[10px] ${boosterActive ? 'bg-orange-500 text-white' : 'border-orange-500/30 text-orange-400'}`}
                  onClick={() => setBoosterActive(!boosterActive)}
                >
                  {boosterActive ? 'Attivo' : 'Attiva'}
                </Button>
              </div>
              {boosterActive && (
                <div className="flex gap-1">
                  {selectedFilms.map(f => {
                    const cost = getBoosterCost(f);
                    return (
                      <div
                        key={f.id}
                        onClick={() => setBoosterFilmId(f.id)}
                        className={`flex-1 p-1.5 rounded text-center cursor-pointer transition-colors ${
                          boosterFilmId === f.id ? 'bg-orange-500/20 border border-orange-500' : 'bg-white/5 hover:bg-white/10'
                        }`}
                      >
                        <p className="text-[9px] font-semibold truncate">{f.title}</p>
                        <p className="text-[10px] text-orange-400">${cost.toLocaleString()}</p>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
          <Button 
            className="w-full h-12 bg-pink-500 hover:bg-pink-600 font-['Bebas_Neue'] text-lg"
            onClick={() => setChallengeMode('choose')}
            disabled={selectedFilms.length !== 3}
            data-testid="launch-challenge-btn"
          >
            <Swords className="w-5 h-5 mr-2" /> LANCIA SFIDA! ({selectedFilms.length}/3 film)
          </Button>
        </div>
      </div>
    );
  }

  // BATTLE VIEW - Animation
  if (view === 'battle' && activeBattle) {
    const battle = activeBattle;
    
    return (
      <div className="fixed inset-0 bg-black z-50 flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-pink-500/10 via-transparent to-purple-500/10 pointer-events-none" />
        
        {/* Close button - always visible */}
        <Button
          variant="ghost"
          size="sm"
          className="absolute top-4 right-4 z-[60] text-white/60 hover:text-white bg-black/40 hover:bg-black/60 rounded-full w-10 h-10 p-0"
          onClick={() => { setView('home'); setActiveBattle(null); setBattleStep(0); loadData(); }}
          data-testid="battle-close-btn"
        >
          <X className="w-5 h-5" />
        </Button>
        
        {/* Skip animation button - visible during rounds */}
        {battleStep < 99 && battleStep > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="absolute bottom-6 right-4 z-[60] text-white/40 hover:text-white text-xs"
            onClick={() => setBattleStep(99)}
            data-testid="battle-skip-btn"
          >
            {language === 'it' ? 'Salta >' : 'Skip >'}
          </Button>
        )}
        
        <AnimatePresence mode="wait">
          {/* Intro */}
          {battleStep === 0 && (
            <motion.div
              key="intro"
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0, opacity: 0 }}
              className="text-center"
            >
              <Swords className="w-24 h-24 text-pink-500 mx-auto mb-4" />
              <h1 className="font-['Bebas_Neue'] text-4xl mb-2">{battle.intro}</h1>
              <p className="text-gray-400">{language === 'it' ? 'La sfida sta per iniziare...' : 'The battle is about to begin...'}</p>
            </motion.div>
          )}

          {/* Team Presentation */}
          {battleStep === 1 && (
            <motion.div
              key="teams"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full max-w-4xl px-4"
            >
              <h2 className="font-['Bebas_Neue'] text-2xl text-center mb-6">{language === 'it' ? 'PRESENTAZIONE SQUADRE' : 'TEAM PRESENTATION'}</h2>
              <div className="grid grid-cols-2 gap-8">
                {/* Team A */}
                <motion.div
                  initial={{ x: -100, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="text-center"
                >
                  <div className="p-4 bg-red-500/20 rounded-lg border border-red-500/30 mb-4">
                    <h3 className="font-['Bebas_Neue'] text-2xl text-red-400">{battle.team_a?.name || 'Team A'}</h3>
                    <p className="text-yellow-400">⚡ {battle.team_a?.scores?.global}</p>
                  </div>
                  <div className="space-y-2">
                    {battle.team_a?.films?.slice(0, 3).map((f, i) => (
                      <div key={i} className="bg-white/5 rounded p-2 text-sm truncate">{f.title}</div>
                    ))}
                  </div>
                </motion.div>

                {/* Team B */}
                <motion.div
                  initial={{ x: 100, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className="text-center"
                >
                  <div className="p-4 bg-blue-500/20 rounded-lg border border-blue-500/30 mb-4">
                    <h3 className="font-['Bebas_Neue'] text-2xl text-blue-400">{battle.team_b?.name || 'Team B'}</h3>
                    <p className="text-yellow-400">⚡ {battle.team_b?.scores?.global}</p>
                  </div>
                  <div className="space-y-2">
                    {battle.team_b?.films?.slice(0, 3).map((f, i) => (
                      <div key={i} className="bg-white/5 rounded p-2 text-sm truncate">{f.title}</div>
                    ))}
                  </div>
                </motion.div>
              </div>
            </motion.div>
          )}

          {/* Manche 1, 2, 3 - Animated skill by skill */}
          {[2, 3, 4].map(step => {
            const matchIndex = step - 2;
            const match = (battle.matches || [])[matchIndex];
            if (battleStep !== step || !match) return null;
            
            return (
              <motion.div
                key={`match-${step}`}
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -40 }}
                className="w-full max-w-lg px-4"
              >
                {/* Manche Header */}
                <div className="text-center mb-4">
                  <motion.p 
                    className="text-xs text-pink-400 font-bold tracking-widest mb-1"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  >
                    MANCHE {matchIndex + 1}/3
                  </motion.p>
                  <h2 className="font-['Bebas_Neue'] text-xl">
                    <span className="text-red-400">{match.film_a?.title}</span>
                    <span className="text-gray-500 mx-2 text-base">VS</span>
                    <span className="text-blue-400">{match.film_b?.title}</span>
                  </h2>
                </div>
                
                {/* Skill Battles - revealed one by one */}
                <div className="space-y-1.5 mb-3">
                  {match.skill_battles.map((sb, si) => {
                    const revealed = si <= currentSkillIndex;
                    const isCurrent = si === currentSkillIndex;
                    const aWin = sb.winner === 'team_a';
                    const bWin = sb.winner === 'team_b';
                    const totalPower = Math.max((sb.team_a_power || 0) + (sb.team_b_power || 0), 1);
                    
                    if (!revealed) return (
                      <div key={si} className="p-2 rounded-lg border border-white/5 bg-white/2 h-10 flex items-center justify-center">
                        <div className="w-4 h-4 rounded-full bg-white/10 animate-pulse" />
                      </div>
                    );
                    
                    return (
                      <motion.div
                        key={si}
                        initial={{ scale: 0.8, opacity: 0, rotateX: -20 }}
                        animate={{ 
                          scale: isCurrent ? 1.03 : 1, 
                          opacity: 1, 
                          rotateX: 0,
                          boxShadow: isCurrent ? '0 0 20px rgba(236,72,153,0.3)' : '0 0 0 transparent'
                        }}
                        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                        className={`p-2 rounded-lg border transition-all ${
                          isCurrent ? 'border-pink-500/50 bg-pink-500/10' :
                          aWin ? 'border-red-500/20 bg-red-500/5' :
                          bWin ? 'border-blue-500/20 bg-blue-500/5' :
                          'border-white/10 bg-white/5'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <motion.span 
                            className="text-lg"
                            animate={isCurrent ? { scale: [1, 1.3, 1] } : {}}
                            transition={{ duration: 0.5 }}
                          >
                            {getSkillIcon(sb.skill || '')}
                          </motion.span>
                          <span className="text-xs font-semibold flex-1 truncate">{sb.skill_name_it || sb.skill}</span>
                          <motion.span 
                            className={`text-sm font-bold min-w-[24px] text-right ${aWin ? 'text-green-400' : 'text-gray-500'}`}
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
                          >
                            {sb.team_a_value}
                          </motion.span>
                          <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden flex">
                            <motion.div 
                              className="h-full bg-red-500 rounded-l-full" 
                              initial={{ width: '50%' }}
                              animate={{ width: `${((sb.team_a_power || 0) / totalPower) * 100}%` }}
                              transition={{ delay: 0.4, duration: 0.6 }}
                            />
                            <motion.div 
                              className="h-full bg-blue-500 rounded-r-full"
                              initial={{ width: '50%' }}
                              animate={{ width: `${((sb.team_b_power || 0) / totalPower) * 100}%` }}
                              transition={{ delay: 0.4, duration: 0.6 }}
                            />
                          </div>
                          <motion.span 
                            className={`text-sm font-bold min-w-[24px] ${bWin ? 'text-green-400' : 'text-gray-500'}`}
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
                          >
                            {sb.team_b_value}
                          </motion.span>
                          {sb.is_upset && <Badge className="bg-orange-500/80 text-[8px] px-1 ml-1">SORPRESA!</Badge>}
                        </div>
                        {/* Animated phrase for current skill */}
                        {isCurrent && (
                          <motion.p 
                            className="text-[10px] text-pink-300/80 mt-1 italic pl-7"
                            initial={{ opacity: 0, y: 5 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                          >
                            {skillPhrase}
                          </motion.p>
                        )}
                        {!isCurrent && sb.comment && (
                          <p className="text-[10px] text-gray-500 mt-0.5 italic pl-7">{sb.comment}</p>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
                
                {/* Tiebreaker */}
                {mancheComplete && match.tiebreaker && (
                  <motion.div 
                    initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                    className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30 text-center mb-3"
                  >
                    <p className="text-xs font-bold text-yellow-400 mb-1">{match.tiebreaker.name_it || 'Spareggio!'}</p>
                    <div className="flex justify-center gap-4 text-sm">
                      <span className={match.tiebreaker.winner === 'team_a' ? 'text-green-400 font-bold' : 'text-gray-400'}>{match.tiebreaker.team_a_value}</span>
                      <span className="text-gray-500">vs</span>
                      <span className={match.tiebreaker.winner === 'team_b' ? 'text-green-400 font-bold' : 'text-gray-400'}>{match.tiebreaker.team_b_value}</span>
                    </div>
                  </motion.div>
                )}
                
                {/* Match Result - shown after all skills revealed */}
                {mancheComplete && (
                  <motion.div 
                    initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                    className="text-center mt-3"
                  >
                    <div className="flex justify-center gap-6 text-2xl font-bold mb-2">
                      <span className="text-red-400">{match.team_a_skill_wins}</span>
                      <span className="text-gray-500">-</span>
                      <span className="text-blue-400">{match.team_b_skill_wins}</span>
                    </div>
                    <Badge className={`text-sm px-4 py-1 ${
                      match.winner === 'team_a' ? 'bg-red-500/30 text-red-300' :
                      match.winner === 'team_b' ? 'bg-blue-500/30 text-blue-300' :
                      'bg-yellow-500/30 text-yellow-300'
                    }`}>
                      {match.winner === 'team_a' ? `${battle.team_a?.name} VINCE LA MANCHE!` :
                       match.winner === 'team_b' ? `${battle.team_b?.name} VINCE LA MANCHE!` :
                       'PAREGGIO!'}
                    </Badge>
                    
                    {/* Auto-advance indicator */}
                    <div className="mt-3 flex items-center justify-center gap-2 text-xs text-gray-400">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      {step < 4 ? 'Prossima manche...' : 'Risultato finale...'}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            );
          })}

          {/* Final Result - Victory/Defeat Animation */}
          {battleStep === 99 && (() => {
            const isWinner = (battle.winner === 'team_a' && battle.team_a?.players?.includes(user?.id)) ||
                             (battle.winner === 'team_b' && battle.team_b?.players?.includes(user?.id));
            const isDraw = battle.winner === 'draw';
            const winnerName = battle.winner === 'team_a' ? battle.team_a?.name : battle.team_b?.name;
            const loserName = battle.winner === 'team_a' ? battle.team_b?.name : battle.team_a?.name;

            return (
              <motion.div
                key="final"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="text-center max-w-md px-4 relative"
              >
                {/* Victory particles */}
                {(isWinner || isDraw) && (
                  <div className="absolute inset-0 pointer-events-none overflow-hidden">
                    {[...Array(20)].map((_, i) => (
                      <motion.div
                        key={i}
                        className={`absolute w-2 h-2 rounded-full ${['bg-yellow-400', 'bg-pink-400', 'bg-green-400', 'bg-blue-400'][i % 4]}`}
                        initial={{ 
                          x: '50%', y: '50%', opacity: 1, scale: 0 
                        }}
                        animate={{ 
                          x: `${Math.random() * 100}%`, 
                          y: `${Math.random() * 100}%`, 
                          opacity: [1, 1, 0], 
                          scale: [0, 1.5, 0],
                          rotate: Math.random() * 360
                        }}
                        transition={{ duration: 2 + Math.random() * 2, delay: Math.random() * 0.5, repeat: Infinity, repeatDelay: 1 }}
                      />
                    ))}
                  </div>
                )}

                {/* Defeat dark overlay */}
                {!isWinner && !isDraw && (
                  <motion.div 
                    className="absolute inset-0 pointer-events-none" 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-b from-red-900/20 to-transparent rounded-3xl" />
                  </motion.div>
                )}

                {/* Icon */}
                <motion.div
                  animate={isWinner || isDraw ? { scale: [1, 1.15, 1], rotate: [0, 5, -5, 0] } : { opacity: [0.5, 1, 0.5] }}
                  transition={{ repeat: Infinity, duration: isWinner ? 1.5 : 3 }}
                >
                  {isWinner ? (
                    <Trophy className="w-24 h-24 text-yellow-500 mx-auto mb-4 drop-shadow-[0_0_30px_rgba(234,179,8,0.5)]" />
                  ) : isDraw ? (
                    <Handshake className="w-24 h-24 text-yellow-400 mx-auto mb-4" />
                  ) : (
                    <Shield className="w-24 h-24 text-red-400/60 mx-auto mb-4" />
                  )}
                </motion.div>
                
                {/* Title */}
                <motion.h1 
                  className={`font-['Bebas_Neue'] text-4xl mb-2 ${isWinner ? 'text-yellow-400' : isDraw ? 'text-yellow-300' : 'text-red-400'}`}
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3 }}
                >
                  {isWinner ? 'VITTORIA!' : isDraw ? 'PAREGGIO!' : 'SCONFITTA'}
                </motion.h1>
                
                <motion.p 
                  className="text-gray-300 mb-4 text-sm italic"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}
                >
                  {isWinner ? getRandomPhrase('win_dominant') : isDraw ? getRandomPhrase('draw') : getRandomPhrase('lose')}
                </motion.p>
                
                {/* Scores */}
                <motion.div 
                  className="flex justify-center gap-4 mb-4"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
                >
                  <div className={`p-3 rounded-lg ${battle.winner === 'team_a' || isDraw ? 'bg-green-500/20 border-2 border-green-500' : 'bg-red-500/20 border-2 border-red-500/50'}`}>
                    <p className="font-['Bebas_Neue'] text-lg">{battle.team_a?.name}</p>
                    <p className="text-2xl font-bold">{battle.team_a?.rounds_won}</p>
                  </div>
                  <div className="flex items-center text-xl text-gray-500 font-bold">VS</div>
                  <div className={`p-3 rounded-lg ${battle.winner === 'team_b' || isDraw ? 'bg-green-500/20 border-2 border-green-500' : 'bg-red-500/20 border-2 border-red-500/50'}`}>
                    <p className="font-['Bebas_Neue'] text-lg">{battle.team_b?.name}</p>
                    <p className="text-2xl font-bold">{battle.team_b?.rounds_won}</p>
                  </div>
                </motion.div>
                
                {/* Prize info */}
                {isWinner && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.8 }}
                    className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 mb-4"
                  >
                    <p className="text-yellow-400 font-bold text-lg">+$100.000</p>
                    {lastCinepassReward > 0 && (
                      <p className="text-cyan-400 font-bold text-lg" data-testid="cinepass-reward-display">+{lastCinepassReward} CinePass</p>
                    )}
                    <p className="text-xs text-gray-400">Montepremi incassato!</p>
                  </motion.div>
                )}

                {/* Buttons */}
                <motion.div 
                  className="flex gap-2 mt-4"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}
                >
                  <Button 
                    className="flex-1 bg-pink-500 hover:bg-pink-600 font-['Bebas_Neue'] text-base"
                    onClick={() => { setView('home'); setActiveBattle(null); setBattleStep(0); loadData(); }}
                    data-testid="battle-continue-btn"
                  >
                    CONTINUA
                  </Button>
                  <Button 
                    variant="outline"
                    className="flex-1 border-pink-500/40 text-pink-400 hover:bg-pink-500/10 font-['Bebas_Neue'] text-base"
                    onClick={() => {
                      const oppId = battle.team_a?.players?.[0] === user?.id 
                        ? battle.team_b?.players?.[0] 
                        : battle.team_a?.players?.[0];
                      if (oppId) {
                        setOpponentId(oppId);
                        setSelectedFilms([]);
                        setChallengeMode(null);
                        setActiveBattle(null);
                        setBattleStep(0);
                        setView('create');
                      }
                    }}
                    data-testid="counter-challenge-btn"
                  >
                    <Swords className="w-4 h-4 mr-1" /> CONTRO-SFIDA
                  </Button>
                </motion.div>
              </motion.div>
            );
          })()}
        </AnimatePresence>
      </div>
    );
  }

  // LEADERBOARD VIEW
  if (view === 'leaderboard') {
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Button variant="ghost" size="sm" onClick={() => setView('home')} className="p-1"><ArrowLeft className="w-5 h-5" /></Button>
            <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2">
              <Trophy className="w-8 h-8 text-yellow-500" />
              {language === 'it' ? 'CLASSIFICA SFIDE' : 'CHALLENGE LEADERBOARD'}
            </h1>
          </div>
        </motion.div>

        <div className="space-y-2">
          {leaderboard.map((entry, i) => (
            <Card 
              key={entry.user_id} 
              className={`${i < 3 ? 'bg-gradient-to-r from-yellow-500/20 to-transparent border-yellow-500/30' : 'bg-[#1A1A1A] border-white/5'}`}
            >
              <CardContent className="p-3 flex items-center gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                  i === 0 ? 'bg-yellow-500 text-black' : 
                  i === 1 ? 'bg-gray-400 text-black' : 
                  i === 2 ? 'bg-orange-600 text-white' : 'bg-white/10'
                }`}>
                  {i + 1}
                </div>
                <div className="flex-1">
                  <p className="font-semibold"><ClickableNickname userId={entry.user_id} nickname={entry.nickname} /></p>
                  <p className="text-xs text-gray-400">{entry.wins}W / {entry.losses}L</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-pink-400">{entry.win_rate}%</p>
                  <p className="text-xs text-gray-400">Win Rate</p>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {leaderboard.length === 0 && (
            <Card className="bg-[#1A1A1A] border-white/5">
              <CardContent className="p-8 text-center">
                <Trophy className="w-12 h-12 mx-auto mb-3 text-gray-500" />
                <p className="text-gray-400">{language === 'it' ? 'Nessuna sfida completata ancora.' : 'No challenges completed yet.'}</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    );
  }

  return null;
};

// Mini Games Page with REAL Questions

export default ChallengesPage;
