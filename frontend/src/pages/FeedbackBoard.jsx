// CineWorld Studio's - FeedbackBoard
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

const FeedbackBoard = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('suggestions');
  const [suggestions, setSuggestions] = useState([]);
  const [bugs, setBugs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formType, setFormType] = useState('suggestion');
  
  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('feature');
  const [severity, setSeverity] = useState('medium');
  const [steps, setSteps] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, [api]);

  const loadData = async () => {
    try {
      const [sugRes, bugRes] = await Promise.all([
        api.get('/suggestions'),
        api.get('/bug-reports')
      ]);
      setSuggestions(sugRes.data.suggestions || []);
      setBugs(bugRes.data.bug_reports || []);
    } catch (e) {
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitSuggestion = async () => {
    if (!title.trim() || !description.trim()) {
      toast.error(language === 'it' ? 'Compila tutti i campi' : 'Fill all fields');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/suggestions', { title, description, category, is_anonymous: isAnonymous });
      toast.success(res.data.message);
      setTitle('');
      setDescription('');
      setIsAnonymous(false);
      setShowForm(false);
      loadData();
    } catch (e) {
      toast.error('Errore nell\'invio');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitBug = async () => {
    if (!title.trim() || !description.trim()) {
      toast.error(language === 'it' ? 'Compila tutti i campi' : 'Fill all fields');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/bug-reports', { 
        title, 
        description, 
        severity,
        steps_to_reproduce: steps || null,
        is_anonymous: isAnonymous
      });
      toast.success(res.data.message);
      setTitle('');
      setDescription('');
      setSteps('');
      setIsAnonymous(false);
      setShowForm(false);
      loadData();
    } catch (e) {
      toast.error('Errore nell\'invio');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVote = async (suggestionId) => {
    try {
      const res = await api.post(`/suggestions/${suggestionId}/vote`);
      toast.success(res.data.message);
      loadData();
    } catch (e) {
      toast.error('Errore');
    }
  };

  const getCategoryColor = (cat) => {
    const colors = {
      feature: 'bg-blue-500/20 text-blue-400',
      improvement: 'bg-green-500/20 text-green-400',
      ui: 'bg-purple-500/20 text-purple-400',
      gameplay: 'bg-yellow-500/20 text-yellow-400',
      other: 'bg-gray-500/20 text-gray-400'
    };
    return colors[cat] || colors.other;
  };

  const getSeverityColor = (sev) => {
    const colors = {
      low: 'bg-green-500/20 text-green-400',
      medium: 'bg-yellow-500/20 text-yellow-400',
      high: 'bg-orange-500/20 text-orange-400',
      critical: 'bg-red-500/20 text-red-400'
    };
    return colors[sev] || colors.medium;
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-gray-500/20 text-gray-400',
      under_review: 'bg-blue-500/20 text-blue-400',
      approved: 'bg-green-500/20 text-green-400',
      rejected: 'bg-red-500/20 text-red-400',
      implemented: 'bg-purple-500/20 text-purple-400',
      open: 'bg-yellow-500/20 text-yellow-400',
      investigating: 'bg-blue-500/20 text-blue-400',
      in_progress: 'bg-orange-500/20 text-orange-400',
      resolved: 'bg-green-500/20 text-green-400',
      closed: 'bg-gray-500/20 text-gray-400',
      wont_fix: 'bg-red-500/20 text-red-400'
    };
    return colors[status] || colors.pending;
  };

  const getCategoryName = (cat) => {
    const names = {
      feature: language === 'it' ? 'Nuova Funzione' : 'New Feature',
      improvement: language === 'it' ? 'Miglioramento' : 'Improvement',
      ui: 'UI/UX',
      gameplay: 'Gameplay',
      other: language === 'it' ? 'Altro' : 'Other'
    };
    return names[cat] || cat;
  };

  const getStatusName = (status) => {
    const names = {
      pending: language === 'it' ? 'In Attesa' : 'Pending',
      under_review: language === 'it' ? 'In Revisione' : 'Under Review',
      approved: language === 'it' ? 'Approvato' : 'Approved',
      rejected: language === 'it' ? 'Rifiutato' : 'Rejected',
      implemented: language === 'it' ? 'Implementato' : 'Implemented',
      open: language === 'it' ? 'Aperto' : 'Open',
      investigating: language === 'it' ? 'In Analisi' : 'Investigating',
      in_progress: language === 'it' ? 'In Corso' : 'In Progress',
      resolved: language === 'it' ? 'Risolto' : 'Resolved',
      closed: language === 'it' ? 'Chiuso' : 'Closed',
      wont_fix: language === 'it' ? 'Non Risolveremo' : 'Won\'t Fix'
    };
    return names[status] || status;
  };

  if (loading) {
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-700 rounded w-1/3"></div>
          {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-700 rounded"></div>)}
        </div>
      </div>
    );
  }

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="feedback-board">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="h-8 w-8">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl flex items-center gap-2">
            <MessageSquare className="w-6 h-6 text-cyan-400" />
            {language === 'it' ? 'SUGGERIMENTI & BUG' : 'FEEDBACK & BUGS'}
          </h1>
          <p className="text-sm text-gray-400">
            {language === 'it' ? 'Aiutaci a migliorare il gioco!' : 'Help us improve the game!'}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <Button 
          variant={activeTab === 'suggestions' ? 'default' : 'outline'}
          onClick={() => setActiveTab('suggestions')}
          className={activeTab === 'suggestions' ? 'bg-cyan-500 text-black' : ''}
        >
          <Lightbulb className="w-4 h-4 mr-2" />
          {language === 'it' ? 'Suggerimenti' : 'Suggestions'} ({suggestions.length})
        </Button>
        <Button 
          variant={activeTab === 'bugs' ? 'default' : 'outline'}
          onClick={() => setActiveTab('bugs')}
          className={activeTab === 'bugs' ? 'bg-red-500 text-white' : ''}
        >
          <Bug className="w-4 h-4 mr-2" />
          Bug ({bugs.length})
        </Button>
      </div>

      {/* Add New Button */}
      <div className="mb-4">
        <Button 
          onClick={() => {
            setFormType(activeTab === 'suggestions' ? 'suggestion' : 'bug');
            setShowForm(true);
          }}
          className={activeTab === 'suggestions' ? 'bg-cyan-500 text-black' : 'bg-red-500 text-white'}
        >
          <Plus className="w-4 h-4 mr-2" />
          {activeTab === 'suggestions' 
            ? (language === 'it' ? 'Nuovo Suggerimento' : 'New Suggestion')
            : (language === 'it' ? 'Segnala Bug' : 'Report Bug')
          }
        </Button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setShowForm(false)}>
          <Card className="bg-[#1A1A1A] border-white/10 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {formType === 'suggestion' ? (
                  <><Lightbulb className="w-5 h-5 text-cyan-400" /> {language === 'it' ? 'Nuovo Suggerimento' : 'New Suggestion'}</>
                ) : (
                  <><Bug className="w-5 h-5 text-red-400" /> {language === 'it' ? 'Segnala Bug' : 'Report Bug'}</>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>{language === 'it' ? 'Titolo' : 'Title'} *</Label>
                <Input 
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder={formType === 'suggestion' 
                    ? (language === 'it' ? 'Es: Aggiungi modalità multiplayer' : 'Ex: Add multiplayer mode')
                    : (language === 'it' ? 'Es: Il pulsante non funziona' : 'Ex: Button not working')
                  }
                  className="bg-black/20 border-white/10"
                />
              </div>
              <div>
                <Label>{language === 'it' ? 'Descrizione' : 'Description'} *</Label>
                <Textarea 
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder={language === 'it' ? 'Descrivi in dettaglio...' : 'Describe in detail...'}
                  className="bg-black/20 border-white/10 min-h-[100px]"
                />
              </div>
              
              {formType === 'suggestion' ? (
                <div>
                  <Label>{language === 'it' ? 'Categoria' : 'Category'}</Label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger className="bg-black/20 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#1A1A1A]">
                      <SelectItem value="feature">{language === 'it' ? 'Nuova Funzione' : 'New Feature'}</SelectItem>
                      <SelectItem value="improvement">{language === 'it' ? 'Miglioramento' : 'Improvement'}</SelectItem>
                      <SelectItem value="ui">UI/UX</SelectItem>
                      <SelectItem value="gameplay">Gameplay</SelectItem>
                      <SelectItem value="other">{language === 'it' ? 'Altro' : 'Other'}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <>
                  <div>
                    <Label>{language === 'it' ? 'Gravità' : 'Severity'}</Label>
                    <Select value={severity} onValueChange={setSeverity}>
                      <SelectTrigger className="bg-black/20 border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#1A1A1A]">
                        <SelectItem value="low">{language === 'it' ? 'Bassa' : 'Low'}</SelectItem>
                        <SelectItem value="medium">{language === 'it' ? 'Media' : 'Medium'}</SelectItem>
                        <SelectItem value="high">{language === 'it' ? 'Alta' : 'High'}</SelectItem>
                        <SelectItem value="critical">{language === 'it' ? 'Critica' : 'Critical'}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>{language === 'it' ? 'Passi per Riprodurre (opzionale)' : 'Steps to Reproduce (optional)'}</Label>
                    <Textarea 
                      value={steps}
                      onChange={e => setSteps(e.target.value)}
                      placeholder={language === 'it' ? '1. Vai a...\n2. Clicca su...\n3. Il bug appare' : '1. Go to...\n2. Click on...\n3. Bug appears'}
                      className="bg-black/20 border-white/10 min-h-[80px]"
                    />
                  </div>
                </>
              )}
              
              {/* Anonymous Toggle */}
              <div className="flex items-center gap-3 p-3 bg-black/20 rounded-lg border border-white/10">
                <input 
                  type="checkbox" 
                  id="anonymous-toggle"
                  checked={isAnonymous}
                  onChange={(e) => setIsAnonymous(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-500"
                />
                <label htmlFor="anonymous-toggle" className="flex-1 cursor-pointer">
                  <p className="text-sm font-medium">
                    {language === 'it' ? 'Invia in modo anonimo' : 'Submit anonymously'}
                  </p>
                  <p className="text-xs text-gray-400">
                    {language === 'it' 
                      ? 'Il tuo nome non sarà visibile agli altri giocatori' 
                      : 'Your name won\'t be visible to other players'}
                  </p>
                </label>
                {isAnonymous && <EyeOff className="w-4 h-4 text-gray-400" />}
              </div>
              
              <div className="flex gap-2 pt-2">
                <Button variant="outline" onClick={() => setShowForm(false)} className="flex-1">
                  {language === 'it' ? 'Annulla' : 'Cancel'}
                </Button>
                <Button 
                  onClick={formType === 'suggestion' ? handleSubmitSuggestion : handleSubmitBug}
                  disabled={submitting}
                  className={formType === 'suggestion' ? 'bg-cyan-500 text-black flex-1' : 'bg-red-500 text-white flex-1'}
                >
                  {submitting ? '...' : (language === 'it' ? 'Invia' : 'Submit')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Content */}
      {activeTab === 'suggestions' ? (
        <div className="space-y-3">
          {suggestions.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-8 text-center text-gray-400">
                <Lightbulb className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>{language === 'it' ? 'Nessun suggerimento ancora. Sii il primo!' : 'No suggestions yet. Be the first!'}</p>
              </CardContent>
            </Card>
          ) : (
            suggestions.map(s => (
              <Card key={s.id} className="bg-[#1A1A1A] border-white/10">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    {/* Vote Column */}
                    <div className="flex flex-col items-center gap-1">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => handleVote(s.id)}
                        className={`h-8 w-8 p-0 ${s.user_has_voted ? 'text-cyan-400' : 'text-gray-400'}`}
                      >
                        <ChevronUp className="w-5 h-5" />
                      </Button>
                      <span className={`font-bold text-lg ${s.votes > 0 ? 'text-cyan-400' : 'text-gray-500'}`}>
                        {s.votes}
                      </span>
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <h3 className="font-semibold">{s.title}</h3>
                        <Badge className={getCategoryColor(s.category)}>{getCategoryName(s.category)}</Badge>
                        <Badge className={getStatusColor(s.status)}>{getStatusName(s.status)}</Badge>
                      </div>
                      <p className="text-sm text-gray-400 mb-2">{s.description}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        {s.is_anonymous ? (
                          <>
                            <EyeOff className="w-3 h-3" />
                            <span className="italic">{language === 'it' ? 'Anonimo' : 'Anonymous'}</span>
                          </>
                        ) : (
                          <>
                            <Avatar className="w-4 h-4">
                              <AvatarImage src={s.user_avatar} />
                              <AvatarFallback className="text-[8px]">{s.user_nickname?.[0]}</AvatarFallback>
                            </Avatar>
                            <span>{s.user_nickname}</span>
                          </>
                        )}
                        <span>•</span>
                        <span>{new Date(s.created_at).toLocaleDateString()}</span>
                      </div>
                      {s.admin_response && (
                        <div className="mt-2 p-2 bg-cyan-500/10 rounded border border-cyan-500/30">
                          <p className="text-xs text-cyan-400 font-semibold mb-1">Risposta Admin:</p>
                          <p className="text-xs text-gray-300">{s.admin_response}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {bugs.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-8 text-center text-gray-400">
                <Bug className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>{language === 'it' ? 'Nessun bug segnalato. Ottimo!' : 'No bugs reported. Great!'}</p>
              </CardContent>
            </Card>
          ) : (
            bugs.map(b => (
              <Card key={b.id} className="bg-[#1A1A1A] border-white/10">
                <CardContent className="p-4">
                  <div className="flex items-start gap-2 mb-2 flex-wrap">
                    <h3 className="font-semibold">{b.title}</h3>
                    <Badge className={getSeverityColor(b.severity)}>
                      {b.severity.toUpperCase()}
                    </Badge>
                    <Badge className={getStatusColor(b.status)}>{getStatusName(b.status)}</Badge>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">{b.description}</p>
                  {b.steps_to_reproduce && (
                    <div className="text-xs text-gray-500 mb-2 p-2 bg-black/20 rounded">
                      <span className="font-semibold">{language === 'it' ? 'Passi per riprodurre:' : 'Steps to reproduce:'}</span>
                      <pre className="whitespace-pre-wrap mt-1">{b.steps_to_reproduce}</pre>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    {b.is_anonymous ? (
                      <>
                        <EyeOff className="w-3 h-3" />
                        <span className="italic">{language === 'it' ? 'Anonimo' : 'Anonymous'}</span>
                      </>
                    ) : (
                      <>
                        <Avatar className="w-4 h-4">
                          <AvatarImage src={b.user_avatar} />
                          <AvatarFallback className="text-[8px]">{b.user_nickname?.[0]}</AvatarFallback>
                        </Avatar>
                        <span>{b.user_nickname}</span>
                      </>
                    )}
                    <span>•</span>
                    <span>{new Date(b.created_at).toLocaleDateString()}</span>
                  </div>
                  {b.admin_response && (
                    <div className="mt-2 p-2 bg-green-500/10 rounded border border-green-500/30">
                      <p className="text-xs text-green-400 font-semibold mb-1">Risposta Admin:</p>
                      <p className="text-xs text-gray-300">{b.admin_response}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
};

// Cinema Journal - Newspaper style film reviews

export default FeedbackBoard;
