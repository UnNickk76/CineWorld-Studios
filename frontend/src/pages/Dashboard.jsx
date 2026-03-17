// CineWorld Studio's - Dashboard
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding, TrendingDown, Pen
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const Dashboard = () => {
  const { user, api, refreshUser, updateUser } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const [stats, setStats] = useState(null);
  const [films, setFilms] = useState([]);
  const [pendingFilms, setPendingFilms] = useState([]);
  const [challenges, setChallenges] = useState({ daily: [], weekly: [] });
  const [catchupData, setCatchupData] = useState(null);
  const [pendingRevenue, setPendingRevenue] = useState(null);
  const [collecting, setCollecting] = useState(false);
  const [emergingCount, setEmergingCount] = useState(0);
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
  const [shootingPopup, setShootingPopup] = useState(null);
  const [shootingDays, setShootingDays] = useState(5);
  const [shootingConfig, setShootingConfig] = useState(null);
  const [startingShooting, setStartingShooting] = useState(false);
  const [endingShootingEarly, setEndingShootingEarly] = useState(false);
  const [showShootingDialog, setShowShootingDialog] = useState(false);
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
        likes: language === 'it' ? 'Like' : 'Likes', quality: language === 'it' ? 'Qualità' : 'Quality',
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
        case 'likes':
          return (<div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-pink-500/10 rounded p-3 text-center"><p className="text-2xl font-bold text-pink-500">{detailedStats.likes?.total || 0}</p><p className="text-xs text-gray-400">{lt('total')} {lt('likes')}</p></div>
              <div className="bg-blue-500/10 rounded p-3 text-center"><p className="text-2xl font-bold text-blue-500">{(detailedStats.likes?.average_per_film || 0).toFixed(1)}</p><p className="text-xs text-gray-400">{lt('avgPerFilm')}</p></div>
            </div></div>);
        case 'quality':
          return (<div className="space-y-4">
            <div className="bg-blue-500/10 rounded p-4 text-center"><p className="text-3xl font-bold text-blue-500">{(detailedStats.quality?.average || 0).toFixed(1)}%</p><p className="text-sm text-gray-400">{lt('average')} {lt('quality')}</p></div>
          </div>);
        default: return <p className="text-gray-400 text-center py-8">Select a stat</p>;
      }
    };
    
    const titles = { films: language === 'it' ? 'Dettagli Film' : 'Films Details', revenue: language === 'it' ? 'Dettagli Incassi' : 'Revenue Details', likes: language === 'it' ? 'Dettagli Like' : 'Likes Details', quality: language === 'it' ? 'Dettagli Qualità' : 'Quality Details' };
    
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

  useEffect(() => {
    const fetchData = async () => {
      try {
        // First, process offline catch-up
        const catchupRes = await api.post('/catchup/process');
        if (catchupRes.data.catchup_revenue > 0) {
          setCatchupData(catchupRes.data);
          toast.success(
            language === 'it' 
              ? `Bentornato! Recuperati $${catchupRes.data.catchup_revenue.toLocaleString()} per ${catchupRes.data.hours_missed} ore offline!`
              : `Welcome back! Collected $${catchupRes.data.catchup_revenue.toLocaleString()} for ${catchupRes.data.hours_missed} hours offline!`,
            { duration: 6000 }
          );
          // Refresh user data to update funds
          refreshUser();
        }
        
        const [statsRes, filmsRes, challengesRes, pendingRes, pendingFilmsRes] = await Promise.all([
          api.get('/statistics/my'),
          api.get('/films/my/featured?limit=9'),
          api.get('/challenges'),
          api.get('/revenue/pending-all'),
          api.get('/films/pending')
        ]);
        setStats(statsRes.data);
        setFilms(Array.from(new Map(filmsRes.data.map(f => [f.id, f])).values()));  // Deduplicate by ID
        setChallenges(challengesRes.data);
        setPendingRevenue(pendingRes.data);
        setPendingFilms(pendingFilmsRes.data || []);
        
        // Fetch emerging screenplays count for badge
        try {
          const emergingRes = await api.get('/emerging-screenplays/count');
          setEmergingCount(emergingRes.data.new || 0);
        } catch {}
        // Fetch available contests count for badge
        try {
          const contestsRes = await api.get('/cinepass/contests');
          const available = (contestsRes.data?.contests || []).filter(c => c.status === 'available' && !c.completed).length;
          setAvailableContests(available);
        } catch {}
        // Check if user owns a production studio
        try {
          const studioRes = await api.get('/production-studio/status');
          if (studioRes.data?.level) setHasStudio(true);
        } catch {}
        // Fetch shooting films
        try {
          const shootRes = await api.get('/films/shooting');
          setShootingFilms(shootRes.data?.films || []);
        } catch {}
        // Fetch shooting config
        try {
          const configRes = await api.get('/films/shooting/config');
          setShootingConfig(configRes.data);
        } catch {}
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
    
    // Setup heartbeat to track activity (every 5 minutes)
    const heartbeatInterval = setInterval(() => {
      api.post('/activity/heartbeat').catch(() => {});
    }, 5 * 60 * 1000);

    // Refresh pending revenue every minute
    const revenueInterval = setInterval(loadPendingRevenue, 60000);
    
    return () => {
      clearInterval(heartbeatInterval);
      clearInterval(revenueInterval);
    };
  }, [api]);

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
      const res = await api.post(`/films/${releasePopup.id}/release`, {
        distribution_zone: selectedZone,
        distribution_continent: selectedZone === 'continental' ? selectedContinent : null
      });
      if (res.data.success) {
        const filmTitle = releasePopup.title;
        const openingRevenue = res.data.opening_day_revenue;
        const zoneName = selectedZone === 'national' ? 'Nazionale' : selectedZone === 'continental' ? 'Continentale' : 'Mondiale';
        setPendingFilms(prev => prev.filter(f => f.id !== releasePopup.id));
        setReleasePopup(null);
        setReleaseSuccess({ title: filmTitle, revenue: openingRevenue, zone: zoneName, poster: releasePopup.poster_url });
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
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-4">
        <h1 className="font-['Bebas_Neue'] text-3xl md:text-4xl mb-1">
          {t('welcome')}, <span className="text-yellow-500">{user?.nickname || user?.production_house_name}</span>
        </h1>
        <p className="text-gray-400 text-sm">{user?.production_house_name}</p>
      </motion.div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mb-4">
        {[
          { label: 'Films', value: stats?.total_films || 0, icon: Film, color: 'yellow', statType: 'films' },
          { label: 'Incassi', value: `$${((stats?.total_revenue || 0) / 1000000).toFixed(1)}M`, icon: DollarSign, color: 'green', statType: 'revenue' },
          { label: 'Like', value: stats?.total_likes || 0, icon: Heart, color: 'red', statType: 'likes' },
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
        <Card className={`mb-4 border ${pendingRevenue.can_collect ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/10 border-green-500/30' : 'bg-[#1A1A1A] border-white/5'}`}>
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
                    <span>🎬 Film: ${(pendingRevenue.film_pending || 0).toLocaleString()}</span>
                    <span>🏢 Infra: ${(pendingRevenue.infra_pending || 0).toLocaleString()}</span>
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

      {/* Pending Films Section - always visible */}
      <Card className={`mb-4 border ${pendingFilms.length > 0 ? 'bg-gradient-to-r from-amber-500/10 to-orange-500/5 border-amber-500/20' : 'bg-[#1A1A1A] border-white/5'}`} data-testid="pending-films-section">
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-400" />
              {language === 'it' ? 'FILM IN ATTESA DI RILASCIO' : 'FILMS PENDING RELEASE'}
              {pendingFilms.length > 0 && <Badge className="bg-amber-500 text-black text-xs">{pendingFilms.length}</Badge>}
            </h3>
          </div>
          {pendingFilms.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {pendingFilms.slice(0, 6).map(film => (
                <div
                  key={film.id}
                  className="flex items-center gap-2 bg-black/30 rounded-lg p-2 cursor-pointer hover:bg-black/50 transition-colors border border-white/5 hover:border-amber-500/30"
                  onClick={() => openReleasePopup(film)}
                  data-testid={`pending-film-${film.id}`}
                >
                  <img
                    src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=100'}
                    alt={film.title}
                    className="w-10 h-14 object-cover rounded"
                    onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=100'; }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold truncate">{film.title}</p>
                    <p className="text-[10px] text-gray-400">{language === 'it' ? 'Qualità' : 'Quality'}: {(film.quality_score || 0).toFixed(0)}%</p>
                    <Button size="sm" className="mt-1 h-5 text-[10px] bg-amber-500 hover:bg-amber-600 text-black px-2" data-testid={`release-btn-${film.id}`}>
                      {language === 'it' ? 'Rilascia' : 'Release'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4" data-testid="no-pending-films">
              <p className="text-gray-500 text-xs mb-2">{language === 'it' ? 'Nessun film in attesa di rilascio.' : 'No films pending release.'}</p>
              <Button size="sm" className="h-7 text-xs bg-amber-500/20 text-amber-300 hover:bg-amber-500/30" onClick={() => navigate('/create-film')} data-testid="create-film-from-pending">
                {language === 'it' ? 'Crea un Film' : 'Create a Film'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

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
                      {sf.poster_url && <img src={sf.poster_url} alt="" className="w-8 h-12 rounded object-cover" />}
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
                  src={releasePopup.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=100'}
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

      {/* Financial Overview Card */}
      {stats && (
        <Card className="mb-4 bg-[#1A1A1A] border-white/5">
          <CardContent className="p-3">
            <h3 className="font-['Bebas_Neue'] text-lg mb-2 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              {language === 'it' ? 'BILANCIO FINANZIARIO' : 'FINANCIAL OVERVIEW'}
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-2 bg-red-500/10 rounded-lg border border-red-500/20">
                <p className="text-xs text-gray-400 mb-1">{language === 'it' ? 'Speso' : 'Spent'}</p>
                <p className="font-bold text-red-400">
                  ${((stats.total_spent || 0) / 1000000).toFixed(2)}M
                </p>
                <div className="text-[10px] text-gray-500 mt-1">
                  <div>Film: ${((stats.total_film_costs || 0) / 1000000).toFixed(1)}M</div>
                  <div>Infra: ${((stats.total_infra_costs || 0) / 1000000).toFixed(1)}M</div>
                </div>
              </div>
              <div className="text-center p-2 bg-green-500/10 rounded-lg border border-green-500/20">
                <p className="text-xs text-gray-400 mb-1">{language === 'it' ? 'Guadagnato' : 'Earned'}</p>
                <p className="font-bold text-green-400">
                  ${((stats.total_earned || 0) / 1000000).toFixed(2)}M
                </p>
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
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-3 gap-2 mb-4">
        {[
          { label: 'Like', value: (stats?.likeability_score || 50).toFixed(0), icon: Heart, color: 'pink' },
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

      <div className="grid grid-cols-2 md:grid-cols-6 gap-2 sm:gap-3 mb-4">
        <Card className="bg-gradient-to-br from-red-500/20 to-red-600/5 border-red-500/20 cursor-pointer" onClick={() => navigate('/festivals')}>
          <CardContent className="p-2 sm:p-3 flex items-center gap-2">
            <div className="p-1.5 sm:p-2 bg-red-500 rounded-lg"><Award className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-base sm:text-lg">{language === 'it' ? 'Festival' : 'Festivals'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{language === 'it' ? 'Premi cinema' : 'Awards'}</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border-yellow-500/20 cursor-pointer" onClick={() => navigate('/create-film')}>
          <CardContent className="p-2 sm:p-3 flex items-center gap-2">
            <div className="p-1.5 sm:p-2 bg-yellow-500 rounded-lg"><Clapperboard className="w-4 h-4 sm:w-5 sm:h-5 text-black" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-base sm:text-lg">{language === 'it' ? 'Produci!' : 'Produce!'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{language === 'it' ? 'Nuova produzione' : 'New production'}</p></div>
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
        <Card className="bg-gradient-to-br from-red-500/20 to-red-600/5 border-red-500/20 cursor-pointer relative" onClick={() => navigate('/create-film?tab=shooting')} data-testid="shooting-shortcut">
          <CardContent className="p-2 sm:p-3 flex items-center gap-2">
            <div className="p-1.5 sm:p-2 bg-red-500 rounded-lg"><Clapperboard className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-base sm:text-lg">{language === 'it' ? 'Ciak!' : 'Action!'}</h3><p className="text-[10px] sm:text-xs text-gray-400">{language === 'it' ? 'Si gira!' : 'Shooting!'}</p></div>
            {shootingFilms.length > 0 && <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-[9px] font-bold flex items-center justify-center animate-pulse">{shootingFilms.length}</span>}
          </CardContent>
        </Card>
      </div>

      {films.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2 sticky top-16 z-10 bg-[#0F0F10]/95 backdrop-blur-sm py-2 -mx-3 px-3" data-testid="my-films-sticky-header">
            <h2 className="font-['Bebas_Neue'] text-xl">{t('my_films')}</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/films')} className="h-7 text-xs">Vedi Tutti <ChevronRight className="w-3 h-3 ml-1" /></Button>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-1 sm:gap-1.5">
            {films.map(film => (
              <Card key={film.id} className="bg-[#1A1A1A] border-white/5 overflow-hidden cursor-pointer hover:border-white/15 transition-colors" onClick={() => navigate(`/films/${film.id}`)}>
                <div className="aspect-[2/3] relative">
                  <img 
                    src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} 
                    alt={film.title} 
                    className="w-full h-full object-cover" 
                    loading="lazy"
                    onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'; }}
                  />
                  {film.is_sequel && (
                    <div className="absolute top-0.5 right-0.5 bg-purple-600/90 text-white text-[6px] px-1 py-0.5 rounded font-bold">
                      #{film.sequel_number || 2}
                    </div>
                  )}
                  {(film.virtual_likes > 0) && (
                    <div className="absolute top-0.5 left-0.5 bg-black/70 rounded px-0.5 py-0.5 flex items-center gap-0.5">
                      <Heart className="w-2 h-2 text-pink-400 fill-pink-400" />
                      <span className="text-[7px] text-pink-300">{film.virtual_likes}</span>
                    </div>
                  )}
                </div>
                <CardContent className="p-1">
                  <h3 className="font-semibold text-[8px] sm:text-[9px] truncate">{film.title}</h3>
                  <div className="flex justify-between mt-0.5 text-[7px] sm:text-[8px] text-gray-400">
                    <span>${((film.total_revenue || 0)/1000).toFixed(0)}K</span>
                  </div>
                </CardContent>
              </Card>
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
    </div>
  );
};

// ==================== CHALLENGES PAGE (Sfide) ====================

export default Dashboard;
