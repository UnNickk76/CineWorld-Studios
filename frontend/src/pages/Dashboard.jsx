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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding, TrendingDown
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const Dashboard = () => {
  const { user, api, refreshUser } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const [stats, setStats] = useState(null);
  const [films, setFilms] = useState([]);
  const [challenges, setChallenges] = useState({ daily: [], weekly: [] });
  const [catchupData, setCatchupData] = useState(null);
  const [pendingRevenue, setPendingRevenue] = useState(null);
  const [collecting, setCollecting] = useState(false);
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
          <DialogHeader><DialogTitle>{titles[statType] || 'Details'}</DialogTitle></DialogHeader>
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
        
        const [statsRes, filmsRes, challengesRes, pendingRes] = await Promise.all([
          api.get('/statistics/my'),
          api.get('/films/my/featured?limit=6'),  // Use featured films sorted by attendance
          api.get('/challenges'),
          api.get('/revenue/pending-all')
        ]);
        setStats(statsRes.data);
        setFilms(filmsRes.data);  // Already limited and sorted by backend
        setChallenges(challengesRes.data);
        setPendingRevenue(pendingRes.data);
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

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="dashboard">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-4">
        <h1 className="font-['Bebas_Neue'] text-3xl md:text-4xl mb-1">
          {t('welcome')}, <span className="text-yellow-500">{user?.nickname}</span>
        </h1>
        <p className="text-gray-400 text-sm">{user?.production_house_name}</p>
      </motion.div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mb-4">
        {[
          { label: 'Films', value: stats?.total_films || 0, icon: Film, color: 'yellow', statType: 'films' },
          { label: 'Revenue', value: `$${((stats?.total_revenue || 0) / 1000000).toFixed(1)}M`, icon: DollarSign, color: 'green', statType: 'revenue' },
          { label: 'Likes', value: stats?.total_likes || 0, icon: Heart, color: 'red', statType: 'likes' },
          { label: 'Quality', value: `${(stats?.average_quality || 0).toFixed(0)}%`, icon: Star, color: 'blue', statType: 'quality' }
        ].map((stat, i) => (
          <Card 
            key={stat.label} 
            className="bg-[#1A1A1A] border-white/5 cursor-pointer hover:border-white/20 transition-colors"
            onClick={() => openStatDetail(stat.statType)}
            data-testid={`stat-card-${stat.statType}`}
          >
            <CardContent className="p-2.5 flex items-center gap-2">
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

      <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-4">
        <Card className="bg-gradient-to-br from-red-500/20 to-red-600/5 border-red-500/20 cursor-pointer" onClick={() => navigate('/festivals')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-red-500 rounded-lg"><Award className="w-5 h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'Festival' : 'Festivals'}</h3><p className="text-xs text-gray-400">{language === 'it' ? 'Premi cinema' : 'Awards'}</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border-yellow-500/20 cursor-pointer" onClick={() => navigate('/create')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-yellow-500 rounded-lg"><Plus className="w-5 h-5 text-black" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{t('create_film')}</h3><p className="text-xs text-gray-400">New blockbuster</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-orange-500/20 to-orange-600/5 border-orange-500/20 cursor-pointer" onClick={() => navigate('/pre-engagement')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-orange-500 rounded-lg"><Users className="w-5 h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'Pre-Ingaggio' : 'Pre-Engage'}</h3><p className="text-xs text-gray-400">{language === 'it' ? 'Ingaggia cast' : 'Engage cast'}</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/5 border-blue-500/20 cursor-pointer" onClick={() => navigate('/games')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-blue-500 rounded-lg"><Gamepad2 className="w-5 h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{t('mini_games')}</h3><p className="text-xs text-gray-400">Earn rewards</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-500/20 to-purple-600/5 border-purple-500/20 cursor-pointer" onClick={() => navigate('/social')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-purple-500 rounded-lg"><Globe className="w-5 h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{t('social')}</h3><p className="text-xs text-gray-400">Explore films</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-pink-500/20 to-pink-600/5 border-pink-500/20 cursor-pointer" onClick={() => navigate('/challenges')} data-testid="challenges-box">
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-pink-500 rounded-lg"><Swords className="w-5 h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'Sfide' : 'Challenges'}</h3><p className="text-xs text-gray-400">{language === 'it' ? 'Sfida altri!' : 'Battle others!'}</p></div>
          </CardContent>
        </Card>
      </div>

      {films.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2 sticky top-16 z-10 bg-[#0F0F10]/95 backdrop-blur-sm py-2 -mx-3 px-3" data-testid="my-films-sticky-header">
            <h2 className="font-['Bebas_Neue'] text-xl">{t('my_films')}</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/films')} className="h-7 text-xs">View All <ChevronRight className="w-3 h-3 ml-1" /></Button>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-1.5 sm:gap-2">
            {films.map(film => (
              <Card key={film.id} className="bg-[#1A1A1A] border-white/5 overflow-hidden cursor-pointer hover:border-white/15 transition-colors" onClick={() => navigate(`/films/${film.id}`)}>
                <div className="aspect-[2/3] relative">
                  <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} alt={film.title} className="w-full h-full object-cover" loading="lazy" />
                  {film.is_sequel && (
                    <div className="absolute top-1 right-1 bg-purple-600/90 text-white text-[8px] px-1 py-0.5 rounded font-bold">
                      SEQUEL #{film.sequel_number || 2}
                    </div>
                  )}
                  {(film.virtual_likes > 0) && (
                    <div className="absolute top-1 left-1 bg-black/70 rounded px-1 py-0.5 flex items-center gap-0.5">
                      <Heart className="w-2.5 h-2.5 text-pink-400 fill-pink-400" />
                      <span className="text-[9px] text-pink-300">{film.virtual_likes}</span>
                    </div>
                  )}
                </div>
                <CardContent className="p-1.5">
                  <h3 className="font-semibold text-[10px] sm:text-xs truncate">
                    {film.title}
                  </h3>
                  <div className="flex justify-between mt-0.5 text-[9px] sm:text-[10px] text-gray-400">
                    <span><Heart className="w-2 h-2 inline" /> {(film.likes_count || 0) + (film.virtual_likes || 0)}</span>
                    <span className="text-green-400">${((film.total_revenue || 0)/1000).toFixed(0)}K</span>
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
