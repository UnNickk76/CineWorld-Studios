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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding, History
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { ClickableNickname } from '../components/shared';

// useTranslations imported from contexts

const ChallengesPage = () => {
  const { user, api } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
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

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [filmsRes, leaderboardRes, myChallengesRes, waitingRes, statsRes] = await Promise.all([
        api.get('/challenges/my-films'),
        api.get('/challenges/leaderboard'),
        api.get('/challenges/my'),
        api.get('/challenges/waiting'),
        api.get(`/challenges/stats/${user.id}`)
      ]);
      setMyFilms(filmsRes.data);
      setLeaderboard(leaderboardRes.data);
      setMyChallenges(myChallengesRes.data);
      setWaitingChallenges(waitingRes.data);
      setMyStats(statsRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  const selectChallengeType = (type) => {
    setChallengeType(type);
    setSelectedFilms([]);
    setView('create');
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
      toast.error(language === 'it' ? 'Seleziona esattamente 3 film!' : 'Select exactly 3 films!');
      return;
    }
    
    setLoading(true);
    try {
      const res = await api.post('/challenges/create', {
        challenge_type: challengeType,
        film_ids: selectedFilms.map(f => f.id),
        team_type: ['2v2', '3v3', '4v4'].includes(challengeType) ? teamType : undefined,
        opponent_id: challengeType === '1v1' && opponentId ? opponentId : undefined,
        ffa_player_count: challengeType === 'ffa' ? ffaPlayerCount : undefined,
        is_live: true
      });
      
      toast.success(res.data.message);
      
      if (res.data.result) {
        // Battle started immediately
        setActiveBattle(res.data.result);
        setView('battle');
        runBattleAnimation(res.data.result);
      } else {
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
      const players = (Array.isArray(res.data) ? res.data : []).filter(
        p => p.accept_offline_challenges && p.id !== user.id
      );
      setOfflinePlayers(players);
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
      toast.success(`Sfida completata! ${res.data.winner_name} vince!`);
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

  const runBattleAnimation = (battle) => {
    setBattleStep(0);
    setTimeout(() => setBattleStep(1), 2000);   // Teams
    setTimeout(() => setBattleStep(2), 5000);   // Manche 1
    setTimeout(() => setBattleStep(3), 12000);  // Manche 2
    setTimeout(() => setBattleStep(4), 19000);  // Manche 3
    setTimeout(() => setBattleStep(99), 25000); // Final Result
  };

  const getSkillIcon = (skill) => {
    const icons = {
      direction: '🎬', cinematography: '📷', screenplay: '📝', acting: '🎭',
      soundtrack: '🎵', effects: '💥', editing: '✂️', charisma: '⭐'
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
                    {language === 'it' 
                      ? 'Seleziona il tipo di sfida: 1v1 per duelli diretti, 2v2/3v3/4v4 per battaglie a squadre, o Tutti contro Tutti per il caos totale!'
                      : 'Select challenge type: 1v1 for direct duels, 2v2/3v3/4v4 for team battles, or Free For All for total chaos!'}
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
                      <span className="text-green-400">🏆</span> 
                      {language === 'it' ? 'Vincitori: +XP, +Fama, +CineCoins, +Qualità Film, +Affluenze' : 'Winners: +XP, +Fame, +CineCoins, +Film Quality, +Attendance'}
                    </p>
                    <p className="flex items-center gap-2">
                      <span className="text-red-400">💔</span> 
                      {language === 'it' ? 'Perdenti: +XP consolazione, -Fama, -Affluenze' : 'Losers: +consolation XP, -Fame, -Attendance'}
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

        {/* Challenge Type Grid */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <Card 
            className="bg-gradient-to-br from-red-500/20 to-red-600/5 border-red-500/20 cursor-pointer hover:scale-[1.02] transition-transform" 
            onClick={() => selectChallengeType('1v1')}
            data-testid="challenge-1v1"
          >
            <CardContent className="p-4 text-center">
              <div className="p-4 bg-red-500 rounded-full w-16 h-16 mx-auto mb-3 flex items-center justify-center">
                <span className="text-2xl font-bold">1v1</span>
              </div>
              <h3 className="font-['Bebas_Neue'] text-xl">1 VS 1</h3>
              <p className="text-xs text-gray-400">{language === 'it' ? 'Sfida diretta' : 'Direct duel'}</p>
            </CardContent>
          </Card>

          <Card 
            className="bg-gradient-to-br from-orange-500/20 to-orange-600/5 border-orange-500/20 cursor-pointer hover:scale-[1.02] transition-transform" 
            onClick={() => selectChallengeType('2v2')}
            data-testid="challenge-2v2"
          >
            <CardContent className="p-4 text-center">
              <div className="p-4 bg-orange-500 rounded-full w-16 h-16 mx-auto mb-3 flex items-center justify-center">
                <span className="text-2xl font-bold">2v2</span>
              </div>
              <h3 className="font-['Bebas_Neue'] text-xl">2 VS 2</h3>
              <p className="text-xs text-gray-400">{language === 'it' ? 'Squadre da 2' : '2-player teams'}</p>
            </CardContent>
          </Card>

          <Card 
            className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border-yellow-500/20 cursor-pointer hover:scale-[1.02] transition-transform" 
            onClick={() => selectChallengeType('3v3')}
            data-testid="challenge-3v3"
          >
            <CardContent className="p-4 text-center">
              <div className="p-4 bg-yellow-500 rounded-full w-16 h-16 mx-auto mb-3 flex items-center justify-center">
                <span className="text-2xl font-bold text-black">3v3</span>
              </div>
              <h3 className="font-['Bebas_Neue'] text-xl">3 VS 3</h3>
              <p className="text-xs text-gray-400">{language === 'it' ? 'Squadre da 3' : '3-player teams'}</p>
            </CardContent>
          </Card>

          <Card 
            className="bg-gradient-to-br from-green-500/20 to-green-600/5 border-green-500/20 cursor-pointer hover:scale-[1.02] transition-transform" 
            onClick={() => selectChallengeType('4v4')}
            data-testid="challenge-4v4"
          >
            <CardContent className="p-4 text-center">
              <div className="p-4 bg-green-500 rounded-full w-16 h-16 mx-auto mb-3 flex items-center justify-center">
                <span className="text-2xl font-bold">4v4</span>
              </div>
              <h3 className="font-['Bebas_Neue'] text-xl">4 VS 4</h3>
              <p className="text-xs text-gray-400">{language === 'it' ? 'Squadre da 4' : '4-player teams'}</p>
            </CardContent>
          </Card>
        </div>

        {/* Free For All */}
        <Card 
          className="bg-gradient-to-br from-purple-500/20 to-pink-500/10 border-purple-500/20 cursor-pointer hover:scale-[1.01] transition-transform mb-4" 
          onClick={() => selectChallengeType('ffa')}
          data-testid="challenge-ffa"
        >
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg">
              <Flame className="w-8 h-8 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="font-['Bebas_Neue'] text-xl">{language === 'it' ? 'TUTTI CONTRO TUTTI' : 'FREE FOR ALL'}</h3>
              <p className="text-sm text-gray-400">{language === 'it' ? 'Da 4 a 10 giocatori, tutti contro tutti!' : '4-10 players battle royale!'}</p>
            </div>
            <ChevronRight className="w-6 h-6 text-gray-500" />
          </CardContent>
        </Card>

        {/* Offline Challenge Section - Same style as online challenges */}
        <Card 
          className="bg-gradient-to-br from-cyan-500/20 to-blue-600/5 border-cyan-500/20 cursor-pointer hover:scale-[1.01] transition-transform mb-4"
          onClick={() => { loadOfflinePlayers(); setShowOfflineDialog(true); setSelectedFilms([]); }}
          data-testid="offline-challenge-btn"
        >
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-4 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="font-['Bebas_Neue'] text-xl text-cyan-400">SFIDA OFFLINE VS</h3>
              <p className="text-sm text-gray-400">{language === 'it' ? "Sfida un giocatore offline! L'AI sceglie i suoi film." : "Challenge an offline player! AI picks their films."}</p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <Button
                size="sm"
                variant={offlineMode ? "default" : "outline"}
                className={offlineMode ? "bg-cyan-600 hover:bg-cyan-500 text-white h-7 text-xs" : "border-cyan-500/30 text-cyan-400 h-7 text-xs"}
                onClick={(e) => { e.stopPropagation(); toggleOfflineMode(); }}
                data-testid="toggle-offline-btn"
              >
                {offlineMode ? (language === 'it' ? 'Accetto Sfide' : 'Accepting') : (language === 'it' ? 'Non Accetto' : 'Not Accepting')}
              </Button>
              <ChevronRight className="w-5 h-5 text-gray-500" />
            </div>
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
                          {p.is_online ? 'Online' : 'Offline'}
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
            onClick={() => loadData()}
          >
            <RefreshCw className="w-4 h-4 mr-2" /> {language === 'it' ? 'Aggiorna' : 'Refresh'}
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

  // CREATE VIEW - Film Selection
  if (view === 'create') {
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Button variant="ghost" size="sm" onClick={() => setView('home')} className="p-1"><ArrowLeft className="w-5 h-5" /></Button>
            <h1 className="font-['Bebas_Neue'] text-3xl">
              {language === 'it' ? 'CREA SFIDA' : 'CREATE CHALLENGE'} - {challengeType?.toUpperCase()}
            </h1>
          </div>
          <p className="text-gray-400 text-sm">{language === 'it' ? 'Seleziona 3 film per la sfida' : 'Select 3 films for the challenge'}</p>
        </motion.div>

        {/* Selected Films */}
        <Card className="bg-gradient-to-r from-pink-500/20 to-purple-500/10 border-pink-500/30 mb-4">
          <CardContent className="p-4">
            <h3 className="font-['Bebas_Neue'] text-lg mb-3">{language === 'it' ? 'FILM SELEZIONATI' : 'SELECTED FILMS'} ({selectedFilms.length}/3)</h3>
            <div className="flex gap-2">
              {[0, 1, 2].map(i => (
                <div key={i} className={`flex-1 h-24 rounded-lg border-2 border-dashed flex items-center justify-center ${selectedFilms[i] ? 'border-pink-500 bg-pink-500/10' : 'border-gray-600'}`}>
                  {selectedFilms[i] ? (
                    <div className="text-center p-2">
                      <p className="text-xs font-semibold truncate max-w-[80px]">{selectedFilms[i].title}</p>
                      <p className="text-[10px] text-pink-400">⚡ {selectedFilms[i].scores.global}</p>
                    </div>
                  ) : (
                    <Plus className="w-6 h-6 text-gray-500" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Team Options for 2v2+ */}
        {['2v2', '3v3', '4v4'].includes(challengeType) && (
          <Card className="bg-[#1A1A1A] border-white/5 mb-4">
            <CardContent className="p-4">
              <h3 className="font-['Bebas_Neue'] text-lg mb-3">{language === 'it' ? 'TIPO SQUADRA' : 'TEAM TYPE'}</h3>
              <div className="grid grid-cols-3 gap-2">
                {['random', 'friends', 'major'].map(type => (
                  <Button 
                    key={type}
                    variant={teamType === type ? 'default' : 'outline'}
                    className={teamType === type ? 'bg-pink-500' : ''}
                    onClick={() => setTeamType(type)}
                  >
                    {type === 'random' ? '🎲 Random' : type === 'friends' ? '👥 Amici' : '🏢 Major'}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* FFA Player Count */}
        {challengeType === 'ffa' && (
          <Card className="bg-[#1A1A1A] border-white/5 mb-4">
            <CardContent className="p-4">
              <h3 className="font-['Bebas_Neue'] text-lg mb-3">{language === 'it' ? 'NUMERO GIOCATORI' : 'PLAYER COUNT'}: {ffaPlayerCount}</h3>
              <Slider 
                value={[ffaPlayerCount]} 
                onValueChange={(v) => setFfaPlayerCount(v[0])}
                min={4} 
                max={10} 
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>4</span>
                <span>10</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Film Grid */}
        <h3 className="font-['Bebas_Neue'] text-lg mb-3">{language === 'it' ? 'I TUOI FILM' : 'YOUR FILMS'}</h3>
        {myFilms.length === 0 ? (
          <Card className="bg-[#1A1A1A] border-white/5">
            <CardContent className="p-8 text-center">
              <Film className="w-12 h-12 mx-auto mb-3 text-gray-500" />
              <p className="text-gray-400">{language === 'it' ? 'Non hai film disponibili per le sfide.' : 'You have no films available for challenges.'}</p>
              <p className="text-xs text-gray-500 mt-2">{language === 'it' ? 'Crea film e portali nei cinema!' : 'Create films and release them!'}</p>
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
                        
                        {/* Skills */}
                        <div className="grid grid-cols-4 gap-1 mb-2">
                          {Object.entries(film.skills).slice(0, 4).map(([skill, value]) => (
                            <div key={skill} className="text-center bg-black/30 rounded p-1">
                              <p className="text-[10px]">{getSkillIcon(skill)}</p>
                              <p className="text-xs font-bold">{value}</p>
                            </div>
                          ))}
                        </div>
                        
                        {/* Scores */}
                        <div className="flex gap-2 text-xs">
                          <span className="text-yellow-400">⚡ {film.scores.global}</span>
                          <span className="text-red-400">⚔️ {film.scores.attack}</span>
                          <span className="text-blue-400">🛡️ {film.scores.defense}</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Create Button */}
        <div className="fixed bottom-20 left-0 right-0 p-3 bg-gradient-to-t from-[#0D0D0D] to-transparent">
          <Button 
            className="w-full h-12 bg-pink-500 hover:bg-pink-600 font-['Bebas_Neue'] text-lg"
            onClick={createChallenge}
            disabled={selectedFilms.length !== 3 || loading}
          >
            {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : (
              <><Swords className="w-5 h-5 mr-2" /> {language === 'it' ? 'CREA SFIDA!' : 'CREATE CHALLENGE!'}</>
            )}
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

          {/* Manche 1, 2, 3 - One per page */}
          {[2, 3, 4].map(step => {
            const matchIndex = step - 2;
            const match = (battle.matches || [])[matchIndex];
            if (battleStep !== step || !match) return null;
            
            return (
              <motion.div
                key={`match-${step}`}
                initial={{ opacity: 0, x: 60 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -60 }}
                className="w-full max-w-lg px-4"
              >
                {/* Manche Header */}
                <div className="text-center mb-3">
                  <p className="text-xs text-gray-400 mb-1">{language === 'it' ? 'MANCHE' : 'MATCH'} {matchIndex + 1}/3</p>
                  <h2 className="font-['Bebas_Neue'] text-2xl">{match.film_a?.title} <span className="text-gray-500 text-lg">VS</span> {match.film_b?.title}</h2>
                </div>
                
                {/* 8 Skill Battles */}
                <div className="space-y-1.5 mb-3">
                  {match.skill_battles.map((sb, si) => (
                    <motion.div
                      key={si}
                      initial={{ x: si % 2 === 0 ? -30 : 30, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: si * 0.25, duration: 0.3 }}
                      className={`p-2 rounded-lg border ${
                        sb.winner === 'team_a' ? 'border-red-500/30 bg-red-500/5' :
                        sb.winner === 'team_b' ? 'border-blue-500/30 bg-blue-500/5' :
                        'border-white/10 bg-white/5'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-base">{getSkillIcon(sb.skill || '')}</span>
                        <span className="text-xs font-semibold flex-1">{sb.skill_name_it || sb.skill}</span>
                        <span className={`text-sm font-bold ${sb.winner === 'team_a' ? 'text-green-400' : 'text-gray-500'}`}>{sb.team_a_value}</span>
                        <div className="w-20 h-1.5 bg-white/10 rounded-full overflow-hidden flex">
                          <div className="h-full bg-red-500" style={{ width: `${(sb.team_a_power / Math.max(sb.team_a_power + sb.team_b_power, 1)) * 100}%` }} />
                          <div className="h-full bg-blue-500" style={{ width: `${(sb.team_b_power / Math.max(sb.team_a_power + sb.team_b_power, 1)) * 100}%` }} />
                        </div>
                        <span className={`text-sm font-bold ${sb.winner === 'team_b' ? 'text-green-400' : 'text-gray-500'}`}>{sb.team_b_value}</span>
                        {sb.is_upset && <Badge className="bg-orange-500/80 text-[8px] px-1">UPSET</Badge>}
                      </div>
                      <p className="text-[10px] text-gray-400 mt-0.5 italic pl-7">{sb.comment}</p>
                    </motion.div>
                  ))}
                </div>
                
                {/* Tiebreaker */}
                {match.tiebreaker && (
                  <motion.div 
                    initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 2.2 }}
                    className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30 text-center mb-3"
                  >
                    <p className="text-xs font-bold text-yellow-400 mb-1">{match.tiebreaker.name_it || 'Spareggio!'}</p>
                    <div className="flex justify-center gap-4 text-sm">
                      <span className={match.tiebreaker.winner === 'team_a' ? 'text-green-400 font-bold' : 'text-gray-400'}>{match.tiebreaker.team_a_value}</span>
                      <span className="text-gray-500">vs</span>
                      <span className={match.tiebreaker.winner === 'team_b' ? 'text-green-400 font-bold' : 'text-gray-400'}>{match.tiebreaker.team_b_value}</span>
                    </div>
                    <p className="text-[10px] text-yellow-300/70 mt-1 italic">{match.tiebreaker.comment}</p>
                  </motion.div>
                )}
                
                {/* Match Result */}
                <motion.div 
                  initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 2.5 }}
                  className="text-center"
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
                    {match.winner === 'team_a' ? `${battle.team_a?.name} ${language === 'it' ? 'VINCE LA MANCHE!' : 'WINS!'}` :
                     match.winner === 'team_b' ? `${battle.team_b?.name} ${language === 'it' ? 'VINCE LA MANCHE!' : 'WINS!'}` :
                     (language === 'it' ? 'PAREGGIO!' : 'DRAW!')}
                  </Badge>
                </motion.div>
                
                {/* Navigation */}
                <div className="flex justify-between mt-4">
                  <Button 
                    variant="ghost" size="sm" 
                    onClick={() => setBattleStep(step - 1)} 
                    disabled={step === 2}
                    className="text-gray-400"
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" /> {language === 'it' ? 'Indietro' : 'Back'}
                  </Button>
                  <Button 
                    size="sm" 
                    onClick={() => setBattleStep(step < 4 ? step + 1 : 99)}
                    className="bg-white/10 hover:bg-white/20"
                    data-testid={`match-next-${matchIndex}`}
                  >
                    {step < 4 ? (language === 'it' ? 'Manche Successiva' : 'Next Match') : (language === 'it' ? 'Risultato Finale' : 'Final Result')} <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </motion.div>
            );
          })}

          {/* Final Result */}
          {battleStep === 99 && (
            <motion.div
              key="final"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="text-center max-w-md px-4"
            >
              <motion.div
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
              >
                <Trophy className="w-24 h-24 text-yellow-500 mx-auto mb-4" />
              </motion.div>
              
              <h1 className="font-['Bebas_Neue'] text-4xl mb-2">
                {battle.winner === 'draw' 
                  ? (language === 'it' ? 'PAREGGIO!' : 'DRAW!')
                  : (battle.winner === 'team_a' ? battle.team_a?.name : battle.team_b?.name)}
              </h1>
              
              <p className="text-lg text-gray-300 mb-6">{battle.winner_comment}</p>
              
              <div className="flex justify-center gap-4 mb-6">
                <div className={`p-4 rounded-lg ${battle.winner === 'team_a' || battle.winner === 'draw' ? 'bg-green-500/20 border-2 border-green-500' : 'bg-red-500/20 border-2 border-red-500'}`}>
                  <p className="font-['Bebas_Neue'] text-xl">{battle.team_a?.name}</p>
                  <p className="text-2xl font-bold">{battle.team_a?.rounds_won}</p>
                </div>
                <div className="flex items-center text-2xl text-gray-500">VS</div>
                <div className={`p-4 rounded-lg ${battle.winner === 'team_b' || battle.winner === 'draw' ? 'bg-green-500/20 border-2 border-green-500' : 'bg-red-500/20 border-2 border-red-500'}`}>
                  <p className="font-['Bebas_Neue'] text-xl">{battle.team_b?.name}</p>
                  <p className="text-2xl font-bold">{battle.team_b?.rounds_won}</p>
                </div>
              </div>
              
              <Button 
                className="bg-pink-500 hover:bg-pink-600 font-['Bebas_Neue'] text-lg px-8"
                onClick={() => { setView('home'); setActiveBattle(null); setBattleStep(0); loadData(); }}
                data-testid="battle-continue-btn"
              >
                {language === 'it' ? 'CONTINUA' : 'CONTINUE'}
              </Button>
            </motion.div>
          )}
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
