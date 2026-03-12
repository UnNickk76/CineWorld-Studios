// CineWorld Studio's - FestivalsPage
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding, User
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { ClickableNickname } from '../components/shared';

// useTranslations imported from contexts

const FestivalsPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useTranslations();
  const location = useLocation();
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

  // Capture live parameter from URL immediately
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const liveId = params.get('live');
    if (liveId) {
      setAutoOpenLiveId(liveId);
      window.history.replaceState({}, '', '/festivals');
    }
  }, [location.search]);

  const periodLabels = {
    'monthly': language === 'it' ? 'Questo Mese' : language === 'es' ? 'Este Mes' : 'This Month',
    'yearly': language === 'it' ? 'Quest\'Anno' : language === 'es' ? 'Este Año' : 'This Year',
    'all_time': language === 'it' ? 'Di Sempre' : language === 'es' ? 'De Todos Los Tiempos' : 'All Time'
  };

  const categoryOptions = [
    { id: 'best_film', name: language === 'it' ? 'Miglior Film' : 'Best Film' },
    { id: 'best_director', name: language === 'it' ? 'Miglior Regia' : 'Best Director' },
    { id: 'best_actor', name: language === 'it' ? 'Miglior Attore' : 'Best Actor' },
    { id: 'best_actress', name: language === 'it' ? 'Miglior Attrice' : 'Best Actress' },
    { id: 'best_screenplay', name: language === 'it' ? 'Miglior Sceneggiatura' : 'Best Screenplay' },
    { id: 'best_soundtrack', name: language === 'it' ? 'Miglior Colonna Sonora' : 'Best Soundtrack' },
    { id: 'audience_choice', name: language === 'it' ? 'Premio del Pubblico' : 'Audience Choice' },
  ];

  useEffect(() => {
    loadFestivals();
    loadCustomFestivals();
    loadLeaderboard();
    loadMyAwards();
    loadCreationCost();
  }, [language]);

  const loadFestivals = async () => {
    try {
      const res = await api.get(`/festivals?language=${language}`);
      setFestivals(res.data.festivals);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCustomFestivals = async () => {
    try {
      const res = await api.get('/custom-festivals');
      setCustomFestivals(res.data.festivals || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCreationCost = async () => {
    try {
      const res = await api.get('/custom-festivals/creation-cost');
      setCreationCost(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCustomFestivalDetails = async (festivalId) => {
    try {
      const res = await api.get(`/custom-festivals/${festivalId}`);
      setSelectedCustomFestival(res.data);
      // Load user's films for participation
      const filmsRes = await api.get('/films/my');
      setMyFilms(filmsRes.data || []);
    } catch (e) {
      toast.error('Errore caricamento festival');
    }
  };

  const createCustomFestival = async () => {
    if (!newFestival.name.trim()) { toast.error('Inserisci un nome'); return; }
    setCreating(true);
    try {
      const res = await api.post('/custom-festivals/create', newFestival);
      toast.success(res.data.message);
      setShowCreateDialog(false);
      setNewFestival({ name: '', description: '', poster_prompt: '', categories: ['best_film'], base_participation_cost: 10000, duration_days: 7 });
      loadCustomFestivals();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore creazione');
    } finally {
      setCreating(false);
    }
  };

  const participateInFestival = async () => {
    if (!selectedCustomFestival || selectedFilmIds.length === 0) return;
    setParticipating(true);
    try {
      const res = await api.post('/custom-festivals/participate', { festival_id: selectedCustomFestival.id, film_ids: selectedFilmIds });
      toast.success(res.data.message);
      loadCustomFestivalDetails(selectedCustomFestival.id);
      setSelectedFilmIds([]);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore partecipazione');
    } finally {
      setParticipating(false);
    }
  };

  const loadFestivalEdition = async (festivalId) => {
    try {
      const res = await api.get(`/festivals/${festivalId}/current?language=${language}`);
      setCurrentEdition(res.data);
      setSelectedFestival(festivalId);
    } catch (e) {
      toast.error('Errore caricamento festival');
    }
  };

  const loadLeaderboard = async (period = leaderboardPeriod) => {
    try {
      const res = await api.get(`/festivals/awards/leaderboard?period=${period}&language=${language}`);
      setLeaderboard(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadMyAwards = async () => {
    try {
      const res = await api.get(`/festivals/my-awards?language=${language}`);
      setMyAwards(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleVote = async (categoryId, nomineeId) => {
    if (!currentEdition || voting) return;
    setVoting(true);
    try {
      await api.post('/festivals/vote', {
        festival_id: selectedFestival,
        edition_id: currentEdition.id,
        category: categoryId,
        nominee_id: nomineeId
      });
      toast.success('+5 XP per il voto!');
      loadFestivalEdition(selectedFestival);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore votazione');
    } finally {
      setVoting(false);
    }
  };

  // Live Ceremony functions
  const [viewingBonus, setViewingBonus] = useState({ viewing_minutes: 0, bonus_percent: 0 });
  
  const loadLiveCeremony = async (festivalId) => {
    try {
      const res = await api.get(`/festivals/${festivalId}/live-ceremony?language=${language}`);
      setLiveCeremony(res.data);
      // Join as viewer and get bonus info
      const joinRes = await api.post(`/festivals/${festivalId}/join-ceremony`);
      if (joinRes.data) {
        setViewingBonus({
          viewing_minutes: joinRes.data.viewing_minutes || 0,
          bonus_percent: joinRes.data.bonus_percent || 0
        });
      }
    } catch (e) {
      console.error('Error loading live ceremony:', e);
    }
  };

  const openLiveCeremony = (festival) => {
    setSelectedFestival(festival.id);
    loadLiveCeremony(festival.id);
    setShowLiveCeremony(true);
    // Start chat refresh interval (also pings for viewing bonus)
    chatRefreshInterval.current = setInterval(() => {
      loadLiveCeremony(festival.id);
    }, 5000);  // Ping every 5 seconds to track viewing time
  };

  const closeLiveCeremony = () => {
    setShowLiveCeremony(false);
    setLiveCeremony(null);
    if (chatRefreshInterval.current) {
      clearInterval(chatRefreshInterval.current);
    }
  };

  // Auto-open live ceremony when festivals are loaded and autoOpenLiveId is set
  useEffect(() => {
    if (autoOpenLiveId && festivals.length > 0) {
      const fest = festivals.find(f => f.id === autoOpenLiveId);
      if (fest) {
        openLiveCeremony(fest);
        setAutoOpenLiveId(null);
      }
    }
  }, [autoOpenLiveId, festivals]);

  const sendChatMessage = async () => {
    if (!chatMessage.trim() || !liveCeremony) return;
    setSendingChat(true);
    try {
      await api.post('/festivals/ceremony/chat', {
        festival_id: liveCeremony.festival_id,
        edition_id: liveCeremony.edition_id,
        message: chatMessage
      });
      setChatMessage('');
      loadLiveCeremony(liveCeremony.festival_id);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore invio messaggio');
    } finally {
      setSendingChat(false);
    }
  };

  useEffect(() => {
    return () => {
      if (chatRefreshInterval.current) {
        clearInterval(chatRefreshInterval.current);
      }
    };
  }, []);

  // Audio playback for TTS announcements
  const audioRef = useRef(null);
  const [playingAudio, setPlayingAudio] = useState(false);
  const [announcingCategory, setAnnouncingCategory] = useState(null);
  const [subtitleText, setSubtitleText] = useState('');
  const [subtitleVisible, setSubtitleVisible] = useState(false);
  const [winnerName, setWinnerName] = useState('');
  const [categoryWon, setCategoryWon] = useState('');
  const [showSpotlight, setShowSpotlight] = useState(false);
  
  // Ceremony video state
  const [ceremonyVideo, setCeremonyVideo] = useState(null);
  const [generatingVideo, setGeneratingVideo] = useState(false);

  // Check for ceremony video availability
  useEffect(() => {
    if (selectedFestival) {
      api.get(`/festivals/${selectedFestival}/ceremony-video`)
        .then(res => setCeremonyVideo(res.data))
        .catch(() => setCeremonyVideo(null));
    }
  }, [selectedFestival, api]);

  // Generate ceremony video
  const generateCeremonyVideo = async () => {
    if (!selectedFestival) return;
    setGeneratingVideo(true);
    try {
      const res = await api.post(`/festivals/${selectedFestival}/generate-ceremony-video?language=${language}`);
      setCeremonyVideo({ available: true, video: res.data.video });
      toast.success(language === 'it' ? 'Video generato!' : 'Video generated!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore generazione video');
    } finally {
      setGeneratingVideo(false);
    }
  };

  // Download ceremony video
  const downloadCeremonyVideo = () => {
    if (!selectedFestival) return;
    const link = document.createElement('a');
    link.href = `${process.env.REACT_APP_BACKEND_URL}/api/festivals/${selectedFestival}/ceremony-video/download`;
    link.download = `ceremony_${selectedFestival}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success(language === 'it' ? 'Download avviato!' : 'Download started!');
  };

  // Confetti effects for winner announcement
  const fireConfetti = () => {
    // Gold confetti burst from sides
    const colors = ['#FFD700', '#FFA500', '#FFFF00', '#FFE4B5'];
    
    // Left side burst
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { x: 0, y: 0.6 },
      colors: colors,
      angle: 60
    });
    
    // Right side burst
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { x: 1, y: 0.6 },
      colors: colors,
      angle: 120
    });
    
    // Center celebration after small delay
    setTimeout(() => {
      confetti({
        particleCount: 150,
        spread: 100,
        origin: { x: 0.5, y: 0.5 },
        colors: colors,
        startVelocity: 45,
        gravity: 1.2
      });
    }, 500);
    
    // Star-shaped burst
    setTimeout(() => {
      const end = Date.now() + 1500;
      const interval = setInterval(() => {
        if (Date.now() > end) {
          clearInterval(interval);
          return;
        }
        confetti({
          particleCount: 20,
          spread: 360,
          origin: { x: Math.random(), y: Math.random() - 0.2 },
          colors: colors,
          ticks: 100,
          gravity: 0.8,
          scalar: 1.2,
          shapes: ['star']
        });
      }, 150);
    }, 1000);
  };

  const playAnnouncementAudio = (audioUrl, text, winner, category) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    setPlayingAudio(true);
    setSubtitleText(text);
    setWinnerName(winner);
    setCategoryWon(category);
    setSubtitleVisible(true);
    setShowSpotlight(true);
    
    // Fire confetti when winner name is revealed (after ~2 seconds)
    setTimeout(() => fireConfetti(), 2000);
    
    audio.play();
    audio.onended = () => {
      setPlayingAudio(false);
      // Keep subtitle visible for 2 more seconds after audio ends
      setTimeout(() => {
        setSubtitleVisible(false);
        setShowSpotlight(false);
      }, 2000);
    };
    audio.onerror = () => {
      setPlayingAudio(false);
      setSubtitleVisible(false);
      setShowSpotlight(false);
    };
  };

  const announceWinnerWithAudio = async (categoryId) => {
    if (!liveCeremony) return;
    setAnnouncingCategory(categoryId);
    try {
      const res = await api.post(`/festivals/${liveCeremony.festival_id}/announce-with-audio/${categoryId}?language=${language}`);
      if (res.data.success) {
        // Refresh ceremony data
        loadLiveCeremony(liveCeremony.festival_id);
        // Play audio with subtitles if available
        if (res.data.audio?.audio_url) {
          const announcementText = res.data.announcement_text?.[language] || res.data.announcement_text?.['en'] || '';
          playAnnouncementAudio(
            res.data.audio.audio_url, 
            announcementText,
            res.data.winner?.name || '',
            res.data.category_name || ''
          );
        }
        toast.success(`${language === 'it' ? 'Vincitore' : 'Winner'}: ${res.data.winner.name}!`);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore annuncio');
    } finally {
      setAnnouncingCategory(null);
    }
  };

  const getPrestigeStars = (prestige) => '⭐'.repeat(prestige);

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto" data-testid="festivals-page">
      {/* Navigation bar with festival icons */}
      <div className="flex items-center justify-between mb-4 bg-[#1A1A1A] rounded-lg p-2 sticky top-16 z-10 overflow-x-auto">
        <Button variant="ghost" size="sm" onClick={() => window.history.back()} className="text-gray-400 hover:text-white flex-shrink-0">
          <ArrowLeft className="w-4 h-4 mr-1" />
          {language === 'it' ? 'Indietro' : 'Back'}
        </Button>
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Official Festivals with specific icons */}
          {festivals.map((fest, idx) => {
            // Assign specific icons based on festival name/type
            const getFestivalIcon = (name) => {
              const lowerName = name.toLowerCase();
              if (lowerName.includes('golden') || lowerName.includes('oro') || lowerName.includes('star')) return <Star className="w-3.5 h-3.5" />;
              if (lowerName.includes('spotlight') || lowerName.includes('riflettori')) return <Sparkles className="w-3.5 h-3.5" />;
              if (lowerName.includes('cinema') || lowerName.includes('film')) return <Film className="w-3.5 h-3.5" />;
              return <Award className="w-3.5 h-3.5" />;
            };
            const getIconColor = (name) => {
              const lowerName = name.toLowerCase();
              if (lowerName.includes('golden') || lowerName.includes('oro') || lowerName.includes('star')) return 'text-yellow-400';
              if (lowerName.includes('spotlight') || lowerName.includes('riflettori')) return 'text-purple-400';
              if (lowerName.includes('cinema') || lowerName.includes('film')) return 'text-blue-400';
              return 'text-gray-400';
            };
            return (
              <Button 
                key={fest.id}
                variant="ghost" 
                size="sm" 
                onClick={() => { setActiveTab('festivals'); loadFestivalEdition(fest.id); }}
                className={`text-xs px-2 gap-1 ${selectedFestival === fest.id ? 'text-yellow-400 bg-yellow-500/10' : getIconColor(fest.name)}`}
              >
                {getFestivalIcon(fest.name)}
                <span className="hidden sm:inline">{fest.name.split(' ')[0]}</span>
                {fest.is_active && <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>}
              </Button>
            );
          })}
          {/* Separator */}
          {customFestivals.length > 0 && <div className="w-px h-5 bg-white/20 mx-1"></div>}
          {/* Custom/Player Festivals */}
          {customFestivals.slice(0, 4).map(fest => (
            <Button 
              key={fest.id}
              variant="ghost" 
              size="sm" 
              onClick={() => { setActiveTab('custom'); setSelectedCustomFestival(fest); }}
              className={`text-xs px-2 gap-1 ${selectedCustomFestival?.id === fest.id ? 'text-purple-400 bg-purple-500/10' : 'text-purple-300'}`}
              title={fest.name}
            >
              <Crown className="w-3.5 h-3.5" />
              <span className="hidden sm:inline max-w-[60px] truncate">{fest.name.split(' ')[0]}</span>
              {fest.is_active && <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>}
            </Button>
          ))}
        </div>
      </div>

      <div className="text-center mb-6">
        <Award className="w-12 h-12 text-yellow-500 mx-auto mb-2" />
        <h1 className="font-['Bebas_Neue'] text-3xl">{language === 'it' ? 'Festival del Cinema' : language === 'es' ? 'Festivales de Cine' : 'Film Festivals'}</h1>
        <p className="text-gray-400 text-sm">{language === 'it' ? 'Vota i migliori film e vinci premi!' : 'Vote for the best films and win awards!'}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 justify-center flex-wrap">
        <Button variant={activeTab === 'festivals' ? 'default' : 'outline'} onClick={() => setActiveTab('festivals')} className={activeTab === 'festivals' ? 'bg-yellow-500 text-black' : ''}>
          <Star className="w-4 h-4 mr-2" />{language === 'it' ? 'Festival Ufficiali' : 'Official Festivals'}
        </Button>
        <Button variant={activeTab === 'custom' ? 'default' : 'outline'} onClick={() => setActiveTab('custom')} className={activeTab === 'custom' ? 'bg-purple-500 text-white' : ''}>
          <Crown className="w-4 h-4 mr-2" />{language === 'it' ? 'Festival dei Player' : 'Player Festivals'}
        </Button>
        <Button variant={activeTab === 'leaderboard' ? 'default' : 'outline'} onClick={() => setActiveTab('leaderboard')} className={activeTab === 'leaderboard' ? 'bg-yellow-500 text-black' : ''}>
          <Trophy className="w-4 h-4 mr-2" />{language === 'it' ? 'Classifica' : 'Leaderboard'}
        </Button>
        <Button variant={activeTab === 'my_awards' ? 'default' : 'outline'} onClick={() => setActiveTab('my_awards')} className={activeTab === 'my_awards' ? 'bg-yellow-500 text-black' : ''}>
          <Medal className="w-4 h-4 mr-2" />{language === 'it' ? 'I Miei Premi' : 'My Awards'}
        </Button>
      </div>

      {/* Festivals Tab */}
      {activeTab === 'festivals' && (
        <div className="space-y-4">
          {!selectedFestival ? (
            <div className="grid md:grid-cols-3 gap-4">
              {festivals.map(fest => (
                <Card key={fest.id} className={`bg-[#1A1A1A] border-white/10 cursor-pointer hover:border-yellow-500/50 transition-colors ${fest.is_active ? 'ring-2 ring-yellow-500' : ''}`} onClick={() => loadFestivalEdition(fest.id)}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="font-['Bebas_Neue'] text-lg text-yellow-400">{fest.name}</CardTitle>
                      <span className="text-lg">{getPrestigeStars(fest.prestige)}</span>
                    </div>
                    {fest.is_active && (
                      <div className="flex items-center gap-2">
                        <Badge className="bg-green-500/20 text-green-400 w-fit">{language === 'it' ? 'IN CORSO' : 'ACTIVE'}</Badge>
                        <Button 
                          size="sm" 
                          onClick={(e) => { e.stopPropagation(); openLiveCeremony(fest); }}
                          className="bg-red-500 hover:bg-red-600 text-white text-xs h-6 px-2"
                        >
                          <Tv className="w-3 h-3 mr-1" />{language === 'it' ? 'LIVE' : 'LIVE'}
                        </Button>
                      </div>
                    )}
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-400 text-xs mb-3">{fest.description}</p>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">
                        {language === 'it' ? 'Cerimonia' : 'Ceremony'}: {fest.ceremony_day}/{language === 'it' ? 'mese' : 'month'} {language === 'it' ? 'alle' : 'at'} {fest.ceremony_time || '21:30'}
                      </span>
                      <Badge variant="outline" className={fest.voting_type === 'player' ? 'border-purple-500 text-purple-400' : 'border-blue-500 text-blue-400'}>
                        {fest.voting_type === 'player' ? (language === 'it' ? 'Voto Giocatori' : 'Player Vote') : 'AI'}
                      </Badge>
                    </div>
                    <div className="mt-3 pt-3 border-t border-white/10 grid grid-cols-3 gap-2 text-center text-xs">
                      <div><p className="text-yellow-400 font-bold">+{fest.rewards.xp}</p><p className="text-gray-500">XP</p></div>
                      <div><p className="text-purple-400 font-bold">+{fest.rewards.fame}</p><p className="text-gray-500">{language === 'it' ? 'Fama' : 'Fame'}</p></div>
                      <div><p className="text-green-400 font-bold">${(fest.rewards.money/1000).toFixed(0)}K</p><p className="text-gray-500">{language === 'it' ? 'Denaro' : 'Money'}</p></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : currentEdition && (
            <div>
              <Button variant="ghost" onClick={() => {setSelectedFestival(null); setCurrentEdition(null);}} className="mb-4">
                <ChevronLeft className="w-4 h-4 mr-1" />{language === 'it' ? 'Torna ai Festival' : 'Back to Festivals'}
              </Button>
              
              <Card className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border-yellow-500/30 mb-6">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-['Bebas_Neue'] text-2xl text-yellow-400">{currentEdition.festival_name}</CardTitle>
                    {currentEdition.can_vote && <Badge className="bg-purple-500/20 text-purple-400">{language === 'it' ? 'VOTA ORA' : 'VOTE NOW'}</Badge>}
                  </div>
                  <CardDescription>{language === 'it' ? `Edizione ${currentEdition.month}/${currentEdition.year}` : `Edition ${currentEdition.month}/${currentEdition.year}`}</CardDescription>
                </CardHeader>
              </Card>

              <div className="space-y-4">
                {currentEdition.categories?.map(cat => (
                  <Card key={cat.category_id} className="bg-[#1A1A1A] border-white/10">
                    <CardHeader className="pb-2">
                      <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                        <Award className="w-5 h-5 text-yellow-500" />
                        {cat.name}
                        {cat.user_voted && <Badge className="bg-green-500/20 text-green-400 text-xs ml-2">{language === 'it' ? 'Votato' : 'Voted'}</Badge>}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
                        {cat.nominees?.map(nom => (
                          <div key={nom.id} className={`p-3 rounded-lg border ${cat.user_voted === nom.id ? 'bg-yellow-500/20 border-yellow-500' : 'bg-white/5 border-white/10 hover:border-white/30'} ${currentEdition.can_vote && !cat.user_voted ? 'cursor-pointer' : ''}`}
                            onClick={() => currentEdition.can_vote && !cat.user_voted && handleVote(cat.category_id, nom.id)}>
                            <div className="flex items-center gap-2 mb-2">
                              {nom.poster_url || nom.avatar_url ? (
                                <img src={nom.poster_url || nom.avatar_url} alt="" className="w-10 h-10 rounded object-cover" />
                              ) : (
                                <div className="w-10 h-10 rounded bg-white/10 flex items-center justify-center"><User className="w-5 h-5 text-gray-500" /></div>
                              )}
                              <div className="flex-1 min-w-0">
                                <p className="font-semibold text-sm truncate">{nom.name}</p>
                                {nom.film_title && <p className="text-xs text-gray-400 truncate">{nom.film_title}</p>}
                              </div>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-gray-500">{nom.votes || 0} {language === 'it' ? 'voti' : 'votes'}</span>
                              {currentEdition.can_vote && !cat.user_voted && <Button size="sm" className="h-6 text-xs bg-yellow-500 text-black hover:bg-yellow-400" disabled={voting}>{language === 'it' ? 'Vota' : 'Vote'}</Button>}
                            </div>
                          </div>
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

      {/* Custom Festivals Tab */}
      {activeTab === 'custom' && (
        <div className="space-y-4">
          {/* Create Button */}
          {creationCost && (
            <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30">
              <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="font-['Bebas_Neue'] text-lg text-purple-400">{language === 'it' ? 'Crea il Tuo Festival' : 'Create Your Festival'}</h3>
                  <p className="text-xs text-gray-400">
                    {creationCost.can_create 
                      ? `Costo: $${creationCost.creation_cost?.toLocaleString()} • Livello ${creationCost.user_level}`
                      : `Richiesto Livello ${creationCost.required_level} (sei ${creationCost.user_level})`}
                  </p>
                </div>
                <Button 
                  onClick={() => setShowCreateDialog(true)} 
                  disabled={!creationCost.can_create}
                  className="bg-purple-500 hover:bg-purple-400"
                >
                  <Plus className="w-4 h-4 mr-2" />{language === 'it' ? 'Crea Festival' : 'Create Festival'}
                </Button>
              </CardContent>
            </Card>
          )}

          {!selectedCustomFestival ? (
            <div className="grid md:grid-cols-2 gap-4">
              {customFestivals.length === 0 ? (
                <Card className="bg-[#1A1A1A] border-white/10 col-span-2">
                  <CardContent className="p-8 text-center">
                    <Crown className="w-12 h-12 text-purple-400/50 mx-auto mb-2" />
                    <p className="text-gray-400">{language === 'it' ? 'Nessun festival dei player attivo. Creane uno!' : 'No player festivals active. Create one!'}</p>
                  </CardContent>
                </Card>
              ) : customFestivals.map(fest => (
                <Card key={fest.id} className="bg-[#1A1A1A] border-white/10 cursor-pointer hover:border-purple-500/50 transition-colors" onClick={() => loadCustomFestivalDetails(fest.id)}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="font-['Bebas_Neue'] text-lg text-purple-400">{fest.name}</CardTitle>
                      <Badge className={fest.status === 'open' ? 'bg-green-500/20 text-green-400' : fest.status === 'live' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'}>
                        {fest.status === 'open' ? 'APERTO' : fest.status === 'live' ? 'LIVE' : fest.status.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-400 text-xs mb-2">{fest.description?.substring(0, 100)}...</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <User className="w-3 h-3" /> {fest.creator_name}
                      <span>•</span>
                      <span>${fest.prize_pool?.toLocaleString()} montepremi</span>
                    </div>
                    {fest.poster_url && <img src={fest.poster_url} alt="" className="mt-2 w-full h-32 object-cover rounded" />}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div>
              <Button variant="ghost" onClick={() => {setSelectedCustomFestival(null); setSelectedFilmIds([]);}} className="mb-4">
                <ChevronLeft className="w-4 h-4 mr-1" />{language === 'it' ? 'Torna ai Festival' : 'Back'}
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
                    {language === 'it' ? 'Creato da' : 'Created by'} {selectedCustomFestival.creator_name} • 
                    Montepremi: ${selectedCustomFestival.prize_pool?.toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-300 mb-4">{selectedCustomFestival.description}</p>
                  
                  {/* Participation Section */}
                  {selectedCustomFestival.status === 'open' && !selectedCustomFestival.user_participating && (
                    <Card className="bg-black/30 border-white/10 mb-4">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">{language === 'it' ? 'Partecipa!' : 'Participate!'}</CardTitle>
                        <CardDescription className="text-xs">
                          {language === 'it' 
                            ? `Costo base: $${selectedCustomFestival.base_participation_cost?.toLocaleString()} per film` 
                            : `Base cost: $${selectedCustomFestival.base_participation_cost?.toLocaleString()} per film`}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ScrollArea className="h-[150px] mb-3">
                          <div className="space-y-2">
                            {myFilms.map((film, i) => {
                              const isSelected = selectedFilmIds.includes(film.id);
                              const cost = Math.floor(selectedCustomFestival.base_participation_cost * Math.pow(1.5, selectedFilmIds.indexOf(film.id) > -1 ? selectedFilmIds.indexOf(film.id) : selectedFilmIds.length));
                              return (
                                <div key={film.id} className={`p-2 rounded flex items-center justify-between cursor-pointer ${isSelected ? 'bg-purple-500/20 border border-purple-500' : 'bg-white/5 hover:bg-white/10'}`}
                                  onClick={() => {
                                    if (isSelected) {
                                      setSelectedFilmIds(selectedFilmIds.filter(id => id !== film.id));
                                    } else if (selectedFilmIds.length < (selectedCustomFestival.creator_id === user?.id ? 1 : 10)) {
                                      setSelectedFilmIds([...selectedFilmIds, film.id]);
                                    }
                                  }}>
                                  <span className="text-sm">{film.title}</span>
                                  {isSelected && <Check className="w-4 h-4 text-purple-400" />}
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
                    <Badge className="bg-green-500/20 text-green-400 mb-4">{language === 'it' ? 'Stai partecipando!' : 'You are participating!'}</Badge>
                  )}
                  
                  {/* Categories */}
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
              <Crown className="w-5 h-5" /> {language === 'it' ? 'Crea il Tuo Festival' : 'Create Your Festival'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 max-h-[60vh] overflow-y-auto">
            <div>
              <Label className="text-xs">{language === 'it' ? 'Nome del Festival' : 'Festival Name'}</Label>
              <Input value={newFestival.name} onChange={e => setNewFestival({...newFestival, name: e.target.value})} placeholder="Il Mio Festival..." className="bg-black/20 border-white/10" />
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Descrizione' : 'Description'}</Label>
              <Textarea value={newFestival.description} onChange={e => setNewFestival({...newFestival, description: e.target.value})} placeholder="Descrivi il tuo festival..." className="bg-black/20 border-white/10 h-20" />
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Prompt Locandina AI (opzionale)' : 'Poster AI Prompt (optional)'}</Label>
              <Input value={newFestival.poster_prompt} onChange={e => setNewFestival({...newFestival, poster_prompt: e.target.value})} placeholder="Stile elegante, colori dorati..." className="bg-black/20 border-white/10" />
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Categorie Premio' : 'Award Categories'}</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {categoryOptions.map(cat => (
                  <Badge key={cat.id} variant={newFestival.categories.includes(cat.id) ? 'default' : 'outline'} className={`cursor-pointer ${newFestival.categories.includes(cat.id) ? 'bg-purple-500' : 'hover:bg-white/10'}`}
                    onClick={() => {
                      if (newFestival.categories.includes(cat.id)) {
                        setNewFestival({...newFestival, categories: newFestival.categories.filter(c => c !== cat.id)});
                      } else {
                        setNewFestival({...newFestival, categories: [...newFestival.categories, cat.id]});
                      }
                    }}>
                    {cat.name}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs">{language === 'it' ? 'Costo Partecipazione' : 'Participation Cost'}</Label>
                <Input type="number" value={newFestival.base_participation_cost} onChange={e => setNewFestival({...newFestival, base_participation_cost: parseInt(e.target.value) || 10000})} className="bg-black/20 border-white/10" />
              </div>
              <div>
                <Label className="text-xs">{language === 'it' ? 'Durata (giorni)' : 'Duration (days)'}</Label>
                <Input type="number" value={newFestival.duration_days} onChange={e => setNewFestival({...newFestival, duration_days: parseInt(e.target.value) || 7})} min={1} max={30} className="bg-black/20 border-white/10" />
              </div>
            </div>
            {creationCost && (
              <Card className="bg-purple-500/10 border-purple-500/30">
                <CardContent className="p-3">
                  <div className="flex justify-between items-center">
                    <span>{language === 'it' ? 'Costo Creazione' : 'Creation Cost'}</span>
                    <span className="text-purple-400 font-bold">${creationCost.creation_cost?.toLocaleString()}</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>{language === 'it' ? 'Annulla' : 'Cancel'}</Button>
            <Button onClick={createCustomFestival} disabled={creating || !newFestival.name || newFestival.categories.length === 0} className="bg-purple-500">
              {creating ? 'Creazione...' : language === 'it' ? 'Crea Festival' : 'Create Festival'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div>
          <div className="flex gap-2 mb-4 justify-center">
            {['monthly', 'yearly', 'all_time'].map(p => (
              <Button key={p} variant={leaderboardPeriod === p ? 'default' : 'outline'} size="sm" onClick={() => {setLeaderboardPeriod(p); loadLeaderboard(p);}} className={leaderboardPeriod === p ? 'bg-yellow-500 text-black' : ''}>
                {periodLabels[p]}
              </Button>
            ))}
          </div>
          
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader><CardTitle className="font-['Bebas_Neue'] text-xl">{language === 'it' ? 'Classifica Premi' : 'Awards Leaderboard'} - {periodLabels[leaderboardPeriod]}</CardTitle></CardHeader>
            <CardContent>
              {leaderboard?.leaderboard?.length > 0 ? (
                <div className="space-y-2">
                  {leaderboard.leaderboard.map((entry, i) => (
                    <div key={entry.user_id} className={`flex items-center gap-3 p-3 rounded ${i < 3 ? 'bg-yellow-500/10' : 'bg-white/5'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${i === 0 ? 'bg-yellow-500 text-black' : i === 1 ? 'bg-gray-400 text-black' : i === 2 ? 'bg-amber-600 text-black' : 'bg-white/10'}`}>
                        {entry.rank}
                      </div>
                      <img src={entry.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${entry.nickname}`} alt="" className="w-10 h-10 rounded-full" />
                      <div className="flex-1">
                        <p className="font-semibold"><ClickableNickname userId={entry.user_id} nickname={entry.nickname} /></p>
                        <p className="text-xs text-gray-400">Lv.{entry.level} • {entry.fame} {language === 'it' ? 'Fama' : 'Fame'}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-yellow-400 font-bold">{entry.total_awards} <Trophy className="w-4 h-4 inline" /></p>
                        <p className="text-xs text-gray-500">{entry.total_prestige} prestige</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-400 py-8">{language === 'it' ? 'Nessun premio assegnato ancora' : 'No awards yet'}</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* My Awards Tab */}
      {activeTab === 'my_awards' && (
        <div>
          {myAwards?.stats && (
            <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30 mb-6">
              <CardContent className="p-6">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <Trophy className="w-8 h-8 text-yellow-500 mx-auto mb-1" />
                    <p className="text-2xl font-bold text-yellow-400">{myAwards.stats.total_awards}</p>
                    <p className="text-xs text-gray-400">{language === 'it' ? 'Premi Totali' : 'Total Awards'}</p>
                  </div>
                  <div>
                    <Star className="w-8 h-8 text-purple-400 mx-auto mb-1" />
                    <p className="text-2xl font-bold text-purple-400">{Object.keys(myAwards.stats.by_festival).length}</p>
                    <p className="text-xs text-gray-400">{language === 'it' ? 'Festival Vinti' : 'Festivals Won'}</p>
                  </div>
                  <div>
                    <Award className="w-8 h-8 text-pink-400 mx-auto mb-1" />
                    <p className="text-2xl font-bold text-pink-400">{Object.keys(myAwards.stats.by_category).length}</p>
                    <p className="text-xs text-gray-400">{language === 'it' ? 'Categorie' : 'Categories'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader><CardTitle className="font-['Bebas_Neue'] text-xl">{language === 'it' ? 'I Miei Premi' : 'My Awards'}</CardTitle></CardHeader>
            <CardContent>
              {myAwards?.awards?.length > 0 ? (
                <div className="space-y-2">
                  {myAwards.awards.map(award => (
                    <div key={award.id} className="flex items-center gap-3 p-3 bg-white/5 rounded">
                      <Award className="w-8 h-8 text-yellow-500" />
                      <div className="flex-1">
                        <p className="font-semibold text-yellow-400">{award.category_name}</p>
                        <p className="text-sm">{award.winner_name}</p>
                        <p className="text-xs text-gray-400">{award.festival_name} • {award.film_title}</p>
                      </div>
                      <div className="text-right text-xs text-gray-500">
                        {award.month}/{award.year}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Trophy className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-400">{language === 'it' ? 'Non hai ancora vinto premi. Partecipa ai festival!' : 'No awards yet. Participate in festivals!'}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Live Ceremony Modal */}
      {showLiveCeremony && liveCeremony && (
        <div className="fixed inset-0 bg-black/95 z-50 flex flex-col" onClick={closeLiveCeremony}>
          
          {/* Spotlight Effect */}
          {showSpotlight && (
            <div className="fixed inset-0 z-[55] pointer-events-none overflow-hidden">
              {/* Radial spotlight from top */}
              <motion.div
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px]"
                style={{
                  background: 'radial-gradient(ellipse at center top, rgba(255,215,0,0.3) 0%, rgba(255,215,0,0.1) 30%, transparent 70%)',
                }}
              />
              {/* Moving spotlight beams */}
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-0 left-1/4 w-32 h-[100vh] origin-top"
                style={{
                  background: 'linear-gradient(180deg, rgba(255,215,0,0.2) 0%, transparent 100%)',
                  transform: 'rotate(-15deg)',
                }}
              />
              <motion.div
                animate={{ rotate: [0, -10, 10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                className="absolute top-0 right-1/4 w-32 h-[100vh] origin-top"
                style={{
                  background: 'linear-gradient(180deg, rgba(255,215,0,0.2) 0%, transparent 100%)',
                  transform: 'rotate(15deg)',
                }}
              />
              {/* Golden particles */}
              {[...Array(20)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-2 h-2 bg-yellow-400 rounded-full"
                  initial={{ 
                    x: Math.random() * window.innerWidth, 
                    y: -20,
                    opacity: 0 
                  }}
                  animate={{ 
                    y: window.innerHeight + 20,
                    opacity: [0, 1, 1, 0],
                    scale: [0.5, 1, 0.5]
                  }}
                  transition={{ 
                    duration: 3 + Math.random() * 2,
                    repeat: Infinity,
                    delay: Math.random() * 2,
                    ease: "linear"
                  }}
                />
              ))}
            </div>
          )}

          {/* Subtitle Overlay */}
          {subtitleVisible && (
            <motion.div 
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 50 }}
              className="fixed inset-0 z-[60] pointer-events-none flex items-center justify-center"
            >
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
              <div className="absolute bottom-20 left-0 right-0 px-8">
                <motion.div 
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  className="max-w-3xl mx-auto text-center"
                >
                  {/* Category name */}
                  <motion.p 
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-yellow-500 text-lg font-semibold mb-2 uppercase tracking-wider"
                  >
                    {categoryWon}
                  </motion.p>
                  
                  {/* Main subtitle text */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="bg-black/70 backdrop-blur-sm rounded-xl px-8 py-6 border border-yellow-500/30"
                  >
                    <p className="text-white text-2xl md:text-3xl font-['Bebas_Neue'] leading-relaxed">
                      {subtitleText}
                    </p>
                  </motion.div>
                  
                  {/* Winner spotlight */}
                  {winnerName && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 1.5, type: "spring", stiffness: 200 }}
                      className="mt-6"
                    >
                      <div className="inline-flex items-center gap-3 bg-yellow-500 text-black px-6 py-3 rounded-full">
                        <Trophy className="w-6 h-6" />
                        <span className="text-xl font-bold">{winnerName}</span>
                        <Trophy className="w-6 h-6" />
                      </div>
                    </motion.div>
                  )}
                  
                  {/* Audio wave animation */}
                  {playingAudio && (
                    <div className="mt-4 flex justify-center gap-1">
                      {[...Array(5)].map((_, i) => (
                        <motion.div
                          key={i}
                          className="w-1 bg-yellow-500 rounded-full"
                          animate={{ height: [8, 24, 8] }}
                          transition={{ 
                            duration: 0.5, 
                            repeat: Infinity, 
                            delay: i * 0.1,
                            ease: "easeInOut"
                          }}
                        />
                      ))}
                    </div>
                  )}
                </motion.div>
              </div>
            </motion.div>
          )}

          <div className="flex-1 overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            {/* Main ceremony area - scrollable */}
            <div className="flex-1 p-3 sm:p-4 overflow-y-auto min-h-0">
              <div className="max-w-4xl mx-auto">
                {/* Header - Mobile Optimized */}
                <div className="flex items-start justify-between mb-4 gap-2">
                  <div className="flex-1 min-w-0">
                    <h1 className="font-['Bebas_Neue'] text-xl sm:text-3xl text-yellow-400 flex items-center gap-2 truncate">
                      <Tv className="w-5 h-5 sm:w-8 sm:h-8 flex-shrink-0" />
                      <span className="truncate">{liveCeremony.festival_name}</span>
                    </h1>
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs sm:text-sm text-gray-400 mt-1">
                      <span className="flex items-center gap-1">
                        <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                        LIVE • {liveCeremony.viewers_count} {language === 'it' ? 'spettatori' : 'viewers'}
                      </span>
                      <span className="px-1.5 py-0.5 bg-green-500/20 rounded-full text-green-400 text-[10px] sm:text-xs flex items-center gap-1">
                        <TrendingUp className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                        +{viewingBonus.bonus_percent.toFixed(1)}% ({viewingBonus.viewing_minutes.toFixed(0)}min)
                      </span>
                    </div>
                    {playingAudio && (
                      <span className="inline-flex items-center gap-1 text-green-400 text-xs mt-1">
                        <Music className="w-3 h-3 animate-bounce" />
                        {language === 'it' ? 'Audio...' : 'Playing...'}
                      </span>
                    )}
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={closeLiveCeremony} 
                    className="bg-red-500/10 border-red-500/50 hover:bg-red-500 hover:text-white h-8 px-2 sm:px-3 flex-shrink-0"
                  >
                    <X className="w-4 h-4" />
                    <span className="hidden sm:inline ml-1">{language === 'it' ? 'Chiudi' : 'Close'}</span>
                  </Button>
                </div>

                {/* Categories with odds/papabili - Mobile Optimized */}
                <div className="space-y-3">
                  {liveCeremony.categories?.map((cat, idx) => (
                    <Card key={cat.category_id} className={`bg-[#1A1A1A] border-white/10 ${cat.is_announced ? 'border-yellow-500/50' : ''}`}>
                      <CardHeader className="pb-2 px-3 sm:px-6 pt-3 sm:pt-6">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <CardTitle className="font-['Bebas_Neue'] text-base sm:text-lg flex items-center gap-2">
                            <Award className="w-4 h-4 sm:w-5 sm:h-5 text-yellow-500" />
                            {cat.category_name}
                          </CardTitle>
                          <div className="flex items-center gap-2 flex-wrap">
                            {cat.is_announced ? (
                              <Badge className="bg-yellow-500 text-black text-[10px] sm:text-xs">{language === 'it' ? 'VINCITORE' : 'WINNER'}</Badge>
                            ) : cat.favorite && (
                              <Badge className="bg-purple-500/20 text-purple-400 text-[10px] sm:text-xs">
                                {language === 'it' ? 'Papabile' : 'Fav'}: {cat.favorite.name.split(' ')[0]} ({cat.favorite.win_probability}%)
                              </Badge>
                            )}
                            {!cat.is_announced && (
                              <Button 
                                size="sm"
                                onClick={() => announceWinnerWithAudio(cat.category_id)}
                                disabled={announcingCategory === cat.category_id}
                                className="bg-red-500 hover:bg-red-600 text-white text-[10px] sm:text-xs h-6 sm:h-7 px-2"
                              >
                                {announcingCategory === cat.category_id ? (
                                  <RefreshCw className="w-3 h-3 animate-spin" />
                                ) : (
                                  <><Music className="w-3 h-3 mr-1" />{language === 'it' ? 'Annuncia' : 'Announce'}</>
                                )}
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
                        <div className="grid gap-1.5 sm:gap-2">
                          {cat.nominees?.map(nom => (
                            <div 
                              key={nom.id} 
                              className={`flex items-center gap-2 p-1.5 sm:p-2 rounded transition-all ${cat.winner?.id === nom.id ? 'bg-yellow-500/20 border border-yellow-500 animate-pulse' : 'bg-white/5'}`}
                            >
                              <div className="flex-1 min-w-0 overflow-hidden">
                                <p className={`font-medium text-xs sm:text-sm truncate max-w-[150px] sm:max-w-[200px] ${cat.winner?.id === nom.id ? 'text-yellow-400' : ''}`}>
                                  {nom.name?.length > 25 ? nom.name.substring(0, 25) + '...' : nom.name}
                                  {cat.winner?.id === nom.id && <Trophy className="w-3 h-3 inline ml-1 text-yellow-500" />}
                                </p>
                                {nom.film_title && (
                                  <p className="text-[9px] sm:text-xs text-gray-400 truncate max-w-[150px] sm:max-w-[200px]">
                                    {nom.film_title?.length > 30 ? nom.film_title.substring(0, 30) + '...' : nom.film_title}
                                  </p>
                                )}
                              </div>
                              <div className="text-right flex-shrink-0 min-w-[40px]">
                                <div className="text-xs font-bold" style={{color: `hsl(${nom.win_probability * 1.2}, 70%, 50%)`}}>
                                  {nom.win_probability}%
                                </div>
                                <div className="text-[8px] sm:text-[9px] text-gray-500">{nom.votes}v</div>
                              </div>
                              {/* Win probability bar - smaller on mobile */}
                              <div className="w-12 sm:w-20 h-1.5 sm:h-2 bg-white/10 rounded-full overflow-hidden flex-shrink-0">
                                <div 
                                  className="h-full bg-gradient-to-r from-purple-500 to-yellow-500 transition-all"
                                  style={{width: `${nom.win_probability}%`}}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Video Generation Section - Shown when all categories are announced */}
                {liveCeremony.categories?.every(cat => cat.is_announced) && (
                  <Card className="mt-4 bg-gradient-to-r from-yellow-500/10 to-purple-500/10 border-yellow-500/30">
                    <CardContent className="p-4">
                      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                        <div className="text-center sm:text-left">
                          <h3 className="font-semibold text-yellow-400 flex items-center gap-2 justify-center sm:justify-start">
                            <Film className="w-5 h-5" />
                            {language === 'it' ? 'Video Riassuntivo Cerimonia' : 'Ceremony Recap Video'}
                          </h3>
                          <p className="text-xs text-gray-400 mt-1">
                            {ceremonyVideo?.available 
                              ? (language === 'it' ? 'Video disponibile per 3 giorni' : 'Video available for 3 days')
                              : (language === 'it' ? 'Genera un video con tutti i vincitori' : 'Generate a video with all winners')
                            }
                          </p>
                        </div>
                        <div className="flex gap-2">
                          {!ceremonyVideo?.available ? (
                            <Button
                              onClick={generateCeremonyVideo}
                              disabled={generatingVideo}
                              className="bg-yellow-500 hover:bg-yellow-600 text-black"
                            >
                              {generatingVideo ? (
                                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />{language === 'it' ? 'Generando...' : 'Generating...'}</>
                              ) : (
                                <><Film className="w-4 h-4 mr-2" />{language === 'it' ? 'Genera Video' : 'Generate Video'}</>
                              )}
                            </Button>
                          ) : (
                            <Button
                              onClick={downloadCeremonyVideo}
                              className="bg-green-500 hover:bg-green-600 text-white"
                            >
                              <Download className="w-4 h-4 mr-2" />
                              {language === 'it' ? 'Scarica Video' : 'Download Video'}
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>

            {/* Chat sidebar - responsive for mobile */}
            <div className="w-full md:w-80 bg-[#0D0D0D] border-t md:border-t-0 md:border-l border-white/10 flex flex-col max-h-[40vh] md:max-h-none">
              <div className="p-3 border-b border-white/10 flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  {language === 'it' ? 'Chat Live' : 'Live Chat'}
                </h3>
                {/* Close button for mobile */}
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={closeLiveCeremony}
                  className="md:hidden h-7 w-7 p-0 text-gray-400 hover:text-red-400"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              
              {/* Chat messages */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-[100px]">
                {liveCeremony.chat_messages?.map(msg => (
                  <div key={msg.id} className="text-sm">
                    <span className="font-semibold text-yellow-400">{msg.nickname}:</span>
                    <span className="text-gray-300 ml-1">{msg.message}</span>
                  </div>
                ))}
                {(!liveCeremony.chat_messages || liveCeremony.chat_messages.length === 0) && (
                  <p className="text-gray-500 text-center text-sm">{language === 'it' ? 'Nessun messaggio ancora' : 'No messages yet'}</p>
                )}
              </div>
              
              {/* Chat input */}
              <div className="p-2 md:p-3 border-t border-white/10">
                <div className="flex gap-2">
                  <Input 
                    value={chatMessage}
                    onChange={e => setChatMessage(e.target.value)}
                    placeholder={language === 'it' ? 'Scrivi...' : 'Type...'}
                    className="flex-1 bg-white/5 border-white/10 text-sm h-9 md:h-8"
                    maxLength={200}
                    onKeyDown={e => e.key === 'Enter' && sendChatMessage()}
                  />
                  <Button 
                    size="sm" 
                    onClick={sendChatMessage} 
                    disabled={sendingChat || !chatMessage.trim()}
                    className="bg-yellow-500 text-black h-9 md:h-8 px-3"
                  >
                    <Send className="w-4 h-4 md:w-3 md:h-3" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Sagas & Series Page

export default FestivalsPage;
