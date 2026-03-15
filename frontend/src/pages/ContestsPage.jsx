import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, LanguageContext } from '../contexts';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Ticket, Lock, Check, Zap, TrendingUp, Users, DollarSign, Trophy, Film, Image, Star, Gift, Clock, Clapperboard } from 'lucide-react';
import { toast } from 'sonner';

const ICON_MAP = { 
  'dollar-sign': DollarSign, 'users': Users, 'trending-up': TrendingUp, 'zap': Zap,
  'film': Film, 'clapperboard': Clapperboard, 'image': Image, 'star': Star, 'gift': Gift, 'clock': Clock
};

const ContestsPage = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const [contestData, setContestData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeContest, setActiveContest] = useState(null);
  const [challenge, setChallenge] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [triviaIndex, setTriviaIndex] = useState(0);
  const [triviaScore, setTriviaScore] = useState(0);
  const [triviaAnswered, setTriviaAnswered] = useState(false);

  useEffect(() => { loadContests(); }, []);

  const loadContests = async () => {
    try {
      const res = await api.get('/cinepass/contests');
      setContestData(res.data);
    } catch (e) { toast.error('Errore caricamento contest'); }
    finally { setLoading(false); }
  };

  const startContest = async (contestId) => {
    try {
      const res = await api.post(`/cinepass/contests/${contestId}/start`);
      setActiveContest(contestId);
      setChallenge(res.data.challenge);
      setResult(null);
      setSelectedAnswer(null);
      setTriviaIndex(0);
      setTriviaScore(0);
      setTriviaAnswered(false);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const submitAnswer = async (answer, correctAnswer) => {
    setSubmitting(true);
    try {
      const res = await api.post(`/cinepass/contests/${activeContest}/submit`, { answer, correct_answer: correctAnswer });
      setResult(res.data);
      refreshUser();
      loadContests();
      toast.success(`${res.data.correct ? 'Corretto!' : 'Sbagliato.'} +${res.data.earned} CinePass${res.data.bonus > 0 ? ` (+${res.data.bonus} bonus!)` : ''}`);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setSubmitting(false); }
  };

  const handleTriviaAnswer = (answer, correct) => {
    setTriviaAnswered(true);
    const isCorrect = answer === correct;
    const newScore = triviaScore + (isCorrect ? 1 : 0);
    setTriviaScore(newScore);
    setSelectedAnswer(answer);
    
    setTimeout(() => {
      if (triviaIndex < (challenge?.questions?.length || 5) - 1) {
        setTriviaIndex(triviaIndex + 1);
        setTriviaAnswered(false);
        setSelectedAnswer(null);
      } else {
        // All done - submit best score
        const totalQ = challenge?.questions?.length || 5;
        submitAnswer(newScore >= Math.ceil(totalQ / 2) ? 'pass' : 'fail', 'pass');
      }
    }, 800);
  };

  if (loading) return <div className="text-center py-12 text-gray-400">Caricamento...</div>;

  const contests = contestData?.contests || [];

  return (
    <div className="max-w-lg mx-auto space-y-4 px-3 pt-2 pb-32" data-testid="contests-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-400" />
            {language === 'it' ? 'Contest Giornalieri' : 'Daily Contests'}
          </h2>
          <p className="text-xs text-gray-500">{language === 'it' ? 'Si azzerano alle 12:00' : 'Reset at 12:00 noon'}</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-gray-500">{language === 'it' ? 'Guadagnati oggi' : 'Earned today'}</p>
          <p className="text-sm font-bold text-cyan-400">{contestData?.total_earned || 0}/50 <Ticket className="w-3 h-3 inline" /></p>
        </div>
      </div>

      {/* Progress */}
      <Progress value={(contestData?.total_earned || 0) * 2} className="h-1.5" />

      {/* Contest Cards */}
      {contests.map((c, i) => {
        const Icon = ICON_MAP[c.icon] || Zap;
        return (
          <Card key={c.contest_id} className={`bg-[#1A1A1B] border-gray-800 ${c.status === 'locked' || c.status === 'timed_lock' ? 'opacity-40' : ''}`} data-testid={`contest-card-${c.contest_id}`}>
            <CardContent className="p-3">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${c.completed ? 'bg-green-500/20' : c.status === 'available' ? 'bg-cyan-500/20' : c.status === 'timed_lock' ? 'bg-yellow-500/20' : 'bg-gray-800'}`}>
                  {c.completed ? <Check className="w-5 h-5 text-green-400" /> : c.status === 'timed_lock' ? <Clock className="w-5 h-5 text-yellow-400" /> : c.status === 'locked' ? <Lock className="w-5 h-5 text-gray-600" /> : <Icon className="w-5 h-5 text-cyan-400" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold">{c.name}</p>
                    {c.completed && <Badge className="bg-green-900/40 text-green-400 text-[9px]">+{c.earned}</Badge>}
                  </div>
                  <p className="text-[10px] text-gray-500">{c.description}</p>
                </div>
                {c.status === 'available' && !c.completed && (
                  <Button size="sm" className="bg-cyan-700 hover:bg-cyan-800 text-xs h-8" onClick={() => startContest(c.contest_id)} data-testid={`start-contest-${c.contest_id}`}>
                    <Ticket className="w-3 h-3 mr-1" />{c.reward}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}

      {contestData?.all_completed && (
        <div className="text-center py-4 text-green-400 font-bold text-sm" data-testid="all-contests-done">
          Tutti i contest completati! Torna domani.
        </div>
      )}

      {/* Contest Dialog */}
      <Dialog open={!!challenge && !result} onOpenChange={() => { setChallenge(null); setActiveContest(null); }}>
        <DialogContent className="bg-[#141416] border-gray-800 text-white max-w-sm" data-testid="contest-dialog">
          <DialogHeader>
            <DialogTitle className="text-base">{contests.find(c => c.contest_id === activeContest)?.name}</DialogTitle>
          </DialogHeader>

          {/* Budget Guess */}
          {challenge?.genre && challenge?.options && !challenge?.questions && !challenge?.actors && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 bg-white/5 rounded"><span className="text-gray-500">Genere:</span> <span className="font-bold">{challenge.genre}</span></div>
                <div className="p-2 bg-white/5 rounded"><span className="text-gray-500">Equip:</span> <span className="font-bold">{challenge.equipment}</span></div>
                <div className="p-2 bg-white/5 rounded"><span className="text-gray-500">Cast:</span> <span className="font-bold">{challenge.cast_level}</span></div>
                <div className="p-2 bg-white/5 rounded"><span className="text-gray-500">Location:</span> <span className="font-bold">{challenge.locations}</span></div>
              </div>
              <p className="text-xs text-gray-400 text-center">{language === 'it' ? 'Qual è il budget totale?' : 'What is the total budget?'}</p>
              <div className="grid grid-cols-2 gap-2">
                {challenge.options.map(opt => (
                  <Button key={opt} variant="outline" disabled={submitting} className={`border-gray-700 text-sm h-10 ${selectedAnswer === opt ? 'ring-2 ring-cyan-400 bg-cyan-500/10' : ''}`}
                    onClick={() => { setSelectedAnswer(opt); submitAnswer(opt, challenge.correct); }} data-testid={`budget-option-${opt}`}>
                    ${opt >= 1000000 ? `${(opt/1000000).toFixed(1)}M` : `${(opt/1000).toFixed(0)}K`}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Cast Match */}
          {challenge?.actors && (
            <div className="space-y-3">
              <p className="text-sm text-center font-medium">{challenge.question}</p>
              <div className="space-y-2">
                {challenge.actors.map(a => (
                  <Button key={a.id} variant="outline" disabled={submitting} className={`w-full border-gray-700 justify-start h-10 ${selectedAnswer === a.id ? 'ring-2 ring-cyan-400 bg-cyan-500/10' : ''}`}
                    onClick={() => { setSelectedAnswer(a.id); submitAnswer(a.id, challenge.correct); }} data-testid={`actor-option-${a.id}`}>
                    <span className="font-medium">{a.name}</span>
                    <span className="ml-auto text-xs text-yellow-400">IMDb {a.imdb}</span>
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Box Office Prediction */}
          {challenge?.title && challenge?.options && !challenge?.actors && !challenge?.genre && (
            <div className="space-y-3">
              <div className="p-3 bg-white/5 rounded text-center">
                <p className="text-xs text-gray-500">{language === 'it' ? 'Film:' : 'Film:'}</p>
                <p className="font-bold">{challenge.title}</p>
                <p className="text-xs text-gray-400">{challenge.genre}</p>
              </div>
              <p className="text-xs text-gray-400 text-center">{language === 'it' ? 'Come andrà al botteghino?' : 'How will it perform?'}</p>
              <div className="grid grid-cols-2 gap-2">
                {challenge.options.map(opt => (
                  <Button key={opt} variant="outline" disabled={submitting} className={`border-gray-700 text-xs h-9 ${selectedAnswer === opt ? 'ring-2 ring-cyan-400 bg-cyan-500/10' : ''}`}
                    onClick={() => { setSelectedAnswer(opt); submitAnswer(opt, challenge.correct); }} data-testid={`box-option-${opt}`}>
                    {opt}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Trivia Speed */}
          {challenge?.questions && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>{language === 'it' ? 'Domanda' : 'Question'} {triviaIndex + 1}/{challenge.questions.length}</span>
                <span className="text-green-400">{triviaScore} {language === 'it' ? 'corrette' : 'correct'}</span>
              </div>
              <Progress value={((triviaIndex + 1) / challenge.questions.length) * 100} className="h-1" />
              <p className="text-sm font-medium text-center">{challenge.questions[triviaIndex]?.q}</p>
              <div className="space-y-1.5">
                {challenge.questions[triviaIndex]?.options.map(opt => (
                  <Button key={opt} variant="outline" disabled={triviaAnswered}
                    className={`w-full border-gray-700 text-xs h-9 justify-start ${
                      triviaAnswered && opt === challenge.questions[triviaIndex].correct ? 'bg-green-500/20 border-green-500' :
                      triviaAnswered && opt === selectedAnswer && opt !== challenge.questions[triviaIndex].correct ? 'bg-red-500/20 border-red-500' : ''
                    }`}
                    onClick={() => handleTriviaAnswer(opt, challenge.questions[triviaIndex].correct)}
                    data-testid={`trivia-option-${opt}`}>
                    {opt}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Result */}
      <Dialog open={!!result} onOpenChange={() => setResult(null)}>
        <DialogContent className="bg-[#141416] border-gray-800 text-white max-w-xs" data-testid="contest-result">
          <div className="text-center space-y-3 py-2">
            <div className={`w-14 h-14 mx-auto rounded-full flex items-center justify-center ${result?.correct ? 'bg-green-500/20' : 'bg-orange-500/20'}`}>
              {result?.correct ? <Check className="w-7 h-7 text-green-400" /> : <Zap className="w-7 h-7 text-orange-400" />}
            </div>
            <p className="font-bold text-lg">{result?.correct ? (language === 'it' ? 'Esatto!' : 'Correct!') : (language === 'it' ? 'Non proprio...' : 'Not quite...')}</p>
            <div className="flex items-center justify-center gap-1 text-cyan-400 text-xl font-bold">
              <Ticket className="w-5 h-5" /> +{result?.earned || 0}
              {result?.bonus > 0 && <span className="text-yellow-400 text-sm ml-2">(+{result.bonus} bonus!)</span>}
            </div>
            <Button onClick={() => setResult(null)} className="w-full bg-cyan-700 hover:bg-cyan-800">OK</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ContestsPage;
