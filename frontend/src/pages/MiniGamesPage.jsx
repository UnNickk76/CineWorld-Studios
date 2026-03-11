// CineWorld Studio's - MiniGamesPage
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';

// useTranslations imported from contexts

const MiniGamesPage = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const [games, setGames] = useState([]);
  const [challenges, setChallenges] = useState({ daily: [], weekly: [] });
  const [currentGame, setCurrentGame] = useState(null);
  const [gameSession, setGameSession] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState([]);
  const [gameResult, setGameResult] = useState(null);
  const [loading, setLoading] = useState(false);
  // Versus state
  const [vsTab, setVsTab] = useState('play');
  const [pendingVs, setPendingVs] = useState([]);
  const [myVs, setMyVs] = useState([]);
  const [vsMode, setVsMode] = useState(null); // 'create' | 'join'
  const [vsChallenge, setVsChallenge] = useState(null);
  const [vsResult, setVsResult] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const [gamesRes, challengesRes] = await Promise.all([api.get('/minigames'), api.get('/challenges')]);
      setGames(gamesRes.data);
      setChallenges(challengesRes.data);
    };
    fetchData();
    loadVsData();
  }, [api]);

  const loadVsData = async () => {
    try {
      const [pendingRes, myRes] = await Promise.all([
        api.get('/minigames/versus/pending'),
        api.get('/minigames/versus/my')
      ]);
      setPendingVs(pendingRes.data);
      setMyVs(myRes.data);
    } catch {}
  };

  const startGame = async (game) => {
    setLoading(true);
    try {
      const res = await api.post(`/minigames/${game.id}/start`);
      setCurrentGame(game);
      setGameSession(res.data);
      setCurrentQuestionIndex(0);
      setSelectedAnswers([]);
      setGameResult(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Cannot start game');
    } finally {
      setLoading(false);
    }
  };

  const selectAnswer = (answer) => {
    const newAnswers = [...selectedAnswers];
    newAnswers[currentQuestionIndex] = { question_index: currentQuestionIndex, answer };
    setSelectedAnswers(newAnswers);
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < gameSession.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const submitGame = async () => {
    setLoading(true);
    try {
      const res = await api.post('/minigames/submit', {
        game_id: currentGame.id,
        session_id: gameSession.session_id,
        answers: selectedAnswers
      });
      setGameResult(res.data);
      refreshUser();
    } catch (err) {
      toast.error('Failed to submit game');
    } finally {
      setLoading(false);
    }
  };

  const closeGame = () => {
    setCurrentGame(null);
    setGameSession(null);
    setGameResult(null);
    setSelectedAnswers([]);
    setCurrentQuestionIndex(0);
    setVsMode(null);
    setVsChallenge(null);
    setVsResult(null);
    loadVsData();
  };

  const createVsChallenge = async (game) => {
    setLoading(true);
    try {
      const res = await api.post('/minigames/versus/create', { game_id: game.id });
      setCurrentGame(game);
      setVsChallenge(res.data);
      setGameSession({ questions: res.data.questions });
      setVsMode('create');
      setCurrentQuestionIndex(0);
      setSelectedAnswers([]);
      setGameResult(null);
      setVsResult(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore creazione sfida VS');
    } finally {
      setLoading(false);
    }
  };

  const joinVsChallenge = async (challenge) => {
    setLoading(true);
    try {
      const res = await api.post(`/minigames/versus/${challenge.id}/join`);
      setCurrentGame(res.data.game);
      setVsChallenge(res.data);
      setGameSession({ questions: res.data.questions });
      setVsMode('join');
      setCurrentQuestionIndex(0);
      setSelectedAnswers([]);
      setGameResult(null);
      setVsResult(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore unione sfida VS');
    } finally {
      setLoading(false);
    }
  };

  const submitVsAnswers = async () => {
    setLoading(true);
    try {
      const challengeId = vsChallenge.challenge_id;
      const res = await api.post(`/minigames/versus/${challengeId}/answer`, { answers: selectedAnswers });
      setVsResult(res.data);
      refreshUser();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore invio risposte');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto" data-testid="minigames-page">
      <h1 className="font-['Bebas_Neue'] text-3xl mb-4">{t('mini_games')}</h1>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        {games.map(game => (
          <Card key={game.id} className="bg-[#1A1A1A] border-white/5">
            <CardContent className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-2 bg-yellow-500/20 rounded-lg"><Gamepad2 className="w-5 h-5 text-yellow-500" /></div>
                <div><h3 className="font-semibold text-sm">{game.name}</h3><p className="text-xs text-gray-400">{game.description}</p></div>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-gray-400">Reward:</span>
                <span className="text-sm text-yellow-500">${game.reward_min.toLocaleString()} - ${game.reward_max.toLocaleString()}</span>
              </div>
              <Button onClick={() => startGame(game)} disabled={loading} className="w-full h-8 bg-yellow-500 text-black hover:bg-yellow-400 text-sm">
                Play Now
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Game Modal */}
      <Dialog open={!!gameSession} onOpenChange={() => !loading && closeGame()}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl">{currentGame?.name}</DialogTitle>
          </DialogHeader>
          
          {!gameResult ? (
            <div className="space-y-4">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Question {currentQuestionIndex + 1} of {gameSession?.questions?.length}</span>
                <span>{selectedAnswers.filter(Boolean).length} answered</span>
              </div>
              <Progress value={((currentQuestionIndex + 1) / (gameSession?.questions?.length || 1)) * 100} className="h-1.5" />
              
              {gameSession?.questions?.[currentQuestionIndex] && (
                <div className="space-y-3">
                  <p className="font-semibold">{gameSession.questions[currentQuestionIndex].question}</p>
                  <RadioGroup 
                    value={selectedAnswers[currentQuestionIndex]?.answer || ''} 
                    onValueChange={selectAnswer}
                  >
                    {gameSession.questions[currentQuestionIndex].options.map((option, i) => (
                      <div key={i} className="flex items-center space-x-2 p-2 rounded border border-white/10 hover:border-yellow-500/50 cursor-pointer">
                        <RadioGroupItem value={option} id={`option-${i}`} />
                        <Label htmlFor={`option-${i}`} className="cursor-pointer flex-1 text-sm">{option}</Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>
              )}
              
              <div className="flex gap-2">
                {currentQuestionIndex < (gameSession?.questions?.length || 0) - 1 ? (
                  <Button onClick={nextQuestion} disabled={!selectedAnswers[currentQuestionIndex]} className="flex-1 bg-yellow-500 text-black">Next</Button>
                ) : (
                  <Button onClick={submitGame} disabled={loading || selectedAnswers.length < (gameSession?.questions?.length || 0)} className="flex-1 bg-green-500 hover:bg-green-400">Submit Answers</Button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-center py-4">
                <div className={`text-5xl mb-2 ${gameResult.score_percentage >= 60 ? 'text-green-500' : 'text-red-500'}`}>
                  {gameResult.score_percentage}%
                </div>
                <p className="text-gray-400">{gameResult.correct_answers} / {gameResult.total_questions} correct</p>
                <p className="text-2xl font-bold text-yellow-500 mt-2">+${gameResult.reward.toLocaleString()}</p>
              </div>
              
              <ScrollArea className="h-48">
                <div className="space-y-2">
                  {gameResult.results.map((r, i) => (
                    <div key={i} className={`p-2 rounded border ${r.is_correct ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'}`}>
                      <p className="text-xs font-semibold mb-1">{r.question}</p>
                      <div className="flex items-center gap-1 text-xs">
                        {r.is_correct ? <Check className="w-3 h-3 text-green-500" /> : <XCircle className="w-3 h-3 text-red-500" />}
                        <span>Your answer: {r.your_answer}</span>
                      </div>
                      {!r.is_correct && <p className="text-xs text-green-400 mt-1">Correct: {r.correct_answer}</p>}
                    </div>
                  ))}
                </div>
              </ScrollArea>
              
              <Button onClick={closeGame} className="w-full">Close</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* === VERSUS 1v1 SECTION === */}
      <div className="mb-6">
        <h2 className="font-['Bebas_Neue'] text-2xl mb-3 flex items-center gap-2">
          <Swords className="w-5 h-5 text-cyan-400" /> MINI GAME VS 1v1
        </h2>
        
        <Tabs value={vsTab} onValueChange={setVsTab}>
          <TabsList className="mb-3">
            <TabsTrigger value="play" data-testid="vs-play-tab">
              {language === 'it' ? 'Crea Sfida' : 'Create Challenge'}
            </TabsTrigger>
            <TabsTrigger value="join" data-testid="vs-join-tab">
              {language === 'it' ? 'Sfide Aperte' : 'Open Challenges'} {pendingVs.length > 0 && <Badge className="ml-1 bg-cyan-500 text-white text-[10px]">{pendingVs.length}</Badge>}
            </TabsTrigger>
            <TabsTrigger value="history" data-testid="vs-history-tab">
              {language === 'it' ? 'Storico' : 'History'}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="play">
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {games.map(game => (
                <Card key={`vs-${game.id}`} className="bg-gradient-to-br from-cyan-500/10 to-purple-500/10 border-cyan-500/20">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-2 bg-cyan-500/20 rounded-lg"><Swords className="w-5 h-5 text-cyan-400" /></div>
                      <div><h3 className="font-semibold text-sm">{game.name} VS</h3><p className="text-xs text-gray-400">{language === 'it' ? 'Sfida 1v1' : '1v1 Challenge'}</p></div>
                    </div>
                    <p className="text-xs text-gray-400 mb-2">{language === 'it' ? 'Rispondi alle domande e aspetta un avversario!' : 'Answer questions and wait for an opponent!'}</p>
                    <Button 
                      onClick={() => createVsChallenge(game)} 
                      disabled={loading} 
                      className="w-full h-8 bg-gradient-to-r from-cyan-600 to-purple-600 hover:from-cyan-500 hover:to-purple-500 text-white text-sm"
                      data-testid={`vs-create-${game.id}`}
                    >
                      {language === 'it' ? 'Lancia Sfida VS!' : 'Launch VS Challenge!'}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
          
          <TabsContent value="join">
            {pendingVs.length === 0 ? (
              <Card className="bg-[#1A1A1A] border-white/5">
                <CardContent className="p-6 text-center text-gray-400">
                  <Swords className="w-10 h-10 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">{language === 'it' ? 'Nessuna sfida VS aperta al momento.' : 'No open VS challenges right now.'}</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-2">
                {pendingVs.map(vs => (
                  <Card key={vs.id} className="bg-[#1A1A1A] border-cyan-500/20">
                    <CardContent className="p-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Avatar className="w-9 h-9"><AvatarFallback className="bg-cyan-500/20 text-cyan-400">{vs.creator_nickname?.[0]}</AvatarFallback></Avatar>
                        <div>
                          <p className="font-semibold text-sm">{vs.creator_nickname}</p>
                          <p className="text-xs text-gray-400">{vs.game_name} - {language === 'it' ? 'Punteggio' : 'Score'}: {vs.creator_score}%</p>
                        </div>
                      </div>
                      <Button 
                        size="sm" 
                        onClick={() => joinVsChallenge(vs)} 
                        disabled={loading}
                        className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold"
                        data-testid={`vs-join-${vs.id}`}
                      >
                        {language === 'it' ? 'Accetta!' : 'Accept!'}
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="history">
            {myVs.length === 0 ? (
              <Card className="bg-[#1A1A1A] border-white/5">
                <CardContent className="p-6 text-center text-gray-400">
                  <p className="text-sm">{language === 'it' ? 'Nessuna sfida VS giocata.' : 'No VS challenges played yet.'}</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-2">
                {myVs.map(vs => {
                  const isCreator = vs.creator_id === user?.id;
                  const myScore = isCreator ? vs.creator_score : vs.opponent_score;
                  const oppScore = isCreator ? vs.opponent_score : vs.creator_score;
                  const oppName = isCreator ? vs.opponent_nickname : vs.creator_nickname;
                  const isWinner = vs.winner_id === user?.id;
                  const isDraw = vs.winner_id === 'draw';
                  
                  return (
                    <Card key={vs.id} className={`bg-[#1A1A1A] ${vs.status === 'completed' ? (isWinner ? 'border-green-500/30' : isDraw ? 'border-yellow-500/30' : 'border-red-500/30') : 'border-white/10'}`}>
                      <CardContent className="p-3 flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm">{vs.game_name}</span>
                            <Badge className={`text-[10px] ${vs.status === 'waiting' ? 'bg-yellow-500/20 text-yellow-400' : vs.status === 'completed' ? (isWinner ? 'bg-green-500/20 text-green-400' : isDraw ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400') : 'bg-blue-500/20 text-blue-400'}`}>
                              {vs.status === 'waiting' ? (language === 'it' ? 'In attesa' : 'Waiting') : 
                               vs.status === 'completed' ? (isWinner ? (language === 'it' ? 'Vittoria' : 'Won') : isDraw ? (language === 'it' ? 'Pareggio' : 'Draw') : (language === 'it' ? 'Sconfitta' : 'Lost')) :
                               (language === 'it' ? 'In corso' : 'Playing')}
                            </Badge>
                          </div>
                          {vs.status === 'completed' && oppName && (
                            <p className="text-xs text-gray-400 mt-1">VS {oppName} | {myScore ?? '?'}% vs {oppScore ?? '?'}%</p>
                          )}
                          {vs.status === 'waiting' && (
                            <p className="text-xs text-gray-400 mt-1">{language === 'it' ? 'In attesa di un avversario...' : 'Waiting for opponent...'} ({myScore}%)</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* VS Game Modal */}
      <Dialog open={!!vsMode && !!gameSession} onOpenChange={() => !loading && closeGame()}>
        <DialogContent className="bg-[#1A1A1A] border-cyan-500/20 max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <Swords className="w-5 h-5 text-cyan-400" /> {currentGame?.name} VS
            </DialogTitle>
            <DialogDescription>
              {vsMode === 'create' 
                ? (language === 'it' ? 'Rispondi alle domande - il tuo punteggio verrà confrontato!' : 'Answer the questions - your score will be compared!') 
                : (language === 'it' ? `Sfida contro ${vsChallenge?.creator_nickname}!` : `Challenge against ${vsChallenge?.creator_nickname}!`)}
            </DialogDescription>
          </DialogHeader>
          
          {!vsResult ? (
            <div className="space-y-4">
              <div className="flex justify-between text-xs text-gray-400">
                <span>{language === 'it' ? 'Domanda' : 'Question'} {currentQuestionIndex + 1} / {gameSession?.questions?.length}</span>
                <span>{selectedAnswers.filter(Boolean).length} {language === 'it' ? 'risposte' : 'answered'}</span>
              </div>
              <Progress value={((currentQuestionIndex + 1) / (gameSession?.questions?.length || 1)) * 100} className="h-1.5" />
              
              {gameSession?.questions?.[currentQuestionIndex] && (
                <div className="space-y-3">
                  <p className="font-semibold">{gameSession.questions[currentQuestionIndex].question}</p>
                  <RadioGroup value={selectedAnswers[currentQuestionIndex]?.answer || ''} onValueChange={selectAnswer}>
                    {gameSession.questions[currentQuestionIndex].options.map((option, i) => (
                      <div key={i} className="flex items-center space-x-2 p-2 rounded border border-cyan-500/20 hover:border-cyan-500/50 cursor-pointer">
                        <RadioGroupItem value={option} id={`vs-opt-${i}`} />
                        <Label htmlFor={`vs-opt-${i}`} className="cursor-pointer flex-1 text-sm">{option}</Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>
              )}
              
              <div className="flex gap-2">
                {currentQuestionIndex < (gameSession?.questions?.length || 0) - 1 ? (
                  <Button onClick={nextQuestion} disabled={!selectedAnswers[currentQuestionIndex]} className="flex-1 bg-cyan-500 text-black">{language === 'it' ? 'Avanti' : 'Next'}</Button>
                ) : (
                  <Button onClick={submitVsAnswers} disabled={loading || selectedAnswers.length < (gameSession?.questions?.length || 0)} className="flex-1 bg-gradient-to-r from-cyan-600 to-purple-600 text-white" data-testid="vs-submit-btn">
                    {loading ? '...' : (language === 'it' ? 'Invia Risposte!' : 'Submit!')}
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-center py-4">
                {vsResult.status === 'completed' ? (
                  <>
                    <Trophy className={`w-12 h-12 mx-auto mb-2 ${vsResult.winner_id === user?.id ? 'text-yellow-500' : vsResult.winner_id === 'draw' ? 'text-gray-400' : 'text-red-400'}`} />
                    <h3 className="font-['Bebas_Neue'] text-2xl">
                      {vsResult.winner_id === user?.id ? (language === 'it' ? 'HAI VINTO!' : 'YOU WON!') : 
                       vsResult.winner_id === 'draw' ? (language === 'it' ? 'PAREGGIO!' : 'DRAW!') : 
                       (language === 'it' ? 'HAI PERSO!' : 'YOU LOST!')}
                    </h3>
                    <div className="flex justify-center gap-4 mt-3">
                      <div className="text-center">
                        <p className="text-xs text-gray-400">{vsResult.creator_nickname}</p>
                        <p className="text-2xl font-bold text-cyan-400">{vsResult.creator_score}%</p>
                      </div>
                      <span className="self-center text-gray-500">VS</span>
                      <div className="text-center">
                        <p className="text-xs text-gray-400">{vsResult.opponent_nickname || user?.nickname}</p>
                        <p className="text-2xl font-bold text-purple-400">{vsResult.opponent_score || vsResult.score}%</p>
                      </div>
                    </div>
                    {vsResult.reward && <p className="text-xl font-bold text-yellow-500 mt-2">+${vsResult.reward.toLocaleString()}</p>}
                  </>
                ) : (
                  <>
                    <div className="text-5xl mb-2 text-cyan-400">{vsResult.score}%</div>
                    <p className="text-gray-400">{vsResult.correct} / {vsResult.total} {language === 'it' ? 'corrette' : 'correct'}</p>
                    <p className="text-sm text-cyan-400 mt-2">{language === 'it' ? 'In attesa di un avversario...' : 'Waiting for an opponent...'}</p>
                  </>
                )}
              </div>
              
              {vsResult.results && (
                <ScrollArea className="h-40">
                  <div className="space-y-2">
                    {vsResult.results.map((r, i) => (
                      <div key={i} className={`p-2 rounded border ${r.is_correct ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'}`}>
                        <p className="text-xs font-semibold mb-1">{r.question}</p>
                        <div className="flex items-center gap-1 text-xs">
                          {r.is_correct ? <Check className="w-3 h-3 text-green-500" /> : <XCircle className="w-3 h-3 text-red-500" />}
                          <span>{r.your_answer}</span>
                        </div>
                        {!r.is_correct && <p className="text-xs text-green-400 mt-1">{language === 'it' ? 'Corretta' : 'Correct'}: {r.correct_answer}</p>}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
              
              <Button onClick={closeGame} className="w-full" data-testid="vs-close-btn">{language === 'it' ? 'Chiudi' : 'Close'}</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <h2 className="font-['Bebas_Neue'] text-2xl mb-3 flex items-center gap-2"><Trophy className="w-5 h-5 text-yellow-500" /> {t('challenges')}</h2>
      <Tabs defaultValue="daily">
        <TabsList><TabsTrigger value="daily">{t('daily')}</TabsTrigger><TabsTrigger value="weekly">{t('weekly')}</TabsTrigger></TabsList>
        <TabsContent value="daily"><div className="grid gap-2">{challenges.daily.map(c => (
          <Card key={c.id} className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3 flex justify-between items-center">
            <div><h4 className="font-semibold text-sm">{c.name}</h4><p className="text-xs text-gray-400">{c.description}</p><Progress value={(c.current / c.target) * 100} className="h-1.5 mt-1 w-32" /></div>
            <p className="text-yellow-500 font-bold">${c.reward.toLocaleString()}</p>
          </CardContent></Card>
        ))}</div></TabsContent>
        <TabsContent value="weekly"><div className="grid gap-2">{challenges.weekly.map(c => (
          <Card key={c.id} className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3 flex justify-between items-center">
            <div><h4 className="font-semibold text-sm">{c.name}</h4><p className="text-xs text-gray-400">{c.description}</p><Progress value={(c.current / c.target) * 100} className="h-1.5 mt-1 w-32" /></div>
            <p className="text-yellow-500 font-bold">${c.reward.toLocaleString()}</p>
          </CardContent></Card>
        ))}</div></TabsContent>
      </Tabs>
    </div>
  );
};

// Film Wizard - simplified

export default MiniGamesPage;
