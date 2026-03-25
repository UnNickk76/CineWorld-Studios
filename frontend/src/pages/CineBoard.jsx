// CineWorld Studio's - CineBoard
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding,
  Tv, Radio
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { ClickableNickname } from '../components/shared';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CineBoard = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const [searchParams] = useSearchParams();
  const currentView = searchParams.get('view') || 'film'; // film, series, anime, tv-alltime, tv-weekly, tv-daily
  const [activeTab, setActiveTab] = useState('daily');
  const [films, setFilms] = useState([]);
  const [attendanceData, setAttendanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seriesData, setSeriesData] = useState([]);
  const [animeData, setAnimeData] = useState([]);
  const [tvStationsData, setTvStationsData] = useState([]);
  const navigate = useNavigate();

  const t = (key) => {
    const translations = {
      cineboard: language === 'it' ? 'CineBoard' : 'CineBoard',
      nowPlaying: language === 'it' ? 'In Sala (Top 50)' : 'Now Playing (Top 50)',
      daily: language === 'it' ? 'Giornaliera' : 'Daily',
      weekly: language === 'it' ? 'Settimanale' : 'Weekly',
      attendance: language === 'it' ? 'Affluenze' : 'Attendance',
      rank: language === 'it' ? 'Pos' : 'Rank',
      score: language === 'it' ? 'Punteggio' : 'Score',
      noFilms: language === 'it' ? 'Nessun film in classifica' : 'No films in rankings',
      quality: language === 'it' ? 'Qualità' : 'Quality',
      revenue: language === 'it' ? 'Incassi' : 'Revenue',
      likes: language === 'it' ? 'Like' : 'Likes'
    };
    return translations[key] || key;
  };

  useEffect(() => {
    setLoading(true);
    if (currentView === 'series') {
      api.get('/cineboard/series-weekly')
        .then(r => setSeriesData(r.data.series || []))
        .catch(() => setSeriesData([]))
        .finally(() => setLoading(false));
    } else if (currentView === 'anime') {
      api.get('/cineboard/anime-weekly')
        .then(r => setAnimeData(r.data.series || []))
        .catch(() => setAnimeData([]))
        .finally(() => setLoading(false));
    } else if (currentView === 'tv-alltime') {
      api.get('/cineboard/tv-stations-alltime')
        .then(r => setTvStationsData(r.data.stations || []))
        .catch(() => setTvStationsData([]))
        .finally(() => setLoading(false));
    } else if (currentView === 'tv-weekly') {
      api.get('/cineboard/tv-stations-weekly')
        .then(r => setTvStationsData(r.data.stations || []))
        .catch(() => setTvStationsData([]))
        .finally(() => setLoading(false));
    } else if (currentView === 'tv-daily') {
      api.get('/cineboard/tv-stations-daily')
        .then(r => setTvStationsData(r.data.stations || []))
        .catch(() => setTvStationsData([]))
        .finally(() => setLoading(false));
    } else if (activeTab === 'attendance') {
      api.get('/cineboard/attendance')
        .then(r => setAttendanceData(r.data))
        .catch(() => setAttendanceData(null))
        .finally(() => setLoading(false));
    } else {
      const endpointMap = {
        now_playing: '/cineboard/now-playing',
        daily: '/cineboard/daily',
        weekly: '/cineboard/weekly'
      };
      const endpoint = endpointMap[activeTab] || '/cineboard/now-playing';
      api.get(endpoint)
        .then(r => setFilms(r.data.films || []))
        .catch(() => setFilms([]))
        .finally(() => setLoading(false));
    }
  }, [api, activeTab, currentView]);

  if (loading) return <LoadingSpinner />;

  const getRankBadge = (rank) => {
    if (rank === 1) return 'bg-yellow-500 text-black';
    if (rank === 2) return 'bg-gray-300 text-black';
    if (rank === 3) return 'bg-amber-600 text-white';
    if (rank <= 10) return 'bg-purple-500/20 text-purple-400';
    return 'bg-white/10 text-gray-400';
  };


  const genreColors = {
    action: 'from-red-900 to-red-700', comedy: 'from-yellow-900 to-yellow-700',
    drama: 'from-blue-900 to-blue-700', horror: 'from-gray-900 to-gray-700',
    scifi: 'from-cyan-900 to-cyan-700', fantasy: 'from-purple-900 to-purple-700',
    thriller: 'from-slate-900 to-slate-700', romance: 'from-pink-900 to-pink-700',
    noir: 'from-zinc-900 to-zinc-700', western: 'from-amber-900 to-amber-700',
    musical: 'from-fuchsia-900 to-fuchsia-700', war: 'from-stone-900 to-stone-700',
    biographical: 'from-emerald-900 to-emerald-700', adventure: 'from-orange-900 to-orange-700',
    animation: 'from-lime-900 to-lime-700', historical: 'from-teal-900 to-teal-700'
  };
  const genreIcons = {
    action: Flame, comedy: Sparkles, drama: Heart, horror: AlertTriangle,
    scifi: Zap, fantasy: Wand2, thriller: Target, romance: Heart,
    noir: Eye, western: MapPin, musical: Music, war: Shield,
    biographical: BookOpen, adventure: Globe, animation: Palette, historical: Crown
  };

  const FilmPoster = ({film}) => {
    const gradient = genreColors[film.genre] || 'from-gray-900 to-gray-700';
    const Icon = genreIcons[film.genre] || Film;
    return (
      <div className={`w-full h-full bg-gradient-to-b ${gradient} flex flex-col items-center justify-center p-1`}>
        <Icon className="w-5 h-5 text-white/60 mb-1" />
        <span className="text-[7px] text-white/80 text-center leading-tight line-clamp-2">{film.title}</span>
      </div>
    );
  };

  // Series TV Weekly Trend View
  if (currentView === 'series') {
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="cineboard-series-page">
        <div className="flex items-center gap-3 mb-4">
          <Tv className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="font-['Bebas_Neue'] text-3xl text-blue-400">Trend Serie TV</h1>
            <p className="text-xs text-gray-400">Classifica settimanale delle migliori serie TV</p>
          </div>
        </div>
        {seriesData.length === 0 ? (
          <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
            <Tv className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <h3 className="text-lg mb-2 text-gray-400">Nessuna serie in classifica</h3>
            <p className="text-xs text-gray-500">Produci serie TV per vederle qui!</p>
          </Card>
        ) : (
          <div className="space-y-2">
            {seriesData.map(s => (
              <Card key={s.id} className={`bg-[#1A1A1A] border-white/10 overflow-hidden ${s.rank <= 3 ? 'border-blue-500/30' : ''}`} data-testid={`series-rank-${s.rank}`}>
                <div className="flex">
                  <div className={`w-12 flex items-center justify-center font-bold text-lg ${
                    s.rank === 1 ? 'bg-yellow-500 text-black' : s.rank === 2 ? 'bg-gray-300 text-black' : s.rank === 3 ? 'bg-amber-600 text-white' : s.rank <= 10 ? 'bg-blue-500/20 text-blue-400' : 'bg-white/10 text-gray-400'
                  }`}>#{s.rank}</div>
                  <div className="w-16 flex-shrink-0 bg-blue-500/10 flex items-center justify-center">
                    {s.poster_url ? <img src={s.poster_url.startsWith('/') ? `${BACKEND_URL}${s.poster_url}` : s.poster_url} alt="" className="w-full h-full object-cover" loading="lazy" /> : <Tv className="w-6 h-6 text-blue-400/50" />}
                  </div>
                  <CardContent className="flex-1 p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm truncate">{s.title}</h3>
                        <p className="text-[10px] text-gray-400 truncate">{s.owner?.production_house_name || s.owner?.nickname || 'Studio'}</p>
                      </div>
                      <div className="flex items-center gap-1 bg-blue-500/20 px-2 py-1 rounded ml-2">
                        <Star className="w-3.5 h-3.5 text-blue-400 fill-blue-400" />
                        <span className="font-bold text-blue-400 text-sm">{s.quality_score?.toFixed(1)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <Badge className="bg-white/10 text-gray-300 text-[10px] h-5">{s.genre_name}</Badge>
                      <span className="text-[10px] text-gray-400">{s.num_episodes} ep. - S{s.season_number}</span>
                      {s.is_new && <Badge className="bg-green-500/20 text-green-400 text-[9px]">Nuovo</Badge>}
                    </div>
                  </CardContent>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Anime Weekly Trend View
  if (currentView === 'anime') {
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="cineboard-anime-page">
        <div className="flex items-center gap-3 mb-4">
          <Sparkles className="w-8 h-8 text-orange-400" />
          <div>
            <h1 className="font-['Bebas_Neue'] text-3xl text-orange-400">Trend Anime</h1>
            <p className="text-xs text-gray-400">Classifica settimanale dei migliori anime</p>
          </div>
        </div>
        {animeData.length === 0 ? (
          <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
            <Sparkles className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <h3 className="text-lg mb-2 text-gray-400">Nessun anime in classifica</h3>
            <p className="text-xs text-gray-500">Produci anime per vederli qui!</p>
          </Card>
        ) : (
          <div className="space-y-2">
            {animeData.map(s => (
              <Card key={s.id} className={`bg-[#1A1A1A] border-white/10 overflow-hidden ${s.rank <= 3 ? 'border-orange-500/30' : ''}`} data-testid={`anime-rank-${s.rank}`}>
                <div className="flex">
                  <div className={`w-12 flex items-center justify-center font-bold text-lg ${
                    s.rank === 1 ? 'bg-yellow-500 text-black' : s.rank === 2 ? 'bg-gray-300 text-black' : s.rank === 3 ? 'bg-amber-600 text-white' : s.rank <= 10 ? 'bg-orange-500/20 text-orange-400' : 'bg-white/10 text-gray-400'
                  }`}>#{s.rank}</div>
                  <div className="w-16 flex-shrink-0 bg-orange-500/10 flex items-center justify-center">
                    {s.poster_url ? <img src={s.poster_url.startsWith('/') ? `${BACKEND_URL}${s.poster_url}` : s.poster_url} alt="" className="w-full h-full object-cover" loading="lazy" /> : <Sparkles className="w-6 h-6 text-orange-400/50" />}
                  </div>
                  <CardContent className="flex-1 p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm truncate">{s.title}</h3>
                        <p className="text-[10px] text-gray-400 truncate">{s.owner?.production_house_name || s.owner?.nickname || 'Studio'}</p>
                      </div>
                      <div className="flex items-center gap-1 bg-orange-500/20 px-2 py-1 rounded ml-2">
                        <Star className="w-3.5 h-3.5 text-orange-400 fill-orange-400" />
                        <span className="font-bold text-orange-400 text-sm">{s.quality_score?.toFixed(1)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <Badge className="bg-white/10 text-gray-300 text-[10px] h-5">{s.genre_name}</Badge>
                      <span className="text-[10px] text-gray-400">{s.num_episodes} ep.</span>
                      {s.is_new && <Badge className="bg-green-500/20 text-green-400 text-[9px]">Nuovo</Badge>}
                    </div>
                  </CardContent>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    );
  }

  // TV Stations Views
  if (currentView.startsWith('tv-')) {
    const viewLabels = {
      'tv-alltime': { title: 'Emittenti Più Viste', subtitle: 'Di Sempre', metric: 'viewers', color: 'red' },
      'tv-weekly': { title: 'Share Settimanale', subtitle: 'Top Emittenti', metric: 'share', color: 'red' },
      'tv-daily': { title: 'Share Giornaliero', subtitle: 'Live (ogni 5 min)', metric: 'live_share', color: 'red' },
    };
    const cfg = viewLabels[currentView] || viewLabels['tv-alltime'];

    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="cineboard-tv-page">
        <div className="flex items-center gap-3 mb-4">
          <Radio className="w-7 h-7 text-red-500" />
          <div>
            <h1 className="font-['Bebas_Neue'] text-2xl">{cfg.title}</h1>
            <p className="text-xs text-gray-400">{cfg.subtitle}</p>
          </div>
          <Button variant="ghost" size="sm" className="ml-auto text-xs text-gray-500" onClick={() => navigate('/social')}>
            <ChevronLeft className="w-3 h-3 mr-1" /> CineBoard
          </Button>
        </div>

        {/* Quick tabs for TV views */}
        <div className="flex gap-1.5 mb-4 overflow-x-auto">
          {[
            { key: 'tv-alltime', label: 'Di Sempre' },
            { key: 'tv-weekly', label: 'Settimanale' },
            { key: 'tv-daily', label: 'Giornaliero' },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => navigate(`/social?view=${tab.key}`)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                currentView === tab.key
                  ? 'bg-red-500 text-white'
                  : 'bg-white/5 text-gray-400 hover:bg-white/10'
              }`}
              data-testid={`tv-tab-${tab.key}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12"><Loader2 className="w-8 h-8 text-red-400 animate-spin" /></div>
        ) : tvStationsData.length === 0 ? (
          <Card className="bg-[#111113] border-white/5">
            <CardContent className="p-6 text-center">
              <Radio className="w-10 h-10 text-gray-700 mx-auto mb-2" />
              <p className="text-gray-500 text-sm">Nessuna emittente in classifica</p>
              <p className="text-gray-600 text-xs mt-1">Crea la tua emittente TV per apparire qui!</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {tvStationsData.map((s, i) => (
              <Card
                key={s.id}
                className={`bg-[#111113] border-white/5 cursor-pointer hover:border-red-500/20 transition-all ${i < 3 ? 'border-red-500/10' : ''}`}
                onClick={() => navigate(`/tv-station/${s.id}`)}
                data-testid={`tv-rank-${s.rank}`}
              >
                <CardContent className="p-3 flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0 ${
                    i === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                    i === 1 ? 'bg-gray-400/20 text-gray-300' :
                    i === 2 ? 'bg-orange-500/20 text-orange-400' :
                    'bg-white/5 text-gray-500'
                  }`}>
                    {s.rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold truncate">{s.station_name}</p>
                    <div className="flex items-center gap-1.5 text-[10px] text-gray-500">
                      <Globe className="w-2.5 h-2.5" />
                      <span>{s.nation}</span>
                      <span>|</span>
                      <span>{s.owner_nickname}</span>
                      <span>|</span>
                      <span>{s.content_count} cont.</span>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    {currentView === 'tv-alltime' ? (
                      <>
                        <p className="text-sm font-bold text-red-400">{(s.total_viewers || 0).toLocaleString()}</p>
                        <p className="text-[9px] text-gray-500">spettatori</p>
                      </>
                    ) : currentView === 'tv-daily' ? (
                      <>
                        <p className="text-sm font-bold text-red-400">{s.live_share || s.current_share || 0}%</p>
                        <p className="text-[9px] text-gray-500">share live</p>
                      </>
                    ) : (
                      <>
                        <p className="text-sm font-bold text-red-400">{s.current_share || 0}%</p>
                        <p className="text-[9px] text-gray-500">share</p>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Default Film View

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="cineboard-page">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <Trophy className="w-8 h-8 text-yellow-500" />
        <div>
          <h1 className="font-['Bebas_Neue'] text-3xl">{t('cineboard')}</h1>
          <p className="text-xs text-gray-400">
            {language === 'it' ? 'Classifica film basata su qualità, incassi, popolarità e premi' : 'Film rankings based on quality, revenue, popularity and awards'}
          </p>
        </div>
      </div>
      
      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-4">
        <TabsList className="grid w-full grid-cols-4 bg-[#1A1A1A]">
          <TabsTrigger value="daily" className="data-[state=active]:bg-green-500 data-[state=active]:text-black text-xs sm:text-sm" data-testid="tab-daily">
            <TrendingUp className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">{t('daily')}</span>
            <span className="sm:hidden">Oggi</span>
          </TabsTrigger>
          <TabsTrigger value="weekly" className="data-[state=active]:bg-purple-500 data-[state=active]:text-white text-xs sm:text-sm" data-testid="tab-weekly">
            <BarChart3 className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">{t('weekly')}</span>
            <span className="sm:hidden">Settimana</span>
          </TabsTrigger>
          <TabsTrigger value="now_playing" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black text-xs sm:text-sm" data-testid="tab-top50">
            <Film className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">{t('nowPlaying')}</span>
            <span className="sm:hidden">Top 50</span>
          </TabsTrigger>
          <TabsTrigger value="attendance" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white text-xs sm:text-sm" data-testid="tab-attendance">
            <Users className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">{t('attendance')}</span>
            <span className="sm:hidden">Affluenza</span>
          </TabsTrigger>
        </TabsList>
      </Tabs>
      
      {/* Score Legend removed - scoring still in backend calculation */}
      
      {/* Film List - Only for now_playing and hall_of_fame tabs */}
      {activeTab !== 'attendance' && (loading ? (
        <div className="text-center py-8 text-gray-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
          {language === 'it' ? 'Caricamento classifica...' : 'Loading rankings...'}
        </div>
      ) : films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
          <Film className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <h3 className="text-lg mb-2">{t('noFilms')}</h3>
        </Card>
      ) : (
        <div className="space-y-2">
          {films.map((film, index) => (
            <Card key={film.id} className={`bg-[#1A1A1A] border-white/10 overflow-hidden ${film.rank <= 3 ? 'border-yellow-500/30' : ''}`}>
              <div className="flex">
                {/* Rank Badge */}
                <div className={`w-12 flex items-center justify-center ${getRankBadge(film.rank)} font-bold text-lg`}>
                  #{film.rank}
                </div>
                
                {/* Poster */}
                <div className="w-20 flex-shrink-0 cursor-pointer relative" onClick={() => navigate(`/films/${film.id}`)}>
                  <img src={film.poster_url ? (film.poster_url.startsWith('/') ? `${BACKEND_URL}${film.poster_url}` : film.poster_url) : `${BACKEND_URL}/api/films/${film.id}/poster`} alt={film.title} className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.style.display='none'; e.target.nextSibling.style.display='flex'; }} />
                  <div style={{display:'none'}} className="w-full h-full items-center justify-center"><FilmPoster film={film} /></div>
                  {/* Virtual Likes Badge */}
                  {(film.virtual_likes > 0) && (
                    <div className="absolute top-1 left-1 bg-black/70 rounded px-1 py-0.5 flex items-center gap-0.5">
                      <Heart className="w-2 h-2 text-pink-400 fill-pink-400" />
                      <span className="text-[8px] text-pink-300">{film.virtual_likes}</span>
                    </div>
                  )}
                </div>
                
                {/* Info */}
                <CardContent className="flex-1 p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 
                        className="font-semibold text-sm cursor-pointer hover:text-yellow-500 truncate" 
                        onClick={() => navigate(`/films/${film.id}`)}
                      >
                        {film.title}
                      </h3>
                      <p className="text-[10px] text-gray-400 truncate">
                        {film.owner?.production_house_name || 'Unknown Studio'}
                      </p>
                    </div>
                    
                    {/* IMDb-style Rating */}
                    <div className="flex items-center gap-1 bg-yellow-500/20 px-2 py-1 rounded ml-2">
                      <Star className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />
                      <span className="font-bold text-yellow-500 text-sm">{film.imdb_rating?.toFixed(1) || '0.0'}</span>
                    </div>
                  </div>
                  
                  {/* Stats Row */}
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <Badge className="bg-white/10 text-gray-300 text-[10px] h-5">{film.genre}</Badge>
                    <span className="text-[10px] text-yellow-400"><Star className="w-3 h-3 inline" /> {film.quality_score?.toFixed(0)}%</span>
                    {activeTab === 'daily' && film.daily_revenue != null ? (
                      <span className="text-[10px] text-green-400 font-medium">${((film.daily_revenue || 0) / 1000000).toFixed(2)}M oggi</span>
                    ) : activeTab === 'weekly' && film.weekly_revenue != null ? (
                      <span className="text-[10px] text-green-400 font-medium">${((film.weekly_revenue || 0) / 1000000).toFixed(2)}M sett.</span>
                    ) : (
                      <span className="text-[10px] text-green-400">${((film.total_revenue || 0) / 1000000).toFixed(1)}M</span>
                    )}
                    
                    {/* CineBoard Score */}
                    <div className="ml-auto flex items-center gap-1">
                      <span className="text-[10px] text-gray-500">{t('score')}:</span>
                      <span className={`font-bold text-sm ${film.cineboard_score >= 70 ? 'text-yellow-400' : film.cineboard_score >= 50 ? 'text-green-400' : 'text-gray-400'}`}>
                        {film.cineboard_score?.toFixed(1)}
                      </span>
                    </div>
                  </div>
                  
                  {/* Release-relative trend bars */}
                  {activeTab === 'daily' && film.hourly_trend?.length > 0 && (() => {
                    const maxRev = Math.max(...film.hourly_trend.map(x => x.revenue), 1);
                    const BAR_H = 28;
                    return (
                      <div className="mt-2 flex items-end gap-1" data-testid={`trend-daily-${film.id}`}>
                        {film.hourly_trend.map((h, i) => {
                          const px = Math.max((h.revenue / maxRev) * BAR_H, 3);
                          return (
                            <div key={i} className="flex flex-col items-center" style={{width: '14%'}}>
                              <div 
                                className="w-full rounded-t-sm bg-green-500/70 hover:bg-green-400/90 transition-colors"
                                style={{height: `${px}px`}}
                                title={`${h.hour}: $${(h.revenue/1000000).toFixed(2)}M`}
                              />
                              <span className="text-[7px] text-gray-500 mt-0.5 leading-none">{h.hour.replace('h','')}</span>
                            </div>
                          );
                        })}
                        <span className="text-[7px] text-gray-600 self-end ml-0.5 pb-0.5">{language === 'it' ? 'ore' : 'hrs'}</span>
                      </div>
                    );
                  })()}
                  {activeTab === 'weekly' && film.daily_trend?.length > 0 && (() => {
                    const maxRev = Math.max(...film.daily_trend.map(x => x.revenue), 1);
                    const BAR_H = 28;
                    return (
                      <div className="mt-2 flex items-end gap-1" data-testid={`trend-weekly-${film.id}`}>
                        {film.daily_trend.map((d, i) => {
                          const px = Math.max((d.revenue / maxRev) * BAR_H, 3);
                          return (
                            <div key={i} className="flex flex-col items-center" style={{width: '12%'}}>
                              <div 
                                className="w-full rounded-t-sm bg-purple-500/70 hover:bg-purple-400/90 transition-colors"
                                style={{height: `${px}px`}}
                                title={`${d.day}: $${(d.revenue/1000000).toFixed(2)}M`}
                              />
                              <span className="text-[7px] text-gray-500 mt-0.5 leading-none">{d.day}</span>
                            </div>
                          );
                        })}
                        <span className="text-[7px] text-gray-600 self-end ml-0.5 pb-0.5">{language === 'it' ? 'giorni' : 'days'}</span>
                      </div>
                    );
                  })()}
                  
                  {/* Action Row */}
                  <div className="flex items-center gap-2 mt-2">
                    {film.hall_of_fame && (
                      <Badge className="bg-purple-500/20 text-purple-400 text-[10px]">
                        <Trophy className="w-3 h-3 mr-1" /> Hall of Fame
                      </Badge>
                    )}
                    
                    {film.awards?.length > 0 && (
                      <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">
                        <Award className="w-3 h-3 mr-1" /> {film.awards.length}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </div>
            </Card>
          ))}
        </div>
      ))}

      {/* Attendance Tab Content */}
      {activeTab === 'attendance' && (
        loading ? (
          <div className="text-center py-8 text-gray-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
            {language === 'it' ? 'Caricamento affluenze...' : 'Loading attendance data...'}
          </div>
        ) : !attendanceData ? (
          <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
            <Users className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <h3 className="text-lg mb-2">{language === 'it' ? 'Nessun dato disponibile' : 'No data available'}</h3>
          </Card>
        ) : (
        <div className="space-y-4">
          {/* Global Stats */}
          <Card className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/30">
            <CardContent className="p-4">
              <h3 className="font-['Bebas_Neue'] text-lg mb-3 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                {language === 'it' ? 'Statistiche Globali' : 'Global Stats'}
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="text-center p-3 rounded-lg bg-black/20">
                  <p className="text-2xl font-bold text-blue-400">{attendanceData.global_stats?.total_films_in_theaters || 0}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Film in Sala' : 'Films Showing'}</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-black/20">
                  <p className="text-2xl font-bold text-green-400">{(attendanceData.global_stats?.total_cinemas_showing || 0).toLocaleString()}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Cinema Totali' : 'Total Cinemas'}</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-black/20">
                  <p className="text-2xl font-bold text-purple-400">{(attendanceData.global_stats?.total_current_attendance || 0).toLocaleString()}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Spettatori Ora' : 'Current Viewers'}</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-black/20">
                  <p className="text-2xl font-bold text-yellow-400">{attendanceData.global_stats?.avg_attendance_per_cinema || 0}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Media/Cinema' : 'Avg/Cinema'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Top 20 Now Playing */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                <Film className="w-5 h-5 text-yellow-500" />
                {language === 'it' ? 'Top 20 - Più Programmati (Ora)' : 'Top 20 - Most Screened (Now)'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {attendanceData.top_now_playing?.length === 0 ? (
                <p className="text-center text-gray-400 py-4">{language === 'it' ? 'Nessun film in programmazione' : 'No films currently showing'}</p>
              ) : (
                attendanceData.top_now_playing?.map((film, idx) => (
                  <div 
                    key={film.id} 
                    className="flex items-center gap-3 p-2 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors"
                    onClick={() => navigate(`/film/${film.id}`)}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      idx === 0 ? 'bg-yellow-500 text-black' :
                      idx === 1 ? 'bg-gray-300 text-black' :
                      idx === 2 ? 'bg-amber-600 text-white' :
                      'bg-white/10 text-gray-400'
                    }`}>
                      {film.rank}
                    </div>
                    <div className="w-10 h-14 rounded bg-gray-800 overflow-hidden flex-shrink-0">
                      <img src={film.poster_url ? (film.poster_url.startsWith('/') ? `${BACKEND_URL}${film.poster_url}` : film.poster_url) : `${BACKEND_URL}/api/films/${film.id}/poster`} alt="" className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.style.display='none'; }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate">{film.title}</p>
                      <p className="text-xs text-gray-400 truncate"><ClickableNickname userId={film.owner?.id} nickname={film.owner?.production_house_name || film.owner?.nickname} /></p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-blue-400">{film.current_cinemas}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'cinema' : 'cinemas'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-400">{film.current_attendance?.toLocaleString()}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'spettatori' : 'viewers'}</p>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Top 20 All-Time */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                <Trophy className="w-5 h-5 text-purple-500" />
                {language === 'it' ? 'Top 20 - Più Programmati (All-Time)' : 'Top 20 - Most Screened (All-Time)'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {attendanceData.top_all_time?.length === 0 ? (
                <p className="text-center text-gray-400 py-4">{language === 'it' ? 'Nessun dato storico' : 'No historical data'}</p>
              ) : (
                attendanceData.top_all_time?.map((film, idx) => (
                  <div 
                    key={film.id} 
                    className="flex items-center gap-3 p-2 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors"
                    onClick={() => navigate(`/film/${film.id}`)}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      idx === 0 ? 'bg-yellow-500 text-black' :
                      idx === 1 ? 'bg-gray-300 text-black' :
                      idx === 2 ? 'bg-amber-600 text-white' :
                      'bg-white/10 text-gray-400'
                    }`}>
                      {film.rank}
                    </div>
                    <div className="w-10 h-14 rounded bg-gray-800 overflow-hidden flex-shrink-0">
                      <img src={film.poster_url ? (film.poster_url.startsWith('/') ? `${BACKEND_URL}${film.poster_url}` : film.poster_url) : `${BACKEND_URL}/api/films/${film.id}/poster`} alt="" className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.style.display='none'; }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate">{film.title}</p>
                      <div className="flex items-center gap-2">
                        <p className="text-xs text-gray-400 truncate"><ClickableNickname userId={film.owner?.id} nickname={film.owner?.production_house_name || film.owner?.nickname} /></p>
                        <Badge className={`text-[9px] ${film.status === 'in_theaters' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                          {film.status === 'in_theaters' ? (language === 'it' ? 'In Sala' : 'Showing') : (language === 'it' ? 'Archivio' : 'Archive')}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-purple-400">{(film.total_screenings || 0).toLocaleString()}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'proiezioni' : 'screenings'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-cyan-400">{(film.cumulative_attendance || 0).toLocaleString()}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'totale spett.' : 'total viewers'}</p>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
        )
      )}
    </div>
  );
};

// Chat Page

export default CineBoard;
