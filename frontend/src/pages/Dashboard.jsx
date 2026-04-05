// CineWorld Studio's - Dashboard
// Extracted from App.js for modularity

import React, { useState, useEffect, useRef, useCallback, useMemo, useContext } from 'react';
import { useNavigate, useLocation, useSearchParams, useParams } from 'react-router-dom';
import { AuthContext, LanguageContext, PlayerPopupContext, useTranslations, API, useProductionMenu } from '../contexts';
import { useSWR, useGameStore } from '../contexts/GameStore';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400';
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { PlayerBadge, MasterpieceBadge } from '../components/PlayerBadge';
import { Progress } from '../components/ui/progress';
import { ComingSoonSection } from '../components/ComingSoonSection';
import { LaPrimaSection } from '../components/LaPrimaSection';
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding, TrendingDown, Pen, Tv, Radio
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const Dashboard = () => {
  const { user, api, refreshUser, updateUser, cachedGet } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const { setIsOpen: openProductionMenu } = useProductionMenu();
  const [stats, setStats] = useState(null);
  const [films, setFilms] = useState([]);
  const [mySeries, setMySeries] = useState([]);
  const [myAnime, setMyAnime] = useState([]);
  const [recentReleases, setRecentReleases] = useState([]);
  const [pendingFilms, setPendingFilms] = useState([]);
  const [challenges, setChallenges] = useState({ daily: [], weekly: [] });
  const [catchupData, setCatchupData] = useState(null);
  const [pendingRevenue, setPendingRevenue] = useState(null);
  const [collecting, setCollecting] = useState(false);
  const [emergingCount, setEmergingCount] = useState(0);
  const [myTVStations, setMyTVStations] = useState([]);
  const [hasEmittenteTV, setHasEmittenteTV] = useState(false);
  const [showTVPopup, setShowTVPopup] = useState(false);
  const [availableContests, setAvailableContests] = useState(0);
  const [releasePopup, setReleasePopup] = useState(null); // film to release
  const [distConfig, setDistConfig] = useState(null);
  const [selectedZone, setSelectedZone] = useState('national');
  const [selectedContinent, setSelectedContinent] = useState('europe');
  const [releasing, setReleasing] = useState(false);
  const [hasStudio, setHasStudio] = useState(false);
  const [releaseSuccess, setReleaseSuccess] = useState(null);
  // Shooting system
  const [shootingFilms, setShootingFilms] = useState([]);
  const [pipelineCount, setPipelineCount] = useState(0);
  const [seriesPipelineCount, setSeriesPipelineCount] = useState(0);
  const [animePipelineCount, setAnimePipelineCount] = useState(0);
  const [shootingPopup, setShootingPopup] = useState(null);
  const [shootingDays, setShootingDays] = useState(5);
  const [shootingConfig, setShootingConfig] = useState(null);
  const [startingShooting, setStartingShooting] = useState(false);
  const [endingShootingEarly, setEndingShootingEarly] = useState(false);
  const [showShootingDialog, setShowShootingDialog] = useState(false);
  // Collapsible financial balance
  const [financeOpen, setFinanceOpen] = useState(false);
  // Collapsible studio section
  const [studioOpen, setStudioOpen] = useState(false);
  const studioRef = useRef(null);
  const collectRef = useRef(null);
  const navigate = useNavigate();
  
  // Stats detail modal state
  const [showStatsDetail, setShowStatsDetail] = useState(false);
  const [selectedStatType, setSelectedStatType] = useState(null);
  
  const openStatDetail = (statType) => {
    setSelectedStatType(statType);
    setShowStatsDetail(true);
  };

  const StatsDetailModal = ({ isOpen, onClose, statType }) => {
    const [detailedStats, setDetailedStats] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
      if (isOpen) {
        setLoading(true);
        api.get('/stats/detailed')
          .then(res => { setDetailedStats(res.data); setLoading(false); })
          .catch(() => setLoading(false));
      }
    }, [isOpen]);
    
    if (!isOpen) return null;
    
    const lt = (key) => {
      const tr = {
        films: language === 'it' ? 'Film' : 'Films', revenue: language === 'it' ? 'Incassi' : 'Revenue',
        quality: language === 'it' ? 'Qualità' : 'Quality',
        byGenre: language === 'it' ? 'Per Genere' : 'By Genre', topFilms: language === 'it' ? 'Top Film' : 'Top Films',
        distribution: language === 'it' ? 'Distribuzione' : 'Distribution', excellent: language === 'it' ? 'Eccellente' : 'Excellent',
        good: language === 'it' ? 'Buono' : 'Good', average: language === 'it' ? 'Medio' : 'Average',
        poor: language === 'it' ? 'Scarso' : 'Poor', total: language === 'it' ? 'Totale' : 'Total',
        avgPerFilm: language === 'it' ? 'Media per Film' : 'Average per Film'
      };
      return tr[key] || key;
    };
    
    const renderContent = () => {
      if (!detailedStats) return null;
      switch(statType) {
        case 'films':

          return (<div className="space-y-4">
            <div><h4 className="text-sm font-semibold mb-2">{lt('byGenre')}</h4>
              <div className="grid grid-cols-2 gap-2">{Object.entries(detailedStats.films?.by_genre || {}).map(([genre, count]) => (
                <div key={genre} className="bg-black/30 rounded p-2 flex justify-between"><span className="text-xs text-gray-400">{genre}</span><span className="text-xs font-bold text-yellow-500">{count}</span></div>
              ))}</div></div>
            <div><h4 className="text-sm font-semibold mb-2">{lt('topFilms')} ({lt('revenue')})</h4>
              <div className="space-y-1">{(detailedStats.films?.top_by_revenue || []).map((film, i) => (
                <div key={film.id} className="bg-black/30 rounded p-2 flex justify-between items-center cursor-pointer hover:bg-black/50 transition-colors" onClick={() => { onClose(); navigate(`/films/${film.id}`); }}>
                  <span className="text-xs hover:text-yellow-500">{i + 1}. {film.title}</span><span className="text-xs text-green-500">${(film.revenue / 1000000).toFixed(2)}M</span>
                </div>))}</div></div></div>);
        case 'revenue':
          return (<div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-green-500/10 rounded p-3 text-center border border-green-500/20"><p className="text-2xl font-bold text-green-500">${((detailedStats.revenue?.total || 0) / 1000000).toFixed(2)}M</p><p className="text-xs text-gray-400">{language === 'it' ? 'Box Office Attuale' : 'Current Box Office'}</p></div>
              <div className="bg-blue-500/10 rounded p-3 text-center border border-blue-500/20"><p className="text-2xl font-bold text-blue-500">${((detailedStats.revenue?.average_per_film || 0) / 1000000).toFixed(2)}M</p><p className="text-xs text-gray-400">{lt('avgPerFilm')}</p></div>
            </div></div>);
        case 'quality':
          return (<div className="space-y-4">
            <div className="bg-blue-500/10 rounded p-4 text-center"><p className="text-3xl font-bold text-blue-500">{(detailedStats.quality?.average || 0).toFixed(1)}%</p><p className="text-sm text-gray-400">{lt('average')} {lt('quality')}</p></div>
          </div>);
        default: return <p className="text-gray-400 text-center py-8">Select a stat</p>;
      }
    };
    
    const titles = { films: language === 'it' ? 'Dettagli Film' : 'Films Details', revenue: language === 'it' ? 'Dettagli Incassi' : 'Revenue Details', quality: language === 'it' ? 'Dettagli Qualità' : 'Quality Details' };
    
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md" data-testid="stats-detail-modal">
          <DialogHeader><DialogTitle>{titles[statType] || 'Dettagli'}</DialogTitle></DialogHeader>
          {loading ? <div className="flex items-center justify-center py-12"><div className="animate-spin h-8 w-8 border-2 border-yellow-500 border-t-transparent rounded-full"></div></div> : renderContent()}
        </DialogContent>
      </Dialog>
    );
  };

  const loadPendingRevenue = async () => {
    try {
      const res = await api.get('/revenue/pending-all');
      setPendingRevenue(res.data);
    } catch (e) {
      console.error('Error loading pending revenue:', e);
    }
  };

  const handleCollectAll = async () => {
    if (!pendingRevenue?.can_collect) return;
    setCollecting(true);
    try {
      const res = await api.post('/revenue/collect-all');
      toast.success(res.data.message, { duration: 5000 });
      refreshUser();
      loadPendingRevenue();
      // Refresh stats
      const statsRes = await api.get('/statistics/my');
      setStats(statsRes.data);
    } catch (e) {
      toast.error('Errore nella riscossione');
    } finally {
      setCollecting(false);
    }
  };

  // SWR: show cached data instantly, revalidate in background
  const { data: batchData, mutate: refreshBatch } = useSWR('/dashboard/batch');
  const { data: pvpStats } = useSWR('/pvp-cinema/stats');
  const gameStore = useGameStore();

  // Apply batch data to local states when it arrives/updates
  useEffect(() => {
    if (!batchData) return;
    const d = batchData;
    setStats(d.stats);
    setFilms(Array.from(new Map((d.featured_films || []).map(f => [f.id, f])).values()));
    setMySeries(d.my_series || []);
    setMyAnime(d.my_anime || []);
    setRecentReleases(d.recent_releases || []);
    setChallenges(d.challenges || []);
    setPendingRevenue(d.pending_revenue || {});
    setPendingFilms(d.pending_films || []);
    setEmergingCount(d.emerging_count || 0);
    setHasStudio(d.has_studio || false);
    setShootingFilms(d.shooting_films || []);
    setPipelineCount(d.pipeline_total || 0);
    setSeriesPipelineCount(d.series_pipeline_total || 0);
    setAnimePipelineCount(d.anime_pipeline_total || 0);
  }, [batchData]);

  useEffect(() => {
    const fetchExtra = async () => {
      try {
        // Process offline catch-up
        const catchupRes = await api.post('/catchup/process');
        if (catchupRes.data.catchup_revenue > 0) {
          setCatchupData(catchupRes.data);
          toast.success(
            language === 'it' 
              ? `Bentornato! Recuperati $${catchupRes.data.catchup_revenue.toLocaleString()} per ${catchupRes.data.hours_missed} ore offline!`
              : `Welcome back! Collected $${catchupRes.data.catchup_revenue.toLocaleString()} for ${catchupRes.data.hours_missed} hours offline!`,
            { duration: 6000 }
          );
          refreshUser();
        }
        // Load TV stations
        try {
          const tvRes = await api.get('/tv-stations/my');
          setMyTVStations(tvRes.data.stations || []);
          setHasEmittenteTV(tvRes.data.has_emittente_tv || false);
        } catch { setHasEmittenteTV(false); }
        // Contests
        try {
          const contestsRes = await api.get('/cinepass/contests');
          const available = (contestsRes.data?.contests || []).filter(c => c.status === 'available' && !c.completed).length;
          setAvailableContests(available);
        } catch {}
        // Shooting config
        try {
          const configRes = await api.get('/films/shooting/config');
          setShootingConfig(configRes.data);
        } catch {}
      } catch (err) {
        console.error(err);
      }
    };
    fetchExtra();
    
    // Setup heartbeat to track activity (every 5 minutes)
    const heartbeatInterval = setInterval(() => {
      api.post('/activity/heartbeat').catch(() => {});
    }, 5 * 60 * 1000);
    
    return () => {
      clearInterval(heartbeatInterval);
    };
  }, [api]);

  // Revenue polling only when studio section is open
  useEffect(() => {
    if (!studioOpen) return;
    loadPendingRevenue();
    const revenueInterval = setInterval(loadPendingRevenue, 60000);
    return () => clearInterval(revenueInterval);
  }, [studioOpen]);

  // Velion event: open studio section and scroll to collect
  useEffect(() => {
    const handler = () => {
      setStudioOpen(true);
      setTimeout(() => {
        collectRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 350);
    };
    window.addEventListener('velion-open-studio', handler);
    return () => window.removeEventListener('velion-open-studio', handler);
  }, []);

  // Velion: notify about pending revenue when studio closed
  useEffect(() => {
    if (studioOpen || !pendingRevenue?.can_collect) return;
    const timer = setTimeout(() => {
      window.dispatchEvent(new CustomEvent('velion-revenue-notify', {
        detail: { message: language === 'it' ? 'Hai incassi pronti da riscuotere! Tocca per aprire.' : 'You have revenue ready to collect! Tap to open.' }
      }));
    }, 5000);
    return () => clearTimeout(timer);
  }, [pendingRevenue?.can_collect, studioOpen, language]);

  const openReleasePopup = async (film) => {
    setReleasePopup(film);
    setSelectedZone('national');
    setSelectedContinent('europe');
    try {
      const res = await api.get('/distribution/config');
      setDistConfig(res.data);
    } catch {}
  };

  const handleRelease = async () => {
    if (!releasePopup || !distConfig) return;
    setReleasing(true);
    try {
      let filmId = releasePopup.id;
      let releaseEvents = null;

      // For pending_release: first call film-pipeline release to create the films entry + get events
      if (releasePopup.status === 'pending_release') {
        const pipelineRes = await api.post(`/film-pipeline/${releasePopup.id}/release`);
        if (pipelineRes.data.success) {
          filmId = pipelineRes.data.film_id; // new film_id in films collection
          releaseEvents = pipelineRes.data; // events, critics, etc.
        }
      }

      // Now do distribution release on the films collection entry
      const res = await api.post(`/films/${filmId}/release`, {
        distribution_zone: selectedZone,
        distribution_continent: selectedZone === 'continental' ? selectedContinent : null
      });
      if (res.data.success) {
        const filmTitle = releasePopup.title;
        const openingRevenue = res.data.opening_day_revenue;
        const zoneName = selectedZone === 'national' ? 'Nazionale' : selectedZone === 'continental' ? 'Continentale' : 'Mondiale';
        setPendingFilms(prev => prev.filter(f => f.id !== releasePopup.id));
        setReleasePopup(null);
        setReleaseSuccess({
          title: filmTitle,
          revenue: openingRevenue,
          zone: zoneName,
          poster: releasePopup.poster_url,
          events: releaseEvents?.events,
          quality_score: releaseEvents?.quality_score,
          imdb_rating: releaseEvents?.imdb_rating,
          critics: releaseEvents?.critics,
          tier: releaseEvents?.tier,
        });
        refreshUser().catch(() => {});
        try {
          const filmsRes = await api.get('/films/my/featured?limit=9');
          setFilms(Array.from(new Map(filmsRes.data.map(f => [f.id, f])).values()));
        } catch {}
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nel rilascio');
    } finally {
      setReleasing(false);
    }
  };

  const getZoneCost = () => {
    if (!distConfig) return { funds: 0, cinepass: 0 };
    const zone = distConfig.zones[selectedZone];
    if (!zone) return { funds: 0, cinepass: 0 };
    const qf = 1.0 + ((releasePopup?.quality_score || 50) - 50) / 200;
    const isDirectRelease = releasePopup?.status === 'pending_release';
    const fundsCost = isDirectRelease ? Math.round(zone.base_cost * qf * 0.7) : Math.round(zone.base_cost * qf);
    const cpCost = isDirectRelease ? Math.max(1, zone.cinepass_cost - 1) : zone.cinepass_cost;
    return { funds: fundsCost, cinepass: cpCost };
  };

  const getShootingCost = (film, days) => {
    const budget = film?.total_budget || film?.production_cost || 500000;
    return Math.round(budget * 0.15 * days);
  };

  const handleStartShooting = async () => {
    if (!shootingPopup) return;
    setStartingShooting(true);
    try {
      const res = await api.post(`/films/${shootingPopup.id}/start-shooting`, { shooting_days: shootingDays });
      if (res.data.success) {
        toast.success(res.data.message);
        setPendingFilms(prev => prev.filter(f => f.id !== shootingPopup.id));
        setShootingPopup(null);
        // Refresh shooting films
        const shootRes = await api.get('/films/shooting');
        setShootingFilms(shootRes.data?.films || []);
        refreshUser().catch(() => {});
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally { setStartingShooting(false); }
  };

  const handleEndShootingEarly = async (filmId) => {
    setEndingShootingEarly(true);
    try {
      const res = await api.post(`/films/${filmId}/end-shooting-early`);
      if (res.data.success) {
        toast.success(res.data.message);
        setShootingFilms(prev => prev.filter(f => f.id !== filmId));
        // Refresh pending
        const pendRes = await api.get('/films/pending');
        setPendingFilms(pendRes.data || []);
        refreshUser().catch(() => {});
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally { setEndingShootingEarly(false); }
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="dashboard">
      {/* Studio Header - Collapsible trigger */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-4" ref={studioRef}>
        <button
          className="w-full text-left flex items-center justify-between group"
          onClick={() => setStudioOpen(prev => !prev)}
          data-testid="studio-toggle-btn"
        >
          <div>
            <h1 className="font-['Bebas_Neue'] text-3xl md:text-4xl mb-1">
              {t('welcome')}, <PlayerBadge badge={user?.badge} badgeExpiry={user?.badge_expiry} badges={user?.badges} size="md" /><span className="text-yellow-500">{user?.nickname || user?.production_house_name}</span>
            </h1>
            <div className="flex items-center gap-2">
              <p className="text-gray-400 text-sm">{user?.production_house_name}</p>
              {!studioOpen && pendingRevenue?.can_collect && (
                <span className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse" data-testid="studio-red-dot" />
              )}
            </div>
          </div>
          <motion.div animate={{ rotate: studioOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
            <ChevronDown className="w-5 h-5 text-gray-500 group-hover:text-white transition-colors" />
          </motion.div>
        </button>
      </motion.div>

      {/* Collapsible Studio Data */}
      <AnimatePresence initial={false}>
        {studioOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
            data-testid="studio-section"
          >
            <div className="grid grid-cols-3 gap-2 mb-4">
              {[
                { label: 'Films', value: stats?.total_films || 0, icon: Film, color: 'yellow', statType: 'films' },
                { label: 'Incassi', value: `$${((stats?.total_revenue || 0) / 1000000).toFixed(1)}M`, icon: DollarSign, color: 'green', statType: 'revenue' },
                { label: 'Qualità', value: `${(stats?.average_quality || 0).toFixed(0)}%`, icon: Star, color: 'blue', statType: 'quality' }
              ].map((stat, i) => (
                <Card 
                  key={stat.label} 
                  className="bg-[#1A1A1A] border-white/5 cursor-pointer hover:border-white/20 transition-colors"
                  onClick={() => openStatDetail(stat.statType)}
                  data-testid={`stat-card-${stat.statType}`}
                >
                  <CardContent className="p-2 sm:p-2.5 flex items-center gap-2">
                    <stat.icon className={`w-5 h-5 text-${stat.color}-500`} />
                    <div>
                      <p className="text-lg font-bold">{stat.value}</p>
                      <p className="text-xs text-gray-400">{stat.label}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-500 ml-auto" />
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Collect All Revenue Card */}
            {pendingRevenue && (
              <Card ref={collectRef} className={`mb-4 border ${pendingRevenue.can_collect ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/10 border-green-500/30' : 'bg-[#1A1A1A] border-white/5'}`} data-testid="collect-revenue-card">
                <CardContent className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${pendingRevenue.can_collect ? 'bg-green-500' : 'bg-gray-600'}`}>
                        <Wallet className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="font-['Bebas_Neue'] text-lg">
                          {language === 'it' ? 'INCASSI DA RISCUOTERE' : 'PENDING REVENUE'}
                        </h3>
                        <div className="flex items-center gap-4 text-xs text-gray-400">
                          <span>Film: ${(pendingRevenue.film_pending || 0).toLocaleString()}</span>
                          <span>Infra: ${(pendingRevenue.infra_pending || 0).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-xl font-bold ${pendingRevenue.can_collect ? 'text-green-400' : 'text-gray-500'}`}>
                        ${(pendingRevenue.total_pending || 0).toLocaleString()}
                      </p>
                      <Button 
                        size="sm"
                        disabled={!pendingRevenue.can_collect || collecting}
                        onClick={handleCollectAll}
                        className={pendingRevenue.can_collect 
                          ? 'bg-green-500 hover:bg-green-600 text-white' 
                          : 'bg-gray-700 text-gray-400'
                        }
                        data-testid="collect-all-btn"
                      >
                        {collecting ? '...' : (language === 'it' ? 'Riscuoti Tutto' : 'Collect All')}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Financial Overview Card - inside studio */}
            {stats && (
              <Card className="mb-4 bg-[#1A1A1A] border-white/5" data-testid="financial-overview-card">
                <CardContent className="p-3">
                  <button
                    className="w-full flex items-center justify-between"
                    onClick={() => setFinanceOpen(prev => !prev)}
                    data-testid="financial-toggle-btn"
                  >
                    <h3 className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                      <BarChart3 className="w-4 h-4 text-cyan-400" />
                      {language === 'it' ? 'BILANCIO FINANZIARIO' : 'FINANCIAL OVERVIEW'}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-bold ${(stats.profit_loss || 0) >= 0 ? 'text-emerald-400' : 'text-orange-400'}`}>
                        {(stats.profit_loss || 0) >= 0 ? '+' : ''}${((stats.profit_loss || 0) / 1000000).toFixed(2)}M
                      </span>
                      <motion.div animate={{ rotate: financeOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      </motion.div>
                    </div>
                  </button>
                  <AnimatePresence initial={false}>
                    {financeOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: 'easeInOut' }}
                        className="overflow-hidden"
                      >
                        <div className="grid grid-cols-3 gap-3 mt-3">
                          <div className="text-center p-2 bg-red-500/10 rounded-lg border border-red-500/20">
                            <p className="text-xs text-gray-400 mb-1">{language === 'it' ? 'Speso' : 'Spent'}</p>
                            <p className="font-bold text-red-400">${((stats.total_spent || 0) / 1000000).toFixed(2)}M</p>
                            <div className="text-[10px] text-gray-500 mt-1">
                              <div>Film: ${((stats.total_film_costs || 0) / 1000000).toFixed(1)}M</div>
                              <div>Infra: ${((stats.total_infra_costs || 0) / 1000000).toFixed(1)}M</div>
                            </div>
                          </div>
                          <div className="text-center p-2 bg-green-500/10 rounded-lg border border-green-500/20">
                            <p className="text-xs text-gray-400 mb-1">{language === 'it' ? 'Guadagnato' : 'Earned'}</p>
                            <p className="font-bold text-green-400">${((stats.total_earned || 0) / 1000000).toFixed(2)}M</p>
                            <div className="text-[10px] text-gray-500 mt-1">
                              <div>Film: ${((stats.total_revenue || 0) / 1000000).toFixed(1)}M</div>
                              <div>Infra: ${((stats.total_infra_revenue || 0) / 1000000).toFixed(1)}M</div>
                            </div>
                          </div>
                          <div className={`text-center p-2 rounded-lg border ${(stats.profit_loss || 0) >= 0 ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-orange-500/10 border-orange-500/20'}`}>
                            <p className="text-xs text-gray-400 mb-1">{language === 'it' ? 'Profitto/Perdita' : 'Profit/Loss'}</p>
                            <p className={`font-bold ${(stats.profit_loss || 0) >= 0 ? 'text-emerald-400' : 'text-orange-400'}`}>
                              {(stats.profit_loss || 0) >= 0 ? '+' : ''}${((stats.profit_loss || 0) / 1000000).toFixed(2)}M
                            </p>
                            <div className="text-[10px] text-gray-500 mt-1 flex items-center justify-center gap-1">
                              {(stats.profit_loss || 0) >= 0 ? (
                                <><TrendingUp className="w-3 h-3 text-emerald-400" /> {language === 'it' ? 'In Profitto' : 'Profitable'}</>
                              ) : (
                                <><TrendingDown className="w-3 h-3 text-orange-400" /> {language === 'it' ? 'In Perdita' : 'In Loss'}</>
                              )}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            )}

            {/* Social/Char scores */}
            <div className="grid grid-cols-2 gap-2 mb-4">
              {[
                { label: 'Social', value: (stats?.interaction_score || 50).toFixed(0), icon: Users, color: 'blue' },
                { label: 'Char', value: (stats?.character_score || 50).toFixed(0), icon: Star, color: 'yellow' }
              ].map(s => (
                <Card key={s.label} className="bg-[#1A1A1A] border-white/5">
                  <CardContent className="p-2 text-center">
                    <s.icon className={`w-4 h-4 mx-auto mb-1 text-${s.color}-500`} />
                    <p className="text-base font-bold">{s.value}</p>
                    <p className="text-xs text-gray-400">{s.label}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* La Prima - Live Premiere Events */}
      <div className="mb-4" data-testid="dashboard-la-prima">
        <LaPrimaSection compact />
      </div>

      {/* Prossimamente - Coming Soon Section */}
      <div className="mb-4" data-testid="dashboard-coming-soon">
        <ComingSoonSection compact />
      </div>

      {/* Ultimi Aggiornamenti - Recent releases from all players */}
      {recentReleases.length > 0 && (
        <Card className="mb-4 bg-gradient-to-r from-purple-500/10 to-pink-500/5 border border-purple-500/20" data-testid="recent-releases-section">
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                {language === 'it' ? 'ULTIMI AGGIORNAMENTI' : 'LATEST RELEASES'}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => navigate('/social')} className="h-6 text-[10px] text-purple-400 hover:text-purple-300 px-2">
                CineBoard <ChevronRight className="w-3 h-3 ml-0.5" />
              </Button>
            </div>
            <div className="grid grid-cols-5 gap-1.5">
              {recentReleases.slice(0, 5).map(film => (
                <div key={film.id} className="cursor-pointer group" onClick={() => navigate(`/films/${film.id}`)} data-testid={`recent-release-${film.id}`}>
                  <div className="aspect-[2/3] relative rounded-lg overflow-hidden">
                    <MasterpieceBadge isMasterpiece={film.is_masterpiece} size="xs" />
                    <img src={posterSrc(film.poster_url)} alt={film.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                    {(film.virtual_likes > 0) && (
                      <div className="absolute top-0.5 left-0.5 bg-black/70 rounded px-0.5 py-0.5 flex items-center gap-0.5">
                        <Heart className="w-1.5 h-1.5 text-pink-400 fill-pink-400" />
                        <span className="text-[6px] text-pink-300">{film.virtual_likes}</span>
                      </div>
                    )}
                  </div>
                  <p className="text-[7px] font-semibold truncate mt-0.5">{film.title}</p>
                  <p className="text-[6px] text-gray-500 truncate"><PlayerBadge badge={film.producer_badge} badgeExpiry={film.producer_badge_expiry} badges={film.producer_badges} size="xs" />{film.producer_nickname}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Shooting Dialog - opens from CIAK! button */}
      <Dialog open={showShootingDialog} onOpenChange={setShowShootingDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <Clapperboard className="w-5 h-5 text-red-400" />
              CIAK, SI GIRA!
              {shootingFilms.length > 0 && <Badge className="bg-red-500 text-white text-xs">{shootingFilms.length}</Badge>}
            </DialogTitle>
          </DialogHeader>
          {shootingFilms.length > 0 ? (
            <div className="space-y-2">
              {shootingFilms.map(sf => {
                const progress = sf.shooting_days > 0 ? (sf.shooting_days_completed / sf.shooting_days) * 100 : 0;
                const lastEvent = sf.shooting_events?.[sf.shooting_events.length - 1];
                return (
                  <div key={sf.id} className="bg-black/30 rounded-lg p-2 border border-white/5" data-testid={`shooting-dialog-film-${sf.id}`}>
                    <div className="flex items-center gap-2 mb-1.5">
                      {sf.poster_url && <img src={posterSrc(sf.poster_url)} alt="" className="w-8 h-12 rounded object-cover" loading="lazy" />}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold truncate">{sf.title}</p>
                        <p className="text-[10px] text-gray-500">Giorno {sf.shooting_days_completed}/{sf.shooting_days} | Bonus: +{sf.shooting_bonus}%</p>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-6 text-[10px] px-2 border-red-500/30 text-red-300 hover:bg-red-500/10"
                        onClick={() => handleEndShootingEarly(sf.id)}
                        disabled={endingShootingEarly}
                        data-testid={`end-early-dialog-${sf.id}`}
                      >
                        {endingShootingEarly ? '...' : `Chiudi (${sf.early_end_cinepass_cost} CP)`}
                      </Button>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-1.5 mb-1">
                      <div className="bg-gradient-to-r from-red-500 to-amber-500 h-1.5 rounded-full transition-all" style={{width: `${progress}%`}} />
                    </div>
                    {lastEvent && (
                      <p className="text-[9px] text-gray-400">
                        Ultimo evento: <span className={lastEvent.bonus > 0 ? 'text-green-400' : lastEvent.bonus < 0 ? 'text-red-400' : 'text-gray-400'}>
                          {lastEvent.name} ({lastEvent.bonus > 0 ? '+' : ''}{lastEvent.bonus}%)
                        </span>
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-6">
              <Clapperboard className="w-8 h-8 text-gray-600 mx-auto mb-2" />
              <p className="text-gray-500 text-sm">Nessun film in riprese.</p>
              <p className="text-gray-600 text-xs mt-1">Inizia le riprese dal popup di distribuzione!</p>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Release Film Popup */}
      <Dialog open={!!releasePopup} onOpenChange={() => setReleasePopup(null)}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <Globe className="w-5 h-5 text-amber-400" />
              {language === 'it' ? 'DISTRIBUZIONE FILM' : 'FILM DISTRIBUTION'}
            </DialogTitle>
            <DialogDescription className="text-gray-400 text-xs">
              {language === 'it' ? 'Scegli dove far uscire il tuo film' : 'Choose where to release your film'}
            </DialogDescription>
          </DialogHeader>
          
          {releasePopup && (
            <div className="space-y-4">
              {/* Film mini card */}
              <div className="flex items-center gap-3 bg-black/30 rounded-lg p-3 border border-white/5">
                <img
                  src={posterSrc(releasePopup.poster_url)}
                  alt={releasePopup.title}
                  className="w-12 h-16 object-cover rounded"
                />
                <div>
                  <p className="font-semibold text-sm">{releasePopup.title}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Qualità' : 'Quality'}: {(releasePopup.quality_score || 0).toFixed(0)}%</p>
                  <p className="text-[10px] text-gray-500">{releasePopup.genre}</p>
                </div>
              </div>

              {/* Distribution zone selection */}
              <div>
                <Label className="text-xs mb-2 block">{language === 'it' ? 'Zona di distribuzione' : 'Distribution Zone'}</Label>
                <RadioGroup value={selectedZone} onValueChange={setSelectedZone} className="space-y-2">
                  {distConfig && Object.entries(distConfig.zones).map(([key, zone]) => {
                    const cost = key === selectedZone ? getZoneCost() : { funds: Math.round(zone.base_cost * (1.0 + ((releasePopup?.quality_score || 50) - 50) / 200)), cinepass: zone.cinepass_cost };
                    return (
                      <div key={key} className={`flex items-center gap-3 p-2 rounded-lg border transition-colors cursor-pointer ${selectedZone === key ? 'border-amber-500/50 bg-amber-500/10' : 'border-white/5 bg-black/20 hover:border-white/15'}`}
                        onClick={() => setSelectedZone(key)}
                      >
                        <RadioGroupItem value={key} id={key} />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            {key === 'national' && <MapPin className="w-3 h-3 text-green-400" />}
                            {key === 'continental' && <Globe className="w-3 h-3 text-blue-400" />}
                            {key === 'world' && <Globe className="w-3 h-3 text-purple-400" />}
                            <span className="text-sm font-medium">{zone.name}</span>
                          </div>
                          <p className="text-[10px] text-gray-500">
                            {key === 'national' && distConfig?.countries?.[distConfig.studio_country]}
                            {key === 'continental' && zone.description}
                            {key === 'world' && zone.description}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-yellow-400">${cost.funds.toLocaleString()}</p>
                          <p className="text-[10px] text-cyan-400">{cost.cinepass} CinePass</p>
                        </div>
                      </div>
                    );
                  })}
                </RadioGroup>
              </div>

              {/* Continent selector (only if continental) */}
              {selectedZone === 'continental' && distConfig && (
                <div>
                  <Label className="text-xs mb-1 block">{language === 'it' ? 'Continente' : 'Continent'}</Label>
                  <Select value={selectedContinent} onValueChange={setSelectedContinent}>
                    <SelectTrigger className="bg-black/30 border-white/10 h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#1A1A1A] border-white/10">
                      {Object.entries(distConfig.continents).map(([key, name]) => (
                        <SelectItem key={key} value={key} className="text-xs">{name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Revenue preview */}
              {releasePopup?.status === 'pending_release' && (
                <div className="bg-orange-500/10 rounded-lg p-2 border border-orange-500/20">
                  <p className="text-[10px] text-orange-400 font-medium mb-1">Rilascio diretto: costo -30% ma qualità capped a 5.8 IMDb e incassi ridotti</p>
                </div>
              )}
              {releasePopup?.status === 'ready_to_release' && (
                <div className="bg-green-500/10 rounded-lg p-2 border border-green-500/20">
                  <p className="text-[10px] text-green-400 font-medium mb-1">Film pronto dopo le riprese! Bonus qualità applicato: +{releasePopup.shooting_bonus || 0}%</p>
                </div>
              )}
              <div className="bg-green-500/10 rounded-lg p-2 border border-green-500/20">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="w-3 h-3 text-green-400" />
                  <span className="text-xs font-medium text-green-400">{language === 'it' ? 'Stima incasso giorno 1' : 'Est. Day 1 revenue'}</span>
                </div>
                <p className="text-lg font-bold text-green-400">
                  ${((releasePopup.opening_day_revenue || 0) * (distConfig?.zones?.[selectedZone]?.revenue_multiplier || 1)).toLocaleString(undefined, {maximumFractionDigits: 0})}
                </p>
              </div>

              {/* Cost summary */}
              <div className="flex items-center justify-between bg-black/30 rounded-lg p-2 border border-white/5">
                <span className="text-xs text-gray-400">{language === 'it' ? 'Costo totale' : 'Total cost'}</span>
                <div className="text-right">
                  <span className="text-sm font-bold text-yellow-400">${getZoneCost().funds.toLocaleString()}</span>
                  <span className="text-xs text-cyan-400 ml-2">+ {getZoneCost().cinepass} CP</span>
                </div>
              </div>
            </div>
          )}

          {/* Studio button - only if user owns production studio */}
          {hasStudio && releasePopup && releasePopup.status === 'pending_release' && (
            <Button
              variant="outline"
              size="sm"
              className="w-full border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/10 hover:text-cyan-200"
              onClick={() => { setReleasePopup(null); navigate('/infrastructure'); }}
              data-testid="go-to-studio-btn"
            >
              <Building className="w-4 h-4 mr-2" />
              {language === 'it' ? 'Porta in Studio di Produzione' : 'Take to Production Studio'}
            </Button>
          )}

          {/* Start Shooting option - only for pending_release films */}
          {releasePopup && releasePopup.status === 'pending_release' && (
            <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 space-y-2" data-testid="shooting-option">
              <div className="flex items-center gap-2">
                <Clapperboard className="w-4 h-4 text-red-400" />
                <span className="text-sm font-semibold text-red-300">Inizia le Riprese</span>
              </div>
              <p className="text-[10px] text-gray-400">Gira il film per migliorarne la qualità. Più giorni = più bonus!</p>
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-400 shrink-0">Giorni:</label>
                <input
                  type="range" min="1" max="10" value={shootingDays}
                  onChange={(e) => setShootingDays(parseInt(e.target.value))}
                  className="flex-1 h-1.5 accent-red-500"
                  data-testid="shooting-days-slider"
                />
                <span className="text-sm font-bold text-white w-6 text-center">{shootingDays}</span>
              </div>
              <div className="grid grid-cols-3 gap-1 text-center text-[10px]">
                <div className="bg-black/30 rounded p-1">
                  <p className="text-gray-500">Bonus</p>
                  <p className="text-green-400 font-bold">+{shootingConfig?.bonus_curve?.[shootingDays] || (shootingDays * 4)}%</p>
                </div>
                <div className="bg-black/30 rounded p-1">
                  <p className="text-gray-500">Costo</p>
                  <p className="text-yellow-400 font-bold">${getShootingCost(releasePopup, shootingDays).toLocaleString()}</p>
                </div>
                <div className="bg-black/30 rounded p-1">
                  <p className="text-gray-500">Durata</p>
                  <p className="text-white font-bold">{shootingDays}g</p>
                </div>
              </div>
              <Button
                size="sm"
                className="w-full bg-red-500/20 text-red-300 hover:bg-red-500/30"
                onClick={() => { 
                  const dirImg = Math.random() < 0.5 ? '/images/shooting/director_female.jpeg' : '/images/shooting/director_male.jpeg';
                  setShootingPopup({...releasePopup, _directorImg: dirImg}); 
                  setReleasePopup(null); 
                }}
                data-testid="start-shooting-from-release"
              >
                <Clapperboard className="w-4 h-4 mr-2" /> Inizia le Riprese ({shootingDays} giorni)
              </Button>
            </div>
          )}

          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setReleasePopup(null)} className="border-white/10">
              {language === 'it' ? 'Annulla' : 'Cancel'}
            </Button>
            <Button
              size="sm"
              className="bg-amber-500 hover:bg-amber-600 text-black font-bold"
              onClick={handleRelease}
              disabled={releasing}
              data-testid="confirm-release-btn"
            >
              {releasing ? <Loader2 className="w-4 h-4 animate-spin" /> : (language === 'it' ? 'Rilascia nelle Sale' : 'Release to Theaters')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Release Success Celebration Dialog */}
      <Dialog open={!!releaseSuccess} onOpenChange={(open) => { if (!open) setReleaseSuccess(null); }}>
        <DialogContent className="bg-[#0a0a0a] border-amber-500/30 max-w-sm p-0 overflow-hidden">
          <div className="relative">
            <img src="https://customer-assets.emergentagent.com/job_0f5ad56a-c26f-4f77-9bc6-853ae85e3ca2/artifacts/69t544vn_IMG_0554.jpeg" alt="CineWorld Cinema" className="w-full h-44 object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-transparent to-transparent" />
            <div className="absolute bottom-2 left-3 right-3">
              <p className="text-amber-400 font-['Bebas_Neue'] text-2xl leading-tight">IN SALA ORA!</p>
            </div>
          </div>
          {releaseSuccess && (
            <div className="px-4 pb-4 space-y-3">
              <div className="flex items-center gap-3">
                {releaseSuccess.poster && <img src={releaseSuccess.poster} alt="" className="w-12 h-16 rounded object-cover border border-white/10" />}
                <div>
                  <p className="font-bold text-base">{releaseSuccess.title}</p>
                  <p className="text-xs text-amber-400">Distribuzione {releaseSuccess.zone}</p>
                </div>
              </div>
              {/* Quality + Rating */}
              {(releaseSuccess.quality_score || releaseSuccess.imdb_rating) && (
                <div className="flex gap-2">
                  {releaseSuccess.quality_score && (
                    <div className="flex-1 bg-blue-500/10 border border-blue-500/20 rounded-lg p-2 text-center">
                      <p className="text-[10px] text-gray-400">Qualita</p>
                      <p className="text-lg font-bold text-blue-400">{releaseSuccess.quality_score.toFixed(0)}%</p>
                    </div>
                  )}
                  {releaseSuccess.imdb_rating && (
                    <div className="flex-1 bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-2 text-center">
                      <p className="text-[10px] text-gray-400">IMDB</p>
                      <p className="text-lg font-bold text-yellow-400">{releaseSuccess.imdb_rating.toFixed(1)}</p>
                    </div>
                  )}
                  {releaseSuccess.tier && (
                    <div className="flex-1 bg-purple-500/10 border border-purple-500/20 rounded-lg p-2 text-center">
                      <p className="text-[10px] text-gray-400">Tier</p>
                      <p className="text-lg font-bold text-purple-400">{releaseSuccess.tier}</p>
                    </div>
                  )}
                </div>
              )}
              {/* Events */}
              {releaseSuccess.events?.length > 0 && (
                <div className="space-y-1.5">
                  {releaseSuccess.events.map((ev, i) => (
                    <div key={i} className="bg-white/5 rounded-lg p-2 flex items-center gap-2">
                      <Sparkles className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                      <div>
                        <p className="text-[11px] font-semibold">{ev.headline}</p>
                        {ev.quality_impact && <p className="text-[9px] text-green-400">+{ev.quality_impact} qualita</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {/* Critics */}
              {releaseSuccess.critics?.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] text-gray-500 uppercase">Recensioni</p>
                  {releaseSuccess.critics.slice(0, 2).map((c, i) => (
                    <div key={i} className="bg-white/5 rounded p-1.5 text-[10px]">
                      <span className="text-gray-400">{c.outlet}:</span> <span className={c.score >= 7 ? 'text-green-400' : c.score >= 5 ? 'text-yellow-400' : 'text-red-400'}>{c.score}/10</span>
                    </div>
                  ))}
                </div>
              )}
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 text-center">
                <p className="text-[10px] text-gray-400 mb-0.5">Incasso Giorno 1</p>
                <p className="text-2xl font-bold text-green-400">${releaseSuccess.revenue?.toLocaleString()}</p>
              </div>
              <Button className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold" onClick={() => setReleaseSuccess(null)} data-testid="close-release-success">
                Fantastico!
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Shooting Confirmation Dialog */}
      <Dialog open={!!shootingPopup} onOpenChange={(open) => { if (!open) setShootingPopup(null); }}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-sm">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <Clapperboard className="w-5 h-5 text-red-400" />
              CIAK, SI GIRA!
            </DialogTitle>
          </DialogHeader>
          {shootingPopup && (
            <div className="space-y-3">
              {/* Random director image */}
              <div className="relative rounded-lg overflow-hidden">
                <img 
                  src={shootingPopup._directorImg || '/images/shooting/director_female.jpeg'} 
                  alt="Director on set" 
                  className="w-full h-40 object-cover rounded-lg"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                <div className="absolute bottom-2 left-3 right-3">
                  <p className="font-['Bebas_Neue'] text-lg text-white drop-shadow-lg">{shootingPopup.title}</p>
                  <p className="text-xs text-gray-300">Qualità: {(shootingPopup.quality_score || 0).toFixed(0)}%</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-400 shrink-0">Giorni di riprese:</label>
                <input type="range" min="1" max="10" value={shootingDays} onChange={(e) => setShootingDays(parseInt(e.target.value))} className="flex-1 h-1.5 accent-red-500" data-testid="shooting-confirm-slider" />
                <span className="text-lg font-bold text-white w-6 text-center">{shootingDays}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-center">
                <div className="bg-green-500/10 rounded-lg p-2 border border-green-500/20">
                  <p className="text-[10px] text-gray-400">Bonus qualità</p>
                  <p className="text-lg font-bold text-green-400">+{shootingConfig?.bonus_curve?.[shootingDays] || (shootingDays * 4)}%</p>
                </div>
                <div className="bg-yellow-500/10 rounded-lg p-2 border border-yellow-500/20">
                  <p className="text-[10px] text-gray-400">Costo riprese</p>
                  <p className="text-lg font-bold text-yellow-400">${getShootingCost(shootingPopup, shootingDays).toLocaleString()}</p>
                </div>
              </div>
              <p className="text-[10px] text-gray-500 text-center">
                Ogni giorno ci saranno eventi casuali che influenzano il bonus: giornate perfette, ritardi meteo, improvvisazioni geniali...
              </p>
            </div>
          )}
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setShootingPopup(null)} className="border-white/10">Annulla</Button>
            <Button size="sm" className="bg-red-500 hover:bg-red-600 text-white font-bold" onClick={handleStartShooting} disabled={startingShooting} data-testid="confirm-shooting-btn">
              {startingShooting ? <Loader2 className="w-4 h-4 animate-spin" /> : `Inizia Riprese (${shootingDays}g)`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid grid-cols-2 md:grid-cols-6 gap-2 sm:gap-3 mb-4">
        {/* PRODUCI! - Double width */}
        <Card className="col-span-2 md:col-span-2 bg-gradient-to-br from-yellow-500/30 to-yellow-600/10 border-yellow-500/30 cursor-pointer relative" onClick={() => openProductionMenu(true)} data-testid="produci-card">
          <CardContent className="p-2 sm:p-3 flex items-center gap-3">
            <div className="p-2 sm:p-2.5 bg-yellow-500 rounded-lg"><Clapperboard className="w-5 h-5 sm:w-6 sm:h-6 text-black" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg sm:text-xl">{language === 'it' ? 'Produci!' : 'Produce!'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{language === 'it' ? 'Nuova produzione' : 'New production'}</p></div>
            {(pipelineCount + seriesPipelineCount + animePipelineCount) > 0 && <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 rounded-full text-[10px] font-bold flex items-center justify-center animate-pulse">{pipelineCount + seriesPipelineCount + animePipelineCount}</span>}
          </CardContent>
        </Card>
        {/* MERCATO */}
        <Card className="bg-gradient-to-br from-orange-500/20 to-orange-600/5 border-orange-500/20 cursor-pointer" onClick={() => navigate('/marketplace')} data-testid="mercato-card">
          <CardContent className="p-2 sm:p-3 flex items-center gap-2">
            <div className="p-1.5 sm:p-2 bg-orange-500 rounded-lg"><Store className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-base sm:text-lg">{language === 'it' ? 'Mercato' : 'Market'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{language === 'it' ? 'Film scartati' : 'Discarded films'}</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/5 border-emerald-500/20 cursor-pointer relative" onClick={() => navigate('/emerging-screenplays')} data-testid="emerging-screenplays-card">
          <CardContent className="p-2 sm:p-3 flex items-center gap-2">
            <div className="p-1.5 sm:p-2 bg-emerald-500 rounded-lg"><Pen className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-base sm:text-lg">{language === 'it' ? 'Sceneggiature' : 'Screenplays'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{language === 'it' ? 'Trame pronte' : 'Ready scripts'}</p></div>
            {emergingCount > 0 && <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-[9px] font-bold flex items-center justify-center">{emergingCount}</span>}
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-cyan-500/20 to-cyan-600/5 border-cyan-500/20 cursor-pointer relative" onClick={() => navigate('/games')} data-testid="contests-box">
          <CardContent className="p-2 sm:p-3 flex items-center gap-2">
            <div className="p-1.5 sm:p-2 bg-cyan-500 rounded-lg"><Trophy className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-base sm:text-lg">{language === 'it' ? 'Contest' : 'Contests'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{language === 'it' ? 'Guadagna CinePass' : 'Earn CinePass'}</p></div>
            {availableContests > 0 && <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-[9px] font-bold flex items-center justify-center">{availableContests}</span>}
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-pink-500/20 to-pink-600/5 border-pink-500/20 cursor-pointer" onClick={() => navigate('/challenges')} data-testid="challenges-box">
          <CardContent className="p-2 sm:p-3 flex items-center gap-2">
            <div className="p-1.5 sm:p-2 bg-pink-500 rounded-lg"><Swords className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-base sm:text-lg">{language === 'it' ? 'Sfide' : 'Challenges'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{language === 'it' ? 'Sfida altri!' : 'Battle others!'}</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-red-500/20 to-orange-600/5 border-red-500/20 cursor-pointer relative" onClick={() => navigate('/pvp-arena')} data-testid="arena-shortcut">
          <CardContent className="p-2 sm:p-3 flex items-center gap-2">
            <div className="p-1.5 sm:p-2 bg-red-500 rounded-lg"><Target className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-base sm:text-lg">{language === 'it' ? 'Arena' : 'Arena'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{pvpStats ? `${pvpStats.total_actions || 0} azioni` : (language === 'it' ? 'PvP' : 'PvP')}</p></div>
            {pvpStats?.actions_remaining > 0 && <span className="absolute top-1 right-1 w-4 h-4 bg-green-500 rounded-full text-[9px] font-bold flex items-center justify-center">{pvpStats.actions_remaining}</span>}
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-red-500/20 to-red-600/5 border-red-500/20 cursor-pointer" onClick={() => navigate('/festivals')}>
          <CardContent className="p-2 sm:p-3 flex items-center gap-2">
            <div className="p-1.5 sm:p-2 bg-red-500 rounded-lg"><Award className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-base sm:text-lg">{language === 'it' ? 'Festival' : 'Festivals'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{language === 'it' ? 'Premi cinema' : 'Awards'}</p></div>
          </CardContent>
        </Card>
      </div>

      {/* LE MIE TV! - Full width button */}
      <Card
        className={`mb-4 cursor-pointer transition-all ${
          hasEmittenteTV
            ? 'bg-gradient-to-r from-red-500/25 to-red-600/10 border-red-500/30 hover:border-red-500/50'
            : 'bg-[#1A1A1A] border-white/10'
        }`}
        onClick={() => {
          if (!hasEmittenteTV) { toast.info(language === 'it' ? 'Sblocca un\'Emittente TV nelle Infrastrutture!' : 'Unlock a TV Broadcaster in Infrastructure!'); return; }
          if (myTVStations.length === 1) { navigate(`/tv-station/${myTVStations[0].id}`); return; }
          setShowTVPopup(true);
        }}
        data-testid="le-mie-tv-card"
      >
        <CardContent className="p-2.5 sm:p-3 flex items-center gap-3">
          <div className={`p-2 sm:p-2.5 rounded-lg ${hasEmittenteTV ? 'bg-red-500' : 'bg-gray-700'}`}>
            <Radio className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-['Bebas_Neue'] text-lg sm:text-xl">{language === 'it' ? 'Le Mie TV!' : 'My TVs!'}</h3>
            <p className="text-[10px] sm:text-xs text-gray-400">
              {hasEmittenteTV
                ? `${myTVStations.length} emittent${myTVStations.length === 1 ? 'e' : 'i'} televisiv${myTVStations.length === 1 ? 'a' : 'e'}`
                : (language === 'it' ? 'Sblocca nelle Infrastrutture' : 'Unlock in Infrastructure')
              }
            </p>
          </div>
          {hasEmittenteTV && <ChevronRight className="w-5 h-5 text-red-400" />}
          {!hasEmittenteTV && <Lock className="w-4 h-4 text-gray-600" />}
        </CardContent>
      </Card>

      {/* I Miei Film - 5 poster row */}
      {films.length > 0 && (
        <div className="mb-4" data-testid="my-films-section">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-['Bebas_Neue'] text-lg flex items-center gap-2"><Film className="w-4 h-4 text-yellow-400" />{language === 'it' ? 'I MIEI FILM' : 'MY FILMS'}</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/films')} className="h-6 text-[10px] text-yellow-400 hover:text-yellow-300 px-2">Vedi Tutti <ChevronRight className="w-3 h-3 ml-0.5" /></Button>
          </div>
          <div className="grid grid-cols-5 gap-1.5">
            {films.slice(0, 5).map(film => (
              <div key={film.id} className="cursor-pointer group" onClick={() => navigate(`/films/${film.id}`)} data-testid={`my-film-${film.id}`}>
                <div className="aspect-[2/3] relative rounded-lg overflow-hidden">
                  <MasterpieceBadge isMasterpiece={film.is_masterpiece} size="xs" />
                  <img src={posterSrc(film.poster_url)} alt={film.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                  {film.is_sequel && <div className="absolute top-0.5 right-0.5 bg-purple-600/90 text-white text-[6px] px-1 py-0.5 rounded font-bold">#{film.sequel_number || 2}</div>}
                  {(film.virtual_likes > 0) && (
                    <div className="absolute top-0.5 left-0.5 bg-black/70 rounded px-0.5 py-0.5 flex items-center gap-0.5">
                      <Heart className="w-1.5 h-1.5 text-pink-400 fill-pink-400" />
                      <span className="text-[6px] text-pink-300">{film.virtual_likes}</span>
                    </div>
                  )}
                </div>
                <p className="text-[7px] font-semibold truncate mt-0.5">{film.title}</p>
                <p className="text-[6px] text-gray-500 truncate">${((film.total_revenue || 0)/1000).toFixed(0)}K</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Le Mie Serie TV - 5 poster row - SEMPRE VISIBILE */}
      <div className="mb-4" data-testid="my-series-section">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-['Bebas_Neue'] text-lg flex items-center gap-2"><Tv className="w-4 h-4 text-blue-400" />{language === 'it' ? 'LE MIE SERIE TV' : 'MY TV SERIES'}</h2>
          {mySeries.length > 0 && <Button variant="ghost" size="sm" onClick={() => navigate('/films?view=series')} className="h-6 text-[10px] text-blue-400 hover:text-blue-300 px-2">Vedi Tutti <ChevronRight className="w-3 h-3 ml-0.5" /></Button>}
        </div>
        {mySeries.length > 0 ? (
          <div className="grid grid-cols-5 gap-1.5">
            {mySeries.slice(0, 5).map(s => (
              <div key={s.id} className="cursor-pointer group" onClick={() => navigate(`/series/${s.id}`)} data-testid={`my-series-${s.id}`}>
                <div className="aspect-[2/3] relative rounded-lg overflow-hidden">
                  {s.poster_url ? (
                    <img src={posterSrc(s.poster_url)} alt={s.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" />
                  ) : (
                    <div className="w-full h-full bg-blue-500/10 flex items-center justify-center"><Tv className="w-6 h-6 text-blue-400/30" /></div>
                  )}
                  <Badge className={`absolute top-0.5 right-0.5 text-[5px] px-0.5 py-0 leading-tight ${s.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'}`}>{s.status === 'completed' ? 'DONE' : s.status}</Badge>
                </div>
                <p className="text-[7px] font-semibold truncate mt-0.5">{s.title}</p>
                <p className="text-[6px] text-gray-500 truncate">{s.genre_name || s.genre}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-blue-500/5 border border-blue-500/10 rounded-lg p-3 text-center">
            <Tv className="w-5 h-5 text-blue-500/20 mx-auto mb-1" />
            <p className="text-[10px] text-gray-500">{language === 'it' ? 'Nessuna serie TV ancora. Crea la tua prima serie!' : 'No TV series yet. Create your first series!'}</p>
          </div>
        )}
      </div>

      {/* I Miei Anime - 5 poster row */}
      {myAnime.length > 0 && (
        <div className="mb-4" data-testid="my-anime-section">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-['Bebas_Neue'] text-lg flex items-center gap-2"><Sparkles className="w-4 h-4 text-orange-400" />{language === 'it' ? 'I MIEI ANIME' : 'MY ANIME'}</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/films?view=anime')} className="h-6 text-[10px] text-orange-400 hover:text-orange-300 px-2">Vedi Tutti <ChevronRight className="w-3 h-3 ml-0.5" /></Button>
          </div>
          <div className="grid grid-cols-5 gap-1.5">
            {myAnime.slice(0, 5).map(a => (
              <div key={a.id} className="cursor-pointer group" onClick={() => navigate('/films?view=anime')} data-testid={`my-anime-${a.id}`}>
                <div className="aspect-[2/3] relative rounded-lg overflow-hidden">
                  {a.poster_url ? (
                    <img src={posterSrc(a.poster_url)} alt={a.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" />
                  ) : (
                    <div className="w-full h-full bg-orange-500/10 flex items-center justify-center"><Sparkles className="w-6 h-6 text-orange-400/30" /></div>
                  )}
                  <Badge className={`absolute top-0.5 right-0.5 text-[5px] px-0.5 py-0 leading-tight ${a.status === 'completed' ? 'bg-green-500' : 'bg-orange-500'}`}>{a.status === 'completed' ? 'DONE' : a.status}</Badge>
                </div>
                <p className="text-[7px] font-semibold truncate mt-0.5">{a.title}</p>
                <p className="text-[6px] text-gray-500 truncate">{a.genre_name || a.genre}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Stats Detail Modal */}
      <StatsDetailModal
        isOpen={showStatsDetail}
        onClose={() => setShowStatsDetail(false)}
        statType={selectedStatType}
        api={api}
      />

      {/* TV Stations Popup */}
      <Dialog open={showTVPopup} onOpenChange={setShowTVPopup}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-sm p-0" data-testid="tv-popup">
          <DialogHeader className="p-4 pb-2">
            <DialogTitle className="font-['Bebas_Neue'] text-lg text-red-400 flex items-center gap-2">
              <Radio className="w-5 h-5" /> Le Mie TV
            </DialogTitle>
          </DialogHeader>
          <div className="p-4 pt-0 space-y-2">
            {myTVStations.length === 0 ? (
              <div className="text-center py-4">
                <p className="text-gray-500 text-xs mb-2">Non hai ancora configurato nessuna emittente</p>
                <Button size="sm" className="bg-red-500 hover:bg-red-600 text-xs" onClick={() => { setShowTVPopup(false); navigate('/my-tv'); }}>
                  Configura Emittente
                </Button>
              </div>
            ) : (
              myTVStations.map(s => (
                <div
                  key={s.id}
                  className="flex items-center gap-3 p-2.5 rounded-lg bg-white/[0.03] border border-white/5 hover:border-red-500/20 cursor-pointer transition-all"
                  onClick={() => { setShowTVPopup(false); navigate(`/tv-station/${s.id}`); }}
                  data-testid={`tv-popup-station-${s.id}`}
                >
                  <div className="p-1.5 bg-red-500/20 rounded-lg"><Radio className="w-4 h-4 text-red-400" /></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold truncate">{s.station_name}</p>
                    <p className="text-[10px] text-gray-500">{s.nation} | Lv.{s.infra_level || 1} | {s.content_count || 0}/{s.capacity?.total || '?'} contenuti</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-600" />
                </div>
              ))
            )}
            <Button variant="outline" size="sm" className="w-full text-xs border-white/10 mt-2" onClick={() => { setShowTVPopup(false); navigate('/tv-stations'); }} data-testid="view-all-tv-btn">
              Vedi Tutte le Emittenti <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ==================== CHALLENGES PAGE (Sfide) ====================

export default Dashboard;
